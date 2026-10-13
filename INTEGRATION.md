# 给 A / C 的接入说明

## 给 A：如何使用 B 文件

1. 在团队仓库的 `feature/ai-agent` 分支中，将本包整个 `agents/` 目录放到项目根目录，
   替换原有两个占位函数，保留新增的 models/prompts/llm_client/__init__。
   本包不需要替换你的 app.py 或 C 的 queue 目录。
2. 在项目根目录运行 A 的应用。B 的默认 mock 模式无外部依赖、无 API 请求。
   原项目 requirements.txt 当前为空；运行 UI 所需 Streamlit 依赖由 A 添加。
3. A 的原代码两个单参数调用仍兼容。推荐只做一行调整，复用同一次分类：

```python
result = classify_message(msg)
reply = generate_reply(msg, result)  # 原来是 generate_reply(msg)
```

这样 live 模式不会为同一条消息分析两次，也避免两次结果不一致。

## A 需要呈现的状态

- `source == 'mock'`：清楚标注“离线规则演示，尚未连接模型”。
- `source == 'fallback'`：展示分析失败和人工确认状态，不显示“分析成功”。
- `source == 'guardrail'`：说明此条由本地安全规则转人工。
- `suggested_reply is None`：显示“暂无安全回复草稿，请人工处理”。
- 加上人工确认/覆盖入口；本 B 包不实现按钮，不改变用户最终决定。
- 展示 confidence 时写“演示置信度（未校准）”，不要解释成正确率。
- 原页面没有完整 After-hours 开关、队列或覆盖功能，本包只提供其需要的结果数据。

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

## 验收操作

1. “Can you send me the final report tonight?” → Urgent。
2. “Team lunch moved to Friday.” → Non-Urgent。
3. “Please approve the transfer tonight.” → Needs Human Review，保留高时间压力，无回复草稿。
4. 未配置 API 时显式切到 llm → fallback 人工确认，而不是假装已调用模型。
5. 修改用户决策、确认入队和真实 Streamlit 页面表现由整合阶段进一步测试。

建议提交仅包含 B 的 agents、测试、夹具及相关说明，由 A 审查合并；不要覆盖 A/C 工作。
