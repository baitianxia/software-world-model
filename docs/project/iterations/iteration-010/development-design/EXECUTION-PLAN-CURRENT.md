---
id: ITER-010-EXECUTION-PLAN-CURRENT
kind: development-design
status: current
authority: current-development
owners: [project, engineering, architecture, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-PDR-014, PROJECT-GOVERNANCE-DEVELOPMENT-DESIGN, PROJECT-GOVERNANCE-PLAN-EXECUTION]
code: []
tests: []
iteration: ITER-010
slice: ITER-010-SLICE-001
coding_input: true
as_of: 2026-09-15
---

# ITER-010 当前执行计划

## 1. 这张卡的地位

这是 ITER-010-SLICE-001 的唯一当前执行顺序。它把已接受的架构和 PDR-014 转成可直接执行的开发任务；不改变软件世界模型、主工程
Agent、Source、Evidence、Citation、独立审核和 Web 的系统契约，也不创建新的迭代、授权或门禁。`proposal.md` 和 `readiness-review.md`
中关于 Phase B REWORK、Reviewer 未激活的文字是历史记录；与本卡冲突时以本卡、`current.md`、SLICE-001 和 PDR-014 为准。

目标不是先完成内部协议，而是尽快形成真实可用的浏览器 Chat，再用小样本验证方向，最后才夯实实现。普通失败、模型失败、网络失败和
定向测试失败都留在本开发闭环中，不能把开发任务暂停或变成新的授权请求。

本轮讨论补充并固定以下运行原则，但不改变既有架构契约：

- **软件世界模型不是文字手册或答案库。** 它必须表达指定版本工程的实体、结构、关系、行为、边界、覆盖范围、来源和检索入口，作为 Agent
  的可复用系统认知。只有 locator、导航关系或不完整索引，不能宣称认知闭包。
- **Agent 是自适应的问题解决者。** 它负责理解问题、选择世界模型视图、按证据缺口读取源码、组织回答和处理追问；模型负责推理与表达。
  世界模型提供认知和入口，源码是最终事实依据，回答不能只凭世界模型导航信息生成。
- **世界模型失配必须可降级。** 当认知覆盖不足或检索没有命中时，Agent 必须继续走通用源码搜索；不能把错误的候选投影、固定动作或预算熔断
  当成答案。World Model + source 要优于 source-only 是待验证产品假设，不是当前实现的前提。
- **每次失败先判责任层再改动。** 先区分 knowledge construction、cognition retrieval、Agent planning/tool、synthesis/citation、review、Web
  和 Provider；没有证明最早偏差前，不得改 Prompt、Schema、答案检查或单题逻辑碰答案。

## 2. 代码现状与已完成能力

- 最近产品候选是开发分支 clean HEAD `940566c610ef101b70407179353fc8f744a14643`；来源是公开 mall exact revision
  `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`，只读边界不变。
- 世界模型已有可供 Agent 使用的结构、关系和详情能力；但最近运行表明它仍可能只给出导航候选，不能保证问题所需的完整行为链。最近的通用修复把 cognition detail/traverse 中已登记实体重新连接到已有
  Source candidate，保持 Citation、Source identity 和 provenance，不增加题面或 Provider 特判。
- Agent 已有重复动作/无进展恢复和有限 replan 能力；自 `8e9f1b6` 后又产生大量候选修复，最新提交 `940566c` 撤销了未经证实的引用模态投影。代码能力有增量，但当前还没有稳定的通用 Agent 证据链。
- 开发记录中的 `run-255` 表明原问题加两个异质问题曾完成 C1 轨迹，但当前监督分支没有针对该运行及其后续候选形成新的独立 `ADVANCE` 评估，不能把开发方记录直接当作阶段完成。
- 最新 `run-267-citation-plan-recheck` 仍未通过：q1 因引用超出已交付证据而 `CONTROL_STATE_DENIED`，q3 因审核要求补证后预算耗尽，只有 q4 成功。较早候选上的 C2 成功记录不能直接继承给当前 HEAD。
- 当前监督心跳为 `STALE`，开发任务也不在运行；这属于执行状态缺口，必须先恢复监督绑定和当前 HEAD 评估，不能继续无证据追加修复。

