---
id: ITER-010-PDR-014
kind: project-decision
status: accepted
authority: project-decision
owners: [product, project, architecture, engineering, quality, ai]
depends_on: [ITER-010-PDR-012, ITER-010-PDR-013, FINDING-010-256, FINDING-010-257, SYS-ADR-018, PROJECT-GOVERNANCE-PLAN-EXECUTION]
code: []
tests: []
iteration: ITER-010
decision: REWORK
rework_strategy: CAPABILITY_SEPARATED_WORLD_MODEL_AND_AGENT_RECOVERY
decision_ref: local-user-direction-2026-09-01-plan-failure-review
effective_scope: ITER-010-SLICE-001
supersedes: ITER-010-PDR-013
coding_input: false
execution_sequence_owner: ITER-010-EXECUTION-PLAN-CURRENT
operational_sequence_status: historical-compatibility-only
---

# PDR-014：按世界模型、Agent 和产品增益分层恢复 ITER-010

> 本决定保留目标、边界和历史恢复依据，不是当前任务顺序的编码输入。当前唯一执行顺序是
> [`EXECUTION-PLAN-CURRENT.md`](../development-design/EXECUTION-PLAN-CURRENT.md)。本文后面的 Phase A/B/C/D
> 仅是历史决策映射；它们不得被实现 Agent、监督器或门禁解释成当前阶段、晋级条件或固定运行时顺序。

## Decision

PDR-013 的执行路线终止。它正确停止了旧协议扩张，但仍把“建立 Agent-first 候选”作为一个整体任务，没有把知识构建、Agent harness 和
二者集成增益分开，也没有给知识构建分配必须发生的交付。因此它不足以纠正已发生的系统性偏航。这里保留该判断作为决策背景；当前任务的
拆分和顺序不由本节重定义。

ITER-010 不新建迭代、不等待新的治理动作，也不改变产品架构和 standing authority。`SYS-ADR-018` 的两项核心能力保持：软件世界模型负责
精确版本上的持久软件认知，主工程 Agent 负责理解问题、使用认知、调查源码、根据观察重规划和自然回答。当前被替换的是实现路线：旧
Answer/Review/preflight 封闭协议不再是产品候选。当前实现路线由
[`EXECUTION-PLAN-CURRENT.md`](../development-design/EXECUTION-PLAN-CURRENT.md) 的用户价值纵向任务定义；本决定不另行创建阶段或固定运行时顺序。

## 历史分支收敛与阶段复位记录（非当前执行）

`268b4546a893ff346da34d4f4d06057d860e2aa3` 是本次收敛唯一可信产品基线。仓库只保留 `main`、`codex/development` 和
`codex/supervision` 三个活动分支；所有 `codex/iter-*` 分支及两处未提交候选先转为可恢复 `archive/*` 标签，再退出开发与监督目标。
后续迭代沿用统一开发/监督分支，不再为每个失败、运行或计划修订创建长期开发分支。

Phase A 的 source-only Agent 结果、Phase B 的 `REWORK` 和当时用于选择性恢复的诊断依据均保留在历史记录中；它们不推动当前任务，也不产生
新的晋级条件。当前唯一产品任务、最小证据和失败出口由 `EXECUTION-PLAN-CURRENT.md` 定义。归档中的 Reviewer、Provider recovery 和 Phase C/D
材料不得整包回灌；需要恢复某项能力时，必须先在当前任务内形成真实端到端证据。

历史上曾要求开发分支不能自报推进 Phase、监督分支绑定 exact HEAD；这些约束只说明当时的失败背景。静态检查器只能报告风险信号和证据是否
过期，不能把非空字段解释成能力完成。监督 Agent 仍需独立检查任务、代码和真实运行证据，提出纠偏动作，不能以静态报告代替复核。
监督实际是否运行必须有可观察 heartbeat；Codex heartbeat `iter-010` 虽已创建但当前已按用户停止要求暂停，
Manifest 状态恢复为 `SUPERVISION_UNVERIFIED`，在用户重新允许并完成首次运行确认前不得宣称周期监督已经生效。

## 被否决的进度定义

以下结果从本决定起都不再推动产品阶段：Prompt/Schema/Reviewer 版本增加，旧模型边界文件的新增行，正文词法校验增加，定向协议测试数量，
重复运行已知问题，以及没有浏览器或独立能力证据的“内部闭合”。它们可以是局部诊断证据，但不能称为产品进展。

