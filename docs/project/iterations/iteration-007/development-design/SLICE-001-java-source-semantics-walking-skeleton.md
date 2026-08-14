---
id: ITER-007-SLICE-001
kind: development-slice
status: blocked
authority: development-evidence
owners: [engineering]
depends_on: [ITER-007-PROPOSAL, ITER-007-READINESS, ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-ACCEPTANCE, SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY]
code: [src/software_world_model/application_services, src/software_world_model/knowledge_engine, src/software_world_model/infrastructure, src/software_world_model/interface, src/software_world_model/ai_infrastructure, pyproject.toml]
tests: [tests]
iteration: ITER-007
coding_input: false
product_goal_gate: V-000
product_goal_accepted_capability_refs: [ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-ACCEPTANCE]
product_goal_cross_domain_case_ids: [V-XD-001]
product_goal_web_checkpoint_id: V-WEB-001
product_goal_live_ad_hoc_checkpoint_id: V-ADHOC-001
product_goal_slice_gate_case_ids: [V-001, V-002, V-002A, V-003, V-004, V-004A, V-XD-001, V-WEB-001, V-CANARY-001, V-005]
---

# SLICE-001：最小实现语义正式 Web walking skeleton

## Status and dependencies

`BLOCKED / PRODUCT FAIL / NO LONGER CODING INPUT`。run-004 正式 Web 技术链 PASS，但登录流程因多候选被拒答，下单边界题又返回无关登录候选。
`ITER-007-RESULT-SLICE-001-STOP-DECISION` 已保留用户产品 FAIL 结论。本 Slice 不得继续修补，SLICE-002/003 保持 proposed / not-executed。

## Product-goal contribution and cumulative integration

- Planned product gap contribution: 原计划从“只能按符号名回答声明/静态调用封闭题”前进到“不点名符号也能定位并解释一个功能实现”；
  实际产品 Gate FAIL，没有形成 accepted capability。
- Existing capabilities combined: 复用 ITER-005 正式 Web/Citation 以及接受后的 ITER-006 declaration/`CALLS`，与本段
  branch/return/throw 事实进入同一 Need/Support chain。
- User-visible Web questions at slice end: 一条无 class/method/signature 的 `V-XD-001` 和一条真实 boundary question。
- User-held live canary: 用户在本 Slice 产品代码冻结前不披露问题；冻结后现场提出至少一条可回答、无符号名并组合旧 `CALLS`
  与新实现语义的问题，以及一条真实 boundary。开发者自拟或测试夹具中的问题不能替代该 Gate。
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

- 本机 frontend/version/license/canonicalization Oracle 已冻结；SLICE-001 须在首次产品 Gate/capability qualification 前补
  `pyproject.toml` exact dependency 和跨执行环境 offline artifact/lock，不能把当前 macOS/Python 3.14 wheel 摘要外推为跨平台资格；
- reference typed atoms 已通过 exact Support closure 与六个 direct/reversible/ref-distribution 泄露反例，但真实 Bundle 仍可能信息
  不足或越过 no-payload 边界；
- 三调用 role package 与 Gateway workload 已实现。首次 `1.2.0` 资格运行 12 例中 9 例通过、3 例失败并保留；Finding
  `FINDING-007-003/004` 已据此形成 `1.2.1` Prompt/vocabulary/schema 与独立 evaluator 修正；第二次资格运行 11/12，唯一
  遗留为模型持续遗漏英文 returning 的 canonical `return` term。`FINDING-007-005` 形成 `1.2.2` language-independent semantic
  canonicalization，不加入工程/题目分支。run-003 在 exact post-freeze 用户授权下以恰好 12 次 Provider request、无 retry 取得
  12/12 `PASS_VALID`；run-001/002 两个旧失败资格仍永久保留且不得复用；
- ITER-006 的 inventory 排序、调用方向和异常路径限制必须在新资格与本 Web Gate 中关闭，不能沿用旧 run-008 冒充验证。
- run-001 product freeze 的首次现场 Web 披露暴露 `FINDING-007-006`：Answer 以 runtime exact `-I -S -B` 启动时，
  `interface/__init__.py` 的无关 eager Update import 把 `tree_sitter` 带入 source-off role，导致四次用户提交均在 `ANSWER`
  阶段 `ModuleNotFoundError` 失败关闭且模型调用记录为 0。run-001 freeze 与四次失败永久保留；修复必须切断该依赖、增加 exact
  role import gate 并形成新产品冻结，不能改写或重用已披露问题的旧 Result。替代 run-002 通过 exact import、66 focused、
  24 candidate package、911 full regression、docs 和 unauthorized-prelisten Gate 后取得 post-freeze 授权；现场第二个请求严格完成
  三调用，但 `FINDING-007-007` 证明 runtime role audit 仍把 Answer `unix_connect` 固定为旧单调用值 1，导致成功 Answer/Gateway
  被 `ROLE_POSTCONDITION` 误判。run-002 与两个失败请求必须保留；修复已从 frozen dispatch count 推导期望连接数。run-003
  freeze 因 workspace sandbox 禁止 AF_UNIX listener 未形成 report 并保留；run-004 在允许 listener 的执行面以 67 focused、
  25 candidate package、912 full、docs 和 unauthorized-prelisten 全部 PASS，等待新的 post-freeze 用户授权。

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
   digest，并报告从披露到 Slice Result seal 的产品变更数 0。该窗口内任何产品改动都必须保留原结果、烧毁该 canary，并由独立方
   换全新工程和问题后重新冻结；seal 后 capsule consumed，后续已授权 Slice 的改动不追溯改写本 Slice 结果。

## Findings

链接本轮 [Findings](../findings/README.md) 与[实现发现回写规则](../../../governance/implementation-feedback-policy.md)。
