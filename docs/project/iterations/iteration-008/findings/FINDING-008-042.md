---
id: FINDING-008-042
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [quality, engineering, project]
depends_on: [ITER-008-SLICE-001, FINDING-008-040, FINDING-008-041, ITER-008-VERIFICATION]
code: []
tests: [tests/test_product_holdout_manifest.py, tests/test_product_holdout_cli.py, tests/test_iteration_008_slice1_freeze.py]
iteration: ITER-008
classification: verification
disposition: materialize-sealed-validation-checkouts-inside-clean-producer
target: ITER-008-VERIFICATION
---

# FINDING-008-042：sealed validation checkout 必须真实位于 clean producer 内

## Observation

run-028 资格证据写回提交 `b0f8ce835d8cbfbe5330513115e651691da7621b` / tree
`f502dd492fc1438737cb118e2375e261e23bd0d9` 后，formal `run-011-freeze` 从该 clean tracked tree 启动。产品 source、
candidate package、Capability/Conformance authority chain 与 focused Gate 均成功；但 full regression 拒绝形成 report，报
`full regression differs from the exact preserved historical hold`。外部模型、Web、credential、hidden canary 与 Production
Activation 均未执行。

诊断重放仍包含 `FINDING-008-020` 的 exact 4 FAIL + 1 ERROR，同时新增：

- `test_product_holdout_manifest.ProductHoldoutManifestTests.test_local_validation_checkouts_match_the_sealed_suite` ERROR；
- `test_product_holdout_cli.ProductHoldoutCliTests.test_verify_inputs_command_is_offline_and_reports_sealed_counts` FAIL。

因此 run-011 的问题不是旧 hold marker 漂移，也不是产品、Provider 或 run-028 Qualification 失败，而是 formal producer 的验证输入
装配仍不完整。

## Evidence and root cause

run-011 把五个 ignored nested Git repository 作为 symlink 放入 clean workspace。文件可读、Git revision 也正确，但 sealed checkout
验证先 `resolve()` canonical path，再要求 repository 位于本次 workspace root 内；symlink 因此解析回原工作区并被正确拒绝为
`sealed repository checkout is missing or outside the workspace`。把它们改为本地 clone 后，revision 已正确，但 clone 的默认
`origin` 指向本机源路径，又被下一层 exact remote identity Gate 拒绝。

将五个 repository 真实 materialize 到 producer 的 `validation-projects/`，并恢复 sealed canonical remote 后，新增两项定向
`2/2 PASS`。五个 exact revision / remote 为：

| Repository | Revision | Remote |
|---|---|---|
| gson | `310ac341f2f92a454b229bf21f70d2d18b2b6db7` | `https://github.com/google/gson.git` |
| mall | `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` | `https://github.com/macrozheng/mall.git` |
| maven-wrapper | `62c6a95364ea44243b6c30a17ee793fce067a4c2` | `https://github.com/apache/maven-wrapper.git` |
| poi-tl | `58fdb6c7d9db7da53cd420ff1ebde49813bd7af2` | `https://github.com/Sayi/poi-tl.git` |
| transmittable-thread-local | `9c6552bbd7eda52b7bfb03c24c4f9aee514e91f3` | `https://github.com/alibaba/transmittable-thread-local.git` |

这属于 `FINDING-008-040` 所定义 protected validation corpus 的 containment/identity 细化；不是把验证仓库加入产品 source、
candidate stage 或 qualification identity。

## Decision and disposition

1. formal producer 的主仓库仍必须是 exact tracked commit/tree 且 `git status --porcelain --untracked-files=all` clean；
2. sealed nested repository 不能用解析到 workspace 外的 symlink。必须在 clean workspace 的 ignored `validation-projects/` 下真实
   materialize，并同时匹配 exact revision、canonical remote identity 与 clean nested status；
3. 历史 `var/` 与 nested repositories 仍只服务 full regression，不进入 `producer-source`、candidate stage、launcher、Gateway
   input 或产品 manifest；
4. run-011 保留为没有 report 的 failed producer attempt，不复用其目录。正确装配只能创建全新 run-012；
5. 该 Finding 主处置到 `ITER-008-VERIFICATION`，不改变 System Contract、产品实现、run-028 Qualification、hidden suite 或
   Activation 边界。

## Verification and closure

全新 run-012 使用同一 clean tracked commit/tree，并在 producer 内 materialize 上述五个 sealed checkout。formal report status
为 PASS：

- focused 89/89、candidate-package 37/37、docs 与 unauthorized-prelisten PASS；
- full 1039 中 1034 PASS，只保留 `FINDING-008-020` 的 exact 4 FAIL + 1 ERROR，gate status 为
  `PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD`；
- report / deterministic qualification / candidate-stage digest 为
  `sha256:aada406ea647980993515a6a2f2c77c34efe63b4bdd21b636f1597018b294a5a` /
  `sha256:0dbb2e8eb805ba855264a638dd2a8295bc25189a00c3467b6993398c6e39fce6` /
  `sha256:7484be1bf2e4f0023991a4e058e3c9ae1cf61e69bda205d55864e5c9b2400a97`；
- source snapshot commit/tree/manifest 为 `03fa8603c0693ab7b22be12ad4abbbc0e40b146d` /
  `7098432f53d0baed12ff8a91cfb88853ddcc9a83` /
  `sha256:37daf84db6b5657d5e058ca06b1873f16c696dc4c95d39e67c6aac7f8a482a3c`；
- run-028 Capability/closed/Conformance digest 被精确绑定为 `sha256:0880bb0d…eb6` / `sha256:4aa86b5c…db4b` /
  `sha256:5dffdf36…b5dd7`；Gateway freeze/permission digest 为 `sha256:13e4f761…582a` / `sha256:ae6317a9…62ef`；
- external model dispatch、Git publish、hidden canary 与 Production Activation 均为 `NOT_EXECUTED`。

pending evaluation grant digest 为 `sha256:5cb184368da3e62c1b0f19495e275f6913ccd271ecfdd8a270ebad02aa9a9370`，状态仍为
`live_dispatch_authorized=false / AWAITING_USER_AFTER_CODE_FREEZE`。因此 V-PRE-008 对 current candidate 再次 PASS，但这不是
Product Result；正式公开 Web 必须取得晚于 exact run-012 freeze 的新用户授权，V-003/V-WEB-001 继续 blocking。
