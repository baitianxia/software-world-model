---
id: PROJECT-CURRENT
kind: project-current
status: current
authority: current-development
owners: [project]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, PROJECT-GOVERNANCE-DEVELOPMENT-DESIGN, ROADMAP-M-002, ITER-001-INDEX, ITER-002-INDEX, ITER-002-RESULT-ACCEPTANCE, ITER-003-INDEX, ITER-003-RESULT-ACCEPTANCE, ITER-004-INDEX, ITER-004-RESULT-ACCEPTANCE, ITER-005-INDEX, ITER-005-RESULT-ACCEPTANCE, ITER-006-INDEX, ITER-006-RESULT-ACCEPTANCE, ITER-007-INDEX, ITER-007-RESULT-SLICE-001-STOP-DECISION, ITER-008-INDEX, ITER-008-RESULT-SLICE-001-STOP-REDIRECT, ITER-009-INDEX, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, ITER-010-INDEX, ITER-010-SLICE-001, ITER-010-RESULT-V-WEB-000-LIVE-RUN-009, ITER-010-RESULT-V-WEB-001-PUBLIC-DIRECTION-QUESTIONS, ITER-010-RESULT-V-ALPHA-ACCESS-001, ITER-010-RESULT-SLICE-001-STOP-REDIRECT, FINDING-010-027, FINDING-010-028, FINDING-010-091, FINDING-010-092, FINDING-010-093, FINDING-010-094, FINDING-010-095, FINDING-010-096, FINDING-010-097, FINDING-010-098, FINDING-010-099, FINDING-010-100, FINDING-010-101, FINDING-010-102, FINDING-010-103, FINDING-010-104, ITER-010-PDR-001, ITER-010-PDR-002, ITER-010-PDR-003, ITER-010-PDR-004, SYS-ADR-017, SYS-ADR-018, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, ITER-011-INDEX]
code: []
tests: []
as_of: 2026-08-25
active_iteration: ITER-010-INDEX
active_slice: ITER-010-SLICE-001
worktree_status: iteration-010-slice-001-ark-transport-session-audit-local-candidate-next-clean-freeze-fresh-conformance-current-artifact-and-live
strategy_relation: dual-core-world-model-cognition-and-conversational-lead-engineering-agent
live_model_path: pdr-004-access-pass-ark-transport-audit-wired-fresh-ark-conformance-required-current-artifact-not-executed-not-qualified-not-live-production-not-activated
---

# 当前工作上下文

## 当前规划与授权

当前活动开发段是 `ITER-010 / ITER-010-SLICE-001`，项目决定仍是 `REWORK`，不是 `REDIRECT`。用户以
`codex-user-message:sha256:f76ba3e864f6612b3dcc14c83392ec54db686fdb5653e408fa300785b97ceef5`（`2026-08-25T05:06:07Z`）
接受 PDR-004 刷新后的 Readiness 并明确授权开发；授权范围是 Slice1 产品/System 代码和本地确定性验证。它不自动授权 credential、
Provider/model call、动态源码披露、live browser、hidden、Slice2/3 或 Production Activation。

用户随后以 `codex-user-message:sha256:7256a886d863712b27a7012c1c791eaca91c98f7183f732b463ce98543a469b6` 精确授权在 clean
`cf2883bef861e0345afc36415d4216f943d31cf4` 启动 `127.0.0.1:8765` 并执行 `V-ALPHA-ACCESS-001` 本机浏览器验证，同时明确禁止
Provider/model、源码/resources 读取或披露和 Production Activation。`ITER-010-RESULT-V-ALPHA-ACCESS-001 / FINDING-010-096` 已记录
`PASS / access-only`：2 Conversation、3 个诚实失败 Turn、Provider dispatch 0、新 Conversation 消息隔离、browser console clean；listener
随后已优雅停止。该一次性 grant 已消费，不扩展任何后续 live 权限。

用户随后以 `codex-user-message:sha256:27ad0abac79f239eb13793fed79f65b8a5dfd7042e1c828b63e7d8545577d88f`
（`2026-08-25T06:20:03Z`）确认前期必须通过快速迭代调整方向，方向错误时不得继续夯实。该收据只修订同一已授权 Slice 的执行拆分，
不重置开发授权，也不新增任何外部执行权限。当前阶段是 `direction-exploration`，hardening 保持锁定。

PDR-004 此前暂停了旧编码权威。用户曾以
`codex-user-message:sha256:32b298dedd814a93d8dc0a086776090342f14856f032283fddb453061c1efeb5`（`2026-08-24T02:55:16Z`）
明确要求继续开发，当时恢复了同一个 Slice 的产品/System 编码与本地确定性验证；该旧权威随后被 PDR-004 暂停，并已由本次
`f76ba3e8…` 授权取代。Slice2/3 proposed 且从未授权。历史 Web、调查、证据、
Citation 和具体失败事实全部保留。旧消息 `d746968f…` 只是要求实现者自行复核并
修复已知错误，并没有明确作出 `REDIRECT`；`3112da25…` 接受该项目决定纠正。最新文档同步收据
`codex-user-message:sha256:d8239ea7da3d767caa5d0a091726849d1a644e45d44f631d36f3028787093a90` 只授权同步最新 Agent/Chat
设计，不授权产品代码、测试扩展、Provider/model、源码披露或 live browser。

未执行的 `ITER-011` 已标记为 superseded。新的首交付目标是真正多轮工程 Chat：固定 loopback/工程/exact revision，页面显示完整消息历史
与“新对话”，主工程 Agent 持续理解目标、指代、纠正、深入和总结；每个 Turn 独立证据、Citation 和 Review，失败 Turn 不关闭
Conversation，新对话不继承旧 Context。首次方向 live canary 本身是一个有界五轮 Conversation，不是孤立问题；随后在同一 Slice Alpha
出口形成 current Codex、same-agent source-only、same-agent full-cognition 三臂方向信号，再由用户决定是否 hardening。

`ITER-010-PDR-002` 已冻结前瞻规则：ITER-010 仍按现有 Gate 执行，ITER-011 不复活；ITER-010 终态后的下一份新产品迭代（按顺序为
ITER-012）必须从首个持续 Web Alpha 起，用相互隔离、答案来源盲化的同题对照证明系统答案质量严格超过当时实际可用的 current Codex。
Codex 只是强外部基线，不是 Oracle 或裁判；质量全体打平也不得用成本、时延或复用优势改判通过。本规则不创建或授权下一迭代。

`ITER-010-PDR-003` 现是 Slice1 的恢复执行约束：用户报告约 14 小时仍无新体验版本且 DeepSeek token 消耗过多。Access 与答案 Quality
已经拆分；本轮超过 240 分钟 hard stop 后停止 scope expansion、外部批量调用和首次体验前 full regression。PDR-003 当时的孤立一题 canary 已被
PDR-004 收窄为一段冻结的五轮 Chat Conversation，不再执行孤立单题方向验证。Provider 对用户透明：Session 预授权 Ark→DeepSeek；fallback 是同一 Turn 下从 immutable original Turn Request、exact relevant Application-sealed Conversation Context 和 exact Cognition 重跑完整链的独立 attempt，用户不重提或重启。失败处理改为 root-cause-first：先定位 Source truth 到 Web 责任链中的最早偏差
并提出可证伪假设；无假设不得改 Prompt/Schema/Contract。修复先过本地最小复现与两个未参与修复的相邻案例，再跑一个有界 live canary 单元；当前 Chat 目标中该单元就是一段五轮 Conversation；
同 signature 修一次仍复现即评审架构职责。该 route 当前 `NOT_IMPLEMENTED / NOT_QUALIFIED`，不能冒充 live PASS。

`ITER-010-PDR-004` 是当前最高优先级规划决定。系统冻结“软件世界模型 + 主工程 Agent”双核心；默认交互冻结为 Conversation/Turn/
Application-sealed Context 的语义多轮 Chat，每轮独立 Evidence/Answer/Review/Delivery，新对话隔离。旧固定多角色内容流水线不是目标 Agent，
旧持续 Session QA 不是 Chat。独立 Chat Access 已为 `CHAT_ACCESS_BROWSER_PASS`；`FINDING-010-097` 又形成
`AGENT_EXECUTOR_LOCAL_CANDIDATE`，在确定性 fake ports 上闭合 Application-owned loop、跨 Turn Work State、Observation/Package、fresh
Review Finding 与 Delivery binding。`FINDING-010-098` 再形成 `EVIDENCE_TOOLS_LOCAL_CANDIDATE`：复用现有 World Model projector 与 Source
Broker/Worker，并把可重算的逐 Turn append-only Ledger prefix 和 Citation receipt 密封进双分区 Observation/Package。Provider-backed 主
Agent/Reviewer 的 sealed no-tools input/output、逐 dispatch Disclosure/Gateway receipt、失败计数和 non-dispatching candidate preflight 又由
`FINDING-010-099` 形成 `MODEL_BOUNDARY_LOCAL_CANDIDATE`；`FINDING-010-100` 又以 typed owner classification、两个隔离 full-chain attempt、
committed Work State repository、logical Turn 分账/duplicate-cost risk/late quarantine 和 non-starting fixed Browser composition 形成
`PROVIDER_ROUTE_COMPOSITION_LOCAL_CANDIDATE`。`FINDING-010-101` 又把生产 Ark/DeepSeek Adapter、credential-lazy transport、Model Gateway、
Session Disclosure 与 model boundary 接入同一 non-starting composition，形成 `PROVIDER_RUNTIME_COMPOSITION_LOCAL_CANDIDATE`。
`FINDING-010-102` 再把两条 Provider runtime、exact evidence authority、per-attempt fresh Tool/Response Control、committed Work State、
Conversation 与 Browser 闭合为 `SESSION_RUNTIME_COMPOSITION_LOCAL_CANDIDATE`。`FINDING-010-103` 又实现 owner-private closed artifact
Session loader 和 `swm-engineering-chat --session-config` 固定命令分支，绑定 product/source identity、published World Model、Source Profile、
ordered Ark→DeepSeek qualification identity、private Gateway repositories 与 launch/terminal receipt，形成
`ARTIFACT_SESSION_FIXED_COMMAND_LOCAL_CANDIDATE`。`FINDING-010-104` 又将 Ark transport 改为每 request 独立 verified TLS、TLS 后取
credential、每 session 一个 HTTP dispatch、retry 0，并把 strict Session audit 接入 Conformance 与 terminal receipt；HTTP 前不可用也由
Gateway owner-typed 为 fallback-eligible `PROVIDER_UNAVAILABLE`。旧 Ark Conformance 已明确失效，current actual artifact 尚未生成或执行，状态仍是
`NOT_QUALIFIED / NOT_LIVE`；不能把 offline
fixture、temp Git、Access、旧实现或旧 Result 追认为 mall 五轮 Chat
或答案质量能力。
PDR-003 的时间盒、根因、测试后置、Ark→DeepSeek 和成本规则继续有效；其孤立一题 canary 对 Chat 被收窄为一个五轮 Conversation，每个
发生 Provider dispatch 的 Turn 分别计 live attempt。Provider 前最多一次本地/Mock Access smoke 的额度已由
`V-ALPHA-ACCESS-001` 这一个 browser run 消费，不能再追加，也不能冒充 Chat canary。

PDR 收据 `3112da25…` 只授权项目决定纠正；`32b298de…` 收据曾补足旧 Slice1 开发授权，但 PDR-004 已将其暂停。当前 `f76ba3e8…`
开发授权不复用任何旧 live grant，也不自动取得 credential、Provider/model call、动态源码披露或 live browser 权限；后续 `7256a886…` 只对
exact `cf2883b…` 的 `V-ALPHA-ACCESS-001` listener/browser 生效并已完成。其余外部执行仍必须按 exact Conversation/Turn、Provider、
工程/revision、来源边界和逐输入披露重新授权。hidden 与 Production Activation 继续未授权。

ITER-010 原规划由用户以
`codex-user-message:sha256:d3b60bdaa52d96ced3c653a8dcd54fabff41beb7f23f0bf691e6983ebb9437bc` 于
`2026-08-21T08:23:25Z` 要求按最新讨论重新制定计划并更新文档；该收据只授权规划/docs，不授权产品编码。

用户随后以 `codex-user-message:sha256:585f02c4edcf25502b40f880c17a7bdf7f1af71044cd8d1bbe97b055a735ee9e` 于
`2026-08-21T09:18:34Z` 接受 Readiness，并只授权 Slice1 产品代码开发与本地确定性验证。授权审核的 planning commit/tree 为
`01dcfe2233625dfaa021495850fb18ae1323063b` / `8e364ae854bfaa48580ab080a3e0d9c9c43c3d6f`。Slice2/3、credential、Provider/model call、
正式 Web/live、hidden disclosure 和 Production Activation 仍未授权。此前 `1b327024… + 5cdb7000…` 仍只绑定被取代的设计。

用户随后以 `codex-user-message:sha256:b8b6931f8d76b45a16fa50ae057d7fa6ccd744d58f6041d3fdfc1fd5ca84e7c7` 明确表示同时授权完成当时
开发所需的权限。该消息作为 Slice1 needed-rights 的 root authorization，允许在产品代码和 deterministic gate 闭合后，为本 Slice 生成并
执行 exact product freeze、current Provider/credential-reference 检查、逐输入 Source/Cognition/Package disclosure、真实模型调用、
loopback listener/Web/browser 验证及其审计；它不把未知的动态输入提前视为已授权。每次 dispatch 仍须从该 root 收窄并密封 exact
Provider/model/endpoint/configuration/role/secret reference/fragment/full-input digest 的一次性 grant，产品 freeze 或输入变化即失效。
`SLICE-002/003`、hidden suite 和 Production Activation 不是完成当前 Slice1 所需权限，继续保持未授权。

针对本次 `mall` / DeepSeek 验证，用户又以
`codex-user-message:sha256:815d868ca3df4795276934acbc21d12584fcfd4cb49b31c67696c72d3a5a6b74` 明确授权把问题、Maven World Model
投影、角色 Ledger，以及 revision `0504e86…` 所选 Java/README/POM/Test evidence 发送到
`https://api.deepseek.com/chat/completions`。累计调用数不限，但产品冻结的每题 24-call fuse、retry 0、Provider switch 0 不变；
`src/main/resources`、配置凭据和 Production Activation 明确排除。

用户随后以 `codex-user-message:sha256:684849e3116168fb6dd67fbc9f9f70df0e5d1b8385b5f72f711cd75d62f1e9c9` 提供现场题
“登录流程是怎样的？”。该 exact question receipt 收窄前述 root authorization；现场 run 已完成并优雅停止，不能复用。它不等于用户对答案
方向的接受收据。

用户消息 `d746968f…` 指出实现者已经知道回答有问题，不应再把客观技术复核退回用户重复确认。旧记录把它推断为 `REDIRECT`；
PDR-001 现已修正为 `REWORK`。`ITER-010-RESULT-SLICE-001-STOP-REDIRECT` 与 `FINDING-010-028` 继续保存答案/审核失败和系统性根因，
但不再证明用户拒绝整个产品方向。

`ITER-009` 已依据三条真实 Web 体验以 `REDIRECT` 结束：技术代码和运行证据完整保留，但代码走读式回答方向未获接受。
`ITER-010` 从 clean commit `1fb997bab6444523f82ebf1a514a1abbf79656c7`、tree
`1369ce932c778c57a118123e8257ede476229d73` 继续，不废弃已经验证的 Web、Citation、Limitation、隔离和审核资产。

用户此前于 `2026-08-13T11:45:33+08:00` 接受 ITER-006 的 exact run-008 窄范围 Result：
在新的 SYSTEM Scope 上以 `JAVA_STATIC_CALL_GRAPH@1` 构建 Java 声明与可静态唯一解析的直接调用，发布 no-payload Snapshot/
Bundle，并从本机 `WORLD_MODEL / EVALUATION_ONLY` Web 入口完成 Source-off 问答、Gap 与 Citation。接受对象是受保护 candidate
stage `sha256:862fdb8d…`，不是当前整个未提交工作树；Production Activation 未执行。

## 当前系统与实现状态

