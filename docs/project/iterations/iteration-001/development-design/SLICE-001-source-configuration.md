---
id: ITER-001-SLICE-001
kind: development-slice
status: completed
authority: historical-development
owners: [source, application]
depends_on: [ITER-001-PROPOSAL, SYS-CONTRACT-SOURCE-DATA-SOURCE, SYS-CONTRACT-SOURCE-ARTIFACT]
code: [src/software_world_model/source_integration, src/software_world_model/application_services/management.py]
tests: [tests/test_source_configuration.py, tests/test_source_operations.py, tests/test_local_git_configuration.py]
iteration: ITER-001
migration: reconstructed-from-existing-iteration-records
---

# SLICE-001：来源配置与精确 Local Git

## Outcome

操作者可以把一个本地 Git 仓库作为稳定 Data Source 绑定到 Knowledge Scope，并对 exact Commit/Path/符号执行有界只读调查，产出可追溯 Artifact。

## Required system semantics

- 遵守 `INV-003`，来源边界止于 Artifact；
- Data Source、Binding、Scope 和外部 Revision 身份分离；
- Target 歧义、短 Revision、越权路径、截断和未完成失败关闭；
- 模型只提议 Source Action，平台授权、预算并执行。

## Affected implementation

`source_integration/configuration.py`、`local_git.py`、`operations.py`、Artifact Processing Repository 和 Management use case。

## Non-goals

远程写操作、跨 Provider 统一 Payload、由 Source 形成 Fact、通过空结果证明代码不存在。

## 阅读与回写

当前语义见 [Source Contracts](../../../../system/contracts/source/README.md)；实现发现进入本轮 [Findings](../findings/README.md)，不得直接改写历史 Result。

## Acceptance

稳定身份、Selector 等价、exact Revision、重载/路径歧义、权限、分页/截断、幂等和 Lineage 均有自动化正反例；任何失败不产生伪完整 Coverage。
