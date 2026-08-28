---
id: PROJECT-GOVERNANCE-ITERATION-LIFECYCLE
kind: project-governance
status: current
authority: project-governance
owners: [project, product]
depends_on: [PROJECT-GOVERNANCE-BOUNDARY, SYS-PRODUCT-SUCCESS, SYS-ADR-019]
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
  → 最小可证伪的产品方向 Gate
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
5. **最早体验与方向点：** 没有代表性 MVP 时，第一个 Slice 如何先在一个长运行动作内交付可重复启动、固定本地地址、持续服务、
   同会话自由提问且单题故障隔离的正式 Web MVP；交付后如何立即用最小、异质、独立真值证据判断核心价值；
6. **停止或转向条件：** 若上游知识不足、只能依赖题型/关键词补丁、不能跨域组合或效果低于成熟源码 Agent，何时停止扩张
   并重新审视建模或查询架构。
7. **差异化价值：** 首个完整 MVP 交付后，立即把完整系统与 current Codex 按相同问题、exact revision、Source scope、输出约束和独立盲评
   比较；目标系统必须绝对质量 PASS、逐题不输 Codex、总体严格超过 Codex，并有可观察的非 locator 世界模型贡献。该比较阻止 hardening
   和方向 PASS，不阻止首个完整体验的形成。用户 `CONTINUE` 后再执行 direct evidence、same-agent source-only、same-agent World Model +
   source、current Codex 四路因果消融。已有代表性 MVP 时可以在新变更前复用它比较。
8. **能力路径位置：** 本轮属于哪一个 Roadmap 能力步骤，哪些前置已被 Acceptance 证明，本轮正式 Web 验证会前进什么，
   以及成功后下一个阻断差距是什么。

不满足上述任一项的 Candidate 可以保留为技术实验或证据收集，但不得被选择为下一轮产品开发 Iteration。风险消除可以是
产品 Iteration 的第一个 Slice，但整个 Iteration 仍须计划同一正式 Web 上可人工验证的通用问答增量；若风险结果触发停止，
则记录证据并把本轮判为失败或转向，不能把组件完成或“学到了什么”称为产品进展。

跨域 Gate 不能用“一条旧能力回归 + 一条新能力孤立测试”拼成。至少一个冻结 Case 必须在同一个问题中同时引用此前已验收
能力和本轮 Slice，正式 Web 与现场临时问题 Gate 还必须执行或探测该跨域 Case。这些关系必须写入 Manifest 的结构化
binding；正文中仅仅出现相关 ID 不算绑定证据。

## 方案假设与方向交接复盘

迭代不是只有“开发—测试”，而是反复执行下面的最小闭环：

```text
冻结关键方案假设与反证
  → 实现最小可持续体验 Alpha
  → 独立技术复核 + 用户实际体验：CONTINUE / REWORK / REDIRECT / REJECT
  ↘ REWORK：保留失败证据 → 同一 Slice 持续通用修复 → 新增权限即时申请 → 重新体验
  → CONTINUE 后工程夯实
  → 正式 Web / hidden canary / 对照验收
  → ACCEPT / REWORK / REDIRECT / REJECT
```

可体验 Alpha 必须早于大规模加固和全面资格评估。它通过真实产品入口、小而多样的输入和新的现场输入尽早暴露核心方向，并确认结果
不是单题偶然。Alpha 明确标记为非验收、非生产；安全、只读、
Secret、授权和失败真实性边界始终生效。完整能力矩阵、全量回归、性能和异常穷举属于 Alpha `CONTINUE` 后的夯实阶段。首次体验所需
的安全或方向验证必须使用聚焦测试，不能以“必要条件”为由提前执行全量回归。

没有代表性 MVP 时，当前产品 Iteration 必须直接冻结一个完整体验长运行动作，交付后立即进入异质问题与 current Codex 方向比较。交付以真实用户主链为准，
不使用 Activation Result、分钟级时钟收据或迟到即非法的时点。首次体验前只运行 targeted impact、startup、safety 和失败真实性测试，不运行 full regression。
Access 与答案质量 Case 必须分离：availability 不等待质量 PASS，hardening 必须等待。

