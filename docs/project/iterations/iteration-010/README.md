---
id: ITER-010-INDEX
kind: iteration-index
status: authorized
authority: current-development
owners: [product, project, architecture, engineering, quality]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ROADMAP-M-002, ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, ITER-010-PROPOSAL, ITER-010-READINESS, ITER-010-VERIFICATION, ITER-010-SLICE-001, ITER-010-SLICE-002, ITER-010-SLICE-003, FINDING-010-028, FINDING-010-091, FINDING-010-092, FINDING-010-093, FINDING-010-094, FINDING-010-095, FINDING-010-096, FINDING-010-097, FINDING-010-098, FINDING-010-099, FINDING-010-100, FINDING-010-101, ITER-010-RESULT-SLICE-001-STOP-REDIRECT, ITER-010-RESULT-V-ALPHA-ACCESS-001, ITER-010-DECISIONS, ITER-010-PDR-001, ITER-010-PDR-002, ITER-010-PDR-003, ITER-010-PDR-004, SYS-ADR-018, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: []
tests: []
iteration: ITER-010
coding_input: true
---

# ITER-010：软件世界模型与主工程 Agent 驱动的多轮工程 Chat

## 先看懂这轮要做什么

系统现在冻结两个同等必要、职责不同的核心：软件世界模型持续提供当前精确版本上稳定、可验证、可更新的软件认知；主工程 Agent 在
真正多轮对话中持续理解用户目标、指代与纠正，维护假设和计划，查询世界模型并按需提出受控源码调查，根据观察重规划和组织答案。
平台负责只读执行、证据身份、权限、熔断和审计；独立 Reviewer 在每轮交付前检查事实、完整性、引用、未知边界和对话目标履约。

| 文档术语 | 中文含义与职责 |
|---|---|
| World Model Cognition Context | 世界模型针对本题投影出的系统认知，不是手册或关键词缓存 |
| Source Broker / Retrieval Worker | 来源代理 / 隔离读取器；前者校验并编译只读操作，后者执行，模型本身没有源码权限 |
| Evidence Ledger | 本题只追加的调查记录，保存每次提议、决定、读取结果、失败和未知 |
| Question Evidence Package | 调查后密封的本题证据包；可支持/引用条目与必须保留但不能支持肯定结论的边界/审计条目严格分区 |
| Legacy Verification Investigation | 旧 `@3` 兼容协议中的独立补证角色；current 目标由主工程 Agent 根据 Reviewer Finding 重写或继续受控调查 |
| Conversation / Turn | 一个对话及其按顺序密封的用户/助手轮次；每轮有自己的 Request、证据包、Answer、Review 与 Citation |
| Conversation Context Revision | 当前目标、指代、用户约束/纠正、未解决问题和 prior Delivery reference 的密封工作状态；不是软件事实 |
| Main Engineering Agent | 持续拥有目标、假设、计划、工具选择、观察解释、重规划、完成判断和答案综合的主工程 Agent |

恢复顺序仍是“先形成可体验版本，再在同一版本上修复，再夯实”，但可体验版本不能再由连续单轮 Q&A 冒充。首个目标是浏览器完整消息
历史、“新对话”、追问/指代/纠正/总结、逐轮证据与 Review。Provider 前最多只做一个本地/Mock Access smoke；首次 live canary 本身就是
一段冻结的五轮 Conversation 和新对话隔离负测，不存在先跑孤立首题再验证 Chat 的步骤。五轮通过后立即形成三臂方向信号，
再由用户决定是否进入持久恢复、复杂冲突/去重、完整异常矩阵、第二工程和其他夸实工作。

## Status and authorization

`AUTHORIZED / REWORK / SLICE-001 ACTIVE / CODING INPUT TRUE / SLICE-002 AND SLICE-003 PROPOSED BUT NOT AUTHORIZED / NO ACCEPTANCE`。

