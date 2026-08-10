---
id: FINDING-003-005
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-003-SLICE-001, SYS-CONTRACT-SOURCE-DATA-SOURCE, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE]
code: [src/software_world_model/source_integration/local_git.py, src/software_world_model/source_integration/operations.py, src/software_world_model/application_services/maven_structure_update.py, src/software_world_model/interface/runtime.py]
tests: [tests/test_source_operations.py, tests/test_maven_structure_update_authority.py]
iteration: ITER-003
classification: local-implementation
disposition: seal-source-dispatch-authority-closure
target: src/software_world_model/source_integration/operations.py
---

# FINDING-003-005：Local Git dispatch 未完整封闭 selector 与 authority

## Observation

Local Git binding selector 接受 `commit`、`comparison_base` 和 `comparison_head`，但 Source Operation 执行初版只从 selector 取 `paths`。调用方因此可以在同一已授权 binding 下提交不同 revision，绕过声明的 revision 范围。

修复 revision 比对后继续做 ref-moving 反例时，还发现 fence 与 connector 会分别解析同一个符号 ref；两次解析间 ref 移动可使检查 A、读取 B。另一个反例可把 INTERNAL eligibility 与 PUBLIC intent 组合，旧重验证没有比较 classification 与完整 eligibility digest，最终产生 PUBLIC Artifact。

对更新入口继续审计时又发现，Canonical Target Resolution 与 Maven Target Authority
虽然使用 public Local Git resolver，却没有消费 Binding selector。commit-pinned A 的 Binding
可先为 B 形成 exact Target Receipt，并把更新 Attempt 推进到 PREPARING；直到后续 TREE/READ
Operation 才失败，导致越界目标已经在 Application authority 中生效。

## Evidence

- `normalize_selection()` 接受上述字段，`SourceOperationService.execute()` 只把 `_selector_paths(...)` 传给 connector。
- 绑定 commit A 后请求 commit B，旧路径会成功读取 B；comparison 两端同样没有与 binding selector 对照。
- 绑定 A 后请求符号 ref `moving`，在 fence 通过后把 ref 从 A 移到 B，旧路径实际读取 B。
- 替换 intent classification 而保留另一 classification 的 eligibility，或篡改 eligibility digest，旧路径仍可完成。
- Binding 固定 commit A 后，用未绑定 selector 的 resolver 构造 commit B Target，
  `MavenStructureUpdateAuthorityService.prepare()` 旧路径返回 PREPARING；固定 A→B comparison
  时交换 B→A 也可形成 exact receipt。

## Impact and classification

Source Contract 已要求 operation 受 binding selector/effective range 约束；这是 Local Git provider 与 dispatch fence 的实现缺口，不改变系统语义，因此属于 local implementation。

## Decision and disposition

配置阶段只接受完整 canonical OID，comparison 两端必须成对，commit 与 comparison 互斥。Target Resolution 与 Maven Target Authority 都必须调用 Source Integration 拥有的 binding-aware resolver；它先把 proposal 固定为 full OID，再复用 dispatch selector fence，越界目标不能产生有效 Target authority。DISPATCHED 后重新验证完整 eligibility closure，把请求 revision（COMPARE 同时包括 base）解析并冻结为 full OID，再将冻结参数传给 connector；不得再次使用符号 ref。intent/eligibility classification 必须相同，重验证除诊断性 `resolved_at` 外逐字段比较并核对 digest。不匹配持久化失败且不产生 Artifact。路径-only selector 保留本轮 A/B 更新所需的多 revision 范围。
