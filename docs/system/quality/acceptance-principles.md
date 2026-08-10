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

1. **固定证据主线：** 同步产品回答只能使用与原问题和 exact 来源目标绑定的密封 Evidence Packet；重写不得临时读取来源或模型历史。跨任务正式知识仍只能经 Admission 与 Snapshot Publication 形成。
2. **任务语义守恒：** 同步回答的每个 Question Checklist Item，以及正式查询的每个 Requirement Need 和 Joint Constraint，都必须被满足或明确报告对应的 Evidence Gap / Knowledge Gap。
3. **诚实状态：** Conflict、Unknown、Limitation、Partial Result 和 Outcome Unknown 不能被隐藏或猜测。
4. **独立复核：** 生成者不能自证；评审依据在候选输出密封后才可提供给独立评审来源。
5. **精确绑定：** 结果绑定实现提交、配置、模型、Prompt/Tool/Strategy、数据集和有效期；任一关键输入变化触发重新验证。
6. **门禁分离：** 机械 Contract Conformance、业务 Capability Evaluation、Product Validation 与 Activation 互不替代。
7. **逐任务不退步：** 同条件下系统答案不得低于直接调查基线；一个任务的重大错误不能被其他任务的高分抵消。
8. **失败保留：** 历史失败和限制不可因后续成功被删除，后续成功也必须明确其替代范围。
9. **质量不服从调用配额：** 调用次数和成本可以形成安全熔断或失败关闭，但不能取消检索完整性、证据绑定、问题检查项或独立审核。
