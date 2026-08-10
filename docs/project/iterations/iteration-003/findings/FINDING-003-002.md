---
id: FINDING-003-002
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-003-SLICE-001, SYS-CONTRACT-SOURCE-ARTIFACT]
code: [src/software_world_model/source_integration/operations.py, src/software_world_model/source_integration/local_git.py]
tests: [tests/test_source_operations.py, tests/test_local_git_configuration.py]
iteration: ITER-003
classification: local-implementation
disposition: add-versioned-local-git-tree-entry-artifact
target: src/software_world_model/source_integration/operations.py
---

# FINDING-003-002：路径列表不足以证明 Maven POM 是普通 Git 文件

## Observation

G1 实现 Maven Structure Builder 时发现，已有 `local-git.list@1` 的
`LOCAL_GIT_PATH_LIST@1` payload 只保留路径。它不能区分普通文件与符号链接，也不保留
exact tree object ID，因此无法在不直接绕过 Source Integration 调用 Git 的前提下执行
`MAVEN-REACTOR-CANONICALIZATION@1.0.0` 的 symlink rejection 和 exact-tree 审计。

## Evidence

- `LocalGitConnector.list_paths()` 使用 `git ls-tree -r --name-only -z`，结果只有路径。
- 冻结 canonicalization 要求 module target 是 exact revision 中的 regular
  `pom.xml`，且 `symlink_policy=REJECT`。
- Knowledge Update 不能自行执行 Git；所有源码读取必须产生受 Scope/Binding/Revision
  约束并可回放的 Source Artifact。

## Impact and classification

缺口只涉及 Local Git Connector 的版本化 payload 表达；不改变 Source Artifact 的
Owner、授权、Revision、Artifact 或 Payload 语义，也不改变现有 LIST 调用方。因此属于
local implementation，不需要修改 System Contract。

## Decision and disposition

保留 `local-git.list@1` 与 `LOCAL_GIT_PATH_LIST@1` 不变，新增
`local-git.tree@1` / `LOCAL_GIT_TREE_ENTRY_LIST@1`。每条 canonical JSON line 保存
`path`、Git `mode`、object `type`、object ID 和派生的 `is_symlink`；沿用现有 selector、
分页、预算、Scope/Binding eligibility、Artifact materialization 与幂等规则。由 Source
Operation tests 覆盖稳定排序、mode/object ID、符号链接、分页、selector 和旧 LIST
兼容性。
