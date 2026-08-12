---
id: FINDING-005-005
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-005-SLICE-002, FINDING-005-002]
code: [src/software_world_model/interface/world_model_runtime.py]
tests: [tests/test_world_model_http.py]
iteration: ITER-005
classification: iteration-design
disposition: separate-candidate-evaluation-grant-from-post-run-product-acceptance
target: ITER-005-SLICE-002
---

# FINDING-005-005：候选 launcher 要求先有自身 Product PASS Result

## Observation

首版 evaluation grant 把已接受 `batch-result` 和 `product-evaluation` 设为启动必需输入。`FINDING-005-003/004` 改变
Answer/Gateway active bytes 后，新候选必须通过 V-007/V-009 才能产生这些 Product Result；若启动前又要求它们已经存在，
候选永远无法进入第一次受控 Product Validation，形成与 `FINDING-005-002` 同类的循环门禁。

## Evidence

- Product Result 只能在 exact candidate package、launcher、Catalog、Bundle 与 Provider subject 上执行后产生；
- 旧 ITER-003 Product Result 绑定旧 commit/tree/package 和 mall 数据，不能重标为新候选 PASS；
- 伪造零运行 batch 或把确定性单测命名为 Product Evaluation 会混淆 Test、Product Validation 与 Acceptance；
- pre-listen 所需的非循环证据实际是 exact candidate provenance、deterministic qualification、held-out suite、independent
  evaluator、Provider qualification、OS preflight 以及当前 disclosure authorization。

## Impact and classification

问题不改变 System 的测试/验证/接受分层，而是本 Slice 把 post-run acceptance evidence 错放到 pre-run grant，分类为
`iteration-design`。

## Decision and disposition

evaluation grant 升级为 `SWM-WORLD-MODEL-EVALUATION-GRANT@2`：

- subject 明确标记 `CANDIDATE`，页面和 health 不再使用 `accepted product` 字样；
- 启动前验证 exact commit/tree/stage、role entrypoints、launcher files、deterministic qualification、在任何 World Model Result
  前密封的 held-out suite、independent evaluator、Provider subject 和当前 disclosure receipt；
- deterministic qualification 必须证明 focused/full/docs 全部 PASS、external model 未调用、Production Activation 未执行；
- Product batch、三路径对照和人工浏览器结果由本次授权运行产生，随后才能支持 SLICE/Iteration Acceptance，不能作为首次运行
  的先验输入。

## Verification after disposition

未授权 grant 仍在 session 创建、Provider socket 和监听前失败；exact @2 grant 的完整正向启动与外部 Product Result 等待单独
披露授权，由 V-007/V-009 闭合。