| 范围 | 状态 | 证据边界 |
|---|---|---|
| Iteration 001 历史裁决 | Completed / pre-Git attestation | 正式知识单路径和本机体验的历史结果；原运行没有 exact Git identity，Production Activation 未执行 |
| Iteration 002 | **Completed / narrow acceptance** | exact 实现提交 `e5b030c6835a69c70153d90f62803d63b7a4ba75`；只接受 Evidence-first 本机同步问答实验，六题与直接源码基线打平 |
| Iteration 003 | **Completed / narrow acceptance** | 接受本机 Maven Structure World Model `EVALUATION_ONLY` 纵向闭环；修复后全新 G3b batch/evaluator 60/60 PASS，G4 与 750 项回归 PASS |
| Iteration 004 | **Completed / narrow acceptance** | implementation `6bacfdfa…`；自由问题已接到 accepted Snapshot-first WORLD_MODEL 隔离链路，真实浏览器、Gap、Citation、失败关闭和 761 项回归 PASS |
| Iteration 005 | **Completed / narrow acceptance** | implementation `956f31d6…`；用户指定 Maven Workspace、零问题显式更新、动态 Read Set 与正式 Web 问答完成；`run-006` 失败保留，`run-007` 三路各 9/9、comparison 与真实浏览器 PASS |
| Iteration 006 | **Completed / narrow acceptance** | 接受 exact run-008 已证明的 Java declaration/static-call `EVALUATION_ONLY` 闭环；run-003/run-007 FAIL、交互体验限制永久保留；不接受当前页面为最终通用 Web Chat |
| Iteration 007 | **Rejected / technical PASS, product FAIL** | run-004 完成正式 Web、三调用、隔离与 Citation，但固定单方法协议不能组合登录流程，也不能可靠判断源码中不存在的下单功能；无 Acceptance |
| Iteration 008 | **Rejected / REDIRECT / evidence preserved** | run-012 正式冻结 PASS；登录题真实 Web 以 5 次调用给出自然答案和 4 个 Citation；下单边界题的 Draft 正确形成 Limitation，但 Review 拒绝交付。该结果证明技术资产可复用，也证明当前边界未闭合；没有 Acceptance，未执行 canary、Agent 对照或 Activation |
| Iteration 009 | **Rejected / REDIRECT / evidence preserved** | 三条真实 Web 已足够判向：链路可运行，但默认答案被方法、分支、调用顺序和内部诊断主导；没有 Acceptance，后续 Slice 未执行 |
| Iteration 010 | **Authorized / active Slice1 / REWORK / PDR-004 Chat Alpha** | `V-ALPHA-ACCESS-001` 已在 clean `cf2883b…` 上通过真实 browser；`FINDING-010-097—104` 又形成 Application-owned Agent、evidence tools、sealed model boundary、Ark→DeepSeek route、生产 Provider runtime、artifact Session loader、固定命令与 Ark transport Session audit 本地候选，最新相关组合 141/141。fresh Ark Conformance、current actual artifact 与 mall 五轮 Chat 仍未执行、资格化或 live；后续 Chat/Quality/XD/Comparison/Preview 继续 blocking，Slice2/3、hidden、Acceptance 与 Production 未授权或未执行 |
| Iteration 011 | **Superseded / never executed** | 原 proposed 的答案优先探针/Alpha/夯实计划未获授权、未开发、未 live；有效的早体验与后置夯实原则已吸收回 ITER-010 REWORK |
| Evidence-first Strategy | PASS / exact and time-bound | `evidence-first-software-answer@1.0.0` 的十类能力、两个 Java 工程六题和本机浏览器体验通过；它读取任务级 Evidence Packet，不是 Snapshot 世界模型问答 |
| 软件世界模型产品闭环 | **ACCEPTED / local Maven + narrow Java static-call evaluation-only** | typed Structure Kernel、独立更新、Source-off View/Citation、Snapshot-first 回答与真实模型对照通过；仍未达到通用源码问答 MVP |
| `local-browser` | **Chat Access browser PASS / transport-audited artifact local candidate** | Direct、strict World Model、旧 Engineering QA 与新 Engineering Chat identity 不混用；`swm-engineering-chat` 无参数 Access 已通过 exact browser handoff，`--session-config` 又在零外部 I/O 测试中接入完整 artifact-backed Session，Ark/DeepSeek terminal transport audit 均已本地闭合。fresh Ark Conformance、current actual artifact、Citation 内容与五轮 Chat 未资格化或 live |
| Production Activation | **NOT EXECUTED** | 不得由任何本机 PASS 自动推导 |

精确产品边界见 [Iteration 006 Acceptance](iterations/iteration-006/results/acceptance.md)。原始 Provider、能力、产品和浏览器证据
保存在本机 `var/`，只通过 Result 中的 ID、Digest 和路径引用，不进入 Git。

## 当前执行顺序

当前已授权 ITER-010/Slice1 产品开发与本地确定性验证。PDR-004 的 Readiness refresh 已完成并由 `f76ba3e8…` 接受；既有自适应
`World Model Cognition Context → Investigation LLM → Source Broker → Retrieval Worker → append-only Evidence Ledger → 调查后 seal
Question Evidence Package → Answer → independent Reviewer` 技术纵切、公开题和现场题证据均已封存，但它只是可复用历史/兼容资产；
不能冒充主工程 Agent 或 Chat。当前项目决定为 `REWORK + AUTHORIZED SLICE1`，不是 Acceptance，也不追认历史答案/审核 FAIL。

当前最短顺序由 PDR-003 的交付纪律与 PDR-004 的 Chat 目标共同约束，但不再把全部 Gate 打包成一次交付：

1. 60 分钟内交付可启动 Chat 页面和固定 URL；Provider 未配置或失败必须如实显示，不能阻塞页面交付。
2. Turn1 前冻结同一份五轮 Conversation 脚本，180 分钟交付线先交其前三轮真实方向体验。180 分钟未交即 timebox FAIL 并停止新增范围；
   181—239 分钟只允许收敛现有纵切，迟到 Alpha 立即交付但只作 `FAIL / REWORK` 证据；240 分钟绝对停止。仍是独立问答、代码走读或
   特判时立即交用户判向并停止后续工作。
3. 只有前三轮方向未被停止，才在 360 分钟前完成五轮 Chat、新对话隔离和失败 Turn 隔离。
4. 只有五轮技术质量通过，才在 480 分钟前形成三臂盲化比较和独立技术判断，再由用户决定是否 hardening。

检查点 1 已完成：`FINDING-010-095` 的本地候选在 exact `cf2883b…` grant 下真实启动 `swm-engineering-chat`，
`ITER-010-RESULT-V-ALPHA-ACCESS-001 / FINDING-010-096` 证明 Conversation/Turn/Context、完整消息历史、新对话隔离、0-dispatch 失败真相和
固定 loopback 安全边界，`V-ALPHA-ACCESS-001` 为 `PASS / access-only`；listener 已优雅停止。下一步不是继续扩张 Access，而是先实现并冻结
同一五轮 Conversation 所需的主 Agent/Provider 纵切。`FINDING-010-097` 已完成其中不调用外部系统的 Application-owned executor 候选；
`FINDING-010-098` 又把现有 World Model projector、Source Broker/Worker、逐 Turn Ledger prefix 与 Citation receipt 接入该端口，定向组合
61/61。`FINDING-010-099` 进一步闭合单 Provider 主 Agent/fresh Reviewer 的 closed input/output、逐 dispatch Disclosure/Gateway receipt、
pre-dispatch/replay/fresh dispatch 计数以及不触发 listener/credential/Source/Provider 的 candidate preflight，当前相关组合为 86/86。
`FINDING-010-100` 随后闭合 ADR-017 双 route/fallback isolation 与 fixed Browser Application composition：只有五类 trusted classification 可
fallback，两个 attempt 从 immutable original Turn/Context 独立运行、分账并保持 retry 0，outcome unknown 标记重复计费风险，失败 primary
中间态不进入 committed Work State。相关组合 76/76。`FINDING-010-101` 随后将生产 Ark/DeepSeek Adapter、credential-lazy transport、Model
Gateway、Session Disclosure 与 Agent model boundary 接入 non-starting fixed composition，最新相关组合 79/79。`FINDING-010-102` 随后把
两条 runtime 与 exact evidence authority、fresh per-attempt Tool/Response Control、committed Work State、route、
Conversation 和 Browser 接成完整 non-starting Session，最新相关组合 89/89。下一最早缺口收窄为从 canonical private artifact Session
Configuration 加载 current sealed Conformance、published World Model、exact Source Profile/Worker 和两个 private Gateway repository，并由
Access-only fixed command 消费该组合。`FINDING-010-103` 已闭合该 loader 与 fixed-command 生命周期的本地实现，相关聚焦组合为 117/117；
`FINDING-010-104` 又闭合 Ark TLS-before-credential、每 request 独立 TLS、typed unavailable fallback 和 terminal Session audit，本地相邻组合
为 141/141。测试没有执行 current actual artifacts 或真实 listener。下一最早缺口是 clean freeze 上按新 identity 取得 fresh Ark
Conformance，再生成 current actual artifact，然后才可按 exact grant 执行五轮 live Chat；在此之前不取 live grant。

三轮检查点只是同一冻结五轮 live canary 的中间交付，不是独立三轮 canary；若在此停止，五轮 canary 记为 `INCOMPLETE / FAIL`。
每个检查点都是立即用户交付和停止点，不是新 Slice 或授权阶段，也不能恢复暂停或失效的授权。计划、测试、文档和内部 Gate 完成都不算用户可见增量；错过检查点时
交付最后可运行版本、唯一最早阻塞点和可证伪根因并停止范围扩张。等待外部授权时也停止产品扩张，不用额外内部建设填满等待时间。
孤立 live question 不能替代 Chat canary；每个到达 Provider dispatch 的 Turn 分别计 live attempt并保留完整 Evidence/Citation/Review。
首次体验前禁止继续扩张 Prompt、Schema、Contract 或跑 full regression。每次失败必须先定位最早偏差并形成可证伪根因假设；同 signature
修一次仍复现就停止规则累积并做架构职责评审。相同 identity 且仍有效的 Conformance 必须复用；DeepSeek 批量调用前重新核对官方峰谷
政策，成本只决定是否开始，不削减已开始 Turn 的完整质量链。

candidate `b6e13eb…` 的首次持续 Alpha 已证明 Session Authority、逐题 server identity、固定 `127.0.0.1:8765` 命令与真实 Provider/browser
链可启动，也再次证明旧 checklist coverage 允许代表性事实伪闭合，并发现 Gateway SQLite mode `0644`。随后 clean candidate `fc827ce…`
绑定 current DeepSeek Conformance `sha256:c6f6a0f…` 重跑原题；5 次 role dispatch、retry/switch 0，Package 与正文已覆盖成功登录数据库审计
写入，DB/WAL/SHM 均为 `0600`，但末尾 coverage-only Limitation 因 schema 强制非空 observation links 而错绑 supported observations，
Application 正确失败关闭。两次会话均已优雅停止，只作为失败证据。

clean candidate `e15ec50…` 再绑定 current Conformance `sha256:5ef04be6…` 执行原题；它已按上一修复返回空-link coverage Limitation，但
Investigation 只读 README 后把单一模态缺细节误作全局 Unknown，Answer 又把 limitation observations 错标为 process/impact roles，Domain
以 structured-output violation 失败关闭。该会话 5 次 role dispatch、retry/switch 0、private DB 成立并已优雅停止，同样只作为失败证据。

closed mapping/跨 evidence-class 修复后的 clean candidate `c7e32b5…` 已以 current Conformance `sha256:8802280…` 执行持续会话。原题用
7 次 dispatch 得到 `APPROVED`，Controller/Service exact Source、正文与独立 Reviewer 均覆盖凭据、验证、`SecurityContext`、JWT、失败分支和
`loginLogMapper.insert`；private SQLite 成立。随后两道异质题各在首个角色调用收到一次 `PROVIDER_HTTP_ERROR`，retry/switch 0，listener
继续；22,000 字符的页面请求在 Provider 前拒绝且调用根不增加。旧页面与 terminal audit 把真实 HTTP 失败误标为 binding drift/outcome
unknown，`FINDING-010-039` 已以 exact-binding failure propagation 和密封 Result rejection audit 修复。该旧会话已优雅停止，只证明原题与
失败隔离，不能追认为三题 PASS。

上述失败分类/审计修复已通过 model-source 11/11、Engineering QA 87/87 和允许 AF_UNIX 的完整 1148/1143；raw 仍精确为既有
4 FAIL + 1 ERROR，见 `FINDING-010-040`。这只允许形成新 clean candidate，不替代 current Conformance 或真实三题体验。

clean candidate `31a9ccd…` 的正确 DeepSeek Conformance 随后在第一次 HTTP dispatch 收到 402；TLS、证书与 credential resolution 成功，
request 1、retry 0、qualification `NOT_ISSUED`。DeepSeek 官方把 402 定义为余额不足。旧 run-008 qualification 的 adapter implementation/
configuration digest 与当前相同且仍在有效期，但它不能冒充当前账户可用或新三题答案证据。按 `FINDING-010-041`，当前 live 环境 hold，
不重试、不切 Provider；账户持有人恢复当前 API key 所属账户余额后，才以最终 clean candidate 和 fresh session 继续两道异质题。

余额恢复后的 run-013 fresh DeepSeek Conformance 已以 2/2 dispatch PASS，Result digest 为
`sha256:77e3d8fef91b1942b103928205a41fd1b40a2fa0016f9be6091b7cff5503f5d6`，retry 0、actual model
`deepseek-v4-pro`。随后 clean candidate `8565fa5…` 的持续会话提交原现场题；Question Understanding 把用户可见答案层级误当证据边界，
只要求文档/UI/日志并排除实现细节，Investigation 因而只读 README 后把全部 checklist 标成 `UNKNOWN`。Answer 经一次 rewrite 后得到
`APPROVED`，但页面仍未回答 `/admin/login`、凭据验证、Security Context、JWT、失败路径或登录审计。会话已优雅停止；terminal receipt
`sha256:8f4fcc04691582e3e69d1e7dc4f142e763868ffe5c5117afe0a556a1c4cea48a` 记录 1 题、8 dispatch、retry/switch 0、private files 和
Production `NOT_EXECUTED`。该 `APPROVED` 是错误失败证据，不能追认。

`FINDING-010-046` 现把 Prompt-only 规则提升为 Application closure：Source Broker 从 exact Source Profile 导出稳定有序的 registered
classes；每个 attempt 明确向角色提供 investigated 与 untried 集合；含 non-supported disposition 的 FINISH 在 untried 非空时追加命名下一个
required class 的 GAP 并继续，而全 SUPPORTED FINISH 不强迫读取无关来源。Question Understanding 同时明确答案抽象层级只控制交付表现，
不能排除 feature/flow/lifecycle/authorization/failure behavior 所需的 Source evidence。Prompt/Strategy 已升为 `@17/@7`，System Contract
已同步；Engineering QA 定向 93/93、docs 439/439，完整 1154 项中 1149 PASS，raw 仍精确保留既有 4 FAIL + 1 ERROR，状态为
`PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD`。下一步是形成 clean commit、重取 current Conformance，再以 root authority 收窄的新 exact
session 执行原题、两个异质题和 Provider 前受控失败；在此之前不把确定性测试或旧 `APPROVED` 写成真实答案 PASS，也不执行 hidden、
三臂消融或 Production Activation。

上述修复形成 clean candidate `8575517…` 并通过 run-014 fresh DeepSeek Conformance 2/2，Result digest 为
`sha256:85c52d9af857bcc3586c821edf9a500539d82de0a56b58bc2cf5beb39f94fefa`。同一持续会话的原登录题以 8 次 dispatch 实际读取
Controller/Service 源码并完整 `APPROVED`；第二、第三题分别在 13/10 次 dispatch 后因 FINISH 把 `LIMITATION` observation 放入
`SUPPORTED` disposition 而由 Domain 失败关闭，同时暴露 registered registry 被误作逐题最小证据集、以及已 allowlist 根 POM 被错称
未授权。terminal receipt `sha256:3f68c27c30207861368da71e4f12ea6bb7ab7d389ef7e457dd8259ab3afbaa0f` 记录 3 题、31
dispatch、retry/switch 0、private files 和 Production `NOT_EXECUTED`；受控超限输入仍在 Provider 前拒绝且 listener 保持 `READY`。

`FINDING-010-047` 已取代 `FINDING-010-046` 的全 registered-class closure：Question Understanding closed output 声明回答 checklist
直接需要的最小 `required_evidence_classes`；Application 分别投影 registered/required/investigated/untried-required/unregistered-required，
只在 non-supported FINISH 尚有可调查 required class 时追加 GAP。Initial/Verification FINISH schema 同时按 outcome 条件化 observation kind，
并明确 Source Profile allowlist 路径不得被声称为未授权。Prompt/Strategy 升为 `@18/@8`，定向 94/94 PASS；完整回归与新 clean/live 证据仍待
闭合，旧第一题 PASS 和后两题 FAIL 都不追认为新候选结果。

上述处置形成 clean candidate `5ce5ab0…`；run-015 fresh DeepSeek Conformance 2/2 PASS，Result
`sha256:38706e7ced6108ea47b35662ac681c1ee25056521de16e8d489d02283f3733f8`。同一持续会话 3 题共 32 dispatch、
retry/switch 0，但原始 Gateway SQLite 证明页面状态仍不可信：原登录题虽 9 次 dispatch 后 `APPROVED`，却再次漏掉
`insertLoginLog` 持久化审计副作用；混合构建/安全/unknown 题在合法 Package 上输出两个 `DIRECT_ANSWER` 而由 Domain 失败关闭；
401/403 题虽 12 次 dispatch 后 `APPROVED`，却只读 `SecurityConfig` 的 manager 接线而未读 manager 自身实现。terminal receipt
`sha256:9ac1011c9348157a1e585fe6b346f95d542ba693687ca75ba4543f0c37939c79` 证明 private files、Provider 前超限拒绝和 Production
`NOT_EXECUTED`，不能补救答案质量。

`FINDING-010-048` 现把 Question Understanding 提升为 class + 1—8 个 exact mandatory-read paths；Application 唯一解析 path/class，任何
FINISH 前都要求无行范围、coverage-complete 的 READ/PARSE，SEARCH/截断内容不消费义务。Answer closed output 改为唯一必填
`direct_answer` 与禁止直答的 follow-up `claims`，混合 Package 只允许 affirmative direct summary + 末尾 limitation。flow/lifecycle 同时
拆分并独立审核持久化、审计、缓存、通知和外部交互，多机制问题要求各决定性实现而非 caller/wiring。Prompt/Strategy 升为 `@19/@9`，
定向 96/96、docs 442/442 PASS；允许 AF_UNIX 的 full 1162 项中 1157 PASS，raw 唯一 4 FAIL + 1 ERROR 仍精确属于冻结历史 hold。
新 clean/fresh 三题仍待执行，run-015 的两个错误批准与一个失败均不追认。

上述处置形成 clean candidate `00afecd…` 并通过 run-016 fresh DeepSeek Conformance 2/2，Result
`sha256:df22a7eb3e289a5edaf6b11ab61df35bfffc63e34780614e4a2e74e821020df4`。同一持续会话中，原题在第 12 次总
dispatch 遇到一次真实 post-dispatch outcome unknown，另外两题各在 1 次 Understanding + 12 次 Investigation 后触发安全上限；三题
Question Understanding 分别声明 6/8/6 个 mandatory-read paths，且 Investigation 会继续读取搜索结果中的非必读相关文件。terminal
receipt `sha256:b3c94c2d30194a42a9a0b286a190ef16b345b662b657acff6b0c7700c283c67b` 记录 3 题、38 dispatch、
retry/switch 0、private files 和 Production `NOT_EXECUTED`；Provider 前超长输入拒绝继续成立。

