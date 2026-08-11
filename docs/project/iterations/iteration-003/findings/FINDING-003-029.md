---
id: FINDING-003-029
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-003-SLICE-001, ITER-003-VERIFICATION, FINDING-003-028]
code: [src/software_world_model/interface/world_model_product.py]
tests: [tests/test_world_model_product.py]
iteration: ITER-003
classification: local-implementation
disposition: render-direct-source-from-same-entity-ga-state
target: src/software_world_model/interface/world_model_product.py
---

# FINDING-003-029：根项目直接依赖答案丢失了完整 GA

## Observation

修正 evaluator 误判后，对 product checkpoint
`7933712d7d00d113abe0ec147729fa41562bea76` 的第二份独立 Result
`product-evaluation-v2.json` 得出 58/60 PASS、边界 PASS、性能 PASS。仅
`static-WM-PRODUCT-007-run-02-paraphrase` 和 `static-WM-PRODUCT-007-run-03-canonical` 保留
`WORLD_MODEL_COMPLETENESS_BELOW_STRONGER_BASELINE`。

两个答案都正确说明根 POM 直接依赖 `org.example.shared:common-lib`、
`dependencyManagement` 不成边，但 `source` 只渲染为 `structure-fixture`，未写出冻结 comparator
检查的完整 `org.example.root:structure-fixture`。

## Evidence

- Result document digest 为
  `sha256:a55bee5c9577d7225ab0066c05efa9ff8bbe7dc6b3997367e3f1ff2f648effb0`，evaluator checkpoint 为
  `4d75aaf43dffc197ec13ae77d7305fd64d8d5aea`；
- 两个失败 run 的 World Model completeness 均为 `666667 ppm`，各自的更强密封 baseline 为
  `1000000 ppm`；其他 58 个 run 通过；
- `ProductDraftGenerator._render_direct` 对 `canonical_ga is None` 的 `SOFTWARE_SYSTEM` 直接退化到
  `state_fields.artifact_id`，而同一受信 Entity State 已同时包含 `effective_group_id` 和 `artifact_id`；
- 该问题的目标 module 始终用完整 GA 渲染，因而缺口只在 root `SOFTWARE_SYSTEM` 的 source
  display path，不是 parser、typed identity 或 query result 错误。

## Impact and classification

这是可在所有 Maven-backed `SOFTWARE_SYSTEM` 上重现的通用渲染缺口，但不改 Entity Root/State
身份公式、View 或查询语义。分类为 `local-implementation`。因冻结协议要求“不低于更强对照”且
重大错误为零，不能以 58/60 降级接受 G3b。

## Decision and disposition

direct-dependency 答案的 source 标识按以下顺序产生：

1. Entity payload 有 `canonical_ga` 时直接使用；
2. root `SOFTWARE_SYSTEM` 没有 module canonical GA 时，从同一 Entity State 内的
   `effective_group_id` 与 `artifact_id` 组合完整 GA；
3. 任一字段缺失即 fail closed，不用 question token、其他 Entity 或 artifactId 候选做名称拼接。

增加 mall 与 identity fixture 的 root source exact GA 断言。已密封的 `7933712…` batch 和两份
FAIL Result 必须保留，不得重写、择优或将新 renderer 套用到旧 terminal。

## Verification after disposition

运行产品聚焦测试、G3b/V-009 聚焦回归、全量回归和文档检查。由于产品 runtime 已变更，
V-011 仍为 FAIL/阻断 G4；若要重新证明 G3b，必须从新 clean product checkpoint 准备全新 60-run
batch，不得使用旧模型输出做选择性修复。本 Finding 本身不会追加 Provider 调用，Production
Activation 仍为 `NOT_EXECUTED`。
