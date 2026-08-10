---
id: SYS-CONTRACT-SOURCE-DATA-SOURCE
kind: system-contract
status: current
authority: normative
owners: [source]
depends_on: [SYS-ARCH-INVARIANTS]
derived_from: [DD-SRC-DATA-SOURCE]
code: [src/software_world_model/source_integration/configuration.py, src/software_world_model/infrastructure/sqlite_source_repository.py]
tests: [tests/test_source_configuration.py, tests/test_local_git_configuration.py]
---

# Data Source 与 Binding

## Purpose and scope

本契约定义外部软件来源如何获得稳定身份，并对调用方传入的 opaque exact Scope Reference / Assertion 形成可授权的 Binding。它不解释 Knowledge Scope 的内部生命周期，也不证明来源当前可达、存在 Artifact、已有正式知识或 Scope 已发布。

## Owner and public contract

Source Integration 是 Data Source、Definition Revision 与 Binding 的唯一写者。Application 只能通过公共命令创建、修订、启停或退休它们；模型和 Agent 只能提出 Proposal。

## Authority and identity

- Data Source、Binding 与 Knowledge Scope 是三个独立身份。
- Source 的永久唯一键一经绑定不得重新指向另一外部来源。
- Selector 只能收窄一个 Source，不能跨 Source 拼接授权。
- Definition Revision 表示配置变化，不等于外部内容 Revision。

## Invariants

1. 同一 Scope、Source 和等价 Selector 最多存在一个有效 Binding 选择。
2. Proposal 不分配正式身份，也不能扩大调用者权限。
3. ACTIVE Binding 只表示配置生命周期允许，不证明 Scope active、网络可达或知识存在。
4. Scope retirement 不跨 Owner 级联写入、停用或删除 Source、Binding 和历史结果。
5. Scope Reference / Assertion 由 Application 作为中立边界值传入，Source Integration 不查询或改写 Knowledge Engine；执行端必须消费 exact Binding Revision 和 exact Scope Assertion，不能长期依赖 `latest`。执行与发布分别在自己的权威边界重验当前资格。
6. Binding Eligibility 的身份绑定 exact Source/Binding Revision、Scope Assertion、配置控制栅栏、Selector、Tool 与安全分类；解析时间只用于诊断，不改变相同权威闭包的身份。相同来源动作重试必须能够恢复原 Operation，任一权威字段变化仍须失败关闭。

## Failure and compatibility boundary

唯一键冲突、Selector 歧义、Revision 冲突、Scope Assertion 失效或权限不足均失败关闭。重试使用稳定幂等键；相同键但不同输入摘要必须拒绝。

## Verification ownership

数据结构、状态枚举、Provider 配置字段和 CAS 实现由所列代码与 Contract Tests 定义；具体 Provider 资格是非规范性执行证据。