## 采用的 harness 原则

主工程 Agent 使用小型、Provider-neutral 的运行时端口，复用现有 Gateway、授权、只读 Source、Conversation 和 Web 资产。运行时只承担：

1. 保存当前 Conversation 目标、相关历史和紧凑 Work State；
2. 让模型在可见工具目录中选择世界模型或 Source 只读动作；
3. 记录 action/observation trajectory，并让模型依据新观察调整计划；
4. 流式报告进度、隔离单 Turn 失败并返回自然答案；
5. 把答案和真实 Citation 交给一个 fresh、独立、面向原问题的技术 Reviewer；最多一次携带全部意见的整体重写。

Application 只校验权限、工具参数、exact revision、只读、资源、Citation identity、Reviewer identity 和失败真实性。它不按答案词语、标题、
Markdown、句段或封闭 Claim 映射判断技术语义。Reviewer 返回简洁的 verdict 与完整缺陷列表，不再形成多版正文证明协议。

Codex、Claude Code、OpenHands、SWE-agent 等只作为 harness 能力参考或外部基线。产品运行时和计划不依赖具体模型/Provider。直接接入外部
harness 只有在阶段 A 的同一短 spike 内能使用现有模型网关、只读工具和 Web 交付时才采用；否则继续薄运行时，不形成独立研究阶段。

## 历史四阶段连续开发计划（非当前执行顺序）

以下 A/B/C/D 只用于解释本决定当时的恢复思路。它们已被当前的用户价值纵向任务替代；不得从本节生成新的阶段游标、前置门禁或监督动作。

时间上限是**自动简化/换路点**，不是停工点、质量裁剪或重新授权点。超出上限时立即删除非必要工作，继续下一条能形成真实结果的路径。

### A. 可用 Agent 基线：累计不超过 2 个开发小时

- 绕过旧语义协议，以最小 Agent loop 接通现有 Web、Conversation、模型网关和只读 Source search/read；
- 用两个异质问题和一个追问证明目标保持、工具选择、观察后重规划、自然答案和真实 Citation；
- 立即把 source-only 浏览器候选交付为诊断基线，明确它不是产品 MVP；
- 若该候选仍显著弱于成熟源码 Agent，根因归 Agent runtime/工具接口，直接替换 loop 或工具设计，不修改答案协议。

### B. 真正世界模型最小纵切：累计不超过 6 个开发小时

复用现有 formal/structure/Java static semantics 资产，从 exact revision 在提问前构建同一份可跨问题复用的认知。首个纵切至少同时包含：

- 实体与层级：module/package/file/type/method；
- 关系：contain/import/inherit/invoke；
- 行为：入口到主要协作者的可遍历路径，以及源码能直接证明的条件、异常、状态读写或外部调用；
- 认识论边界：每个节点/关系的来源、Coverage、Conflict/Unknown 和 exact revision。

向 Agent 暴露三个通用工具：`search cognition`、`traverse relations`、`retrieve cognition detail`。命名是职责说明，不是冻结 API 名。
用至少五个未参与实现的认知任务独立检查：material 实体/关系是否构建正确、能否在有界结果中检索、Coverage/Unknown 是否真实、同一认知
是否被多个问题复用。此阶段不以最终答案文本评分，也不通过增加回答 Prompt 修复知识缺口。

### C. 世界模型增强的浏览器 Alpha：累计不超过 8 个开发小时

- 把阶段 B 的三类工具加入阶段 A 的同一个 Agent；默认先从世界模型建立系统认知，再按 Gap 读取 Source；
- 在同一页面运行三个异质问题和至少一个语义追问，展示自然答案、可打开 Citation、折叠的 Agent trajectory、世界模型命中与 Source 补证；
- 候选一旦贯通立即交付用户体验，不等待 Codex 比较、full regression、hidden、跨工程或工程化；
- 同时冻结 same-Agent source-only 与 same-Agent World Model + source 两臂。后者必须至少增加一项非 locator 的正确实质结论，或让一个原本
  失败/不完整的问题正确完成，且不得造成物质退步；否则明确判定世界模型构建或查询尚无产品增益。

### D. 质量收敛与 Codex 强基线

