---
id: ITER-010-RESULT-SLICE-001-STOP-REDIRECT
kind: iteration-result
status: failed-preserved
authority: execution-evidence
owners: [product, project, architecture, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, ITER-010-RESULT-V-WEB-000-LIVE-RUN-009, ITER-010-RESULT-V-WEB-001-PUBLIC-DIRECTION-QUESTIONS, ITER-010-RESULT-V-WEB-001-USER-ONSITE-QUESTION, FINDING-010-027, FINDING-010-028]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/interface/engineering_qa_browser.py, src/software_world_model/interface/engineering_qa_browser_ui.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py, tests/test_engineering_qa_browser.py, tests]
iteration: ITER-010
product_goal_gate: V-000
product_goal_outcome: user-visible-general-engineering-qa-delta
product_goal_evaluation: independent-hidden-plus-live-ad-hoc
product_goal_verdict: FAIL
product_code_freeze_digest: sha256:69813d778adf9fa81c2915fadd1b00a600035119fea61e54f9f31879afee6acb
reflection_gate_status: PASS
reflection_gate_case_id: V-REFLECT-001
reflection_decision: REDIRECT
reflection_decision_owner: user
reflection_decision_ref: codex-user-message:sha256:d746968f58cea4d2b7689b5902c0ff97f42f63c93ffc4cbc40551cfa2c0359e0
reflection_issue_class: architecture
reflection_issue_scope: systemic
reflection_report_digest: sha256:049b63c990aa38ec5caa01eb192551c1382136c496e8fc8c3ea3826e8787c32b
critical_assumption_catalog_digest: sha256:26769498135692067597a1f59e0fbbc8b82502ebd5336f7fdb033a80e3baff82
production_activation: NOT_EXECUTED
---

# ITER-010 SLICE-001 Stop and Redirect Result

## Claim and scope

SLICE-001 完成了真实 `ENGINEERING_QA` 最小链和方向体验，但产品方向没有通过。14 个 loopback Web run、87 次角色 dispatch 和 14 个已打开
Citation 证明 World Model Cognition、结果驱动调查、Broker/Worker 只读执行、append-only Ledger、调查后 Package、Answer、独立 Review 与
页面交付可以运行；用户现场题却再次以类、方法和调用顺序为默认正文，独立 Reviewer 还批准了该答案。

用户消息 `codex-user-message:sha256:d746968f58cea4d2b7689b5902c0ff97f42f63c93ffc4cbc40551cfa2c0359e0`
指出实现者已经知道回答有问题却仍把裁决退回用户。结合既有“继续开发/修正”要求，该新消息构成 `REDIRECT`：最终工程问答目标不变，
但当前答案/审核方案已被预冻结停止条件证伪。它不是让实现者在同一 Iteration 中继续打补丁的 `CONTINUE`。

## Exact evidence

- public suite freeze：`sha256:f75f2e7881b8b57b4e9dd1b7ff01da9ac322bb4c853ed1853f881db9ca74f100`；successor freeze：
  `sha256:b509042147f9c02123652c8be3a884a7c5233fd4d8fb93e50bb5286f7d56b93d`；
- onsite product/question freeze：`sha256:69813d778adf9fa81c2915fadd1b00a600035119fea61e54f9f31879afee6acb`；exact candidate
  commit/tree：`8632904d4e97e152d6379d7ccc203f5a0234c34c` / `48b2ab7089a33e1fb4187909d102ad7241754a4f`；
- exact repository/revision：`mall` / `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`；Maven Snapshot
  `structure_snapshot_5033a7fc944141d08ecd5ad3879ce1ba`；Source Profile digest
  `sha256:4746c3e41de9d93c10b3b3eaa752b6e0959290e2e7772499a359031a7d497301`；
- onsite Result：`engineering_result_e5f3c335944de0f2f57e8f9fdd48b419` /
  `sha256:2aba0555d732282f5a925360c60f3a7e7ce383e55a49634bb4fd4a04dd992360`；Answer output digest
  `sha256:a349bf1edaa377eacf7319b97a98657949759d1e22ff6d9fb368327ae1660c75`；
- onsite Review：`engineering_review_8599387390a720f279c67844adf31033 / APPROVED`，findings 为空；output digest
  `sha256:1877579df5b0a3f049e910b84b09c6acda1a05d7b4d2d501667f4d4fa6241636`；
