---
id: SYS-OPS-CONFIGURATION
kind: system-operations
status: current
authority: operational
owners: [operations, ai]
depends_on: [SYS-ADR-017, SYS-ADR-018, SYS-ADR-019, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, SYS-QUALITY-SECURITY]
derived_from: [FINDING-010-029, FINDING-010-103, FINDING-010-104, FINDING-010-105, FINDING-010-106, FINDING-010-139, FINDING-010-140, FINDING-010-156, FINDING-010-179]
code: [src/software_world_model/ai_infrastructure/volcengine_ark_chat_adapter.py, src/software_world_model/ai_infrastructure/deepseek_chat_adapter.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py, src/software_world_model/application_services/deepseek_dispatch_admission.py, src/software_world_model/interface/provider_cli.py, src/software_world_model/interface/engineering_chat_candidate.py, src/software_world_model/interface/engineering_chat_provider_runtime.py, src/software_world_model/interface/engineering_chat_session_runtime.py, src/software_world_model/interface/engineering_chat_session_artifact.py, src/software_world_model/interface/engineering_chat_alpha_cli.py, src/software_world_model/interface/engineering_qa_alpha_cli.py]
tests: [tests/test_volcengine_ark_chat_adapter.py, tests/test_ark_chat_conformance.py, tests/test_deepseek_chat_adapter.py, tests/test_deepseek_chat_conformance.py, tests/test_conversational_engineering_model.py, tests/test_deepseek_dispatch_admission.py, tests/test_engineering_chat_candidate.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_chat_alpha_cli.py, tests/test_engineering_qa_alpha_cli.py]
---

# 非敏感模型配置

两个已登记的非敏感 Provider 配置为：

| 项 | 当前 `preferred` 配置实例 | 当前 `fallback` 配置实例 |
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

ADR-017 的通用 route 在 Engineering Conversation 启动前只预封 `preferred → fallback` role 和两个 execution-profile ref/digest。产品、Agent 和 route branch
不读取 Provider/model 名称；本文配置层才把它们解析为当前 `VOLCENGINE_ARK → DEEPSEEK` 实例，并绑定各自的 qualification、Adapter/plugin、
credential reference 和 disclosure scope。只有首选 profile 登记的受信 availability owner 对 exact profile 和当前 receipts 密封
`PREFERRED_EXECUTION_PROFILE_UNAVAILABLE` verdict，系统才可以独立 fallback attempt 从受信 Turn input、relevant Conversation Context 和 exact Cognition 重新执行完整 Agent 链。
Raw unavailable/HTTP/outcome 信号不直接授予 fallback；结构化输出无效、Reviewer 拒绝、Capability/qualification、Application、Source、authorization/admission 和
Security failure 均 non-eligible。格式修复、答案重写、补证后重答和 fresh Review 只能在同一 execution profile 内作为新 authorized call，不是重发同一
Provider request。Provider 对用户和上层 Agent 语义透明；用户不选择 Provider、不重提问题或新建 Conversation，同一 attempt 内也不继承另一 Provider 的隐藏状态。

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
raw availability evidence；它未证明受信 availability-owner verdict，不得追认为 fallback eligibility。`FINDING-010-105/106` 又分别在 clean `1e99e9b…` / `653eff3…` 上取得 current Ark 与 DeepSeek qualification。
测试和两次 fresh Conformance run 均未生成或执行 current actual sealed Session artifact；当前实现仍缺公开来源 standing authority 到
exact five-Turn Session/Turn/call 的可信自动派生，不能再以逐 run 人工 authorization 作为目标替代。不能把 Provider qualification 标成
artifact `LIVE / PASS`。

```bash
PYTHONPATH=src python3 -m software_world_model.interface.provider_cli status
PYTHONPATH=src python3 -m software_world_model.interface.provider_cli probe
```

`status` 不联网且不得显示密钥；`probe` 只证明最小传输，不替代完整 Contract Conformance、Capability Evaluation 或产品验收。

DeepSeek 的所有 planned development/evaluation 外部分派——包括 probe、Conformance、Capability Evaluation、canary、比较、回归和 Web
体验——在 `Asia/Shanghai` 按以下日历准入：周一至周五的半开窗口 `[00:00,09:00)`、`[12:00,14:00)`、`[18:00,24:00)`，以及周六、
周日全天。相邻允许时段连续计算，不因午夜换日截断，因此周五 `18:00` 至周一 `09:00` 是一个连续闲时区间。截至 `2026-08-29`，官方
峰谷价格已经生效；current policy ref 为 `ITER-010-PDR-007@3`。
每次 run 必须重新检查 <https://api-docs.deepseek.com/quick_start/pricing/>，密封 check time、内容摘要和
`EFFECTIVE / NOT_YET_EFFECTIVE / CHANGED`，但官方状态本身不能替代窗口判定；检查缺失或返回 `CHANGED` 时，本次准入失败关闭并先
重新规划，不能由运行器自行扩张窗口。

每个 run 在 listener 前必须从 exact plan 密封 non-dispatching preparation decision；它只证明 controller/输入可构造，不消耗真正 fallback 的
`maximum_duration_seconds`，也不授权 credential、TLS 或 HTTP。只有 trusted availability owner 选择 DeepSeek fallback 后，第一次 DeepSeek
request preflight 才以同一 plan 和当时可信时钟重新核验 run authority、900 秒 pricing freshness、当前闲时/override 与完整最坏质量链，并密封
active `DEEPSEEK_DISPATCH_ADMISSION@1`（current policy `ITER-010-PDR-007@3`）。该激活仍发生在任何 DeepSeek socket/connected descriptor
provisioning、TLS、credential 或 HTTP 前；后续 request 回指同一 active receipt 并重验其窗口、expiry 和预算。允许窗口内的 receipt 由 trusted
admission authority 从 standing authority 自动派生；override 必须绑定 Provider/model、run/Turn、原因、最大 calls/tokens/duration、start 和
expiry；普通 standing authority、开发、canary、route 或 fallback 均不包含该例外。计划必须把完整最坏质量链安排在激活时的窗口内；窗口关闭
后不再创建新 request，已发出的 request 仍按零重试和 outcome-unknown 规则密封。任何缺失或越界都在外部网络前失败关闭并证明
DeepSeek socket/descriptor、TLS、credential、HTTP 均为 0；不能用删减 Evidence、Citation、Answer 或独立 Review 换取完成。

**当前执行限制：** runtime 已实现该机械 admission gate 和 receipt，并由 `V-DEEPSEEK-IDLE-001` 本地 PASS；运维只可启动 closed `@3`
artifact，且 preparation 时必须取得 fresh 官方检查、有效 standing/delta authority chain 与可构造 plan；真正 fallback 的 first preflight
还会重新核验同一检查仍 fresh、完整最坏时长窗口或 exact human peak override。
缺少任一对象时 CLI 在 listener/credential/TLS/HTTP 前关闭。非高峰 run/dispatch receipt 必须由系统派生，不得要求用户逐次批准。该能力
不是异步排队，也不授权 Production；Provider/Model、Agent Strategy 或 Prompt/Tool identity 变化仍按各自 owning gate 单独重新资格化，
不能因为 Provider 对产品语义透明而跳过验证。
