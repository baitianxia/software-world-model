---
id: PROJECT-REFERENCE-DEPLOYMENT-HISTORY
kind: implementation-reference
status: historical
authority: historical-evidence
owners: [engineering, operations, project]
depends_on: [SYS-ARCH-BASELINE]
code: []
tests: []
coding_input: false
source_path: docs/system/architecture/deployment.md
as_of: 2026-10-02
---

# deployment implementation history

以下内容从部署附录迁出，保留具体实现、评测和 OS 隔离记录。它们不是概要部署架构，也不能把当前实现状态当作架构授权或生产资格。

现有 Direct Investigation 与管理实现曾以 Python 模块化单体和 SQLite Repository 部署；本机 `EVALUATION_ONLY` 的 `WORLD_MODEL` 入口曾由
loopback application 与 trusted launcher 组成。launcher 从 verified dynamic Catalog 选择 exact no-payload Read Set，并为每个问题启动
文件与网络能力隔离的 Answer、Gateway、Citation Broker 和 Citation Projector workload。首次 Product Validation 的 subject 为 `CANDIDATE`；
运行后证据与人工接受不能被启动器预先声称。这条评测路径不是 Production Activation，也不能被旧 `http_api` 或 iteration-specific validation
launcher 替代。

交互 launcher 曾要求重新验证 candidate commit/tree、protected stage/role entrypoints、product launcher files、Provider subject、确定性资格、
held-out suite/independent evaluator 和 disclosure authorization，并执行 Workspace/authority targets 的外部可达与 OS isolation preflight。
每个 HTTP question 使用新的私有 run root 和 request identity，最多进行一次 Provider dispatch；Citation 由独立 GET 按 request/result/seal/
projection digest 重新绑定和验签。

历史 OS 隔离实现曾使用 capability sandbox、继承的 `0600` AF_UNIX descriptor、macOS Seatbelt、`syscall-unix` firewall、Darwin
`disconnectx`/`connectx` 以及 `remote tcp "*:443"` 等机制，并审计 `connect`/`bind`、fork、listener handoff、TLS 和 Provider dispatch。
这些机制只证明当时 workload 的有限边界，不能被描述为精确目的地址防火墙或抵抗任意 native code execution 的完整隔离；实际部署必须
如实记录采用的机制和可证明范围。