历史 sealed Result 保持不可变，不反向补造后来出现的体验或 Provider 字段，也不能满足新的体验 Gate。首个完整 Web 体验
`requires_result=false` 并立即交付；新的长运行动作只在最终方向/完成交接或确需迁移项目状态时密封 Result，不按首次体验、每次
失败、提交或外部调用切分 Result。

每个 sealed version 中触发外部 dispatch 的有界用户交互单元计一条 live attempt，单元内部模型/角色调用不重复计数；Chat 按 Turn 计数，不按整段 Conversation 合并。相同 failure
signature 最多一个 successor retry；连续两次 attempt 没有用户可见增量即停止该签名的外部重跑并回到本地诊断。无增量 stop
发生在问题边界，只阻止扩域、hardening 和重复外部运行，不撤销仍有效的本地 Slice 授权；不能中途删除调查、回答、Citation 或独立审核
来省 token。

诊断必须先找最早偏差：`Source truth → knowledge construction/admission → cognition projection/query → conversation/task understanding → Agent work state/plan → tool observation/evidence → answer synthesis → independent review → Web`。
每次另记 downstream guard failure 和 display failure；一题允许有多个故障，但只先修最早有证据的 Owner 层。没有逐层 evidence table 与
可证伪 root-cause hypothesis，不得动 Prompt、Schema、Tool policy 或 Contract。任何通用修复先通过本地最小复现和至少两个未参与修复的相邻案例，
然后只用一个有界 live canary 单元；Chat 目标必须使用最小多轮 Conversation，不得以孤立一题代替。同一 failure signature 修复一次仍复现，停止规则堆叠并进入架构职责评审。Alpha 前测试只允许 targeted impact、
startup、safety；full regression 仅在 Alpha `CONTINUE` 后的 hardening 和正式验收前运行。

Provider route 在首次外部执行前按 `preferred route → fallback route` 角色顺序预密封，并由 standing external authority
一次性批准两个角色的 disclosure scope、execution profile、预算与适用的 admission policy；范围内的新 session、Turn、问题或
run 无需再次向用户申请。preferred-route attempt 若以冻结的 Provider/模型能力 outcome 终态结束且没有 authorized
answer，可在同一 logical interaction unit 内透明启动最多一个 fallback-route attempt；用户不重新提交。具体 Provider/model 名称只能由
execution profile 配置和执行收据携带，不得进入通用状态机、action ID 或路由分支语义。
fallback 从 immutable original interaction input 与 exact cognition 重跑全链，不读取 primary attempt 的中间产物；Chat 还必须携带与当前 Turn 相关的 exact Application-sealed Conversation Context。迟到 primary 只隔离审计。同
Provider retry 为 0；Application/Source/Security failure 不能触发 fallback。输出/schema 或 Reviewer 拒绝必须按 primary capability failure
记录，而不是误标为网络不可用。所有 planned fallback-route 调用均受其 execution profile 引用的 admission plugin 硬准入；
fallback eligibility 和普通外部授权不等于该 plugin 的调度准入。run receipt 与逐 request 准入条件/一次性 exact override
重验必须早于 Provider socket/connected descriptor、TLS、credential 和
HTTP；缺失时相应计数为 0。完整最坏质量链必须能在 admission plugin 准入的时间与资源边界内完成，准入失效后不创建新 request；无法完成审核时当前交互失败
关闭，不降低质量。等待准入时继续 preferred-route-only、本地归因、修复、targeted tests 和 candidate freeze。

权限边界采用 standing-authority continuity。Slice 开发授权、人类 standing external authority、系统派生 exact execution/admission receipt
与一次性 scope-delta grant 分离。`PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY@1` 应覆盖已确认的 canonical public source、许可记录、exact
commit/tree、允许的 revision selection policy、clean 只读测试工程、allowlist、Provider/model/endpoint/credential account route、预算、调度、有效期与 loopback
`EVALUATION_ONLY` Sink；source identity 不变时的新 run、Conversation、Turn 或问题不得逐次申请。每次外部动作仍须
在 Source disclosure、network 和 credential 前生成回指 standing authority 的 one-use exact machine receipt，并校验 source、session、route、预算和调度；该 receipt 只
证明符合既有授权，不能自行授权或扩权，缺失/失配时失败关闭。

