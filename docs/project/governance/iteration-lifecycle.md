---
id: PROJECT-GOVERNANCE-ITERATION-LIFECYCLE
kind: project-governance
status: current
authority: project-governance
owners: [project, product]
depends_on: [PROJECT-GOVERNANCE-BOUNDARY, SYS-PRODUCT-SUCCESS]
code: []
tests: []
---

# 迭代选择与生命周期

## 从最终目标反推的能力路径

迭代不得从组件列表、局部方案或“下一个可以开发的点”出发。项目必须先在 planning-only Roadmap 中维护一条从
`SYS-PRODUCT-SUCCESS` 反推的能力路径：

```text
最终产品目标
  → 达成目标必需的用户能力
  → 已有 Acceptance 实际证明的基线
  → 当前最早未证明的阻断能力
  → 能在正式 Web 人工验证的最小纵向增量
```

每个产品 Iteration 必须绑定该路径的一个明确步骤，并同时说明：前置能力的接受证据、本轮结束时用户在
正式 Web 上新增的能力、以及成功后仍然阻断最终目标的下一个差距。选择顺序以“最早未证明的阻断能力”
为准，不得跳过它去开发新 Profile、View、知识域或入口。

若早期纵向 Slice 的证据只证明当前尝试或实现有缺陷，必须保留失败 Result 并在同一 Slice 使用 `REWORK` 修复；不得据此终止
Iteration。只有用户明确改变产品方向、核心架构假设被证伪，或达到预提交的无进展上限时，才进入转向评审并可能把 Iteration 终止为
`rejected`。新方案仍必须证明同一用户能力，不得把“修好一个内部组件”当作 redirect 后的新终点。

## 产品目标对齐门禁

本门禁从 `ITER-007` 的选择开始强制执行。所有新 Iteration 必须以 `SYS-PRODUCT-SUCCESS` 的“基于预构建世界模型进行通用源码问答”作为共同产品目标。迭代可以缩小
实现范围，但不能另立与该目标无关的局部终点，也不能用改名把解析器、Schema、View、Profile 或固定题型包装成产品结果。

进入候选比较前，每个 Proposal 必须明确并冻结：

1. **目标差距：** 当前 Web 体验相对通用源码问答 MVP 具体缺什么，证据来自哪些真实自由问题；
2. **累积路径：** 本轮如何复用并组合此前已接受的知识和查询能力。只新增一个不能与既有能力联合回答问题的孤立模型，
   不得作为产品迭代 Outcome；
3. **可测增量：** 本轮完成后，哪组未参与实现的真实工程与 held-out 自由问题会从 Gap/失败变成有证据的正确答案，并冻结
   问题总数、baseline 支持数和目标支持数；覆盖率、重大错误、完整性、默认工程问答的 Broker/Worker-only Source 访问、模型直接
   Source/FS/Shell/network 权限为零、严格 `WORLD_MODEL` Source-off 回归、每题读取操作/bytes 对账和源码 Agent 对照如何判定；问题由独立
   评测方或用户持有并在实现阶段保持不可见，正式 Web 验收还必须加入至少一条现场临时自由提问。用户选择现场持有模式时，
   编码前只冻结计数下限、判定规则和“代码冻结前不披露”；exact 问题、输入、baseline 与 target 在产品代码冻结后首次披露时
   一次性密封，随后任何产品修改都烧毁该组证据；
4. **跨域证明：** 除新能力自身的问题，还必须包含至少一类需要组合既有能力与本轮能力的问题，证明产品能力是累积的；
5. **最早体验点：** 第一个 Slice 如何直接交付可重复启动、固定本地地址、持续服务、同会话自由提问且单题故障隔离的正式 Web Alpha；
6. **停止或转向条件：** 若上游知识不足、只能依赖题型/关键词补丁、不能跨域组合或效果低于成熟源码 Agent，何时停止扩张
   并重新审视建模或查询架构。
7. **差异化价值：** 若当前方案比成熟替代方案更复杂，在首个拥有正式对照的 hardening Slice 授权前冻结哪项可测的正向价值、PASS 阈值、
   测量周期和基线复用政策；体验 Alpha 只记录 stage-applicable early signal；
   “答案不退步”或只披露成本不足以证明值得继续。
8. **能力路径位置：** 本轮属于哪一个 Roadmap 能力步骤，哪些前置已被 Acceptance 证明，本轮正式 Web 验证会前进什么，
   以及成功后下一个阻断差距是什么。