- onsite Package digest/seal：`sha256:a69bc1d3c8731144b87ac28b5806999193a23143ef2b669df7bcb96af62e1037` /
  `sha256:934a86397ec2f935df5cbd8c54e348dec8de0c91421c93ec037190fb641609ed`；Ledger seal
  `sha256:cd368301c7b3b949d7be2ccde7016eb4d4898848addfec1766381ca884b8e685`；
- exact 用户现场问题收据：`codex-user-message:sha256:684849e3116168fb6dd67fbc9f9f70df0e5d1b8385b5f72f711cd75d62f1e9c9`；
  direction decision 收据：`codex-user-message:sha256:d746968f58cea4d2b7689b5902c0ff97f42f63c93ffc4cbc40551cfa2c0359e0`。

## Product execution and direction failure

4 条公开题执行为 3 个 `APPROVED`、1 个 no-progress fail-closed，11 个 Citation 全部打开；现场登录题再形成 1 个 `APPROVED` Result，3 个
Citation 全部打开，console 为 `[]`。因此 `V-WEB-000` 和 `V-WEB-001` 的真实浏览器、Citation、安全与非生产技术检查成立。

方向失败发生在答案层而不是 transport 或 UI。现场答案正确覆盖 POST `/admin/login`、Service 认证/JWT 和 Filter 后续认证主链，但默认
正文依次展开 Controller、Service、`SecurityContextHolder`、token-null 分支和 Filter；没有先把用户登录概括为“验证身份 → 签发凭据 →
后续请求恢复认证”三个用户可理解阶段，并省略 exact Source 中 token 生成后的 `insertLoginLog(username)` 副作用。Reviewer 仍返回
`APPROVED` 且没有 Finding，说明现有 Review 不能识别“事实有据但答案层级和用户目标不匹配”。

`FINDING-010-028` 定位最早共同偏差：Question Understanding 的抽象层级只是自由文本；Answer Schema 只有扁平 Claim；Application 机械拼接
Claim 文本；Review Schema 没有可执行的层级/直接回答/实现细节主导判据。页面只是原样呈现 `answer.body`。该根因跨问题、Application 与
Strategy，和 ITER-009 的代码走读失败同类，不是登录题特例。

## Verification outcome

- `V-WEB-000`、`V-WEB-001`：**PASS**；真实 loopback Web、密封 Package、独立 Review、可打开 Citation、console 与非生产边界有执行证据；
- `V-ANSWER-001`：**FAIL**；公开计数阈值技术达标，但现场默认正文仍被实现步骤主导，违反“先给直接、层级匹配答案，代码按需”的 Case
  Claim 和停止条件；
- `V-REVIEW-001`：**FAIL**；独立 Reviewer 对方向不合格且有流程副作用遗漏的答案给出无 Finding `APPROVED`，没有触发 rewrite 或补证；
- `V-XD-001`：**FAIL**；真实链使用 Maven Cognition 与 query-time Source，但没有 accepted declaration/`CALLS` World Model Result，未达到
  同一答案组合已接受认知与新来源的冻结条件；
- `V-PREVIEW-001`：**FAIL / executed REDIRECT**；用户已明确指出不应再把已知方向问题退回给他裁决；
- `V-REFLECT-001`：**PASS / decision REDIRECT**；复盘、根因、假设、Finding 和用户收据完整；PASS 不表示方案通过；
- 其余尚未取得 exact Case Result 的 Slice1 Gate、全部 Slice2/3 Case、hidden canary、成熟源码 Agent 对照、三臂消融和 Acceptance：
  **NOT-RUN**；Production Activation：**NOT_EXECUTED**。

## Architecture reflection and continuation decision

### Assumption verdicts

