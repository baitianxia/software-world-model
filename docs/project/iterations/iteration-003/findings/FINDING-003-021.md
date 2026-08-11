---
id: FINDING-003-021
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-003-SLICE-001, ITER-003-VERIFICATION, FINDING-003-020]
code: [validation/product_holdout_iteration_002/direct_answer.py, validation/structure_world_model_iteration_003/questions/direct-baseline-protocol-1.0.1.json]
tests: [tests/test_product_holdout_direct_answer.py, tests/test_iteration_003_validation_assets.py]
iteration: ITER-003
classification: verification
disposition: preserve-direct-failures-and-defer-quality-comparison-to-v011-without-imputation
target: ITER-003-VERIFICATION
---

# FINDING-003-021：Direct baseline 的完整样本包含 Provider 限流和输出合同失败

## Observation

最终 controlled Direct baseline 严格按冻结顺序完成 55 个 cold process，未做 run-level retry，也未在看到
结果后改 Prompt、资源或顺序。15 个 run 成功，40 个 run 以 `FAILURE_KEPT_NO_RETRY` 终止。40 个终态失败
中，25 个是结构化输出或 Agent action contract 未取得 eligible Result，13 个来自 Ark HTTP 429，另 2 个
是 Provider outcome unknown。后 15 个外部分派失败均按协议保留，不能事后等待限流恢复再补跑。

Mature Source Agent 使用另一冻结模型和质量比较协议，55/55 均成功；因此 V-009 已取得完整的强质量
对照样本，但 Direct 的逐题质量与性能证据不能被描述为 55 个 eligible answer。

## Evidence

- Direct batch Result：
  `var/iteration-003/v009/019f9fced69110c6a7e357a4ea2394ec6742fd2e/baselines/direct/batch-result.json`，
  document digest
  `sha256:64a7a9c2357427f0b4f0c77b47a895c454de1cfce5830d759941764963ac871d`；
- 55/55 都有 invocation、child process 与 terminal receipt；15 SUCCESS、40 FAILURE；
- transport terminal 分布为 HTTP 200=510、HTTP 429=13、exception=2；最终 model call failure code 包含
  `PROVIDER_HTTP_ERROR`=13、`PROVIDER_OUTCOME_UNKNOWN`=2，另有 133 个中间/终态
  `STRUCTURED_OUTPUT_INVALID` call；
- run-level 失败分布：25 structured/action contract、13 control-state/provider HTTP、2 outcome unknown；
- Direct 全终态 executor latency P50=40.213 秒、P95=101.502 秒；
- Mature batch Result document digest
  `sha256:1b10854b1dc17a022c35542a68b1bafd0ee238710c60dbdb461c5323688a2f6f`，55 SUCCESS、0 FAILURE。

## Impact and classification

协议本来就要求保存全部失败并禁止挑选成功，因此该分布不使 V-009 的“baseline 已预先密封”声明失真，
也不授权重跑。它会影响后续 V-011 如何解释更强质量对照和 Direct P95，属于
`verification`，不修改产品、Provider adapter 或 System Contract。

## Decision and disposition

V-009 Result 必须同时报告成功与失败，不能把 15 个 eligible answer 外推成 55 次质量 PASS，也不能把
429/unknown 从时延分布中静默删除。V-011 仍为 pending：离线 evaluator 逐 case 比较时，Direct 只有真实
eligible output 才能形成质量候选；没有 eligible Direct output 的 case 不填补、不推定，完整的 Mature
55-run 对照仍参与“二者中更强者”判断。性能 verdict 必须明确报告全终态 population、Provider failure
population 与 eligible-success population；任何选择性过滤都不能形成 PASS。

## Verification after disposition

联合 baseline seal 绑定全部 110 个 terminal receipt 和两个 batch Result，明确
`failures_preserved=true`、`production_eligible=false`。V-011 在 G3b/G4 之前仍未执行，故本 Finding 不提前
声称产品质量或性能达标。
