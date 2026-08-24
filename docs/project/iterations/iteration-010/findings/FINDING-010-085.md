---
id: FINDING-010-085
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [engineering, quality, project]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-084]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py, scripts/docs.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py, tests/test_engineering_question_cognition.py, tests/test_engineering_qa_source.py, tests/test_engineering_qa_live.py, tests/test_engineering_qa_preview_cli.py, tests/test_engineering_qa_alpha_cli.py, tests/test_engineering_qa_browser.py, tests/test_docs_gate.py, tests/test_iteration_007_readiness.py, tests]
iteration: ITER-010
classification: verification
scope: systemic
disposition: material-effect-omission-layer-deterministic-gate-closed
target: ITER-010-VERIFICATION
---

# FINDING-010-085：material-effect omission layer 的确定性 Gate 已闭合

## Observation and evidence

`FINDING-010-084` 的 corrective implementation 没有增加 same-package rewrite fuse。Review material-effect assessment 改为 closed
schema：每个 `DRAFT_OMITS_MATERIAL_EFFECT` 必须返回 1—16 个 unique exact effect statements，以及唯一
`APPLICATION_PACKAGE / DEFAULT_DRAFT` layer。challenge input 同时投影 challenged entry 已有的 exact Application observations：

- `APPLICATION_PACKAGE` effect 必须不在该 exact observation set 中，Finding 必须是 challenged entry 同 evidence class 的
  `INVESTIGATE_MISSING_EVIDENCE`；
- `DEFAULT_DRAFT` effect 必须精确存在于该 set 中，Finding 必须是包含 challenged entry 的
  `REWRITE_WITH_EXISTING_EVIDENCE`；
- Application 重建 assessment、Finding、Package entry/class 与 statement membership；错误 layer、remediation、entry 或 effect
  membership 全部以 `PROVIDER_RESPONSE_INVALID` 失败关闭。

既有确定性恢复链已升级为 application-layer effect → Verification successor → 新 typed observation → 新 Package → Answer →
comprehensive + challenge 双审；另一个对抗用例证明把 application-layer omission 伪装成 draft-only rewrite 会被 Application 拒绝。
Strategy/Prompt/Review Schema 为 `@24/@34/@9`，无工程、问题、关键词、符号、类、方法、fixture 或 Oracle 特判。

确定性验证结果：

- 三模块 focused 80/80 PASS；全部 Engineering QA 九模块 117/117 PASS；
- focused + docs Gate 150/150 PASS；focused + 历史 ITER-007 readiness oracle 82/82 PASS；
- `python3 scripts/docs.py check` 在本 Finding 与最终索引回写前为 478 current documents PASS；`compileall` 与 diff check PASS；
- 完整 `unittest discover` 共 1183 项。默认 sandbox 为 5 FAIL + 7 ERROR，其中额外 1 FAIL + 6 ERROR 精确来自 AF_UNIX socket
  权限拒绝；允许 AF_UNIX 后 1178 PASS，只保留 4 FAIL + 1 ERROR。

最后五项与此前 Gate 完全相同：四项 ITER-003 V-009 Adapter Conformance 冻结 digest historical hold，以及一项本机 Codex prepared
binary digest historical hold。没有 ITER-010 新失败；raw suite 仍保持 FAIL，不把冻结 hold 改写为 PASS。

Manifest exact bindings 为：answer hierarchy
`sha256:97d24a2a1c70965c6b6953f8665d2808762f0231c3626904013e209dd32e6947`，System fileset
`sha256:aa03a300a400fa816e154f41a814f6c34b939369bcd260107958b0b9c1ef0e96`，investigation protocol
`sha256:1bb9290e27ff0faefc0da7cd6079ff3b9263d9fb53f9f27867e12f72aa4cebde`。

## Decision and disposition

- material-effect omission layer、exact statements、Application membership/class/remediation 重算及 projected observation table 的
  deterministic Gate 已闭合，可以形成新的 clean candidate。
- run-031 永久保持 Q1 FAIL、Q2/Q3 与负测 NOT-RUN；本 Finding 不追认该 live。
- 下一 Gate 必须从新 clean candidate 执行 fresh DeepSeek Conformance、同一持续 Browser 三题、66,000-byte Provider 前负测及 raw
  Answer/Reviewer/challenge-assessment 独立复核；Production Activation 仍不执行。
