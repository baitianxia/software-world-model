---
id: ITER-005-INDEX
kind: iteration-index
status: completed
authority: historical-project
owners: [project]
depends_on: [ITER-005-PROPOSAL, ITER-005-READINESS, ITER-005-RESULT-ACCEPTANCE]
code: [src/software_world_model/application_services/maven_workspace.py, src/software_world_model/application_services/read_set_catalog.py, src/software_world_model/infrastructure/sqlite_maven_workspace_repository.py, src/software_world_model/infrastructure/file_read_set_catalog.py, src/software_world_model/interface/read_set_catalog_cli.py, src/software_world_model/interface/world_model_http.py, src/software_world_model/interface/world_model_runtime.py, validation/structure_world_model_iteration_005/slice2_comparison.py, validation/structure_world_model_iteration_005/slice2_evaluator.py]
tests: [tests/test_maven_workspace.py, tests/test_world_model_http.py, tests/test_world_model_product.py, tests/test_iteration_005_slice2_comparison.py, tests/test_iteration_005_slice2_evaluator.py]
iteration: ITER-005
coding_input: false
---

# Iteration 005：用户指定 Maven 仓库的软件世界模型工作区

## Status and authorization

用户于 2026-08-11 明确要求开发 ITER-005，并于 `2026-08-12T08:44:55+08:00` 接受最终 Result。冻结 G0 输入后，公共 CLI 在 exact baseline `a91dc7c…` 上对 TTL3 与
Gson 两个真实多模块仓库均产生与独立 Oracle 一致的 COMPLETE Structure；Maven Wrapper valid→unsupported 序列准确
拒绝 reactor 内 `type=pom` 依赖并保持旧 CURRENT。System Workspace/Catalog 边界已写回 current Contract，因此本轮的
`ITER-005-SLICE-001` 已完成实现与证据并由用户接受；`ITER-005-SLICE-002` 的 `run-006` 真实浏览器 PASS、comparison
`FAIL` 原样保留。修复后的 `run-007` 已在 exact 用户授权下完成 baseline-first 三路比较：Direct、Mature、World 各 9/9，
independent comparison 与正式产品 Web 的 supported/Gap/Citation/动态 Read Set 人工验收均 PASS。最终接受对象为
implementation commit `956f31d6…`，详见 [Final Acceptance](results/acceptance.md)；Production Activation 仍未执行。

为避免到浏览器阶段才发现真实仓库不适配，本轮分为两个顺序 Slice。先完成并人工核对无模型的工作区、更新、Bundle
与动态目录，再复核并授权正式本机 Web 问答入口。前一 Slice 的通过不会自动授权后一 Slice，但 ITER-005 也不能在
SLICE-002 之前完成；最终必须能从统一产品 Web 页面真实提问。

## Required inputs

- [Proposal](proposal.md)
- [Manifest](manifest.yaml)
- [Verification Matrix](verification-matrix.md)
- [Readiness Review](readiness-review.md)
- [Development Design](development-design/README.md)
- [Findings](findings/README.md)
- [Results](results/README.md)

[SLICE-001 Result](results/slice-001-workspace-catalog.md) 已被用户接受，主报告 `sha256:7047522d…`、全量回归
771/771 PASS。[SLICE-002 Run-006 Live Evaluation](results/slice-002-run-006-live.md) 保存失败 comparison 与通过的真实浏览器
证据；[SLICE-002 Candidate Freeze](results/slice-002-candidate-freeze.md) 记录 `run-007` 的 51 focused、13 staged Answer、801 full
regression 与 exact disclosure set；[SLICE-002 Run-007 Live Evaluation](results/slice-002-run-007-live.md) 记录新授权、三路
population、comparison 与浏览器 PASS。本目录已转为历史证据，不再授权产品代码修改。