[PDR-004](decisions/PDR-004-agent-first-conversational-recovery.md) 已依据 Agent 方向收据 `2f8b92d8…`、Chat 目标收据 `f164d65a…` 和本次
文档同步收据 `d8239ea7…` 曾暂停旧编码权威。用户随后以
`codex-user-message:sha256:f76ba3e864f6612b3dcc14c83392ec54db686fdb5653e408fa300785b97ceef5`（`2026-08-25T05:06:07Z`）
接受刷新后的 Readiness 并授权 Slice1 产品/System 编码与本地确定性验证。新的 Chat Access 已形成
`CHAT_ACCESS_LOCAL_CANDIDATE`。用户随后以
`codex-user-message:sha256:7256a886d863712b27a7012c1c791eaca91c98f7183f732b463ce98543a469b6` 只授权 exact
`cf2883bef861e0345afc36415d4216f943d31cf4` 的本机 listener/browser Case；`ITER-010-RESULT-V-ALPHA-ACCESS-001 / FINDING-010-096`
已把 `V-ALPHA-ACCESS-001` 更新为 `PASS / access-only`。`FINDING-010-097` 随后形成
`AGENT_EXECUTOR_LOCAL_CANDIDATE`：Application-owned loop、跨 Turn Work State、Observation/Package、fresh Review Finding 与 exact
Delivery binding 已通过 48/48 确定性 Gate。`FINDING-010-098/099` 又形成 `EVIDENCE_TOOLS_LOCAL_CANDIDATE /
MODEL_BOUNDARY_LOCAL_CANDIDATE`：World Model/Source/Ledger adapter、单 Provider Agent/Reviewer closed role contract、逐 dispatch
Disclosure/Gateway receipt 和 non-dispatching candidate preflight 已闭合。`FINDING-010-100` 进一步以 trusted failure classification、隔离的
Ark→DeepSeek full-chain attempts、committed Work State 和 logical Turn 分账形成 `PROVIDER_ROUTE_COMPOSITION_LOCAL_CANDIDATE`，最新相关
组合为 76/76。`FINDING-010-101` 又用生产 Ark/DeepSeek Adapter、credential-lazy transport、Model Gateway 与 Session Disclosure 形成
`PROVIDER_RUNTIME_COMPOSITION_LOCAL_CANDIDATE`，最新相关组合 79/79。current sealed Conformance、Source/World Model runtime、固定命令
Session 接线与五轮 Chat 仍为 `NOT_LOADED / NOT_QUALIFIED / NOT_LIVE`；该进展没有外部 Provider/model、mall Source/resources、listener/browser 或 Production 执行，
也不授权 hidden 或 Slice2/3。

Slice1 已完成 4 条公开方向题和用户现场题。真实 Web、受控调查、Broker/Worker、Ledger/Package、Citation、独立 Review 与失败关闭技术链
能够运行；现场登录答案却仍由 Controller/Service/Filter 方法序列主导，并省略登录日志副作用，Reviewer 无 Finding 批准。

旧记录曾把用户消息 `d746968f…` 解释为 `REDIRECT`。最新接受的 [PDR-001](decisions/PDR-001-resume-as-rework.md) 明确：该消息要求
实现者自行复核并修复已知错误，并没有明确拒绝产品方向；历史 Result 的技术事实与具体 FAIL 保留，但整轮终止结论修订为 `REWORK`。
`FINDING-010-028` 定位的答案和审核根因回到本轮处理。用户随后以
`codex-user-message:sha256:32b298dedd814a93d8dc0a086776090342f14856f032283fddb453061c1efeb5`（`2026-08-24T02:55:16Z`）
明确要求“继续开发”，因此同一个 `ITER-010-SLICE-001` 当时恢复为编码输入。PDR-004 现已暂停这项旧权威；历史失败 Result 和 PDR-001
均保留。该收据不授权 `SLICE-002/003`、hidden 或 Production Activation，也不自动复用任何已消费的 live grant。

用户消息 `codex-user-message:sha256:d3b60bdaa52d96ced3c653a8dcd54fabff41beb7f23f0bf691e6983ebb9437bc` 于
`2026-08-21T08:23:25Z` 要求按最新讨论重新制定计划并更新文档。它确认：World Model 仍是真正的软件外部认知；提问期由 LLM 主导
自适应调查，Broker/Worker 控制实际读取，调查后 seal，Reviewer 可独立要求补证。

