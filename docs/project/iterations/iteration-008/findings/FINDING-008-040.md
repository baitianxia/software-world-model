---
id: FINDING-008-040
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [quality, engineering, project]
depends_on: [ITER-008-SLICE-001, FINDING-008-020, FINDING-008-028, FINDING-008-039, ITER-008-VERIFICATION]
code: []
tests: []
iteration: ITER-008
classification: verification
disposition: mount-protected-historical-validation-inputs-with-clean-product-source
target: ITER-008-VERIFICATION
---

# FINDING-008-040：formal producer 必须区分干净产品源码与受保护历史验证输入

## Observation

`FINDING-008-039` 的测试修复提交 `3f4e4789adea9f0dfe7c754ea3d659e6d71c9c1f` / tree
`a7a38cc457e0a42223976566a0171fd98319f35f` 后，formal `run-009-freeze` 从纯 Git checkout 启动。focused 89/89 与
candidate-package 37/37 均 PASS，证明 hermetic freeze test 已修复；但 full discovery 只发现 1020 项，并出现 8 FAIL、25 ERROR
与 1 skip，未形成 report。外部模型调用为 0，grant、Web、hidden canary 与 Production Activation 均未执行。

缺失项不是产品源码，而是仓库有意忽略、由既有验证协议保护的本机输入：`validation-projects/` 下五个 exact nested Git repository，
以及 `var/iteration-003`、`var/iteration-007` 等历史 frozen evidence。对应测试会直接检查这些工程的 revision、prepared baseline、
旧 freeze 和 exact failure marker；纯 checkout 因而不是完整的 full-regression 执行面。

## Evidence and root cause

formal freeze 同时承担两种不同的完整性检查：

1. 产品候选必须来自 exact、tracked、clean Git source；`src/software_world_model` 与 `pyproject.toml` 被复制到独立
   `producer-source` 并重新形成 source commit/tree、candidate stage 和 manifest digest；
2. full regression 必须读取既有 accepted/failed-preserved 验证语料。它们按设计不进入产品 Git tree，但缺失时会让历史测试
   ERROR、skip 或改变总数，无法证明 `FINDING-008-020/028` 的 exact preserved hold。

run-009 把“tracked product cleanliness”误等同为“删除所有 ignored validation inputs”。这是 formal producer 装配问题，不是
产品、Qualification、Provider、模型或 `FINDING-008-039` 回归。后者已经在完全不含历史 `var/` 的纯 producer 中单项 1/1、
focused 89/89 PASS；不能用 full-suite 所需历史输入反向恢复 unit test 的隐式依赖。

## Decision and disposition

1. formal producer 的 tracked tree 必须绑定 exact commit/tree 且 `git status --short` clean；产品 source snapshot、candidate stage、
   launcher 与 Gateway input 仍只能由该 tracked source 产生；
2. full regression 同时挂载当前工作区已有的受保护 `var/` 与五个 `validation-projects/` nested repositories。它们只是历史测试输入，
   不进入 `producer-source`、candidate package 或产品 manifest，也不能修改产品 identity；
3. full regression 的 exact 1038 总数、4 FAIL + 1 ERROR identity/reason、其余 1033 PASS 和零新增 skip/error 是该挂载的机械
   完整性 Gate。缺失或漂移仍失败关闭，不新增 fallback；
4. run-009 保留为未形成 report 的失败 producer 尝试且不得复用。正确装配只能使用全新 `run-010-freeze` 路径；
5. 本 Finding 只写回 Iteration verification/producers 的执行语义，不改变 System Contract、产品代码、run-027 Qualification、
   hidden suite 或授权边界。

## Verification and closure

`run-010-freeze` 使用 exact tracked commit `3f4e4789adea9f0dfe7c754ea3d659e6d71c9c1f` / tree
`a7a38cc457e0a42223976566a0171fd98319f35f`，tracked status clean，并挂载上述受保护历史验证输入。正式 report status 为 PASS：

- focused 89/89、candidate-package 37/37、docs 与 unauthorized-prelisten PASS；
- full 1038 中 1033 PASS，只保留 `FINDING-008-020` 的 exact 4 FAIL + 1 ERROR，gate status
  `PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD`；
- external model dispatch、Git stage/commit/push 与 Production Activation 均为 `NOT_EXECUTED`；
- report / deterministic qualification / candidate-stage manifest digest 为
  `sha256:42281adee871a1924d9f05e9ec9b87596a12946d137029cc02df941280e1361a` /
  `sha256:96a96370ecf0b472b5aec82520a4709e10196db7db801f225aa66e57f6127876` /
  `sha256:ce4d635a9e6211f457b3f54ee6b24501b94a391bf97f46ca7fa85c0f6026886c`；
- source snapshot commit/tree/manifest 为 `e65691bef67ae6d6ff68dc41e61f4a3945607341` /
  `330a65055de6187bc3ceb096229be1c0a7098011` /
  `sha256:e1f4c4142bbb54b0f1e3fcaa07fbed2e0f92533829e84724a5cb4f5ccdeca247`；
- pending grant digest 为 `sha256:e3c9bed539fdfff0421fa49be39f0a49e339303fbfde97102751808c9301b082`，状态仍为
  `AWAITING_USER_AFTER_CODE_FREEZE` / `live_dispatch_authorized=false`。

因此 V-PRE-008 对 current candidate 的 formal freeze 已闭合，但这不是 Product Result。正式公开 Web 仍须取得晚于 exact freeze 的
用户授权；hidden canary、SLICE-002、Reflection 与 Production Activation 继续阻断。