不满足上述任一项的 Candidate 可以保留为技术实验或证据收集，但不得被选择为下一轮产品开发 Iteration。风险消除可以是
产品 Iteration 的第一个 Slice，但整个 Iteration 仍须计划同一正式 Web 上可人工验证的通用问答增量；若风险结果触发停止，
则记录证据并把本轮判为失败或转向，不能把组件完成或“学到了什么”称为产品进展。

跨域 Gate 不能用“一条旧能力回归 + 一条新能力孤立测试”拼成。至少一个冻结 Case 必须在同一个问题中同时引用此前已验收
能力和本轮 Slice，正式 Web 与现场临时问题 Gate 还必须执行或探测该跨域 Case。这些关系必须写入 Manifest 的结构化
binding；正文中仅仅出现相关 ID 不算绑定证据。

## 方案假设与逐 Slice 复盘门禁

迭代不是只有“开发—测试”，而是反复执行下面的最小闭环：

```text
冻结关键方案假设与反证
  → 实现最小可持续体验 Alpha
  → 独立技术复核 + 用户实际体验：CONTINUE / REWORK / REDIRECT / REJECT
  ↘ REWORK：暂停 → 同一 Slice 通用修复 → 重新授权 → 重新体验
  → CONTINUE 后工程夯实
  → 正式 Web / hidden canary / 对照验收
  → ACCEPT / REWORK / REDIRECT / REJECT
```

可体验 Alpha 必须早于大规模加固和全面资格评估。它通过真实产品入口、小而多样的输入和新的现场输入尽早暴露核心方向，并确认结果
不是单题偶然。Alpha 明确标记为非验收、非生产；安全、只读、
Secret、授权和失败真实性边界始终生效。完整能力矩阵、全量回归、性能和异常穷举属于 Alpha `CONTINUE` 后的夯实阶段，除非它们是
运行早期真实版本或判断核心方向不可缺少的最小条件。

项目不得连续进行多轮 Prompt、Schema、Contract 或评测优化，却一直没有可供用户操作的真实体验。可供操作是指可重复启动、固定本地
地址、同一会话连续自由提问、版本和限制可见，且单题失败不会关闭服务；一次性运行器或启动前冻结单题的页面不满足该定义。Alpha
发现缺陷时默认先 `REWORK`；只有满足本政策的转向条件时才 `REDIRECT` 或 `REJECT`。正式 Gate 不能成为延迟方向反馈的理由，
方向体验的认可也不能替代最终正式 Gate。

本门禁从 `ITER-008` 开始强制执行。Proposal 必须在编码前写明少量决定方案能否成立的关键假设、每项假设的最早反证方式、
反证后停止或换路的动作，以及被认真比较过的替代方案。第一个 Slice 必须优先验证风险最高、最可能导致整条路线无效的假设，
不能只实现“基础组件”并把真实产品效果留到最后一段。体验 Alpha 可以只记录相对成熟方案的可观察 early signal 和暂不正式比较的
理由；正式对照与正向价值阈值必须在拥有该对照的首个 hardening Slice 授权前冻结，而不是在首次体验前冻结。

每个 Slice 必须恰好拥有一个 `V-REFLECT-NNN` 阻断 Case。本 Slice 适用的真实 Web、机械 Gate，以及仅对 hardening/验收适用的 hidden
canary 与对照形成 exact Result 后，Result 必须新增“Architecture reflection and continuation decision”，至少回答：

1. 原方案假设是什么，实际证据与预期哪里一致、哪里不一致；
2. 问题属于架构、实现、配置/环境、需求/使用还是验证设计，影响是个案还是系统性；
3. 知识表示、查询/编排、产品 Web 链和验证方案各自是否仍成立；
4. 若本 Slice 已拥有成熟直接源码 Agent 对照，比较正确性、完整性、无关证据、时延、成本和复杂度；体验 Alpha 则记录 early signal、
   未正式比较的原因与明确后置阶段；
5. 本 Slice Finding 如何处置，当前最早未证明的风险是什么；
6. 明确作出 `CONTINUE`、`ACCEPT`、`REWORK`、`REDIRECT` 或 `REJECT` 决策并说明理由。