`FINDING-010-049` 现把 mandatory-read path 上限从 8 收紧为 4，使当前 12-call initial fuse 在最坏 search/read/finish 组合下仍留 3 次
自适应余量；unread required path 存在时只向角色暴露对应 locator，并投影 exact maximum/remaining calls。exact-binding
`OUTCOME_UNKNOWN` 也不再落入 qualification drift，而以 `LIVE_INTEGRATION_HELD` 明确当前题关闭且 zero retry。Prompt/Strategy/
Understanding schema 升为 `@20/@10/@4`；新确定性、完整回归、clean commit、fresh Conformance 和三题 live 仍待闭合，旧三题全部只保留
为失败诊断。

本次处置的 Engineering QA 组合 97/97、docs 444/444、compile/diff PASS。允许 AF_UNIX 的 full 1163 项中 1158 PASS，raw 唯一
4 FAIL + 1 ERROR 仍精确为冻结 V-009 Adapter Conformance 与本机 Codex binary digest historical hold；默认 sandbox 额外 1 FAIL +
6 ERROR 精确属于 AF_UNIX 权限噪声。见 `FINDING-010-050`。raw suite 保持 FAIL，只允许形成下一 clean candidate，不替代 fresh live。

上述处置形成 clean candidate `d12223f225d4cd57335a25a6d2eff4af5ee6ee7b` / tree
`5f7011668f5d76343a5b7b1ecb3c47eb739472f5`。run-017 fresh DeepSeek Conformance 2/2 PASS，Result
`sha256:dccfffa4991cd2f8df7f586f3e94e825f5859bcb0e96983fd032a6274992da12`。同一持续会话三题分别使用 9/14/12
次 dispatch：原登录题和 401/403 题都完成 required paths 与 FINISH、进入 Answer，却分别以
`USER_VISIBLE_PROCESS → IMPACT_OR_SIDE_EFFECT → USER_VISIBLE_PROCESS → IMPACT_OR_SIDE_EFFECT` 和
`USER_VISIBLE_PROCESS → IMPACT_OR_SIDE_EFFECT → USER_VISIBLE_PROCESS` 返回合法但乱序的 follow-up roles，Application 在 Review 前
失败关闭；构建/安全/resources unknown 题取得 `APPROVED`，并诚实保留未授权 resources 中数据库连接、JWT 密钥和端口为未知。
terminal receipt `sha256:e901faf295850f7aff1c94b36ab7f02cdda1c7d36f611821a9757445f077f69f` 记录 35 dispatch、retry/switch
0、private files、verified transport 与 Production `NOT_EXECUTED`；22,000 字符输入仍在 Provider 前拒绝且 call root 不增加。

`FINDING-010-051` 现让可信 Answer adapter 在 Gateway raw output/digest 保持不变的前提下，只按既有受控 content-role 顺序稳定归一化
follow-up claims；同 role 原顺序及所有 Claim ID、kind、role、文本、checklist/observation/evidence links 均不改写，其他 Domain invariant
继续失败关闭。Strategy 升为 `@11`，Engineering QA 组合 98/98、docs 446/446、compile/diff PASS；允许 AF_UNIX 的 full 1164 项中
1159 PASS，raw 唯一 4 FAIL + 1 ERROR 仍精确为冻结 historical hold，见 `FINDING-010-052`。确定性 Gate 已闭合；新 clean/fresh
Conformance 和三题 live 仍须继续，本次 1 PASS + 2 FAIL 不追认为体验或答案质量 PASS。

上述处置形成 clean candidate `88e33bdd40bcea4c3cbb9f2bb13b8a7f07cc1b6c` / tree
`70f9a1fdc2125e8a776bac1208dea9c8513c647f`。run-018 fresh DeepSeek Conformance 2/2 PASS，Result
`sha256:37e3a3485990acbbac13e30721745700494cfdd521d1f444b6bc24ffe8d72836`。同一持续会话中，原登录题与构建/
resources unknown 题分别以 13/15 次 dispatch 取得 `APPROVED`；401/403 题以 8 次 dispatch 到达 Answer，三个检查面、401/403 区分和
Citation 均已形成，但用户明确要求的源码核对依据被正确分类为 `IMPLEMENTATION_EVIDENCE` 后无条件移出默认正文，使其独自绑定的 3 个
material observations 不可见并在 Review 前失败关闭。terminal receipt
`sha256:08d8404580043c4c1e0a52aa78f46d785eef2b321e1b67b5c2ddbce49c2d609c` 记录 36 dispatch、retry/switch 0、
private files、verified transport 与 Production `NOT_EXECUTED`；22,000 字符输入仍在 Provider 前拒绝且 call root 不增加。

`FINDING-010-053` 现让 `USER_VISIBLE_EXPLANATION` 只隐藏 observations 已由其他用户可见 Claim 完整覆盖的 implementation evidence；
uniquely material 的简洁核对依据必须进入默认正文，部分交叠仍失败关闭，`IMPLEMENTATION_DETAIL` 仍展开全部实现证据。Prompt/Strategy/
Draft identity 升为 `@21/@12/@5`。Engineering QA 99/99、docs 448/448、compile/diff PASS；允许 AF_UNIX 的 full 1165 项中 1160 PASS，
raw 唯一 4 FAIL + 1 ERROR 仍为冻结 historical hold，见 `FINDING-010-054`。确定性 Gate 已闭合；新 clean/fresh Conformance 和三题 live
仍须继续，本次 2 PASS + 1 FAIL 不追认为体验或答案质量 PASS。

上述处置形成 clean candidate `c65617ee36280b5473b142e840fe6a50a1331623` / tree
`df98dd0749eb6b8a7d91186674fcae454c02b49a`。run-019 fresh DeepSeek Conformance 2/2 PASS，Result
`sha256:8cde961ffd9a4f285204c8aff0a2ed5f838bfc3ddcf18a23388710d749bf89fe`。同一持续会话三题分别以 12/15/12 次
dispatch 得到模型 `APPROVED`；implementation evidence visibility 修复在第三题真实生效。但独立技术复核发现第三题先把未认证与权限不足
都写成 403，随后又正确区分为 401/403；raw Review 逐字复述冲突且 Findings 为空。terminal receipt
`sha256:cfed19a1dd5da2bc6a9970c855d0bac4f8b773b87018c2e8409e2d35c5dafde8` 记录 39 dispatch、retry/switch 0、
private files、verified transport 与 Production `NOT_EXECUTED`；22,000 字符输入仍在 Provider 前拒绝且 call root 不增加。

`FINDING-010-055` 现为 Review quality 新增 closed `claim_consistency`，强制成对比较 direct/default Claims、Package observations 与独立
observations；同一条件的互斥结果必须 FAIL 并 rewrite。Quality/Review schema、Prompt/Strategy 升为 `@2/@4/@22/@13`，APPROVED 需要
五项全 PASS。Engineering QA 99/99、docs 450/450、compile/diff PASS；允许 AF_UNIX 的 full 1165 项中 1160 PASS，raw 唯一 4 FAIL +
1 ERROR 仍为冻结 historical hold，见 `FINDING-010-056`。确定性 Gate 已闭合；新 clean/fresh live 仍须执行，run-019 不能追认为答案质量
PASS。

上述处置形成 clean candidate `274e5ea23423072574bf1797ec5254def4be3903` / tree
`c7875bef05b6538c0d240fa28e462d5f763d0a1c`。run-020 fresh DeepSeek Conformance 2/2 PASS，Result
`sha256:8bf5f3b763e2e987ec796e8c1e58e890f156847dcedc07ca303c290bbec394dc`。同一持续会话中，原登录题以 10 次 dispatch
获得独立可接受的 `APPROVED`；Q2 在 5 次 dispatch 后以 `NO_PROGRESS_FUSE_EXHAUSTED` 关闭，因为 Application 已知 4 个 exact
mandatory paths 却没有 direct locator，模型只能以内容搜索重发现 path；Q3 在 11 次 dispatch 后完整形成三个检查面的证据，却在
`SUPPORTED` disposition 中混入 `LIMITATION` 与 search-only boundary reference，以 `STRUCTURED_OUTPUT_INVALID` 正确关闭。Q2 后同一
listener 接受 Q3，单题失败隔离成立。随后 22,000 ASCII 字符约 22 KB，低于 65,536-byte 服务端上限，合法发生 1 次 dispatch 后人工停止。
terminal receipt `sha256:1408e82757b454bc8246f9cc5ea0be2f180243a16a300715ecfdfeae25e477f2` 记录 4 题、27 dispatch
（10/5/11/1）、retry/switch 0、verified transport 与 Production `NOT_EXECUTED`。

`FINDING-010-057/058` 现由 Broker 为每个已验证 mandatory path 签发 exact Request + Investigation attempt + Source Profile + class + path
绑定的 opaque direct locator，模型不再用内容 SEARCH 重新发现已知 path；Provider-facing FINISH 同时拆为
`supported_finish_dispositions / non_supported_finish_dispositions` 两个结构互斥数组，可信 adapter 只合并已验证内容，Domain 继续独立
拒绝 outcome/kind/reference 混类。Question Understanding 也不得因 modality 可用或用户只要求“可核对依据”而引入无关 TEST/log/config
need。Broker/Strategy/Prompt/Initial+Verification schema 升为 `@2/@14/@23/@6`。`FINDING-010-059` 已以 Engineering QA 101/101、
docs/compile/diff 和允许 AF_UNIX 的 full 1167/1162 闭合确定性 Gate；raw 唯一 4 FAIL + 1 ERROR 仍为冻结 historical hold。新 clean/fresh
Conformance 与三题 live 尚待闭合，run-020 不能追认为体验或答案质量 PASS。

上述 deterministic candidate `dfba244…` 已通过隔离 clone Engineering QA 101/101、docs 453/453 与 run-021 fresh DeepSeek
Conformance 2/2；同一持续 Alpha 中，原登录题与 401/403 排障题各以 8 次 dispatch 得到独立可接受的 `APPROVED`。Q2 的 4 个
mandatory paths 也已由 direct locator 无 SEARCH 完整读取，但 FINISH 把 3 个 UNKNOWN 先放进含全部 7 项的 supported array，再复制到
non-supported array，Application 在第 6 个总 dispatch 正确以 `STRUCTURED_OUTPUT_INVALID` 关闭。该 FINISH 仍有 8 个含当前动作的
initial-investigation call，证明 mandatory minimum 又被误作完整调查计划。真正 66,000-byte 的输入在 Provider 前拒绝，Gateway 根保持
22；terminal receipt `sha256:d38d94bb…` 记录 8/6/8 dispatch、retry/switch 0、verified TLS、private files 与 Production
`NOT_EXECUTED`。`FINDING-010-060` 现把两数组收紧为 disjoint union + checklist exact-once，并要求有授权未读来源且剩余预算可达时继续
缩小 material gap；Strategy/Schema/Prompt 升为 `@15/@7/@24`。`FINDING-010-061` 已以 Engineering QA 101/101、docs/compile/diff 与
允许 AF_UNIX 的 full 1167/1162 exact historical hold 闭合 deterministic Gate；新 clean/fresh live 待执行，run-021 不能取得三题 Gate。

随后 clean `be15a0a…` / run-022 的首题 Understanding 正常，第一个 Investigation 也选择合法 direct locator 与 current basis，却返回空
`checklist_item_ids`；Domain 正确失败关闭。Provider Schema 原先对 checklist/basis binding arrays 仍使用允许空/重复的普通数组，而
Domain 一直要求 non-empty + unique。run-022 在 2 次 dispatch 后停止，retry/switch 0、verified TLS、private files、Production
`NOT_EXECUTED`；没有提交 Q2/Q3 或超限输入，不能用 run-021 拼接。`FINDING-010-062` 已将 Initial/Verification Provider Schema、Prompt
与 Domain 对齐；`FINDING-010-063` 以三模块 65/65、Engineering QA 102/102、docs/compile/diff 与允许 AF_UNIX 的 full 1168/1163
exact historical hold 闭合 deterministic Gate。下一步是新 clean candidate/fresh Conformance、三题与超限负测。

该处置形成 clean `656b549…` / run-023。fresh Conformance 2/2 PASS；同一持续 Alpha 的 Q1/Q2/Q3 分别发生 8/8/7 次 dispatch，
retry/switch 0，66,000-byte UTF-8 输入继续在 Provider 前拒绝，private files 与 Production `NOT_EXECUTED` 成立。Q1/Q2 独立可接受；Q3
虽获模型 `APPROVED`，却仅凭 token filter 的 empty-context 状态和 authorization manager 的 deny decision 断言最终 401/403，并把同一
unauthenticated 条件赋予互斥外部结果，Reviewer 仍将 consistency 误判为 PASS。`FINDING-010-064` 将根因收敛为下游 response ownership
缺失：外部 status/error/body 必须由 response/exception mapper 的 full-content evidence 支持；handler wiring 只证明选择，transport status
与 application/response-body code 必须分开。Prompt 升为 `@26`，新 clean/fresh live 尚待执行，run-023 不能取得答案质量 Gate。

`FINDING-010-065` 已以三模块 65/65、Engineering QA 102/102、docs 459/459、compile/diff PASS 闭合 deterministic Gate；默认 sandbox
full 1168 项为 5 FAIL + 7 ERROR，允许 AF_UNIX 后为 1163 PASS，raw 唯一 4 FAIL + 1 ERROR 仍精确是冻结 V-009/Codex historical
hold，没有 ITER-010 新失败。新的 clean candidate/fresh Conformance 与三题仍是下一 Gate。

随后 clean `740c74a…` / run-024 在三题 6/14/5 dispatch 中暴露 FINISH parent/child reference 重复维护、UNKNOWN 双分区和 Review
action/request 重复维护三类错配。`FINDING-010-066/067` 已收敛 Provider output，由可信 Adapter/Application 派生重复状态；
`FINDING-010-068/069` 以 Engineering QA 106/106、current docs 463/463、允许 AF_UNIX 的 full 1172/1167 及同一历史 hold 闭合
deterministic Gate。

该处置形成 clean `7fb7e7c…` / run-025。fresh DeepSeek Conformance 2/2 PASS；同一持续 Alpha 的 Q1/Q2/Q3 分别发生 8/13/12 次
dispatch，retry/switch 0，每题一次 verified TLS handshake，66,000-byte UTF-8 输入在 Provider 前拒绝。Q1 `APPROVED` 且四个
Citation 已逐个打开核对。Q2 的 typed Review 正确只请求 `check-3`，Verification 也正确只返回一个 supported `check-3` delta；旧 Domain
却要求全四项而失败。Q3 请求的 handler implementation 不在本次 exact 12-file allowlist，重复搜索被 Broker 拒绝并由 no-progress fuse
安全关闭。terminal receipt document digest `sha256:7e75662d…7f11` 证明 private files、listener continuity 与 Production
`NOT_EXECUTED`。`FINDING-010-070/071` 正在以 authorized single-gap scope、trusted stable merge、Package full-read consumption 和
latest Broker rejection projection 修复通用根因；run-025 保持 1 PASS + 2 FAIL，不追认为体验或答案质量 PASS。

`FINDING-010-072` 已以 Engineering QA 109/109、docs 组合 142/142、历史 oracle 组合 74/74、current docs 466/466、compile/diff PASS
以及允许 AF_UNIX 的 full 1175/1170 exact historical hold 闭合 deterministic Gate。默认 sandbox 的额外 1 FAIL + 6 ERROR 也精确属于
AF_UNIX 权限噪声。下一步是提交新的 clean candidate 并执行 fresh DeepSeek Conformance、持续三题、66,000-byte Provider 前负测与
raw Answer/Reviewer 独立复核；run-025 不追认，Production Activation 仍未执行。

随后 clean `32a00a3…` / run-026 的 fresh Conformance 2/2 PASS，同一 listener 三题使用 8/12/14 dispatch，retry/switch 0，
66,000-byte 输入在 Provider 前拒绝且调用总数保持 34。Q1 `APPROVED`；Q2 的 Verification limitation observations 错把旧
`cognition-unknown-1/2/3` 当成 CommonResult gap，Answer citation closure 正确失败；Q3 的 handler limitation 已诚实形成，却被第二次
Review 对同一 gap 再请求并耗尽一次 preview fuse。terminal receipt document digest `sha256:cfa93204…32c0ea`，Browser console 为空，
private files 与 Production `NOT_EXECUTED` 成立。`FINDING-010-073` 已把 predecessor boundary 从补证 eligibility 排除，逐 child 强制
current gap reference，并向 Reviewer 投影 typed terminal verified outcome；Strategy/Prompt 升为 `@19/@29`，focused 76/76 PASS。run-026
永久保持 1 PASS + 2 FAIL；扩展 Gate 与下一 clean/fresh live 仍待执行。

`FINDING-010-074` 已以 Engineering QA 113/113、docs 组合 146/146、历史 oracle 组合 78/78、current docs 468/468、
compile/diff PASS 与允许 AF_UNIX 的 full 1179/1174 exact historical hold 闭合 deterministic Gate。默认 sandbox 额外
1 FAIL + 6 ERROR 精确属于 AF_UNIX 权限噪声；raw 唯一 4 FAIL + 1 ERROR 仍是冻结 V-009/Codex hold，没有
ITER-010 新失败。下一步只能从新 clean candidate 执行 fresh Conformance、持续 Browser 三题、Provider 前负测与
raw Answer/Reviewer 独立复核；Production Activation 仍未执行。

