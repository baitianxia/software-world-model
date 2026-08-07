---
id: SYS-CONTRACT-APPLICATION-MANAGEMENT
kind: system-contract
status: current
authority: normative
owners: [application]
depends_on: [SYS-CONTRACT-SOURCE-DATA-SOURCE, SYS-CONTRACT-KNOWLEDGE-SCOPE]
derived_from: [DD-APP-MANAGEMENT]
code: [src/software_world_model/application_services/management.py, src/software_world_model/infrastructure/sqlite_management_repository.py]
tests: [tests/test_management.py]
---

# Management Application Services

## Purpose and scope

Management 组合跨 Owner 的配置与生命周期用例，保存可恢复的 Attempt、Step 和 Result。它不拥有 Source、Scope、Schema 或 Capability 的内部状态。

## Public contract

Application 只调用各 Owner 的公共命令，按步骤封存返回的权威 Result Reference。模型和 Agent 只能提出 Management Proposal，不能直接执行或改变授权。

## Invariants

1. 跨 Owner 不建立大事务，不因后续失败擦除已经完成的权威步骤。
2. Result 必须逐步披露成功、失败、未知和未执行；无论代码选择何种 aggregate status，都不能擦除 Step Outcome、把已发生或未知写成未执行，或伪造跨 Owner 原子性。
3. `OUTCOME_PENDING` 表示已分派但结果尚不可证明；取消不覆盖已经发生或仍未知的外部效果。
4. 相同逻辑命令使用稳定幂等键恢复；不同输入 Digest 不得共享结果。
5. 历史成功不能证明当前 Scope、Binding、资格或权限仍可用。

## Failure and implementation boundary

恢复时重新读取 Owner Result，不扫描或修正其私有 Store。Command/Attempt/Step/Result DTO、aggregate status、状态和错误投影由应用代码与测试定义。