该收据曾只授权重制计划和文档。用户随后以
`codex-user-message:sha256:585f02c4edcf25502b40f880c17a7bdf7f1af71044cd8d1bbe97b055a735ee9e`（`2026-08-21T09:18:34Z`）
接受 Readiness，并只授权 `ITER-010-SLICE-001` 产品代码开发与本地确定性验证。用户随后以
`codex-user-message:sha256:815d868ca3df4795276934acbc21d12584fcfd4cb49b31c67696c72d3a5a6b74` 授权本次 mall / DeepSeek
验证的 exact endpoint、问题、Maven World Model 投影、角色 Ledger 和所选 Java/README/POM/Test evidence；调用数不限、retry 0，
`src/main/resources` 与配置凭据排除，Production Activation 不执行。该 root authorization 只允许每个 fresh candidate/session 继续
收窄并密封 exact dispatch，不能跨产品冻结复用旧 dispatch grant。`SLICE-002/003`、hidden disclosure 和 Production Activation 仍未授权。
此前 `1b327024… + 5cdb7000…` 仍只绑定被取代的设计。

clean candidate `274e5ea…` 的 run-020 current DeepSeek Conformance 2/2 PASS；同一持续 Alpha 中，原登录题独立可接受，构建/安全接入题
因 mandatory path 只能经内容 SEARCH 重新发现而触发 no-progress，401/403 题完整读取决定性实现后又因一个 `SUPPORTED` FINISH item
混入 `LIMITATION` observation 被本地 validator 正确失败关闭。`FINDING-010-057/058` 因而增加 Request + attempt + Profile-bound opaque
direct locator，并把 provider-facing FINISH 拆成结构互斥的 supported/non-supported arrays；旧 run-020 只作失败诊断证据，新 clean/fresh
三题与超限输入仍须重跑后才能更新体验 Gate。`FINDING-010-059` 已以 Engineering QA 101/101、current docs/compile/diff 和允许 AF_UNIX
的 full 1167/1162 exact historical hold 闭合确定性 Gate；它不替代 fresh Provider/browser 证据。

随后 clean `dfba244…` / run-021 已让原登录题和 401/403 题各以 8 次 dispatch 获得独立可接受的 `APPROVED`，也证明 66,000-byte
输入在 Provider 前拒绝且调用根不变。Q2 虽已用 direct locator 连续闭合 4 个 mandatory paths，却把 3 个 UNKNOWN 同时复制进
supported/non-supported arrays，并在仍有 8 个含当前动作 call 时结束；本地 validator 正确失败关闭。`FINDING-010-060` 因而要求
partition disjoint + checklist exact-once，并明确 mandatory minimum 不是 investigation maximum；`FINDING-010-061` 已以 Engineering QA
101/101、docs/compile/diff 与 full 1167/1162 historical hold 闭合 deterministic Gate。run-021 仍不能取得三题体验 Gate。

随后 clean `be15a0a…` / run-022 的 current Conformance 2/2 PASS；首题 Understanding 正常，第一个 Investigation 也选择了合法 direct
locator 与 current basis，却返回空 `checklist_item_ids`。Domain 以 structured-output violation 正确关闭，暴露 Provider Schema 允许
checklist/basis 数组为空或重复，而 Domain 一直要求 non-empty + unique。会话在 2 次 dispatch 后停止，没有提交 Q2/Q3 或超限输入，不能
用 run-021 补齐。`FINDING-010-062` 将两个 binding arrays 的 Provider Schema、Prompt 与 Domain 对齐；`FINDING-010-063` 已以
Engineering QA 102/102、docs/compile/diff 与允许 AF_UNIX 的 full 1168/1163 exact historical hold 闭合 deterministic Gate。新
clean/fresh live 仍待执行。

随后 clean `656b549…` / run-023 完成 fresh Conformance 2/2、同会话三题 8/8/7 dispatch 与 66,000-byte Provider 前拒绝；retry/switch
0、private files 和 Production `NOT_EXECUTED` 成立。Q1/Q2 独立可接受，Q3 却仅凭上游 empty authentication context 与 deny decision
推导最终 401/403，并把同一局部条件分配到互斥外部结果；模型 Reviewer 仍误判 `claim_consistency=PASS`。`FINDING-010-064` 现要求
externally visible status/error/body 必须由下游 response/exception mapper full-content evidence 支持，custom-handler wiring 不证明输出，
transport status 与 application/response-body code 分开；Prompt 升为 `@26`。run-023 不能取得三题质量 Gate，新 clean/fresh live 待执行。