Manifest 和已接受 Readiness 必须同时冻结 Proposal 关键假设表的 exact SHA-256；每个 Slice Result 必须引用同一摘要，且
`Expected` 必须逐字等于 Proposal 中对应假设原文，避免看到结果后改写假设。Manifest 还必须冻结关键假设 ID、每个 Slice 当期到期的有序假设子集和独立的 product/architecture/quality 决策 Owner；后续 Slice
只能保留并增加已到期假设，最终 Slice 必须覆盖全部关键假设。尚未到期的假设必须分别绑定本 Slice 的 early blocking falsifier；
该 falsifier 必须归属当前 Slice，不能借用后续 Slice 的 Case 推迟反证。
若该 Case FAIL，阻断 Result 必须把对应假设追加为结构化 `FALSIFIED/UNRESOLVED` 行，不能只在散文里提及。Result 必须逐项给出 Expected、exact Evidence、
Verdict 和 Impact，并填写问题分类/范围、分层诊断、替代方案与决策理由；`reflection_report_digest` 是上述 exact Reflection 章节 UTF-8
正文的 SHA-256；Result 只能有一个同名 Reflection 章节，不能用一句“已复盘”或只有标题的空壳通过。Verification 状态只接受 exact
`PASS / blocking`、`FAIL / blocking` 或 `NOT-RUN / blocking`（Readiness 可加 `readiness`），不得用词袋或“not blocking”伪装。

`CONTINUE` 或 `ACCEPT` 要求该 Slice 绑定的每项假设都由本 Slice 的证据判为 `SUPPORTED`。任一项为 `FALSIFIED` 或
`UNRESOLVED` 时，必须阻止晋级，但默认决定是 `REWORK`；逐假设证据必须引用本 Slice 已执行的 Verification Case，不能用
`V-REFLECT` 自证。正文决定、Owner、exact 用户决策消息收据、Result metadata 与 Manifest 必须完全一致；下一 Slice 的用户授权
必须引用同一条前序 Reflection 决策消息。每个 Reflection 决策必须使用一条发生在本 Slice 授权之后的新用户消息；不同 Slice
不得复用决策收据，也不得复用 Readiness 或更早授权收据。阻断 Result 必须至少有一项 `FALSIFIED/UNRESOLVED` 假设及其 executed
FAIL Case，不能用全部假设 SUPPORTED、全部 Case PASS 的材料宣告失败。

`REWORK` 表示目标和总体架构仍成立，当前失败可以通过实现、提示、答案组织、审核、配置或局部 Contract 的通用修复处理。单个错误答案、
问题陈述、用户要求复核或 Reviewer 的遗漏意见都不能推导 `REDIRECT`。`REDIRECT` 只能绑定以下一项明确依据：用户明确改变产品方向；
证据证明核心架构职责或主数据流不可成立；连续修复达到 Proposal 预先冻结的无进展上限。问题被分类为“系统性”也不自动等于核心架构
证伪。`REJECT` 只用于明确放弃当前产品增量，或在既定约束下没有可行路线。

若某个 Slice 绑定成熟源码 Agent 的正向价值比较，completed Result 必须在唯一 `## Positive value report` 中记录冻结指标、数值
actual、输入 digest、比较 Case 和独立裁决收据；docs gate 从该 exact JSON 章节重算 digest 并核对 metadata/Manifest。比较 Case
已经执行但 Slice 被阻断时也必须保留同样的可重放报告，不能只写 `V-COMP FAIL`。裁决收据必须来自测量后的新消息，不得复用
Readiness、当前/更早 Slice 授权或此前 Reflection 决策；允许用户用同一条事后消息同时裁决本次测量并作出本 Slice Reflection 决定。
未达到预提交阈值不能 `CONTINUE/ACCEPT`。

`V-REFLECT-NNN PASS` 只表示复盘完整、证据可审计，不表示产品方案本身 PASS。中间 Slice 只有产品 Gate 全部 PASS、复盘决定为
`CONTINUE` 且用户再次明确授权时，下一 Slice 才能进入开发；最终 Slice 只有产品 Gate 全部 PASS 且复盘决定为 `ACCEPT` 时，
才可形成 Iteration Acceptance。`REWORK` 使当前 Slice 进入 `paused / coding_input=false`，只阻止晋级；在新授权后恢复同一 Slice，
不得新建 Iteration。`REDIRECT` 表示最终目标不变但当前总体方案满足上述转向依据，当前 Iteration 必须按 `rejected` 封存并用新
Proposal 重新选路；
`REJECT` 表示当前增量不成立且尚无已验证替代。测试 PASS、Web 能打开、代码完成或“没有新 Finding”都不能绕过复盘。

## 每轮内容如何确定

迭代从可验证的变化需求产生，而不是从目录、组件或“还有代码可写”产生。合法触发包括产品差距、上一轮失败、实现发现、运维风险、已满足进入条件的 Roadmap Candidate 或系统 Contract 必须修订。

