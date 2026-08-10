---
id: FINDING-003-009
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, architecture, security, quality]
depends_on: [ITER-003-SLICE-001, SYS-ADR-014, SYS-ARCH-DEPLOYMENT, SYS-CONTRACT-KNOWLEDGE-EVIDENCE, SYS-CONTRACT-KNOWLEDGE-PERSISTENCE, SYS-CONTRACT-APPLICATION-STRUCTURE-VIEW, SYS-QUALITY-SECURITY]
code: [src/software_world_model/application_services/citation_projection.py, src/software_world_model/infrastructure/file_citation_observation_store.py, src/software_world_model/interface/structure_view_cli.py, src/software_world_model/interface/citation_projector_cli.py, validation/structure_world_model_iteration_003/isolation/answer_workload.py, validation/structure_world_model_iteration_003/isolation/projector_workload.py]
tests: [tests/test_structure_view.py, tests/test_structure_view_cli.py, tests/test_citation_projector.py, tests/test_iteration_003_g2_integration.py, tests/test_iteration_003_g2_isolation.py]
iteration: ITER-003
classification: system-contract
disposition: result-scoped-disposable-citation-store
target: SYS-ADR-014
---

# FINDING-003-009：Citation Projector 需要 Result-scoped 最小观察存储

## Observation

G2 初版若让 Citation Projector 直接挂载包含全部自包含 Evidence observation 的权威
Evidence Store，虽然仍与 answer worker 分离，却给展示进程开放了超出密封 Structure View
Result allowlist 的物理读取面。实现进一步发现，只有 Evidence ID 列表不足以安全复制正文：还必须
把 View Result digest、完整 typed Evidence metadata allowlist、allowlist digest、逐 observation
digest 和 Store manifest digest 绑定在同一个不可变封印中，才能拒绝缺失、额外、重复、换序或篡改
的 observation。

## Evidence

- `StructureViewResult` 从 Support Map 机械派生 canonical Evidence allowlist；调用方不能另行自报
  allowlist。
- `CitationObservationBroker` 只接受实际 typed View Result，通过 Knowledge owner 的窄
  `get_evidence` Port 重读 allowlisted observation，并拒绝 metadata 或 digest 不一致。
- `FileCitationObservationStoreWriter` 创建新的、可删除的 Result-scoped Store；Store manifest
  同时绑定 Result、allowlist 和全部 observation file digest。Reader 要求物理文件集合与 manifest
  精确相等并拒绝 symlink、路径逃逸、非 canonical JSON 和未知字段。
- `CitationProjector` 只组合只读 Store Port 与 Result seal，没有 Knowledge Repository、Source、
  Query、Update、模型、网络或答案回传 Port；G2 隔离策略只向它开放 package、seal、该 Store 与
  独立输出目录。
- 对抗测试覆盖自签 seal、跨 Result Store、缺失/额外/重复 observation、篡改引用/正文/manifest、
  symlink 和路径逃逸。

## Impact and classification

这改变了 System 文档中 `Evidence Store → Citation Projector` 的物理安全拓扑，涉及
Knowledge/Application/Interface 的跨 Owner 引用和最小权限边界，不是文件布局或私有 codec
选择，因此分类为 `system-contract`。它不改变 Evidence 或 Snapshot 的领域所有权，也不让
disposable Store 成为新的知识权威。

## Decision and disposition

保留更窄的三阶段路径：密封 View/Query Result → trusted broker 按 exact allowlist 从
Knowledge owner 物化 disposable Citation Observation Store → 独立 Projector 只读 seal 和该
Store。Broker 属于受控应用编排，不进入 answer worker；Store 是 Result-bound、可删除、可重建的
展示输入，不拥有 Evidence、Snapshot 或 Result。浏览器或隔离评测展示 Sink 分别读取密封答案
结果和 Citation Projection，正文不得回流 Requirement、Plan、Query、Draft、Review、模型或
answer worker。

该决定作为 `SYS-ADR-014` 已有 Snapshot-first 隔离后果的精化，并同步写回 Deployment、
Components、Security、Evidence、Persistence 与 Structure View 的唯一当前正文；不新增领域
Owner，也不以本 Finding 或后续 Result 代替 System Contract。

## Verification after disposition

Contract/Fault tests 必须证明 seal 只能从实际 View Result 派生，Store 物理集合严格等于
allowlist，任一身份、digest、正文、顺序、路径或文件类型异常均失败关闭。V-007 仍必须在真实
独立 Projector 进程中保存 Store inventory、seal/manifest/projection digest、拒绝探测和单向
Result 传递；单元测试不能把 G2 标记为 PASS。
