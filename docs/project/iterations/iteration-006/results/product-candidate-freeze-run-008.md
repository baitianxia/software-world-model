---
id: ITER-006-RESULT-PRODUCT-CANDIDATE-FREEZE-RUN-008
kind: iteration-result
status: candidate-frozen-historical-subsequent-live-pass
authority: execution-evidence
owners: [engineering, quality, security]
depends_on: [ITER-006-RESULT-LIVE-RUN-007, ITER-006-RESULT-JAVA-CAPABILITY-RUN-002, FINDING-006-012]
code: [validation/structure_world_model_iteration_006/live_freeze.py, validation/structure_world_model_iteration_006/live_comparison.py, validation/structure_world_model_iteration_006/live_evaluator.py, validation/structure_world_model_iteration_006/live_product_probe.py, src/software_world_model/interface/world_model_runtime_assets/gateway_authorized_workload.py]
tests: [tests/test_world_model_gateway_authorization.py, tests]
iteration: ITER-006
---

# ITER-006 Product Candidate Freeze run-008

## Decision

run-007 的 wrapper digest 冲突修复后，`run-008` 已重新冻结产品 subject、六题 held-out suite、三路协议与 role package，并通过
全部 zero-provider Gate：deterministic probe、56 项 focused、18 项 candidate Answer package、836 项 full regression、docs、
未授权 pre-dispatch 与 pre-listen 均 PASS。

这是新候选，不追溯改变 run-007 FAIL，也未得到外部分派授权。`live_dispatch_authorized=false`、
`external_model_called=false`；没有 Ark/Codex 产品任务，没有源码披露。Production Activation 与 Git stage/commit/push 均未执行。

该段是 freeze 时点事实。用户随后提交独立 exact 授权，[Live run-008](live-run-008.md) 已三路各 6/6、comparison PASS；freeze
自身仍保持 zero-provider evidence，不追溯写成 live run。

## Exact subject and suite

- producer commit/tree：`c4d3d4be48e778a8380ba321dd37058f382d5d32` /
  `8cc1177bba3ffb7a1d862c412fa6d0161fadbde6`；
- producer source manifest：
  `sha256:d362a5aaee7ee157f5b1d35131a0fb325bdb8b48b836084b316329e8727c3ab5`；
- protected candidate stage：
  `sha256:862fdb8d91006555d6b6f40a9ca4d7a520871dfa3baea248f1f4b02ef6de213b`；
- launcher manifest：
  `sha256:4318cb502cc38e289f2d2de0634f5623310a5ec1f2b28ccbca71d708c1c7882a`；
- held-out suite：
  `sha256:0793db736409191f729cce70d19c31cfffc9e398d0dae4dd822c1ab629db4a38`；
- independent evaluator：
  `sha256:bb972939badfbebf8f0f3365e86a0ffc841bf70b38466f247f3aad383bbb7e03`；
- comparison runner：
  `sha256:d35cf82381d736c6a9255cd3b58e0a89521ccd4b194eeb35d1868a4de5082440`；
- deterministic qualification：
  `sha256:30102725badcf0471fbc1f6acdab9cc0a213b131691d1887bbdf832fc62dd473`；
- freeze report：
  `sha256:a036921cfa5873ad55e578c32309664479f84570ea547362942a3845e02a1ae4`。

suite raw SHA-256 为 `aac5a59e…`，report raw SHA-256 为 `021bf21b…`。suite 在 World Model result count 为 0 时密封，继续覆盖
method inventory、direct call、positive path、supported negative path、ordered diff 与 runtime Knowledge Gap；随机 suffix 为
`90febd94`，R1/R2 revision 为 `40890473…` / `e5a6e3ad…`。

## Remediation and qualification binding

授权 Gateway wrapper 的 source 与 protected stage entrypoint raw SHA-256 均为
`ca853a9ab6cc0d9c84dc9549e977590eb1aae7deae3292f4eef47752f8d078d6`。新增 Java baseline regression 证明 wrapper 只对最终
visible core 形成外层 seal，不再把被包装 baseline 的同名 digest 作为隐藏 hash input。完整回归从 run-007 的 835 增至 836，
全部 PASS。

候选继续精确绑定 capability proof `sha256:65d18436…`、closed Result `sha256:e6d39d16…`、Ark conformance
`sha256:c86aad99…` 与 Java Gateway freeze `sha256:c1d54d18…`。qualification loader 独立复验有效期至
`2026-08-19T07:10:03.636096Z`；到期或任何 subject/policy drift 必须失败关闭。

deterministic qualification 明确记录 `external_model_called=false`、full 836/836 PASS、comparison `NOT_AUTHORIZED` 与 Production
Activation `NOT_EXECUTED`。拒绝探针后 `blocked-comparison`、`blocked-session`、`blocked-sockets` 均不存在。

## Authorization boundary

- pending comparison authorization：
  `sha256:a89cba779fa537a0317d495bdc6d06a93b5661d247a11548768bfbb49c0d03fe`；
- disclosure set：
  `sha256:1ffb8aa61cd50e20bb2f0658ef96812283c08e57ffaa9979d45b32724860281c`；
- pending evaluation grant：
  `sha256:f8f9fe6ef9e1993b4f656960b08e56e8509dfcaa7288bfa8ea6d5629438575f7`，
  `live_dispatch_authorized=false`。

后续授权必须精确绑定本 freeze report、suite 与 disclosure set，仍限六题每题每路一次、controller 无 retry：World Model 向
Ark 只发送 original question + no-payload published Structure；controlled Direct 向 Ark、Mature Source Agent 向 OpenAI Codex
分别发送 original question + exact sealed Java source closure。该条件后来由 run-008 exact 授权满足并已消费；没有 Evidence
payload、Oracle、Production Activation、提交或推送，run-003、capability 与 run-007 授权均未复用。
