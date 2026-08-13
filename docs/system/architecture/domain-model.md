---
id: SYS-ARCH-DOMAIN
kind: system-architecture
status: current
authority: normative
owners: [architecture, knowledge]
depends_on: [SYS-ARCH-OVERVIEW]
code: [src/software_world_model/knowledge_engine, src/software_world_model/application_services/evidence_answer.py]
tests: [tests/test_formal_knowledge.py, tests/test_knowledge_scope.py, tests/test_evidence_answer.py]
---

# 顶层领域模型

```mermaid
flowchart TD
    DS["Data Source + Binding"] --> AR["Artifact"]
    Q["Direct Question + Checklist"] --> EP["Sealed task Evidence Packet"]
    AR --> EP
    EP --> DA["Cited Answer Draft"]
    Q --> RV["Independent Answer Review"]
    DA --> RV
    EP --> RV
    RV --> AA["Authorized synchronous answer"]
    AR --> EV["Evidence"]
    EV --> CC["Entity / Fact / Inference Candidate Closure"]
    PS["Exact published premises / base Snapshot"] -.-> CC
    CX["Exact Context + Schema"] --> CC
    CC --> AD["Independent Admission"]
    AD --> PB["Atomic Publication"]
    KS["Knowledge Scope"] --> PB
    PB --> SN["Complete immutable Snapshot"]
    SN --> EN["Entity State"]
    SN --> FA["ASSERTED Fact State"]
    SN --> IN["Inference / Conflict State"]
    SN --> RB["Exact Snapshot Read Bundle<br/>no Evidence payload"]
    RB --> SV["Read-only Structure / Behavior View"]
    WQ["World Model Question"] --> WR["Exact Snapshot Read Session"]
    SV --> WR
    WR --> WA["Reviewed World Model Answer / Gap"]
    SN --> RS["Read Session"]
    RQ["Requirement + Needs"] --> AS["Sufficiency Assessment"]
    RS --> AS
    AS --> KA["Reviewed formal-knowledge query result"]
```

该图表达三条不同边界：Direct Investigation 把 Artifact 内容密封为只对当前问题有效的 Evidence Packet；Knowledge Update 把受审核 Candidate 原子发布为 Snapshot；World Model Query 只读 exact Snapshot/View 并返回受支持答案或 Knowledge Gap。三者不能静默互换。Candidate 内的 Inference 只能使用 exact Snapshot 中已发布的正式前提；同批 Candidate 之间的局部引用不会获得正式前提资格。

## 概念边界

- **Artifact** 是来源的中立、可追溯观察载体，不是知识结论。
- **Evidence** 是 Artifact 中有界且可定位的观察，不表达全局真假。
- **Evidence Packet** 是绑定原问题、检查清单、exact Target、来源操作和 Artifact 内容的不可变任务输入；它没有跨任务正式知识资格。
- **Answer Draft / Review Finding** 分别是可引用自然答案和独立审核意见；只有空 Finding 的 APPROVED Draft 可被授权。
- **Entity** 提供稳定身份；属性和关系由 Fact 或 Inference 表达。
- **Fact** 是在明确 Context 中由直接 Evidence 完整支持的命题。
- **Inference** 从已发布前提形成受控结论；Conflict 证明语义不兼容但不擅自选赢家。
- **Snapshot** 是单一 Scope 下完整、不可变、原子发布的正式知识状态。
- **Structure / Behavior View** 是 exact Snapshot 中 typed Entity Relation 的可重建只读组织，不创建知识；当前 Behavior 只覆盖 Java 静态调用子集。
- **Requirement** 固定任务语义；Sufficiency 必须逐 Need 从同一 Read Session 重建。

Knowledge Scope 保留三类稳定归属边界：

- **System Scope** 拥有单个软件系统的本地技术实体与知识。
- **Shared Component Scope** 拥有公共组件定义与静态知识；该组件在宿主系统中的运行观察仍归宿主 System Scope。
- **Business Domain Scope** 拥有跨系统 Business Entity 与业务语义；它通过对 exact upstream Snapshot 的 Fact / Inference 引用关联多个 System Scope，不复制或改变技术对象的归属。

Structure View 与 `JAVA_STATIC_CALL_GRAPH@1` 的最小 Behavior View 已接受；二者都不拥有知识、不改变充分性。完整 Behavior、
Business、History 和其他语言尚未接受，不能从当前子集推导其存在。