该 candidate 的 run-027 fresh Conformance 2/2 PASS；持续三题共 23 dispatch、retry/switch 0，66,000-byte 输入仍在 Provider 前拒绝。
Q1 `engineering_result_60a8a…` 独立复核 PASS；Q2 `engineering_result_b8f5…` 与 Q3 `engineering_result_279b…` 虽被页面标为
`APPROVED`，但 raw Package/Draft/Review 证明其把 `${jwt.tokenHeader}`/`${jwt.tokenHead}` 扩张为具体 `Authorization`，从未挂载
`UmsAdminLoginParam` 推断 fields，并从 handler registration/deny decision 推断未挂载 handler output 与下游 401/403。23 个调用中没有
Verification，唯一 Reviewer 完整复述同一错误且五项全 PASS；因此实际 Gate 为 1 PASS + 2 FAIL。terminal receipt document digest 为
`sha256:84a46df1…3de2a`，private files、Browser console clean 与 Production `NOT_EXECUTED` 成立。

`FINDING-010-075` 已把 finding-free comprehensive Review 降为 provisional，并强制另一个 fresh evidence-boundary challenge；Application
向该 challenge 投影 cited configuration placeholder、Claim 中 cited content 未出现的 status literal 和 Draft 提及但未挂载的同 application
type，Gateway 只允许 `Answer → COMPREHENSIVE → EVIDENCE_BOUNDARY_CHALLENGE`，最终 Authorization 只接受后者。每题预留 Answer +
双 Review 三次 role call，Review attempt 上限 4、hard 24-call fuse 和 zero retry/switch 不变。focused 78/78、Engineering QA 115/115
已通过；扩展 docs/oracle/full deterministic Gate 与下一 clean/fresh live 尚待闭合，run-027 永久保持 1 PASS + 2 FAIL。

`FINDING-010-076` 已以 focused 78/78、Engineering QA 115/115、docs 组合 148/148、历史 oracle 组合 80/80、current docs/compile/diff
与允许 AF_UNIX 的 full 1181/1176 exact historical hold 闭合 deterministic Gate。默认 sandbox 额外 1 FAIL + 6 ERROR 均为 AF_UNIX
权限噪声；raw 唯一 4 FAIL + 1 ERROR 仍精确属于冻结 V-009/Codex hold，没有 ITER-010 新失败。下一步只能从新 clean candidate
执行 fresh Conformance、持续 Browser 三题、Provider 前负测与独立复核；Production Activation 仍未执行。

该 candidate 的 run-028 fresh Conformance 2/2 PASS；同一持续 Browser 三题分别使用 9/9/8 次 dispatch，共 26 次，retry/switch 0；
66,000-byte 输入在 Provider 前拒绝且调用数不变，服务继续 READY，private files、console clean 与 Production `NOT_EXECUTED` 成立。
Q1 `engineering_result_347a96a…` 与 Q3 `engineering_result_4b0ff46a…` 独立 PASS；Q2
`engineering_result_15123f1a…` 虽保留 `${jwt.tokenHeader}` / `${jwt.tokenHead}` 具体值、secret、端口和数据库连接为未知，却把
Controller 的 `getUsername()/getPassword()` caller use 写成 `UmsAdminLoginParam`“包含”字段。raw challenge 已含 exact
`MENTIONED_APPLICATION_TYPE_WITHOUT_MOUNTED_IMPLEMENTATION` lead，Reviewer 仍复制该断言并五项全 PASS、Findings 为空；实际 Gate 为
2 PASS + 1 FAIL，terminal receipt document digest 为 `sha256:b199e6c9…afc76`。

`FINDING-010-077` 已把投影 lead 提升为 Application-owned typed value 与 stable `challenge_id`。Provider Review closed output 现必须
逐项返回 evidence scope、Draft scope 和 `WITHIN_EVIDENCE_BOUNDARY / DRAFT_EXCEEDS_EVIDENCE_BOUNDARY`；越界项必须绑定同输出中作用于
被挑战 Claim 的 Finding。Application 在 Review accept 与 Authorization 都重算 exact ID 集合，漏项、重复、未知 ID、comprehensive
提前处置或 Finding 错绑全部失败关闭。Strategy/Prompt/Review Schema 为 `@21/@31/@6`，focused 78/78、Engineering QA 115/115 PASS；
扩展 deterministic 与下一 clean/fresh live 尚待闭合，run-028 不追认，Production Activation 仍未执行。

`FINDING-010-078` 已以 Engineering QA 115/115、docs 组合 148/148、历史 oracle 组合 80/80、current docs/compile/diff 与允许
AF_UNIX 的 full 1181/1176 exact historical hold 闭合 deterministic Gate；没有 ITER-010 新失败。下一步只能从新 clean candidate
执行 fresh Conformance、持续 Browser 三题、Provider 前负测与 raw challenge assessment 独立复核；run-028 仍不追认，Production
Activation 仍未执行。

clean `e0ad3c8…` 的 run-029 fresh DeepSeek Conformance 2/2 PASS；同一持续 Browser 三题分别使用 9/11/8 次 dispatch，共 28 次，
retry/switch/outcome-unknown 0。66,000-byte 输入在 Provider 前拒绝且调用数不变，private files、console clean、listener continuity 与
Production `NOT_EXECUTED` 成立。Q1 `engineering_result_890ecfc…` 被错误 `APPROVED`，但完整 Service entry 中的
`insertLoginLog` / `loginLogMapper.insert` 登录审计持久化仍被 Answer 和双 Review 漏掉。Q2 正确识别未挂载 DTO 扩张，rewrite 却丢掉
另一个安全 observation，Application 失败关闭；Q3 正确识别 401/403 扩张，assessment Finding 的 Claim 却不属于每个 exact
challenge，Application 失败关闭。因此 run-029 是 0/3 PASS，不因两项安全失败关闭而改写为通过。

`FINDING-010-079` 已要求每个被默认正文引用的 cited full-content Java entry 独立执行 material-effect scan，新增
`DRAFT_OMITS_MATERIAL_EFFECT`；Answer input 在大对象前投影 exact observation ID/statement/kind/checklist/evidence table，rewrite
收窄一个推断时仍须保留其他安全 observation；所有非 passing assessment 都必须绑定 exact challenge Claim，Finding code 只有在同一 Claim
属于每个 challenge 时才能复用。full entry 已证明但 sealed Package 缺 observation 时，通过 successor gap delta 复用 predecessor support
补入原子 observation，再完整重答重审。Strategy/Prompt/Review Schema 为 `@22/@32/@7`，focused 79/79、Engineering QA 116/116 PASS；
扩展 deterministic 与下一 clean/fresh live 尚待闭合，run-029 不追认，Production Activation 仍未执行。

`FINDING-010-080` 已以 Engineering QA 116/116、docs 组合 149/149、历史 oracle 组合 81/81、current docs/compile/diff 与允许
AF_UNIX 的 full 1182/1177 exact historical hold 闭合 deterministic Gate；默认 sandbox 额外 1 FAIL + 6 ERROR 精确属于 AF_UNIX
权限噪声，raw 唯一 4 FAIL + 1 ERROR 仍是冻结 V-009/Codex hold，没有 ITER-010 新失败。下一步只能从新 clean candidate 执行 fresh
Conformance、持续 Browser 三题、Provider 前负测与 raw Answer/Reviewer/challenge assessment 独立复核；run-029 不追认，Production
Activation 仍未执行。

clean `9ae982b…` / run-030 的 fresh DeepSeek Conformance 2/2 PASS；同一持续 Browser 三题分别使用 14/14/8 次 dispatch，共 36 次，
retry/switch/outcome-unknown 0。66,000-byte 输入在 Provider 前拒绝且调用数不变，private files、console clean、listener continuity、
clean SQLite checkpoint 与 Production `NOT_EXECUTED` 成立。Q1 最终覆盖登录审计持久化，Q3 正确分开 token 校验、SecurityContext 与动态
权限并保留 handler mapping unknown，两题独立 PASS；Q2 虽被页面错误 `APPROVED`，却只并列依赖与安全组件，没有把登录返回的
token/tokenHead 交接到受保护请求输入，也没有明确 configuration-backed header/prefix unknown。因此 run-030 实际为 2 PASS + 1 FAIL，
见 `FINDING-010-081`。

`FINDING-010-082` 已将 startup/call/use/integrate/diagnose 的 operational checklist、Answer input/output handoff、通用
`ORIGINAL_QUESTION_FULFILLMENT_SCAN` 与 `DRAFT_OMITS_MATERIAL_REQUIREMENT` 写入 System Contract；专用 disposition 与错误
challenge kind 的组合由 Application 失败关闭。Strategy/Prompt/Review Schema 为 `@23/@33/@8`，focused 80/80、Engineering QA
117/117 PASS。`FINDING-010-083` 再以 docs 组合 150/150、历史 oracle 组合 82/82、current docs/compile/diff 与允许 AF_UNIX 的
full 1183/1178 exact historical hold 闭合 deterministic Gate；raw 唯一 4 FAIL + 1 ERROR 仍为冻结 V-009/Codex hold，没有 ITER-010
新失败。下一步只能从新 clean candidate 执行 fresh Conformance、持续 Browser 三题、Provider 前负测与 raw
Answer/Reviewer/challenge-assessment 独立复核；run-030 不追认，Production Activation 仍未执行。

clean `3c45072…` / run-031 的 fresh DeepSeek Conformance 2/2 PASS；Q1 在同一持续 Browser 会话使用 12 次 dispatch，request retry、
provider switch 与 outcome unknown 均为 0。第二次 challenge 从完整 Service entry 发现 `getCacheService().setAdmin` cache write，却没有把它
声明为 Application material-observation omission，反而绑定 `REWRITE_WITH_EXISTING_EVIDENCE`；由于 sealed Package 没有 cache
observation ID，放宽 rewrite 会破坏 observation authority，现有 `maximum_same_package_rewrites=1` 正确以
`SAME_PACKAGE_REWRITE_FUSE_EXHAUSTED` 关闭 Q1。Q2/Q3 与 66,000-byte 负测未执行，见 `FINDING-010-084`。

当前修复要求 material-effect assessment 返回 exact omitted-effect statements 与 `APPLICATION_PACKAGE / DEFAULT_DRAFT` closed layer；
Application 重算 effect 是否存在于 challenged entry 的 exact observations，并强制前者走同 evidence class Verification、后者仅在 exact
observation 已存在时走 entry-bound rewrite。Strategy/Prompt/Review Schema 为 `@24/@34/@9`；`FINDING-010-085` 已以 focused 80/80、
Engineering QA 117/117、docs 组合 150/150、历史 oracle 组合 82/82、current docs/compile/diff 与允许 AF_UNIX 的 full 1183/1178 exact
historical hold 闭合 deterministic Gate。下一步只能形成新 clean candidate/fresh live；run-031 不追认，Production Activation 仍未执行。

clean `3bd3c04…` / run-032 的 fresh Conformance 2/2 PASS。持续 Browser 的 Q1 用 12 dispatch 得到独立可接受的 APPROVED；Q2 用 9
dispatch 后暴露 challenge projection 与 Application membership Gate 都把 observation 的 `retrieval_item_*` source reference 错当成
`support_entry_*` entry ID 比较，导致 sealed Package 已有登录日志 observation 却投影为空，并以错误 `DEFAULT_DRAFT` 响应失败关闭。Q3
前 5 次 dispatch completed，第 6 次 Answer dispatch 遇到 `REMOTE_DISCONNECTED`，按授权零重试封存 outcome unknown；66,000-byte
请求在 Provider 前拒绝，accepted question 3、dispatch 27 均未增加。terminal receipt、Gateway quick check、checkpoint、0600 与 listener
关闭审计均通过，Production `NOT_EXECUTED`。

`FINDING-010-086` 现要求 challenge 与 Application 复用 exact support entry → `source_reference` → observation resolver，并明确空投影有
omission 时禁止 `DEFAULT_DRAFT`、两层 omission 同时存在时先补 Application observation。Strategy/Prompt 为 `@25/@35`，Review Schema
保持 `@9`；`FINDING-010-087` 已以 focused 80/80、Engineering QA 117/117、docs 组合 150/150、历史 oracle 82/82、481 current docs、
compile/diff 和允许 AF_UNIX 的 full 1183/1178 exact historical hold 闭合 deterministic Gate。没有 ITER-010 新失败；下一步只能形成新
clean candidate/fresh live。run-032 不追认，项目状态仍为 REWORK，Production Activation 仍未执行。

clean `d70a3e6…` / run-033 的 fresh Conformance 2/2 PASS。持续 Browser 的 Q1 用 15 dispatch 正确进入 `APPLICATION_PACKAGE`
Verification，但 gap need 扩张到未挂载 cache callee 内部，Verification 又用单一 `UNKNOWN` replacement 覆盖 supported check-6，静默删除
predecessor 登录流程/审计 observations；后续 challenge 错绑 Claim 并失败关闭。Q2 用 8 dispatch，在 Initial `FINISH` 自造
`cognition-unknown-*`，由 admissible-reference Gate 正确关闭。Q3 用 8 dispatch，第二轮 Review 在 HTTP dispatch 后发生
`NETWORK_FAILURE`，按零重试封存 outcome unknown。66,000-byte 在 Provider 前拒绝且总 call roots 保持 31；terminal receipt、private
SQLite quick-check/checkpoint、0600、无 WAL/SHM 与 listener 关闭审计均通过，Production `NOT_EXECUTED`。

`FINDING-010-088` 将 Verification supported target replacement 改为单调保留：角色输入取得 exact observation preservation contract，
Application 在 successor seal 前机械拒绝删除、改写或重排旧 observation；non-supported predecessor boundary 仍可由真实新证据替换。
`APPLICATION_PACKAGE` effect gap 只请求 caller full content 已可见 interaction 的 typed observation，不要求未挂载 callee internals。
Strategy/Prompt 为 `@26/@36`，Review Schema 保持 `@9`；focused 80/80 已 PASS，扩展 deterministic Gate 与新 clean/fresh live 仍待闭合。
`FINDING-010-089` 已以 Engineering QA 117/117、docs 组合 150/150、历史 oracle 82/82、483 current docs、compile/diff 与允许
AF_UNIX 的 full 1183/1178 exact historical hold 闭合 deterministic Gate；没有 ITER-010 新失败。新 clean/fresh live 仍待执行；run-033
不追认，项目状态仍为 REWORK，Production Activation 仍未执行。

新 clean candidate `fe6b6b6…` / tree `fa0b429…` 随后启动 run-034 fresh DeepSeek Conformance。第一条
`deepseek-v4-pro` request 已完成 credential resolution、verified TLS 与 HTTP dispatch，但 Provider 返回 HTTP 402；
request 1、input/output token 0、retry/switch 0，第二条 canary 未发送。Result
`sha256:f13d2e0afe3ea3dc41b1b2cf25a11f34d038c14a1e2891dfac283daba26e6215` 已以 FAIL 封存，没有
Qualification、Alpha Session、listener、Browser 提交或 mall 证据披露。`FINDING-010-090` 将其分类为
configuration-environment hold；当前 `DEEPSEEK_API_KEY` 所属账户恢复 Provider 可用性后，必须新建 fresh
Conformance run，不得重用 run-034。项目状态仍为 REWORK，Production Activation 仍未执行。

以下内容是 `ITER-008` 的历史执行记录，用于追溯证据，不是当前开发指令。

### ITER-008 已终止的历史执行记录

ITER-008 活动 bounded capability/Strategy 为 `1.5.11`、prompt/vocabulary `@20`、semantic-intent
compiler `@7`、terminal authority compiler `@3`、Gateway policy `@1.4.12`、suite/oracle `@1.5.11`。18 个 Case、18/18 threshold、
41 次资格调用、temperature 0、no-request-retry
与三层完整性不变。首轮模型提交通用 search terms 和注册 operation/relation evidence requests；Application 做依赖收敛和预算可达性
校验后冻结 ledger；强制 candidate discovery 的同名 raw evidence alias 保守向上归一为 method evidence，不能让非零候选只凭存在性
结束。method Result 已包含 exact supported outgoing `CALLS`，因此 standalone raw outgoing-direct alias 也收敛为 method；path 组合、
incoming/both 不折叠。Application 再从 ledger、立即前序 typed Result 和预算推导每轮唯一合法 transition。raw operation、premature FINISH 与 terminal
text 均不取得查询、终态或完整性解释权力；evaluator 的 independent later-state Case 使用另一个预冻结、产品可达 ledger fixture。
对完全 ASCII 的原问题，Application compiler 以 closed tokenizer 排除 function/discourse/authority/budget 与 negated presentation
clause，将 direct question term 置于 model normalization 之前，casefold 去重并共同受 12 项上限约束；raw model output/digest 不变，
non-ASCII translation 仍由模型负责。
Draft/Review 的 terminal compiler 另从 sealed typed method Result 编译 caller 不可伪造的 ordered
`behavior_obligation_scope`，逐 event 暴露 source order、可读 reference 与 same-target occurrence/count；Draft 不得合并重复调用，
Reviewer 对遗漏 exact multiplicity 返回 `MATERIAL_OMISSION`。raw Query Result 仍是 authority，compiler 不加入题目/工程/Oracle 特判。
活动 bounded model-egress policy 为 `@1.4.12`：Provider preference 是 `VOLCENGINE_ARK → DEEPSEEK`，但只从 dispatch 前完整且
current 的 exact qualification route 中选择；本轮 Ark 不合格，因此 product candidate 密封 DeepSeek。选择后只允许 DeepSeek 的
host/model/credential/TLS/socket route，任何 request 已分派或 outcome unknown 后都不切换 Provider。DeepSeek Adapter 为
`deepseek-chat-completions-no-tools@7`、Conformance fixture `1.2.0` / Result `@2`；Adapter 只把 closed schema 与 Gateway semantic prompt
合并为恰好一个 leading system message，不再承担领域 lexical-coverage 编译；connection policy 为
`PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@2`，每条 verified session 最多 20 次 HTTP dispatch，一次授权运行最多 3 次
credential-free TLS acquisition；轮换发生在下一次 credential/HTTP 前，成功 session 承载彼此独立的 stateless request，任何
HTTP bytes 可能发送后的失败均不重发。
本机现存 15 份 Ark Conformance Result 全部属于 Adapter `@1`—`@7`，对当前
`openai-chat-completions-no-tools@8` 均以 `QUALIFICATION_INVALID` 失败关闭。

