---
id: FINDING-010-089
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [engineering, quality, project]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-088]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py, scripts/docs.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py, tests/test_engineering_question_cognition.py, tests/test_engineering_qa_source.py, tests/test_engineering_qa_live.py, tests/test_engineering_qa_preview_cli.py, tests/test_engineering_qa_alpha_cli.py, tests/test_engineering_qa_browser.py, tests/test_docs_gate.py, tests/test_iteration_007_readiness.py, tests]
iteration: ITER-010
classification: verification
scope: systemic
disposition: verification-target-monotonic-preservation-deterministic-gate-closed
target: ITER-010-VERIFICATION
---

# FINDING-010-089：Verification target monotonic-preservation 的确定性 Gate 已闭合

## Observation and evidence

`FINDING-010-088` 的 corrective implementation 为每个 Verification input 投影
`target_disposition_preservation_contract`，绑定 exact checklist target、predecessor outcome，以及在 predecessor 为 `SUPPORTED` 时必须保留的
完整 material observation objects。补证模型必须复制每个旧 observation 的 kind、statement、evidence references 和相对顺序，可以在其间或
其后加入新 observation；Application 在 single-gap merge 时以 Application-owned observation identity 重算 retained subsequence，任何删除、
改写、重排或 non-supported replacement 都以 `PROVIDER_RESPONSE_INVALID` 失败关闭，不进入 successor Package seal。

确定性测试覆盖两个方向：合法 Verification 复制 predecessor observations 后增加新配置/副作用 observation，可以形成 successor Package、
重答并经双 Review 授权；只保留新 observation、静默删除 predecessor support 的 lossy replacement 被 merge Gate 拒绝。non-supported
predecessor gap-boundary fixture 继续允许真实新证据替换旧 limitation，不被 affirmative monotonic rule 冻结。结构化 fake role 也直接读取
preservation contract，证明真实 Adapter/Input Builder 路径不是只在 hand-written role 中成立。

Reviewer Prompt 同时要求 `APPLICATION_PACKAGE` semantic need 只为 challenged full-content entry 已可见的 helper/cache/write/notification/
external interaction 创建 caller-boundary typed observation；Verification 可以复用 predecessor Package support，不重读 consumed path，不要求
未挂载 callee internals。Strategy/Prompt 升为 `@26/@36`，Review Schema closed shape 未变，保持 `@9`；没有增加 24-call、rewrite、Review、
Provider retry 或 Provider switch fuse。

验证结果：

- 三模块 focused 80/80 PASS；全部 Engineering QA 九模块 117/117 PASS；
- focused + docs Gate 150/150 PASS；focused + 历史 ITER-007 readiness oracle 82/82 PASS；
- `python3 scripts/docs.py check` 为 483 current documents PASS；`compileall` 与 `git diff --check` PASS；
- 完整 `unittest discover` 共 1183 项。默认 sandbox 为 5 FAIL + 7 ERROR，其中额外 1 FAIL + 6 ERROR 精确来自 AF_UNIX socket
  `Operation not permitted`/listener unavailable；允许 AF_UNIX 后为 4 FAIL + 1 ERROR，即 1178 PASS。

最后五项与此前 Gate 完全相同：四项 ITER-003 V-009 Adapter Conformance 冻结 digest historical hold，以及一项本机 Codex prepared
binary digest historical hold。没有 ITER-010 新失败；raw suite 仍保持 FAIL，不把冻结 hold 改写为 PASS。

Manifest exact bindings 为：answer hierarchy
`sha256:97d24a2a1c70965c6b6953f8665d2808762f0231c3626904013e209dd32e6947`，System fileset
`sha256:825d01d9e4fc20777bb524820ba31fb846976faab6584abeeef58edcd58f0f31`，investigation protocol
`sha256:369be01ad3850ec2af5018c1ba316fd446ec19b0c4ee7f8284903dbdfc8865c7`。

## Decision and disposition

- supported Verification target 的 exact/relative-order monotonic preservation、lossy merge rejection 与 caller-visible effect-gap boundary 的
  deterministic Gate 已闭合，可以形成新的 clean candidate。
- run-033 永久保持 Q1 FAIL、Q2 FAIL、Q3 OUTCOME_UNKNOWN、66,000-byte Provider-before-call PASS；本 Finding 不追认该 live。
- 下一 Gate 必须从新 clean candidate 执行 fresh DeepSeek Conformance、同一持续 Browser 三题、66,000-byte Provider 前负测及 raw
  Answer/Reviewer/challenge-assessment 独立复核；Production Activation 仍不执行。
