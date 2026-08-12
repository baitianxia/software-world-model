---
id: SYS-CONTRACT-APPLICATION-MANAGEMENT
kind: system-contract
status: current
authority: normative
owners: [application]
depends_on: [SYS-CONTRACT-SOURCE-DATA-SOURCE, SYS-CONTRACT-KNOWLEDGE-SCOPE]
derived_from: [DD-APP-MANAGEMENT]
code: [src/software_world_model/application_services/management.py, src/software_world_model/application_services/maven_workspace.py, src/software_world_model/infrastructure/sqlite_management_repository.py, src/software_world_model/infrastructure/sqlite_maven_workspace_repository.py, src/software_world_model/interface/runtime.py, src/software_world_model/interface/cli.py, src/software_world_model/interface/presenters.py]
tests: [tests/test_management.py, tests/test_maven_workspace.py]
---

# Management Application Services

## Purpose and scope

Management 组合跨 Owner 的配置与生命周期用例，保存可恢复的 Attempt、Step 和 Result。它还拥有用户登记的 Maven
Workspace、不可变 Workspace Version 及其面向人的生命周期状态，但不拥有 Source、Scope、Schema、Snapshot、Bundle
或 Capability 的内部状态。

## Public contract

Application 只调用各 Owner 的公共命令，按步骤封存返回的权威 Result Reference。模型和 Agent 只能提出 Management
Proposal，不能直接执行或改变授权。Workspace 管理入口只接受 stable workspace/system key、本机 Local Git 目标、逻辑
root POM 与在入口解析一次的 exact full commit；分派后只保存并报告 exact revision。

## Invariants

1. 跨 Owner 不建立大事务，不因后续失败擦除已经完成的权威步骤。
2. Result 必须逐步披露成功、失败、未知和未执行；无论代码选择何种 aggregate status，都不能擦除 Step Outcome、把已发生或未知写成未执行，或伪造跨 Owner 原子性。
3. `OUTCOME_PENDING` 表示已分派但结果尚不可证明；取消不覆盖已经发生或仍未知的外部效果。
4. 相同逻辑命令使用稳定幂等键恢复；不同输入 Digest 不得共享结果。
5. 历史成功不能证明当前 Scope、Binding、资格或权限仍可用。
6. Workspace Registration 固定自身 ID、canonical system key、Scope、Source Binding、root POM 和管理侧 repository
   locator；后续 Version 不得借 branch、`HEAD` 或 Catalog current pointer 改写这些身份。repository locator 只属于受信
   Management/Update 输入，不进入 Read Set Catalog 或 question request。
7. Workspace Update Attempt 以可恢复 Step 依次引用 exact target resolution、Snapshot Publication、Read Session、Bundle
   Receipt 和 queryable Read Set Registration。每步只保存 Owner 返回的 ID/digest/outcome；不能复制或重解释其私有状态。
8. Snapshot 已发布而 Bundle 或 Catalog registration 失败时，Version 必须如实标记 `READ_BUNDLE_UNAVAILABLE` 并保留已
   完成 Step；不得伪造全局回滚。旧 queryable Version/Read Set 保持可用，resume 使用原 Attempt 与稳定幂等键继续尚未
   闭合的步骤。
9. Workspace register/update/resume/list 只属于独立管理入口。Question、Read/View 和 Answer 入口没有创建、恢复或推进
   Workspace Update Attempt 的权限。

## Failure and implementation boundary

恢复时重新读取 Owner Result，不扫描或修正其私有 Store。Command/Attempt/Step/Result DTO、aggregate status、状态和错误投影由应用代码与测试定义。
