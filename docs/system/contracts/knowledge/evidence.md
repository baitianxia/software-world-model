---
id: SYS-CONTRACT-KNOWLEDGE-EVIDENCE
kind: system-contract
status: current
authority: normative
owners: [knowledge]
depends_on: [SYS-CONTRACT-SOURCE-ARTIFACT, SYS-CONTRACT-KNOWLEDGE-SCHEMA-CORE]
derived_from: [DD-KNW-EVIDENCE]
code: [src/software_world_model/knowledge_engine/formal.py, src/software_world_model/knowledge_engine/structure.py, src/software_world_model/application_services/citation_projection.py, src/software_world_model/infrastructure/sqlite_formal_knowledge_repository.py, src/software_world_model/infrastructure/sqlite_structure_knowledge_repository.py, src/software_world_model/infrastructure/file_citation_observation_store.py]
tests: [tests/test_formal_knowledge.py, tests/test_artifact_processing.py, tests/test_structure_knowledge.py, tests/test_structure_publication.py, tests/test_citation_projector.py, tests/test_iteration_003_g2_integration.py]
---

# Evidence

## Purpose and scope

Evidence 是对一个 Artifact 中有界位置的来源观察，是正式命题的支持材料，不是结论、Snapshot 成员或普通 Knowledge Use 的直接回答旁路。

## Owner and public contract

Knowledge Engine 独占 Evidence Record 与 Evidence Snapshot 写权，但不得直接读取 Source。Source Integration 展开并授权 exact Artifact Read Package / Read Protection，并签发绑定当前持久使用的一次性 use confirmation；Knowledge Engine 消费这些证明后保存自包含的最小观察。模型只提出 Locator / Interpretation Proposal，平台重建。

## Invariants

1. 每条 Evidence 恰好绑定一个 Artifact 与有界 Locator。
2. Operation、Agent、模型响应、Telemetry 或自由文本摘要不能充当 Evidence。
3. Derived Artifact 只有在单一 Source Root、完整无环 Lineage、可回放 Locator 和已验证机械 Transformation Contract 成立时才可作为 Evidence 输入；语义变换不能伪装成直接观察。
4. Evidence 不定义全局 polarity 或 confidence；观察含义由使用它的 Fact Proposition 表达。
5. Zero Result 只在已证明封闭且完整的观察边界内成立。
6. Evidence 保留 Source Context；只能由直接可复核内容合法收窄，不能覆盖或扩大来源成立条件。
7. Evidence 不可变，并保存足以在来源变化或 Payload 淘汰后独立复核 exact observed content、Context 与 Provenance 的最小快照。
8. 正常 Knowledge Use 只读正式知识，不读取 Evidence Quote 补齐 Gap。
9. Evidence observation/payload 的物理可读边界必须与 `WORLD_MODEL` Query/回答进程分离。View/Query Result 密封后，trusted broker 只能按该 Result 固定的 typed Evidence ref allowlist 和 digest 从 Knowledge owner 重读自包含观察，并物化 Result-scoped disposable Citation Store；它不能让调用方自报或扩大 allowlist。Citation Projector 只读取 Result seal 与该 exact Store 并输出展示投影，不直接访问权威 Evidence Store，也不能把内容送回 Requirement、Plan、Query、Draft、Review、模型调用或答案进程。

## Failure and implementation boundary

Artifact 授权失效、Locator 越界、内容 Digest 不匹配、Lineage 不完整，或 use confirmation 未与 exact Materialization、Package / Closure、Read Protection、用途和 downstream request 一致时均拒绝。Record、Locator、Materialization 状态、身份公式和重试由代码与测试定义。
