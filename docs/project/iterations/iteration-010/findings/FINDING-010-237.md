---
id: FINDING-010-237
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [ai, operations, quality, project, security]
depends_on: [FINDING-010-236, ITER-010-PDR-008, ITER-010-PDR-012, ITER-010-VERIFICATION, SYS-CONTRACT-AI-MODEL-GATEWAY]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: individual-case
disposition: record-ark-request-envelope-and-actual-model-identity-drift-and-require-provider-restore-or-exact-human-delta-before-more-disclosure
target: ITER-010-VERIFICATION
---

# FINDING-010-237：Ark 当前拒绝 thinking，并把冻结 alias 解析为 glm-5.3

## Observation and execution evidence

在 `FINDING-010-236` 的 exact committed implementation identity
`2b7fe76524b3cd3856e08b457d466e95cebca583 / 6f0e1215bd93842f6759bd03bf4310e0d0103c49` 上，fresh Ark
Conformance `ccrun_27769cd6a2b045f3a3292c8595ba162c` 使用 current full qualified envelope 发出 1 个无源码 canary request。verified
TLS、credential resolution 和 HTTP dispatch 均为 1，Ark 返回 400 `InvalidParameter / BadRequest`，request ID
`02178817042822191b94d62e219899eaebadcce7b395a23d3d2c7`；新 optional `provider_error_parameter` 为空，证明 Provider response 没有提供可安全
投影的 `error.param`。result/file digest 分别为
`sha256:ca97f347d849eb6e2b1b6fedca36632375d236925ca2ac5f74f6a461f04d0e33` 与
`1b71f6cc65848f444e97c2788f21d75d73a3431be055791b5054c43808c41803`。

随后只对同一 Conformance canary 做受控、临时、未提交的 top-level field differential；每个 variant 都是新的 request identity、零 retry，且
只包含 schema instruction/canary，不包含 mall Source、冻结问题、Conversation Context 或用户数据：

1. 只移除 `response_format`、保留 `thinking={"type":"disabled"}` 时，`ccrun_f93453f21fe34b958ccf5d242eb36497` 仍为同一
   HTTP 400 signature，request ID `021788170599034ed95513e461b85a83ff8b942ff8c8617d36f93`；result/file digest 为
   `sha256:cc31bbd0cf65891d1c1cd2d5cb48b05cf3bfdd66cf3f735c313b85727b562f4a` / 
   `6cec88aef6783e158a95be46c191b042d1d9686d87db25cb04725c32a480242a`；
2. 恢复 `response_format`、只移除 `thinking` 时，`ccrun_785c3d950b9140369dd3b4c2ec6c10b1` 已越过 HTTP parameter validation，得到
   1 个 Provider HTTP response；其内容未通过 closed JSON output validator，故准确密封 `STRUCTURED_OUTPUT_INVALID` 而不颁发资格。该
   one-field differential 把 400 的直接 request-field divergence 定位到 `thinking`。result/file digest 为
   `sha256:24eac2a5e490b042307184d7c337ca890c183cead0adf2e4f4f0de26de756954` / 
   `8b72a4005c8f27f91b1326b8da1768659e9d52b16cb76d981597922955627c30`；
3. 进一步缩到 `model + messages` 的官方兼容最小形状后，`ccrun_7bd73e2d9a9c482688c61b5ed2384447` 的 2 个 TLS/credential/HTTP call
   都完成、Usage 完整且 closed JSON 有效；但两个 response 都报告 actual model fingerprint `glm-5.3`，而冻结 requested alias 仍是
   `glm-5-2-260617`、expected actual fingerprint 是 `glm-5.2`。request ID 为
   `0217881706590224f08adabc2a0b7ee0ad3a2fcb671c8c4c5d9b4` 与
   `021788170664295006c460d0b2d36d003716bcb3522c0d1b62a19`；input/output tokens 为 `334/210`，result/file digest 为
   `sha256:cca407f1a77cb6beb68a0cec7f6afb68be72a8ea919fae42b57bcd47f6717875` / 
   `0e0607db6488884955e1bffe58b77e6085e798fe9b19fa852a54ea76980e3bdf`。

全部临时 differential 已用 exact patch 反向恢复；worktree 回到 committed full envelope，未把诊断 variant 变成产品 request contract。四个
Conformance run 合计 5 个独立 Ark HTTP dispatch、retry 0、Source/user-question disclosure 0、Production 0。

## Decision and disposition

1. run-107 的重复 400 不再归因于 mall payload、问题长度或 Conversation：fresh minimal canary 也复现 full-envelope 400；one-field
   differential 又证明 current resolved model 不接受冻结的 `thinking` field。
2. 更早且更强的边界是 actual model identity drift。standing authority、Ark execution profile 与既有 Conformance 精确冻结
   `requested alias glm-5-2-260617 → actual glm-5.2`；Provider 当前却返回 `glm-5.3`。按 Model Gateway exact-identity contract，不能通过放宽
   fingerprint、删字段或沿用旧资格继续向该模型披露冻结问题和源码。
3. `FINDING-010-236` 的安全 parameter-name evidence 仍是有效通用 contract repair，并已证明 Provider 未给出该可选字段；其代码/文档处置
   完成，但不授予 Ark 新 identity 资格。
4. 下一外部产品 dispatch 需要二选一的 material state change：Provider 把该 exact alias 恢复为 actual `glm-5.2`，然后 fresh Conformance；或
   用户明确批准把 preferred execution profile/standing disclosure scope 更新到 actual `glm-5.3`，随后重新冻结 request contract、fresh
   Conformance 和相应 Capability qualification。获得其中之一前，只停止 Ark/DeepSeek 外调；本地文档、测试和证据闭合继续，run-108 不创建。
