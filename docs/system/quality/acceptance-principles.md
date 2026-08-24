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

1. **固定权威主线：** `WORLD_MODEL` 回答只能使用 exact Snapshot 的正式查询/View 与 Support Map；`DIRECT_INVESTIGATION` 只能使用与原问题和 exact 来源目标绑定的密封 Evidence Packet；`ENGINEERING_QA` 由独立 Investigation LLM 基于原问题、World Model Cognition Context 和 append-only Evidence Ledger 自适应调查，但 Answer/Reviewer 只能消费调查结束后密封的当前 Question Evidence Package。Package 的 `support/citation` 仅含可采信条目，`boundary/audit` 强制保留 Gap/Failure/Partial/Conflict/Unknown 且不能支持肯定 Claim；seal 证明完整性和来源，不使内容自动为真。模式在请求开始前固定，不得静默切换。
2. **任务语义守恒：** 同步回答的每个 Question Checklist Item，以及正式查询的每个 Requirement Need 和 Joint Constraint，都必须被满足或明确报告对应的 Evidence Gap / Knowledge Gap / Limitation。
3. **诚实状态：** Conflict、Unknown、Limitation、Partial Result 和 Outcome Unknown 不能被隐藏或猜测。
4. **独立复核：** 生成者不能自证；Reviewer 使用不继承调查或回答会话的新上下文。Engineering QA 的 finding-free comprehensive Review 只是 provisional approval，还必须由另一个 fresh evidence-boundary challenge Review 检查配置 placeholder、引用中缺失的 status literal 与未挂载 application type leads；最终授权只能绑定后者。Reviewer 只能返回绑定当前 Package 或具体 material Claim/evidence need 的 typed remediation Finding；可信 Application 派生 Review action 与 Verification Request。补证由另一个全新上下文的 Verification Investigation 读取 gap + current Package/Ledger，自适应提议并经 Broker/Worker 校验执行，形成新 Ledger/Package、Answer 和双 Review，不回初始调查。
5. **精确绑定：** 结果绑定实现提交、配置、模型、Prompt/Tool/Strategy、数据集和有效期；任一关键输入变化触发重新验证。
6. **门禁分离：** 机械 Contract Conformance、业务 Capability Evaluation、Product Validation 与 Activation 互不替代。
7. **严格超过当前 Codex：** 从 `ITER-010-PDR-002` 后首个新建产品迭代起，current Codex 作为精确冻结的强外部基线，不是 Oracle 或
   裁判。系统先通过绝对质量门，再在同题、同 revision、同授权 Source scope 的独立盲评中逐题不发生物质性退步，并取得严格为正的
   总体答案质量差值；全体打平、双方失败、无法裁决或盲化失效都不能 PASS。一个任务的重大错误不能被其他任务的高分抵消，效率指标
   不能补偿质量平局或退步。
8. **失败保留：** 历史失败和限制不可因后续成功被删除，后续成功也必须明确其替代范围。
9. **质量不服从调用配额：** 调用次数和成本可以形成预密封 revision/call/operation/bytes/wall-time/no-progress 安全熔断或失败关闭，但不能取消检索完整性、证据绑定、问题检查项或独立审核。正式协议不得永久固定一轮补证；answerable 因熔断未获批准计失败。
10. **世界模型必须是可离线复用的系统认知：** 世界模型 Product Gate 必须在目标仓库和原工作树不可见的隔离环境重启读取进程，禁用 Source/Git/越界文件读取和非白名单网络，并证明指定 Snapshot 中的实体、关系、行为或约束、Coverage/Unknown、View、差异和引用仍可用；只生成手册文本、地图或 locator 缓存不能单独证明世界模型成立。答案进程只挂载不含 Evidence payload 的 exact Snapshot Read Bundle，不能挂载权威数据库或 Evidence Store；真实模型调用只能经过 exact Model Egress Gateway。密封结果后的独立 Citation Projector 进程可从另一存储展示 allowlisted 自包含 observation，但不能出网或回流答案。
11. **更新与提问解耦：** 至少提供一种不依赖提问的可人工验证更新入口；若声称自动更新，还必须在零提问场景验证触发、陈旧识别、发布 SLA 与失败保留。
12. **产品证据可人工核对：** 任何世界模型产品验收都必须包含人可查看的结构、身份、差异、引用或页面结果；仅有测试计数或完成代码不能证明产品成立。
13. **工程问答必须像工程回答：** `ENGINEERING_QA` 验收要求结论优先、抽象层级匹配、引用支持、未知边界准确和对用户可用；方法、分支或调用顺序的完整平铺不能替代对原问题的直接回答。
14. **自适应调查不等于模型直接取权：** Investigation LLM 只提出下一步，Source Broker 重新校验并编译，只有 Retrieval Worker 可以只读 exact revision，全部步骤追加到 Ledger；Answer/Reviewer 不能读 Repository/Source/Tool、shell、网络或 credential，只读当前密封包。资源上限只能失败关闭，不得删减调查、证据、检查项或独立审核。
15. **世界模型增益需要独立受控消融：** 从 `ITER-010-PDR-002` 后首个新建产品迭代起，“系统 vs current Codex”是产品替代价值对照，双方只统一 exact revision、问题、授权 Source
    scope、输出约束和盲评规则，并分别如实冻结各自模型、reasoning、工具、权限和预算；“完整 World Model Cognition vs
    locator-only/empty”才是因果消融，必须在相同系统模型、调查链、问题、模型/来源 budget、cache policy/state、rubric 与 evaluator
    下执行。完整认知仍须先过自身绝对质量门，再按预提交协议证明相对 locator control 的质量或非 locator 调查成本增益，并计入世界
    模型建模、更新、存储、Provider 成本和冻结复用周期；locator control 失败不能降低产品对 current Codex 的严格胜出门槛。ITER-010
    继续使用已冻结的原 Gate，不受本条前瞻拆分追溯影响。
