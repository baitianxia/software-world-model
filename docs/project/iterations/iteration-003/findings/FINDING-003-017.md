---
id: FINDING-003-017
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-003-SLICE-001, FINDING-003-016, ITER-003-VERIFICATION]
code: [validation/product_holdout_iteration_002/direct_answer.py, validation/structure_world_model_iteration_003/questions/direct-baseline-protocol-1.0.1.json, validation/structure_world_model_iteration_003/v009]
tests: [tests/test_product_holdout_direct_answer.py, tests/test_iteration_003_validation_assets.py, tests/test_iteration_003_v009.py]
iteration: ITER-003
classification: iteration-design
disposition: add-exact-per-revision-source-closure-and-requalify-v009
target: ITER-003-SLICE-001
---

# FINDING-003-017：Direct baseline 无法表达移动 POM 的双 revision 完整覆盖

## Observation

第三轮 V-009 在 checkpoint `ce543190950d0ba8001117cadc02b25ebd34bd33` 上先取得 exact
Conformance PASS，再取得 closed CE 7 PASS、0 FAIL、0 UNKNOWN 与 PASS/VALID qualification。
在任何 baseline 模型请求发出前，运行前兼容性审计发现：冻结的 Direct 实现只把一个
`allowed_paths` 列表解释为“target revision 必须完整读取的全部路径”，而 frozen metamorphic
generator 会把一个 child module 的 POM 从 A 路径移动到 B 路径。

若 Direct task 传 A/B POM 路径并集，A-only 路径在 B 不存在，target 全读必然失败；若只传 B
路径，则 A 的完整源码覆盖不成立。`COMPARE` 只能补充 ordered diff，不能替代两个 revision 的
完整 POM read closure。该冲突不能由模型选择 action、增加重试或 baseline runner 参数解决。

## Evidence

- qualified input freeze：`ITER-003-V009-EXACT-INPUTS@1.0.2` /
  `sha256:f2355e8f681ef5bcf4ada645f741b1acae47d63d56b45f5bcc30342058ec5e3c`；
- Conformance binding：`sha256:a8735d10cdaa5598478694bb8bc4b50d2f8a3a3bdb56d4a51e4949d384281de3`；
- closed Result：`evaluation_result_0319e8c9c3254c92a59b89f9c32ac0c6` /
  `sha256:6d224aa435f47f3f8a522ac6ee54a4ed76890d77b4ec5049f33633c400899238`；
- qualification：`capability-evaluation:evaluation_result_0319e8c9c3254c92a59b89f9c32ac0c6` /
  `sha256:b08a555c77345e812a110f64f0aca1c2d9a7d23660aa4cc7170004cc21a040a1`；
- 原始证据目录：`var/iteration-003/v009/ce543190950d0ba8001117cadc02b25ebd34bd33/`；
- `generate_reactor.py` 明确把 `nodes_b[moved_index]["path"]` 改成新路径；旧
  `_source_coverage_view` 只为 target 与整个 `allowed_paths` 生成 required READ；
- 审计阶段没有发起 controlled Direct 或 mature Agent baseline 请求，没有可被挑选的 baseline
  success/failure。

## Impact and classification

该发现阻断 V-009 要求的真实比较基线，但不改变 System Contract 或产品 Oracle。它要求增强既有验证
实现和版本化 baseline protocol，并因 exact V-009 input drift 重新资格化，故分类为
`iteration-design`。第三轮 7/7 PASS 是真实且不可变的历史证据，但不能授权使用改变后的 Direct
baseline 输入。

## Decision and disposition

Direct task 保留 `allowed_paths` 作为 Source access union，同时允许 `source_policy` 使用
`LOCAL_GIT_REVISION_PATH_CLOSURE@1`，按 exact parent/target 分别列出必须完整读取的路径。执行器在首次
模型调用前验证 revision 顺序、每组非空唯一、全部路径属于 union，且各组 union 与
`allowed_paths` 精确相等；FINISH 前逐 revision/逐 path 验证从 byte 0 到 EOF，并对 ordered read set
继续要求 exact `COMPARE`。原 ITER-002 string policy 保持原 target-only 行为，避免破坏历史调用方。

Direct Strategy/Prompt 升为 `direct-source-answer-baseline@5` /
`product-holdout-direct-source-investigator@4`；新
`ITER-003-DIRECT-SOURCE-BASELINE@1.0.1` 显式冻结 per-revision closure、实现 raw digest 与 semantic
digest。新 `ITER-003-V009-EXACT-INPUTS@1.0.3` 必须绑定第三轮 PASS 及本 Finding。由于 baseline
protocol/implementation 属于 V-009 exact inputs，`@1.0.2` qualification 不可复用；必须从新 clean
checkpoint 完整重跑 Conformance 和全部七个 CE Case，之后才能运行任何 baseline。

## Verification after disposition

新增移动路径测试必须证明 parent old path、target new path 与 exact comparison 三项 closure 全部完成后
才允许 FINISH；原 string policy 测试继续通过。ITER-003 资产测试重新核对 protocol/ref/raw digest，
V-009 input verifier 重新绑定 semantic digest。运行聚焦测试、全量测试与文档检查后形成新 clean
checkpoint，再执行完整外部资格化。
