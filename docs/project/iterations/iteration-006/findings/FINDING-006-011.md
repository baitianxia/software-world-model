---
id: FINDING-006-011
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-006-SLICE-001, ITER-006-VERIFICATION]
code: [validation/structure_world_model_iteration_006/live_product_probe.py]
tests: [tests/test_behavior_view.py, tests/test_world_model_product.py, tests]
iteration: ITER-006
classification: local-implementation
disposition: bind-java-formal-probe-to-exact-strategy-identity
target: validation/structure_world_model_iteration_006/live_product_probe.py
---

# FINDING-006-011：Java deterministic formal stub 缺少 exact Strategy identity

## Observation and evidence

capability qualification PASS 后首次生成产品候选时，`run-005` 在 deterministic product probe 的第一个 Java case 失败，错误为
`PRODUCT_MODEL_STRATEGY_PROFILE_MISMATCH`。产品服务已按 `FINDING-006-008` 正确要求挂载 Java profile 时 Strategy ref 必须是
`model-snapshot-first-world-model-answer@1.1.0`；但 iteration-only `_FormalProposalStub` 没有声明任何 `strategy_ref`，因此被
fail-closed guard 正确拒绝。

这不是 capability qualification 或产品 runtime 漂移。live provider strategy 支持 `for_proposal_contract(...)`，Java 产品测试
fixture 也已绑定 `JAVA_PRODUCT_STRATEGY_REF`；仅该 deterministic freeze stub 漏掉相同身份。

把 capability freeze 的 60-path checkpoint 与修复后工作树逐项比较，唯一变化路径就是
`validation/structure_world_model_iteration_006/live_product_probe.py`；`src/`、Strategy/Prompt/policy、Gateway、role package 与
既有 tests 均未漂移。

## Classification and disposition

最小修复是在 Java-only formal stub 上显式声明 `strategy_ref = JAVA_PRODUCT_STRATEGY_REF`，不放宽产品 guard、不改变 proposal
内容或运行时接口。对 `run-005` 同一 sealed suite 的直接重放随后 6/6 PASS；全新 `run-007` 的 deterministic probe、55 项 focused、
18 项 candidate package 与 835 项 full regression 全部 PASS。

该变化只修正 iteration validation fixture，不改变调用方或系统语义，故处置到本地代码/测试，不需要修改 System Contract。
