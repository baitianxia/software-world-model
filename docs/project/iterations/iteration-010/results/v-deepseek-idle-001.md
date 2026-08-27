---
id: ITER-010-RESULT-V-DEEPSEEK-IDLE-001
kind: iteration-result
status: passed-local-dispatch-admission
authority: execution-evidence
owners: [operations, ai, interface, quality, project]
depends_on: [ITER-010-PDR-007, FINDING-010-139, SYS-ADR-017, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-OPS-CONFIGURATION, SYS-QUALITY-SECURITY]
code: [src/software_world_model/application_services/deepseek_dispatch_admission.py, src/software_world_model/interface/engineering_chat_provider_runtime.py, src/software_world_model/interface/engineering_chat_session_artifact.py, src/software_world_model/interface/engineering_chat_alpha_cli.py]
tests: [tests/test_deepseek_dispatch_admission.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_chat_alpha_cli.py]
iteration: ITER-010
case_id: V-DEEPSEEK-IDLE-001
case_verdict: PASS
external_model_calls: 0
credential_resolutions: 0
tls_attempts: 0
http_dispatches: 0
acceptance: NOT_ACCEPTANCE
production_activation: NOT_EXECUTED
---

# ITER-010 V-DEEPSEEK-IDLE-001 本地调用准入 Result

## Verdict

`V-DEEPSEEK-IDLE-001: PASS / local-dispatch-admission-only`。planned DeepSeek run 现在必须在任何 credential、TLS、Provider
socket/connected descriptor 或 HTTP 工作前密封 `DEEPSEEK_DISPATCH_ADMISSION@1`；每个 exact execution envelope 在 Gateway
preflight 与实际 invoke 边界分别重验同一收据、当前窗口或 exact peak override、run/session/provider/model identity 以及剩余
call/input-token/output-token/duration 上限。缺少门禁、价格检查过期或变化、窗口关闭、identity 漂移、预算耗尽或 override 越界均失败关闭。

本 Case 只证明本地机械门禁。它没有执行 Provider/model、credential、TLS、listener、Browser 或 Source，也没有把
`run-043` 的调度/质量 FAIL 改判为 PASS。后继 direction canary 仍必须使用新的 exact one-shot external grant，并在允许窗口内形成新的
`@3` Session、fresh 官方价格检查、launch/terminal 和逐 dispatch receipt；普通 canary/fallback grant 仍不包含峰时 override。

## Exact implementation binding

- 调度门禁提交：`03520eb2b01e16116b3419dd5f1aa562e96cd21c`，tree
  `9a73b04641e681ab6d9a9e3499b36d6f831c1a3c`；
- 集成 F138 语义查询修复的 clean successor：`3a6089fa0ff1d5df88f43199ae77ae4c4ecc6f19`，tree
  `b1fd51bb533c8ff393dc42b6864a08e5c94929c0`，worktree
  `/private/tmp/swm-iter010-successor.TEGSIi/candidate`；
- current Artifact Session schema 为 `SWM-ENGINEERING-CHAT-ARTIFACT-SESSION-CONFIG@3`。`@3` 在 `@2` 多 Profile identity 上新增
  closed `deepseek_dispatch_admission`；`@1/@2` 仍可读取历史记录，但 current preparation 在缺少 admission 时失败关闭；
- Agent Strategy/Prompt/Primary Input 的 successor identity 为
  `conversational-engineering-agent@8 / conversational-engineering-agent-no-tools-prompt@8 / ENGINEERING_AGENT_PRIMARY_INPUT@8`；
  Reviewer identity 保持 `ENGINEERING_AGENT_REVIEW_INPUT@2`。这些领域 identity 变化不冒充 Provider Conformance。

## Deterministic gate evidence

| Requirement | Local evidence | Verdict |
|---|---|---|
| 半开窗口边界 | `08:59:59` allow、`09:00:00` deny、`12:00:00` allow、`14:00:00` deny、`18:00:00` allow；非零 duration 还要求 `now + worst_case_duration <= window_end` | PASS |
| 峰时失败关闭 | 北京时间 `11:19` 无 override 时 receipt 为 `DENIED_PEAK_WINDOW`；真实 Provider runtime preflight 的 credential/TLS/HTTP 均为 0 | PASS |
| exact override | run、Turn scope、product/source/session、provider configuration、model、time、call/token/duration 任一越界均不取得准入 | PASS |
| 逐 request 重验 | 窗口关闭后不能创建新 request；相同 envelope 只能以相同预算复用 authorization，实际 invoke 只能一次 | PASS |
| 同一收据与预算 | 每个 invoked envelope 回指同一 admission receipt；累计 call/input/output reservation 超限失败关闭 | PASS |
| 官方检查 | 只接受冻结官方 URL、15 分钟内的 digest/summary/status；缺失、过期或 `CHANGED` 失败关闭 | PASS |
| Artifact/CLI | `@3` closed loader 绑定 admission；prepare 不做网络/credential；denied receipt 在固定 loopback listener 启动前关闭 | PASS |
| terminal audit | DeepSeek Gateway request/authorization、admitted/invoked envelope、transport dispatch 与同一 receipt 对账；缺失或漂移失败关闭 | PASS |

## Verification scope

clean successor 上与门禁、Session、Agent/World Model 及相邻 route/launcher 相关的 10 个 unittest module 共 `78` 项通过。另以
run-043 的真实双 Profile artifact 做零外部调用诊断：登录问题命中 `UmsAdminServiceImpl.login`；两个未参与修复的异质问题分别命中
`mall-portal -> mall-security/mall-mbg` 和
`PmsProductServiceImpl.handleUpdateSkuStockList/handleSkuStockCode`。这组诊断只读取已发布 World Model bundle，没有 query-time Source read。

按 PDR-005/PDR-006/PDR-007，本阶段没有运行 full regression；这不是 Acceptance 证据。ITER-010 仍为
`REWORK / NOT_ACCEPTED`，`V-CHAT-EXPERIENCE-001 / V-CHAT-001 / V-CHAT-QUALITY-001 / V-CHAT-XD-001` 仍需一个新授权、合规窗口内的后继
canary 才能重新裁决。
