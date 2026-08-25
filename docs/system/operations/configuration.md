---
id: SYS-OPS-CONFIGURATION
kind: system-operations
status: current
authority: operational
owners: [operations, ai]
depends_on: [SYS-ADR-017, SYS-ADR-018, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, SYS-QUALITY-SECURITY]
derived_from: [FINDING-010-103, FINDING-010-104]
code: [src/software_world_model/ai_infrastructure/volcengine_ark_chat_adapter.py, src/software_world_model/ai_infrastructure/deepseek_chat_adapter.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py, src/software_world_model/interface/provider_cli.py, src/software_world_model/interface/engineering_chat_candidate.py, src/software_world_model/interface/engineering_chat_provider_runtime.py, src/software_world_model/interface/engineering_chat_session_runtime.py, src/software_world_model/interface/engineering_chat_session_artifact.py, src/software_world_model/interface/engineering_chat_alpha_cli.py, src/software_world_model/interface/engineering_qa_alpha_cli.py]
tests: [tests/test_volcengine_ark_chat_adapter.py, tests/test_ark_chat_conformance.py, tests/test_deepseek_chat_adapter.py, tests/test_deepseek_chat_conformance.py, tests/test_conversational_engineering_model.py, tests/test_engineering_chat_candidate.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_chat_alpha_cli.py, tests/test_engineering_qa_alpha_cli.py]
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
| Connection policy | `DIRECT_VERIFIED_TLS_HTTP11_ONE_REQUEST_PER_SESSION@1` | `PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@2` |
| Credential resolution | verified TLS 后、每次 HTTP dispatch 前 | verified TLS 后、每次 HTTP dispatch 前 |
| TLS / session dispatch bound | 每 request 1 次 TLS attempt；每 session 1 次 HTTP | transport lifetime 最多 3 次 pre-dispatch TLS；每 session 最多 20 次 HTTP |
| Request retry | `false` | `false` |
| Tools/session/stream | 禁用 | 禁用 |
| Thinking | `thinking.type=disabled` | 按 exact qualification 冻结 |

请求别名与 Provider 实际返回身份是不同字段，只有符合性和能力结果可以证明其当前匹配。Adapter/Configuration/endpoint/model/transport/
rendering identity 或有效期变化会使旧 Conformance 失效；领域 Prompt、答案 Schema 或不改变上述 identity 的产品变化不得强制重复取得
Conformance。

ADR-017 的目标 route 是在 Engineering Conversation 启动前预封 `VOLCENGINE_ARK → DEEPSEEK` 及两者各自的 qualification、credential
reference 和 disclosure scope。用户提交一个 Turn；Ark Agent attempt 无 authorized answer 且属于已允许 Provider/model reason 时，系统
透明地以独立 DeepSeek attempt 从受信 Turn input、relevant Conversation Context 和 exact Cognition 重新执行完整 Agent 链。Provider 对
用户和上层 Agent 语义透明；用户不选择 Provider、不重提问题或新建 Conversation，同一 attempt 内也不继承另一 Provider 的隐藏状态。

**当前实现边界：** 兼容 Engineering QA Alpha 的 `@1` 配置仍是单 DeepSeek session，不定义
`CONVERSATIONAL_ENGINEERING_AGENT@1`。新 Chat 已实现独立 `SWM-ENGINEERING-CHAT-ARTIFACT-SESSION-CONFIG@1`：canonical absolute、
owner-private mode `0600`、unique-key UTF-8 JSON、closed root fields；它固定 distinct product/source Git identity、published World Model
artifacts、exact Source Profile、`src/main/resources` 排除、ordinal 1 Ark/ordinal 2 DeepSeek、两份 Conformance result、两个 private Gateway
repositories、Session authority 和 receipt paths。当前 bounds 精确为 5 Turns、每 Turn 每 Provider 15 dispatch、每 Provider 总计 75；任一
unknown/missing/duplicate/reordered field、identity drift 或 allowlist/exclusion overlap 都在 attempt、credential、Source read、dispatch 和
listener 前失败关闭。

`FINDING-010-103` 已让 `swm-engineering-chat --session-config <owner-private-artifact>` 消费该完整对象图；无参数命令继续保留 Access-only
身份。固定命令不接受 host、port、工程、revision、Provider、question、credential 或单项 authority 参数；artifact 分支固定
`127.0.0.1:8765`，在 listener 构造前写零活动 launch receipt，并在 shutdown 后写 terminal receipt。当前状态只是
`ARK_TRANSPORT_SESSION_AUDIT_LOCAL_CANDIDATE`：`FINDING-010-104` 已把 Ark strict Session audit 接入 Conformance 与 terminal receipt，
并将 HTTP 前 transport unavailable owner-typed 为 fallback eligibility。测试使用本地构造或 patched typed qualification/artifact evidence，
尚未生成或执行 current actual sealed Session artifact；真实 credential/Provider/browser 均未执行。旧 Ark Result 因 fixture、implementation
与 configuration identity drift 失效，必须在 clean freeze 上执行 fresh Conformance，不能把现有本地组合标成
`QUALIFIED / LIVE / PASS`。

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
