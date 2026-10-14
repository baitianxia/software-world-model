---
id: ITER-010-ARCHITECTURE-REVIEW-2026-10-14
kind: architecture-review
status: current
authority: project-evidence
owners: [architecture, quality]
depends_on: [SYS-ARCH-BASELINE, SYS-ADR-021, FINDING-010-298, ITER-010-EXECUTION-PLAN-CURRENT]
code: []
tests: []
iteration: ITER-010
verdict: FIT_WITH_ACTIONS
---

# 架构评审 2026-10-14（基线 V1.4，TASK-1 开始前）

> 评审者：Claude（与开发会话隔离，未参与产品代码实现）。限制：本评审者同时起草了基线 V1.4 的修订，对架构文本不完全独立；
> 下一次检查点（2026-10-16）应由全新会话或其他评审者执行。本报告只记录结论与动作，不改变架构。

## 结论：`FIT_WITH_ACTIONS`

V1.4 的架构可以支撑 TASK-1 的价值假设，但代码与 V1.4 存在系统性差距，且核心假设尚无对照证据。

## 清单

| # | 问题 | 判断 | 证据 |
|---|---|---|---|
| 1 | 价值支撑 | 已有设计，实现缺口大 | 基线 6.10 定义了认知分层、混合检索与差量构建；当前认知只有 5 类实体、5 类关系，检索为字面分词匹配，无路径查询与语义检索 |
| 2 | 风险覆盖 | 已覆盖 | ITER-010 失败集中在证据规划、预算耗尽与重复动作（FINDING-010-282 等），对应 V1.4 的工具对等与预算模型 |
| 3 | 实现一致 | 不一致（迁移中） | 认知由 `application_services/java_capability_cognition.py` 直接构建、未经准入发布；读取须先有 read candidate；Turn 证据终态释放；Reviewer 无核验读取——均与 V1.4 不符 |
| 4 | 约束成本 | 偏高，已部分处理 | 候选登记、调用次数熔断与协议版本造成多轮无效返工；本次已把契约收敛为跨模块语义、门禁从约 3.4 万行降到约 1.8 千行 |
| 5 | 复杂度预算 | 失衡 | ITER-010 期间产品代码 +8.1 万行、文档 +7.7 万行、门禁与测试 +3.2 万行、知识引擎 +2.3 千行；旧协议模块仍被广泛引用（如 `engineering_question_answering` 被 13 个模块导入、`conversational_engineering_model` 被 7 个导入） |
| 6 | 证据质量 | 核心假设无证据 | “同一 Agent 下世界模型 + 源码优于只读源码”尚未做过冻结问题集上的成对对照 |

## 动作（排入 TASK-1）

1. **步骤 A：** Route-0 与源码只读工具对等，去掉 read candidate 读取前置条件，预算改为 token/时延/字节；完成后旧证据规划补丁（候选排序、屏蔽、
   计划失效等 sidecar）应随之删除而不是保留。
2. **步骤 B：** Java 认知经确定性通道准入并发布为 Snapshot，提供概览、搜索、关系遍历、路径查询与详情检索；未发布的索引不再计为世界模型贡献。
3. **步骤 0 与 C：** 冻结问题集与判定规则，并在步骤 C 完成同一 Agent 的成对对照，作为核心假设的第一份证据。

## 残余风险

- 旧协议代码体量大、被多处引用，步骤 A/B 若在其上叠加而不删除，会重现复杂度失衡；建议步骤 A 完成后评估删除不再被默认路径使用的旧协议模块。
- 一周时间盒较紧；到期按失败出口交付，不延长内部修复。
