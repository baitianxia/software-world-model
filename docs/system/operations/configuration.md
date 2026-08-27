---
id: SYS-OPS-CONFIGURATION
kind: system-operations
status: current
authority: operational
owners: [operations, ai]
depends_on: [SYS-ADR-017, SYS-ADR-018, SYS-ADR-019, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, SYS-QUALITY-SECURITY]
derived_from: [FINDING-010-029, FINDING-010-103, FINDING-010-104, FINDING-010-105, FINDING-010-106, FINDING-010-139, FINDING-010-140]
code: [src/software_world_model/ai_infrastructure/volcengine_ark_chat_adapter.py, src/software_world_model/ai_infrastructure/deepseek_chat_adapter.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py, src/software_world_model/application_services/deepseek_dispatch_admission.py, src/software_world_model/interface/provider_cli.py, src/software_world_model/interface/engineering_chat_candidate.py, src/software_world_model/interface/engineering_chat_provider_runtime.py, src/software_world_model/interface/engineering_chat_session_runtime.py, src/software_world_model/interface/engineering_chat_session_artifact.py, src/software_world_model/interface/engineering_chat_alpha_cli.py, src/software_world_model/interface/engineering_qa_alpha_cli.py]
tests: [tests/test_volcengine_ark_chat_adapter.py, tests/test_ark_chat_conformance.py, tests/test_deepseek_chat_adapter.py, tests/test_deepseek_chat_conformance.py, tests/test_conversational_engineering_model.py, tests/test_deepseek_dispatch_admission.py, tests/test_engineering_chat_candidate.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_chat_alpha_cli.py, tests/test_engineering_qa_alpha_cli.py]
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

## 公开来源 standing authority

固定公开开源测试工程、clean exact revision、上述已批准 Provider route/credential account、只读披露边界、预算和 loopback
`EVALUATION_ONLY` Sink 使用一次 `PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY@1`。运维不得为该边界内的每个 run、Turn、Agent/Reviewer
step 或 dispatch 再申请人工批准；trusted launcher/Application 自动派生 exact Session/Turn/attempt/call authority、Manifest 和 one-use
receipt，并继续逐调用记录 payload digest、Usage、transport 和成本。

以下变化必须停止自动派生并申请 human delta：private/unknown/dirty/local data；新 Provider/model/endpoint/credential account；预算扩张；
DeepSeek 峰时 override；外部写；非 loopback 或 Production。公开性、clean revision、资格、standing authority 有效性或派生链无法证明时
失败关闭。正常 Turn 文本、run identity 和 dispatch 数量本身不是新的人工授权事件。

**当前实现边界：** 兼容 Engineering QA Alpha 的 `@1` 配置仍是单 DeepSeek session，不定义
`CONVERSATIONAL_ENGINEERING_AGENT@1`。新 Chat 已实现独立 `SWM-ENGINEERING-CHAT-ARTIFACT-SESSION-CONFIG@1`：canonical absolute、
owner-private mode `0600`、unique-key UTF-8 JSON、closed root fields；它固定 distinct product/source Git identity、published World Model
artifacts、exact Source Profile、`src/main/resources` 排除、ordinal 1 Ark/ordinal 2 DeepSeek、两份 Conformance result、两个 private Gateway
repositories、Session authority 和 receipt paths。当前 bounds 精确为 5 Turns、每 Turn 每 Provider 15 dispatch、每 Provider 总计 75；任一
unknown/missing/duplicate/reordered field、identity drift 或 allowlist/exclusion overlap 都在 attempt、credential、Source read、dispatch 和
listener 前失败关闭。