run-001 已在 exact candidate `872d1e9ec6bd185dd05aa2974a33faf2ef509d5b` 上取得并消费一次性 2-call 授权，但实际 CLI 返回
`PROVIDER_OUTCOME_UNKNOWN`，没有形成当前 `@8` 的 PASS Result。旧 runner 只密封 invocation，因此现有证据只能证明执行过 1—2 次
调用，无法恢复更精确计数或网络原因；不得猜测、补造或用原授权重试。失败证据缺口及 runner 修复见 `FINDING-008-007`。

observability 修复提交 `60e1081e89705882fab17a67fc75dcb152b7994d` 后，run-002 绑定 preflight
`sha256:86874caa477b5bc0edee5845db3e9ce11ea6cfbd6012527636f6b07ad23fad45` 获得新授权。它在第 1 次 Provider request
以 `TLS_FAILURE` 密封关闭，exact attempt count 为 1，第 2 次调用没有发生；原始 prompt/response 与 credential 未持久化。授权已经消费，
不得重试，也没有形成当前 `@8` 的 PASS Result。

独立授权的 direct TLS diagnostic 随后完成一次 handshake：TCP connect 成功，但在 certificate verification 前以 `SSLEOFError` / errno 8
关闭；credential、HTTP request 与 application payload byte 均为 0。这排除了本次 DNS、TCP connect 和 CA verify 阶段失败，却不能仅凭
EOF 区分远端与 direct egress 路径。当前环境声明无凭据 loopback proxy `127.0.0.1:7897`，但存在性不是采用证据。

独立授权的 loopback proxy 对照随后成功完成唯一一条 CONNECT，但其唯一 verified TLS handshake 仍在 certificate verification 前以相同
`SSLEOFError` / errno 8 关闭；proxy authorization、credential、Ark HTTP request 与 target payload 均为 0。因此问题不是 proxy
不可达，也不能归因于 Adapter 禁用 ambient proxy；direct 与 proxy tunnel 的共同下游 TLS 路径当前不可用。

当时 live qualification 因 environment/external-state 进入 hold。verified TLS 路径恢复前，不改 Adapter、不启用 ambient proxy、不关闭
证书验证、不生成 Conformance run-003，也不申请新的 Provider 调用；Capability、hidden canary、正式 Web、SLICE-002、Production
Activation 与 push 继续不在授权内。详见 `FINDING-008-008`。

用户随后关闭系统代理并声明所有流量改走 TUN；单独冻结和授权的 TUN direct probe 仍在 certificate verification 前返回完全相同的
`SSLEOFError` / errno 8。模式切换没有构成路径恢复证据，hold 继续生效；后续必须先由代理规则、上游节点或网络环境变化产生实际 verified
handshake PASS，不能继续用 Conformance grant 或重复失败 probe 猜测。

用户更换节点后，独立 changed-node TLS diagnostic run-004 已取得一次 credential-free verified handshake PASS；随后唯一一次最小
`ark-code-latest` 模型诊断也 PASS，请求 identity 为 `ark-code-latest`，Provider response identity 为 `auto`，并返回
Adapter-compatible strict JSON。这只证明该时点替代路由与最小调用可用，不是 Adapter `@8` Conformance 或 Capability。

切回原节点后，original-node TLS diagnostic run-005 又得到与 run-001/run-003 完全相同的 certificate-verification 前
`SSLEOFError`；用户同时在全新无痕浏览器访问同一 endpoint 并收到 Ark HTTP AuthenticationError。因此问题范围是
Python/OpenSSL 与浏览器的客户端/路由选择性差异，不是 Ark 或节点对所有客户端全局不可用，当前证据也没有应用代码修复点。

用户随后决定更换模型 Provider。自该决定起不再生成 Ark freeze、发起 Ark 调用或修改 Ark Adapter/default model。Provider-independent
实现与确定性验证已闭合，当时没有需要为等待 Provider 而追加的产品代码；剩余 Conformance、Capability、正式 Web 和 canary 均等待新
Provider exact contract。新 Provider 不继承 Ark 的协议假设、资格或已消费授权；若其 endpoint、secret、TLS/proxy 或模型 identity 改变
System Contract/安全 Owner，必须先更新对应 System 文档/ADR。详见 `FINDING-008-009`。

用户现已指定新增 DeepSeek，并已把 API Key 配置到受控执行环境。独立 `DEEPSEEK` Provider 已冻结
`https://api.deepseek.com/chat/completions`、默认与期望响应 identity `deepseek-v4-pro`、可选 `deepseek-v4-flash`、
`env:DEEPSEEK_API_KEY`、direct verified TLS / ambient proxy disabled、no tools / no session / no retry 与 Adapter
`deepseek-chat-completions-no-tools@1`。该初始版本的 Adapter、独立 2-call Conformance、CLI 及 ITER-008 fake-transport Gate 已离线通过；没有读取真实
credential，也没有公网调用。正式 bounded runtime 与 product egress policy 继续保持 Ark，按用户要求先从新 exact candidate 冻结并
单独授权最小 DeepSeek model diagnostic，PASS 后才能依次申请 Conformance 与 Capability。详见 `FINDING-008-010`。

credential 先经一次无网络布尔检查确认为可见，密钥值未输出或持久化。随后 clean candidate `8cbb3ab…` 生成 model diagnostic
run-001 freeze `sha256:1c17dbe8…c6d9` 并取得 exact 单次授权；runner 恰好调用 1 次并返回 `MODEL_DIAGNOSTIC_PASS`，请求/响应 identity
均为 `deepseek-v4-pro`，input/output tokens 为 115/5。result/terminal digest 为 `sha256:42d1cacd…27b6` / `sha256:6202f52a…61c5`；
证据 digest、0600 权限和 secret/raw payload absence 复核 PASS，授权已消费且不可重试。该结果不是 Conformance 或 Capability。

写回后的 clean candidate `45fe1523b286f944cdc1ea781f49fe2bc5461da2`（tree `31fead7b…`）随后以 preflight
`sha256:243d154eb3d89072d947a9bd678fd52786ff847cee309cbc38e9ccdef452b3a6` 取得新的 exact 2-call 授权。runner 恰好调用 2 次并返回
`CONFORMANCE_PASS`：12/12 case PASS，响应 identity 仅为 `deepseek-v4-pro`，input/output tokens 为 378/87，usage 完整；result/terminal
digest 为 `sha256:390378f0…1d37e` / `sha256:4e81b650…54261`。六份 freeze/authorization/执行证据均为 0600，digest、资格有效期、授权消费、
无 retry 及 secret/raw payload absence 复核 PASS。

同一候选随后零调用生成 Capability freeze `sha256:ad1ba1fd75739e3dcbc5e127301bb0817a3cd6b3c3258af4d86782f6d7d72551`，但独立
`verify-capability-freeze` 在授权前因 verifier 未导入既有 metric contract 常量而触发 `NameError`。该 freeze 未请求授权，39-call
Capability 没有读取 credential 或建立 Provider transport。缺陷按 `FINDING-008-011` 以最小 import 和有效 freeze 正向回归修复；由于
修复改变 exact Git candidate，旧 Capability freeze 不得执行，下一步须从修复后的 clean candidate 重新完成同候选 2-call Conformance，
再形成新的 Capability freeze 和独立授权请求。

修复后的 clean candidate `3d2f35c35efe56edce7a1938afcc8e8acbb8425b` 以 preflight
`sha256:3a95fe038ac8ae8b8277187c0a8ea87516fc1f5d6688878dc2908af85eec8a36` 恰好执行 2 次 DeepSeek Conformance call 并 PASS；
result digest 为 `sha256:627ff4c9…16438`，唯一 response identity 为 `deepseek-v4-pro`。同候选 Capability run-003 绑定 freeze
`sha256:05267d91…7ce8`，在第 25 次 dispatch 以 `TLS_FAILURE / PROVIDER_OUTCOME_UNKNOWN` 密封关闭：24 次 request 和 11 个 Case
完成，没有 retry，不能形成能力裁决。

使用 Adapter 同一 CA fallback 的 credential-free 对照随后连续 5/5 完成 verified TLS 1.3 handshake；新 Capability run-004 绑定
freeze `sha256:94695257…c9292`，无 retry 地完成全部 39 次 request 与 18 个 Case，`unknown_count=0`。该 closed evaluation 只有
`WM-JSS-I8-FIRST-CANDIDATES-001` 与 `WM-JSS-I8-DRAFT-017` PASS，其余 16 Case FAIL；result/document digest 为
`sha256:b2308fac…f3ccca` / `sha256:6d698e84…1c876`，因此 Capability Qualification 与 Production Activation 均未形成。

逐 Case sealed output 证明主要缺口是 `prompt@4` 没有完整暴露 evaluator 使用的 canonical operation field shape、graph bounds、
result-driven progress 与三层完整性/Review 规则，而不是本次 Provider transport。按 `FINDING-008-012`，active bounded contract 正在
Provider-independent 地版本化为 capability/Strategy `1.3.1`、prompt/vocabulary `@5`、egress policy `@1.0.1` 和 suite/oracle
identity `@1.3.1`；18 Case、39-call、Oracle、metric、阈值与 no-retry 不变，也不加入 Provider/题目/工程特判。旧 live 证据保留但
不能授权新候选；下一步是在测试和文档闭合后的 clean exact candidate 上重新执行 Conformance，再执行一次完整 Capability Gate。

clean candidate `d9f401f290bd229f95e03853caa7e4089cf96873` 随后完成 run-005：Conformance preflight
`sha256:f4dc39bd…ab71b` 恰好执行 2 次并 12/12 PASS，result digest `sha256:9d2aa4a2…bb80ae`；Capability freeze
`sha256:5f8e0688…86750` 无 retry 地完成 39 calls / 18 Case，`unknown_count=0`，result/document digest 为
`sha256:27103346…a75775` / `sha256:aed052c6…fadd02`。该版本已有 13 Case PASS，五个 FAIL 为 declared inventory、legal finish、
max-four、budget exhaustion 与 Review，仍没有 Qualification 或 Activation。

按 `FINDING-008-013`，剩余失败进一步归因为 declared-set primary Need、non-null previous Result precedence、`remaining_budget=1`
仍可执行当前 query、Ref identifier 逐字符复制、正/负 FINISH precedence 与 Reviewer finding-code precedence。active contract 正在版本化为
capability/Strategy `1.3.2`、prompt/vocabulary `@6`、policy `@1.0.2` 和 suite/oracle `@1.3.2`；原 18/39、Oracle、metric、阈值与
no-retry 不变。完成 clean candidate 后只再执行一轮完整资格；若仍 FAIL，则停止无新证据的 Prompt 重复迭代并评估模型/协议替代。

clean candidate `6e443a324d2289321457b6d828163d0dc9005300` 随后完成 run-006：Conformance preflight
`sha256:03d02def…7990` 恰好执行 2 次并 12/12 PASS，result digest `sha256:b80972ae…df50`；Capability freeze
`sha256:e2e40a3c…6a767` 无 retry 地完成 39 calls / 18 Case，`unknown_count=0`，result/document/terminal digest 为
`sha256:85a51dc5…f99692` / `sha256:fa38bc98…73d3` / `sha256:884d6a35…5cf5`。该版本 12/18 PASS，六个 FAIL 为 N candidates、
result-driven batch、declared inventory、budget exhaustion 与两个 negative boundary，仍无 Qualification 或 Activation。

run-006 后的产品实现审查形成新的架构证据：模型正确选择 operation 时仍会重建并漂移 opaque Ref；旧 Oracle 同时要求
JAVA_METHOD 直接进入只接受 JAVA_TYPE 的 inventory、对同一 previous Result 按回合选择不同查询，并在真实零候选 Result 上伪造
scope Ref。正式 progress receipt 也缺少资格输入使用的三层 completeness projection。按 `FINDING-008-014`，System Owner 边界已改为
模型只提 semantic intent，Application 以 `java-source-semantics-investigation-argument-compiler@1` 编译 authority arguments；一个
executed Result 后即可显式 FINISH，使冻结的 2-call investigation 下界真实可达。active contract/Strategy 为 `1.4.0`、prompt/vocabulary
`@7`、policy `@1.1.0`、suite/oracle `@1.4.0`；18 Case、Oracle metric、18/18 threshold 和 no-retry 不变，显式合法 transition 使
exact call count 调整为 41。当前只进行本地验证，不再发起相同 Prompt Provider 调用；新的 live requalification、正式 Web、hidden
canary、SLICE-002 与 Production Activation 均未执行。

`1.4.0` 当前离线验证为 affected 117/117、18-case fake transport 41 calls / 18/18、full discovery 978/978、current documents
318/318 与 `git diff --check` PASS；full run 仅出现既有 SQLite connection `ResourceWarning`。这些结果不替代 live Capability 或产品
Gate。

`1.4.0` clean candidate `f056cb86b76ab3364208d9cfbba7f2562ed68688` 随后完成 run-007：Conformance 绑定 preflight
`sha256:c8e962711ce617f113e9589564b75eb00538e6e0b8506686a10394f5e1245ac0`，恰好 2 calls / 12 Case PASS，result digest 为
`sha256:26a6460003c7f930d99c139d5813efd6046523a46a19eea25f421962c1a09bd0`。Capability freeze
`sha256:975b195a060bbc51a5376dc80af0ad551d4a8c2eb46c72a8efb1fb07d3cd64a2` 在第 38 次 Provider request 已返回后，因
`NEGATIVE-REPRESENTATION-UNKNOWN-016:call-1` 的 12 个 search term 重复 `order` 而失败关闭。37 次 request / 15 Case
完整落盘，无 retry，failure/terminal digest 为 `sha256:82905e643b9c9968ce9d00f3b1e3f87c33a5a92d98ab24eaca4e39251ef174b5` /
`sha256:0f160da005c79fc488a1ff66b249dffe9c35788fc5b044cdeb43a84c7036a8df`。

已完整评审的 15 Case 为 10 PASS / 5 FAIL；证据将偏差分成 declared-inventory 与过早 FINISH 的模型缺口，以及三项资格
缺陷：可无损去重的 model-owned term 被当成整轮失败、单一 Oracle 拒绝合法短路径、独立 sealed-state 样本按 operation 名称误判
cycle。按 `FINDING-008-015` 升级到 capability/Strategy `1.4.1`、prompt/vocabulary `@8`、compiler `@2`、policy `@1.1.1`
与 suite/oracle `@1.4.1`。本地 affected 66/66、18-case fake transport 41 calls / 18/18 和 full discovery 980/980 PASS；新 live
Conformance/Capability 必须等 clean commit 后以全新 freeze 执行。正式 Web、hidden canary、SLICE-002 与 Production Activation 仍未执行。

`1.4.1` clean candidate `e299c097ee02dd89c404a368f070da9d546ba973` 随后完成 run-008：Conformance 绑定 preflight
`sha256:e031932adb843c4109a3920337d2502e406a71b28ff97d4db119388c599cb005`，恰好 2 calls / 12 Case PASS，result/terminal
digest 为 `sha256:e13ac784248589ec1b029a98fbe8a2515bebe8619275977d5d65b57921ba3d27` /
`sha256:a52bf779d5d4727805a359c5ee1f10b659f9e6f25de373e752e2fd6bbd073151`。Capability freeze
`sha256:ac0f0c6e76fe7b6bed003185b74622b9af6c6d88ab4a9b04380c97440916dca1` 在第二次已完成 Provider request 后失败关闭：
`ZERO-CANDIDATES-002` 返回 `declared_method_inventory` intent，但 sealed state 没有可绑定的 exact `JAVA_TYPE` Ref；仅首个 Case 完成并
PASS，无 retry，failure/terminal digest 为 `sha256:463cd849706040c44ee7f62bdfe2e37bcaa83177ea1651ac1799ea000e8e89c4` /
`sha256:7b8cdbd8ab55a5b12f8f39c665cf16597f3a8029109b21ccf32c92e722535416`。

按 `FINDING-008-016`，不再修改 Prompt、suite、Oracle 或 threshold。代码审查确认 DeepSeek Adapter `@1` 未发送或冻结
temperature，因此实际继承 Provider 默认值 1；活动 Provider protocol 升级为 `deepseek-chat-completions-no-tools@2`、Conformance
fixture `1.0.1`，固定 JSON numeric `temperature: 0` 并纳入 configuration fingerprint、公开状态、sanitized Result 与 live wire
检查。旧 `@1` Result 全部 stale。定向 40/40、full discovery 981/981、current documents 320/320 与 `git diff --check` PASS；
完成 clean commit 后只执行一次全新 run-009 Conformance + Capability；若仍未达到 18/18，停止继续调整 Prompt 或 Provider 参数。
正式 Web、hidden canary、SLICE-002 与 Production Activation 仍未执行。

temperature-zero protocol repair 的 clean candidate `5d2bce381e9c9495571c148a69c3fb43ee3f6dc8` 随后完成最终 run-009。
Conformance preflight/result/terminal digest 为
`sha256:7408d2ee7f49d4f3ff83b93321510e38003d9da4436af77f1bb0d2a485860d4e` /
`sha256:c2b999fb4c313e0913a49284ddb3783672761fd6155924f9a7154a0d6298db76` /
`sha256:197a15e21fa90d2e001db8fe0cdb1357c2abf0537adbf29cf7fd64a90bb873c1`，恰好 2 calls、12/12 PASS，证明 Adapter `@2`、
fixture `1.0.1`、temperature 0 与 `deepseek-v4-pro` exact identity。