通过产品目标对齐门禁后，再按顺序回答：

1. **Outcome：** 哪个用户、运营或学习结果会改变？不做的成本是什么？
2. **Evidence：** 现有事实是什么，哪些仍是假设？
3. **Smallest vertical slice：** 能独立证明结果的最小端到端切片是什么？
4. **System impact：** 需要哪些 current Contract；是否依赖尚未接受的系统能力？
5. **Risk and dependency：** 先关闭哪项高风险未知，哪些工作可以明确不做？
6. **Acceptance：** 用什么输入、Oracle、对照和失败条件判定，而不是用完成代码量判定？

Roadmap 只提供候选。只有 Proposal 被明确接受、Manifest 闭合并由 `project/current.md` 指向后，Development Slice 才获得编码授权。

## 新一轮最小启动顺序

1. 按[模板落位表](templates/README.md#最小落位)建立 Iteration Index、Proposal、Manifest、Verification Matrix、Readiness、Development Design 和 Findings Index；全部保持 proposed / non-coding。
2. 冻结 baseline、System IDs、外部输入、风险、Acceptance 和第一个纵向 Slice，不复制上一轮运行身份。
3. Readiness Review 记录用户的明确授权，把 Proposal 与 Readiness 状态改为 `accepted`；未授权字段不得用默认值代替。
4. 把 Iteration Index、Manifest 与第一个 Slice 改为 authorized，把 Slice `authority` 改为 `current-development`，并将 Index/Slice 的 `coding_input` 改为 `true`；Manifest 已规划的后续 Slice 保持 `proposed / proposed-development / coding_input: false`。
5. 最后更新 `project/current.md` 的 `active_iteration`、`active_slice` 与 `depends_on`。`scripts/docs.py check` 只有在这些对象属于同一 Iteration 且必需输入闭合时才通过。

同一 Iteration 的累积 Slice 以 Manifest `new_capability_slice_refs` 的顺序推进：执行态必须为“零个或多个 `completed` + 恰好一个
`authorized/in-progress` + 零个或多个 `proposed`”；修复等待态则为同样的 completed 前缀、恰好一个 `paused` 当前 Slice 和 proposed
后缀。每个后续 Slice 必须直接依赖前一个；前一个 Slice 的人工 Web/停止 Gate 完成
并形成 Result，且方案复盘 Gate 为 PASS、决定为 `CONTINUE` 后，用户再明确授权下一个 Slice，随后才移动
`project/current.md.active_slice`。后续 Slice 获得授权时，其 `depends_on` 与 Manifest `reflection_prerequisite_result` 还必须绑定
前一 Slice 的 exact Reflection Result，不能先授权再补复盘证据。可体验 Alpha 以真实可见问题与现场输入尽早判向，不要求
hidden canary；从 Alpha `CONTINUE` 后的工程夯实 Slice 开始，最终 held-out 验证前的每个适用 Slice 必须在本 Slice 产品代码冻结后
通过独立持有的隐藏 canary，曝光后修改产品会烧毁 canary并保留原失败。不得为了通过 Readiness 一次性授权全部 Slice，也不得跳过失败
Slice。完成的 Slice 使用 `historical-development / coding_input: false`，当前 Slice 使用
`current-development / coding_input: true`，后续 Slice继续保持 proposed。

若某个 Slice 的阻断 Gate 触发，默认把 Iteration 和当前 Slice 标记为 `paused`，把失败尝试以 `failed-preserved` Result 保存，
`coding_input=false` 且 `project/current.md` 不再指向它。Manifest 的 `rework_result_refs` 保留所有失败尝试；用户用新的明确授权收据后，
同一 Slice 可以恢复为 `authorized`，不得因修复循环创建新 Iteration。只有正式 `REDIRECT` 或 `REJECT` 才把 Iteration 设为
`rejected`，失败 Slice 设为 `blocked`，后续 proposed Slice 只保留历史。任何 redirect 都必须建立新 Iteration，重新经过 Proposal、
Readiness 和用户逐 Slice 授权。

每个 completed Slice 的 Result 必须绑定该 Slice 的 exact 产品代码冻结 digest。拥有 early hidden canary 的 Result 还必须绑定
Manifest 冻结的 canary project/suite digest、披露收据和“曝光后产品变更数为 0”；否则不得授权下一 Slice。

## 生命周期

```text
roadmap candidate
  → iteration proposal
  → readiness review
  → authorized in current.md
  → development slices + findings
  → verification + result
  → findings disposition
  ├→ acceptance → completed
  ├→ failed attempt → paused → same-Slice reauthorization
  ├→ stop / evidence-driven redirect → rejected
  └→ pre-execution administrative replacement → superseded
```

## Readiness gate

- Proposal 已通过产品目标对齐门禁，目标差距、累积路径、独立持有且对实现隐藏的可测增量、跨域问题、最早 Web 体验点、
  现场临时问题和停止条件均已冻结；
- Proposal 已绑定 planning-only Roadmap 中的精确能力步骤，前置接受证据、本轮结束时的 Web 用户能力和成功后的下一阻断差距均已明确；
- Proposal 已冻结关键方案假设、最早反证、替代方案和逐 Slice 复盘计划；可体验 Alpha 会尽早使用正式 Web 和现场输入判断架构
  与用户价值，hidden 输入和成熟基线对照则在 Alpha `CONTINUE` 后的首个夯实 Slice 执行，不推迟到最终验收；
- 一个明确 Outcome 和非目标；
- 所引用 System 文档均 current，或先完成所需 System 设计；
- 每个 Slice 有可验证退出条件和风险边界；
- 外部输入、权限、Secret Reference 和原始证据保存方式已说明；若评测问题由用户现场持有，则必须明确在产品代码冻结前不收集
  问题，并把未披露 marker 与完成前必须替换的 exact Result 绑定写入 Manifest；
- Verification Matrix 能区分机械测试、真实能力和产品价值；
- `current.md` 同一时刻最多指向一个活动迭代和一个主要 Slice。

`scripts/docs.py` 只负责检查引用、状态、digest、计数和依赖是否闭合，不能替代产品判断。Readiness Reviewer 必须实际核对
冻结工程、隐藏问题协议、跨域案例和 Web 体验设计，确认它们不是把 parser、Profile/View、CLI 或固定关键词题型重新包装成
产品增量；随机 digest、空洞 case 名和自报 PASS 都不构成证据。该判断必须由用户明确接受并绑定 exact review reference。

## Completion gate

代码完成不是迭代完成。每个 Slice 都必须有实际 Result、失败/限制、方案复盘、相关 Finding disposition，以及明确的继续、接受、
修复重试、转向或拒绝决策；最终还必须完成必要的 System 与能力路径回写。生产启用若不属于 Proposal，就不能被“剩余工作”自动推入下一轮。

声称产品能力前进的 Iteration 还必须报告相对 baseline 的目标差距变化：同一正式 Web 入口上的 held-out 自由问题支持率、
重大错误、完整性、至少一个新旧知识跨域问题、提问时 Source/Update/Direct fallback 计数，以及与成熟源码 Agent 的逐题对照。
Manifest 绑定的每个跨域、正式 Web、隐藏 canary 和现场临时问题 Case 必须逐项 PASS，并以
`<拥有该 Case 的 Slice Result ID>#<case-id>` 绑定不可变执行证据；最终 Product Result 必须依赖并聚合全部 Slice Result，不能改写
逐 Case Evidence，也不能用 V-000 的 PASS 或汇总计数代替逐项执行。
只证明本轮新增 Profile/View 的封闭题集通过，或只有旧能力回归而没有跨域组合证据，不得标记为完成的产品进展。结果未显示
可测增量时，应保留为失败/学习证据并默认把 Iteration/Slice 置为 `paused / REWORK`；只有满足正式转向依据时才判为 `rejected` 并建立
新 Iteration。执行后的失败不能标为仅用于执行前行政替换的 `superseded`，更不能继续堆叠下一个孤立知识域。

从 ITER-005 起，任何声称扩展 Software World Model 建模、查询或问答能力的 Iteration，在标记 completed 前必须把本轮新增
能力接入同一个产品代码拥有的本机 Web 问答入口，并由人工提交至少一条支持问题和一条边界/Gap 问题。一次性
`validation.*` launcher、静态回放页、测试计数或 API-only smoke 不能替代该体验。中间 Slice 可以先用 CLI/View 暴露风险，
但整个 Iteration 不得在正式 Web 问答入口尚不可用时完成；这不自动授予公网部署或 Production Activation。

产品 Iteration 被接受时还必须回写能力路径：当前步骤的用户能力已由哪个 Product Result 证明，以及下一个最早阻断差距。
若本轮被拒绝，Roadmap 只能记录同一步骤的方案转向和失败证据，不得把未证明的步骤标成已完成。
