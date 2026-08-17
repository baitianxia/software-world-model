---
id: PROJECT-CURRENT
kind: project-current
status: current
authority: current-development
owners: [project]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ROADMAP-M-002, ITER-001-INDEX, ITER-002-INDEX, ITER-002-RESULT-ACCEPTANCE, ITER-003-INDEX, ITER-003-RESULT-ACCEPTANCE, ITER-004-INDEX, ITER-004-RESULT-ACCEPTANCE, ITER-005-INDEX, ITER-005-RESULT-ACCEPTANCE, ITER-006-INDEX, ITER-006-RESULT-ACCEPTANCE, ITER-007-INDEX, ITER-007-RESULT-SLICE-001-STOP-DECISION, ITER-008-INDEX, ITER-008-SLICE-001]
code: []
tests: []
as_of: 2026-08-17
active_iteration: ITER-008-INDEX
active_slice: ITER-008-SLICE-001
worktree_status: iteration-008-run-006-architecture-evidence-semantic-intent-compiler-1.4.0-local-verification-in-progress
strategy_relation: bounded-result-driven-world-model-investigation-replaces-rejected-fixed-single-method-answering
live_model_path: iteration-008-deepseek-v4-pro-conformance-run-006-pass-capability-run-006-twelve-of-eighteen-architecture-redirect-not-qualified-production-not-activated
---

# 当前工作上下文

## 开发授权

当前活动 Iteration 为 `ITER-008`，唯一活动 Slice 为 `ITER-008-SLICE-001`。ITER-007 已按其早期 stop/redirect 规则终止为
`rejected`；SLICE-002/003 从未授权。用户消息 `codex-user-message:sha256:eb381cfd…7221` 接受 ITER-008 Readiness，并只授权最小
bounded investigation 闭环、正式 Web 早期 Gate 和代码冻结前的确定性验证。`SLICE-002`、live Provider 披露与 Production
Activation 不在本次授权内。

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
| Iteration 008 | **SLICE-001 authorized / architecture redirect under local verification** | `1.3.2` candidate 的 DeepSeek Conformance run-006 PASS；Capability run-006 完整执行 39 calls / 18 Case、无 unknown，但只有 12/18。证据证明模型复制 opaque authority 参数是职责倒置，旧 suite 还包含产品不可达状态；现以 `1.4.0` semantic-intent compiler 和产品可达 18-case / 41-call qualification 修复，尚未 live requalify；正式 runtime 仍保持 Ark |
| Evidence-first Strategy | PASS / exact and time-bound | `evidence-first-software-answer@1.0.0` 的十类能力、两个 Java 工程六题和本机浏览器体验通过；它读取任务级 Evidence Packet，不是 Snapshot 世界模型问答 |
| 软件世界模型产品闭环 | **ACCEPTED / local Maven + narrow Java static-call evaluation-only** | typed Structure Kernel、独立更新、Source-off View/Citation、Snapshot-first 回答与真实模型对照通过；仍未达到通用源码问答 MVP |
| `local-browser` | Two explicit local evaluation surfaces | 原 `http_api` 仍是 ITER-002 Direct；World Model 页面是带强制评测标识的本机验证入口，不是最终 Chat，二者不互相兜底 |
| Production Activation | **NOT EXECUTED** | 不得由任何本机 PASS 自动推导 |

精确产品边界见 [Iteration 006 Acceptance](iterations/iteration-006/results/acceptance.md)。原始 Provider、能力、产品和浏览器证据
保存在本机 `var/`，只通过 Result 中的 ID、Digest 和路径引用，不进入 Git。

## 当前执行顺序

ITER-008 当前只推进已授权的 SLICE-001。活动 bounded contract 已升级为 semantic-intent compiler `1.4.0`；Capability
suite/oracle/evaluator 保持 18 个 Case 和 18/18 threshold，但以 41 次模型调用覆盖产品可达 transition。纯本地 fake transport 已证明
18/18 PASS 和 exact call count；本轮架构修复未读取 credential、未建立 Provider transport。
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
`deepseek-chat-completions-no-tools@1`。Adapter、独立 2-call Conformance、CLI 及 ITER-008 fake-transport Gate 已离线通过；没有读取真实
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

Agent 只能按 `ITER-008-SLICE-001` 修改其列明的 bounded investigation、Query、Strategy、Gateway/runtime、正式 Web 与验证资产，
并以 baseline `38ebed20c5fa7bb603b8bc91981ad25da57f5877` 为起点。不得执行 ITER-007 SLICE-002/003、ITER-008 SLICE-002、
不得披露/收集早期 canary 或最终隐藏题，不得复用已消费的外部分派 grant，也不得执行 Production Activation。
