---
id: PROJECT-GOVERNANCE-DEVELOPMENT-DESIGN
kind: project-governance
status: current
authority: project-governance
owners: [architecture, engineering]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, PROJECT-GOVERNANCE-BOUNDARY]
code: []
tests: []
---

# Development Design Policy

Development Design 是当前编码输入，不是长期详细设计百科。它应当足以让人或 Agent 知道要改变什么、不能破坏什么、如何验证，并允许局部实现由代码和测试快速探索。

## 每个 Slice 必须包含

- 目标结果、触发和明确非目标；
- 当前行为与期望行为；
- 引用的 System Contract/Invariant，而不是复制正文；
- 受影响入口、Owner、数据迁移与兼容边界；
- 需要在编码前确定的跨模块接口语义；
- 关键风险、开放问题和失败关闭方式；
- 可执行的验收场景和 Finding 回写入口。

## 不应预写

- 私有类、函数、表字段和内部状态枚举；
- 可由重构和测试低成本决定的算法步骤；
- 逐错误码、逐日志字段或逐 Mock 行为；
- 没有当前消费者的未来扩展点；
- 与 Contract 重复的大段背景和不变量。

## 何时先设计再编码

跨 Owner 权限、公开协议、不可逆数据、并发一致性、安全隔离或迁移语义必须先闭合设计。局部实现、可逆重构和算法选择可以通过最小代码/测试实验决定；若实验发现系统影响，立即进入 Finding 回写流程。

## Variance

实现与 Slice 不同不自动是错误。记录原因和证据：局部差异可直接修订 Slice；影响 System 的差异必须先暂停并升级；被延后的价值进入 Roadmap Candidate，不能埋在 Result 尾部。
