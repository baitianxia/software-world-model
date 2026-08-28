---
id: FINDING-010-158
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, interface, ai-infrastructure, operations, quality]
depends_on: [FINDING-010-156, FINDING-010-157, SYS-ADR-017, ITER-010-PDR-010]
code: [src/software_world_model/application_services/conversational_engineering_routing.py, src/software_world_model/application_services/__init__.py, src/software_world_model/interface/engineering_chat_provider_launcher.py, src/software_world_model/interface/engineering_chat_session_runtime.py, src/software_world_model/interface/engineering_chat_session_artifact.py]
tests: [tests/test_conversational_engineering_routing.py, tests/test_engineering_chat_provider_launcher.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_chat_alpha_cli.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: wire-a-narrow-trusted-owner-for-gateway-sealed-pre-http-unavailability
target: SYS-OPS-LOCAL-BROWSER
---

# FINDING-010-158：真实 launcher 未接入可用性 Owner，已密封的 TLS 前不可用证据无法形成回退判定

## Observation

`FINDING-010-157` 修复后，fresh `run-048` 在 DeepSeek admission 为 `DENIED_PRICING_CHECK` 时成功启动 preferred-only listener，证明备用
路线门禁不再阻塞 Ark。Browser 第一 Turn 随后创建 3 个 Ark model call receipt：前 2 个都完成 TLS、credential resolution 与 HTTP dispatch，
第三个在 credential resolution 和 HTTP 前的独立 TLS acquisition 失败。Gateway 将第三个 call 密封为 canonical
`PROVIDER_UNAVAILABLE`，Agent attempt 也准确传播同名 closed classification/code；Turn 仍以 fallback dispatch 0 失败关闭。

这不是“Ark 模型不可用”的证据。它只证明同一 Turn 的第三次独立连接在 HTTP 前遇到一次 TLS failure；同一 Turn 前两次 HTTP 已经成功。真正的
产品缺口是：通用 Router 为了安全仍默认使用 fail-closed availability boundary，而真实 Artifact launcher 没有显式组合一个受信 Owner。因此
已经由 Gateway 密封、且已知没有 HTTP outcome duplication risk 的 canonical evidence 不能形成 exact
`PREFERRED_EXECUTION_PROFILE_UNAVAILABLE` verdict。

## Evidence

- exact candidate `e547fa388fdada8e28067b5cce4d733bb536f1bf` / tree
  `9613102a5e86fccf14a2392540ee9395404992cb` 的 `run-048-mvp-experience` terminal receipt 为
  `STOPPED_AFTER_DISPATCH`，Conversation/Turn=`1/1`，Ark model dispatch receipt=3，DeepSeek dispatch=0，retry=0，human approval=0，
  Production Activation=`NOT_EXECUTED`。
- Ark transport audit 为 TLS attempt/success=`3/2`、pre-dispatch TLS failure=`1`、credential resolution=`2`、HTTP dispatch=`2`、
  post-dispatch unknown=`0`；DeepSeek authorization/TLS/credential/HTTP 均为 0。terminal internal digest 为
  `sha256:726d6af8c38b7db2809b2b572d70f9bc4338a0fc4e330ac6f359edfd130c649b`。
- 默认 Router 的 fail-closed boundary 正确阻止 raw failure 自行授权 fallback；缺口只存在于 real launcher composition，没有理由放宽
  Router、把 HTTP error/outcome unknown 升格，或再次按 Provider/model identity 写分支。

## Disposition

当前运维契约 `SYS-OPS-LOCAL-BROWSER` 增加唯一 current composition policy
`GATEWAY_SEALED_PRE_DISPATCH_UNAVAILABLE_ONLY@1`：

- Router 默认仍 fail closed；只有真实 launcher 显式注入独立 availability Owner。
- Owner 只接受 exact preferred attempt 上同时满足 closed `PROVIDER_UNAVAILABLE` classification、canonical
  `PROVIDER_UNAVAILABLE` Gateway failure code、至少一个 model dispatch receipt 的证据，并用 runtime injected aware clock 密封 exact
  profile/attempt verdict。
- raw transport reason（包括 `TLS_FAILURE`）、HTTP error、outcome unknown、结构化输出无效、Reviewer reject、无 model call receipt 的合成失败
  都不能形成 verdict；它们继续 fallback dispatch 0。
- verdict 只使 Router 创建一次隔离 fallback attempt；该 attempt 仍必须通过自己的 admission，denied admission 仍在 credential/TLS/HTTP 前
  失败关闭。因此 listener/Ark-only 不等待 DeepSeek，而真正选择 DeepSeek 时也不绕过它的硬门禁。

实现把 Owner 接入 provider launcher，并把同一 runtime clock 贯穿 Artifact Session，避免 verdict 时间与 launch/terminal audit 使用不同时间源。
正向测试证明 canonical pre-HTTP unavailable 只创建一个 fallback attempt；负向矩阵覆盖非 canonical unavailable code、HTTP error、outcome unknown
和零 dispatch/零 receipt。受影响的 routing/launcher/runtime/artifact/CLI 共 36 tests PASS，外部 Provider/network dispatch 0，full regression 0。
