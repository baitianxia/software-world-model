---
id: ITER-007-SLICE-001
kind: development-slice
status: proposed
authority: proposed-development
owners: [engineering]
depends_on: [ITER-007-PROPOSAL, ITER-007-READINESS, ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-LIVE-RUN-008]
code: [src/software_world_model/application_services, src/software_world_model/knowledge_engine, src/software_world_model/infrastructure, src/software_world_model/interface, src/software_world_model/ai_infrastructure, pyproject.toml]
tests: [tests]
iteration: ITER-007
coding_input: false
product_goal_gate: V-000
product_goal_accepted_capability_refs: [ITER-005-RESULT-ACCEPTANCE]
product_goal_cross_domain_case_ids: [V-XD-001]
product_goal_web_checkpoint_id: V-WEB-001
product_goal_live_ad_hoc_checkpoint_id: V-ADHOC-001
product_goal_slice_gate_case_ids: [V-001, V-002, V-002A, V-003, V-004, V-004A, V-XD-001, V-WEB-001, V-CANARY-001, V-005]
---

# SLICE-001：最小实现语义正式 Web walking skeleton

## Status and dependencies

`PROPOSED / NOT AUTHORIZED`。授权时必须把 ITER-006 技术 Result 依赖替换为真实 `ITER-006-RESULT-ACCEPTANCE`，并使 Manifest、
accepted refs 和本 Slice 完全一致。只授权本 Slice；SLICE-002/003 保持 proposed。

## Product-goal contribution and cumulative integration

- Product gap shortened: 从“只能按符号名回答声明/静态调用封闭题”前进到“不点名符号也能定位并解释一个功能实现”。
- Existing capabilities combined: 复用 ITER-005 正式 Web/Citation 以及接受后的 ITER-006 declaration/`CALLS`，与本段
  branch/return/throw 事实进入同一 Need/Support chain。
- User-visible Web questions at slice end: 一条无 class/method/signature 的 `V-XD-001` 和一条真实 boundary question。
- Early hidden canary: 独立评测方持有 `V-CANARY-001` 的小型真实 Java 工程及问题；身份、源码和问题在本 Slice 产品代码冻结前
  对实现方隐藏，至少含一条可回答、无符号名并组合旧 `CALLS` 与新实现语义的问题，且不复用为最终 held-out 工程。
- Slice stop / redirect signal: 不能从正式 Web 真实回答、需要关键词/题型/工程补丁、Source-off 失败、三调用独立 Review 不合格或
  `V-CANARY-001` 未 PASS，都立即停止，不进入 SLICE-002。

## Current vs expected behavior

当前 `_analyze_java()` 只形成固定 Need，Snapshot 又没有方法体。预期用一个可见 development 工程证明最短正式链：

```text
零问题 Java 更新
  → 固定成熟 parser
  → 一个方法的 call / if / return / throw typed facts
  → Admission / Snapshot / no-payload Bundle
  → Call 1: feature → implementation_candidates + Query Plan
  → 平台执行 CALLS + method_implementation
  → Call 2: Query Result → Draft
  → Call 3: independent semantic Answer Review
  → deterministic Authorization → 正式产品 Web
```

第一次 Web 前不要求 common-Java 全量语法、两个工程或 held-out closure。

## System contracts and invariants

- 新 `JAVA_SOURCE_SEMANTICS@1` 使用新 SYSTEM Scope `INITIAL` Schema；旧 `CALLS` 只按 ITER-006 exact 规则重建。
- 新语义只含 branch guard、被 guard 控制的 direct call/return/throw、return、throw 和必要 source order。
- `implementation_candidates(search_terms, limit)` 从问题无关的 typed formal index 返回方法、匹配依据和 Support；无符号名也必须工作。
- `method_implementation(method_ref)` 只返回 semantic atoms、method completeness 和 Limitation，不返回源码或 AST 文本。
- Bundle 禁止 raw source/comment/token/expression text/full AST；信息保持与信息越界 Oracle 都必须 PASS。
- 每个授权方法有 `SEMANTICS_COMPLETE / UNSUPPORTED_EXCLUDED / FAILED` disposition；只有 COMPLETE 方法支持闭世界结论。
- 每题 exact 三调用且无 retry：Plan、Draft、独立 Reviewer；平台确定性校验 schema、Query、Support 和 Authorization。
- 新关系不能扩张 `CALLS`；不满足旧 exact 规则的 source call 使用新 predicate/modality 或明确不支持。

## Interfaces and affected code

- `knowledge_engine/structure.py`、`structure_authority.py`：新 Schema/Profile、Admission 和 disposition；
- 新 `application_services/java_source_semantics.py`：frontend Port、canonical projection、independent replay；
- `maven_structure_update.py`、`maven_workspace.py`：零问题构建和 Profile；
- `structure_read_bundle.py`、`read_set_catalog.py`、SQLite/File repositories：Bundle/Catalog 与重启；
- `structure_view.py`、`world_model_answering.py`、`world_model_product.py`：候选发现、实现查询和三阶段问答；
- runtime/CLI/presenters/HTTP/Web、`citation_projection.py`；
- capability qualification、egress policy/gateway workload 与 `pyproject.toml` 的 parser exact dependency。

不得新增顶层 Orchestrator，也不得把旧 Formal-first 同步长链接回主路径。

## Compatibility, data and security boundaries

ITER-003—006 旧 Profile、Bundle、Catalog 和 Web 继续可读。Source、authority DB 和 Evidence Store 在问题阶段不可挂载；Citation 只在
Result 密封后投影。正式入口只能是 `world_model_http.py` + `world_model_browser_ui.py`，不能用 stub、预制答案、fixture 分支、
HTTP-only probe 或 validation-only launcher 冒充产品体验。

## Open questions and implementation risks

- frontend exact 版本、license、离线可用性和 canonicalization 尚未冻结；
- typed atoms 可能信息不足，也可能过度保真成为可逆源码；
- 三调用协议需要新 Contract、Prompt vocabulary、Gateway workload 和 capability qualification；
- ITER-006 的 inventory 排序、调用方向和异常路径限制必须在新资格与本 Web Gate 中关闭，不能沿用旧 run-008 冒充验证。

## Acceptance scenarios

1. 可见 development 工程零问题更新后，卸载 Source/authority DB/Evidence Store 并重启正式 Web。
2. 无符号名功能问题通过 `implementation_candidates` 找到方法，并在同一 Support chain 使用旧 `CALLS` 与
   branch/return/throw 回答 `V-XD-001`。
3. source-insufficient 边界问题给出可解释 Gap。
4. 每题模型调用严格为 3；Source/Update/Direct delta=0；Citation 可打开；browser console clean。
5. 问题改写仍走同一通用操作；`ProductNeedKind`、工程、题目或关键词补丁全部 FAIL。
6. method inventory canonical 排序、incoming/outgoing 方向和“异常路径”反例由新 qualification 与正式 Web 回归关闭。
7. 完成可见 Gate 后冻结本 Slice 产品代码，再由独立评测方披露并执行 `V-CANARY-001`；它必须走同一正式产品链且 PASS，才允许
   授权 SLICE-002；可回答问题给 Gap 不算 PASS。Slice Result 必须绑定 code-freeze、canary project/suite 和 disclosure receipt
   digest，并报告曝光后产品变更数 0。曝光后任何产品改动都必须保留原失败、烧毁该 canary，并由独立方换全新工程和问题后重新冻结。

## Findings

链接本轮 [Findings](../findings/README.md) 与[实现发现回写规则](../../../governance/implementation-feedback-policy.md)。
