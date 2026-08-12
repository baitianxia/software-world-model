---
id: FINDING-005-001
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-005-SLICE-001, ITER-005-VERIFICATION]
code: [src/software_world_model/application_services/read_set_catalog.py]
tests: [tests/test_maven_workspace.py]
iteration: ITER-005
classification: local-implementation
disposition: reconcile-each-contiguous-catalog-publication-before-advancing
target: src/software_world_model/application_services/read_set_catalog.py
---

# FINDING-005-001：Catalog pointer 恢复可能跳过 Application receipt revision

## Observation

Catalog immutable manifest 与 current pointer 已成功发布、但 Application publication receipt 尚未落库的进程中断之后，
若恢复前又登记了新的 Read Set，旧实现会直接从 pointer revision 发布下一版。文件链仍连续，但 Application receipt 历史
会从 revision 1 跳到 revision 3，遗漏已经真实发布的 revision 2。

## Evidence

- `tests.test_maven_workspace.MavenWorkspaceTests.test_catalog_pointer_crash_reconciles_before_a_later_publication`
  注入 pointer 发布后的单次 receipt 写入中断；
- 中断后的 pointer 为 revision 2，而 DB latest receipt 仍是 revision 1；
- 另一个 Workspace 随后登记 Read Set 并发布 revision 3；修正后 DB receipt 明确为 `[1, 2, 3]`，原 Attempt 再恢复时
  复用 revision 3，不重复发布；
- 原有无新增 Entry 的窄恢复场景继续由同一逻辑覆盖。

## Impact and classification

current Persistence Contract 已要求连续持久历史、真实 immutable manifest 不得被跳过；Owner、Schema 和调用方语义无需
改变。这是 Catalog service 恢复顺序没有完整实现既有不变量，分类为 `local-implementation`。

## Decision and disposition

读取 current manifest 后先比较 pointer 与 latest Application receipt：同 revision 必须 exact 一致；恰好领先一版时必须
验证 `previous_catalog_digest` 并补录该 receipt；无历史却不是 revision 1、领先多版、落后或 digest 不连续均失败关闭。
只有 receipt 链连续后，才比较当前 Entry set 并决定复用或发布下一 revision。

## Verification after disposition

Catalog crash + intervening registration 的聚焦测试通过；完整 SLICE-001 聚焦集合 45/45 PASS。System Contract 无需回写，
因为修正只恢复其已有连续性要求。
