---
id: SYS-QUALITY-ACCEPTANCE
kind: system-quality
status: current
authority: normative
owners: [product, quality]
depends_on: [SYS-ARCH-INVARIANTS]
code: []
tests: []
---

# 长期验收原则

1. **正式知识单路径：** 产品回答不得在答案阶段直接读取来源、Artifact、Evidence Quote 或模型历史来补齐正式知识缺口。
2. **任务语义守恒：** 每个 Requirement Need 和 Joint Constraint 都必须被满足或明确报告 Gap。
3. **诚实状态：** Conflict、Unknown、Limitation、Partial Result 和 Outcome Unknown 不能被隐藏或猜测。
4. **独立复核：** 生成者不能自证；评审依据在候选输出密封后才可提供给独立评审来源。
5. **精确绑定：** 结果绑定实现提交、配置、模型、Prompt/Tool/Strategy、数据集和有效期；任一关键输入变化触发重新验证。
6. **门禁分离：** 机械 Contract Conformance、业务 Capability Evaluation、Product Validation 与 Activation 互不替代。
7. **逐任务不退步：** 同条件下系统答案不得低于直接调查基线；一个任务的重大错误不能被其他任务的高分抵消。
8. **失败保留：** 历史失败和限制不可因后续成功被删除，后续成功也必须明确其替代范围。
