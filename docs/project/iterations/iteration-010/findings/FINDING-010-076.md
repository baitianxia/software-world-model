---
id: FINDING-010-076
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [engineering, quality, project]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-075]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py, scripts/docs.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py, tests/test_engineering_question_cognition.py, tests/test_engineering_qa_source.py, tests/test_engineering_qa_live.py, tests/test_engineering_qa_preview_cli.py, tests/test_engineering_qa_alpha_cli.py, tests/test_engineering_qa_browser.py, tests/test_docs_gate.py, tests/test_iteration_007_readiness.py, tests]
iteration: ITER-010
classification: verification
scope: systemic
disposition: deterministic-gate-closed-exact-historical-hold-preserved
target: ITER-010-VERIFICATION
---

# FINDING-010-076：fresh evidence-boundary challenge 的确定性 Gate 已闭合

## Observation and evidence

`FINDING-010-075` 将 finding-free comprehensive Review 降为 provisional；Application 只在另一个 fresh
`EVIDENCE_BOUNDARY_CHALLENGE` 无 Finding 时授权答案。Strategy 从当前 Package/Draft 投影 cited configuration placeholder、Claim 中
cited content 未出现的 HTTP status literal，以及 Draft 提及但实现未挂载的同 application type；Gateway 在 Provider 前强制
`Answer → COMPREHENSIVE → EVIDENCE_BOUNDARY_CHALLENGE` 顺序。import 挂载比较使用 package-qualified identity，异包同名 Java
文件不能掩盖缺失实现；投影仍只是 review lead，不替代 Reviewer 的语义裁决。

确定性验证得到：

- 三模块 focused 组合 78/78 PASS；全部 Engineering QA 九模块 115/115 PASS；
- focused + docs Gate 148/148 PASS；focused + 历史 ITER-007 readiness oracle 80/80 PASS；
- `python3 scripts/docs.py check` 在本 Finding 与索引最终回写后报告 470 current documents PASS；`compileall` 与 `git diff --check` PASS；
- 完整 `unittest discover` 共 1181 项。默认 sandbox 为 5 FAIL + 7 ERROR，其中额外 1 FAIL + 6 ERROR 精确来自 AF_UNIX socket
  权限拒绝；允许 AF_UNIX 后 1176 PASS，仅保留 4 FAIL + 1 ERROR。

该五项与此前 Gate 完全相同：四项 ITER-003 V-009 Adapter Conformance 冻结 digest historical hold，以及一项本机 Codex prepared
binary digest historical hold。没有 ITER-010 新失败；raw suite 仍保持 FAIL，本 Finding 不把冻结历史 hold 改写为 PASS。

## Decision and disposition

- 双 Review focus、三类通用 evidence-boundary lead、最终授权绑定、预算预留与文档 Manifest Gate 的确定性验证已闭合，可以形成新的
  clean candidate。
- run-027 永久保持 Q1 PASS + Q2/Q3 FAIL，不因本次修复或确定性 PASS 被追认。
- 下一 Gate 必须从该 clean candidate 执行 fresh DeepSeek Conformance、同一持续 Browser 三题、66,000-byte Provider 前负测与 raw
  Answer/Reviewer 独立复核；Production Activation 仍不执行。
