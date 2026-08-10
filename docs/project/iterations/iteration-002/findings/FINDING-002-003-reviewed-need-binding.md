---
id: FINDING-002-003
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, architecture]
depends_on: [SYS-CONTRACT-KNOWLEDGE-FACT]
code: [src/software_world_model/knowledge_engine/formal.py, src/software_world_model/infrastructure/sqlite_formal_knowledge_repository.py, src/software_world_model/ai_infrastructure/agentic_knowledge_strategy.py]
tests: [tests/test_formal_knowledge.py, tests/test_agentic_knowledge_strategy.py]
iteration: ITER-002
classification: system-contract
disposition: updated-current-fact-contract
target: SYS-CONTRACT-KNOWLEDGE-FACT
---

# FINDING-002-003：事实覆盖复核需要保留 Need 绑定

## Observation

事实文本即使由 Evidence 支持，也不能仅凭词汇相似度证明它覆盖了哪个用户 Need。若审核后的 Need 绑定在持久化时丢失，后续 Sufficiency 可能重新猜测覆盖关系。

## Evidence / reproduction

旧 `ReviewedFactGrounding` 没有 Need IDs，SQLite 重建后的 `FormalKnowledgeRecord` 也无法恢复该审核结果。当前策略的逐 Need 覆盖复核需要 exact 绑定才能避免跨 Need 借用事实。

## Impact

该信息跨越 Strategy、Knowledge Engine 和持久化边界，并直接支撑 `INV-011`，属于正式 Fact 使用边界的一部分。

## Classification rationale

这不是单个 SQLite 字段的局部细节；它约束 Fact 如何保留审核得出的 Requirement 适用范围，因此归类为 system-contract。

## Decision and disposition

Fact Contract 增加审核 Need 绑定不丢失、不可由读取方猜测或扩张的规则。`ReviewedFactGrounding@2` 和 Repository round trip 提供实现，旧记录缺失时恢复为空绑定而不是制造默认覆盖。

## Verification after disposition

`tests/test_formal_knowledge.py` 验证新摘要和持久化往返；Strategy 测试验证逐 Need 覆盖只消费审核绑定。
