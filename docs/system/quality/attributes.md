---
id: SYS-QUALITY-ATTRIBUTES
kind: system-quality
status: current
authority: normative
owners: [quality, architecture]
depends_on: [SYS-ARCH-INVARIANTS]
code: [src/software_world_model]
tests: [tests]
---

# 质量属性

| 属性 | 系统级要求 |
|---|---|
| 正确性 | 用户可见结论由正式知识蕴含，逐 Need 完整且不过度推断 |
| 可追溯性 | 结论可回到 exact Snapshot、知识成员、Evidence、Artifact 和来源 Context |
| 可靠性 | 幂等恢复不重复副作用；未知结果保持未知；部分成功如实披露 |
| 一致性 | 单 Scope 原子发布，CURRENT 不指向部分状态，跨 Scope 无隐式原子性 |
| 安全性 | 默认拒绝外部能力；Secrets、内容和思维链不进入日志或 Telemetry |
| 可维护性 | Owner、Contract 和代码依赖同向；局部实现细节不复制到永久文档 |
| 可演进性 | Strategy 可替换但权限、知识和公开语义不漂移；变化有精确身份 |
| 可观测性 | 成功、失败和真实消耗可关联；观察链不参与业务放行 |

性能、容量和成本阈值必须在有真实负载证据的迭代中确定，不能由架构文档虚构。