只有私有、来源/许可证未知、仅本机存在或 dirty 数据，超出 approved upstream/revision selection policy/allowlist，新的外部接收方/Provider/model/
endpoint/credential account，预算增加，超出 fallback admission policy 的调度范围或需要一次性 override，外部写入、非 loopback 暴露、
Production Activation 或其他明确排除项才是 scope
delta。实现者完成 credential-free preflight 和 exact identity/disclosure freeze 后，必须
直接调用审批能力或提交最小 exact-delta request；不得先问是否申请，也不得只报告“未授权”后退出。批准后自动继续；等待期间继续所有
独立本地工作。只有 delta request 已实际发出且安全替代工作穷尽时，才可用 `WAITING_EXACT_GRANT / IN_PROGRESS` 让出回合。用户明确
停止/转向/拒绝或不可绕过的安全禁止仍可终止开发；本规则不授权任何 standing scope 之外的动作。

项目不得连续进行多轮 Prompt、Schema、Contract 或评测优化，却一直没有可供用户操作的真实体验。可供操作是指可重复启动、固定本地
地址、同一会话连续自由提问、版本和限制可见，且单题失败不会关闭服务；一次性运行器或启动前冻结单题的页面不满足该定义。若目标是
Chat，还必须冻结语义追问、纠正、总结、逐轮证据/审核和新对话隔离 Gate；仅共享 Runtime Session 的多个独立问题不能标成 Chat。Alpha
发现缺陷时默认先 `REWORK`；只有满足本政策的转向条件时才 `REDIRECT` 或 `REJECT`。正式 Gate 不能成为延迟方向反馈的理由，
方向体验的认可也不能替代最终正式 Gate。

本门禁从 `ITER-008` 开始强制执行。Proposal 必须在编码前写明少量决定方案能否成立的关键假设、每项假设的最早反证方式、
反证后停止或换路的动作，以及被认真比较过的替代方案。没有代表性 MVP 时，第一个 Slice 必须优先形成真实完整用户主链，不能只实现“基础组件”并把真实产品效果留到最后。
完整体验交付后立即完成小样本 current Codex 严格价值 Gate；已有可代表纵切时该 Gate 可位于新产品/Web 变更前。四路因果消融、完整 hidden、跨工程和统计复验仍在用户 `CONTINUE` 后的 hardening Slice 或最终验收执行。

首个完整体验和随后的独立质量比较共同形成一次方向交接。交接 Result 中的“Architecture reflection and continuation decision”至少回答：

1. 原方案假设是什么，实际证据与预期哪里一致、哪里不一致；
2. 问题属于架构、实现、配置/环境、需求/使用还是验证设计，影响是个案还是系统性；
3. 知识表示、查询/编排、产品 Web 链和验证方案各自是否仍成立；
4. 完整体验后的首次方向 Gate 必须报告完整系统与 current Codex 的绝对质量、逐题关系、严格总体差值和可观察的非 locator 世界模型
   贡献，不能用用户体验偏好替代；四路因果消融在用户 `CONTINUE` 后另行报告；
5. 本动作 Finding 如何处置，当前最早未证明的风险是什么；
6. 明确作出 `CONTINUE`、`ACCEPT`、`REWORK`、`REDIRECT` 或 `REJECT` 决策并说明理由。

关键假设在 Proposal 中冻结稳定 ID、原文、最早反证和 Owner，方向交接按 ID 逐项记录 `SUPPORTED / FALSIFIED / UNRESOLVED`、exact Evidence、
Verdict 与 Impact。不需要为整张假设表或 Reflection 正文维护人工 SHA-256；Git 版本和交接 evidence 身份负责固定它们。`CONTINUE` 或 `ACCEPT` 要求当期关键假设均为 `SUPPORTED`；任一项 `FALSIFIED / UNRESOLVED` 阻止晋级，但默认决定为 `REWORK`。

