---
id: ITER-010-PDR-004
kind: project-decision
status: accepted
authority: project-decision
owners: [product, project, architecture, engineering, quality, ai, interface, security]
depends_on: [ITER-010-RESULT-SLICE-001-STOP-REDIRECT, FINDING-010-093, FINDING-010-094, FINDING-010-095, FINDING-010-096, ITER-010-RESULT-V-ALPHA-ACCESS-001, SYS-ADR-018, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: []
tests: []
iteration: ITER-010
decision: REWORK
rework_strategy: PAUSE_OLD_CODING_AND_RECOVER_WITH_AGENT_FIRST_MULTI_TURN_CHAT
decision_ref: codex-user-message:sha256:d8239ea7da3d767caa5d0a091726849d1a644e45d44f631d36f3028787093a90
effective_scope: ITER-010-planning-and-readiness-refresh
coding_input: false
---

# PDR-004：以主工程 Agent 和真正多轮 Chat 恢复 ITER-010

## Context

PDR-003 已纠正“长时间内部加固、反复 live 重跑、没有体验版本”的交付方式，并冻结体验时间盒、根因优先、Ark primary / DeepSeek
transparent fallback 和成本边界。最新体验又暴露两个更上游的问题：当前架构重流程而主 Agent 过薄；持续 Runtime Session 只能连续执行
相互独立的问题，并不理解追问、指代、纠正或总结。

用户分别以 `codex-user-message:sha256:2f8b92d817ae111401eaaad959a5f786dd3a289763d9b258b38f5a12efd66a90` 与
`codex-user-message:sha256:f164d65a815c67b86d427ee8057f41b20d47bbbd0e8febec8ec1e02c28448068` 确认双核心和 Chat 目标，并以
`codex-user-message:sha256:d8239ea7da3d767caa5d0a091726849d1a644e45d44f631d36f3028787093a90` 要求把最新讨论同步到对应文档。
该最后收据只授权文档同步，不授权产品/System 编码、模型调用、源码披露或 live browser。

## Decision

### 1. 产品采用双核心

- 软件世界模型负责构建和维护准确、版本化、可验证、可更新的软件认知，表达实体、关系、行为、约束、状态、来源、Coverage、Conflict
  和 Unknown；它不是聊天记录、手册或检索缓存。
- 主工程 Agent 是解决用户问题的大脑：持续理解对话目标，维护假设、计划、观察与未解决问题，查询世界模型，按需提出受控源码调查，
  根据结果重规划并组织自然答案。
- 平台继续机械拥有版本、权限、Broker/Worker、证据身份、熔断和审计；独立 Reviewer 继续拥有交付前质量挑战。Agent 不直接获得源码、
  filesystem、shell、network、credential、知识写入或自我放行权。

### 2. 默认产品交互必须是真正多轮 Chat

固定 Runtime Session 之下新增 server-owned Conversation、Turn 和 Conversation Context Revision。Context 保存目标、指代、约束、纠正、
未解决问题和 prior Delivery references，但不把上一轮答案提升为事实。每个 Turn 仍独立调查、密封证据、回答、引用和审核；安全复用旧证据
必须在 exact revision/digest 下重新纳入当前 Turn Package。新 Conversation 不继承旧对话工作状态或逐轮证据。

页面必须展示有序消息历史、每轮状态与 Citation，并提供“新对话”。一轮失败只结束该 Turn，不关闭 Conversation 或 Runtime Session。
跨重启长期 Memory、跨工程对话和多用户隔离仍后置；进程内 server-side Conversation state 足以形成首个方向 Alpha。

### 3. Slice1 的首个语义 Gate 是五轮 Chat，而不是三道独立题

Access 仍先于 Quality：页面、历史、“新对话”、Turn 提交和真实失败展示可先形成 `V-ALPHA-ACCESS-001`，但不能取得 Chat/答案 Quality。
Provider 前可以执行最多一次本地或 Mock 单轮 Access smoke，但不得用孤立 live question 作为 Chat canary。首次方向 live canary 本身就是
`FINDING-010-094` 冻结的一个有界五轮 Conversation，并同行执行新对话隔离负测；每个到达 Provider dispatch 的 Turn 分别计一次 live
attempt，且必须独立完成证据、Citation 与 Review。任一重大事实错误、指代错误、未执行用户纠正、旧答案被当证据或跨对话泄漏都使
`V-CHAT-001` 失败。

### 4. 三臂分别证明 Agent 基线和世界模型增益

三臂不阻塞页面交付：用户必须先取得可操作 Chat，并完成上述五轮 canary 与泄漏负测；随后在 Slice1 Alpha 出口立即产出小样本方向信号。
同一 exact revision 与同一多轮脚本冻结三臂：

1. current Codex：实际可用的成熟源码 Agent 强外部基线，不读取本系统答案或世界模型产物；
2. source-only：使用本系统同一主工程 Agent、Provider、权限和审核链，但 Cognition 为规范 empty，只通过受控源码调查；
3. full-cognition：使用同一主工程 Agent 和调查/审核链，同时获得 exact World Model Cognition 与受控源码调查。

三臂答案分别在 fresh 隔离任务中先密封，再盲化给独立评测。current Codex 不是 Oracle 或裁判。full-cognition 必须先通过绝对事实、完整性、
引用、对话连续性和新对话隔离门；再相对 source-only 证明世界模型带来的质量或非 locator 调查成本增益。PDR-002 对 ITER-010 后首个新
产品迭代的“严格超过 current Codex”前瞻门继续有效；ITER-010 当前三臂用于验证新 Agent/Chat 方向，不把成本优势补成答案质量 PASS。

### 5. PDR-003 全部恢复约束继续有效

60/180/240 分钟检查点、Access/Quality 分离、首次体验前 qualification≤1、live smoke≤1、full regression=0、root-cause-first、本地最小
复现加两个未参与修复的相邻案例、同 failure signature 一次修复上限、Ark→DeepSeek 透明独立 attempt、Conformance 精确复用、DeepSeek
非高峰调度偏好以及“成本不降低已开始问题质量”全部继续有效。

PDR-003 的体验前 `smoke≤1` 只约束上述本地/Mock Access 探针，不把五轮 Chat canary 缩减为单题。这里的 live attempt 单位从
“logical question”精确为“一个 sealed version 的一个 Conversation Turn 到达任一外部 dispatch”；同一 Turn
内 Provider fallback 仍属于同一 logical turn 的独立 provider attempt，不把整段 Conversation 重跑。

## Authorization and current state

- 旧 `ITER-010 / SLICE-001` 编码权威立即暂停：Iteration 和 Slice1 均为 `paused / coding_input=false`，`project/current.md` 不再指向 active
  Slice。Slice2/3 继续 proposed、未授权。
- 新 Agent/Chat 架构为 `NOT_IMPLEMENTED / NOT_QUALIFIED / NOT_LIVE`；旧 Session QA、旧 Result 或现有页面不能冒充 Chat PASS。
- 当前只允许同步项目/System/治理文档并完成新的 Readiness。产品编码、确定性测试扩展、Provider/model 调用、动态源码披露和 live browser
  均须在新设计完整、Readiness 复核和用户明确重新授权后开始。
- 历史 Result、Finding、run、资格与失败事实全部保留，不修改、不拼接，也不因本决定追认为新架构证据。

## Revisit condition

项目文档、System Owner、Manifest 与 Verification Gate 一致并通过文档检查后，形成新的 Readiness review。只有用户明确接受该 Readiness
并重新授权 Slice1，才能恢复产品开发。恢复后的第一项产品变化必须直接服务最小 Chat Alpha，不得再次先扩张完整 Agent 平台、长期
Memory、多 Agent、完整异常矩阵或 full regression。

## Revisit condition satisfied

System Owner、Proposal、Manifest、Slice1 与五轮 Verification Gate 已在 planning commit
`b66ff9f058b92cebd78d5644ffef042753567b4d` / tree `30e437eea83e048e3fb59ddd90a8d1b76242d82c` 一致冻结。用户以
`codex-user-message:sha256:f76ba3e864f6612b3dcc14c83392ec54db686fdb5653e408fa300785b97ceef5`（`2026-08-25T05:06:07Z`）
接受刷新 Readiness 并授权 Slice1 产品/System 编码与本地确定性验证，因此暂停条件已解除，`REWORK` 决定不变。该收据不授权
Provider/model、credential、动态源码披露、live browser、hidden、Slice2/3 或 Production Activation；旧 Result 和已消费 grant 继续保留。

## Authorized implementation progress

重新授权后，`FINDING-010-095` 已形成不接 Provider 的 `CHAT_ACCESS_LOCAL_CANDIDATE`：独立固定命令、server-owned
Conversation/Turn/Context、消息历史、“新对话”和失败 Turn 隔离通过本地定向验证。它不改变本 PDR 对主 Agent、逐轮证据/审核、Provider
route 和真实体验的要求。随后用户以仅限 exact `cf2883bef861e0345afc36415d4216f943d31cf4` 本机 Access 的 grant 执行 listener/browser；
`ITER-010-RESULT-V-ALPHA-ACCESS-001 / FINDING-010-096` 证明同会话连续失败、完整历史、新 Conversation 隔离、Provider dispatch 0 与非生产边界，
因此 `V-ALPHA-ACCESS-001` 为 `PASS / access-only`。该 grant 没有授权或执行 Provider/model、源码/resources、五轮 Chat 或 Production，
本 PDR 的 Agent/Quality/Provider 要求保持不变。
