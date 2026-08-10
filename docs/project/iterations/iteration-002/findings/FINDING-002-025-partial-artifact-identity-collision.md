---
id: FINDING-002-025
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, source]
depends_on: [ITER-002-SLICE-001, FINDING-002-024]
code: [src/software_world_model/infrastructure/sqlite_source_operation_repository.py]
tests: [tests/test_source_operations.py]
iteration: ITER-002
classification: system-contract
disposition: include-coverage-in-artifact-identity
target: SYS-CONTRACT-SOURCE-ARTIFACT
---

# FINDING-002-025：同一路径的分段读取会发生 Artifact 身份碰撞

## Observation

Local Git Artifact 身份原先绑定来源、版本、路径和 Tool，但没有绑定实际字节 Coverage。同一大文件的第二段 READ 因路径相同取得相同 identity digest，却具有不同 content digest，Repository 会把合法续读误判为不可变来源内容漂移。

## Impact

证据优先路径必须支持任意工程中的大文件和有界分段读取；该缺陷会使授权续读失败，并可能迫使调查停在不完整证据。问题属于通用 Source Artifact 身份契约，不是模型策略问题。

## Decision and disposition

Artifact identity strategy 升级为 `local-git-artifact@2`，把 Source Observation 的 exact Coverage 纳入身份。相同路径、版本和范围仍保持稳定幂等；不同范围形成不同 Artifact。`SYS-CONTRACT-SOURCE-ARTIFACT` 已增加该不变量。
