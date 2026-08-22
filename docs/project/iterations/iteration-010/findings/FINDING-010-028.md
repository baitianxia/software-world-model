---
id: FINDING-010-028
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [product, architecture, application, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, ITER-010-RESULT-V-WEB-001-USER-ONSITE-QUESTION, FINDING-010-027]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/interface/engineering_qa_browser_ui.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py, tests/test_engineering_qa_browser.py]
iteration: ITER-010
classification: roadmap
scope: systemic
disposition: redirect-to-typed-answer-hierarchy-and-directional-review-gate
target: ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST
---

# FINDING-010-028：答案与审核只有扁平 Claim，无法执行“答案优先”方向约束

## Observation

ITER-010 的 Prompt 已明确要求 Answer “按请求的抽象层级先给直接结论”，Reviewer 也被要求只批准直接、完整且层级合适的答案；真实现场题
仍按 Controller、Service、Filter 的类/方法和调用顺序展开，独立 Reviewer 返回 `APPROVED`。这不是页面漏渲染：页面原样展示
Application 交付的 `answer.body`，而该正文就是 Answer Proposal 中所有 Claim 文本的顺序拼接。

这与 ITER-009 的三条代码走读式答案具有同一方向症状。ITER-010 改造了认知、调查、Broker、Ledger、Package 和补证边界，但没有改变
“用户目标/抽象层级如何约束答案结构和审核”的可执行表示，因此真实新链仍重现旧方向失败。

## Evidence and root cause

- `QuestionUnderstandingProposal.requested_abstraction_level` 是最大 1,024 bytes 的任意字符串；Application 只验证原问题、Request digest 和
  response language，不把层级归一为受控语义，也不验证后续 Answer 是否履行该层级；
- `ENGINEERING_QUESTION_ANSWER_OUTPUT_SCHEMA` 只有 `response_language` 和扁平 `claims[]`；每个 Claim 只有
  `claim_id/kind/text/evidence_entry_ids`，没有“直接答案、阶段、影响、限制、可选实现证据”等角色，也没有重要性、展开条件或细节预算；
- `EngineeringAnswerDraft.accept()` 以 `"\n\n".join(item.text for item in proposal.claims)` 机械生成用户正文。Application 能验证 Citation
  分区，却无法区分“先回答登录三阶段”与“逐方法走读”，也无法阻止后者占据默认正文；
- Review 输出只有 decision、Finding 和可选 Verification Request。Finding 可绑定 checklist/claim，但没有结构化的抽象层级、直接回答、
  实现细节占比或用户可用性判据；当模型错误返回 `APPROVED` 时，Application 只验证包、Draft、上下文和 Finding 形状，不能拒绝方向不合格
  的批准；
- 页面通过 `textContent` 原样展示 `answer.body`。因此 UI 不是最早偏差层；最早共同偏差位于 Question Understanding → Answer Plan/Schema →
  Review quality contract，范围跨 Application 与 Strategy，属于 systemic product/architecture direction，而不是现场题或模型随机性个案；
- exact 现场 Result 为 `engineering_result_e5f3c335944de0f2f57e8f9fdd48b419` /
  `sha256:2aba0555d732282f5a925360c60f3a7e7ce383e55a49634bb4fd4a04dd992360`，Review
  `engineering_review_8599387390a720f279c67844adf31033 / APPROVED` 且 findings 为空；用户方向决定收据为
  `codex-user-message:sha256:d746968f58cea4d2b7689b5902c0ff97f42f63c93ffc4cbc40551cfa2c0359e0`。

## Decision and disposition

不在已被方向 Gate 否决的 ITER-010 中追加 Prompt 文案、登录题特判或对 Claim 字符串做启发式重排。该路线会让同一结构在新问题上继续
退化，而且无法证明不是项目、题目、符号、类或方法特判。

主要处置回到 `ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST`。下一 Proposal 必须先选择并验证通用、typed 的答案层次表示：至少
机械区分直接答案、用户可见流程/影响、诚实边界和仅在需要时展开的实现证据；Answer Proposal、Application acceptance、Reviewer rubric
和页面投影必须消费同一结构。Reviewer 必须能因“默认正文被实现步骤主导”“没有先回答用户目标”或“关键流程副作用遗漏”而给出
可执行的 rewrite/reject Finding，且要以跨题型真实问题证明，不允许问题/工程/关键词/符号/类/方法/fixture/Oracle 分支。

该 Candidate 仍是 planning-only。`REDIRECT` 使 ITER-010 rejected、Slice1 blocked；任何新产品代码必须来自新的 Iteration Proposal、
Readiness 和用户逐 Slice 授权，不能把本 Finding 当成编码许可。