`FINDING-010-065` 已以三模块 65/65、Engineering QA 102/102、docs 459/459、compile/diff PASS 与允许 AF_UNIX 的 full 1168/1163
exact historical hold 闭合 deterministic Gate；raw 唯一 4 FAIL + 1 ERROR 仍为冻结 V-009/Codex hold，没有 ITER-010 新失败。新的
clean candidate/fresh live 仍是 blocking evidence。

run-024—run-026 继续以通用机制收敛 Provider 跨字段重复状态、Review remediation 派生、Verification single-gap delta/
stable merge、predecessor full-read consumption、Broker rejection 投影、current-gap boundary 绑定与 terminal verified-gap 复审。
run-026 的 Q1 独立可接受，Q2/Q3 仍作为不相关 predecessor boundary 与重复 terminal-gap 的失败证据保留。
`FINDING-010-073/074` 现已区分普通 `GAP` 与 typed `VERIFICATION_GAP`，并以 Engineering QA 113/113、current docs
468/468 及允许 AF_UNIX 的 full 1179/1174 exact historical hold 闭合 deterministic Gate。下一阻断项是新 clean candidate
的 fresh Conformance、同一持续 Browser 三题、66,000-byte Provider 前负测与独立复核；Production 仍不执行。

随后 clean `b709fad…` / run-027 完成 fresh Conformance 2/2、同一持续 Browser 三题和 Provider 前超限拒绝。Q1 独立复核 PASS；
Q2/Q3 却把配置 placeholder 扩张为具体 header、caller/import 扩张为未挂载 DTO fields/handler output，并把上游局部决定扩张为下游
401/403，唯一 Reviewer 复述这些扩张后错误 `APPROVED`。`FINDING-010-075` 将 comprehensive Review 降为 provisional，随后强制 fresh
evidence-boundary challenge，并由 Gateway 校验 focus 顺序、只以 challenge 授权。focused 78/78、Engineering QA 115/115 已通过；
扩展 deterministic Gate 与新 clean/fresh live 仍是当前阻断项，run-027 永久保留 1 PASS + 2 FAIL，Production 仍不执行。

`FINDING-010-076` 已以 docs 组合 148/148、历史 oracle 组合 80/80、current docs/compile/diff 与允许 AF_UNIX 的 full
1181/1176 exact historical hold 闭合上述 deterministic Gate；raw 唯一 4 FAIL + 1 ERROR 仍精确属于冻结 V-009/Codex hold，没有
ITER-010 新失败。下一步只能从新 clean candidate 执行 fresh Conformance、持续 Browser 三题、Provider 前负测与独立复核；
run-027 不追认，Production 仍不执行。

clean `f832ceb…` / run-028 随后完成 fresh Conformance 2/2、同一 Browser 三题与 66,000-byte Provider 前负测；26 次 dispatch 的
retry/switch 均为 0。Q1/Q3 独立 PASS，Q2 虽保留所有具体配置值为未知，却仍把 Controller 的 getter caller use 写成未挂载
`UmsAdminLoginParam`“包含”字段；fresh challenge 收到精确 type lead 后仍复制该断言并错误 `APPROVED`。`FINDING-010-077` 因此要求
Application-owned stable challenge ID、逐项 evidence/Draft scope assessment、exact 集合重算与越界 Finding-on-challenged-Claim 绑定；
run-028 永久保持 2 PASS + 1 FAIL，新的 deterministic 与 clean/fresh live Gate 待闭合，Production 仍不执行。

`FINDING-010-078` 已以 focused 78/78、Engineering QA 115/115、docs 组合 148/148、历史 oracle 组合 80/80、current
docs/compile/diff 与允许 AF_UNIX 的 full 1181/1176 exact historical hold 闭合上述 deterministic Gate；raw 唯一 4 FAIL + 1 ERROR
仍是冻结历史 hold，没有 ITER-010 新失败。下一步只能从新 clean candidate 执行 fresh Conformance、持续 Browser 三题、Provider 前
负测与 raw challenge assessment 独立复核；run-028 不追认，Production 仍不执行。

