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
worktree_status: iteration-008-direct-tls-eof-awaiting-explicit-proxy-comparison-authorization
strategy_relation: bounded-result-driven-world-model-investigation-replaces-rejected-fixed-single-method-answering
live_model_path: iteration-008-direct-tls-eof-before-certificate-verification-explicit-proxy-comparison-required-capability-not-executed-production-not-activated
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
| Iteration 008 | **SLICE-001 authorized / direct TLS EOF before certificate verification** | run-002 与独立 direct probe 均在 TLS 阶段关闭；probe 证明 TCP connect 后唯一 handshake 以 `SSLEOFError` 结束。下一步只允许 credential-free loopback proxy 对照；Capability、正式 Web 与 canary 均未执行或授权 |
| Evidence-first Strategy | PASS / exact and time-bound | `evidence-first-software-answer@1.0.0` 的十类能力、两个 Java 工程六题和本机浏览器体验通过；它读取任务级 Evidence Packet，不是 Snapshot 世界模型问答 |
| 软件世界模型产品闭环 | **ACCEPTED / local Maven + narrow Java static-call evaluation-only** | typed Structure Kernel、独立更新、Source-off View/Citation、Snapshot-first 回答与真实模型对照通过；仍未达到通用源码问答 MVP |
| `local-browser` | Two explicit local evaluation surfaces | 原 `http_api` 仍是 ITER-002 Direct；World Model 页面是带强制评测标识的本机验证入口，不是最终 Chat，二者不互相兜底 |
| Production Activation | **NOT EXECUTED** | 不得由任何本机 PASS 自动推导 |

精确产品边界见 [Iteration 006 Acceptance](iterations/iteration-006/results/acceptance.md)。原始 Provider、能力、产品和浏览器证据
保存在本机 `var/`，只通过 Result 中的 ID、Digest 和路径引用，不进入 Git。

## 当前执行顺序

ITER-008 当前只推进已授权的 SLICE-001。bounded 产品内核和确定性测试已完成第一轮实现；Capability suite/oracle/evaluator 固定为
18 个 Case、39 次模型调用，纯本地 fake transport 已证明 18/18 PASS 和 exact call count，未读取 credential、未建立 Provider transport。
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

因此下一 live 步骤仍不是 Capability、产品题或另一轮 Conformance。只允许另行冻结并授权一次显式 loopback HTTP proxy CONNECT + verified
TLS 对照，继续禁止 bearer 和 Ark HTTP body；对照失败则停止为环境 blocker，对照通过也必须先设计受控 proxy configuration，不能读取
ambient value。hidden canary、正式 Web、SLICE-002、Production Activation 与 push 继续不在授权内。详见 `FINDING-008-008`。

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
