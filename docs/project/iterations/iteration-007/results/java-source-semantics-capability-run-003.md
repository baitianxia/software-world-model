---
id: ITER-007-RESULT-JAVA-SOURCE-SEMANTICS-CAPABILITY-RUN-003
kind: iteration-result
status: capability-qualified
authority: execution-evidence
owners: [engineering, quality, security]
depends_on: [ITER-007-VERIFICATION, ITER-007-SLICE-001, FINDING-007-005]
code: [src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, src/software_world_model/ai_infrastructure/java_source_semantics_model_egress_policy.json, validation/structure_world_model_iteration_007/capability]
tests: [tests/test_world_model_answer_strategy.py, tests/test_iteration_007_capability_qualification.py, tests/test_model_egress_gateway.py, tests]
iteration: ITER-007
---

# ITER-007 Java Source Semantics Capability Qualification run-003

## Decision

run-003 对 contract/Strategy `1.2.2`、Prompt `@3`、vocabulary `@3` 的 12 个 closed synthetic capability case 取得
**12/12 `PASS_VALID`**。执行器发出恰好 12 次 Provider request，每例一次、无 retry；failure/unknown 均为 0，实际模型指纹为
`glm-5.2`。该资格允许构建 SLICE-001 正式产品候选，但不等于产品 Web、用户现场问题或隐藏 canary 已通过。

## Frozen identity and authorization

- freeze document digest：
  `sha256:ae597aa59c6ca663ea6a93d1abf55ca3d6c77ef0c6b2eaaa120a15dd6bbca4bf`；
- suite digest：
  `sha256:f6a38dc1357dfdb895d6ad02121705190f5fad32c869862c131e08633c170965`；
- Oracle digest：
  `sha256:e07d06639b39f7daf05a5c8e8728f79a0028c155eeb6016dfac46317d47abe56`；
- exact post-freeze authorization document digest：
  `sha256:ddd102d3c789ea3afc9260cf7716ac5b699d68b6a196e866437a86d1ab1fb8aa`；
- authorization message digest：
  `sha256:ec6f1dc61b2d1787129b1ed5d389f083f437c76d4bec1b79e8a18d80f9106570`；
- authorization 已消费，不能复用；Production Activation 与 Git stage/commit/push 均未执行。

## Closed result

- result id：`evaluation_result_72dab3cd81e64a8c90860a1260d565f8`；
- result digest：
  `sha256:2223ceefbbfc8a775b58b228c0c3f8be7b56fc341e343ddb14577a55ec25f8c2`；
- closed result document digest：
  `sha256:3b0a6eca360f00fa41e1db86ce13c5e43e3d1e098c4d6c214bfc726484f1825f`；
- capability qualification digest：
  `sha256:f7466141339ba78de31393126fb33e1ba903456fb7e340530e1954e0213d1a41`；
- qualification proof document digest：
  `sha256:73164a934cc2c3178ac34fd785bf24c8e41ba9ff1f5016e8bba15663418eb113`；
- validity：`VALID`，由本次 frozen dependency closure 决定；不得外推到改变后的 Strategy、Prompt、policy、suite、Oracle 或
  product candidate。

run-001 的 9/12 与 run-002 的 11/12 失败证据永久保留。本 Result 不覆盖或改写旧运行，也不允许 retry 后挑选结果。

## Remaining gates

下一步必须在零额外 Provider call 的条件下构建并验证产品 candidate stage，形成 product-code freeze。只有冻结后，用户才披露
一条支持范围内的无符号跨域问题和一条真实 boundary 问题；问题执行必须走正式 Web、严格三调用、Source-off 边界和独立 evaluator。
隐藏 canary 未 PASS 前不得完成 `SLICE-001` 或进入 `SLICE-002`。
