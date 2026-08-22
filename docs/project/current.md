---
id: PROJECT-CURRENT
kind: project-current
status: current
authority: current-development
owners: [project]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ROADMAP-M-002, ITER-001-INDEX, ITER-002-INDEX, ITER-002-RESULT-ACCEPTANCE, ITER-003-INDEX, ITER-003-RESULT-ACCEPTANCE, ITER-004-INDEX, ITER-004-RESULT-ACCEPTANCE, ITER-005-INDEX, ITER-005-RESULT-ACCEPTANCE, ITER-006-INDEX, ITER-006-RESULT-ACCEPTANCE, ITER-007-INDEX, ITER-007-RESULT-SLICE-001-STOP-DECISION, ITER-008-INDEX, ITER-008-RESULT-SLICE-001-STOP-REDIRECT, ITER-009-INDEX, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, ITER-010-INDEX, ITER-010-SLICE-001, ITER-010-RESULT-V-WEB-000-LIVE-RUN-009, ITER-010-RESULT-V-WEB-001-PUBLIC-DIRECTION-QUESTIONS, ITER-010-RESULT-V-WEB-001-USER-ONSITE-QUESTION, ITER-010-RESULT-SLICE-001-STOP-REDIRECT, FINDING-010-027, FINDING-010-028]
code: []
tests: []
as_of: 2026-08-22
active_iteration: none
active_slice: none
worktree_status: iteration-010-rejected-redirect-next-iteration-not-authorized
strategy_relation: world-model-external-cognition-guides-adaptive-model-led-broker-controlled-investigation
live_model_path: stopped-direction-failure-production-not-activated
---

# 当前工作上下文

## 当前规划与授权

当前没有活动 Iteration 或 coding Slice。`ITER-010` 已由用户方向决定 `REDIRECT` 封存为 rejected，Slice1 blocked，Slice2/3
proposed 但从未授权。任何继续实现都必须先形成新的 Iteration Proposal、Readiness 和逐 Slice 用户授权，不能重新激活 ITER-010。

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

用户最后以 `codex-user-message:sha256:d746968f58cea4d2b7689b5902c0ff97f42f63c93ffc4cbc40551cfa2c0359e0` 指出实现者
已经知道回答有问题，不应再把客观停止条件退回用户重复确认。结合持续修正最终目标的要求，该消息构成 `REDIRECT` 而不是 `REJECT`。
`ITER-010-RESULT-SLICE-001-STOP-REDIRECT` 与 `FINDING-010-028` 已保存方向失败、系统性根因和下一路线边界。

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
| Iteration 010 | **Rejected / REDIRECT / evidence preserved** | `V-WEB-000/V-WEB-001` 技术 PASS；公开 4 题为 3 APPROVED / 1 fail-closed，现场题再形成 1 个 APPROVED Result，14 个 Citation 全部打开、console clean。但现场正文仍由方法序列主导并省略登录日志副作用，Reviewer 错误批准；`V-ANSWER-001`、`V-REVIEW-001`、`V-XD-001`、`V-PREVIEW-001` FAIL，用户决定 `REDIRECT`。Slice2/3、hidden、三臂对照、Acceptance 与 Production 未执行 |
| Evidence-first Strategy | PASS / exact and time-bound | `evidence-first-software-answer@1.0.0` 的十类能力、两个 Java 工程六题和本机浏览器体验通过；它读取任务级 Evidence Packet，不是 Snapshot 世界模型问答 |
| 软件世界模型产品闭环 | **ACCEPTED / local Maven + narrow Java static-call evaluation-only** | typed Structure Kernel、独立更新、Source-off View/Citation、Snapshot-first 回答与真实模型对照通过；仍未达到通用源码问答 MVP |
| `local-browser` | Two explicit local evaluation surfaces | 原 `http_api` 仍是 ITER-002 Direct；World Model 页面是带强制评测标识的本机验证入口，不是最终 Chat，二者不互相兜底 |
| Production Activation | **NOT EXECUTED** | 不得由任何本机 PASS 自动推导 |

精确产品边界见 [Iteration 006 Acceptance](iterations/iteration-006/results/acceptance.md)。原始 Provider、能力、产品和浏览器证据
保存在本机 `var/`，只通过 Result 中的 ID、Digest 和路径引用，不进入 Git。

## 当前执行顺序

当前没有执行中的开发。ITER-010 的自适应
`World Model Cognition Context → Investigation LLM → Source Broker → Retrieval Worker → append-only Evidence Ledger → 调查后 seal
Question Evidence Package → Answer → independent Reviewer` 技术纵切、公开题和现场题证据均已封存；方向 Gate 已作出 `REDIRECT`。

下一条合法执行路径是 planning-only Candidate 先吸收 `FINDING-010-028`，再由新的 Iteration 冻结 typed Answer Hierarchy、Application
acceptance 和 Reviewer 方向质量 Gate。未出现新 Proposal/Readiness/用户逐 Slice授权前，不修改产品代码、不发 Provider call、不启动
live Web，不执行 hidden、三臂消融或 Production Activation。

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

Slice1 是唯一 coding input。公开方向题和用户现场题已经执行；当前不得进入 Slice2/3、披露或收集 hidden 输入、复用已消费 grant，亦不得
执行 Production Activation。下一项必须是用户对真实结果的 `CONTINUE / REDIRECT / REJECT` 方向决定，而不是新的 Provider 调用。
`src/main/resources`、配置凭据仍在授权范围外。
