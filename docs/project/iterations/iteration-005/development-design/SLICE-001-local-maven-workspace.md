---
id: ITER-005-SLICE-001
kind: development-slice
status: completed
authority: historical-development
owners: [engineering]
depends_on: [ITER-005-PROPOSAL, SYS-CONTRACT-APPLICATION-MANAGEMENT, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-CONTRACT-KNOWLEDGE-STRUCTURE-MODEL, SYS-CONTRACT-KNOWLEDGE-SNAPSHOT-PUBLICATION, SYS-CONTRACT-KNOWLEDGE-PERSISTENCE, SYS-CONTRACT-APPLICATION-STRUCTURE-VIEW, SYS-QUALITY-ACCEPTANCE]
code: [src/software_world_model/application_services, src/software_world_model/infrastructure, src/software_world_model/interface]
tests: [tests]
iteration: ITER-005
coding_input: false
---

# SLICE-001：Maven 工作区、独立更新与动态 Read Set

## Status and dependencies

本 Slice 已由用户于 `2026-08-11T18:10:12+08:00` 授权。它复用现有 Maven Structure Kernel、Publication、Read Session
与 Bundle，不修改 Schema 或关系语义。G0 已在无产品代码改动的 baseline `a91dc7c…` 上通过：TTL3 与 Gson 两个支持
case 均为 COMPLETE，Maven Wrapper valid→unsupported 序列准确拒绝并保持旧 CURRENT；报告 digest 为
`sha256:bcd7a269…`。

实现与 V-002—V-005 证据已完成；[SLICE-001 Result](../results/slice-001-workspace-catalog.md) 的主报告 digest 为
`sha256:7047522d…`，全量回归 771/771 PASS。用户已接受本 Slice，并随后接受整个 ITER-005；本文件不再授权产品代码修改。

## Current vs expected behavior

当前底层命令可以完成单步操作，但用户必须手工传递 Scope、Source、Binding、Snapshot、Session 和 Bundle ID；执行结果
也不会形成可跨重启发现的项目/Read Set 目录。期望增加一个窄的管理工作流，把已有 Owner 操作组合成可恢复步骤，并让
成功 Bundle 成为动态、只保存权威引用的可查询 Read Set。

## System contracts and invariants

1. 输入使用用户确认的 stable workspace/system key、本机 Local Git 路径、root POM 和 exact full commit；`HEAD` 或 branch
   最多在管理入口解析一次，保存结果只称该 exact revision，不声称自动最新。
2. Update 在零 Question/Task/Session 状态独立运行。任何 question endpoint 都不能创建或恢复 Update Attempt。
3. 当前实现是 `FULL_REBUILD`：完整 TREE/POM 扫描后执行 `REPLACE_COVERAGE`。界面、报告和 Telemetry 不得称真增量。
4. 管理工作流遵守跨 Owner 非原子语义：Snapshot 发布后 Bundle 失败时保留 Snapshot 和真实 Step Result，将新版本标为
   `READ_BUNDLE_UNAVAILABLE`；旧 queryable 版本不受影响。
5. Application Management 拥有 Workspace/Version/Attempt/Step；Application Knowledge Use 拥有 queryable Read Set
   registration 与 Catalog manifest；Knowledge/Bundle owner 继续拥有 Snapshot、Session、Bundle Receipt。Infrastructure
   只实现存储，不能合并这些权威。
6. Catalog canonical schema 固定为 `SWM-READ-SET-CATALOG@1`。允许字段只有 schema、catalog ID/revision、producer
   commit/tree、生成时间、entries、previous catalog digest 和 document digest；每个 entry 只有 read-set/workspace/
   Scope identity、ordered Snapshot IDs/source revisions、Schema/Context/Profile/Coverage refs+digests、完整序列化 Bundle
   Receipt、Bundle-root-relative normalized locator、完整 file manifest/digest 与 availability。repository/source/authority DB
   path、Entity/Fact、Evidence/Artifact payload 和任意自由扩展字段全部拒绝。
7. trusted process 先写 immutable Catalog manifest，再以 CAS 更新只含 exact ID/revision/digest 的 current pointer。读取进程
   只挂载只读 Catalog root 与 Bundle root，先按 canonical encoding 重算 document digest、解析 current pointer，再逐项验证
   embedded Receipt 与 Bundle file manifest；无需权威数据库。Catalog 删除后可从 owner Receipt 重建，不拥有知识。
8. 单 Snapshot 与 ordered A→B Read Set 都固定 exact IDs 和顺序。后续 CURRENT 或 Catalog current pointer 移动不改变已
   选择/打开的 Read Set。
