---
id: FINDING-003-028
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-003-SLICE-001, ITER-003-VERIFICATION, FINDING-003-027]
code: [validation/structure_world_model_iteration_003/g3b/evaluate_results.py]
tests: [tests/test_iteration_003_g3b.py]
iteration: ITER-003
classification: iteration-design
disposition: distinguish-policy-and-transport-endpoint-representations
target: ITER-003-SLICE-001
---

# FINDING-003-028：evaluator 混同了 policy endpoint 与 transport 规范化表示

## Observation

纯本地 evaluator checkpoint `1ff44f074ce3164ba3c93aca12b350a51af7ff01` 在先行密封 invocation
后完成了 60 个 product terminal 扫描，密封的首份 Product Evaluation Result 为 FAIL。其中 60/60 均含
`AUTHORITY_OR_EXECUTION_BOUNDARY_INVALID`，但 batch/preflight 总边界裁决为 PASS，显示存在系统性 evaluator
不一致。

## Evidence

- 60 份 transport audit 均记录 exact Adapter endpoint
  `https://ark.cn-beijing.volces.com/api/coding/v3/chat/completions`、200/`HTTP_RESPONSE`和同一个
  `EXECUTOR_SYNTHETIC_EXTERNAL` peer；evaluator 却要求 audit 文本必须包含显式 `:443`；
- sealed invocation/policy 的 endpoint 为
  `https://ark.cn-beijing.volces.com:443/api/coding/v3/chat/completions`，每份 supervisor provisioning 都独立记录
  hostname、provider/connected peer port `443`、exact numeric address 和 descriptor transfer；Gateway/Server audit 都绑定
  exact policy ref/digest；
- `WM-PRODUCT-003` 的五份 mall diff payload 都正确给出 Entity
  `{added:1, removed:0, state_changed:7, unchanged:0}` 和 Relation
  `{added:3, removed:0, state_changed:11, unchanged:0}`；evaluator 以缺少 `unchanged` 键的 dict 做整对象相等，因而误拒绝。
- 同一 Result 还独立暴露 `WM-PRODUCT-007` 在两个 run 上未写出完整 root GA 的真实对照完整性缺口；
  该缺口不属于本 Finding 的 evaluator 误判，不得被同时放宽。

## Impact and classification

第一份 FAIL Result 是有效、不可覆写的实施证据；它不能用来宣称产品边界失败，也不能因两个
evaluator bug 就把真实内容缺口删除。变更只修正事后裁决规则，不改产品 runtime、60 个请求或任何冻结
input，分类为 `iteration-design`。

## Decision and disposition

evaluator 分别校验：

- invocation/policy 必须是含显式 `:443` 的 exact endpoint；
- Adapter transport audit 必须是省略 HTTPS 默认端口的 exact normalized endpoint；
- provisioning 必须同时给出 exact hostname、provider port 443、connected peer port 443；
- Gateway 和 Server audit 必须绑定 exact policy ref/digest，transport 还必须绑定同一 numeric address/scope 与
  certificate digest。

mall diff counts 改为精确包含 `unchanged:0` 的四字段比较。新 evaluator checkpoint 必须使用新的
output basename 密封 invocation/Result，保留原 `product-evaluation.json` 不变；整个重评估不发起 Provider 调用，
Production Activation 仍为 `NOT_EXECUTED`。

## Verification after disposition

新增 policy/transport endpoint 规范化正反例、diff `unchanged` 精确计数正反例，重跑聚焦、全量回归和文档检查。
在 clean descendant evaluator checkpoint 上用 `product-evaluation-v2.json` 重新裁决 immutable `7933712…` batch，
预期只保留由 frozen comparator 证明的真实产品缺口。
