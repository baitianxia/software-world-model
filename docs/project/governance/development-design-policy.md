---
id: PROJECT-GOVERNANCE-DEVELOPMENT-DESIGN
kind: project-governance
status: current
authority: project-governance
owners: [architecture, engineering]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, PROJECT-GOVERNANCE-BOUNDARY, SYS-ADR-019]
code: []
tests: []
---

# Development Design Policy

Development Design 是当前编码输入，不是长期详细设计百科。它应当足以让人或 Agent 知道要改变什么、不能破坏什么、如何验证，并允许局部实现由代码和测试快速探索。

## 先证伪方向，再提供最小体验，最后夯实实现

凡是用户可以直接感知、且方向风险较高的产品变化，计划必须围绕“最早能证伪的产品价值假设”拆分，而不是围绕组件完成度拆分。默认
顺序如下，不能把方向判断拖到内部实现完成之后：

1. **最早方向证据：** 复用既有 clean 产品和能力，以最小实现/对照直接检验核心价值。已有可运行产品但替代价值未证明时，先做小而异质、
   独立真值、强基线和严格失败条件的受控 Gate；没有可运行纵切时，先做最小可操作 Alpha。不得先完善 Prompt、Reviewer、Provider、Web
   或内部证明再事后比较。
2. **最小可体验 Alpha：** 方向证据 PASS 后，立即形成可重复启动、持续可操作的真实产品版本，让用户用自由问题、追问和纠正判向。
3. **工程夯实：** 只有严格质量 Gate 和 Alpha 用户方向都通过后，才补齐完整契约、边界处理、回归、性能、可观测性和扩大评估。
4. **正式验收：** 在实现稳定后执行隐藏输入、跨工程、现场问题和发布前 Gate。

最早方向证据必须是一个有界动作，不得演变成长期内部工程。它通过后立即进入最小体验，失败后只允许对最早责任层做一个通用修复并用
原题和至少两个未参与修复的异质问题复验。一次性运行、静态回放或启动前冻结问题不能冒充可体验版本；可体验版本也不能替代严格方向
质量证明。两者都必须早于与方向判断无关的全面夯实。

当前开发权威还必须把唯一下一动作、允许/禁止路径、外部执行权、唯一 Result 和 PASS/FAIL/INVALID 后继写入 Manifest。Slice 的广义代码
范围不能覆盖 action-level 白名单；base→target 差分必须只使用 base plan 授权，目标分支不得通过同时修改计划自我扩权。具体机械合同由
`PROJECT-GOVERNANCE-PLAN-EXECUTION` 拥有。

### 方向探索检查点必须是用户交付出口

方向尚未被用户确认时，Alpha 不能再被计划成“全部产品 Gate 通过后一次性交付”的大任务。当前 Slice 必须在最前面维护一张不超过一页的
执行卡，用少量有序检查点依次交付可启动产品入口、可持续方向体验，以及本轮要求的方向证据和用户判向。具体检查点数量和 Alpha 后时限由
当前 Iteration 按最小判向需要冻结，不作为所有未来工程的固定流程。

检查点是当前 Slice 内的交付和方向决策点，不是自动结束开发回合的停止点，也不是新 Iteration、Slice、Readiness 或授权阶段。它们只能
在当前 Slice 授权仍 active 时沿用该授权，不能恢复已暂停、消费或失效的授权；外部调用仍须落在 active standing external authority 内并
生成逐次精确审计收据。每个检查点完成后必须
立即把启动方式、地址、精确版本、已知限制和可操作结果交给用户；若下一项工作仍在现有授权和既定方向内，交付后继续执行，不为重复
确认自行停下。代码、测试、文档、Gate 数量或内部链路完成都不算用户可见增量。

未达到检查点时，必须交付最后一个可运行版本、唯一最早阻塞点和可证伪根因，并停止范围扩张；但当前最小体验目标、本地根因归因和已
授权的收敛工作继续，不能把 checkpoint FAIL 当成开发终态，也不能用建设无关内部组件掩盖没有体验出口。任何检查点上用户明确认为方向
错误，才立即停止后续检查点和 hardening。减少的是场景数量，不是单个已开始交互的 Evidence、Citation、独立 Review 或失败关闭质量。
完整回归、跨工程、hidden、性能、持久化和协议夯实只有质量通过且用户 `CONTINUE` 才能解锁。

### 授权连续性与开发回合退出条件