| Assumption | Expected | Exact evidence refs | Verdict | Impact |
|---|---|---|---|---|
| A1 | 保持软件世界模型作为持久、版本化外部认知而非手册或缓存，同时可让提问期 Source 调查核实、补充或纠正本题认知，并能证明完整认知不只是 locator 装饰 | V-XD-001 | UNRESOLVED | Maven Cognition 与受控 Source 在同一真实链出现，但冻结 Case 要求的 accepted declaration/`CALLS` 未形成，不能证明完整认知相对 locator 导航的独立作用 |
| A2 | 独立 Investigation LLM 可以依据不可变原问题、exact World Model Cognition Context 和先前 Ledger 结果自适应提出下一步，而 Source Broker/Worker 能在不授予模型直接权限的情况下执行 | V-WEB-001 | SUPPORTED | 现场 run 的 7 次 Investigation 由 prior Ledger Result 驱动，6 个 Broker Decision 均授权只读执行；模型 direct Source/FS/Shell/network/credential authority 为 0 |
| A3 | 调查后密封、包内 Answer 和 Reviewer 独立补证可以同时保证直接答案、正确 Citation、失败关闭与真实首版体验 | V-ANSWER-001, V-REVIEW-001, V-PREVIEW-001 | FALSIFIED | Package/Citation/fail-close 成立，但 Answer 仍为代码走读，Reviewer 错误批准，用户方向 Gate 明确失败；当前答案/审核方案必须停止 |
| A4 | 相同认知—调查—Broker—Ledger—Package 协议能跨第二工程、来源组合和复杂失败模式泛化，不依赖问题、项目、关键词、符号、类、方法、fixture 或 Oracle 路由 | V-XD-001 | UNRESOLVED | 第一个真实工程尚未满足 accepted cognition + new Source 组合条件，第二工程和复杂失败模式未授权；不得宣称泛化 |
| A5 | 在不因调用次数裁剪调查或审核质量的前提下，完整认知与成熟源码 Agent 先通过零重大错误、boundary 正确且完整认知逐结论不退步的质量门；再以 locator-only/empty 同链为消融 control，证明完整认知有预提交质量或非 locator 调查成本增益，并计入建模成本与复用周期 | V-ANSWER-001 | UNRESOLVED | 现场方向质量先失败，成熟源码 Agent 与消融未执行；调用不限和零重试不能替代质量或价值证据 |

### Deviation and issue classification

偏差分类为 **systemic architecture/product direction**。调查、Broker、Ledger、Package 和 Citation 已按新架构运行，但用户目标到答案正文的
中间表示仍是自由文本层级加扁平 Claim；Reviewer 也只能对同一扁平 Draft 做模型判断，没有 Application 可执行的答案层次 invariant。
因此换 Prompt 措辞、隐藏类名或修补登录题不能关闭根因。

### Layer diagnosis and mature-source-Agent comparison

Source ground truth、exact revision、Maven Cognition 投影、typed Source Result、Broker/Worker、Ledger/Package、Provider transport、Citation 和
Web 呈现均有真实执行证据。最早共同偏差位于 Question Understanding → Answer representation：层级未成为可验证结构；Draft 随后按 Claim
顺序生成正文；Review 又批准了同一偏差；UI 只原样显示结果。

本 Slice 没有执行成熟源码 Agent 同题比较、三臂消融或第二工程，因此不能声称正确性、完整性、时延、成本或复杂度优于成熟 Agent。
已知事实反而是 10 次现场角色调用、283,781 input tokens 后仍未通过用户方向 Gate；这足以停止当前路线，但不足以评价替代路线的成本。

### Findings, alternatives and next risk

`FINDING-010-027` 保留现场答案的具体层级和登录日志遗漏；`FINDING-010-028` 把跨 ITER-009/010 的共同根因处置到
`ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST`。后续替代必须让 Question Understanding、typed Answer Plan、Application
acceptance、Reviewer 和页面共享同一答案层次：先回答用户目标与可见流程/影响，再按需展开实现证据，并对限制与未知单独建模。

下一最大风险是把转向缩减为新的 Prompt 文风或字符比例启发式。新 Proposal 必须先用通用结构和跨题型 Gate 证明不会依赖问题、工程、
关键词、符号、类、方法、fixture 或 Oracle；同时保留现有 exact revision、Broker/Worker 只读隔离、Package、Citation、独立 Review、
零重试和失败关闭资产。

### Decision and rationale

Decision: REDIRECT

Decision owner: user

Decision ref: codex-user-message:sha256:d746968f58cea4d2b7689b5902c0ff97f42f63c93ffc4cbc40551cfa2c0359e0

A3 被真实现场体验证伪，A1/A4/A5 未解决。用户指出实现者已知道答案有问题却仍要求用户重复判断；这关闭了 `CONTINUE` 路径，但他此前和
当前都要求继续修正最终目标，因此选择 `REDIRECT` 而不是放弃目标的 `REJECT`。依据治理规则，ITER-010 必须 rejected，Slice1 blocked，
Slice2/3 保持 proposed；任何后续实现必须在新 Iteration 重新 Proposal、Readiness 和逐 Slice 授权。

## Validity and preservation

本 Result 永久保留 ITER-010 的技术资产和产品方向失败，不因后续成功而改写。公开/现场 raw evidence、exact candidate、Package、Review、
Citation 和授权审计可用于下一 Proposal 的基线与对照，但不得进入 `accepted_capability_refs`，也不得让旧 Provider grant、question freeze、
qualification 或用户收据跨新产品代码自动继承。Production Activation 从未执行。
