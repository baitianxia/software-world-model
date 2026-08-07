---
id: PROJECT-GOVERNANCE-BOUNDARY
kind: project-governance
status: current
authority: project-governance
owners: [architecture, project]
depends_on: [SYS-INDEX, PROJECT-INDEX]
code: []
tests: []
---

# 系统文档与项目文档的边界

## System owns essence

`docs/system/` 保存当前接受、跨迭代稳定的产品承诺、Owner、架构关系、不变量、跨模块契约和质量下限。它不记录工作包、测试计数、某次模型、有效期或项目进度。

## Project owns change

`docs/project/` 保存 Roadmap、迭代范围、开发设计、发现、项目决策、验证方法和结果。项目文档可以选择或约束某个系统 Contract，但不能通过一次结果静默重新定义它。

## Routing test

删除某条文档约束后，如果两个实现都可能通过局部测试，但其中一个会改变跨 Owner 权限、公开语义、安全边界、不可逆数据或并发一致性，它属于 System。若它只影响当前技术选择、内部类型、算法、错误码、文件布局或测试夹具，它属于 Iteration、代码或测试。

## Conflict rule

当实现证据与 System 冲突：

1. 暂停受影响的 Development Slice；
2. 登记 Implementation Finding；
3. 判断是实现缺陷、System 文档错误，还是需要新架构选择；
4. 若改变系统真相，在同一变更中更新唯一 System Owner 文档和必要 ADR；
5. 更新 Slice、Verification 和 Finding disposition 后再继续。

Result 和 Archive 永远不能在冲突时“赢过”当前 System；它们只能提供促成显式修订的证据。
