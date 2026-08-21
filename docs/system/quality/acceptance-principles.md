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

1. **固定权威主线：** `WORLD_MODEL` 回答只能使用 exact Snapshot 的正式查询/View 与 Support Map；`DIRECT_INVESTIGATION` 只能使用与原问题和 exact 来源目标绑定的密封 Evidence Packet；`ENGINEERING_QA` 只能使用同时绑定 World Model 结果/缺口与受控 exact-revision 检索的密封 Question Evidence Package。模式在请求开始前固定，不得静默切换。
2. **任务语义守恒：** 同步回答的每个 Question Checklist Item，以及正式查询的每个 Requirement Need 和 Joint Constraint，都必须被满足或明确报告对应的 Evidence Gap / Knowledge Gap / Limitation。
3. **诚实状态：** Conflict、Unknown、Limitation、Partial Result 和 Outcome Unknown 不能被隐藏或猜测。
4. **独立复核：** 生成者不能自证；评审依据在候选输出密封后才可提供给独立评审来源。
5. **精确绑定：** 结果绑定实现提交、配置、模型、Prompt/Tool/Strategy、数据集和有效期；任一关键输入变化触发重新验证。
6. **门禁分离：** 机械 Contract Conformance、业务 Capability Evaluation、Product Validation 与 Activation 互不替代。
7. **逐任务不退步：** 同条件下系统答案不得低于直接调查基线；一个任务的重大错误不能被其他任务的高分抵消。
8. **失败保留：** 历史失败和限制不可因后续成功被删除，后续成功也必须明确其替代范围。
9. **质量不服从调用配额：** 调用次数和成本可以形成安全熔断或失败关闭，但不能取消检索完整性、证据绑定、问题检查项或独立审核。
10. **世界模型必须可离线复用：** 世界模型 Product Gate 必须在目标仓库和原工作树不可见的隔离环境重启读取进程，禁用 Source/Git/越界文件读取和非白名单网络，并证明指定 Snapshot、View、差异和引用仍可用。答案进程只挂载不含 Evidence payload 的 exact Snapshot Read Bundle，不能挂载权威数据库或 Evidence Store；真实模型调用只能经过 exact Model Egress Gateway。密封结果后的独立 Citation Projector 进程可从另一存储展示 allowlisted 自包含 observation，但不能出网或回流答案。
11. **更新与提问解耦：** 至少提供一种不依赖提问的可人工验证更新入口；若声称自动更新，还必须在零提问场景验证触发、陈旧识别、发布 SLA 与失败保留。
12. **产品证据可人工核对：** 任何世界模型产品验收都必须包含人可查看的结构、身份、差异、引用或页面结果；仅有测试计数或完成代码不能证明产品成立。
13. **工程问答必须像工程回答：** `ENGINEERING_QA` 验收要求结论优先、抽象层级匹配、引用支持、未知边界准确和对用户可用；方法、分支或调用顺序的完整平铺不能替代对原问题的直接回答。
14. **组合证据不等于降低隔离：** 只有 Retrieval Worker 可以只读 exact revision；Answer/Reviewer 不能读 Repository/Source/Tool，只读密封包。资源上限只能失败关闭，不得删减证据、检查项或独立审核。
