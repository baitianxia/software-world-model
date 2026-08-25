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

1. **固定权威主线：** `WORLD_MODEL` 回答只能使用 exact Snapshot 的正式查询/View 与 Support Map；`DIRECT_INVESTIGATION` 只能使用与原问题和 exact 来源目标绑定的密封 Evidence Packet；默认 Engineering Conversation 由主工程 Agent 基于 current Turn、受信 relevant Conversation Context、World Model Cognition 和 append-only Evidence Ledger 迭代调查，但用户可见答案与独立 Reviewer 只能以调查结束后密封的当前 Turn Evidence Package 为证据。Package 的 `support/citation` 仅含可采信条目，`boundary/audit` 强制保留 Gap/Failure/Partial/Conflict/Unknown 且不能支持肯定 Claim；seal 证明完整性和来源，不使内容自动为真。Conversation 中的用户陈述、Agent Work State 或 Provider memory 都不是 Source truth。模式在 Conversation/Turn 授权边界内固定，不得静默切换。
2. **任务语义守恒：** 同步回答的每个 Question Checklist Item，以及正式查询的每个 Requirement Need 和 Joint Constraint，都必须被满足或明确报告对应的 Evidence Gap / Knowledge Gap / Limitation。
3. **诚实状态：** Conflict、Unknown、Limitation、Partial Result 和 Outcome Unknown 不能被隐藏或猜测。
4. **独立复核：** 生成者不能自证；每个用户可见答案至少经过一个不继承主 Agent 隐藏状态或 Provider memory 的 fresh independent Reviewer。Reviewer 逐项检查原 Turn 目标、当前检查清单、Package 支持、引用、冲突、未知与答案可用性，只能返回绑定当前 Package 或具体 material Claim/evidence need 的 typed Finding。可信 Application 把 Finding 路由为同包重写，或绑定具体 gap 的新主 Agent evidence Attempt；后者继续经 Broker/Worker 校验并形成新 Ledger/Package，之后必须重新独立审核。固定 comprehensive/challenge 双 Reviewer 和独立 Verification Investigation 可作为兼容 Strategy，但不再是新协议的固定角色拓扑。
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
13. **工程 Chat 必须像持续协作的工程师：** 默认体验必须结论优先、抽象层级匹配、引用支持、未知边界准确并对用户可用；还必须理解有依据的追问、指代、纠正、深入和总结。方法、分支或调用顺序的完整平铺不能替代对当前 Turn 和持续目标的直接回答；用户纠正只能改变目标或待验证假设，不能成为 Source truth。
14. **Agent 自适应不等于模型直接取权：** 主 Agent 只提出 World Model query 或下一步 Source Tool Proposal，Source Broker 重新校验并编译，只有 Retrieval Worker 可以只读 exact revision，全部步骤追加到 Ledger；主 Agent 不能获得直接 Repository/Source、shell、任意网络、credential 或写权限，Reviewer 不能取得 World Model/Source Tool。资源上限只能失败关闭，不得删减调查、证据、检查项或独立审核。
15. **世界模型增益需要独立受控消融：** 从 `ITER-010-PDR-002` 后首个新建产品迭代起，“系统 vs current Codex”是产品替代价值对照，双方只统一 exact revision、问题、授权 Source
    scope、输出约束和盲评规则，并分别如实冻结各自模型、reasoning、工具、权限和预算；“完整 World Model Cognition vs
    locator-only/empty”才是因果消融，必须在相同系统主 Agent、工具链、问题、模型/来源 budget、cache policy/state、rubric 与 evaluator
    下执行。完整认知仍须先过自身绝对质量门，再按预提交协议证明相对 locator control 的质量或非 locator 调查成本增益，并计入世界
    模型建模、更新、存储、Provider 成本和冻结复用周期；locator control 失败不能降低产品对 current Codex 的严格胜出门槛。ITER-010
    继续使用已冻结的原 Gate，不受本条前瞻拆分追溯影响。
16. **对话状态与证据分离：** Conversation Context 保存用户目标和语义连续性，Agent Work State 保存可丢弃的计划与假设，World Model 保存版本化系统认知，Turn Evidence Package 保存当前答案依据；四者不得互相冒充。单个 Turn 失败关闭不得自动结束仍有效的 Conversation，也不得把未密封工具结果或旧答案授权带入下一 Turn。