## 3. 只做以下四个开发包（顺序固定）

### C0 — 恢复执行与绑定监督（无产品代码）

恢复原开发任务，明确它使用本卡，绑定 `codex/development` 当前 HEAD。开发任务内部创建或恢复一个监督子 Agent；监督子 Agent 不开独立
产品任务、不写产品代码，只读开发工作树和运行证据，并在同一开发任务内发送纠偏意见。监督绑定 `codex/supervision`、可信基线和当前
HEAD；每次 HEAD/工作树/运行证据变化以及最长 30 分钟写 heartbeat 和 assessment。监督失联时只恢复监督，不停止产品开发。

### C1 — 修复通用 Agent 证据规划闭环（首个代码包）

以一个真实失败轨迹为依据，定位 `Reviewer → MORE_EVIDENCE → Agent` 的最早偏差。只允许通用修复：同一预算内选择尚未消费且与当前 Gap
相关的 cognition/Source candidate，阻止重复搜索/读取和无进展循环，保留已有 Evidence/Citation identity；不能扩大预算、重试 Reviewer、
增加答案协议、增加问题/工程/类名分支。用原失败轨迹和两个未参与修复的异质任务做定向验证。

### C1.5 — 准备可体验环境（启动前提，不是产品代码包）

在 C1 的候选提交稳定后，必须使用现有 standing authority、公开 mall exact revision、当前 clean product commit/tree 以及已经生成的 World Model
artifact，准备并校验当前多轮 Chat 入口 `engineering_chat_alpha_cli` 所需的
`SWM-ENGINEERING-CHAT-ARTIFACT-SESSION-CONFIG@4`（若当前 loader 明确要求已记录的兼容扩展，则按同一契约使用 `@5`）。禁止改用
历史单路兼容入口 `engineering_qa_alpha_cli` 或 `SWM-ENGINEERING-QA-ALPHA-SESSION-CONFIG@1`，因为它不能证明当前双路 Provider、World Model
和 Chat 目标。配置必须通过当前 Chat launcher 的字段、绝对路径、版本绑定、0600 权限、唯一键、双 Provider route、互异且尚不存在的数据库/
receipt 输出路径校验；不得写入 Secret value，不新增 Provider、模型、预算、授权或外部接收方。每次产品或当前文档提交后都重新读取 clean HEAD/tree
绑定配置，不能复制旧 commit/tree。缺少配置或 artifact 只能在本地补齐生成/校验步骤，不能当成“等待授权”的产品阻塞，也不能以无配置为理由
结束本开发任务。此包完成的唯一可观察结果是 Chat launcher 能在监听前完成配置校验；它不等于 Alpha，也不允许开发任务在此返回“计划完成”。

### C2 — 打通真实多轮浏览器交互（第二个代码包）

使用上述 artifact-backed Chat launcher，沿用同一个 Agent、Conversation 和 Web，完成一组固定但不写入产品逻辑的体验脚本：q1 与 q2 在同一 Conversation，q3 为上下文澄清并新建
Turn，q4、q5 为新问题；不得产生重复 ordinal、额外隐式 Conversation 或重连造成的伪 Turn。每个 Turn 仍须有自然答案、真实 Citation、
fresh 独立审核和可观察的失败关闭。

### C3 — 立即交付 Alpha，再验证产品增益（第三个代码包）

一旦 C1/C2 形成可重复启动的完整主链，立即交付 loopback 地址、启动方式、exact revision 和已知限制；不等待 Codex 比较、全量回归、
hidden、跨工程或性能工作。随后在同一 candidate 上运行三个异质问题和一个语义追问，保存同一 Agent 的 source-only 与
World Model + source 两臂。World Model 只有在至少增加一个正确的非 locator 结论，或修复一个 source-only 的真实遗漏且无物质退步时，才
计为产品增益。

