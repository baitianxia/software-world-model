---
id: ITER-005-RESULT-SLICE-001
kind: iteration-result
status: accepted
authority: execution-evidence
owners: [engineering, quality]
depends_on: [ITER-005-VERIFICATION, ITER-005-FINDINGS, ITER-005-RESULT-G0]
code: [src/software_world_model/application_services/maven_workspace.py, src/software_world_model/application_services/read_set_catalog.py, src/software_world_model/infrastructure/sqlite_maven_workspace_repository.py, src/software_world_model/infrastructure/file_read_set_catalog.py, src/software_world_model/interface/runtime.py, src/software_world_model/interface/cli.py, src/software_world_model/interface/read_set_catalog_cli.py, src/software_world_model/interface/presenters.py, validation/structure_world_model_iteration_005/slice1.py, validation/structure_world_model_iteration_005/coverage_copy.py]
tests: [tests/test_maven_workspace.py, tests/test_iteration_005_g0.py, tests]
iteration: ITER-005
---

# SLICE-001 Maven Workspace 与 Source-off Catalog Result

## Decision

SLICE-001 的实现和执行证据通过 V-002—V-005。用户于 `2026-08-11T19:32:39+08:00` 回复“继续开发”，接受本 Result
并授权 SLICE-002 编码。这个 Result 不接受 ITER-005、不授权真实外部分派，也不执行 Production Activation。

## Exact implementation subject

正式证据目录是 `var/iteration-005/slice-001/run-005/`，主报告 `report.json` digest 为
`sha256:7047522d5f2f7fe936c0db3c3a28ff3f75e4141e5c50fbe3f9af7c02df41498f`。由于当前实现尚未提交到主仓库，runner 没有
把旧 `HEAD` 伪装成实现身份；它把实际执行的完整 `src/` 与 `pyproject.toml` 复制到隔离 provenance Git repository，得到：

- producer commit `16442fd5bd8eea0d8299fc08c427e1065e35ad87`；
- producer tree `bef645bc2991224c9a7f12ae27db59ff66bc1d1d`；
- source manifest digest `sha256:88957c6d402538796c4cb2cdc517095c5e52fe1a92ca11645c90fa6ff44c4e11`。

runner 前后重算执行目录的 source manifest，确认运行期间代码未漂移。该隔离 commit 是 validation provenance，不是对主仓库
已提交状态的声明。

## G0 compatibility and V-002 copy correction

[G0 Result](g0-generalization.md) 已在 baseline 上证明 TTL3/Gson COMPLETE，以及 Maven Wrapper valid→unsupported
准确拒绝并保持 CURRENT。V-002 使用产品自己的 `WorldModelBrowserApplication` 和 UI assets 进行只读 copy audit；Answer
path 没有激活：

- 页面出现 `Maven reactor 子模块成员关系`、`POM-local 直接内部依赖` 与 `exact A/B diff`；
- 页面明确说明插件、属性与 Maven parent 超出 Coverage；旧 overclaim 不存在；
- screenshot `v002-coverage-copy.jpg` / `sha256:6ed4f9b2…`，1280×1197；
- `v002-copy-audit.json` / `sha256:8fc1de51…`；UI 文件与 producer snapshot 的 digest 均为
  `sha256:50fdaa7a…`。

这是 Coverage 文案核对，不是 SLICE-002 产品问答验证。

## G1 zero-question R1 → R2

runner 每次随机生成 system key、group/artifact、module name/path 和三段式 Maven topology；产品不导入 runner 或 Oracle。本次
exact fixture 为 R1 `7f3ad26ce8ce56031c1a5ce2726a0fa7da066df6` → R2
`047792c869ea89a4f9c58140347b50540ef6b877`。

| Revision | Coverage | Entity / Relation | 删除成员 | Source calls / bytes / ms | Snapshot / Bundle |
|---|---|---:|---:|---:|---|
| R1 | COMPLETE / `MAVEN_REACTOR_STRUCTURE@1` | 4 / 5 | 0 | 5 / 2211 / 371 | `structure_snapshot_a3bd…` / `sha256:421ea81d…` |
| R2 | COMPLETE / `MAVEN_REACTOR_STRUCTURE@1` | 3 / 3 | 3 | 4 / 1539 / 298 | `structure_snapshot_4e1e…` / `sha256:a12b32d…` |

