---
id: FINDING-010-072
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-070, FINDING-010-071]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py, tests/test_engineering_question_cognition.py, tests/test_engineering_qa_source.py, tests/test_engineering_qa_live.py, tests/test_engineering_qa_preview_cli.py, tests/test_engineering_qa_alpha_cli.py, tests/test_engineering_qa_browser.py, tests/test_iteration_007_readiness.py, tests/test_docs_gate.py, tests]
iteration: ITER-010
classification: verification
scope: systemic
disposition: preserve-exact-historical-full-suite-hold-after-verification-gap-delta-controls
target: ITER-010-VERIFICATION
---

# FINDING-010-072：Verification gap-delta 与补证控制修复无新增完整回归失败

## Observation and evidence

`FINDING-010-070/071` 处置后：

- Initial/Verification/Strategy 三模块 72/72 PASS；全部 Engineering QA 九模块 109/109 PASS；含 docs Gate 的四模块组合 142/142 PASS，
  历史 ITER-007 oracle 与三模块组合 74/74 PASS；
- `compileall` 与 `git diff --check` PASS；包含本 Finding 的 current docs generate/check 466/466 PASS；
- 默认 workspace sandbox 的 full discovery 共 1175 项，raw 为 5 FAIL + 7 ERROR，其中额外 1 FAIL + 6 ERROR 精确来自 AF_UNIX
  listener/connect 被 sandbox 拒绝；
- 允许本机 AF_UNIX 的同一 full discovery 共 1175 项，其中 1170 PASS，raw 唯一 4 FAIL + 1 ERROR：3 FAIL + 1 ERROR 为冻结 V-009
  Adapter Conformance implementation drift，另 1 FAIL 为本机 Codex binary digest 与历史 prepared digest 不同；identity、结果类型与 marker
  与 `FINDING-010-069` 完全相同，没有 ITER-010 新失败。

新增回归机械覆盖：Verification FINISH 只接受 Request 指定 gap、越权 checklist 失败关闭、trusted merge 保序替换唯一目标且保留非目标
对象、predecessor Package full-content path 进入 consumed set 并移除同路径 locator、最近 Broker rejection 显式投影且后续授权 decision
清除。Provider Schema/Prompt identity 分别升级为 Initial/Verification `@10`、Strategy `@18`、Prompt `@28`。

## Decision and disposition

raw full suite 继续记录为 FAIL，不能写成全通过；本轮 deterministic Gate 为
`PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD`。该证据只允许提交并冻结新的 clean candidate，再执行 fresh DeepSeek Conformance、同一持续
Browser 会话三题、66,000-byte Provider 前负测和 raw Answer/Reviewer 独立复核；它不追认 run-025、不提前给
`V-EXPERIENCE/V-ANSWER-REWORK/V-REVIEW` 下 PASS，也不授权 Production Activation。
