---
id: PROJECT-GOVERNANCE-DEVELOPMENT-DESIGN
kind: project-governance
status: current
authority: project-governance
owners: [architecture, engineering]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, PROJECT-GOVERNANCE-BOUNDARY]
code: []
tests: []
---

# Development Design Policy

Development Design 是当前编码输入，不是长期详细设计百科。它应当足以让人或 Agent 知道要改变什么、不能破坏什么、如何验证，并允许局部实现由代码和测试快速探索。

## 先体验方向，再夯实实现

凡是用户可以直接感知、且方向风险较高的产品变化，计划默认拆成三个阶段，顺序不得倒置：

1. **可体验 Alpha：** 用最小纵向实现直接形成可重复启动、持续可操作的真实产品版本，并用一组小而多样的输入和现场输入尽快判向；
2. **工程夯实：** 只有 Alpha 被明确确认后，才补齐完整契约、边界处理、回归、性能、可观测性和质量评估；
3. **正式验收：** 在实现稳定后执行隐藏输入、对照、现场问题和发布前 Gate。

可以在 Alpha 内设置更早的内部检查点，但它不能成为独立晋级门槛，也不能用一次性运行、静态回放或启动前冻结问题代替可体验版本。
用户可操作的真实结果必须先于与方向判断无关的全面夯实。

从 `ITER-010-PDR-002` 后首个新建产品迭代起，首个持续 Web Alpha 必须把小样本 current Codex 同题盲评并入同一体验出口，而不是把
比较继续推迟到 hardening，也不是在体验前增加独立阶段。Alpha 至少覆盖一条原失败题和另外两条相邻或异质问题，后两条中至少一条是
产品冻结后的现场输入；完整
hidden、跨工程与统计复验仍在 `CONTINUE` 后执行。Alpha 只有在系统自身绝对质量合格、逐题无物质性退步且总体答案质量严格优于
Codex 时才能进入工程夯实；全体打平时使用 `REWORK`。

方向体验版不是验收版，不得声称完整、稳定或可生产使用，但始终必须遵守数据/源码授权、只读和写入权限、Secret 隔离、外部调用
披露、失败不伪造成功等不可推迟的安全边界。首次体验前不得执行全量回归；安全运行或判断核心方向所需的验证只能收窄为聚焦测试。
完整 Schema、全面能力资格、性能优化或完备证明材料同样不得放在首次体验之前。

从 `ITER-012` 起，第一个持续 Alpha Slice 采用固定体验时间盒；ITER-010 可以在 Manifest 显式 opt in。计时点是 Slice 授权后的第一次
产品代码变更，而不是第一次 live 调用：60 分钟内页面必须可启动，180 分钟内必须形成用户可连续操作的持续 Alpha；到 240 分钟仍未
形成时，硬停止功能扩张、hardening 和外部模型调用，密封已有证据并缩围复盘。60/180 是交付检查点，不能等完整质量证明才开始计时；
240 是停止边界，不能以“再跑一次”绕过。

若该 policy 在一次失败 Result 密封后才被采用，Manifest 必须用 `historical_pre_policy_result_refs` 精确列出这些历史 Result，并声明它们
不能满足新的体验 Gate。门禁继续验证其 failed-preserved 身份、所属 Slice、不可变摘要和后继非编码 REWORK 决定，但不得反向要求历史
Result 补造当时尚不存在的体验或 Provider 字段。新授权后的任何 Result 均须完整遵守当前 policy，不能加入该历史列表绕过验证。

首次体验前只允许最小启动、安全边界、失败真实性、一次 current Provider 资格确认和最多一个 Provider 前本地/Mock Access smoke。全量回归、完整能力矩阵、hidden、
跨工程和统计对照都必须后置。Access 与 Quality 是两道不同的 Gate：Access 只证明 credential/reference、endpoint/model、current exact
Conformance、策略能力资格和 active hold；它可以使页面 availability 成立，但不能证明答案正确。只有用户可见答案质量 Case PASS 后，
才可进入 hardening。

