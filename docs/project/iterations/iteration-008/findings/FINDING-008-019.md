---
id: FINDING-008-019
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [architecture, application, ai, engineering, quality, project]
depends_on: [ITER-008-SLICE-001, FINDING-008-018, SYS-ADR-015, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
code: [src/software_world_model/application_services/bounded_world_model_investigation.py, src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, src/software_world_model/ai_infrastructure/model_egress_gateway.py, src/software_world_model/interface/world_model_product.py, validation/structure_world_model_iteration_008/capability]
tests: [tests/test_bounded_world_model_investigation.py, tests/test_world_model_answer_strategy.py, tests/test_iteration_008_capability_qualification.py, tests/test_model_egress_gateway.py, tests/test_iteration_008_capability_harness.py]
iteration: ITER-008
classification: system-contract
disposition: application-owned-evidence-obligation-transition-machine
target: SYS-ADR-015
---

# FINDING-008-019：调查终止必须受平台冻结的证据义务约束

## Observation

compiler `@3` redirect 的 clean candidate `4e79a126faf8c6992c1649ad8f82150d69cd414d`（tree
`b4bee2c52d5f79ad2cfa66e083849dfd29da8179`）完成 DeepSeek run-010。Conformance 绑定 preflight
`sha256:60ac01be1f28d5766256fa1eb5c2996500683bb90e90dcfd90d48e7acd822a9a`，恰好执行 2 次 request 并取得
12/12 PASS；result/terminal digest 为
`sha256:a145a64ba15f49a14825f95c13accb58424f6ffe2b388f2b9b82663bef82075b` /
`sha256:326bd75035792d20634f8a1ad3db550dc920532b131cbd9230c96ed5719ac056`。

同候选 Capability freeze `sha256:9e425d2fec706658d6574305730ff20cc37ee45a1824f0b1ac2e6eca6ec8fcfb`
无 retry 地完整执行 41/41 次 Provider request 与 18/18 个 Case；response identity 只有 `deepseek-v4-pro`，usage 完整，
input/output tokens 为 105,890/2,680，`unknown_count=0`。closed Result 的 logical result/document/terminal digest 为
`sha256:47436f2f24eb39cf359dba08c1437a35c93aebe67daedd0447daf235f3d1a193` /
`sha256:341777308d364d2732c528c1d705cd9b823702c960119f4bf0980bdf65bab9dd` /
`sha256:3937818ae9f39677945592dbb6a68a685b0fc68fd1b24c1f66711779e74135ff`。结论为 16/18 FAIL；没有
Qualification、正式 Web、hidden canary 或 Production Activation。

原 run-009 反例 `WM-JSS-I8-ALL-SIMPLE-PATHS-008` 已 PASS，证明 operation-discriminated slot projection 生效。仅剩：

- `WM-JSS-I8-MAX-FOUR-010`：第 3 回合在 method batch 后提前 `FINISH`，但“trace through”问题仍缺少直接 `CALLS` 关系；
- `WM-JSS-I8-BUDGET-EXHAUSTION-011`：第 4 回合在 direct `CALLS` 后提前 `FINISH`，但“every bounded relation”仍缺少最后一个
  `all_simple_paths` 查询。

两项 independent Review 都记录 `CONTRACT_PROJECTION_NOT_EXACT`，同时确认 `platform_contract_valid=true`、semantic constraints
满足、无 forbidden event 或越权 Ref。另一个 `LEGAL-FINISH-009` 在 method batch 后正确结束，因此不能用“总是多查一步”修补。

## Evidence and root cause

当前协议让模型在每一轮重新从原问题、最后一个 Result 和 receipt 推断“问题还欠哪类证据”，同时又允许它在任意已执行 Result 后
自由选择 `FINISH`。Application 只验证 FINISH 的形状和“至少已有一个 Result”，没有保存从首轮语义解释得到的、跨回合不可变的证据
义务，也没有在把 `FINISH` 编译为终态前证明这些义务已经关闭。

因此模型必须自行维持平台本可机械保存的短期状态。run-010 表明字段 shape、Ref、transition、transport 与模型可用性全部正常时，
同一模型仍会把“上一 Result 有一些支持”误当成“原问题所需证据已经充分”。这是终止 Owner 的系统性职责倒置，不是两个题目的
关键词缺口，也不是继续追加 Prompt 说明可以可靠关闭的问题。

## Impact and classification

`SYS-ADR-015` 当前写明 Agent 拥有逐轮 investigation control，而 Application 只拥有 authority argument、预算和终态校验。新的证据要求
把控制面拆开：模型仍拥有原问题的语义解释和通用 search terms；Application 必须拥有跨回合 evidence obligation ledger、合法
transition allowlist 与 FINISH eligibility。该变化改变 Owner、model-visible input 和 terminal invariant，主分类为
`system-contract`，目标为 `SYS-ADR-015`；不能只在 Result、Prompt 或 evaluator 中处置。

证据义务必须由现有通用 operation/relation vocabulary 表达，不新增题型 enum，不读取项目名、固定问题、关键词表、隐藏 Oracle 或
答案。Application 只根据首轮已密封义务、实际 typed Result、Ref provenance、completeness 和剩余预算确定下一组合法 transition；
模型的后续 operation/FINISH 只能在该集合内生效，不能缩小未完成义务或提前终止。

## Decision and disposition

升级为 Application-owned evidence-obligation transition machine：

1. 首个 Investigation call 同时提交 1—12 个通用 search terms 和一个有界、closed evidence-request 集合。request 只引用已注册的
   candidate/method/inventory/direct/path operation 及 direct relation intent；Application 做 operation-discriminated normalization、
   去重、依赖收敛和预算可达性校验后密封，模型不能在后续回合改写；
2. candidate discovery 始终是第一步。Application 从冻结义务和立即前序 typed Result 推导下一组合法 operation：例如 graph evidence
   先取得 method batch，declared inventory 先通过 `DECLARES_METHOD` 取得 declaring type；零候选则没有伪查询；
3. 每轮 Gateway 只披露该状态的受限 `available_operations`。compiler 将固定模型 envelope 投影到平台选定的合法 transition；raw
   model output digest 继续保存，但未完成义务时的 `FINISH` 不获得终态权力；
4. 只有全部冻结义务已由 sealed Result 覆盖，或 typed Result 证明已无合法缩小缺口的查询时，Application 才允许 FINISH，并从平台
   completeness 产生正向充分、bounded absence 或具体 Limitation reason。最后一个预算内 query 仍可执行并按既有规则密封
   `INVESTIGATION_BUDGET_EXHAUSTED`；
5. 2—4 Investigation / 4—6 total、41-call 资格上限、18 Case、18/18 threshold、no-retry、三层完整性、Source-off 与 Provider
   temperature 不变。Prompt/schema、compiler、Gateway policy、suite/oracle 和 Capability identity 全部版本化，旧 run-010 不可继承。

该处置先更新 ADR、World Model Answering、Agentic Task、Implementation Query、runtime flow、Model Gateway 与 Capability Evaluation，
再实现同一 production compiler/state machine 和产品可达资格 fixture。任何问题文本、工程、符号或 evaluator-only 分支均直接违反本
Finding。

## Verification required before disposition

- regression 必须复现 run-010 两个 premature-FINISH raw envelope，并证明对应 evidence ledger 分别编译为 required direct/all-paths query；
- legal method-only、zero-candidate complete/unknown、declared inventory、direct/path、cycle、Ref provenance 与 budget terminal 继续通过；
- Gateway 必须拒绝越出当前 transition allowlist 的权限扩张，同时允许 full contract operation universe 的受限子集；
- fake transport 必须使用 production compiler/state machine 完成原 18 Case、41 requests、18/18，独立 evaluator 不导入产品代码；
- 目标测试、full discovery、current-doc check、diff/secret scan PASS 后形成 clean candidate；新的 live qualification 必须使用全新
  Conformance/Capability freeze。未达到 18/18 时仍阻断正式 Web、hidden canary、SLICE-002 与 Production Activation。

## Verification evidence and closure

本地 targeted contract/product/capability/Gateway/runtime 回归 96/96 PASS；production compiler/state machine 的 fake transport
精确完成原 18 Case、41 requests、18/18，独立 evaluator 不导入产品代码。两个 run-010 premature-FINISH raw envelope 分别被投影为
required direct/all-paths query，legal method-only、zero-candidate、inventory、path、budget、Ref provenance 和 Gateway transition
扩张反例继续通过；截断 candidate 即使仍暴露 Ref 也只允许平台 query-incomplete FINISH，不会安排 contract 必然拒绝的 method batch。
current-doc check 324/324 与 `git diff --check` PASS。

允许 AF_UNIX listener 的完整执行面完成 985 项测试，其中 980 项通过；其余五项不是本 Finding 的产品或 contract failure，而是
桌面应用自动更新后，ITER-003 frozen mature Codex CLI exact digest 校验按设计失败关闭。该环境事实、聚焦复现、不得改写历史 freeze
以及对 Acceptance 的限制已由 [FINDING-008-020](FINDING-008-020.md) 单独处置。因此这里不把完整 suite 误报为 PASS；本 Finding 的
system-contract 目标、实现与相关验证已经闭合，新的 live qualification 仍须使用 clean candidate 和全新 freeze，且 18/18 之前所有
后续产品 Gate 保持阻断。
