---
id: FINDING-003-003
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-003-SLICE-001, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE, SYS-CONTRACT-KNOWLEDGE-ADMISSION, SYS-CONTRACT-KNOWLEDGE-SNAPSHOT-PUBLICATION]
code: [src/software_world_model/application_services/maven_structure_update.py, src/software_world_model/knowledge_engine/structure_authority.py, src/software_world_model/knowledge_engine/structure_publication.py, src/software_world_model/infrastructure/sqlite_maven_structure_update_repository.py, src/software_world_model/infrastructure/sqlite_structure_knowledge_repository.py]
tests: [tests/test_maven_structure_update_authority.py, tests/test_structure_publication.py, tests/test_maven_structure_update.py]
iteration: ITER-003
classification: local-implementation
disposition: close-existing-update-authority-chain
target: src/software_world_model/application_services/maven_structure_update.py
---

# FINDING-003-003：Maven 更新初版未闭合既有 Authority 链

## Observation

G1 首次组合 Source operation、Maven evaluator 与 Snapshot publisher 时，成功路径可以直接把 evaluator batch 发布为 CURRENT，却没有先证明既有 Build Objective、exact Canonical Target、Schema Registry Availability 和独立 Admission ACCEPT；更新 Attempt/Result 也只存在于调用栈中，重启后无法按幂等键恢复。

继续做公共入口和故障窗口审计时发现，初版 Admission assessment 允许 Application 同时提供
candidate 与“verified”两侧，或仅凭可伪造的 verifier 字符串建立 PASS。Publisher 还可能信任
调用方传入但未持久化的 receipt/Admission。Knowledge publication 已提交而 Application Result
写入失败时，旧逻辑会把真实成功投影为 FAILED；反向地，未知 publication outcome 又可能在重试时
重新 dispatch Source effect。

## Evidence

- 构造 `MavenStructureUpdateRequest` 时只接收调用方字符串，没有 Objective/Target authority record。
- publisher 初版只校验 batch，自身没有 Admission decision 或 Schema adoption 输入。
- update service 初版没有 durable Attempt/Result repository；同键重试只能依赖下游 source/publication 副作用。
- 用同一 public verifier ref 构造恶意 assessment service，可把删边 batch 自签为 PASS；仅比较
  字符串无法证明 verifier authority。
- 在 Knowledge commit 后注入 Application Result 写失败，可复现 CURRENT 已前进而 durable Result
  被误记为失败；unknown outcome 重试若重新采集来源则会产生新 Operation intent。

## Impact and classification

上述要求已经由当前 System Contract 与本轮 Slice 明确规定，发现没有改变 Owner、接口语义或一致性规则；它暴露的是新实现尚未接齐既有 authority closure，因此属于 local implementation。

## Decision and disposition

更新请求必须携带已解析的 Objective、exact Canonical Target 和显式
`requirement_binding=None`；固定 Maven Structure Schema 经 Proposal/Review 后注册。Repository
为配置的 verifier 签发不可伪造 capability，独立 verifier 只能通过受限 replay 从 exact
Source/Artifact closure 重建 candidate/evaluation/report/batch；Assessment 同时保存 candidate 与
verified 两侧，Admission 和 Publisher 都重读 exact persisted Assessment/Admission 并校验同一
capability。

Attempt/Result 按请求摘要与幂等键持久化。Publisher 只接受 owner-read 的 Publication receipt；
Knowledge commit 后的 Result 写失败先查询并协调为同一 PUBLISHED Result，无法判定时保存
`OUTCOME_PENDING`。后续重试复用 exact child idempotency key、Admission 和 package-bounded replay，
不得重新 dispatch Source Operation；fake/unpersisted receipt、同 ref 自签、缺边 verifier closure、
before/after-commit failure 与 unknown outcome 都由故障测试闭合。
