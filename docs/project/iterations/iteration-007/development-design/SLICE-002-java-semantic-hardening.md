---
id: ITER-007-SLICE-002
kind: development-slice
status: proposed
authority: proposed-development
owners: [engineering, quality]
depends_on: [ITER-007-PROPOSAL, ITER-007-READINESS, ITER-007-SLICE-001, ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-ACCEPTANCE]
code: [src/software_world_model/application_services, src/software_world_model/knowledge_engine, src/software_world_model/infrastructure, src/software_world_model/interface, src/software_world_model/ai_infrastructure]
tests: [tests, validation]
iteration: ITER-007
coding_input: false
product_goal_gate: V-000
product_goal_accepted_capability_refs: [ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-ACCEPTANCE]
product_goal_cross_domain_case_ids: [V-XD-002]
product_goal_web_checkpoint_id: V-WEB-002
product_goal_live_ad_hoc_checkpoint_id: V-ADHOC-001
product_goal_slice_gate_case_ids: [V-XD-002, V-WEB-002, V-CANARY-002, V-006]
---

# SLICE-002：可见语料上的 Java 语义加固

## Status and dependencies

`HISTORICAL PROPOSAL / NOT EXECUTED / PERMANENTLY NOT AUTHORIZABLE IN REJECTED ITER-007`。本 Slice 在原计划中依赖
SLICE-001 PASS；该前提已经失败。frontmatter 保留 `proposed` 只为满足 rejected Iteration 的历史序列，不表示未来仍可授权。
若以后需要其中任何内容，必须在新 Iteration 重新提案和授权。

## Product-goal contribution and cumulative integration

- Product gap shortened: 把一个方法的 walking skeleton 扩展为可见真实语料上的常见 Java 功能实现问答。
- Existing capabilities combined: 继续通过同一 `JAVA_SOURCE_SEMANTICS@1`、Update/Bundle、`CALLS`、功能候选和正式 Web 回答链。
- User-visible Web questions at slice end: `V-XD-002` 与至少 5 条自由问题，其中至少 2 条不含符号名并覆盖四类源码问题。
- Early hidden canary: 独立评测方持有 `V-CANARY-002` 的 common-Java 小型真实工程及问题；身份、源码和问题在本 Slice 产品代码冻结
  前对实现方隐藏，至少含一条可回答的无符号问题，且不复用为最终 held-out 工程。
- Slice stop / redirect signal: common-Java/disposition 无法闭合、Web 效果退步、需要样本特判、no-payload 失衡或
  `V-CANARY-002` 未 PASS 即停止，不进入 SLICE-003。

## Current vs expected behavior

SLICE-001 只证明最小方法。本段只在预先声明的 development/qualification corpus 上扩展 frontend、状态和异常语义、功能候选召回、
R1→R2 与重启持久化；完成后仍从同一正式 Web 人工提问，而不是只看 parser/View 测试。

## System contracts and invariants

- frontend 覆盖 annotation、interface、inheritance、generic、constructor、overload、variable receiver、lambda、try/catch/finally；
- 新增 state read/write、catch/finally、多个 branch 和受控 source order；新增调用关系使用新 predicate/modality，不改变旧 `CALLS`；
- formal index 和 `implementation_candidates` 扩大召回/消歧，但禁止 enum、固定关键词答案和工程特判；
- 全局只表示 disposition manifest COMPLETE；方法级 `SEMANTICS_COMPLETE` 才支持否定结论；
- R1→R2 无问题更新，旧 Session 固定 R1，invalid R2 保留 CURRENT，SQLite/File Bundle/Catalog 重启可读；
- exact 三调用、Source-off、Citation 和独立 Reviewer Contract 不变。

## Interfaces and affected code

沿用 SLICE-001 的 Authority、Java frontend、Update、Bundle/Catalog、repositories、View/query、world-model answering、runtime/HTTP/Web、
Citation 和 model gateway Owner，只扩展同一 Profile 和操作，不增加平行入口或 Profile。

## Compatibility, data and security boundaries

ITER-003—006 accepted behavior 必须回归。可见 corpus 与 held-out corpus 身份严格分离；本段所有 Source 只在 Update/qualification 授权
边界使用，问题阶段仍无 Source/Artifact/Evidence payload 或 Direct tools。

## Open questions and implementation risks

- variable receiver/inheritance 的 source relation 很容易被错误包装成旧 static `CALLS`；
- method-level completeness 必须贯穿 Candidate、Query、Assessment、Bundle、Web，不能只存在于 parser 报告；
- 功能候选在可见 corpus 上过拟合会在真正 held-out 工程暴露，禁止看到 SLICE-003 工程后再加固。

## Acceptance scenarios

1. 可见 corpus 的 common-Java Oracle、disposition、no-payload 与新旧 predicate consistency PASS。
2. R1→R2、重启 Source-off、Citation 和旧 Session 不漂移 PASS。
3. 正式 Web 执行 `V-XD-002` 和至少 5 条自由问题；至少 2 条无符号名，覆盖功能定位、条件/状态、返回/异常、跨方法调用。
4. 每题严格 3 次模型调用，Source/Update/Direct fallback=0，无 fixture/问题/工程分支。
5. ITER-003—006 回归及 method inventory 排序、调用方向、“异常路径”反例全部 PASS。
6. 完成可见 Gate 后冻结本 Slice 产品代码，再由独立评测方披露并执行 `V-CANARY-002`；它必须走同一正式产品链且 PASS，才允许
   授权 SLICE-003；可回答问题给 Gap 不算 PASS。Slice Result 必须绑定 code-freeze、canary project/suite 和 disclosure receipt
   digest，并报告从披露到 Slice Result seal 的产品变更数 0。该窗口内任何产品改动都必须保留原结果、烧毁该 canary，并由独立方
   换全新工程和问题后重新冻结；seal 后 capsule consumed，后续已授权 Slice 的改动不追溯改写本 Slice 结果。

## Findings

链接本轮 [Findings](../findings/README.md) 与[实现发现回写规则](../../../governance/implementation-feedback-policy.md)。