live attempt 使用轻量计数：同一 sealed product version 中，每个触发任一外部 dispatch 的有界用户交互单元计一次 attempt，不按单元内部模型/
角色调用数放大；对 Chat，这个单元是 Turn，一段 Conversation 中多个已 dispatch Turn 分别计数；纯本地诊断不计。相同 failure signature 最多重试一次；连续两次 live attempt 没有用户可见增量，立即停止外部重跑，
回到本地根因诊断。此停止规则发生在问题之间；已经开始的问题仍须执行完整调查、答案、Citation 与独立审核链，调用或成本不得成为
质量裁剪理由。

live failure 必须先沿 `Source truth → World Model cognition → conversation/task understanding → Agent work state/plan → tool observation/evidence → answer → independent review → Web`
定位最早偏差。没有可证伪 root-cause hypothesis，不得修改 Prompt、Schema 或 Contract。修复顺序固定为：本地最小复现，至少两个未参与
修复的相邻案例通过，再执行一个有界 live canary 单元；Chat 目标必须把该单元冻结为最小多轮 Conversation，不得用孤立一题代替。不能直接用下一次昂贵 live run 猜测修复。相同 failure signature 经过一次通用修复仍复现，
必须停止堆规则并评审架构职责。首次体验前只运行 targeted impact、startup 和 safety 测试；full regression 在 Alpha `CONTINUE` 后的
hardening 和正式验收前各运行，不得用它延迟首个体验。

Provider route 默认 `VOLCENGINE_ARK → DEEPSEEK`，并在 session 开始前预授权 ordered route 与双方 disclosure scope。Ark attempt 因已冻结的
Provider 或模型能力原因终态结束且未形成 authorized answer 时，可对同一 logical interaction unit 透明启动最多一个 DeepSeek attempt，用户无需
重提或新建 session。两个 attempt 必须独立密封；fallback 从 immutable original interaction input 与 exact World Model cognition 重跑完整链，禁止
复用前次中间产物；对 Chat，fallback 输入必须是 immutable original Turn Request、与该 Turn 相关的 exact Application-sealed Conversation Context 和 exact World Model Cognition，不得退化为只重放孤立问句；迟到 primary 结果只允许隔离审计，不得覆盖已密封结果；同 Provider retry 为 0。Provider 输出/schema 或模型审核失败
必须记录为能力失败，不能伪称网络不可用；Application、Source 或 Security 失败不得通过 fallback 掩盖。DeepSeek 批量运行优先使用执行时
重新核对的官方非高峰窗口，峰时紧急启动需审计 override，但已开始问题仍不得降低质量。

可体验 Alpha 必须记录 `CONTINUE`、`REWORK`、`REDIRECT` 或 `REJECT`；只有 `CONTINUE` 才能进入工程夯实。任一阻断项失败默认只阻止
晋级：保留失败证据、暂停当前 Slice，并在同一 Slice 做通用修复和重新体验。
回答错误、用户指出问题或独立评测要求复核，本身都不能推出 `REDIRECT`。只有用户明确改变产品方向、核心架构假设被证伪，或者达到
Proposal 预先冻结的无进展上限，才可以转向；否则使用 `REWORK`。若最小可体验 Alpha 本身无法较快形成，应把它视为优先修复的风险，
而不是先开发更多内部组件。

## 可体验版本的最低定义

一次性验证运行、静态回放页或只能回答启动前冻结问题的页面，不是可体验版本。首次方向体验至少必须同时满足：

- 可从一个精确版本用固定、可重复的启动方式启动；
- 使用固定本地地址，并持续服务直到用户主动停止；
- 用户可以在同一浏览器会话连续自由提问，不需要每题重启、重新构建或理解内部运行编号；
- 页面明确显示版本、实验性质和已知限制；
- 单题失败只结束该题并显示真实失败或限制，服务仍可接受后续问题。

“同一浏览器会话连续自由提问”只证明持续问答，不自动证明产品已经是 Chat。若产品目标声明语义多轮 Chat，首个体验版本还必须显示有序
消息历史和“新对话”，能够解析追问与指代、接受用户纠正、按当前上下文总结，并证明每轮都有独立 Request/Evidence/Review 身份且新对话
不会继承旧指代或工作状态。上一轮答案和 Provider 隐藏记忆只能作为受信 Application 密封的对话上下文候选，不能直接成为本轮事实证据。
首次 Chat Alpha 可使用进程内短期状态；跨重启长期记忆、分支和多 Agent 不是方向确认前置条件。

