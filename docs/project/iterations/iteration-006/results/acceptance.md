---
id: ITER-006-RESULT-ACCEPTANCE
kind: iteration-acceptance
status: completed
authority: evidence
owners: [product, project, quality]
depends_on: [ITER-006-VERIFICATION, ITER-006-FINDINGS, ITER-006-RESULT-IMPLEMENTATION-VERIFICATION, ITER-006-RESULT-LIVE-RUN-003, ITER-006-RESULT-JAVA-CAPABILITY-RUN-002, ITER-006-RESULT-LIVE-RUN-007, ITER-006-RESULT-PRODUCT-CANDIDATE-FREEZE-RUN-008, ITER-006-RESULT-LIVE-RUN-008, FINDING-006-013]
code: [src/software_world_model, validation/structure_world_model_iteration_006]
tests: [tests]
iteration: ITER-006
accepted_scope: local-java-static-call-world-model-evaluation-only
subject_identity: sha256:862fdb8d91006555d6b6f40a9ca4d7a520871dfa3baea248f1f4b02ef6de213b
baseline_commit: bc0ecefb806c946f9c2b5938470be18ec780115b
baseline_relation: exact-protected-candidate-stage-derived-from-baseline
accepted_by: user
accepted_at: 2026-08-13T11:45:33+08:00
acceptance_ref: codex-user-message:sha256:49cfd2249745a37870221fdb78be545de1d364bdaf5f02432e342c9f5c2dcb0f
production_activation: not-executed
---

# Iteration 006 Acceptance

## Exact subject and scope

用户以“验收完成”接受 `run-008` 精确密封的受保护 candidate stage
`sha256:862fdb8d91006555d6b6f40a9ca4d7a520871dfa3baea248f1f4b02ef6de213b`。该 stage 的 producer
commit/tree 为 `c4d3d4be48e778a8380ba321dd37058f382d5d32` / `8cc1177bba3ffb7a1d862c412fa6d0161fadbde6`，
producer source manifest 为 `sha256:d362a5aaee7ee157f5b1d35131a0fb325bdb8b48b836084b316329e8727c3ab5`。当前主工作树仍以
`bc0ecefb…` 为 `HEAD` 且包含未提交/未跟踪文件；本裁决不把整个工作树或其后出现的 ITER-007 规划文件隐式纳入接受对象。

接受范围是新的本机 SYSTEM Scope 上 `JAVA_STATIC_CALL_GRAPH@1` 的 `EVALUATION_ONLY` 纵向闭环：从 exact Local Git Java
源码独立构建类型、方法声明及冻结语法子集内可唯一解析的静态直接调用，原子发布 Snapshot/Bundle/Catalog，在问题阶段不读取
Source、Evidence payload 或权威数据库，并通过同一产品 Web 入口回答指定 Java 类型的方法清单、直接调用、静态路径、支持性
否定、相邻 Snapshot 有序差异和明确的 Coverage Gap。

## Gate results and limitations

| Gate / claim | Verdict |
|---|---|
| Java declaration/call Oracle、R1→R2、R3 fail-closed、Source-off View/Citation | PASS；V-001—V-007 的确定性证据闭合 |
| Java proposal capability | run-002 为 8/8 `PASS_VALID`、8 个唯一 Ark request、0 retry；授权已消费 |
| 历史失败保留 | run-003 World Model 4/6；run-007 World Model 0/6 terminal success（6 次内部 call 后 postcondition 拒绝）；均未改写或重试 |
| 最终 Product Validation | run-008 Direct/Codex/World Model 各 6/6 terminal SUCCESS；comparison `sha256:857085c4…` PASS、blocker 0、0 retry/filter/interpolation |
| 正式 Web 评测入口 | 对 run-008 冻结的 supported/negative/diff/Gap/Citation 范围 PASS；它是评测台，不是最终通用 Web Chat |
| Production Activation | **NOT EXECUTED / out of scope** |

本裁决不扩展到 Java 全语言、变量接收者或运行时 dispatch、反射、依赖注入、业务/设计意图、README/ADR/配置/部署知识、跨 Profile
组合、通用实体发现、多轮会话、认证、公网部署或 Production Activation。网页中的十阶段 Authority、评测标识和失败关闭仍属于
验证界面，不构成最终聊天产品体验。

用户在最终裁决前又运行了单独授权的本机交互会话，形成两条补充但不改写 run-008 的现场证据：第一题在 Ark TLS 握手失败后
按零重试规则失败关闭，但页面只显示通用 terminal 错误；第二题“列出当前 Read Set 中的 Java 类型和声明方法”虽完成一次 Ark
调用，却因确定性解释器要求先出现一个具体 `JAVA_TYPE` 而生成空 Query Plan 和误导性的 `KNOWLEDGE_NOT_MODELED`。页面硬编码
`FlowService` 示例也没有随随机 Read Set 的实际类型更新。这些事实明确限制了 Acceptance：当前入口不能被称为正式最终 Web Chat，
也不能据此声称可回答系统用途、架构意图或总体介绍。

## Product-goal delta and cumulative evidence

- Baseline versus current：相对 ITER-005 只含 Maven reactor Structure 的接受基线，本轮新增 Java 类型、方法声明、有限静态
  `CALLS`、静态路径和相邻 Snapshot 差异；run-008 六个封闭 Java case 全部通过，但没有测得通用自由问题支持率。
- New plus existing cross-domain result：本轮没有在同一问题中组合已接受 Maven Structure 与新增 Java 调用知识的跨域 Case，
  因此不能把本轮称为通用源码问答 MVP；`FINDING-006-013` 已把该累积 Gate 写入下一轮起生效的产品成功标准和治理规则。
- Product Web ad-hoc questions and fallback counters：上述两条现场问题分别暴露 TLS 错误呈现和全局清单路由缺口；两题均保持
  Source/Update/Direct fallback 为 0，第二题 Provider call=1、retry=0，但没有产生支持性 View Result。
- Mature source Agent comparison：run-008 的六个冻结 case 已逐题对照受控 Direct 与 Mature Source Agent，World Model 重大错误
  为 0、完整性 1,000,000；该结论只适用于密封题集，不覆盖现场的系统介绍、架构或全局发现问题。

## Finding dispositions and System write-back

`FINDING-006-001` 至 `FINDING-006-013` 均已处置，没有 open Finding。Java Profile、静态调用 modality、更新与 Source-off View、
模型资格、失败关闭和产品边界已写回 owning System 文档。`FINDING-006-013` 进一步把“孤立 Profile PASS 不等于通用源码问答
进展”写入 `SYS-PRODUCT-SUCCESS`、迭代生命周期、Roadmap 选择规则和治理模板；run-003/run-007 的失败及本次交互限制均保留，
没有用 Acceptance 覆盖负面证据。

## Verdict

**Accepted and completed for the exact local Java static-call World Model evaluation-only scope proven by run-008.**

该裁决接受窄范围 Java 静态调用闭环及其证据，不接受当前页面为正式最终 Web Chat，也不证明系统已能回答总体用途、架构意图或
通用源码问题。ITER-006 不再授权产品代码修改；任何体验修复或能力扩张都需要新的 Proposal/Readiness/开发授权与全新验证。
Production Activation、Git stage/commit/push 均未执行。
本次交互会话的 `127.0.0.1:55130` 后端和 `127.0.0.1:55131` 限额网关在验收后均无监听进程。