Slice 开发授权、人类授予的 standing external authority、系统派生的 exact execution/admission receipt 和一次性 scope-delta grant 必须分开。
standing authority 在 Readiness 或后续明确用户决定中以 `PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY@1` 一次性冻结可重复使用的外部范围：
canonical public source、许可/公开性记录、允许的 revision selection policy、每次运行的 exact commit/tree、allowlist 与只读披露边界，Provider/model/endpoint/credential account route、
调用/重试/token/时长预算、调度窗口、有效期/撤销条件、结果保存、loopback `EVALUATION_ONLY` Sink 和 exclusions。对于上述公开开源测试
工程，只要 source identity、clean 状态、route、预算和调度仍在已批准范围内，新的 run、Conversation、Turn 或问题不构成权限变化，不得逐
run 或逐题向用户重新申请。

每次实际外部动作仍必须在 Source disclosure、network 或 credential 前冻结 exact product/source revision、session/turn、Provider/model/
endpoint/credential account、披露内容、预算和时间判定，并生成系统派生的 one-use exact receipt；receipt 必须回指 active standing
authority，且只能证明本次动作满足既有权限，不能自行创建、扩大或替代人类授权。standing authority 存在但 receipt 缺失、失效或与
本次身份不一致时必须失败关闭；反之，系统生成 receipt
也不能为未获人类授权的范围放行。

只有发生 scope delta 才提交新的最小 exact human-approval request：私有、来源/许可证未知、仅本机存在或 dirty 的数据；超出已批准
upstream/revision selection policy/allowlist；新的外部接收方、Provider、model、endpoint 或 credential account；提高调用、重试、token、时长或费用预算；
超出 fallback admission policy 的调度范围或需要一次性 override；任何外部写入；非 loopback 暴露或 Production Activation；或 standing
authority 明确排除的其他动作。同一 approved
public upstream/revision policy 内的新 clean exact commit 经 Source Authority 复核后只重新派生机器收据，不属于 delta。普通公开开源
只读测试在 standing authority 内切换问题或运行身份同样不属于 delta。到达 delta 边界后，实现者
先完成不需要该权限的 preflight 和 exact identity/disclosure freeze，再直接调用平台审批能力；没有审批入口时提交一条完整的 exact-delta
request。不得先问“是否要申请”，不得只报告缺权限后结束，也不得重复请求相同 pending delta。相同 active standing authority 必须复用；
批准 delta 后在 exact scope 内自动继续，不再重复确认计划。

等待 scope delta 时继续所有不依赖该 delta 的安全工作。只有 delta request 已实际发出且本地替代工作穷尽，才能以
`WAITING_EXACT_GRANT / IN_PROGRESS` 让出回合；必须报告 request identity、唯一受阻动作和批准后自动执行的动作。授权被拒绝时不得绕过或
重复催促，只能继续安全替代方案或在范围/证据变化后申请更窄 delta。

开发回合只能在当前阶段交付已实现并交给用户、scope-delta exact request 已发出且安全替代工作穷尽、用户明确
`STOP/REDIRECT/REJECT`，或存在不可
通过申请绕开的安全禁止时结束。“需要授权”、局部 Gate 完成、timebox FAIL 或外部权限为零本身都不是退出条件。

从 `ITER-010-PDR-009` 起，current Codex 严格基线和 World Model 因果消融必须在任何新产品/Web 变更前，或在没有既有可运行纵切时并入
最早 Alpha 出口。小样本至少覆盖一条系统性失败类别和另外两条异质问题，至少两条未参与开发；禁止只用模块/POM 问题。目标系统只有在
自身绝对质量合格、逐题不输直接证据/仅源码/current Codex、总体严格优于 Codex 且有非 locator 世界模型贡献时，才能进入最小 Chat；
全体打平使用 `REWORK`。完整 hidden、跨工程与统计复验仍在用户 `CONTINUE` 后执行。

方向体验版不是验收版，不得声称完整、稳定或可生产使用，但始终必须遵守数据/源码授权、只读和写入权限、Secret 隔离、外部调用
披露、失败不伪造成功等不可推迟的安全边界。首次体验前不得执行全量回归；安全运行或判断核心方向所需的验证只能收窄为聚焦测试。
完整 Schema、全面能力资格、性能优化或完备证明材料同样不得放在首次体验之前。

