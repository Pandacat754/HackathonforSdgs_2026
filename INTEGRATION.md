# 给 A / C 的接入说明

## 给 A：如何使用 B 文件

1. 在团队仓库的 `feature/ai-agent` 分支中，将本包整个 `agents/` 目录放到项目根目录，
   替换原有两个占位函数，保留新增的 models/prompts/llm_client/__init__。
   本包不需要替换你的 app.py 或 C 的 queue 目录。
2. 在项目根目录安装 `requirements.txt` 并启动 Streamlit 页面：

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

   `app.py` 会从项目目录读取 `data/sample_messages.json`。默认 mock 模式无外部依赖、
   无 API 请求；要启用真实模型，请按 `AI_AGENT.md` 配置环境变量并显式设置
   `SILENCER_MODE=llm`。
3. 分类和草稿应复用同一次分析结果：

```python
result = classify_message(msg)
reply = generate_reply(msg, result)
```

不要在页面中再调用 `generate_reply(msg)` 而不传入 `result`；那会再次调用模型。
Streamlit 页面会在 session state 中保留分析结果，避免交互 rerun 后结果消失。

## A 需要呈现的状态

- `source == 'mock'`：清楚标注“离线规则演示，尚未连接模型”。
- `source == 'fallback'`：展示分析失败和人工确认状态，不显示“分析成功”。
- `source == 'guardrail'`：说明此条由本地安全规则转人工。
- `suggested_reply is None`：显示“暂无安全回复草稿，请人工处理”。
- 加上人工确认/覆盖入口；本 B 包不实现按钮，不改变用户最终决定。
- 展示 confidence 时写“演示置信度（未校准）”，不要解释成正确率。
- 页面展示离线演示、模型 fallback、安全检查等状态；置信度标为未校准。
- 页面不自动发送回复或写入队列，所有结果仍需用户确认。

不要用 `classification != 'Urgent'` 判断可以排队；第三类必须单独处理：

```python
if result['category'] == 'urgent':
    # 展示优先提醒，交用户决定；这不是自动接受任务
    pass
elif result['category'] == 'wait_until_morning':
    # 交 C 的接口；由 A/C 实现确认、去重与实际入队
    pass
else:
    # 独立“待人工确认”区域，不自动归入明早队列
    pass
```

## 给 C：可用的数据

使用原始 msg 的 id 做稳定关联。传入队列所需原始消息和 result；
字段包括 queue_title、queue_for、category、reason。具体 add_to_queue 签名由 A/C 确定。
queue_title 是原始消息截短摘要，不是 AI 生成的任务承诺。
queue_for 缺失时不要虚构早上九点：提示用户确认下个工作时段或保持待安排。
避免每次 Streamlit rerun 重复入队；用户覆盖决定后，要同步更新队列状态。

`data/agent_test_cases.json` 是 B 的测试夹具，不替换 C 的 sample_messages.json。
若用于 UI 演示，去除 expected_category 后再传入 agent（agent 本身也只读取白名单字段）。
消息可包含 `app` 来源字段，取值为 `Teams`、`Gmail`、`Outlook` 或 `Whatsapp`；
页面会在消息和详情弹窗中以 `From:` 显示该来源。
联系人偏好通过 `sender_relationship` 消息元数据和 `preferred_tone`
策略字段提供给 agent；这些内容只用于草稿语气，不得改变分类或安全约束。

## 验收操作

1. “Can you send me the final report tonight?” → Urgent。
2. “Team lunch moved to Friday.” → Non-Urgent。
3. “Please approve the transfer tonight.” → Needs Human Review，保留高时间压力，无回复草稿。
4. 未配置 API 时显式切到 llm → fallback 人工确认，而不是假装已调用模型。
5. 修改用户决策、确认入队和真实 Streamlit 页面表现由整合阶段进一步测试。

建议提交仅包含 B 的 agents、测试、夹具及相关说明，由 A 审查合并；不要覆盖 A/C 工作。
