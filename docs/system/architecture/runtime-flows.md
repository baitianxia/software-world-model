---
id: SYS-ARCH-FLOWS
kind: system-architecture
status: current
authority: normative
owners: [architecture, application]
depends_on: [SYS-ARCH-COMPONENTS, SYS-ARCH-INVARIANTS]
code: [src/software_world_model/application_services, src/software_world_model/interface]
tests: [tests/test_knowledge_update.py, tests/test_knowledge_use.py, tests/test_agentic_runtime.py]
---

# 运行主流程

## 来源配置

Application 校验管理命令，经 Source Integration 创建稳定 Data Source 和 Binding；Scope Assertion 只证明本次精确修订的生命周期资格。配置成功不证明来源可达、存在 Artifact 或已有知识。

## 知识更新

```text
Build Objective
  + optional Requirement Revision / Gap binding
  → Canonical Build Target
  → authorized bounded source investigation
  → Artifact / Evidence
  → Candidate bundle
  → independent Admission
  → application acceptance
  → atomic Snapshot publication
```

首次、手动和计划更新使用自己的 Build Objective，不伪造 Requirement Binding；只有任务驱动更新才可以绑定某个 Requirement Revision / Gap。每一步产生自己的权威结果。Proposal、Admission ACCEPT、Application PASS 和 PUBLISHED 不能互相替代；发布失败保持旧 CURRENT。

## 知识使用与回答

任务冻结 Requirement Revision，打开固定 Snapshot 的有效 Read Session，对每个 Need 和 Joint Constraint 建立可重建证明。只有该有效 Session 内的语义不足才形成 Gap；访问、执行、Session 或 Schema 失败必须保留为失败或限制。只有全部 Need 满足才可声明 SUFFICIENT。答案候选随后接受独立 Claim Review、授权和唯一交付，答案文本不能补齐知识缺口。

## 模型资格

Provider Contract Conformance 证明 Adapter 接口成立；Capability Evaluation 证明精确 Strategy 适合业务能力；Product Validation 证明端到端用户价值；显式 Activation 决定可用范围。四者独立且按精确实现、模型、配置和有效期绑定。