R1 前 `app_questions`、`app_tasks` 表不存在，两种 Structure Read Session 计数均为 0。更新明确报告
`FULL_REBUILD`；Software System Root 稳定、State 变化、删除成员存在、CURRENT 为 R2，历史顺序为 exact R1/R2，重复 R1
幂等键复用同一个 Attempt/Version。`graphs.md`、`raw/workspace-r{1,2}.json`、`raw/workspace-versions.json` 和
`raw/workspace-read-sets.json` 保存完整人读/机器证据。

## G2 dynamic Catalog and Source-off Views

主 Workspace 的 R1 single、R2 single 和 ordered R1→R2 三个 Read Set 均进入动态 Catalog；附加 recovery Workspace 使最终
Catalog revision 4 含 6 个 queryable Entry。current pointer 与 manifest 的 Catalog digest 为
`sha256:131302dd9ee2d33c43afb74b5f0b4fed5454c6f7a9b60f9eaacd7949bd046b6f`。

`catalog-audit.json` 证明 Catalog 中没有 repository/database path，也没有 Entity、Relation、Fact、Evidence、Artifact 或
Source payload 字段。随后 runner 把 authority DB（含 WAL/SHM）与 Git repository 移到不可用位置；一个全新 Source-off
进程的 parser 只有 Catalog/Bundle root 输入，并完成：

| Operation | Exact raw output |
|---|---|
| Catalog verify / list | `raw/source-off-{verify,list}.json` |
| candidates | `raw/source-off-candidates.json` |
| reactor inventory | `raw/source-off-inventory.json` |
| POM-local direct dependency | `raw/source-off-direct-dependency.json` |
| R1 dependency path | `raw/source-off-path.json`，`exists=true` |
| ordered R1→R2 diff | `raw/source-off-diff.json` |

`source-off-mount-manifest.json` 与主报告均记录 DB/Source 原路径不存在；R1 exact read 在 CURRENT 移动后仍可用。

## Failure and recovery evidence

| Case | Observed result | Recovery / retained truth |
|---|---|---|
| 实际 Bundle root `PermissionError` | Step/Attempt `OUTCOME_PENDING`；新 Version `READ_BUNDLE_UNAVAILABLE` | 旧 Version/Catalog 可查；重启沿同 Attempt 恢复，Snapshot successful Step 只有 1 个 |
| 明确 Bundle Domain failure | Step `FAILED` / Attempt `READ_BUNDLE_UNAVAILABLE` | 同 Attempt 重放成功，旧 Read Set 不变 |
| Catalog pointer 后 receipt 中断 | pointer 已发生，Attempt 不伪造回滚 | 先补录连续 receipt，再允许新 Entry 发布；DB revision `[1,2,3]` |
| stale expected CURRENT | Snapshot owner `REVISION_CONFLICT` | 不创建 Workspace Version/Read Set，旧 queryable Version 保持 |
| 重复幂等键不同输入 | `IDEMPOTENCY_MISMATCH` | 不产生第二结果 |

Catalog、embedded Receipt、locator、pointer、Bundle bytes、额外文件与 symlink 七类篡改全部由只读 CLI 拒绝；精确 reason
code 见主报告和 `raw/tamper-*.json`。实现过程中发现的 receipt 连续性缺口已由
[FINDING-005-001](../findings/FINDING-005-001.md) 处置。

## Regression and limitations

`test-results.json` / `sha256:b92b61a7…` 记录：

- SLICE/兼容聚焦集合 45/45 PASS；
- Catalog 连续性修正后的 Workspace fault 集合 8/8 PASS；
- 允许本机 loopback/Unix socket 的全量回归 771/771 PASS，76.687 秒。

全量测试仍打印既有 `sqlite_structure_read_session_repository` 未关闭连接 `ResourceWarning`，没有失败；本 Result 不把警告
隐藏，也不把它误归为本 Slice 的通过条件。最终 `python3 scripts/docs.py check` 对 216 个 current documents PASS。

当前仍只支持冻结的 Maven Structure Profile，更新是完整重建；没有 Scheduler、真 Delta、多源、其他语言、动态产品 Web
问答、模型调用或 Production Activation。SLICE-002、V-006—V-009 和最终 ITER-005 Acceptance 均未执行。
