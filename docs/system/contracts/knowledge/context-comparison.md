---
id: SYS-CONTRACT-KNOWLEDGE-CONTEXT-COMPARISON
kind: system-contract
status: current
authority: normative
owners: [knowledge]
depends_on: [SYS-CONTRACT-KNOWLEDGE-REFERENCE-CONTEXT, SYS-CONTRACT-X-CAPABILITY-EXECUTION]
derived_from: [DD-KNW-CONTEXT-COMPARISON]
code: [src/software_world_model/knowledge_engine/formal.py, src/software_world_model/application_services/knowledge_use.py]
tests: [tests/test_formal_knowledge.py, tests/test_knowledge_use.py]
---

# Context Comparison

## Purpose and scope

Context Comparison 在明确 Purpose 下判断两个 exact Context 的关系，为知识组合、任务读取或冲突分析提供 basis。它不创建 Fact、Inference 或用户可见 Claim。

## Owner and public contract

Knowledge Engine 拥有 Assessment 与 Validity。确定性规则或持有 exact delegated capability grant 的模型 Strategy 可以产生 Proposal，但 Knowledge Engine 必须从 exact 输入、Purpose、Strategy execution identity 与该 Grant 重建封存结果；它不读取 Application 的 Evaluation / Activation Store。

## Invariants

1. 比较必须声明 Purpose；同一 Context 对不同用途可能有不同可用关系。
2. 执行失败与语义 `UNKNOWN` 分离，不能互相投影。
3. Difference、Incompatible 与 Conflict 是不同结论；Comparison 不擅自选择赢家。
4. Assessment 不得成为 Fact/Inference 的隐藏前提或直接对外 Claim。
5. 复用绑定 exact inputs、canonicalizer、Strategy execution identity、delegated grant 与 Validity；任一漂移使旧结果单调失效。
6. 若跨来源 Context 关系本身需要成为用户可见语义或 Inference 前提，必须形成 Fact / Inference 并经过 Admission 与 Publication；Assessment 只在 exact Purpose 下充当组合门禁。

## Failure and implementation boundary

输入不完整、delegated grant 失效、规则冲突或模型 Proposal 无法机械重建时拒绝 Assessment。Request/Assessment DTO、组合算法、状态和错误由代码与测试定义。
