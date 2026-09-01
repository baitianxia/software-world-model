---
id: ITER-010-PDR-013
kind: project-decision
status: accepted
authority: project-decision
owners: [product, project, architecture, engineering, quality, ai]
depends_on: [ITER-010-PDR-012, FINDING-010-254, FINDING-010-255, SYS-ADR-018]
code: []
tests: []
iteration: ITER-010
decision: REWORK
rework_strategy: AGENT_FIRST_PRODUCT_CONVERGENCE_CUTOVER
decision_ref: local-user-message-utf8:sha256:246ac00e741f49834fe83711bc97b24f10772f3abd630d706409d6175b4fb749
effective_scope: ITER-010-SLICE-001
coding_input: true
---

# PDR-013：终止协议扩张和逐题修补，切换到 Agent 优先的产品收敛

本决定是 PDR-012 已授权产品目标、总体架构、Source、外部范围和持续开发动作内的执行设计收敛，不创建新的
`plan_execution_control` 版本，不迁移动作游标，也不改变 standing authority。可信 Manifest 继续使用 PDR-012 及其现有产品动作；
PDR-013 只替换该动作内部已经被事实证明不收敛的实现路线。这样既不伪造历史产品 PASS，也不等待治理恢复动作。

## 立即生效的停止项

1. `run-127` 之后不得继续 `run-128` 式的“新增一条语义校验—重放原题—发现下一条校验”循环。
2. 不再增加 Answer、Review 或 preflight 协议版本，不再用 Claim 文本复刻、Markdown 结构、inline-code anchor、标题、标签、句段 substring
   等机械规则判断答案语义正确性。
3. 不再针对一个已知问题修改 Prompt、Schema、Validator 或 Reviewer 后只重放该题。`FINDING-010-255` 的 `@40` candidate 只保留为失败证据，
   不进入产品主线。
4. 不再等待内部协议全部通过后才运行 current Codex。系统候选与 Codex 强基线从第一个新候选开始同步执行。

以上停止项不降低质量标准。答案仍必须基于授权的 exact Source，重要结论必须有可打开 Citation，证据不足必须如实说明，最终答案必须经过
独立技术复核；被取消的是以不断增长的应用层文本协议代替 Agent 推理和独立技术判断。

## 新的产品主线

浏览器只保留一条主线：

`用户问题 → 世界模型提供系统认知和调查入口 → 主工程 Agent 自主规划并按需读取源码 → 自然答案与 Citation → 独立 Reviewer 对原问题、源码和完整答案作技术审核 → 最多一次携带全部审核意见的重写 → 页面交付`

- 世界模型提供版本化的软件认知、结构关系、行为、约束、覆盖范围和检索入口；不能退化为 POM、模块或 locator 清单。
- 主工程 Agent 是回答大脑。它决定需要哪些认知、何时读源码、如何重规划以及怎样组织答案；应用层不得替它判断答案句子的技术语义。
- Reviewer 一次返回全部重大错误、遗漏、错误引用和未知边界；只审核，不编辑 Draft，不用封闭字段协议逐项重建答案。
- Application 只执行确定性边界：授权、只读访问、预算、Provider 路由、结构可解析、Citation 引用真实存在、Reviewer 与答案身份绑定以及失败真实性。

## 唯一开发顺序

### 1. 建立简化候选

从浏览器入口切出一条不依赖现有语义 Claim/Boundary/content-unit 校验链的 Agent-first 路径。可以复用 Provider、世界模型查询、只读源码工具、
Conversation 和 Web；不得复用把答案文本拆成形式证明对象的控制循环。完成后立即在现有 loopback 页面交付非 MVP 候选。

第一提交同时加入一个轻量架构检查，机械阻止：

- 产品代码出现冻结问题全文、测试工程专有类名/方法名/路径分支；
- Application/Response Control 根据答案正文词语、Markdown、标题、inline-code 或 substring 判断技术正确性；
- 在旧 `conversational_engineering_model.py` 与对应测试上继续增加协议版本或语义校验分支。

该检查只保护架构边界，不审核答案内容，也不得发展成新的答案协议。

### 2. 首个候选立即双路体验

使用五个异质问题一次性运行同一 frozen candidate；问题至少覆盖系统入口/用途、跨层调用与副作用、失败/事务边界、配置或数据流、一次真实多轮
追问。至少三个问题不得参与候选实现或 Prompt 调整。系统与 actual current Codex 在相同源码版本、问题和输出要求下独立作答，双方答案在完成前
互不可见。

这一比较与浏览器体验同步发生，不以内部 Reviewer 全绿为前置条件。独立技术评估直接读取 exact Source，逐题判断正确性、完整性、引用和未知
边界；任何模型答案都不是 Oracle。

### 3. 只允许按责任层修复一次

失败必须先归因到世界模型认知、Agent 调查/源码使用、答案综合、Reviewer 漏判或显示/运行边界中的最早一层。一次变更只能修一个系统性根因，
并同时重跑原失败题和至少两个未参与修复的异质题。

同一责任层连续两次出现新的语义规则或只在原题变好而异质题退步时，机械判定当前实现路线不收敛：停止该路线，不得增加第三条规则；下一变更
必须删除/绕过造成失败的控制层或替换 Agent 策略。Provider/network 的独立故障不计入产品语义次数，也不得触发答案逻辑修改。

### 4. 产品判定

只有五题均无重大事实错误、物质遗漏、错误 Citation 或假 Unknown，真正多轮对话可用，世界模型至少提供一项非 locator 的实质认知贡献，且系统
逐题不比 Codex 差、总体严格更好，才称为 MVP。否则如实交付当前候选和逐层差距，继续架构调整；不得以协议通过、测试数量、调用次数或页面存在
代替产品结果。

## 当前授权与边界

沿用公开 mall exact revision、只读 Source、现有首选/备用执行配置、loopback 和非 Production standing authority，不重复申请人工授权。
全量回归、hidden、跨工程、性能和生产夯实继续后置。当前只允许为 Agent-first 纵切、五题浏览器体验、Codex 同题基线和直接相关的最小测试工作；
治理扩建和旧协议修补不属于下一动作。
