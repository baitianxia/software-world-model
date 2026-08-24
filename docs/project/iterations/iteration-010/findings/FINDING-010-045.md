---
id: FINDING-010-045
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-044]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_model_source.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: update-current-engineering-qa-contract
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-045：短直答摘要需要受控空 Observation link，不能与 coverage Limitation 混同

## Observation and evidence

`FINDING-010-044` 修复后的 clean candidate `47a96b6f4ec0ad87f29578667308e60a170d887e` / tree
`2aeb628ed3e1d2a05df86644e40a0d2580866024` 取得 fresh DeepSeek Conformance 2/2 PASS，Result digest
`sha256:6097fa352119b9cf767fedc9cef97169045b9af47a609cf942b6985373d44fa6`，request 2、retry 0、actual model
`deepseek-v4-pro`。fresh Session Authority
`sha256:95a4866869a38786c3f75b98398063da501663d9b96f6c3b3d1ba6efef39362c` 再次提交原现场题。

该题完成 Understanding、4 次 Investigation 和 Answer，共 7 次 dispatch。model call
`model_call_29a5fcc38d3c4b9abd25a74ec1d4cb68` 返回了新的、方向上正确的结构：

- 首个 DIRECT_ANSWER 用一句话直接概括 endpoint、凭据验证、成功 token/tokenHead 和失败信息，并保留两个 support citations；
- 后续 7 个用户可见 Claim 分别且无重复地绑定完整 Package observations，覆盖入口、凭据、加载用户、密码/disabled 校验、JWT、成功/失败、
  `SecurityContextHolder` 与包含管理员 ID/时间/IP 的登录日志；
- 为避免与后续观察重复，DIRECT_ANSWER 的 `material_observation_ids` 为空。既有 Claim value rule 只允许 coverage-only LIMITATION 使用空 link，
  因此在 Draft 前以 `Engineering QA answer output violates the domain contract` 失败关闭，Review 未发生。

空-link affirmative direct summary 与 coverage Limitation 的语义不同：它仍必须引用 support，只做后续事实的简短导航，不取得 observation
coverage；coverage Limitation 只能引用 boundary/audit 并表达边界。若一律禁止前者，模型只能在直答中重复全部 observation 或不再先直答，
两者都违背当前答案方向。

会话已优雅停止；terminal receipt digest
`sha256:d4d033a8e5e5695d38aac5763fdd94c0c048d98635275748ff28e8956b56d82e`，accepted question 1、dispatch 7、retry/switch 0、
Production Activation `NOT_EXECUTED`，Gateway/launch/terminal 文件均为 `0600`。该 run 仍是失败证据。

## Decision and disposition

- `EngineeringAnswerClaimProposal` 允许 affirmative `DIRECT_ANSWER` 使用空 observation 集合作为摘要；其他 affirmative role 仍必须带 observation，
  direct limitation 仍绑定 limitation observation，只有末尾 coverage-only Limitation 享有既有 boundary 空-link 例外；
- Application 要求空-link affirmative summary 的所有 checklist disposition 均为 SUPPORTED；其 evidence IDs 仍必须属于 support/citation；摘要不计入
  observation coverage，因此后续默认 Claim 仍须覆盖精确 observation 全集；
- Answer/Reviewer Prompt 和 current System Contract 明确摘要不得引入后续 Claim 未展开的条件、结果、状态变化、副作用或 limitation，Reviewer
  必须审核语义等价和 Citation。该规则无题目、工程或 Provider 特判，最终三题必须在新 clean candidate/fresh session 上重跑。