9. `READ_BUNDLE_UNAVAILABLE`、Coverage 非 COMPLETE、Receipt/digest 漂移或 CAS 冲突均不得进入 queryable Catalog。

## Interfaces and affected code

- 高层 Workspace Management application service：register、update、resume、list versions/read sets；
- 持久化 Workspace/Version/Step/Read Set registration，并生成独立密封 Catalog artifact；复用 Owner 的
  idempotency/result references；
- 一个面向人的 CLI 工作流，隐藏跨命令 ID 搬运，但完整输出每个权威引用和失败步骤；
- 复用现有 `ApplicationRuntime.build_maven_structure`、Read Session 和 Bundle service，不复制构建逻辑；
- 修正现有页面/数据集对插件、属性、父子结构的错误 Coverage 宣称并加契约测试。

具体 DTO、命令名和表结构由代码与测试决定，但不得改变上述 authority、恢复和隔离语义。任何产品代码前先把 Workspace
与 sealed Catalog 的 Owner/public contract 写回 `SYS-CONTRACT-APPLICATION-MANAGEMENT`、
`SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE` 和 `SYS-CONTRACT-KNOWLEDGE-PERSISTENCE`。

## Compatibility, data and security boundaries

现有 ITER-003/004 Snapshot、Bundle、固定 launcher 与 Direct browser 保持可读；本 Slice 不迁移旧 Schema，不激活模型，
不修改问答端口。Local Git 只对管理/Update 进程可见；Source path、POM bytes 与 Evidence payload 不进入 Catalog。数据库和
Bundle root 必须显式配置，Secret 不适用。

## Open questions and implementation risks

- G0 可能证明当前 Evaluation Context 对真实多模块项目过窄；此时先形成失败 Result，再决定未来 Profile 扩展，不能放宽
  complete Coverage 或按名称连边。
- 跨步骤恢复容易把“Snapshot 已发布、Bundle 未生成”误报成全局失败或回滚；故障测试必须覆盖进程中断与重放。
- 动态 Catalog 若保存 Entity/Fact 副本，会形成第二权威；代码评审和篡改测试必须阻断。
- 大仓库完整重建可能成本过高；本轮只测量，不提前实现 Delta。

## Acceptance scenarios

### G0 — Current-code generalization preflight

冻结两个未参与实现的多模块 Maven repo，以及第三个 repo 在同一 Scope/Binding/root POM 下的 valid baseline commit 和
unsupported commit；每个输入都固定 exact identity 与不导入产品代码的结构/拒绝 Oracle。只用当前 public CLI 运行：
两个支持 case 必须 COMPLETE 且 Entity/Relation/absence 与 Oracle 一致；拒绝序列必须先发布 valid CURRENT，再对
unsupported commit 准确拒绝并证明 CURRENT 仍是 valid Snapshot。任何一个支持 case 失败都停止后续编码并产出人工
兼容性报告。

### G1 — Zero-question workspace update

从空数据库登记 repo R1，在 Questions/Tasks/Sessions 均为 0 时构建 Snapshot 和 Snapshot Bundle；提交 R2 后显式更新，
验证 Root 稳定、State 变化、删除正确、CURRENT 指向 R2、R1 仍可 exact 读取。报告显示 exact commit、Profile、Coverage、
Entity/Relation、Source calls/bytes/time、Snapshot/Bundle digest 和 `FULL_REBUILD`。

### G2 — Dynamic catalog, restart and failure recovery

R1、R2 和 ordered R1→R2 进入独立 sealed Catalog artifact。关闭管理进程，使目标 Git 与权威数据库对读取进程不可见；
重启后只挂载 Catalog root + no-payload Bundle root，先机械验证内嵌 Receipt 与 file manifest，再执行 candidates、
inventory、direct dependency、path 与 diff。篡改 Catalog/Receipt/locator/Bundle、Bundle 构建中断、stale expected
CURRENT 与进程重启均失败关闭；旧 queryable Read Set 保持可用。

人工验收物包括兼容性表、Workspace CLI 报告、R1/R2 图与 diff、版本/Read Set 列表、Source-off View 输出和故障恢复表。
测试计数不能替代这些内容。

## Findings

链接本轮的 [Findings](../findings/README.md) 与[实现发现回写规则](../../../governance/implementation-feedback-policy.md)。
`FINDING-005-001` 已由 Catalog 连续恢复代码与测试处置。当前本 Slice 是等待人工接受的已实现结果，不再是活动编码输入。
