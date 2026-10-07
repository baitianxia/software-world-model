---
id: PROJECT-REFERENCE-ENGINEERING-QA-HISTORY
kind: implementation-reference
status: historical
authority: historical-evidence
owners: [engineering, project]
depends_on: [SYS-ARCH-BASELINE]
code: []
tests: []
coding_input: false
source_path: docs/system/contracts/application/engineering-question-answering.md
as_of: 2026-10-01
---

# engineering qa history

以下内容从 `docs/system/contracts/application/engineering-question-answering.md` 的实现/运行记录原样移出，保留当时措辞；其中“当前”“下一步”“须执行”均为历史语境，不是现行任务、架构决策或能力验收。读取最新工作状态应回到 [current](../current.md)。

## Failure and implementation state

本节的 failure 与 implementation state 只陈述 `@3` 兼容实现。它不能证明 `CONVERSATIONAL_ENGINEERING_AGENT@1` 的 Conversation/
Turn/Agent Work State、统一主 Agent 循环、语义多轮 Chat 或相应资格。

未授权模式或外发、revision/allowlist/Source Profile 漂移、越界文件、evidence class 重标、Source instruction 注入、Ledger 覆盖或缺口、未密封输入、无依据结论、无关 Citation、Package seal 被误当真值、冲突静默消解、任一模型直接取得来源权限、静默模式切换、审核未通过或资源耗尽均使当前 provider attempt 失败关闭。若 Provider 已完成响应但 closed output schema 拒绝其内容，Gateway 必须保留 completed response identity/usage 供审计，产品边界只在 exact Manifest/Provider/model/configuration/receipt 绑定全部成立时传播真实 structured-output failure。该失败与 Reviewer 拒绝都不是 execution-profile availability evidence，也不具备 fallback 资格。若本 `@3` 资格、权威与预算允许格式修复、Answer rewrite、Verification 后重答或 fresh Review，每一步都必须在同一 exact execution profile 内创建新 authorized model call，有新 call identity、Manifest、one-use receipts 和 Usage；不得重发旧 request bytes。同样，dispatch 后 outcome unknown 只有在 exact request digest、isolation receipt 和 qualification 全部重验成立时才传播为 raw outcome unknown，并明确当前 request 关闭、same-request retry 0。Raw unavailable/HTTP/outcome 信号都不直接授予 fallback；真正 identity 不一致仍保持 qualification failure。只有 primary execution profile 登记的受信 availability owner 对 exact profile 和 receipts 密封 `PREFERRED_EXECUTION_PROFILE_UNAVAILABLE` verdict 时，logical question 才可进入一次完全隔离的 fallback attempt；迟到 primary 结果 quarantine 且不能覆盖。具体 DTO、注册操作目录、其余高安全数值上限和 UI 投影由代码与测试定义，但不得改变本契约的认知定义、权威、角色、Ledger/Package 边界和失败语义。

`ITER-010 / SLICE-001` 已提供本地确定性的 Request、持久 Structure Read Bundle → bounded Cognition Adapter、Profile-bound Broker/Worker、request/attempt/profile-bound mandatory-path direct locator、append-only Ledger、双分区 Package、Answer、comprehensive + evidence-boundary challenge Review、一次独立 Verification Investigation、五类 closed role-input/output contract、input/schema-bound output receipt、可信坐标补入、exact run → one-use role disclosure narrowing、Gateway-side role/focus/config/qualification policy、current DeepSeek composition、Session Authority、逐题 server-owned Request/run 与持续 Alpha launcher。返工还实现了受控答案层级、逐 Claim checklist links、默认正文投影、单一 outcome-tagged FINISH dispositions 与 trusted parent-reference derivation、逐 disposition material observations、Claim observation/evidence closure、Answer exact observation coverage table、Reviewer 独立 checklist + observation comparison、typed Finding remediation → derived action/request、配置/未挂载类型/status literal challenge leads、逐 Java full-entry material-effect scan、非 passing assessment 的 exact challenged-Claim binding 和五项方向质量 Gate，其中独立 `claim_consistency` 明确阻断跨 Claim/observation 的互斥结果。确定性 fake transport 不读取 credential、不建立网络且不把 secret/authorization ref 放入 wire；这些证据不构成真实 Provider dispatch、外发执行证据、listener/browser 运行、Capability Qualification、Product Validation、Slice Result、Acceptance 或 Activation 证据。

`FINDING-010-082` 又把 operational Question Understanding、Answer input/output handoff 和 `ORIGINAL_QUESTION_FULFILLMENT_SCAN` 纳入同一通用契约；专用 material-effect / material-requirement disposition 与错误 challenge kind 的组合由 Application 失败关闭。该确定性实现不追认任何旧 live Result，新的 clean/fresh live 仍须独立验证。

`FINDING-010-084` 进一步要求 material-effect omission 的 exact statements 与 `APPLICATION_PACKAGE / DEFAULT_DRAFT` closed layer；
Application 重算 observation membership、challenged entry/evidence class 与 remediation，不通过增加 rewrite fuse 掩盖 observation 缺口。
`FINDING-010-085` 已闭合该协议的 deterministic Gate；run-031 保持 Q1 FAIL、Q2/Q3 NOT-RUN，新的 clean/fresh live Gate 仍须执行。
`FINDING-010-086` 的 run-032 又证明 observation evidence references 属于 source-reference 域；旧实现错误地直接比较 Package entry ID，
导致 challenge projection 与 membership Gate 同时得到伪空集。统一 resolver 与 application-missing-first layer precedence 是本契约的一部分；
run-032 保持 Q1 PASS、Q2 FAIL、Q3 post-dispatch OUTCOME_UNKNOWN、66,000-byte Provider-before-call PASS，不得追认。
`FINDING-010-087` 已闭合 source-reference resolver 与 layer precedence 的 deterministic Gate；新的 clean/fresh live 仍须独立执行。

## ADR-016 Adoption state（历史原文）

曾有 ITER-010 / SLICE-001 本地确定性实现，包含 `ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3`、World Model Cognition Adapter、
Source Profile-bound Broker/Worker、Ledger/Package、Answer、独立 Review、Session Authority、逐题 Request/run 和 Alpha launcher 等。
该实现还包含答案层级、Claim/observation links、FINISH arrays、challenge leads 和方向质量 Gate。以上仅是本地确定性验证，不能证明
真实 Provider、Capability Qualification、Product Validation、Slice Acceptance 或 Activation；旧 prepared launcher 不能标为当前产品。

ADR-018 所定义的新默认架构已有 `ACCESS_BROWSER_PASS / AGENT_EXECUTOR_LOCAL_CANDIDATE / EVIDENCE_TOOLS_LOCAL_CANDIDATE /
MODEL_BOUNDARY_LOCAL_CANDIDATE`，但 ADR-017 fallback、真实 Provider/fixed launcher/Citation wiring 仍为
`NOT_INTEGRATED / NOT_QUALIFIED / NOT_LIVE`。迁移必须复用本合同已经证明的 exact revision、World Model Cognition、
Source Profile、Broker/Worker、Ledger/Package、Citation、Provider disclosure、安全和独立 Review 资产，但不得继续把固定五角色/双 focus
工作流作为新 Agent 的产品合同。