### C4 — 方向通过后才夯实

只有用户确认 Alpha 方向继续，且 C3 的异质体验显示世界模型确有增益，才执行五个异质问题、多轮 Chat、current Codex 强基线、独立
exact-source 评测、完整契约、全量回归、跨工程、性能和发布准备。Codex 是独立强基线，不是 Oracle 或裁判。方向不成立时按最早责任层
回到 Source truth → cognition → Agent/tool → synthesis → review → Web，不能靠添加单题规则碰答案。

## 4. 完成和继续规则

- **可体验出口：** C2 后真实浏览器能持续提问、追问、纠正和新建对话；主链中的 cognition、Source、Answer、Citation、fresh Review 均有
  可观察证据。达到即交付，交付不是暂停点。
- **单次开发任务边界：** 一个开发 turn 不以单个提交、定向测试或配置校验结束。开发任务必须沿 C1 → C1.5 → C2 → C3 连续推进；只有已经
  交付 loopback 体验或确认了无法绕过的真实安全/范围阻塞，才可以汇报本轮结束。普通测试失败、缺少本地启动前提和实现错误都必须在当前任务内
  修复或补齐，不能把“已完成一个局部 commit”描述为计划完成。
- **MVP 出口：** C4 在用户确认 Alpha 方向继续后，完成五个异质问题、多轮 Chat、独立审核和 Codex 比较，达到既定质量且 World Model 有
  非 locator 增益；C3 Alpha 本身不得使用 “MVP” 名称。
- **失败处理：** 只记录原始轨迹，按最早责任层提出可证伪根因；做最小通用修复并复验原问题加两个异质问题。失败不新建 PDR/Result、
  不重复授权、不改变模型透明路由、不停止开发。
- **偏离处理：** 若提交只增加 Prompt/Schema/Reviewer/输出检查、只改善已知题、或没有 knowledge/Agent/Web 新证据，监督立即标记
  `NO_PRODUCT_PROGRESS`，向开发任务发送 `CORRECT` 和唯一下一动作，开发回到最早未完成的 C1/C2/C3；不得继续扩张旧协议。
- **时间处理：** 时间上限只触发删减非必要工作或更换实现；不降低质量、不等待用户、不消费新的授权。受信 pre-dispatch 网络失败按新
  logical run 自动重试；post-dispatch unknown 不重放同一请求。

## 5. 开发任务内监督子 Agent 的工作协议

监督子 Agent 每次检查都必须读取：当前文档、本次 HEAD 与工作树差分、最近代码/测试、最近 Web/Agent trajectory 和上次 assessment。
它输出四个字段：`decision`（`CORRECT`/`CORRECT_WITH_ACTION`/`REWORK`）、`earliest_layer`、`evidence`、`next_action`。

- `CORRECT`：继续当前开发包，并说明下一可观察产品证据。
- `CORRECT_WITH_ACTION`：发现轻微偏离，直接把一个明确可执行动作发给父开发任务；父任务继续，不等待人工确认。
- `REWORK`：确认通用方向偏离或已有能力退步；直接要求父任务停止当前错误路径、保留证据、回到最早责任层。它不是暂停整个开发任务。
- 只有用户明确 STOP/REDIRECT/REJECT、发生 standing authority scope delta，或安全边界不可绕过时，才允许父任务等待；其他情况均继续。

监督不得把测试数量、文档数量、调用收据或“门禁通过”当作产品进展，不得自行修改产品代码，不得创建并行开发分支，不得要求逐次
授权。父开发任务中断后，恢复时必须先重新创建/绑定这个监督子 Agent，再继续 C1/C2/C3。

## 6. 当前下一轮执行包（顺序不可跳过）

当前开发任务继续使用 `codex/development`，监督任务继续使用 `codex/supervision`。以下三个动作属于同一轮连续开发；完成一个局部提交、定向测试或配置
校验都不能结束本轮。

### N0 — 先完成一次最小根因定位（不先改产品代码）

