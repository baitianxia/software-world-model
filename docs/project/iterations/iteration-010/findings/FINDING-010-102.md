---
id: FINDING-010-102
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, source, ai, security, interface, operations, quality, project]
depends_on: [FINDING-010-101, SYS-ADR-017, SYS-ADR-018, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, SYS-OPS-LOCAL-BROWSER]
code: [src/software_world_model/interface/engineering_chat_session_runtime.py, src/software_world_model/interface/engineering_chat_provider_runtime.py, src/software_world_model/interface/engineering_chat_provider_launcher.py, src/software_world_model/interface/engineering_qa_source.py, src/software_world_model/interface/__init__.py, src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/application_services/conversational_engineering_tools.py, src/software_world_model/application_services/conversational_engineering_agent.py]
tests: [tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_provider_launcher.py, tests/test_conversational_engineering_tools.py, tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_routing.py, tests/test_engineering_qa_source.py, tests/test_engineering_chat_browser.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: non-starting-full-session-runtime-composition
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-102：Provider、Evidence 与 Browser 形成完整 Session runtime 本地组合候选

## Observation

`FINDING-010-101` 已证明两条生产 Provider model runtime 可接入 route，但 evidence tool factory 仍由测试调用者任意提供。若 fixed Session 只复用
一个有状态 Tool Adapter，失败 Ark attempt 的 locator/Ledger/progress state 会进入 DeepSeek；若每个 attempt 自行选择 World Model/Source
对象，又无法证明两条链消费同一 exact Cognition authority、Source Profile 和 repository revision。Response Control 也必须每 attempt fresh，
不能因为 Provider runtime 已预构建而共享一次性 Delivery 状态。

## Evidence

- 新 Session runtime 要求 Binding、Evidence Tool Configuration、World Model projector 的 read authority/source revision/binding、Source
  Broker/Worker 的 repository/binding/profile identity、Ark/DeepSeek runtime 的 zero-I/O preparation receipt 和 Route Plan 全部 exact 一致。
  两个 Provider 的 repository ref、transport 对象和 model boundary 必须 distinct；任一漂移在 attempt 创建前失败关闭。
- `EngineeringChatEvidenceToolFactory` 对每个 exact Provider Attempt Authority 只签发一个 fresh
  `EngineeringAgentEvidenceToolAdapter`。两个 adapter 共享受信只读 projector/Broker/Worker，但各自拥有独立 Turn Ledger、locator catalog、
  progress 与资源状态；因此 fallback 不接收 primary 中间态。Response Control factory 同样每 attempt 返回 fresh one-use sealed control。
- full Session composition 把上述 factory、生产 Provider runtimes、committed Work State repository、route、Conversation Service 和 Browser
  Application 接在一起。preparation receipt 明确是时间点快照；此时 artifact Session Config 未加载、attempt/tool 未创建、cognition 未投影、
  Source read、credential、Provider dispatch、listener 和 Production 全为 0/false/`NOT_EXECUTED`。
- 测试使用空临时目录上的真实 `LocalGitEvidenceClassProfile / SourceBroker / LocalGitRetrievalWorker` 与明确不可投影的 cognition port；preflight
  没有读取临时 Source。新增 Session composition 与 cognition drift 两例后，Agent/Conversation/Tools/Model/Route/Candidate/Launcher/
  Provider-runtime/Source-runtime/Browser/Access/Gateway 这 12 个相关模块的命令实际得到 `89/89 PASS`；相关 application/AI/interface `compileall`、
  `git diff --check` 与 current documentation `502/502` 同时通过。本次没有 mall Source/resources、外部网络、Provider/model、credential、
  listener/browser 或 Production Activation。

## Decision and disposition

- 实现状态增加 `SESSION_RUNTIME_COMPOSITION_LOCAL_CANDIDATE`。完整本地对象图已经闭合 attempt-scoped evidence/Response Control 与共享
  committed/read-only authority 的边界；不再由 fixed command 临时拼接这些状态所有者。
- 该组合接受已经构造的 runtime 对象，尚未实现或执行从 canonical private Session Configuration 加载 product/source Git identity、published
  World Model Bundle、两份 current sealed Conformance 与两个 private SQLite Gateway repositories；现有 `swm-engineering-chat` 仍是 Access-only。
- 下一最早缺口因此只剩 artifact Session Config loader + fixed command composition/launch receipt 的本地冻结。它完成前不请求
  Provider/browser live grant；Production Activation 仍不执行。