`REWORK` 表示目标和总体架构仍成立，当前失败可以通过实现、提示、答案组织、审核、配置或局部 Contract 的通用修复处理。单个错误答案、
问题陈述、用户要求复核或 Reviewer 的遗漏意见都不能推导 `REDIRECT`。`REDIRECT` 只能绑定以下一项明确依据：用户明确改变产品方向；
证据证明核心架构职责或主数据流不可成立；连续修复达到 Proposal 预先冻结的无进展上限。问题被分类为“系统性”也不自动等于核心架构
证伪。`REJECT` 只用于明确放弃当前产品增量，或在既定约束下没有可行路线。

成熟源码 Agent 的正向价值比较必须在方向交接 Result 中记录冻结指标、数值 actual、输入身份、比较 Case 和独立裁决收据。比较失败也保留可重放报告，不能只写 `FAIL`。
技术裁决 Owner 必须未参与任一候选答案生成；用户消息只作方向、授权或接受决定，不能冒充盲评 verdict。未达到严格为正的答案质量阈值不能 `CONTINUE/ACCEPT`。

方向复盘完整只表示证据可审计，不表示产品方案本身 PASS。只有产品质量 Gate 全部 PASS 且用户决定 `CONTINUE` 才能解锁 hardening；最终只有产品 Gate 全部 PASS 且决定 `ACCEPT` 时，
才可形成 Iteration Acceptance。`REWORK` 只阻止 PASS 声明、晋级和 hardening；若现有 Slice 授权仍覆盖通用修复，保持
`authorized / in-progress / coding_input=true` 并持续返工。只有 scope/Owner 变化、用户明确暂停或本地授权失效时才进入
`paused / coding_input=false`，且实现者应立即申请恢复所需的最小精确权限；恢复同一 Slice，不得新建 Iteration。`REDIRECT` 表示最终目标
不变但当前总体方案满足上述转向依据，当前 Iteration 必须按 `rejected` 封存并用新
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
2. 冻结 baseline、System IDs、外部输入、风险、Acceptance 和第一个纵向 Slice，不复制上一轮运行身份；同时冻结完整体验长运行动作、交付后 current Codex 方向 Gate、
   Access/Quality 分离、live-attempt stop rule 和透明 Provider route。
3. Readiness Review 记录用户的明确授权，把 Proposal 与 Readiness 状态改为 `accepted`；未授权字段不得用默认值代替。
4. 把 Iteration Index、Manifest 与第一个 Slice 改为 authorized，把 Slice `authority` 改为 `current-development`，并将 Index/Slice 的 `coding_input` 改为 `true`；Manifest 已规划的后续 Slice 保持 `proposed / proposed-development / coding_input: false`。
5. 最后更新 `project/current.md` 的 `active_iteration`、`active_slice`、`plan_revision_ref`、`next_action` 与 `depends_on`。Manifest 还必须冻结
   action-level 允许/禁止路径、外部执行权、交接时的唯一 Result 和预声明后继；`scripts/docs.py check` 与 base→target plan gate 都通过后才可开发。

首次方向比较前必须冻结当时 current Codex 的客户端/二进制、实际模型、reasoning、工具、权限，以及双方相同的 exact revision、问题、
Source scope、输出约束、fresh-task、答案先密封和独立盲评协议；不得复制历史 Codex 身份或把任何模型答案指定为 Oracle/裁判。用户
`CONTINUE` 后的因果消融再冻结 direct evidence 与两个系统 Agent 路的同 Provider/model/config 和公平变量。

同一 Iteration 的累积 Slice 以 Manifest `new_capability_slice_refs` 的顺序推进：执行态必须为“零个或多个 `completed` + 恰好一个
`authorized/in-progress` + 零个或多个 `proposed`”；只有 scope/Owner 变化、用户明确暂停或本地授权失效时，修复等待态才使用同样的
completed 前缀、恰好一个 `paused` 当前 Slice 和 proposed 后缀。external scope-delta grant pending 不属于该状态，活动 Slice 仍是
`authorized/in-progress`。每个后续 Slice 必须直接依赖前一个；前一个 Slice 的人工 Web/停止 Gate 完成并形成交接 Result，且方案复盘 Gate 为 PASS、用户决定为 `CONTINUE` 后，可按 Manifest 已预授权的后续合同直接移动
`project/current.md.active_slice`，不再对同一 scope 重复申请一次授权。后续 Slice 的 `depends_on` 绑定前一 Slice 的 exact 交接 Result。可体验 MVP 以真实可见问题与现场输入尽早判向，不要求
hidden canary；从 Alpha `CONTINUE` 后的工程夯实 Slice 开始，最终 held-out 验证前的每个适用 Slice 必须在本 Slice 产品代码冻结后
通过独立持有的隐藏 canary，曝光后修改产品会烧毁 canary并保留原失败。不得为了通过 Readiness 一次性授权全部 Slice，也不得跳过失败
Slice。完成的 Slice 使用 `historical-development / coding_input: false`，当前 Slice 使用
`current-development / coding_input: true`，后续 Slice继续保持 proposed。