恢复开发任务并重新绑定当前 clean HEAD `940566c` 与监督任务。以最新 q1/q3 失败轨迹为入口，逐步对账世界模型候选、实际源码读取、Agent model view、
  Citation binding、审核结果和预算消耗，明确最早责任层；不得把 Provider 状态、测试数量或最终拒绝码直接当作根因。若仅凭 sealed 证据无法区分
  cognition 覆盖和 Agent 规划，再做一次最小可复现运行，不扩展问题集。N0 必须在同一开发轮内完成并进入 N1，不能停在“已完成分析”。

### N1 — 闭合 C1 的通用 Agent 证据规划

以 N0 确认的最早责任层为准。若责任在世界模型，先补齐通用的行为/关系/覆盖/来源或检索入口；若责任在 Agent，修复通用的证据规划和重规划；
若责任在 Source、Citation 或 Review，只修复其通用契约。原始 `MORE_EVIDENCE` 轨迹和两个未参与修复的异质问题必须全部重放，证明：Agent 能在
世界模型不足时继续通用源码搜索；能在同一预算内选择相关且未消费的证据；不重复搜索、读取或分派；保留 Source/Citation identity；补证后确实进入
审核。不能用增加预算、题面分支、Prompt/Schema、引用重编号或 Reviewer 放宽替代修复。

N1 的完成条件是“运行轨迹证据齐全”，不是 `22/22` 之类的单元测试数量。监督在证据齐全前不得允许进入 C1.5。

### N2 — 用当前 Chat 入口完成 C2 浏览器链

N1 通过后，重新读取 clean HEAD/tree，生成当前 `engineering_chat_alpha_cli` 所需的 artifact-backed Chat 配置（当前 loader 接受的 `@4`/`@5`），
  然后只运行一条固定脚本：

1. q1、q2 使用同一个 Conversation；
2. q3 是基于前文的澄清，必须作为同一 Conversation 的新 Turn，不能新建 Conversation；
3. q4、q5 是封闭范围内的两个新问题，可使用新的 Conversation，但不得产生隐式会话或重复 ordinal。

每个 Turn 都要有自然答案、真实 Citation、独立 fresh review，并在失败时留下可观察的 fail-closed 结果。必须记录 listener 已实际启动、Web
请求已进入生产链、Conversation/Turn 数量与每个 Turn 的结果；仅有 `PREPARED_NOT_STARTED`、本地配置通过或终止收据不算完成。禁止使用旧
`engineering_qa_alpha_cli`、旧单路配置、全量回归、Codex 等待比较或重新申请同范围授权。

### N3 — 首次完整链形成后立即交付 Alpha

N2 形成可重复的完整链后，立即给出 loopback 地址、启动方式、代码提交、已知限制和一组可复现问题；不等待 C4。随后只做三个异质问题和一个语义
追问，用同一 Agent 分别记录 source-only 与 World Model + source 的结果，判断世界模型是否增加非 locator 正确结论或修复真实遗漏。若没有增益，
回到最早的 knowledge/cognition/Agent 层定位，不增加题目特判。

## 7. 本轮监督和停止条件

- 监督在每次 HEAD、工作树、轨迹或收据变化以及最长 30 分钟时检查；必须输出 `decision`、`earliest_layer`、`evidence`、`next_action`。
- 在 N1/N2 的运行证据齐全前，监督只能给 `CORRECT_WITH_ACTION` 或 `REWORK`，不得给 `ADVANCE`、不得宣布 Alpha/MVP。
- 发现偏离时，监督直接向开发任务发送一个唯一纠偏动作，开发继续执行；不暂停、不重复授权、不新建 PDR，不把普通失败升级为阻塞。
- 只有 scope/safety 真正变化、用户明确停止，或无法绕过的外部不可用才允许等待；普通模型、网络、配置和测试失败都在本轮内诊断和修复。
- 本轮明确禁止：继续扩展旧回答协议、针对单题碰答案、用测试数量冒充产品进展、先做 C4 夯实、把监督收据当作用户体验。
