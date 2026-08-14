---
id: FINDING-008-004
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [interface, quality]
depends_on: [ITER-008-SLICE-001, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING]
code: [src/software_world_model/interface/world_model_evaluation.py, src/software_world_model/interface/world_model_runtime.py, src/software_world_model/interface/world_model_runtime_assets/java_source_semantics_answer_workload.py, src/software_world_model/interface/world_model_runtime_assets/bounded_java_source_semantics_answer_workload.py]
tests: [tests/test_iteration_007_slice1_freeze.py, tests/test_world_model_evaluation.py, tests/test_java_source_semantics.py, tests/test_iteration_008_capability_qualification.py]
iteration: ITER-008
classification: local-implementation
disposition: preserve-historical-assets-and-version-bounded-page
target: src/software_world_model/interface/world_model_evaluation.py
---

# FINDING-008-004：有界协议不能改写历史运行资产和评测页格式

## Observation

最初把 ITER-008 的调查 Trace 直接加入既有 Java source-semantics Answer workload 和
`WORLD_MODEL_EVALUATION_PAGE@1`，会改变 ITER-007 已冻结的 launcher closure、资产 bytes、页 canonical payload 与 digest。即使新字段在
语义上可选，这仍会让历史候选无法按原冻结证据重放，并把有界 `1.3.0` 的身份混入固定 `1.2.2` 协议。

## Evidence

- ITER-007 `slice1_freeze` 对 launcher 文件集合及每个文件 bytes 做 exact 比较；修改历史 Answer workload 会直接破坏该回归；
- 历史评测页以 `WORLD_MODEL_EVALUATION_PAGE_PAYLOAD@1` 对固定字段集合计算 digest，加入 `investigation_trace` 会改变同一 format ref 的
  canonical identity；
- 恢复历史 Answer workload 后，ITER-007 closure 回归保持不变；新增独立 bounded Answer/Gateway 资产只在
  `_launcher_files(include_bounded=True)` 中出现；
- 无 Trace 的回答继续生成 `WORLD_MODEL_EVALUATION_PAGE@1`，有密封 Trace 的回答生成独立的
  `WORLD_MODEL_EVALUATION_PAGE@2`，Reader 对 format、字段集合和 digest domain 做 exact 验证。

## Impact and classification

System Contract 已要求历史证据可重放，并要求有界调查携带密封 Trace；发现的是两个协议版本在 interface 资产和 envelope DTO 中需要独立
身份，而非新的 Owner、调用语义或安全边界。变更只影响本地文件闭包选择和序列化版本，因此分类为 `local-implementation`。

## Decision and disposition

保留 `java_source_semantics_answer_workload.py` 的 ITER-007 exact bytes，并为 ITER-008 新增
`bounded_java_source_semantics_answer_workload.py` 与 bounded Gateway workload。默认 launcher closure 仍代表历史冻结集合；只有显式
bounded freeze 才加入两个新资产。评测页按是否存在已验证调查 Trace 选择 `@1` 或 `@2`，两个版本使用不同 digest domain，禁止字段跨版本
漂移。

主处置进入 `world_model_evaluation.py`，资产闭包和历史 freeze 测试提供回归证据；无需修改 System 文档，因为现有规范已经拥有版本身份和
历史可重放要求。

## Verification after disposition

- ITER-007 launcher closure 的 key、path 与 bytes 继续和历史 freezer exact 相等；
- ITER-008 bounded closure 只额外包含两个显式命名资产；
- legacy page 不含 `investigation_trace`，仍使用 `@1` payload digest；
- bounded formal page 必须包含可重放 Trace，并使用 `@2` payload digest。