同候选 Capability freeze `sha256:d436a104be64ef22caf8f499c950863b36cecf12cede1fb4c624b14e1a6eec35` 在前 7 Case
independent Review 全 PASS 后，于 `ALL-SIMPLE-PATHS-008:call-3` 失败关闭。18 个实际 Provider call record 均已 `COMPLETED`；最后一次
semantic intent 选择 `all_simple_paths` 并携带只属于 direct-neighborhood 的 `BOTH_CALLS`，旧 compiler `@2` 因此拒绝该响应。
failure/terminal digest 为 `sha256:beadc9bbca1544bebcf29620a13b98128e65bdcc9c72364515c1fc2a38e763fb` /
`sha256:99fc7923db8696f4a3a3b81ac5960459b81698737597a2a0325d82a28e4f422c`；无 retry、Qualification 或 Activation。

按 `FINDING-008-017`，预提交的最终资格尝试已经耗尽：不创建 run-010，不再调整 Prompt、Provider 参数、compiler、suite、Oracle 或
threshold。V-WEB-001、hidden canary、SLICE-002 和 Production Activation 继续阻断。后续必须先取得新的显式 redirect decision：恢复
Ark Python/OpenSSL verified TLS 路径、选择另一个独立资格模型，或重新设计 constrained transition 协议。

用户随后以 `codex-user-message:sha256:375246d919e8541021acd7b319f13d5af928794ff23a022ae01a82531a09a8e2`
作出所需的显式协议 redirect：集成层适配模型，不能要求模型替平台维持每个 operation 的内部 null shape。按 `FINDING-008-018`，
`operation` 成为 fixed envelope 的 semantic discriminant；Application 只解析该 operation 拥有的 slot，确定性丢弃其他 slot，同时
继续严格校验适用 slot、transition、Ref provenance、predicate、bounds、budget 与 closed shape。compiler 升级为 `@3`、Gateway
policy 为 `@1.1.2`；capability/Strategy `1.4.1`、prompt/vocabulary `@8`、suite/oracle `@1.4.1`、18/18、temperature 0 与 no-retry
不变。run-009 作为旧 compiler 失败证据保留且不 retry；新 clean candidate 完成本地验证后须以全新 freeze 重新执行 Conformance 与
Capability，PASS 前 V-WEB-001、hidden canary、SLICE-002 和 Production Activation 继续阻断。

compiler `@3` redirect 的本地闭包现为：定向 contract/compiler/policy/fake-live-harness 54/54 PASS，其中 fake transport 以 run-009
原始 `all_simple_paths + BOTH_CALLS` 输出完整执行 41 requests / 18 Case 并 18/18 PASS；full discovery 982/982 PASS，仅出现既有
SQLite connection `ResourceWarning`；current documents 322/322、`git diff --check` 与 credential-shaped secret scan PASS。上述结果
不是 live Qualification。下一步是 clean commit 后生成全新同候选 DeepSeek Conformance preflight，不复用 run-009 的任何 grant。

compiler `@3` clean candidate `4e79a126faf8c6992c1649ad8f82150d69cd414d` 随后完成 run-010。Conformance 绑定 preflight
`sha256:60ac01be1f28d5766256fa1eb5c2996500683bb90e90dcfd90d48e7acd822a9a`，恰好 2 requests / 12 Case PASS；result/terminal digest 为
`sha256:a145a64ba15f49a14825f95c13accb58424f6ffe2b388f2b9b82663bef82075b` /
`sha256:326bd75035792d20634f8a1ad3db550dc920532b131cbd9230c96ed5719ac056`。同候选 Capability freeze
`sha256:9e425d2fec706658d6574305730ff20cc37ee45a1824f0b1ac2e6eca6ec8fcfb` 无 retry 地完成 41/41 requests 与全部 18 Case；唯一 response
identity 为 `deepseek-v4-pro`，usage 完整，tokens 105,890/2,680，`unknown_count=0`。closed Result 为 16/18 FAIL；result/document/
terminal digest 为 `sha256:47436f2f24eb39cf359dba08c1437a35c93aebe67daedd0447daf235f3d1a193` /
`sha256:341777308d364d2732c528c1d705cd9b823702c960119f4bf0980bdf65bab9dd` /
`sha256:3937818ae9f39677945592dbb6a68a685b0fc68fd1b24c1f66711779e74135ff`。run-009 的 slot 反例已 PASS；仅 `MAX-FOUR-010` 第 3 回合和
`BUDGET-EXHAUSTION-011` 第 4 回合提前 FINISH，分别遗漏 direct CALLS 与 all-simple-paths。合法 method-only FINISH 同时 PASS，故不能
用固定多查一步修补。

按 `FINDING-008-019`，该证据被分类为终止 Owner 的 system-contract 缺口，而非模型、TLS、identity、shape 或 Ref 问题。用户既有
`codex-user-message:sha256:375246d919e8541021acd7b319f13d5af928794ff23a022ae01a82531a09a8e2` redirect 要求平台适配模型；Application
现以通用 evidence obligation ledger 约束 transition/FINISH，不含问题、工程、符号或 evaluator 特判。活动版本升级为
`1.5.0/@9/@4/@1.2.0` 与 suite/oracle `@1.5.0`。当前 targeted contract/product/capability/Gateway/runtime 回归 96/96 PASS，fake
transport 完成 41 calls / 18/18，current documents 324/324 PASS。允许 AF_UNIX listener 的完整执行面为 980/985；其余五项全部由
当前桌面 Codex CLI `0.148.0-alpha.15` 与 ITER-003 frozen `0.147.0-alpha.1.2` 的 exact binary drift 触发，已按
`FINDING-008-020` 保留 fail-closed，未改写历史 freeze，也不把 full suite 写成 PASS。该独立环境 hold 不阻断新的 DeepSeek
Conformance/Capability requalification；clean commit 与 live 18/18 仍待执行，正式 Web/canary/Activation 继续阻断。

上述本地闭包形成 clean candidate `ab87c442218a06292829c0508963508d88d54119`（tree
`190b186656fe3cd29c55d04cb8987cdeb06d5821`）并执行 run-011。Conformance preflight/result 为
`sha256:5661c28fde972b366f89aeb92093acac703a2dbdd83dc6180325df6c4f8c43ee` /
`sha256:32ff8a4a3a45b55a229c60bfe28486937e6eb24aca3cdb587289a7db4bc1d464`，恰好 2 requests / 12/12 PASS，唯一
identity `deepseek-v4-pro`，tokens 381/79，usage 完整。Capability freeze
`sha256:f708e49f453a14959b588be3c91424dccb6f20d5320f4ab10fc6b65a4b7407f8` 的前 14 Case / 35 accepted calls 全部
independent PASS；第 36 次 request 已由 Provider 完成，但 `NEGATIVE-QUERY-UNKNOWN-015:call-1` 因模型将“是否实现”解释为
`implementation_candidates` evidence、而冻结 ledger 要求 method evidence，在本地 exact obligation 校验失败。failure/terminal
document digest 为 `sha256:5e9d8a7199bafb8dd46deba170faf2c1f0fe0d4fd59905debc78d2f9f7bc7a6b` /
`sha256:c2847e3fc0597ae503cfc69f3353530099ef341246a1034103cb0c7c6842dbfc`；无 retry、Qualification 或 Activation。

按 `FINDING-008-021`，candidate operation 是每题强制 prerequisite，不应同时充当非零候选可终止 evidence class。Application 现把 raw
candidate evidence alias 无条件向上归一为 `method_implementations`，不读取问题、Case、工程、符号、Oracle 或未来 Result；graph/
inventory 依赖收敛和零/截断候选 Limitation 不变。活动版本升级为 `1.5.1/@10/@5/@1.2.1` 与 suite/oracle `@1.5.1`。当前相关
回归 116/116、其中 Gateway AF_UNIX 12/12，fake transport 41 calls / 18/18，current documents 325/325 PASS；完整回归仍为
980/985，唯一五项是 `FINDING-008-020` 已隔离的 ITER-003 Codex CLI exact-binary drift。compileall、diff check 与路径级 secret scan
也已通过。`FINDING-008-021` 已处置；clean candidate 与全新 live requalification 仍待闭合，所有后续产品 Gate 继续阻断。

上述版本形成 clean candidate `5ef09d4f29f538fc40985613c963d9c29bd2ee15`（tree
`f912744582d4864c26697295668a9560a07f21d1`）并执行 run-012。Conformance preflight/authorization/result digest 为
`sha256:51d892770d777073e3337e074122b22acc6954610a1d5e357e73894a9442ecec` /
`sha256:15dca55301643f148755998f609ea3a66427d74f04eb4712338754c320edbbca` /
`sha256:f50ea41a6ec5502df6a7cc90e840d52e3474b5f78b3c593e0f58672f8b69715c`，恰好 2 requests / 12/12 PASS，唯一
identity `deepseek-v4-pro`，tokens 376/86，temperature 0、thinking disabled、usage 完整。Capability freeze/authorization 为
`sha256:4964298813d036ee59e2ffec7fd9013a88e4d16ac557c1703c4ca4ec5bd61d93` /
`sha256:4f7758ff216cec47be4bfdd7d1f0eecfe36c000bef26f4938718d9a35e573ed8`；前 9 Case / 21 calls 全部 independent
PASS，第 22 次 request 完成后 `MAX-FOUR-010:call-1` 因 raw method evidence 与 frozen outgoing-direct ledger 不一致失败关闭。
failure/terminal digest 为 `sha256:58c1a33c3fb458db0dd592c1871072dac6a6ec815f7aaba5ca57350ed8d9382a` /
`sha256:fabb08a4731f4d2d6d5b8f1890f203e887048229c57e9edec29f149dd7b03f4c`；无 retry、Qualification 或 Activation。

按 `FINDING-008-022`，正式 method Result 已密封同方法的 outgoing `CALLS`、direction、Coverage 与 Support，追加 standalone
`direct_neighborhood(OUTGOING_CALLS)` 是重复查询。Application 仅按 formal operation/relation 将该 alias 收敛为 method，不读取问题、
terms、工程、Case、Oracle 或未来 Result；path/incoming/both 继续保留。活动版本为 `1.5.2/@11/@6/@1.2.2` 与 suite/oracle
`@1.5.2`，closed evaluation `@1.0.2` 固定 18 Case / 40 calls。相关 DeepSeek/Gateway/runtime/product 回归 169/169、fake transport
40 calls / 18/18、current documents 326/326 PASS；完整回归为 980/985，唯一五项仍是 `FINDING-008-020` 已隔离的 ITER-003 frozen
Codex CLI drift。compileall、diff check、路径级 secret scan 与两套 System Contract fileset digest 重算均通过，`FINDING-008-022`
已处置。

上述实现形成 clean candidate `a93666ce51f24149a487581a3c12283691cbd14b`（tree
`e3ffdb9d72aa1202a6029a5202db20af3178ad8b`）并完成 run-013。Conformance preflight/authorization/result/terminal digest 为
`sha256:38a95bcddae1bbb03de98c419d8577cd98903560ecbca681524b2379f9ce467e` /
`sha256:1c0225c7420bcea9634a805bc1a1181a73f29ed28c8906bce5ce569f8bb6d1cf` /
`sha256:8505983e13d9e2ab4ec9fbeec6b92b2cc9369fb89f921582457fd8703146c2c1` /
`sha256:cb4cd8efd219e18ea88d0a78ae6f34cb5410daa38863e96780ef18dd393fb6ad`，恰好 2 requests / 12/12 PASS，唯一
identity `deepseek-v4-pro`，tokens 374/86，temperature 0、thinking disabled、usage 完整。

Capability freeze/authorization/result/qualification/terminal digest 为
`sha256:11524d4c219c13c8593cbdfb499e2b23c809b3cfdcf56eb4e06d3adddf9b469b` /
`sha256:d56412847278bdf15ba59522dede32c4eebfb6594c7a7271616ebd6a3f602fbb` /
`sha256:b05583d6edf669008253618c0bd3cd2c872da037da33a8dacae3c46f2ee1ca25` /
`sha256:61f18bd62d217ad68ac778a5aa4e8537eff180f4009067a75c8e2c011102a0c1` /
`sha256:e5200a15709585be50f6cb4c56a5f3ff7087f0e53bc8483518a58bc48cdab7fd`。它恰好完成 40 requests / 18 Case，
18/18 independent PASS、failure/unknown 均为 0，唯一 identity `deepseek-v4-pro`，tokens 103471/2909、usage 全部完整；无 retry、
hidden canary disclosure、正式 Web 或 Production Activation。资格有效至 `2026-08-27T05:19:50.677774+00:00`；V-002 因而 PASS，
下一个阻断是正式 runtime/Web 的公开回归、隔离与安全 Gate，随后才可烧录 early canary 和执行独立 Agent 对照。

`FINDING-008-023` 随即暴露下游边界：正式 bounded egress policy、Gateway workload、socket supervisor 与 runtime 仍把 Ark 写死为
唯一 Provider，不能消费 DeepSeek qualification，也不能把 DeepSeek Result 错配给 Ark。当前实现已把该要求闭合为 dispatch 前的
exact qualification route selection；本轮 Ark 没有 `1.5.2` current qualification，因此选择 DeepSeek。DeepSeek exact endpoint、
Adapter/model/fingerprint、selected-only credential、内部 host registry、TLS SNI/certificate、exact path、4—6 calls 与
unused-close audit 已贯穿 policy/grant/Answer/Gateway/runtime，历史 fixed Profile 仍保持 Ark。

`FINDING-008-023` 阶段已确认 Gateway connection policy 是 Capability Contract 的资格身份之一；当时的 loader 要求 closed
Definition 同时绑定 DeepSeek Adapter `@2` 和 model-egress policy `@1.3.0` 的 exact digest，因此 run-013 不能授权该阶段 product
route。后续 `FINDING-008-024` 又使这些身份失效；正式 Web、early canary、Agent 对照、Reflection、SLICE-002 与 Production
Activation 始终继续阻断。

该 route 的 clean candidate `5ffb6ef1def72be56c3343d2fc97a4398208fd16` 随后执行 run-014：Conformance 2 requests / 12/12
PASS；Capability 前 3 Case / 3 requests PASS，第 4 个独立 TLS session 在 certificate verification 前 EOF。独立 run-015 前 5 Case /
9 requests PASS，第 10 个 session 同样失败。两个 authorization 均已消费、均以 `PROVIDER_OUTCOME_UNKNOWN` 密封，不得拼接或重试。
credential-free 对照显示短序列 4/5、随后 12/12 verified TLS PASS；同一 verified connection 上两次无凭据 HTTP 均返回 401、
`Connection: keep-alive`、`will_close=false`。证据将根因定位为当前 TUN 对大量独立 TLS session 的间歇 EOF，而非模型、Adapter wire、
Oracle 或 evaluator。

`FINDING-008-024` 因而把 TLS acquisition 与 Provider request 分开：direct qualification 和 pinned product transport 都显式持有 verified
TLS session；在 credential/Authorization/HTTP 前最多顺序尝试 3 次，HTTP dispatch 后仍零 retry。正式 Capability closed Result 必须
记录 40 HTTP dispatch、TLS attempts/successes、connection reuse、credential resolution、post-dispatch unknown 与
`request_retry_count=0`；product Gateway 预置 3 个 exact connected descriptor，并闭合
`provisioned = TLS attempts + unused_closed`。该改变把 Adapter 升至 `@3`、egress policy 升至 `@1.4.0`，旧 run-014/015 只保留失败
证据。写回后的 `ITER-008-SYSTEM-CONTRACT-SET@1` digest 为
`sha256:b1193e2a97f8c4c8db26dd2d3cbe98ff0b8fb7d6e8414fb15b71d1e0536b5df7`；共享文档使 ITER-007 fileset 同步重算为
`sha256:248d4d51411856640aa60af5299771b08514540ae17819cef129753f37997d2a`。核心 50/50、跨模块 89/89 与 Gateway 13/13 PASS；完整执行面
1010/1015，唯一五项仍是 `FINDING-008-020` 的历史 exact runtime drift。`compileall`、diff check 与本地实现门禁已经闭合；新的 exact
clean candidate 和 live Conformance/Capability 资格仍待完成；docs gate 328/328 PASS。

上述 persistent candidate 形成 clean commit `139e61c94f218a6076022f1863cf871b2d3104f2` / tree
`efb2cd48b6fb02365ab2a2544f3a5e9adec890cf` 并执行 run-016。Conformance preflight/result digest 为
`sha256:6af24a38abc6292787f7abc2f714669827877b2c6ddf85150d0a1480fbaba63a` /
`sha256:9e035d75899140ecb02f5513666b16ff09f72f5490ff8c259201353aa8c1d83b`，2 requests / 12/12 PASS；transport 只完成
1 次 verified TLS handshake、复用 1 次，HTTP/credential 各 2 次，unknown/retry 为 0。随后 Capability freeze
`sha256:63151e87fc13d241b1586429276dfd8269af8c9f59f10f9b09e67e263c13f43d` 前 6 Case / 12 requests 全部 PASS，第 13 次
已完成 request 在 `PATH-EXISTS-007:call-1` 因 raw method evidence 不等于 frozen `path_exists` ledger 而失败关闭；transport 此时仍是
1 次 TLS、12 次 reuse、13 次 HTTP/credential、unknown/retry 为 0，授权已消费且不可重试。

`FINDING-008-025` 将根因限定为 DeepSeek instruction rendering：旧 Adapter 先发送 schema system，再发送任务 semantic system；失败
输出同时包含 reach/path，却选择 method，并复制了只在 prompt 示例中的 direct/all/method/implementation/candidate。Application 和
evaluator 保持 exact，不读取问题、Case 或 Oracle。活动 Adapter `@4` 改为单一 leading system authority；Contract `1.5.3/@12` 明确
只应用当前 capability section、示例词不得凭空复制，以及显式 reachability 即使提到 static calls/trace 仍选择 `path_exists`。
Conformance fixture `1.2.0`、policy `@1.4.1`、suite/oracle `@1.5.3` 随之重冻结；完成本地门禁和全新 live qualification 前，V-002 对
当前身份重新 blocking，正式 product freeze/Web/canary/Agent/Reflection 与 Activation 均不得开始。当前
`ITER-008-SYSTEM-CONTRACT-SET@1` digest 为 `sha256:c9992a431726a48274355d1075187311471c40bea6efbb51de1c7b3ff9e14968`。