- 在同一 frozen candidate 上运行五个异质、至少三个未参与实现的问题和一段多轮 Chat；
- actual current Codex 使用相同 exact revision、问题和输出目标独立回答，双方在完成前互不可见；
- 未参与生成的技术评测方直接读取 exact Source，按正确性、完整性、相关性、Citation 和 Unknown 逐题裁决；任何模型答案都不是 Oracle；
- 只有系统重大错误为 0、逐题不低于 Codex、总体严格更好、Reviewer 无重大漏判且世界模型有非 locator 增益时，才称为 MVP；
- 未通过时按最早偏差责任层定位：Source truth、knowledge construction/admission、cognition retrieval、Agent understanding/plan、tool use、
  synthesis、review 或 Web。这个列表只用于归因，不规定运行时先后。Knowledge 失败改构建/表示/查询；Agent 失败改 loop、memory 或工具；只有
  替换实验确认最早偏差确在模型交互时才允许改精简 Prompt。开发在同一动作继续，不暂停、不重复申请授权。

用户确认 Alpha 和质量方向后，才进入跨工程、hidden、持久恢复、性能、安全矩阵和 full regression。

## 历史机械防偏航规则（非当前执行）

以下规则只记录当时的防偏航设计，不产生当前任务、阶段、监督或重试动作；当前开发规则唯一见 `EXECUTION-PLAN-CURRENT.md`。

第一项开发变更必须实现轻量检查；它只保护方向，不审核答案语义：

1. 以 PDR-014 可信产品基线为起点，旧 `conversational_engineering_model.py` 和对应测试在 MVP 前净行数不得增长，只允许删除、简化或加入
   最薄兼容适配；不得新增 `ENGINEERING_AGENT_*@N` 版本、Answer/Review/preflight 封闭内容协议或正文词法语义校验；
2. 阶段 B 完成声明必须包含知识构建/查询代码和独立 knowledge evidence；阶段 C 必须同时包含 Agent 工具循环、世界模型查询和真实浏览器
   Turn。仅 Docs/Test/Prompt/Schema diff 自动标记 `NO_PRODUCT_PROGRESS`；
3. 每两个开发小时输出一次四项机器可读进度：`knowledge evidence`、`agent behavior evidence`、`browser evidence`、`prompt/schema delta`。
   没有前三项中的新证据时，不停止开发，而是把下一任务自动重置到最早缺失阶段；
4. 任何答案缺陷在改 Prompt/Schema 前必须有分层 trajectory 和最早偏差替换实验。没有该证据的 Prompt/Schema diff 不进入候选；
5. 一个修复必须同时复验原失败和至少两个异质未参与问题。只改善原题时，下一变更必须换责任层或实现策略，不能叠加第二条题面规则；
6. Provider、网络、成本和备用路线不计产品能力进展，也不改变开发顺序。首选路线成功时不运行备用；只有可信不可用结论才按既有透明配置
   回退，调用次数不能降低回答或独立审核质量；
7. 受信 transport receipt 证明 HTTP/model dispatch 为 0、post-dispatch outcome unknown 为 0 时，当前 logical run 诚实结束，但开发任务必须
   自动创建 fresh successor schedule：5 分钟、15 分钟、随后每 30 分钟。每次使用新 run/request identity，same-request retry/replay 保持 0。
   计时期间继续独立本地工作；本地工作穷尽时保持带 `next_retry_at` 的 active 状态，不能 Final、Pause 或等待用户。首选恢复即取消后续调度；
   到达备用允许窗口后仍先尝试首选，只有本次可信不可用才透明回退。post-dispatch outcome unknown 不适用本条且始终禁止重放。

这些规则只阻止错误的候选声明或旧路线增长；普通测试失败、模型失败、答案失败和时间上限不会撤销开发权限或让开发停下。

## Acceptance of this decision

本决定不宣称产品或方向已经通过。它只确认计划审计完成，并在 PDR-012 的既有公开 Source、模型透明 route、预算、loopback、只读和非
Production standing scope 内替换执行路线。`ITER-010-ACTION-USER-DIRECTION-DECISION-001` 和
`V-BROWSER-CHAT-MVP-BUILD-001` 继续作为 Manifest 兼容身份，但其当前语义和顺序只由
[`EXECUTION-PLAN-CURRENT.md`](../development-design/EXECUTION-PLAN-CURRENT.md) 定义。
