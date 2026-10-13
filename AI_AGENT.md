# Silencer — Person B 交付包

这是 B 的消息分类、理由、提示词、回复草稿和测试模块。原始 A 项目没有改动。
Python 3.10+；核心代码和测试只用标准库，不需要安装依赖或提供密钥。

## 1. 现在能做什么

- 保留 A 的 `classify_message(message)`、`generate_reply(message)` 入口。
- 返回三类结果：Urgent、Non-Urgent、Needs Human Review，以及稳定的机器枚举。
- 提供紧急程度、判断理由、置信度、建议动作、可选队列时间和中/英文回复草稿。
- 高风险、模糊、低置信度、输入错误、模型错误默认交人工确认。
- 默认 `mock` 是**离线规则演示**，不是已经接上 GenAI。结果包含 `source`，离线理由也有标记。
- `llm` 模式已配置 DeepSeek-V4.1-Flash（API 名称 `deepseek-flash`），显式关闭思考模式。
- 不发送消息，不操作队列，不触发真实通知；`action` 是给 A/C 的建议。

## 2. 本地运行

在终端执行：

```bash
cd HackathonforSdgs_2026
python3 demo_agent.py
python3 demo_agent.py --message 'FYI, I uploaded the meeting notes.'
python3 -m unittest discover -s tests -v
```

默认命令始终离线。22 条模拟消息放在 `data/agent_test_cases.json`。
案例 17、18 的历史/否定表述在离线版保守交人工，不代表语义 AI 的理想分类。
其中 `expected_category` 是规则演示验收目标，不能拿来当真实模型准确率的研究数据。

## 3. 文件职责

| 文件 | 用途 |
| --- | --- |
| `agents/classifier.py` | 兼容 A 的入口、离线演示、安全检查、输出组装 |
| `agents/reply_generator.py` | 回复草稿入口，不发送消息 |
| `agents/models.py` | 输入与模型 JSON 校验、固定枚举 |
| `agents/prompts.py` | 集中管理模型规则和提示词版本 |
| `agents/llm_client.py` | 可替换模型调用，超时与错误处理 |
| `demo_agent.py` | 无界面的 B 模块演示 |
| `tests/test_agent.py` | 自动化测试与 A 调用流程兼容检查 |
| `INTEGRATION.md` | 给 A/C 的复制和联调说明 |

## 4. 接口

```python
from agents.classifier import classify_message
from agents.reply_generator import generate_reply

message = {
    'id': 'msg002',
    'sender': 'Colleague',
    'message': 'FYI, I uploaded the meeting notes.',
    'received_at': '2026-10-16T20:00:00+08:00',
    'user_workday_starts_at': '2026-10-19T09:00:00+08:00',
}
result = classify_message(message)
reply = generate_reply(message, result)  # 复用分析结果，避免第二次调用模型
```

必须提供 `message`（也兼容交接文档的 `body`）。二者同时存在必须一致。
可选字段：id、sender、sender_relationship、channel、received_at、
user_workday_starts_at、deadline_at。时间使用带时区的 ISO 8601。
下一个工作时段由 A/用户提供，B 不猜周末、公众假期或轮班安排。
缺少时间时，非紧急结果的 `queue_for` 为 null，由 C 在已确认的用户日程下处理。

支持 `user_policy={'confidence_threshold': 0.70, 'reply_language': 'auto'}`。
reply_language 支持 auto/en/zh；阈值默认 0.70，是可调整演示参数，未经过统计校准。
低置信度不会变成“非紧急”。所有结果的 `requires_user_confirmation` 都是 true。

| category | classification（兼容 A 展示） | action |
| --- | --- | --- |
| urgent | Urgent | notify_user_now |
| wait_until_morning | Non-Urgent | queue_for_morning |
| needs_human_review | Needs Human Review | ask_user_to_review |

其他字段：message_id、urgency_score、confidence、reason、suggested_reply、
queue_title、queue_for、requires_user_confirmation、source、error_code、prompt_version。
source 为 mock / llm / guardrail / fallback；分数不是已校准的概率。

## 5. 启用 DeepSeek-V4.1-Flash（非思考模式）

已选定 DeepSeek-V4.1-Flash。默认仍为离线模式；真实调用需要配置密钥并显式选择 llm。不要把密钥发到群聊或提交 Git。
`.env.example` 只是字段示例，代码不会自动加载 `.env`。
通过终端环境变量或部署平台 Secret 设置以下值：

- `SILENCER_MODE=llm`
- `SILENCER_API_URL=https://api.deepseek.com/chat/completions`（代码已有此默认值）
- `SILENCER_MODEL=deepseek-flash`（代码已有此默认值）
- `SILENCER_API_KEY`：仅保存在环境变量/Secret
- `SILENCER_TIMEOUT_SECONDS=15`：可选，允许 0–60 秒（不含 0）

请求使用 `max_tokens=600`、`response_format={"type":"json_object"}` 和
`thinking={"type":"disabled"}`，避免默认启用思考模式。
直接 HTTP 请求的 thinking 位于顶层，不包在 SDK 专用的 extra_body 中。
更换供应商时须检查这些参数的兼容性，修改 llm_client.py 不影响 A/C 接口。
配置后可用 `python3 demo_agent.py --mode llm --message 'FYI, meeting notes are ready.'`
进行一次合成消息测试；这会产生真实 API 请求及相应费用。

API 缺配置、超时、拒绝、截断、无效 JSON 或错误 schema 均返回 fallback，
不会偷偷改用离线结果假装模型成功。不在错误输出中展示密钥、原始服务器错误或响应正文。

API 格式参考（2026-10-13 查阅）：
https://api-docs.deepseek.com/api/create-chat-completion/
https://api-docs.deepseek.com/zh-cn/guides/thinking_mode/

## 6. 回复与风险边界

首版让模型选择受约束的回复意图，再由本地安全模板生成英文或中文草稿，
而不是直接放行模型任意生成的承诺。未来若扩展自由措辞，需要额外审核与评估。
草稿不声称用户已阅读、不承诺交付时间，也不声称队列已实际写入。
财务/人事/法律等敏感消息直接转人工；敏感且紧急可以同时保留高 urgency_score，
但 action 仍是人工确认。A 不应把人工确认当作普通明早队列，也不要无条件频繁通知用户。

本地关键词检查是 Demo 防线，不保证穷尽敏感表达或提示注入。
离线模式只覆盖有限中英文常见表达，对未知措辞保守转人工；不声称具备通用语义理解。
LLM 的理由也是模型输出，必须以普通文本展示，不应作为命令执行。
同样的输入多次真实调用可能产生差异，A 应把本次结果保留在 session state，复用结果。

## 7. 验证状态

- 自动化测试覆盖 22 条合成消息、API 响应模拟、格式校验、错误降级和接口兼容。
- 原 A 页面调用流程使用轻量显示替身验证，不等于真正启动 Streamlit 的 UI 测试。
- 已选择并适配 DeepSeek-V4.1-Flash 非思考模式，已于 2026-10-13 完成一次合成场景实测：16/16 通过（13 次模型调用 + 3 次本地安全检查），模型调用约 0.79–1.22 秒。这是小规模演示验收，不代表真实工作消息准确率。
- 尚未实现或测试 C 的队列，完整 Streamlit UI 仍需由团队联调。