`FINDING-010-103` 已让 `swm-engineering-chat --session-config <owner-private-artifact>` 消费该完整对象图；无参数命令继续保留 Access-only
身份。固定命令不接受 host、port、工程、revision、Provider、question、credential 或单项 authority 参数；artifact 分支固定
`127.0.0.1:8765`，在 listener 构造前写零活动 launch receipt，并在 shutdown 后写 terminal receipt。当前状态是
`ARK_CONFORMANCE_PASS / DEEPSEEK_CONFORMANCE_PASS / DUAL_PROVIDER_QUALIFICATION_CURRENT / STANDING_AUTHORITY_DERIVATION_REQUIRED`：
`FINDING-010-104` 已把 Ark strict Session audit 接入 Conformance 与 terminal receipt，并将 HTTP 前 transport unavailable owner-typed 为
fallback eligibility；`FINDING-010-105/106` 又分别在 clean `1e99e9b…` / `653eff3…` 上取得 current Ark 与 DeepSeek qualification。
测试和两次 fresh Conformance run 均未生成或执行 current actual sealed Session artifact；当前实现仍缺公开来源 standing authority 到
exact five-Turn Session/Turn/call 的可信自动派生，不能再以逐 run 人工 authorization 作为目标替代。不能把 Provider qualification 标成
artifact `LIVE / PASS`。

```bash
PYTHONPATH=src python3 -m software_world_model.interface.provider_cli status
PYTHONPATH=src python3 -m software_world_model.interface.provider_cli probe
```

`status` 不联网且不得显示密钥；`probe` 只证明最小传输，不替代完整 Contract Conformance、Capability Evaluation 或产品验收。

DeepSeek 的所有 planned development/evaluation 外部分派——包括 probe、Conformance、Capability Evaluation、canary、比较、回归和 Web
体验——只允许在 `Asia/Shanghai` 半开窗口 `[00:00,09:00)`、`[12:00,14:00)`、`[18:00,24:00)`。截至 `2026-08-27`，DeepSeek 官方页面
仍将北京时间每日 `09:00–12:00`、`14:00–18:00` 定义为高峰，峰谷价格正式生效日以公告为准；本项目硬门禁不依赖价格是否已经生效。
每次 run 必须重新检查 <https://api-docs.deepseek.com/quick_start/pricing/>，密封 check time、内容摘要和
`EFFECTIVE / NOT_YET_EFFECTIVE / CHANGED`，但官方状态本身不能替代窗口判定；检查缺失或返回 `CHANGED` 时，本次准入失败关闭并先
重新规划，不能由运行器自行扩张窗口。

每个 run 在任何 DeepSeek socket/connected descriptor provisioning、TLS、credential 或 HTTP 前必须密封
`DEEPSEEK_DISPATCH_ADMISSION@1`；每个新 DeepSeek request 前重验
可信时钟仍在允许窗口，或存在一次性 exact human peak override。允许窗口内的 receipt 由 trusted admission authority 从 standing
authority 自动派生；override 必须绑定 Provider/model、run/Turn、原因、最大 calls/tokens/duration、start 和 expiry；普通 standing
authority、开发、canary、route 或 fallback 均不包含该例外。计划必须把完整最坏质量链安排在窗口内；窗口关闭
后不再创建新 request，已发出的 request 仍按零重试和 outcome-unknown 规则密封。任何缺失或越界都在外部网络前失败关闭并证明
DeepSeek socket/descriptor、TLS、credential、HTTP 均为 0；不能用删减 Evidence、Citation、Answer 或独立 Review 换取完成。

**当前执行限制：** runtime 已实现该机械 admission gate 和 receipt，并由 `V-DEEPSEEK-IDLE-001` 本地 PASS；运维只可启动 closed `@3`
artifact，且必须在启动前取得 fresh 官方检查、有效 standing/delta authority chain、完整最坏时长窗口判定或 exact human peak override。
缺少任一对象时 CLI 在 listener/credential/TLS/HTTP 前关闭。非高峰 run/dispatch receipt 必须由系统派生，不得要求用户逐次批准。该能力
不是异步排队，也不授权 Production；Provider/Model、Agent Strategy 或 Prompt/Tool identity 变化仍按各自 owning gate 单独重新资格化，
不能因为 Provider 对产品语义透明而跳过验证。
