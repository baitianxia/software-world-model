---
id: FINDING-003-006
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-003-SLICE-001, SYS-CONTRACT-KNOWLEDGE-PERSISTENCE]
code: [src/software_world_model/infrastructure/sqlite_legacy_formal_reader.py]
tests: [tests/test_legacy_formal_reader.py]
iteration: ITER-003
classification: local-implementation
disposition: recompute-legacy-record-and-evidence-authority
target: src/software_world_model/infrastructure/sqlite_legacy_formal_reader.py
---

# FINDING-003-006：Legacy 读取器未闭合对象与 Snapshot authority

## Observation

Legacy compatibility reader 初版验证 manifest 中的 `object_digest` 等于对象表中存储的 `object_digest`，但没有从完整 Entity/Fact/Inference/Evidence 字段重新计算 identity 与 digest。只修改 label、locator 或 excerpt 而保留旧摘要时仍会被读取。

完成摘要重算后，对抗复核又发现 Entity/Fact support 没有强制 Evidence kind，协调重算后可用 Snapshot member 冒充 Evidence；Snapshot manifest 虽包含 predecessor，却没有验证 revision 1 空 predecessor、连续同 Scope predecessor、无环与旧成员保留。通用 reference parser 还错误拒绝了旧 admission 实际允许的重复 Evidence/premise refs。

## Evidence

- 初版 SELECT 没有读取重算所需的完整 context、subject、rule、grounding 与 Evidence 内容字段。
- 对 disposable legacy database 副本只修改 Entity label 或 Evidence locator/excerpt，可复现 manifest 比对仍通过。
- 把 Fact support 改成 Entity ID 并协调重算 Fact ID/object/manifest，旧 reader 会递归继承 Entity locator 后接受。
- 把 revision 1 predecessor 改成自身并协调重算 manifest，旧 reader 仍接受；旧 Formal publisher 则固定连续链并累加保留成员。

## Impact and classification

Legacy Snapshot 的不可变 identity/digest 规则已经冻结；缺口只在 read-only adapter 的校验完整性，不改变当前 persistence contract，因此属于 local implementation。

## Decision and disposition

adapter 继续使用 SQLite immutable read-only URI，但读取完整 authority 字段，并按 `INITIAL@1` 的原始 canonical digest 公式重算 Context、Entity、Fact、Inference 与 Evidence identity/digest；Entity/Fact support 只接受 Evidence，Inference premise 才能指向 exact manifest member。逐级验证 predecessor 存在、同 Scope、revision 连续、无环及 additive member/digest 保留。为保持所有旧合法 Snapshot 可读，不额外禁止旧 admission 允许的重复 support refs。协调重哈希、类型混淆和 predecessor 反例必须以 `AUTHORITY_RECORD_INCONSISTENT` 闭合失败。
