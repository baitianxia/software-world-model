---
id: SYS-CONTRACT-APPLICATION-STRUCTURE-VIEW
kind: system-contract
status: current
authority: normative
owners: [application]
depends_on: [SYS-ADR-005, SYS-ADR-014, SYS-CONTRACT-KNOWLEDGE-STRUCTURE-MODEL, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE]
code: [src/software_world_model/application_services, src/software_world_model/interface]
tests: [tests/test_knowledge_use.py, tests/test_browser_chat_interface.py]
---

# Structure View

## Purpose and scope

Structure View 把 exact Snapshot 中已经发布的 Structure Model 组织为模块、直接边、路径和 Snapshot 差异。它是可重建的只读派生结果，不拥有知识、不读取 Source，也不决定任意问题是否充分。

## Input and output contract

普通查询必须固定 Scope、Snapshot ID、Schema、Context、Profile、权限和查询预算。比较查询固定同一 Scope 下有明确 base/target 顺序的两个 exact Snapshot；每个 `CURRENT` 只可在入口解析一次。输出至少保留：

- View ID、一个 exact Snapshot ID 或有序 base/target Snapshot IDs、对应 source revisions、Profile 与 Coverage Root/States；
- Entity Root ID、Entity State ID、类型、显示字段；
- Fact Root ID、Fact State ID、source Entity ID、predicate、target Entity ID；
- Evidence Reference、Artifact Reference 与 locator；
- Coverage 状态、View Limitation、Conflict、truncation、pagination 和 query completeness。View Limitation 只描述本次投影为何不完整；它不是对某个 Requirement 的 Knowledge Gap 判定。

`entity_candidates` 是路径/邻域操作前的通用受控解析：输入保留原始 mention 及用户明确给出的 Entity type、Root ID、canonical GA/GAV 等限定，只在 exact Snapshot State 的公开 identity/display 字段上执行 frozen NFC/trim/case-preserving 匹配，输出 0/1/N 个 typed Root/State Ref、命中字段和歧义状态。它不创造身份或关系；只有唯一候选，或用户在新的显式请求中选择 exact Ref，才可绑定后续 typed argument。0/N 候选返回 Entity Resolution Limitation，不能按 label、列表顺序或模型偏好选一个。

路径只沿明确 Relation Fact 遍历；零路径、单路径、多路径和截断是不同结果。Snapshot diff 只能在已验证兼容的有序 Read Set 中比较 Root membership 与 State 变化，必须区分新增、删除、保持与状态变化，不能从 label 或列表顺序推断。

## Invariants

1. View 只能读取 exact Snapshot/Read Set 的公开 Knowledge Port；隔离模式下该 Port 只能由已验证且不含 Evidence payload 的 exact Snapshot Read Bundle 实现。View 不能直接访问权威数据库、Evidence Store、SQLite、Source Provider 或模型会话。
2. View 不按名称补边、不隐藏悬空端点、不把 `dependencyManagement` 或传递可达性伪装成直接依赖。
3. View `READY` 只表示所请求投影可读；Coverage 不足时必须返回 View Limitation。只有 Knowledge Use 把该结果与 exact Requirement/Need 对照后，才能形成 Knowledge Gap；View 不能证明任意软件结构问题已充分。
4. 同一输入产生可验证的稳定结果；缓存可以删除和重建，不能成为第二权威。
5. 世界模型回答只能引用当前 View 输出及其 Support Map；需要源码调查时必须结束当前模式并由用户显式启动独立 `DIRECT_INVESTIGATION`。
6. 结构查询、路径、diff、规划、生成和审核只能读取 Read Bundle 中的 Entity/Fact State、Coverage 及 Evidence ref/locator/digest，禁止读取或重解析 Evidence excerpt/POM bytes。引用展示由 Query Result 密封后的独立 Citation Projector 进程从未挂载给答案进程的 Evidence Store 读取 Knowledge Engine 已保存的自包含 observation；不得重新访问 Source/工作树，也不得把 excerpt 回流到 Query Result、模型或审核。Artifact Reference 只用于 provenance 身份。
7. 输出必须显式携带关系的 Profile 与 modality。本版 `CONTAINS_MODULE` 是 software system 对递归 child module 的扁平成员关系，不表达 Maven aggregator/parent 层级；`DEPENDS_ON` 是 POM 本地声明的直接内部依赖，不是 effective、传递、compile 或 runtime 依赖图。
8. 需要 EntityRef 的 operation 只接受用户输入中已有的 exact Ref，或同一 Read Session 中已密封的唯一 `entity_candidates` 结果。模型直接生成、名称哈希、跨 Session candidate 或歧义候选均拒绝。

## Failure and implementation boundary

Snapshot 不存在、Schema/Profile 不匹配、权限失败、端点闭包破坏、分页不完整或预算耗尽均失败关闭。DTO、路径算法、排序和缓存属于实现，但不能改变 typed endpoint、exact Snapshot 和 Support 完整性。