该候选形成 clean commit `e3cc34fdd830498414480684151944139ca9489c` / tree
`0d83e59ed273c2f6c01dba977f2089576eda2da2` 并执行 run-017。Conformance preflight/authorization/result digest 为
`sha256:7dbff2868c58e8582e44e3fd989282430dc762d13c529607ab6f4a0a3c2a9dad` /
`sha256:901b6a9158beae9fab35f921e6617939859908d5349c67a2d62fbaba7ea96875` /
`sha256:f17c58dd13ece22e3bf7da216119fb2e00d552fed7bd31e9bec23accb98d02f4`，2 requests / 12/12 PASS。Capability
freeze/authorization `sha256:38d07801b13fa581fc7d82120cc1bd319202862b76a79b044895b2a96fb86deb` /
`sha256:d4f9518043a0c6c030e3a74b60267f50216f43efb5ebd4d69dd35216f41dad2f` 已消费；旧 PATH-EXISTS Case 完整 PASS，但前
9 Case / 21 calls 后，第 22 次 completed request 把 workflow trace 误选为 binary `path_exists`。失败时 TLS 1/1、reuse 21、
HTTP/credential 22/22、unknown/retry 0；failure/terminal 为 `sha256:9877b420…793d` / `sha256:c1c50229…05a59`。

`FINDING-008-026` 证明自然语言声明非当前 section “inactive” 不是输入隔离：实际 Investigation Manifest 仍携带 legacy Query
Planning、Draft 与 Review 文本，并从中复制 `order/return/throw/audit`。活动 Contract `1.5.4/@13` 现为三个 capability 冻结独立
prompt entry，Manifest 前按 sealed stage 选择并绑定 `capability-prompt-selection@1`；Gateway 校验所选 digest。workflow trace 与显式
binary reachability 的通用判别也已闭合。Adapter `@4`、fixture `1.2.0`、compiler `@6`、18/40、Oracle、persistent TLS 与 no-retry
不变；policy/suite/oracle 分别升级为 `@1.4.2/@1.5.4`。新 clean candidate 完整资格前，V-002 与全部产品 Gate 继续 blocking。
相关回归 121/121、fake 40-call / 18/18、current documents 330/330、compileall/diff/secret scan PASS；完整执行面
1012/1017，唯一五项仍是 `FINDING-008-020` 的历史 ITER-003 runtime drift。当前 System fileset digest 为
`sha256:0143229ee22d1db3962e6bc6fedf7982fea96642fe84d1f116667f3b144219a5`；这些本地结果不替代 live qualification。

上述变化形成 clean candidate `51c8ac369b29b609d6a5dcf53f55370a0cb49f04` / tree
`10abd04fd45fdd13a156fac9349a7a6e21690d8b` 并执行 run-018。Conformance preflight/authorization/result digest 为
`sha256:5e1d00112eb592e68b3e8861c1a99a8d88d83b38e0456e05badc436d3b477934` /
`sha256:eb8b08aea2f44cafb0fbbfef4ceabb35160cf7dc4d6e7851ae366d728f6341c2` /
`sha256:e5ac81e07a36badc53c34699e262168b2ca2052d1503d9d25e2ea71eb37f4727`，2 requests / 12/12 PASS。Capability
freeze/authorization `sha256:93cef5a0c2315ed6bc603ee6a9ae5a327a120d5bb3781010f85f8d3f75ac059d` /
`sha256:b41bad4b7a56553b9601b102cc856a7db3c35b8157a5cb13671dbe860b9f3d2a` 已消费；40/40 request 与 18/18 Case 均完成，
transport 为 TLS 1/1、reuse 39、HTTP/credential 40/40、unknown/retry 0，但 closed result 为 16/18 FAIL。result/closed/terminal
digest 为 `sha256:6cd3f4f8…2459e` / `sha256:4fe292ac…99f04` / `sha256:39a86a2d…8cbf2`。

两个失败的 operation、Application compiler、typed projection、第二步 Result/Ref provenance 均 exact；唯一偏差是首轮 search term。
REF-PROVENANCE 的模型输出遗漏原问题明确包含的 `implementation`，属于 question concept 与 instruction vocabulary 重叠时的 Prompt
来源判定歧义。RESULT-DRIVEN-BATCH 的模型输出覆盖原问题全部 material concept，旧 suite 却额外要求未请求的具体
`return/throw` 机制，属于产品不真实的 evaluator 假阴性。按 `FINDING-008-027`，System Contract 现要求按原问题语义来源而非词面
overlap 判断 term provenance，资格 semantic constraint 不能把一种可能实现机制提升为唯一等价表达。活动身份为
`1.5.5/@14/@1.4.3`、suite/oracle `@1.5.5`；operation Oracle、18/40、18/18、Adapter `@4`、compiler `@6`、persistent TLS 与
no-retry 不变。当前 System fileset digest 为 `sha256:948647ad…7aaa4`；共享文档使 ITER-007 fileset 同步重算为
`sha256:cec082d8…331b`。相关回归 117/117、fake 40-call / 18/18、docs 331/331、compileall/diff/secret scan PASS；完整执行面
1013/1018，唯一五项仍是 `FINDING-008-020` 的历史 ITER-003 runtime drift。run-018 永久保留为 FAIL；clean commit 和全新
run-019 完整资格前，V-002 与全部产品 Gate 继续 blocking。

本地闭包形成 exact candidate `6dc7a9e4c9e24dc901c95088c549441fc1b8497c` / tree
`229d11d186e986c8b1746d901f81f574e808b59a` 并执行 run-019。Conformance preflight/authorization/result/terminal digest 为
`sha256:18cc7ea9e470d1dc983805090f43cc789a7f94dbef1bc6223ca0b32c5c34d4d3` /
`sha256:c36214d5c7418a4e0a0f3b6c507f889125f1ba0dcba4673f5230e5412cc06ebb` /
`sha256:c3ce93867fcc180573fd0c3a7391fb64c866e48839cc31ad5687b76380e1120c` /
`sha256:507ef67670c0ac2c783eac20c0e664671e20c937001c4324975e0dab05a0dc6a`，2 calls / 12/12 PASS，tokens 405/67；
TLS 1/1、reuse 1、HTTP/credential 2/2、unknown/retry 0。

同候选 Capability freeze/authorization digest 为 `sha256:a7e99c16730c60cd977cec3cee8da0ca330e1b1d437b6f03c0d464540aba386e` /
`sha256:e2a112334c8e2352b5859ceb0134841a1e02a76706da7eadcf00ec2f5ef393ee`。它无 retry 地完成 40 calls / 18 Case 并
18/18 PASS，tokens 78,618/2,602；TLS 1/1、reuse 39、HTTP/credential 40/40、unknown/retry 0。result/closed document/
qualification proof/document/terminal digest 为 `sha256:16e9e6bc…5020b` / `sha256:17422796…42528` /
`sha256:7e460107…224fc` / `sha256:b0ec3ad1…e556` / `sha256:a1cd6fb6…981f`，valid until
`2026-08-27T09:09:31.851862Z`。run-018 的两个目标 Case 分别返回 question-owned
`authentication/failure/success/flow` 与 `authentication/candidate/returned/complete/implementations/inspect`，semantic constraint、
operation、typed projection 和 Ref provenance 全部 PASS。全部证据文件为 0600，credential-shaped secret scan 无命中；授权均已消费，
hidden canary 与 Production Activation 均未执行。V-002 对当前 exact Contract 已 PASS；下一步是写回后以 current qualification 生成
SLICE-001 正式 product freeze，不直接进入 canary 或 Activation。

正式 freeze 审查随后暴露 `FINDING-008-028`：旧 producer 既要求完整 suite exit 0，又必须原样保留 `FINDING-008-020` 的五项
historical exact-runtime hold，形成机械死锁。当前 deterministic qualification 升级为 bounded-route-only `@2`，raw suite 仍如实为
FAIL；只有五个测试各执行一次、精确 4 FAIL + 1 ERROR、原因 marker 相等且其余测试全部 PASS 时，gate 才记录
`PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD`。任何新增/不同失败继续阻断，旧 `@1`、历史断言、canary/Acceptance/Activation 边界均
不变。System fileset 已重算为 ITER-008 `sha256:80b5393b…b311` / ITER-007 `sha256:3f25570e…4819`；首次 full 验证在 digest 写回前
正确拒绝了第六项 readiness failure。重算后的定向门禁 22/22、完整执行面 1021/1026；raw exit 1，唯一五项精确 hold，结构化
gate PASS。下一步形成 clean candidate 并生成正式 product freeze。

该 formal product freeze 随后 PASS，但第一次公开 Web 登录问题在唯一一次 DeepSeek request 后因 Query 的 ASCII-only tokenizer
失败关闭；`FINDING-008-029` 将 Query 对齐 Unicode Contract，并加入真实 cross-script Capability Case。由此产生的 run-020 完成
Conformance 2/2，但 Capability 在第 33 次已完成 request 后停止；中文 translation 已正确，剩余证据暴露旧 equivalence、一般疑问
evidence intent 与 direct Latin term 约束歧义。`FINDING-008-030` 将活动上游重冻结为 `1.5.7/@16` 与 suite/oracle `@1.5.7`。

run-021 随后完成 40 calls / 18 Case，15/18；三个失败只是在首轮省略被 operation/evidence request 表达的
`reach/method/implementation`。`FINDING-008-031` 曾把 lexical-coverage 显著性重述放入 Adapter `@5`。该处置的 exact candidate
`c925496…` 又完成 run-022：Conformance 2/2 PASS，Capability 40 calls / 18 Case、16/18，TLS 1/1、reuse 39、HTTP/credential
40/40、unknown/retry 0。PATH-EXISTS 已 PASS，CYCLE-PROGRESS 与 REF-PROVENANCE 仍遗漏 direct
`methods/implementations`；run-022 result/closed/terminal digest 为 `sha256:e47b0ade…dfc1c` / `sha256:49a22c81…d339d` /
`sha256:1de7e387…636ad`，没有 Qualification，授权已消费且不可 retry。

按 `FINDING-008-032`，Adapter-owned disposition 已被取代。活动 compiler `@7` 从完全 ASCII 原问题机械合并 direct question terms，
raw response 保持审计，cross-script translation 仍由模型负责；Adapter 移除领域 adaptation 并升级为 `@6`，policy 升级 `@1.4.7`。
本地相关 127/127、fake 40-call / 18/18、current documents 336/336 与 compile/diff/secret scan 已 PASS；完整执行面
1024/1029，raw exit 1，唯一 4 FAIL + 1 ERROR 精确属于 `FINDING-008-020`，没有新增失败。下一步只能从新 clean exact
candidate 执行 run-023 Conformance 与 Capability；PASS 前不得生成 formal product freeze、继续 Web、披露 canary 或执行 Activation。

新 clean exact candidate `837171e611ae6e1dd3a0939e446e0658b1d08d6c` / tree
`11b4a2a083d1e1c0f239e0a132e61cd125cd12ec` 已完成 run-023。Conformance preflight/authorization/result/terminal digest 为
`sha256:c7c730f556e994c7b3278a35104c47a631e46dd84997122f95c1133783813703` /
`sha256:fbc6a8c70f7d3b6bd19f17e636591459bc10c0ac700b1450838b3ee94264b93c` /
`sha256:16e947ad1aaf698227ae59f06db3ec53caca04eb9f1c46375adf6ae1bd960522` /
`sha256:5eb114c04f745b46137c4408ed16788be92d7979f0e4c1630a9b33ac342077fb`，恰好 2 requests / 12/12 PASS；TLS 1/1、
reuse 1、HTTP/credential 2/2、unknown/retry 0。

同候选 Capability freeze/authorization digest 为
`sha256:7bfd08c6307314a15b7f0d41e666d559154f7906c9818f4296ac5937fb724cae` /
`sha256:fdf3e0e23cc7010225e9d3e952dbc6390e051e7cc63578744d25bbb37ec0b43d`。它无 retry 完成 40 calls / 18 Case / 18/18
PASS，input/output tokens 84,396/2,560；TLS 1/1、reuse 39、HTTP/credential 40/40、unknown/retry 0。result/closed/
qualification proof/document/terminal digest 为 `sha256:9306f487…ba6d` / `sha256:d17e6d67…d977` /
`sha256:0c78cb15…0c31` / `sha256:15f4d4f1…148ba` / `sha256:c2175a9b…563`，valid until
`2026-08-27T11:28:37.309517+00:00`。CYCLE-PROGRESS、REF-PROVENANCE 与 PATH-EXISTS 分别保留
`methods`、`implementations` 与路径直接词项，semantic constraint/projection 全部 PASS。授权均已消费且不可 retry；
hidden canary 未披露，Production Activation 仍为 `NOT_EXECUTED`。V-002 因而已 PASS；下一步从证据写回后的 clean
producer 生成绑定该 qualification chain 的 SLICE-001 formal product freeze，不直接进入 canary 或 Activation。

随后生成的 formal `run-004-freeze` 已通过 focused 88/88、candidate package 37/37、raw full 1024/1029 与精确历史 hold Gate、docs
和 unauthorized-prelisten；report/grant digest 为 `sha256:909c8d4b…7352` / `sha256:95a2562d…334f`。authorized Web startup 的
preflight/receipt 为 `sha256:61ae7e8f…29e` / `sha256:cfc86952…2b30`，但浏览器在任何问题 POST 前仍显示旧
`3 次模型调用`，且代码审查确认 public validator 也固定期待 3 calls。会话 request 目录为空，模型调用为 0。

`FINDING-008-033` 将该偏差归类为既有 4—6 call System Contract 的本地实现漂移。修复提交
`41b766a179bcc1bf78aed3278f6687a5e1c15abd` / tree `e78427b474dc401308f1f69a0fe1adfb68b00e37` 现以已校验 startup
`dispatch_policy` 统一驱动 Web 披露与 public result boundary；bounded 4/5/6 接受、3 拒绝。定向 21/21 与包含 ITER-008 focused 的
109/109 PASS。旧 run-004 freeze/grant 因 product identity 改变不得继续使用；下一步是从写回后的 clean candidate 全新 formal
refreeze，再执行公开登录/下单 Web。run-023 qualification chain 未被改写，hidden canary 仍未披露，Production Activation 仍为
`NOT_EXECUTED`。

run-005 refreeze 随后以 source snapshot `f7796993…`、focused 88/88、candidate 37/37、full 1025/1030 与精确历史 hold Gate PASS；
report/grant 为 `sha256:93200c78…a7ff` / `sha256:72949de7…84d`。startup receipt `sha256:869287ec…8a00` PASS，页面已正确显示
4—6 calls。首个登录题却在 560 ms 内失败，terminal `sha256:5288b0c2…a791` 的 Gateway role 在接受请求前为 `RuntimeError`：
packaged bounded workload raw SHA-256 为 `af5059c2…e3c3`，authorized wrapper 仍 pin 旧 `ac0cf321…f49c`。Gateway network audit、
credential、TLS、HTTP 与模型调用均为 0；Source/Update/Direct/Evidence payload 访问为 0，browser console clean，后续问题未执行。

`FINDING-008-034` 以提交 `54bc8c8fa7d2ab9709191d448dbd7509c3aa4095` / tree
`4cc184e1c61178cd825904271777774c1dea5cf7` 同步 self-integrity pin，并新增三份 current packaged Gateway entrypoint 的直接 file/hash
回归，gateway/freeze 14/14、扩展 focused 110/110 PASS。System exact-integrity contract 未改变。旧 run-005 request 不 retry，且其
freeze/grant/session 因 launcher identity 改变不得复用；下一步仍是全新 formal refreeze，再从登录题开始。hidden canary 未披露，
Production Activation 为 `NOT_EXECUTED`。

formal run-006 随后完成 3 个 Investigation 与第 4 个 DeepSeek Draft HTTP 200；Draft 语义正确，却因旧契约要求复制 4 个 Result ID
和 35 个 support digest 在 1000 tokens 截断。`FINDING-008-035` 把 Draft/Review exact authority collection 收回 Application：模型
raw envelope 必须为空，terminal compiler `@1` 注入 sealed exact 值；上游 identity 升级为 `1.5.8/@17` 与 suite/oracle `@1.5.8`。

exact candidate `1725b44e8c92382eaa7c288919a25139934d0d80` / tree
`79a748a9a2e72215a6199899f1b12816b75ffe72` 的 run-024 Conformance 2/2 / 12/12 PASS。Capability freeze/authorization digest 为
`sha256:fa119ba7903863391d2c2edecaf9e897bb409a326bbbd75a5fb9238ff9a90acf` /
`sha256:490a1c6a32c64b653829ea95724ac1d0cbb42c525066513b8e5107195d0779a0`；前 39 responses / 17 Case 完成，Draft 以
104 tokens、raw 空 authority collection PASS。第 40 次 Review request 在唯一 TLS session 复用 39 次、运行约 120 秒后收到
`REMOTE_DISCONNECTED`；HTTP/credential 40/40、retry 0，failure/terminal digest 为 `sha256:4f13c0e2…a771a` /
`sha256:3cf8ccd7…573f8`。授权已消费且不能 retry；没有 Qualification、hidden canary 或 Activation。

`FINDING-008-036` 将长运行 transport 改为 Adapter `@7`、connection policy/audit `@2`：每条 verified session 最多 20 次 HTTP
dispatch，第 21 次 logical request 在 credential/Authorization/HTTP 前主动轮换；一次运行仍最多 3 次 acquisition，任何已 dispatch
request 仍绝不重发。bounded policy 升级为 `@1.4.9`，configuration fingerprint 为
`sha256:c3d8ee6932e8b3bb63dcdf9c8fd001ee03315a34c5fb48dbdf397082577b508b`。上游 `1.5.8/@17`、suite/oracle、18/40 与
18/18 threshold 不变。新 clean candidate 必须重新完成 Conformance 与 Capability；PASS 前不得生成 formal product freeze、继续
Web 或披露 canary，Production Activation 保持 `NOT_EXECUTED`。

