---
id: FINDING-010-034
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [security, interface, operations]
depends_on: [ITER-010-SLICE-001, FINDING-010-029, SYS-QUALITY-SECURITY, SYS-OPS-LOCAL-BROWSER]
code: [src/software_world_model/interface/engineering_qa_preview_cli.py, src/software_world_model/interface/engineering_qa_alpha_cli.py]
tests: [tests/test_engineering_qa_preview_cli.py, tests/test_engineering_qa_alpha_cli.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: exclusive-create-private-gateway-database-and-sidecars
target: SYS-QUALITY-SECURITY
---

# FINDING-010-034：Alpha Gateway 数据库继承默认公开权限

## Observation

candidate `b6e13eb…` 的首次持续 Alpha 会话正确把 session configuration、launch receipt 和 terminal receipt 写为 `0600`，但
`gateway.sqlite3` 实际 mode 为 `0644`。该数据库保存 model-visible role input、Source evidence、Ledger、Package、Draft、Review 与 dispatch
audit，不能按普通非敏感缓存处理。

## Evidence and root cause

- launcher 只验证数据库目标是尚不存在的 absolute canonical path，然后直接把路径交给 `sqlite3.connect`；
- SQLite 因而按进程默认 umask 创建主文件，WAL/SHM sidecar 同样没有 private-mode 保证；
- receipt writer 已使用 `O_EXCL + 0600`，但数据库路径没有复用同一安全创建语义；
- 问题影响 prepared preview 与持续 Alpha 两个 launcher，是系统性本机数据暴露窗口，不涉及 Provider credential value 泄漏。

## Decision and disposition

两个 launcher 都必须在打开 SQLite 前用 `O_CREAT | O_EXCL` 原子创建主文件并 `fchmod(0600)`；并发占用失败关闭。数据库及 listener 的整个
存活期使用 `0077` private creation mask，保证 SQLite `-wal` / `-shm` sidecar 从创建起就是 `0600`，退出后恢复调用进程原 umask。不能以
事后 chmod 修补已经出现的可读窗口。

该规则写回 Security Boundary 与 Local Browser Operations；不改变 Source、Provider 或 Production 权限。

## Verification

测试在真实 file-backed WAL SQLite 上写入敏感占位数据，并在连接存活时核对主文件、`-wal` 和 `-shm` 均为 `0600`；Alpha main 顺序测试
另核对启动时创建的 Gateway 主文件 mode。现有 path collision、receipt 顺序、零 dispatch 启动和 graceful terminal 行为保持通过。
