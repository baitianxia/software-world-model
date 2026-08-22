---
id: ITER-011-PROPOSAL
kind: iteration-proposal
status: proposed
authority: project-proposal
owners: [product, project, architecture, engineering, quality]
depends_on: [SYS-PRODUCT-SUCCESS, ROADMAP-M-002, ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST, ITER-006-RESULT-ACCEPTANCE, ITER-010-RESULT-SLICE-001-STOP-REDIRECT, FINDING-010-027, FINDING-010-028, SYS-ADR-016, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-QUALITY-SECURITY, SYS-OPS-LOCAL-BROWSER]
code: []
tests: []
iteration: ITER-011
coding_input: false
---

# ITER-011 Proposal：答案优先的工程问答快速验证与分阶段夯实

## Trigger and evidence

ITER-010 的真实 Web 证明了 World Model Cognition、结果驱动调查、Broker/Worker 只读执行、append-only Ledger、调查后 Package、Citation、
独立 Review 和页面链路能够运行；也证明扁平 Claim、自由文本抽象层级和不可执行的审核方向规则会让正文继续由类、方法和调用顺序主导，
甚至在遗漏用户可见副作用时被审核批准。该系统性失败由 `ITER-010-RESULT-SLICE-001-STOP-REDIRECT` 与 `FINDING-010-028` 固定，不是
单题措辞问题，也不允许以关键词、类名、题型或工程特判修补。

用户随后以
`codex-user-message:sha256:7711b359a33d13ac1dd4577dd316fd4bf49d04a05aef263cfc88ad9b3ad49af4` 指出开发拆分仍把完整代码夯实放在
可验证内容之前，要求恢复“尽快给出可体验证据，再根据方向夯实”的原则。该消息是 planning-only 过程拆分反馈，不是产品编码授权，
也不是任何已有或未来 Slice 的方向决定。

## Product-goal alignment and cumulative delta

- MVP target：`SYS-PRODUCT-SUCCESS`；继续建设基于真正软件世界模型认知的通用工程问答，不另建源码 Agent 产品。
- Baseline gap：技术链可运行，但答案层级与用户目标不一致，Reviewer 不能机械阻断“有据但像代码走读”的正文。
- Reused assets：保留 ITER-006 accepted cognition/Citation 基线和 ITER-010 的 Investigation、Broker/Worker、Ledger/Package、Gateway、Web 与
  安全资产；不继承 ITER-010 产品方向 Acceptance 或任何 live grant。
- New capability：共享版本化质量 contract/schema、但分别形成的 Application checklist 与 Reviewer 独立 checklist；typed answer hierarchy 让
  结论、用户可见流程/影响、必要实现解释、限制/未知和 Citation 可分别验证。
- Earliest checkpoint：Slice1 只做足以从同一产品 Web 回答 1 条代表题和 1 条现场题的最小改动，立即取得独立用户方向决定。
- Alpha checkpoint：Slice1 `CONTINUE` 后，Slice2 做一轮系统性最小迭代，立即展示 3—5 条跨维度题和至少 1 条现场题；不得先做
  persistence、hidden、三臂或 full regression。Slice2 没有用户 `CONTINUE` 时 Slice3 不得开始。
- Later proof：Slice3 才进行跨工程泛化、复杂补证、持久恢复、conflict/dedup、安全性能、完整回归、early hidden canary 和三臂消融；
  Slice4 执行最终两个 held-out 工程 10 answerable + 2 boundary、现场题和正式验收。
- End capability：普通用户无需认证即可在 loopback Web 获得先回答目标、层级匹配、证据可核对的工程答案或诚实 Limitation。
- Next gap：第二语言、跨仓库、大型工程持续更新和受控非本机部署。
- Stop/redirect：答案继续被实现清单主导；层级 Gate 依赖题目/工程/关键词/符号特判；Citation 不支持结论；Reviewer 漏阻重大遗漏；模型取得
  直接 Source/FS/Shell/network/credential 权限；安全/失败真实性下降；任一阶段用户 `REDIRECT/REJECT`。