该处置形成 clean candidate `34048ae770944a11aa4e01d0249b90933a30e8c7` / tree
`153c2dc625fd3e72e6b49c6d6cf94be95a3ef894` 并完成 run-025。Conformance preflight/authorization/result/terminal digest 为
`sha256:b5590984…69f0` / `sha256:9e79ef2f…fc6d` / `sha256:476f4d87…0518` / `sha256:9e1151ac…4049`，
2 requests / 12/12 PASS。Capability freeze/authorization 为 `sha256:011544d5…4924` / `sha256:7955eb96…15a2`；40 calls /
18 Case / 18/18 PASS，tokens `84,420/2,463`，TLS `2/2`、reuse `38`、HTTP/credential `40/40`、unknown/retry `0`，真实证明
20 dispatch/session 的轮换。

Capability result/closed/qualification proof/document/terminal digest 为 `sha256:caf062a2…cc11` /
`sha256:53fe0e40…570a` / `sha256:b407f6ad…8453` / `sha256:7d3b4ea2…208a` / `sha256:b0dd5291…a8d6`；
Qualification ref `capability-evaluation:evaluation_result_81d1cb091ea249e78bbdf562aabc7403`，valid until
`2026-08-27T13:19:05.298209+00:00`。两份授权均已消费且不可 retry，hidden canary 未披露，Activation 未执行。V-002 对当前
exact identity PASS；下一步从证据写回后的 clean producer 生成新的 formal product freeze，再执行公开登录/下单/跨域 Web，
不直接进入 canary 或 Production Activation。

证据写回后的 formal `run-007-freeze` 以 focused 89/89、candidate package 37/37、docs PASS 和 full 1036 项 exact historical
4 FAIL + 1 ERROR hold 通过；report/deterministic qualification digest 为 `sha256:515a88b8…92b0` /
`sha256:49957156…120d`，freeze 阶段模型 dispatch 为 0。授权启动后的公开问题 `登录流程是怎样的？` 完成 5/5 DeepSeek HTTP 200，
TLS `1/1`、reuse `4`、credential `5/5`、unknown/retry `0`。Investigation、四份 COMPLETE Query Result、COMPLETE knowledge
representation、SATISFIED Need 与语义正确的 Draft 均完成；旧 `@17` Review 却仅因
`business_discovery_recall=UNKNOWN` 返回 `QUERY_INCOMPLETE`。terminal/Gateway summary digest 为
`sha256:2182903a…0399` / `sha256:7349affd…e98`；第二题未执行。

`FINDING-008-037` 将 business-discovery recall 明确限定于 absence、non-existence、total inventory、exhaustive recall 等
bounded-negative claim；有 COMPLETE 正向事实支持的行为答案不得仅因该 recall 为 UNKNOWN 而被拒。活动 Contract/Strategy、
Prompt/Vocabulary、policy 与 suite/oracle 升级为 `1.5.9/@18/@1.4.10/@1.5.9`，并在同一 `REVIEW-018` 同时冻结 UNKNOWN recall
下 negative REJECT 与 positive APPROVE。18 Case / 40 calls、Adapter `@7`、connection/audit `@2/@2`、两个 compiler、no-retry
和 1000-token budget 不变。run-025 Qualification 与 run-007 freeze/grant/session 不适用于新 identity；必须从 clean candidate
重新执行 2-call Conformance 与完整 Capability，PASS 前不得再生成 formal product freeze 或提交公开题。

clean candidate `ec2201abb96c8b2badb27835fe4508906681538d` / tree `1eded0e1526c5a920b951c5f6df43a5da7e7bd67`
的 run-026 随后完成 Conformance 2/2 / 12/12 PASS；Capability 也完整执行 40 calls / 18 Case，TLS `2/2`、reuse `38`、
HTTP/credential `40/40`、unknown/retry `0`，但只有 17/18。唯一失败是 positive `REVIEW-018`：两次 Review 输出 digest 都为
`sha256:2c0317e0…c7e7`，模型把 SATISFIED 正向输入与 bounded-negative 输入同样返回 `REJECT / QUERY_INCOMPLETE`。Capability
result/closed/terminal digest 为 `sha256:5c03b738…a55b` / `sha256:b5da8910…6fde` / `sha256:a7fbdfb5…ef3f`；授权已消费且
不得 retry，没有 Qualification。

`FINDING-008-038` 证明问题不再是语义规则缺失，而是 wire 仍把 `BUSINESS_DISCOVERY_RECALL_UNPROVEN` 标成 positive Review 的
missing limitation。Application terminal compiler `@2` 现从 sealed Need outcome 编译不可伪造的 `review_completeness_scope`：全部
`SATISFIED` 时使用 `POSITIVE_SUPPORTED_ONLY`，从 model-visible Trace 删除仅对负向主张适用的三项 recall 字段，并明确禁止 Draft
偷带 bounded-negative claim；其他 outcome 使用 `THREE_LAYER_REVIEW` 并保留三层。原 sealed Trace/raw output/audit 不改写。
活动 identity 升级为 `1.5.10/@19/@1.4.11/@1.5.10`；18/40、Adapter/transport、Investigation compiler、no-retry 与 budget
不变。run-026 与此前资格/产品运行不可继承，新 clean 2-call Conformance 和 40-call Capability 仍是下一 Gate。

上述处置形成 clean candidate `be9ab1e56dcd62bf3e3151bd5f1beb427f25203b` / tree
`25489f35236b00402effb8f036f393130906eb84`，run-027 已完成 Conformance 2/2 / 12/12 与 Capability 40 calls / 18 Case /
18/18 PASS。Conformance result/terminal digest 为 `sha256:eb8f728b…010a` / `sha256:651d6a93…42a7`；Capability
result/closed/qualification/qualification-document/terminal digest 为 `sha256:af60335e…0a46` / `sha256:cb31bbbf…83ec` /
`sha256:2b1141f3…b634` / `sha256:4111846f…8138` / `sha256:8ca137b4…69af`，有效至
`2026-08-27T14:34:15.238182+00:00`。完整运行 tokens 为 `83,527/2,461`，TLS `2/2`、reuse `38`、HTTP/credential
`40/40`、unknown/retry `0`。`REVIEW-018` 的第一项仍为 `REJECT / QUERY_INCOMPLETE`，第二项准确变为 `APPROVE`；exact
positive manifest 只保留 Query/knowledge COMPLETE 并显示 `POSITIVE_SUPPORTED_ONLY / NOT_APPLICABLE / REJECT` scope。
两份授权均已消费且不可 retry；V-002 对当前 identity 已 PASS，下一 Gate 是证据写回后的全新 formal product freeze/Web。

资格证据写回提交 `173da886b6a9bf16065130837a4e85350478948f` 后启动的 formal `run-008-freeze` 在 focused 阶段停止：
88 项 PASS，`test_candidate_stage_uses_the_bounded_answer_and_gateway` 因 clean producer 没有未跟踪的 workspace-relative
`var/iteration-006/live/run-008/candidate-stage` 而 ERROR。CLI 显式传入的 accepted baseline 已在该测试前成功完成真实 candidate
staging，所以 baseline 没有漂移；失败来自 unit test 的隐式本机 evidence 依赖。run-008 未形成 report，外部模型调用为 0。
`FINDING-008-039` 已将该 unit test 改为自包含 temporary baseline fixture，实际 formal CLI 的显式 exact baseline digest Gate 不变；
无 `var/iteration-006` 的 clean producer 中单项 1/1、focused 89/89 PASS。run-008 永久保留且不复用，下一尝试为全新
`run-009-freeze`。

run-009 随后在纯 Git checkout 中通过 focused 89/89 与 candidate-package 37/37，但 full discovery 因缺少仓库有意忽略的五个
`validation-projects/` nested repositories 和历史 frozen `var/` 语料，只发现 1020 项并出现 8 FAIL、25 ERROR、1 skip；没有
formal report 或外部模型调用。`FINDING-008-040` 将 formal producer 明确分成 exact clean tracked product source 与受保护历史验证
输入；后者只服务 full regression，不进入 source snapshot、candidate package 或产品 manifest。

正确装配的 formal `run-010-freeze` 使用 tracked commit `3f4e4789adea9f0dfe7c754ea3d659e6d71c9c1f` / tree
`a7a38cc457e0a42223976566a0171fd98319f35f` 并 PASS：focused 89/89、candidate 37/37、docs/prelisten PASS，full 1038 中
1033 PASS 且只保留 `FINDING-008-020` 的 exact 4 FAIL + 1 ERROR。report/deterministic qualification/candidate-stage digest 为
`sha256:42281ade…361a` / `sha256:96a96370…7876` / `sha256:ce4d635a…886c`；freeze 外部模型 dispatch、Git 发布与
Activation 均未执行。pending grant `sha256:e3c9bed5…b082` 仍为未授权状态，下一 Gate 是晚于该 exact freeze 的公开 Web 授权；
hidden canary 仍未披露。

用户随后以 `codex-user-message:sha256:2f9d8871…84de` 授权 run-010 正式公开 Web；authorized grant digest 为
`sha256:56b457ce…91dc`。首个问题“登录流程是怎样的？”完成 3 Investigation + Draft + Review，5/5 DeepSeek request、TLS `1/1`、
reuse `4`、credential `5/5`、unknown/retry `0`；页面、四个 Citation projection、console 和 Source-off audit 均正常，page/terminal
digest 为 `sha256:f796b10d…7c49` / `sha256:bbba266d…aa1dc`。但答案只写一次 `recordFailure()`，而 frozen Source 与 typed
Result 都明确保存 ordinal 1/2 两个 call site、legacy count 2；Reviewer 仍 APPROVE。V-003 因而 objective FAIL，首次偏差为 Draft，
Review 是二次偏差，Web 只是忠实交付。当前没有 user quality-verdict receipt；同一旧 identity 的下单与跨域题未继续执行。

`FINDING-008-041` 将确定性语义放回 Application Owner。terminal compiler `@3` 编译 ordered behavior obligation 与 exact
same-target multiplicity，caller 不可伪造；Draft 必须保留，Reviewer 对合并 occurrence 返回 `MATERIAL_OMISSION`。活动 identity 为
`1.5.11/@20/@1.4.12/@1.5.11`；18 Case / 18/18 不变，新增独立 omitted-duplicate Review 后为 41 calls，产品每题 4—6 calls
不变。expanded focused 106/106、fake 18/18、compileall/diff PASS；full 1039 中 1034 PASS，只保留
`FINDING-008-020` 的 exact 4 FAIL + 1 ERROR。旧 run-027 Qualification 与 run-010 freeze/grant/session 不可复用。

该处置形成 clean candidate `6d5f2de66338942787aa0465f540f732dbdb3626` / tree
`f31c82ed57e4509b169900c38cd720e624d41915`。run-028 Conformance preflight/result/terminal digest 为
`sha256:59ffbaf1…198e` / `sha256:5dffdf36…b5dd7` / `sha256:3ecdd7cf…1893`，2/2 requests / 12/12 PASS；TLS
`1/1`、reuse `1`、HTTP/credential `2/2`、unknown/retry `0`。Capability freeze/authorization digest 为
`sha256:d7d13acc…9bf9` / `sha256:3e129b30…3cfe`；完整执行 41 calls / 18 Case / 18/18 PASS，tokens
`89,014/2,568`，TLS `3/3`、reuse `38`、HTTP/credential `41/41`、unknown/retry `0`。

Capability result/closed/qualification-proof/qualification-document/terminal digest 为 `sha256:4dbfa35d…4443` /
`sha256:4aa86b5c…db4b` / `sha256:0880bb0d…eb6` / `sha256:50fc40ff…77d0` / `sha256:e341bc7b…45eb`，有效至
`2026-08-28T00:28:17.345205+00:00`。`DRAFT-017` 明确 `recordFailure()` exactly twice；`REVIEW-018` 依次得到
bounded-negative `REJECT / QUERY_INCOMPLETE`、完整答案 `APPROVE`、遗漏重复调用 `REJECT / MATERIAL_OMISSION`。两份授权均已
消费且不可 retry。V-002 对 current identity PASS；下一步从证据提交后的 clean producer 生成全新 formal product freeze。
V-003/V-WEB-001 保持 blocking，hidden canary、SLICE-002、Reflection 与 Production Activation 继续阻断。

run-028 证据提交 `b0f8ce835d8cbfbe5330513115e651691da7621b` 后的 formal run-011 使用 symlink 挂载五个 nested
validation repository；sealed checkout 的 canonical path 因而落在 clean producer 外，full 1039 除既有 exact hold 外新增
ProductHoldout 1 FAIL + 1 ERROR，未形成 report，模型调用 0。`FINDING-008-042` 要求这些 checkout 在 producer 内真实
materialize，并同时保持 exact revision、canonical remote 与 clean status；定向新增两项随后 2/2 PASS。

正确装配的 formal `run-012-freeze` 使用同一 tracked commit/tree 并 PASS：focused 89/89、candidate 37/37、docs/prelisten
PASS；full 1039 中 1034 PASS，只保留 `FINDING-008-020` 的 exact 4 FAIL + 1 ERROR。report/deterministic qualification/stage
digest 为 `sha256:aada406e…4a5a` / `sha256:0dbb2e8e…fce6` / `sha256:7484be1b…0a97`；source snapshot
commit/tree/manifest 为 `03fa8603…146d` / `7098432f…9a83` / `sha256:37daf84d…2a3c`。freeze 外部模型 dispatch 为 0，
pending grant `sha256:5cb18436…9370` 仍为 `live_dispatch_authorized=false`。下一 Gate 是晚于 exact run-012 freeze 的公开 Web
授权；hidden canary、SLICE-002、Reflection 与 Production Activation 继续阻断。

ITER-006 已完成窄范围 Acceptance。ITER-007 的 SLICE-001 已按计划先走正式 Web，并在大量 Java 语义加固前暴露产品架构问题；
该失败已由 `ITER-007-RESULT-SLICE-001-STOP-DECISION` 保留，因此不进入 SLICE-002/003。

替代 product freeze run-002 已取得 post-freeze 授权并启动正式 Web。用户两个独立请求均失败：第一个在单次 Plan 后以
`DomainError` 结束；第二个完成严格三调用且 Answer/Gateway 均 PASS，但被遗留的单连接 role audit 在
`ROLE_POSTCONDITION` 阶段误判。`FINDING-007-007` 已处置为从 frozen dispatch call count 推导 Answer 连接期望；run-002 freeze、
grant、session 与失败 terminal 全部保留，修复中的代码必须生成新的 product freeze 和 post-freeze live 证据。

修复后的 run-003 冻结尝试因 workspace sandbox 禁止 AF_UNIX listener 未形成 report，失败目录和 912 项测试输出已保留；同一
producer 的受影响 7 项在允许 listener 的执行面 7/7 PASS。随后 run-004 以 focused 67/67、candidate package 25/25、
full 912/912、docs 与 unauthorized-prelisten 全部 PASS，report digest 为
`sha256:07f3431e919706f3c9a6fbe601906d7dd2c5532b53032b3fbefb5702cef725fe`。该冻结随后获得了明确绑定 run-004 的用户 live 授权；
冻结阶段没有外部模型调用。

用户已在 run-004 冻结后通过正式 Web 提问。登录流程所需的 `authenticate`、`recordFailure`、`issueSession` 已进入候选，
但系统因不能唯一选择一个方法而拒答；下单问题在源码中没有实现，系统却返回三个登录方法候选。三调用均成功，所以根因不是
本次模型调用失败，而是固定 `Plan → 单方法消歧 → Draft → Review` 协议不能继续跨方法调查，也没有可靠的 Coverage 穷尽语义。
`FINDING-007-008/009` 已记录，用户产品 verdict 为 FAIL，隐藏 canary 不再执行。

run-003 与 run-007 的失败、run-002 capability 8/8、run-008 三路各 6/6 及 comparison
`sha256:857085c4…` PASS 均保留；所有单次外部分派授权已经消费，不得复用。最终用户 Acceptance 只接受 run-008 candidate stage
证明的 Java 静态调用子集，不把封闭题集外推为系统介绍、架构意图、跨域组合或通用源码问答能力。

验收现场进一步确认当前 Web 是评测台而非最终 Chat：全局类型/方法清单被误路由为 Gap，示例未随动态 Read Set 更新，底层 TLS
失败只显示通用 terminal 错误。这些限制进入 ITER-007 的验证范围，但不得追溯改写 ITER-006 Acceptance。

下一步仍服务同一个最终目标，不改名也不偏离为“自建 Agent 产品”。`ROADMAP-M-002` 已把目标反推成连续能力路径；ITER-008 只尝试
其中最早未证明的 Step 1：Agent 作为调查控制器，只能查询提问前构建的 World Model，不能读源码、触发更新或 Direct fallback。

[生产启用](roadmap/candidates/production-activation.md) 与已有 Scope 的
[Schema Evolution](roadmap/candidates/schema-evolution.md) 仍未授权；当前被接受的 Behavior 只限 ITER-006 静态调用子集。

## Agent 读取范围

当前 coding input 是 `ITER-010-SLICE-001`。已授权修改该 Slice 所需的产品/System 代码并执行本地确定性验证；唯一下一出口是先交付
可启动 Chat 页面，而不是闭合全部五轮质量和比较 Gate。技术质量先由独立复核裁决，用户在每个检查点均可停止方向，最终再决定
`CONTINUE / REWORK / REDIRECT / REJECT`。不得启动 live Web、调用
Provider、进入 Slice2/3、披露或收集 hidden 输入、复用已消费 grant，亦不得执行 Production Activation。`src/main/resources`、配置凭据
仍在授权范围外。