从 `ITER-010-PDR-009` 起，方向风险较高的产品开发默认采用固定体验时间盒；活动 Iteration 可在 Manifest 对 exact action 顺序和时限作更
严格、可机械验证的覆盖，历史旧字段不得反向恢复被取代的顺序。计时点是授权后的第一次
产品代码变更，而不是第一次 live 调用：60 分钟内页面必须可启动，180 分钟内必须形成用户可连续操作的持续 Alpha；到 240 分钟仍未
形成时，硬停止功能扩张、hardening、full regression 和无新证据的外部重复调用，密封已有证据并缩围复盘，同时继续本地根因归因和最小
体验纵切收敛。60/180 是交付检查点，不能等完整质量证明才开始计时；240 是失控路径和扩域的停止边界，不能以“再跑一次”绕过，但不是
整个开发目标的终点。180 分钟未交付持续 Alpha 即记 timebox FAIL、立即交付现状并停止新增范围；181—239 分钟只允许定位根因和收敛已有
纵切。期间形成的迟到 Alpha 仍须立即交用户，但只能作为 `FAIL / REWORK` 证据，不能追认为按时成功或解锁后续夯实。当前 Iteration 对
Alpha 后方向证据和判向另有明确时限时，同样不得把它们拖成新的无界内循环。

若该 policy 在一次失败 Result 密封后才被采用，Manifest 必须用 `historical_pre_policy_result_refs` 精确列出这些历史 Result，并声明它们
不能满足新的体验 Gate。门禁继续验证其 failed-preserved 身份、所属 Slice、不可变摘要和后继非编码 REWORK 决定，但不得反向要求历史
Result 补造当时尚不存在的体验或 Provider 字段。新授权后的任何 Result 均须完整遵守当前 policy，不能加入该历史列表绕过验证。

首次体验前只允许最小启动、安全边界、失败真实性、一次 current Provider 资格确认和最多一个 Provider 前本地/Mock Access smoke。全量回归、完整能力矩阵、hidden、
跨工程和统计对照都必须后置。Access 与 Quality 是两道不同的 Gate：Access 只证明真实产品页面和请求通路已经交给用户操作；Provider
未配置、未资格或失败必须如实显示，但不能阻塞页面交付。Provider 资格只约束需要外部模型的方向体验，Access 不能证明答案正确。只有
用户可见答案质量 Case PASS 且用户决定 `CONTINUE` 后，才可进入 hardening。

live attempt 使用轻量计数：同一 sealed product version 中，每个触发任一外部 dispatch 的有界用户交互单元计一次 attempt，不按单元内部模型/
角色调用数放大；对 Chat，这个单元是 Turn，一段 Conversation 中多个已 dispatch Turn 分别计数；纯本地诊断不计。相同 failure signature
最多重试一次；连续两次 live attempt 没有用户可见增量，立即停止该签名的外部重跑并回到本地根因诊断，但保持最小体验目标和当前 Slice
开发进行中。此停止规则发生在问题之间；已经开始的问题仍须执行完整调查、答案、Citation 与独立审核链，调用或成本不得成为质量裁剪
理由。

live failure 必须先沿 `Source truth → knowledge construction/admission → cognition projection/query → conversation/task understanding → Agent work state/plan → tool observation/evidence → answer synthesis → independent review → Web`
定位最早偏差，并分别记录 first divergence、没有阻断错误的 downstream guard failure 和 display failure。一题可以有多个故障，但下一项
产品修改只能归属最早有证据的 Owner 层；不得用下游 Prompt、搜索排序或 Reviewer 文案补偿上游知识/投影缺口。没有逐层 evidence table、
可证伪 root-cause hypothesis 和反事实验证，不得修改 Prompt、Schema、Tool policy 或 Contract。修复顺序固定为：本地最小复现，至少两个未参与
修复的相邻案例通过，再执行一个有界 live canary 单元；Chat 目标必须把该单元冻结为最小多轮 Conversation，不得用孤立一题代替。不能直接用下一次昂贵 live run 猜测修复。相同 failure signature 经过一次通用修复仍复现，
必须停止堆规则并评审架构职责。首次体验前只运行 targeted impact、startup 和 safety 测试；full regression 在 Alpha `CONTINUE` 后的
hardening 和正式验收前各运行，不得用它延迟首个体验。

