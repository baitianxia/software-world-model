---
id: FINDING-010-099
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai, security, interface, quality, project]
depends_on: [FINDING-010-098, SYS-ADR-017, SYS-ADR-018, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/model_gateway.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py, src/software_world_model/ai_infrastructure/__init__.py, src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/application_services/engineering_conversation.py, src/software_world_model/application_services/__init__.py, src/software_world_model/interface/engineering_chat_candidate.py, src/software_world_model/interface/engineering_chat_browser.py, src/software_world_model/interface/__init__.py]
tests: [tests/test_model_gateway.py, tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_agent.py, tests/test_engineering_chat_candidate.py, tests/test_engineering_conversation.py, tests/test_engineering_chat_browser.py, tests/test_engineering_chat_alpha_cli.py, tests/test_conversational_engineering_tools.py, tests/test_engineering_qa_source.py, tests/test_engineering_qa_browser.py, tests/test_engineering_qa_alpha_cli.py]
iteration: ITER-010
classification: verification
scope: systemic
disposition: model-boundary-local-candidate
target: ITER-010-VERIFICATION
---

# FINDING-010-099：主 Agent/Reviewer 模型边界与非调度启动预检形成本地候选

## Observation

`FINDING-010-097/098` 已闭合 Application-owned Agent loop 与 trusted evidence tools，但 fake Agent/Reviewer 输出没有可由 Application
重算的 Gateway dispatch receipt，因而不能区分 Provider 前拒绝、已 dispatch 后拒绝、outcome unknown 与 repository replay。已有
Model Gateway 也只有 `invoke`，产品若想在 listener 前验证 Adapter/Manifest 会同时进入调用准备边界。另一个可用性缺口是主 Agent 只收到
操作名称，没有收到 `query / evidence_class / locator_reference` 的 exact proposal contract。

## Evidence

- 主 Agent 与 independent Reviewer 现在使用两个独立 no-tools Prompt、closed input/output Schema 和 exact model configuration。Provider
  输出不允许提交 `model_call_ref`；可信 Adapter 只接受 closed output，再把 Gateway 的 call identity 注入 typed proposal，Application
  要求成功 proposal 与 exact role receipt 一致。
- Session Disclosure Authority 绑定 exact product candidate、Chat Binding、Provider configuration、Prompt/output contract、两个角色、
  有效期和 Turn/per-Turn/session fuse。每次角色调用再密封完整输入 digest、逐 leaf path/fragment digest、字节数、Gateway Manifest、
  Provider/model/endpoint/configuration/qualification、redaction 与 one-use authorization；session authority 本身标为 `NOT_PROVIDED`，
  credential reference 不进入模型消息。
- Model Gateway 新增纯 `preflight`：只重验 Adapter、isolation capability、Context 和可渲染 Manifest，不 prepare call、不 dispatch、也不解析
  Secret。角色 policy 在实际 `invoke` 时先消费 exact one-use authorization，再通过 Gateway preflight；失败后同输入不得重试。
- Application 现在以 typed receipt 计数：确定可知的 pre-dispatch rejection 与 repository replay 计 0；fresh dispatched completion/rejection/
  outcome unknown 计 1；角色错绑保留真实 receipt/count 但 Turn 以 protocol violation 失败关闭。Conversation Turn 与 Browser developer view
  保存 receipt digest reference，`retry_count` 继续固定为 0。
- 主 Agent sealed input 明确把 Conversation/先前 Answer 标为 context-only、不是 Source truth，并投影每个当前允许操作的 exact 参数名；
  `SOURCE_READ` 只能提交先前本 Turn Observation 返回的 opaque locator，path 明确禁止。Reviewer 输入只含 current Turn、relevant
  Conversation Context、Work State、Package 与 Draft，不含工具目录或工具权限。
- 使用真实本地 `ModelGateway + SQLite repository + OFFLINE_FIXTURE Adapter` 的测试实际越过一次本地 Adapter boundary，并证明 offline
  output 即使 schema 合法也不能取得 live eligibility；binding drift 在 Gateway dispatch 前计 0，outcome unknown 计 1 且 retry 0。
  成功 decode 只由纯 closed decoder fixture 验证，未伪称真实 Provider 成功。
- 新 `engineering_chat_candidate` preflight 只接受调用者已解析并密封的 product commit/tree、ready Chat Binding、evidence-tool
  configuration、单 Provider configuration 与 Session Disclosure Authority；它不读取 Git/worktree、Source 或 credential，不启动
  listener，也不调用 Gateway。receipt 固定 `ready_for_live=false`，并列出 `ARK_DEEPSEEK_FALLBACK_NOT_INTEGRATED`、
  `FIXED_PROVIDER_LAUNCHER_NOT_WIRED`、`LIVE_PROVIDER_AND_BROWSER_NOT_EXECUTED` 三个阻断项。
- 定向命令
  `PYTHONPATH=src:. python3 -m unittest tests.test_conversational_engineering_model tests.test_engineering_chat_candidate tests.test_model_gateway tests.test_conversational_engineering_agent tests.test_engineering_conversation tests.test_engineering_chat_browser tests.test_engineering_chat_alpha_cli tests.test_conversational_engineering_tools tests.test_engineering_qa_source tests.test_engineering_qa_browser tests.test_engineering_qa_alpha_cli -q`
  实际得到 `86/86 PASS`；相关 `py_compile` 与 `git diff --check` 同时通过。本次没有外部网络、Provider/model、listener/browser、mall
  Source/resources、credential 或 Production Activation。

## Decision and disposition

- 当前实现状态增加 `MODEL_BOUNDARY_LOCAL_CANDIDATE`：单 Provider 下主 Agent/Reviewer 的 sealed input、Disclosure、Gateway receipt、closed
  decode、失败真实性和非调度启动预检已有本地确定性证据。这不是 Ark 或 DeepSeek 当前资格、真实答案或 live Chat 证据。
- ADR-017 的 `VOLCENGINE_ARK → DEEPSEEK` session route、两个完全隔离的 full-chain attempt、eligible terminal classification、late primary
  quarantine 与 logical Turn 汇总仍为 `NOT_INTEGRATED / NOT_QUALIFIED`。固定 `swm-engineering-chat` 继续保持已验证的 Access-only
  launcher；candidate preflight 不会也不能把它切换成 Provider-ready。
- Citation browser projection、真实 Provider adapter/transport composition、clean fixed launcher freeze、五轮 mall Chat 与新 Conversation
  live probe 仍为 `NOT_LIVE / NOT_RUN`。所有 Chat/Quality/XD/Comparison/Preview verdict 保持不变；下一最早编码缺口是双 route/fallback
  isolation 与 fixed launcher wiring，随后才可形成 exact live grant 请求。
