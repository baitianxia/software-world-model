---
id: FINDING-010-068
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-067]
code: []
tests: [tests/test_iteration_007_readiness.py]
iteration: ITER-010
classification: local-implementation
scope: individual
disposition: preserve-historical-iteration-007-contract-digest-without-recomputing-current-system-documents
target: tests/test_iteration_007_readiness.py
---

# FINDING-010-068：历史 Readiness 摘要不能用 current System 文档重算

## Observation and evidence

`FINDING-010-066/067` 合法修改 current System Contract 后，默认沙箱 full discovery 的 1172 项中新增
`test_iteration_007_readiness.Iteration007ReadinessOracleTests.test_frontend_and_no_payload_oracles_are_reproducible` 失败：测试读取
ITER-007 历史 Manifest 中冻结的 `system_contract_set_digest`，却用今天已经演进的 `docs/system/` 同路径文件重新计算，得到不同摘要。

这不是 ITER-010 产品回归，也不能通过修改 ITER-007 历史 Manifest 来追认今天的 Contract bytes。当前文档 Gate 已明确区分两种语义：活动
Iteration 必须与 current exact fileset 相等；completed/rejected/paused 历史 Iteration 只要求保留合法 exact SHA-256，因为当时的 bytes
不再由 current path 拥有。该单测仍使用旧的 current-fileset 算法，和项目历史/当前权威分离规则不一致。

## Decision and disposition

测试改为核对 ITER-007 当时冻结的 schema `ITER-007-SYSTEM-CONTRACT-SET@1` 与摘要
`sha256:5857ee235478c5e2b8f4d516dfdfcc99b4c6503e827b7ca23fbc5ae2a864e355`，不再用 current 文档重算历史输入。
该修复只校正历史 oracle 的测试实现，不改变 ITER-007 Manifest、current System 语义或产品代码，因此归类为
`local-implementation` 并落位于该测试。含 ITER-007 oracle 与本次三模块的定向组合 71/71 PASS；允许 AF_UNIX 的 full 1172 项恢复为
1167 PASS，raw 唯一 4 FAIL + 1 ERROR 仍是冻结 V-009/Codex historical hold。
