---
id: FINDING-010-087
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [engineering, quality, project]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-086]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py, scripts/docs.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py, tests/test_engineering_question_cognition.py, tests/test_engineering_qa_source.py, tests/test_engineering_qa_live.py, tests/test_engineering_qa_preview_cli.py, tests/test_engineering_qa_alpha_cli.py, tests/test_engineering_qa_browser.py, tests/test_docs_gate.py, tests/test_iteration_007_readiness.py, tests]
iteration: ITER-010
classification: verification
scope: systemic
disposition: material-observation-source-resolution-deterministic-gate-closed
target: ITER-010-VERIFICATION
---

# FINDING-010-087：material observation source-reference resolver 的确定性 Gate 已闭合

## Observation and evidence

`FINDING-010-086` 的 corrective implementation 在 `QuestionEvidencePackage` 建立唯一 Application-owned resolver：先以 exact
`support_entry_*` 找到 support entry，再用该 entry 的 `source_reference` 匹配 material observation 的 `retrieval_item_*` evidence
references。challenge projection 与 `EngineeringAnswerReview.accept` 的 statement membership 重算复用该 resolver，不再各自比较不同 ID 域。

Review input 同时投影 closed layer precedence：空 observation projection 且存在 effect omission 时只允许 `APPLICATION_PACKAGE`；任一 effect
缺少 Application observation 时当前轮只返回缺失 effects 并走同 evidence class Verification；只有全部 omitted statements 都精确存在于
投影时才允许 `DEFAULT_DRAFT` 与 challenged-entry rewrite。Prompt 明确禁止把 default Claim 已覆盖的 effect 再列为 omission。Strategy/Prompt
升级为 `@25/@35`，Review Schema 的 closed shape 未变，保持 `@9`；未增加 rewrite、Review、24-call 或 Provider retry fuse。

确定性测试直接构造 observation evidence reference 与 Package entry ID 不同的真实域形状，证明 challenge 投影不再为空；同一测试又证明 exact
projected statement 可合法进入 `DEFAULT_DRAFT` rewrite，而不在投影中的 statement 伪装为该 layer 会被 Application 以
`PROVIDER_RESPONSE_INVALID` 拒绝。验证结果：

- 三模块 focused 80/80 PASS；全部 Engineering QA 九模块 117/117 PASS；
- focused + docs Gate 150/150 PASS；focused + 历史 ITER-007 readiness oracle 82/82 PASS；
- `python3 scripts/docs.py check` 为 481 current documents PASS；`compileall` 与 `git diff --check` PASS；
- 完整 `unittest discover` 共 1183 项。默认 sandbox 为 5 FAIL + 7 ERROR，其中额外 1 FAIL + 6 ERROR 精确来自 AF_UNIX socket
  `Operation not permitted`/listener unavailable；允许 AF_UNIX 后为 4 FAIL + 1 ERROR，即 1178 PASS。

最后五项与此前 Gate 完全相同：四项 ITER-003 V-009 Adapter Conformance 冻结 digest historical hold，以及一项本机 Codex prepared
binary digest historical hold。没有 ITER-010 新失败；raw suite 仍保持 FAIL，不把冻结 hold 改写为 PASS。

Manifest exact bindings 为：answer hierarchy
`sha256:97d24a2a1c70965c6b6953f8665d2808762f0231c3626904013e209dd32e6947`，System fileset
`sha256:aec7d46872fcc0c8c5d16cd53ad8f28f8cc98fac1e39065a63dded40c9b7076f`，investigation protocol
`sha256:1bb9290e27ff0faefc0da7cd6079ff3b9263d9fb53f9f27867e12f72aa4cebde`。

## Decision and disposition

- material observation 的 exact entry → source-reference resolution、challenge/Application 单一 resolver 和 layer precedence 的
  deterministic Gate 已闭合，可以形成新的 clean candidate。
- run-032 永久保持 Q1 PASS、Q2 FAIL、Q3 OUTCOME_UNKNOWN、66,000-byte Provider-before-call PASS；本 Finding 不追认该 live。
- 下一 Gate 必须从新 clean candidate 执行 fresh DeepSeek Conformance、同一持续 Browser 三题、66,000-byte Provider 前负测及 raw
  Answer/Reviewer/challenge-assessment 独立复核；Production Activation 仍不执行。