## Critical assumptions and falsification plan

| 假设 | 最早证据与反证 | 反证后的动作 |
|---|---|---|
| A1：统一 typed answer hierarchy 与应用层/独立审核共用的质量 Gate 能让答案先响应用户目标、按需解释实现，而不靠题目或工程特判 | Slice1 的代表题、现场题、V-HIERARCHY-001、V-REVIEW-001、V-WEB-001；若正文仍由类/方法/调用顺序主导，或遗漏用户可见影响仍被批准，则反证 | 立即 REDIRECT；停止进入 Alpha，不以 Prompt 文风或字符比例打补丁 |
| A2：同一答案优先协议能在一轮系统性最小迭代后覆盖同一真实工程的多个问题维度，不退化为只对探针题有效 | Slice2 的 3—5 条跨维度题、现场题、V-ALPHA-002、V-XD-002；需新增题型/关键词/符号/类/方法分支或主要维度不成立即反证 | REDIRECT 表示或 Gate；Slice3 不启动 |
| A3：确认方向后的通用实现可在复杂补证、持久恢复、冲突去重、跨工程、性能和安全约束下可靠运行 | Slice3 的 V-RERETRIEVE-003、V-PERSIST-003、V-CONFLICT-003、V-CANARY-003、V-SEC-003、V-PERF-003；越权、错误、漏审、不可恢复或不收敛即反证 | REDIRECT/REJECT；不把工程失败留给最终验收 |
| A4：完整 World Model Cognition 在自身质量合格后，相比 locator-only/empty 同链和成熟源码 Agent 具有预提交的质量或非 locator 调查成本增益 | Slice3 的 V-COMP-EARLY-003 最早判断，Slice4 的 V-COMP-004 最终复验；完整认知质量退步、成本遗漏或增益未达即反证 | REDIRECT/REJECT；不降低质量 Gate，不因调用次数取消独立审核 |

每个 Slice 都形成独立 Result、`V-REFLECT` 和用户决定。Slice1 到期 A1；Slice2 累积到 A2；Slice3 累积到 A3 并提前判断 A4；Slice4
覆盖 A1—A4。资源上限只作为安全熔断，不是质量裁剪目标。

问题集由用户持有，不等于让用户承担技术验收。每次 Probe/Alpha 先由独立评测方判断正确性、完整性、Citation、边界和是否存在特判；
用户只根据已经复核且连同限制一起展示的真实结果，决定产品方向是继续、改向还是停止。最终技术质量与三臂价值同样由独立评测方裁决，
最终是否接受产品仍由用户决定。

## Outcome and users

首要用户是理解或维护陌生工程的开发者。他只提出自然语言问题，不选择内部模式。系统仍使用精确世界模型认知和受控 query-time Source
调查形成密封证据；答案计划先把用户要解决的目标、可见流程/行为/影响和限制组织为层次，再把必要实现细节及 Citation 绑定到对应结论。
Application 对结构与证据关系做机械验收；独立 Reviewer 使用同一冻结质量 contract/schema、但从原问题独立重建 checklist，先比较遗漏，
再检查直接性、层级、完整性、支持和限制，不负责猜测未表达的产品方向。答案层次是条件职责而不是固定模板：直接回答始终存在；流程、
影响、实现解释和限制只在原问题或证据边界实际需要时出现。

## Scope / non-goals

范围是 loopback、无认证、本地 Git exact revision、Java、预构建 World Model、仓库源码/文档/构建配置/测试的受控只读调查和一个
`ENGINEERING_QA` 产品 Web。Slice1/2 只提供明确标注的非验收方向版本；Slice3 工程化；Slice4 验收。

不包括公网、Production Activation、团队权限、多用户隔离、远程仓库写入、任意 shell、第二语言、跨仓库知识和同步知识发布。严格
`WORLD_MODEL` 与显式 `DIRECT_INVESTIGATION` 保留，不能成为默认问答的静默 fallback。

