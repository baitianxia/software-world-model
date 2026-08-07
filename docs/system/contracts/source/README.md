---
id: SYS-CONTRACT-SOURCE-INDEX
kind: system-contract-index
status: current
authority: normative
owners: [source]
depends_on: [SYS-CONTRACT-INDEX]
code: [src/software_world_model/source_integration]
tests: [tests/test_source_configuration.py, tests/test_source_operations.py]
---

# Source Contracts

Source Integration 拥有来源配置、只读操作和 Artifact。其知识边界止于 Artifact；它不定义 Fact，不执行 Admission，也不判断任务是否充分。

- [Data Source 与 Binding](data-source.md)
- [Source Operation 与 Artifact](source-artifact.md)