后续 run-029—run-032 继续闭合 full-entry effect scan、Answer observation preservation、original-question fulfillment、effect omission layer
与 entry → source-reference resolver；`FINDING-010-079`—`FINDING-010-087` 保留每次 live FAIL/PASS 与对应 deterministic Gate，均不互相
拼接追认。

最新完整 Alpha clean `d70a3e6…` / run-033 的 fresh Conformance 2/2 PASS，但三题仍为 Q1 FAIL、Q2 FAIL、Q3 OUTCOME_UNKNOWN；66,000-byte
Provider-before-call negative PASS，总 dispatch 31、retry/switch 0、Production `NOT_EXECUTED`。`FINDING-010-088` 定位 Q1 的系统根因：
single-gap Verification replacement 可以删除 supported predecessor target observations。当前修复要求 exact/relative-order monotonic
preservation，并把 `APPLICATION_PACKAGE` effect gap 收窄为 caller full content 已可见 interaction；`FINDING-010-089` 已闭合
deterministic Gate，新 clean/fresh live 仍是 blocking evidence，项目决定继续为 `REWORK`。

新 clean `fe6b6b6…` / run-034 已在用户表示充值后启动 fresh DeepSeek Conformance，但第一条 exact
`deepseek-v4-pro` request 仍收到 HTTP 402。credential resolution/TLS/HTTP dispatch 为 1/1，token 0、retry/switch 0，
第二条 canary 未发送，没有 Qualification、Alpha、Browser 或 Production。`FINDING-010-090` 将 run-034 永久封存为
FAIL；当前 key 所属账户恢复 Provider 可用性后，只能启动新的 fresh Conformance。项目决定仍为 `REWORK`。

PDR-003 取代了上述“余额恢复后继续 DeepSeek”的历史下一步，但不改写 run-034。它先冻结质量未验收 Web Access、透明 Ark→DeepSeek
route 和有界 canary；PDR-004 又把孤立 live question 收窄为 Provider 前本地/Mock Access smoke，并把首次方向 live canary 明确为一个
五轮 Conversation 与新对话泄漏负测。Provider 对用户透明，fallback 是同一 logical Turn 下重跑完整链的新 attempt，不共享 Ark 中间态，
用户无需重提或新建 Conversation。该 route 与 Chat 均尚未实现/资格化；首次体验前停止无关 Prompt/Schema/Contract 扩张、外部批量调用和 full regression。

本轮产品基线固定为 commit `1fb997bab6444523f82ebf1a514a1abbf79656c7`、tree
`1369ce932c778c57a118123e8257ede476229d73`；授权审核的 planning commit/tree 为
`01dcfe2233625dfaa021495850fb18ae1323063b` / `8e364ae854bfaa48580ab080a3e0d9c9c43c3d6f`。ITER-009 的体验代码保留为技术资产，但其代码走读式产品方向已由
`ITER-009-RESULT-SLICE-001-STOP-REDIRECT` 否决，不能被写成 Acceptance。

## Required inputs

- [Proposal](proposal.md)
- [Manifest](manifest.yaml)
- [Verification Matrix](verification-matrix.md)
- [Readiness Review](readiness-review.md)
- [Development Design](development-design/README.md)
- [Findings](findings/README.md)
- [Results](results/README.md)
- [Decisions](decisions/README.md)

旧计划在 Slice1 的方向 Gate 失败：技术链能够运行，但答案/审核质量失败，随后又证明重流程、薄 Agent 和无状态连续问答不能实现目标
Chat。Slice2/3、三臂、hidden、正式验收和 Production 均未执行。PDR-004 的 System Owner、Readiness 和重新授权现已完成；下一步不是
继续旧三题 live，而是先交五轮 Chat Alpha 与新对话隔离，再以 current Codex、same-agent
source-only、same-agent full-cognition 三臂判断方向。任何旧 Result 或本机 PASS 都不授权新架构编码、hidden、Slice2/3 或 Production。
