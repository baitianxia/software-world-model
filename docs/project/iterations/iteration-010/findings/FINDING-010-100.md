---
id: FINDING-010-100
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai, security, interface, operations, quality, project]
depends_on: [FINDING-010-099, SYS-ADR-017, SYS-ADR-018, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py, src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/application_services/conversational_engineering_routing.py, src/software_world_model/application_services/engineering_conversation.py, src/software_world_model/application_services/__init__.py, src/software_world_model/interface/engineering_chat_provider_launcher.py, src/software_world_model/interface/engineering_chat_browser.py, src/software_world_model/interface/__init__.py]
tests: [tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_routing.py, tests/test_engineering_chat_provider_launcher.py, tests/test_engineering_conversation.py, tests/test_engineering_chat_browser.py, tests/test_engineering_chat_alpha_cli.py, tests/test_engineering_chat_candidate.py, tests/test_conversational_engineering_tools.py, tests/test_model_gateway.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: application-owned-provider-attempt-routing
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-100：Ark→DeepSeek 独立 attempt 路由和固定 Chat 组合形成本地候选

## Observation

`FINDING-010-099` 的单 Provider model receipt 只有 raw `failure_code`。相同字符串可能来自已密封 Provider Result，也可能来自 Gateway
identity、repository、qualification 或 Application 错误；若路由只匹配字符串，会把实现缺口或安全错误伪装成 Provider unavailable 并错误
触发 fallback。另一个冲突是既有 executor 私有保存跨 Turn Work State：为 fallback 创建 fresh executor 会丢失已提交 Conversation 状态，
复用同一 executor 又可能让失败 primary 的临时状态进入 DeepSeek attempt。

## Evidence

- model call receipt 升级为 raw code + trusted `failure_kind` 双层记录。只有由有效 Gateway terminal Result 或成功 Result 后 closed decoder
  建立的 `PROVIDER_HTTP_ERROR / PROVIDER_OUTCOME_UNKNOWN / PROVIDER_OUTPUT_INVALID` 会映射为 ADR-017 fallback classification；pre-dispatch、
  qualification、Gateway Result identity 和其他 Gateway failure 保持非 eligible。错误 role 仍保留真实 dispatch receipt/count，但 classification
  被清空并以 protocol violation 关闭。
- Application Turn outcome 新增 closed Provider failure classification/raw code，以及 route/attempt receipt refs、fallback attempt count 和
  outcome-unknown duplicate-cost risk。Conversation Result digest 和 Browser developer projection 同步这些字段；same-Provider retry 仍固定为 0。
- 新 Application router 只接受 exact `VOLCENGINE_ARK → DEEPSEEK` route plan。每个 attempt authority 绑定 immutable original Turn、原
  User Message digest、Application-sealed relevant Conversation Context、World Model cognition authority、Source Profile、Provider
  configuration、Session Disclosure 和 retry 0。primary 只有在五类 closed classification 之一成立时才创建一个 fallback；Application、Source、
  Security、qualification、Gateway identity 或 runtime initialization failure 均不 fallback。
- 每个 attempt 由 lazy factory 形成独立 full-chain runtime 和 receipt；fallback factory只收到 original attempt authority，不接收 primary
  Work State、Ledger、Package、Draft、Review 或 Provider memory。复用 primary executor/component scope 会在 fallback dispatch 前失败。
  logical Turn 只投影最后一个完整 attempt 的 Outcome，同时聚合两次 attempt 的 dispatch/receipt audit；outcome unknown + fallback 明示潜在
  重复计算/计费，late-result policy 固定为 `QUARANTINE_AUDIT_ONLY`，没有覆盖或 merge API。
- 跨 Turn Work State 被提取为 Application-owned committed repository。fresh attempt executor 可以读取 current sealed Conversation 状态；
  只有成功 Outcome 写入 repository，失败 attempt 的临时 Work State 不会污染后续 fallback 或 Turn。新的 sealed Response Control 只对 exact
  approved Work State→Package→Draft→Review chain 签发一次 Delivery Authorization。
- 新 fixed Provider launcher composition 在不创建 attempt 的前提下绑定 exact product commit/tree、Chat Binding、evidence tools、双 route、
  两份 current Session Disclosure、lazy attempt factory、Conversation Service 和 Browser Application。receipt 保持 listener、credential、
  Source read、Provider dispatch 全为 0，并明确真实 Adapter/transport/credential attestation 与 live Provider/browser 尚未执行。现有公开
  `swm-engineering-chat` 命令仍是已验证的 Access-only launcher，没有被本地组合预检静默切换。
- 定向命令
  `PYTHONPATH=src:. python3 -m unittest tests.test_engineering_conversation tests.test_conversational_engineering_agent tests.test_conversational_engineering_tools tests.test_conversational_engineering_model tests.test_conversational_engineering_routing tests.test_engineering_chat_candidate tests.test_engineering_chat_provider_launcher tests.test_engineering_chat_browser tests.test_engineering_chat_alpha_cli tests.test_model_gateway`
  重新实际得到 `76/76 PASS`；相关 `compileall`、`git diff --check` 与 current documentation `500/500` 同时通过。本次没有外部网络、
  Provider/model、listener/browser、mall Source/resources、credential 或 Production Activation。

## Decision and disposition

- Application/Conversation Contract 现在明确区分 committed Conversation Work State 与 attempt-local intermediate state，并以 typed owner
  classification、parent/child identity、one-fallback fuse、两 attempt 分账、duplicate-cost risk 和 late quarantine 实现 ADR-017 的本地
  deterministic candidate。实现状态增加 `PROVIDER_ROUTE_COMPOSITION_LOCAL_CANDIDATE`。
- 这不是 Ark/DeepSeek 当前 live qualification、账户可用性、真实 Adapter/transport、真实 Disclosure、mall 答案质量或 Browser canary 证据。
  fixed composition 接受预构建的 model/source runtime dependencies；真实 runtime/session config 与当前 Access-only command 尚未形成 clean
  live freeze，因此保持 `NOT_ATTESTED / NOT_QUALIFIED / NOT_LIVE`。
- 下一最早缺口收窄为 exact Ark/DeepSeek Adapter+transport+credential-reference、Source/World Model runtime 与固定命令的真实组合冻结；其后
  才能请求五轮 Conversation 的逐输入 disclosure/Provider/browser grant。Citation/Review/attempt developer projection 已有类型字段，但真实
  内容和用户体验仍须 live 验证；所有 Chat/Quality/XD/Comparison/Preview verdict 保持不变。
