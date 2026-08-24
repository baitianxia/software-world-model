---
id: FINDING-010-062
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-060, FINDING-010-061]
code: [src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: align-provider-schema-with-domain-investigation-binding-arrays
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-062：Provider Schema 必须闭合 Investigation 的非空唯一绑定数组

## Observation and evidence

clean candidate `be15a0a2a9ca8ceab4dfadd74b1dfd3854b0aeeb` / tree
`e887588026b8513d495838fd255868daf52d068c` 的隔离 clone 通过 Engineering QA 101/101 与 docs 455/455。run-022 fresh
DeepSeek Conformance 2/2 PASS，Result digest 为
`sha256:5022319bde7454f55de9a17509f134dd9519deb82fdf9d4e2fd1bda32db0aba3`，文件 SHA-256 为
`5b23bfa4f45975d4612c67e9edf1f15b253142e6efc0a228bddc502bdbc068a0`，actual model `deepseek-v4-pro`、retry 0。

fresh session authority `sha256:5f8b62b3b29f0c54fdbc6e7b6ed6d01791125e582c0b0f49bb4dc3d4f83258dd` 绑定 exact candidate、mall
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`、Source Profile、run-022 qualification 与 user root authorization。原登录题的 Question
Understanding 正常完成；第一个 Investigation 输出选择合法 `SOURCE` direct locator、合法 current basis entry、空 FINISH arrays 和具体
unknown，却把 `checklist_item_ids` 返回为 `[]`。Application Domain 的 `InvestigationStepProposal.create` 一直要求 checklist references
non-empty + unique，因此以“initial investigation output violates the domain contract”正确关闭。

根因不是 locator、来源权限或证据内容，而是 Provider-facing `_INVESTIGATION_OUTPUT_SCHEMA` 对 `checklist_item_ids` 和
`basis_entry_ids` 复用了允许空/重复的普通 string-array schema；Domain 却要求两者非空唯一。过去 Prompt 通常使模型碰巧返回全部 checklist
ID，不能证明 closed schema 与 Domain 一致。run-022 在 2 次 dispatch 后停止，没有提交 Q2/Q3 或超限输入；不能借 run-021 的结果补齐。
terminal receipt 文件 SHA-256 为 `8cb63307942eabc8eb07256eb896610fa25e6c17b02fda08578068996d684556`，document digest 为
`sha256:e85d31aec376088743f154960290e2870ebba1436ba23db68c62a78a6c632c9c`，记录 accepted question 1、dispatch 2、retry/switch 0、
verified TLS、private session/launch/terminal/SQLite files 和 Production `NOT_EXECUTED`。

## Decision and disposition

- Initial 与 Verification Investigation output schema 的 `checklist_item_ids` 改为 `minItems=1 + uniqueItems=true`，description 要求复制当前
  role input 的 exact IDs；`basis_entry_ids` 同样 non-empty + unique，并描述必须包含 exact `required_basis_entry_id`。
- Prompt 对每种动作明确同一约束；Domain、Application binding/eligibility checks 与失败关闭保持不变，不把空 checklist 自动补成全部项目，
  也不对非法 Provider output 做静默修复。
- 新回归直接以 run-022 同形空数组以及重复 checklist/basis 数组验证 `STRUCTURED_OUTPUT_INVALID`；该约束不含工程、题目、类、方法、fixture
  或 Oracle 特判。

Strategy / Initial / Verification Schema / Prompt identity 升为 `@16 / @8 / @8 / @25`。三模块定向 65/65 PASS；完整 Engineering QA、
docs/full 与新 clean/fresh live 仍待闭合，run-022 永久保留为 Schema/Domain mismatch 失败证据。
