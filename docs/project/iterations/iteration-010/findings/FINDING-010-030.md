---
id: FINDING-010-030
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [project, quality, engineering]
depends_on: [ITER-010-SLICE-001, ITER-010-PDR-001, PROJECT-GOVERNANCE-ITERATION-LIFECYCLE]
code: [scripts/docs.py]
tests: [tests/test_docs_gate.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: materialize-closed-rework-authorization-history-sequences-before-validation
target: scripts/docs.py
---

# FINDING-010-030：惰性 Manifest 解析遗漏返工授权历史序列

## Observation

ITER-010 Slice1 恢复开发时，Manifest 需要同时保留历史失败 Result 和旧开发授权，分别使用嵌套的 `rework_result_refs` 与
`prior_authorization_refs`。文档门禁的惰性 YAML 解析器不会直接物化 block sequence；file-backed product-goal 校验此前只显式解析前者，
因此会把合法的 `prior_authorization_refs` 留成占位 mapping，并错误报告缺少新的返工授权历史。

## Evidence and root cause

- `manifest_resolved_nested_sequence_items()` 已能安全解析任意已知嵌套 sequence，但调用方只列出 `rework_result_refs`；
- in-memory 单元输入使用普通 list，不触发该问题，只有读取真实 Manifest 的闭合校验路径会出现；
- 当前 rework authorization invariant 要求新收据不得等于项目决定收据或任一旧开发授权，门禁必须取得真实旧授权列表后才能判断；
- 根因是 file-backed adapter 的字段 materialization 不完整，不是 rework authorization 规则错误。

## Decision and disposition

`validate_product_goal_reference_targets()` 只对 closed allowlist 中的 `rework_result_refs` 与 `prior_authorization_refs` 调用既有 inert-text
sequence resolver，再交给原有 rework validator。没有引入通用 YAML 构造器、动态字段解析或新的治理语义；未知字段仍不会获得执行意义。
该修复属于治理脚本的本地实现，处置到代码与测试即可。

## Verification

文档门禁测试直接从 ITER-010 file-backed Manifest 解析 exact `prior_authorization_refs`，并继续通过完整 rework reference validation；
`python3 scripts/docs.py check` 作为最终当前文档门禁执行。