## Adopted system IDs

沿用 `SYS-ADR-016`、Engineering Question Answering、Response Control、Model Gateway、Source Artifact、Security 和 Local Browser Owner。
Readiness 接受前必须确认 typed hierarchy 与共用 Review Gate 已由 owning System 文档表达；若改变跨模块语义，必须先形成 ADR/Contract
更新，不能只写在 Slice 或代码里。

## Development slices and dependencies

1. `SLICE-001`：方向探针。只实现/接通 typed answer hierarchy 和共用质量 Gate 的最小真实纵切，从同一产品 Web 回答 1 条代表题和
   1 条现场题，取得独立 `CONTINUE / REDIRECT / REJECT`。
2. `SLICE-002`：可用 Alpha。只有 Slice1 exact Result=`CONTINUE` 且另行授权后，做一轮系统性最小迭代，立即展示 3—5 条跨维度题和
   至少 1 条现场题；仍不做 persistence、hidden、三臂、完整性能安全矩阵或 full regression。
3. `SLICE-003`：工程化夯实。只有 Slice2 exact Result=`CONTINUE` 且另行授权后，完成跨工程、复杂补证、持久恢复、conflict/dedup、
   security、performance、full regression、early hidden canary 和三臂消融。
4. `SLICE-004`：正式验收。只有 Slice3 exact Result=`CONTINUE` 且另行授权后，冻结最终候选并执行 held-out 10+2、现场题、最终对照、
   安全回归与用户 `ACCEPT / REDIRECT / REJECT`。

任何后段工作不得为了“顺手夯实”前移到 Slice1/2；任何前段 PASS 也不得被写成正式 Acceptance。

## Risks and unknowns

- typed hierarchy 可能变成僵硬模板；它必须表达通用回答职责，而不是固定段落、术语或字数比例。
- Reviewer 与 Application 共用质量 contract/schema，但不能共用检查项结论：Application 使用已接受的问题理解 checklist；Reviewer 必须从
  immutable original question 独立重建 checklist，先比较遗漏，再审核 Draft 与证据，且不共享会话或裁决结果。
- 两轮早期体验会增加 freeze/授权成本，但能在大规模实现前连续检验方向，代价小于错误路线全面夯实。
- Alpha 的同工程跨维度小样本只用于判向，不能替代 Slice3 的第二工程 canary 或 Slice4 held-out 泛化证明。
- ITER-010 的真实输入和 grant 已消费；复用代码/证据资产不等于复用 Provider qualification、运行授权或产品结论。

## Verification and acceptance

Slice1 用 1+1 真实 Web 问题验证答案层次和 Reviewer Gate；Slice2 用 3—5 个跨维度问题加现场题验证系统性 Alpha 方向。两段都要求重大
错误 0、物质结论有 Citation、独立 Review、最小安全边界成立，但都只产生方向决定。

Slice3 执行完整第二工程 held-out-question canary、复杂可靠性、安全性能、full regression 和三臂 early comparison。Slice4 在两个最终
held-out 工程执行 10 answerable + 2 boundary、两条现场题和最终 comparison；answerable 10/10、boundary 2/2、重大错误 0、逐结论不退步、
价值 Gate PASS、Source/role/Secret/loopback 边界全部成立。Production Activation 始终 `NOT_EXECUTED`。

## Authorization decision

**PROPOSED / PLANNING ONLY。** 收据
`codex-user-message:sha256:7711b359a33d13ac1dd4577dd316fd4bf49d04a05aef263cfc88ad9b3ad49af4` 只授权按快速验证原则制定计划；
它不接受 Proposal/Readiness，不授权任何产品代码、credential、Provider/model call、Source disclosure、live Web/browser、hidden 或
Production Activation，也不构成 Slice1/2 的产品方向决定。全部四个 Slice 保持 `proposed / coding_input=false`。