若某个 Slice 的阻断 Gate 触发，默认只阻止 PASS、晋级和 hardening，失败证据留在当前动作工件中，不按每次失败生成 Result 或移动游标。现有授权覆盖同 Slice
修复时保持 `authorized / coding_input=true` 和 `project/current.md` 指针；需要新增权限时直接申请。只有 scope/Owner 变化、用户明确暂停或
本地授权失效时才标记 `paused / coding_input=false` 并暂时移除指针；新授权后恢复同一 Slice，不得因修复循环创建新 Iteration。Manifest
的 `rework_result_refs` 只保留已经密封的历史失败交接。只有正式 `REDIRECT` 或 `REJECT` 才把 Iteration 设为
`rejected`，失败 Slice 设为 `blocked`，后续 proposed Slice 只保留历史。任何 redirect 都必须建立新 Iteration，重新经过 Proposal、
Readiness 和必要的新 scope 授权。

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
  ├→ failed attempt → active same-Slice REWORK → standing authority reused; exact delta requested only on scope change
  ├→ stop / evidence-driven redirect → rejected
  └→ pre-execution administrative replacement → superseded
```

## Readiness gate

- Proposal 已通过产品目标对齐门禁，目标差距、累积路径、独立持有且对实现隐藏的可测增量、跨域问题、最早 Web 体验点、
  现场临时问题和停止条件均已冻结；
- Proposal 已绑定 planning-only Roadmap 中的精确能力步骤，前置接受证据、本轮结束时的 Web 用户能力和成功后的下一阻断差距均已明确；
- Proposal 已冻结关键方案假设、最早反证、替代方案和逐 Slice 复盘计划；没有代表性 MVP 时先在一个长运行动作内形成完整 Web 体验，
  交付后立即把完整系统与 current Codex 严格比较。目标系统绝对质量 PASS、逐题不输 Codex、总体严格超过 Codex 且有可观察的非 locator
  世界模型贡献后，用户才可决定进入 hardening；完整四路因果消融在 `CONTINUE` 后执行；
- Experience policy 已绑定完整持续 MVP、Access/Quality 分离、交付后独立质量比较、首次体验前 full-regression 禁止、相同 failure signature 重试上限和连续无可见增量停止条件；不得设置 Activation 或分钟时钟合法性 Gate；
- Provider policy 已冻结 preferred-first ordered route、两个角色的 execution profile 与 session disclosure scope、transparent independent fallback
  attempt、eligible/ineligible outcome、迟到结果隔离、零同 Provider retry、fallback admission plugin/Case/receipt、外部网络前硬准入、逐
  request 重验、一次性 exact override 和
  “成本不得降低质量”；
- 一个明确 Outcome 和非目标；
- 所引用 System 文档均 current，或先完成所需 System 设计；
- 每个 Slice 有可验证退出条件和风险边界；
- 外部输入、standing external authority、机器派生 exact receipt、scope-delta 边界、Secret Reference 和原始证据保存方式已说明；公开开源
  exact revision、clean、allowlisted、只读测试在已批准 route/预算/调度/有效期和 loopback evaluation 边界内不得逐 run/逐题申请；若评测
  问题由用户现场持有，则必须明确在产品代码冻结前不收集
  问题，并把未披露 marker 与完成前必须替换的 exact Result 绑定写入 Manifest；
- Verification Matrix 能区分机械测试、真实能力和产品价值；
- `current.md` 同一时刻最多指向一个活动迭代和一个主要 Slice。

`scripts/docs.py` 只负责检查引用、状态、digest、计数和依赖是否闭合，不能替代产品判断。Readiness Reviewer 必须实际核对
冻结工程、隐藏问题协议、跨域案例和 Web 体验设计，确认它们不是把 parser、Profile/View、CLI 或固定关键词题型重新包装成
产品增量；随机 digest、空洞 case 名和自报 PASS 都不构成证据。该判断必须由用户明确接受并绑定 exact review reference。

## Completion gate

代码完成不是迭代完成。每个 Slice 都必须有实际 Result、失败/限制、方案复盘、相关 Finding disposition，以及明确的继续、接受、
修复重试、转向或拒绝决策；最终还必须完成必要的 System 与能力路径回写。生产启用若不属于 Proposal，就不能被“剩余工作”自动推入下一轮。

首个持续 MVP Result 必须报告完整主链、用户交接身份、首次体验前 targeted/startup/safety/full-regression 次数、轻量 live-attempt ledger、同签名最大重试数、
连续无可见增量次数和 stop 后外部 dispatch 数；不报分钟时钟或 Activation 结果。Provider Result 必须逐 attempt 报告 sealed identity、trigger/outcome 分类、是否重跑完整链、
中间产物复用、迟到 primary 隔离、fallback 次数和用户重提次数；fallback route 还必须报告 execution profile identity、
admission plugin/Case/receipt、逐 request admission verdict、override、配置源检查、Provider socket/TLS/credential/HTTP 零计数或实际计数以及任何准入违规。缺失或把 Access PASS 当 Quality PASS 都不能晋级
hardening。

声称产品能力前进的 Iteration 还必须报告相对 baseline 的目标差距变化：同一正式 Web 入口上的 held-out 自由问题支持率、
重大错误、完整性、至少一个新旧知识跨域问题、提问时 Source/Update/Direct fallback 计数，以及与成熟源码 Agent 的逐题对照。
首个完整 MVP 交付后，首次对照必须使用完整系统与 current Codex 的独立盲评：系统自身绝对质量 PASS、逐题不输 Codex、总体质量差值
严格为正，且至少一项可观察的非 locator 世界模型贡献；全体打平、任一重大失败、无法裁决、盲化无效或只凭效率优势均不能完成方向 Gate。
用户 `CONTINUE` 后的四路消融还必须证明完整认知相对 direct evidence 与 source-only control 的因果价值。
Manifest 绑定的每个跨域、正式 Web、隐藏 canary 和现场临时问题 Case 必须逐项 PASS，并以
`<拥有该 Case 的 Slice Result ID>#<case-id>` 绑定不可变执行证据；最终 Product Result 必须依赖并聚合全部 Slice Result，不能改写
逐 Case Evidence，也不能用 V-000 的 PASS 或汇总计数代替逐项执行。
只证明本轮新增 Profile/View 的封闭题集通过，或只有旧能力回归而没有跨域组合证据，不得标记为完成的产品进展。结果未显示
可测增量时，应保留为失败/学习证据并进入 active same-Slice `REWORK`；只在 scope/Owner 变化、用户明确暂停或授权失效时使用
`paused`。只有满足正式转向依据时才判为 `rejected` 并建立新 Iteration。执行后的失败不能标为仅用于执行前行政替换的 `superseded`，
更不能继续堆叠下一个孤立知识域。

从 ITER-005 起，任何声称扩展 Software World Model 建模、查询或问答能力的 Iteration，在标记 completed 前必须把本轮新增
能力接入同一个产品代码拥有的本机 Web 问答入口，并由人工提交至少一条支持问题和一条边界/Gap 问题。一次性
`validation.*` launcher、静态回放页、测试计数或 API-only smoke 不能替代该体验。中间 Slice 可以先用 CLI/View 暴露风险，
但整个 Iteration 不得在正式 Web 问答入口尚不可用时完成；这不自动授予公网部署或 Production Activation。

产品 Iteration 被接受时还必须回写能力路径：当前步骤的用户能力已由哪个 Product Result 证明，以及下一个最早阻断差距。
若本轮被拒绝，Roadmap 只能记录同一步骤的方案转向和失败证据，不得把未证明的步骤标成已完成。
