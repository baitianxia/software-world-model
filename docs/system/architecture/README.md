---
id: SYS-ARCH-INDEX
kind: system-architecture-index
status: current
authority: normative
owners: [architecture]
depends_on: [SYS-PRODUCT-VISION]
code: [src/software_world_model]
tests: [tests]
---

# 架构文档

架构层描述顶层关系和选择；Contract 拥有精确跨模块语义；代码和测试拥有局部实现。

- [概览与上下文](overview.md)
- [领域模型](domain-model.md)
- [组件与依赖](components.md)
- [运行主流程](runtime-flows.md)
- [数据和一致性](data-and-consistency.md)
- [部署视图](deployment.md)
- [架构不变量](invariants.md)
- [架构决策](decisions/README.md)

当实现发现要求反转依赖、改变权威所有者、修改正式知识路径或削弱不变量时，当前开发切片必须暂停；先更新对应 ADR、架构或 Contract，再继续编码。
