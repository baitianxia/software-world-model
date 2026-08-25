---
id: SYS-OPS-CONFIGURATION
kind: system-operations
status: current
authority: operational
owners: [operations, ai]
depends_on: [SYS-ADR-017, SYS-ADR-018, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, SYS-QUALITY-SECURITY]
code: [src/software_world_model/ai_infrastructure/volcengine_ark_chat_adapter.py, src/software_world_model/ai_infrastructure/deepseek_chat_adapter.py, src/software_world_model/interface/provider_cli.py, src/software_world_model/interface/engineering_qa_alpha_cli.py]
tests: [tests/test_volcengine_ark_chat_adapter.py, tests/test_ark_chat_conformance.py, tests/test_deepseek_chat_adapter.py, tests/test_deepseek_chat_conformance.py, tests/test_engineering_qa_alpha_cli.py]
---

# 非敏感模型配置

两个已登记的非敏感 Provider 配置为：

| 项 | Ark primary | DeepSeek fallback |
|---|---|---|
| Provider | `VOLCENGINE_ARK` | `DEEPSEEK` |
| Base URL | `https://ark.cn-beijing.volces.com/api/coding/v3` | `https://api.deepseek.com` |
| Endpoint | `/chat/completions` | `/chat/completions` |
| Request model reference | `glm-5-2-260617` | `deepseek-v4-pro` |
| Adapter | `openai-chat-completions-no-tools@8` | `deepseek-chat-completions-no-tools@7` |
| Secret reference | `env:ARK_API_KEY` | `env:DEEPSEEK_API_KEY` |
| Tools/session/stream | 禁用 | 禁用 |
| Thinking | `thinking.type=disabled` | 按 exact qualification 冻结 |

请求别名与 Provider 实际返回身份是不同字段，只有符合性和能力结果可以证明其当前匹配。Adapter/Configuration/endpoint/model/transport/
rendering identity 或有效期变化会使旧 Conformance 失效；领域 Prompt、答案 Schema 或不改变上述 identity 的产品变化不得强制重复取得
Conformance。

ADR-017 的目标 route 是在 Engineering Conversation 启动前预封 `VOLCENGINE_ARK → DEEPSEEK` 及两者各自的 qualification、credential
reference 和 disclosure scope。用户提交一个 Turn；Ark Agent attempt 无 authorized answer 且属于已允许 Provider/model reason 时，系统
透明地以独立 DeepSeek attempt 从受信 Turn input、relevant Conversation Context 和 exact Cognition 重新执行完整 Agent 链。Provider 对
用户和上层 Agent 语义透明；用户不选择 Provider、不重提问题或新建 Conversation，同一 attempt 内也不继承另一 Provider 的隐藏状态。

**当前实现偏差：** 现有 Engineering QA Alpha Session Configuration 仍只接受一份 DeepSeek Conformance，并形成单 Provider session；
透明双 route、双 attempt、late-result quarantine 和 Turn 汇总尚未实现或资格化。它也没有实现
`CONVERSATIONAL_ENGINEERING_AGENT@1` 的主 Agent、Conversation/Turn/Work State 分离和语义多轮 Chat。Ark Adapter 已存在不等于产品
route 可用，实现缺口也不算 Ark unavailable。新对话架构与目标 route 均为 `NOT_IMPLEMENTED / NOT_QUALIFIED`；在确定性测试和 live
audit 闭合前不得标成 PASS。

```bash
PYTHONPATH=src python3 -m software_world_model.interface.provider_cli status
PYTHONPATH=src python3 -m software_world_model.interface.provider_cli probe
```

`status` 不联网且不得显示密钥；`probe` 只证明最小传输，不替代完整 Contract Conformance、Capability Evaluation 或产品验收。

DeepSeek 批量调用的计划窗口为北京时间 `00:00–09:00`、`12:00–14:00`、`18:00–24:00`。截至 `2026-08-25`，DeepSeek 官方页面只
预告峰谷定价，正式生效日期仍以公告为准；每次批量启动前必须重新检查
<https://api-docs.deepseek.com/quick_start/pricing/>，密封检查时间、当时窗口和 `EFFECTIVE / NOT_YET_EFFECTIVE / CHANGED` 状态。
紧急高峰启动必须有显式审计 override。成本只决定 Turn 开始前是否承担完整 primary/fallback 最坏预算，不得削减已经开始的 Agent
调查、Evidence、Citation 或独立 Review。Provider/Model、Agent Strategy 或 Prompt/Tool identity 变化必须按其 owning gate 单独重新资格化，
不能因为 Provider 对产品语义透明而跳过验证。