Provider route 默认按 `preferred route → fallback route` 角色顺序运行，并通过 standing external authority 预授权 ordered route、两个角色的
execution profile、disclosure scope 与适用的 admission policy；范围内的新 session/Turn 不要求再次取得用户授权。
preferred-route attempt 因已冻结的 Provider 或模型能力原因终态结束且未形成 authorized answer 时，可对同一 logical interaction unit 透明启动最多一个
fallback-route attempt，用户无需
重提或新建 session。两个 attempt 必须独立密封；fallback 从 immutable original interaction input 与 exact World Model cognition 重跑完整链，禁止
复用前次中间产物；对 Chat，fallback 输入必须是 immutable original Turn Request、与该 Turn 相关的 exact Application-sealed Conversation Context 和 exact World Model Cognition，不得退化为只重放孤立问句；迟到 primary 结果只允许隔离审计，不得覆盖已密封结果；同 Provider retry 为 0。Provider 输出/schema 或模型审核失败
必须记录为能力失败，不能伪称网络不可用；Application、Source 或 Security 失败不得通过 fallback 掩盖。所有 planned fallback-route 调用都必须
执行该 execution profile 引用的 admission plugin，不以 batch、fallback、smoke、canary 或 live 名称区分。run-level receipt 和每个新 request 的
准入条件/一次性 exact override 重验必须早于 Provider socket/connected descriptor、TLS、credential 和 HTTP；缺失或越界时相关计数为 0。
完整最坏质量链必须能在 admission plugin 准入的时间与资源边界内完成；准入失效后不创建新 request。已发出 request 继续按零重试和 outcome-unknown 规则密封，
但无法完成独立审核时必须失败关闭，不能交付降质答案。等待准入时 preferred-route-only 与本地开发继续。具体 Provider/model 名称只属于
execution profile 配置和执行收据，不得写入通用 action/Case 语义。

可体验 Alpha 必须记录 `CONTINUE`、`REWORK`、`REDIRECT` 或 `REJECT`；只有 `CONTINUE` 才能进入工程夯实。任一阻断项失败默认只阻止
PASS 声明、晋级和 hardening：保留失败证据，并在当前授权仍覆盖修复时保持 Slice active，在同一 Slice 做通用修复和重新体验。只有
修复改变已授权 scope/System Owner、用户明确暂停，或本地授权本身被撤销/失效时才进入 `paused / coding_input=false`；需要新权限时按
本政策直接申请。
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
模型职责和安全边界没有改变，就在当前 Slice 做最小通用修复，复测原问题，并增加相邻表达或不同类型问题防止特判。失败尝试保留为
`failed-preserved`，但 `REWORK` 本身不撤销仍有效的 Slice coding input，也不从 `project/current.md` 移除活动 Slice。只有 scope/Owner
变化、明确用户暂停或授权失效时才进入 `paused / coding_input=false`；实现者必须直接申请恢复所需的最小精确权限。新授权到达后恢复同一
Slice，不新建 Iteration；只有 standing authority 失效或发生 scope delta 才产生新的人类授权收据，范围内每次运行只产生系统派生的精确
execution/admission receipt。历史失败 Result 通过 Manifest 的 `rework_result_refs` 保留。

Proposal 必须预先冻结无进展的可测定义和正整数尝试上限。达到上限只触发一次架构转向评审，不自动证明应当转向；实际
`REDIRECT` 仍必须绑定用户明确转向、核心架构证伪或该上限已达到中的一项。模型调用次数不得充当无进展定义，也不得成为降低调查、
回答或独立审核质量的理由。

输入持有、技术质量裁决和产品方向决定必须分离。用户可以持有现场问题并决定继续、改向、停止或最终接受，但正确性、完整性、引用支持、
边界判断和是否存在特判必须先由独立评测方裁决，不能把代码事实审核转嫁给用户，也不能用用户喜欢某种表达替代技术质量 PASS。
current Codex 对照是强外部基线参赛者，不是事实来源或评测方；它必须在 fresh 独立任务中先生成并密封答案，系统看不到该答案，评测方
也不参与任一候选答案生成。产品价值与世界模型因果贡献必须在同一个四路 Gate 中判读：直接相关证据到相同 generator、同一主 Agent
仅源码、同一主 Agent 世界模型认知+源码、current Codex。第 2/3 路除认知开关外保持相同，事实由独立 exact-source ledger 提供；不得
拆成 Web 后对照和另一套后置消融，也不得把任何一条基线当成 Oracle 或裁判。

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
- 同一 Slice 的修复记录、standing external authority、系统派生 exact receipt、scope-delta 重新授权边界，以及预提交的无进展定义和尝试上限。

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