完整 hidden、跨工程对照、性能证明和全量回归不是可体验版本的前置条件。首次体验 Slice 必须直接交付上述版本；不得把它拆成若干
只有内部组件或一次性运行证据、却没有持续可操作页面的前置 Slice。

## 同一 Slice 的修复循环

体验发现缺陷后，必须保留原问题、原答案、证据、评审和产品代码冻结身份，再完成根因分类。只要产品目标、总体架构、主要数据流、
模型职责和安全边界没有改变，就在当前 Slice 做最小通用修复，复测原问题，并增加相邻表达或不同类型问题防止特判。失败尝试进入
`paused / coding_input=false`，不再由 `project/current.md` 指向；新的用户授权到达后，同一 Slice 可以恢复为
`authorized / coding_input=true`。每次重新授权都必须使用新收据，历史失败 Result 通过 Manifest 的 `rework_result_refs` 保留。

Proposal 必须预先冻结无进展的可测定义和正整数尝试上限。达到上限只触发一次架构转向评审，不自动证明应当转向；实际
`REDIRECT` 仍必须绑定用户明确转向、核心架构证伪或该上限已达到中的一项。模型调用次数不得充当无进展定义，也不得成为降低调查、
回答或独立审核质量的理由。

输入持有、技术质量裁决和产品方向决定必须分离。用户可以持有现场问题并决定继续、改向、停止或最终接受，但正确性、完整性、引用支持、
边界判断和是否存在特判必须先由独立评测方裁决，不能把代码事实审核转嫁给用户，也不能用用户喜欢某种表达替代技术质量 PASS。
current Codex 对照是强外部基线参赛者，不是事实来源或评测方；它必须在 fresh 独立任务中先生成并密封答案，系统看不到该答案，评测方
也不参与任一候选答案生成。系统对 current Codex 的产品价值比较与 full cognition 对 locator-only/empty 的因果消融必须分别计划。

## 每个 Slice 必须包含

- 目标结果、触发和明确非目标；
- 当前行为与期望行为；
- 引用的 System Contract/Invariant，而不是复制正文；
- 受影响入口、Owner、数据迁移与兼容边界；
- 需要在编码前确定的跨模块接口语义；
- 关键风险、开放问题和失败关闭方式；
- 可执行的验收场景和 Finding 回写入口。
- 最小方向体验的真实入口、代表性任务、明确不做项、可见限制和体验后方向决策点。
- 可体验版本的重复启动方式、固定本地地址、连续自由提问、版本/限制显示和单题故障隔离证明。
- 若目标是 Chat，增加追问、纠正、总结、逐轮证据/审核、新对话隔离和最小五轮语义链证明。
- 若目标是 Agent，明确主 Agent 拥有目标、假设、计划、工具选择、观察解释、重规划和完成判断；平台继续拥有权限、执行、证据与审计，
  独立 Reviewer 继续拥有放行前技术复核。
- 同一 Slice 的修复记录、重新授权边界，以及预提交的无进展定义和尝试上限。

## 不应预写

- 私有类、函数、表字段和内部状态枚举；
- 可由重构和测试低成本决定的算法步骤；
- 逐错误码、逐日志字段或逐 Mock 行为；
- 没有当前消费者的未来扩展点；
- 与 Contract 重复的大段背景和不变量。

## 何时先设计再编码

跨 Owner 权限、公开协议、不可逆数据、并发一致性、安全隔离或迁移语义必须先闭合设计。局部实现、可逆重构和算法选择可以通过最小代码/测试实验决定；若实验发现系统影响，立即进入 Finding 回写流程。

## Variance

实现与 Slice 不同不自动是错误。记录原因和证据：局部差异可直接修订 Slice；影响 System 的差异必须先暂停并升级；被延后的价值进入 Roadmap Candidate，不能埋在 Result 尾部。
