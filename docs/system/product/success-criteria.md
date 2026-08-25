---
id: SYS-PRODUCT-SUCCESS
kind: system-product
status: current
authority: normative
owners: [product]
depends_on: [SYS-PRODUCT-VISION, SYS-QUALITY-ACCEPTANCE]
code: []
tests: []
---

# 长期成功标准

## 当前产品目标与 MVP 门槛

当前所有产品迭代必须共同逼近同一个目标：系统在提问前把经授权的软件来源构建成版本固定、可验证、可更新且可跨任务复用的软件世界
模型，为 AI 提供对系统实体、关系、行为、约束、状态、证据、覆盖范围和未知边界的持久认知；同时提供一个优秀的主工程 Agent，通过
同一个产品 Web Chat 在未参与开发的真实工程上持续解决用户问题。主 Agent 在同一授权 exact revision 上按需使用世界模型查询和受控
源码、仓库文档、构建/运行配置与测试工具，根据观察重规划并自然回答；严格 `WORLD_MODEL` 另行保留 Source-off 复用语义。这里的
“通用”和“Chat”不是承诺所有问题都有答案，也不是把单轮结果放进消息列表，而是要求：

- 用户可以自由表述关于系统用途、结构、功能实现、调用过程、业务规则、条件与状态变化、配置和异常路径的问题，不能
  依赖预先枚举的题型、工程名、问题文本或关键词补丁；
- 问答能力可以动态分解 Need，并组合已经接受的结构、代码与行为知识；新增知识域必须进入同一查询和回答链，不能形成
  只能单独体验、不能与既有能力组合的孤立 Profile、View 或入口；
- 同一 Conversation 中可以连续追问、指代、纠正、收窄、深入和总结；Application 保存受信 Conversation/Turn/Agent Work State
  Revision，先前答案和模型隐藏状态不自动成为事实，用户纠正不会被旧上下文覆盖；
- 主工程 Agent 保存用户目标、假设、计划、子任务、观察、证据缺口和完成判断；它根据 World Model/Source Observation 修改计划，而不是
  执行一次性固定检索，也不是由多个窄模型角色机械拼接答案；
- Conversation 在开始前固定 exact revision、World Model Read Authority、Source allowlist、Provider disclosure、工具目录和资源熔断；
  主 Agent 只能通过 Application 查询世界模型或向 Source Broker 提交 Proposal，只有隔离 Retrieval Worker 可以只读 Source；
- 每个候选答案绑定 append-only Evidence Ledger 和当前密封、`support/citation` 与 `boundary/audit` 分区的 Question Evidence Package；
  至少一个 fresh 独立 Reviewer 从当前用户目标、受信对话上下文、Package 和 Draft 审核，具体缺口返回主 Agent 重写或继续受控调查，任何
  新证据都形成新 Package 并重新审核；
- 答案先回应用户目标并匹配期望抽象层级，代码细节只按问题需要展开；每个实质结论绑定包内真实引用，经授权软件来源仍不能证明的设计动机或其他内容明确返回 unknown/limitation；
- 在未参与实现的工程上，由独立评测方或用户持有、实现阶段不可见的 held-out 自由问题，加上验收现场临时提出的问题，
  答案重大错误、物质遗漏和无据实质结论为零，未知边界准确，重要结论有可核验引用；从 `ITER-010-PDR-002` 后首个新建产品迭代起，
  还必须在同题独立盲评中逐题不低于当时实际可用的 current Codex 强基线，并取得严格为正的总体答案质量差值。全体打平不是产品价值
  PASS，成本、时延、调用数或复用优势不能补偿答案质量平局或退步。

在达到该门槛前，模块图、静态调用图、单个 Semantic View、解析器或固定问题集的 PASS 都只能作为中间证据，不能单独
称为产品 MVP。

系统达到产品价值必须同时满足：

1. 对当前 Turn 和相关对话目标的每个实质 Need 都能从当前密封 Question Evidence Package 的 admissible support/citation 分区重建支持链，
   或由强制保留的 boundary/audit 分区明确返回 unknown/limitation；后者不能支持肯定 Claim，Package seal 只证明集合完整性和来源，不替
   内容提供真值。严格世界模型验收仍以同一固定 Snapshot/Read Set 为唯一输入。
2. 用户可见 Claim 不扩张引用证据的 Context、Modality 或 Coverage。
3. 来源、生成、准入、发布、答案生成和答案审核之间不存在未授权旁路。
4. 更新后旧知识不会因局部成功被静默删除；并发失败不会产生部分正式状态。
5. 从 `ITER-010-PDR-002` 后首个新建产品迭代起，产品价值对照与因果消融必须分开：系统与 current Codex 在相同 exact revision、问题、授权 Source scope、输出约束和盲评量表下比较，
   各自冻结实际模型、reasoning、工具与权限，不强行伪装成同模型或同调用预算；Codex 是强外部基线，不是 Oracle 或裁判。完整 World
   Model Cognition 与 locator-only/empty 同一主 Agent/工具链的消融才要求相同系统模型、问题、budget、cache 与 evaluator，用于证明世界模型认知的
   独立质量或非 locator 调查成本增益，并计入建模成本和冻结复用周期。ITER-010 保持其已冻结的现有对照 Gate，不追溯改判。
6. 主 Agent 在多轮目标守恒、观察驱动重规划、工具选择、对话纠正、证据综合和完成判断上取得资格；资格、有效期和启用范围可机械验证，
   过期、漂移或未知结果安全关闭。

测试数量、模型分数和一次运行的 PASS 只是证据，不是这些标准本身。
