---
id: FINDING-010-015
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-011, FINDING-010-012]
code: [src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_model_source.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: align-live-role-progression-with-authoritative-investigation-enum-values
target: src/software_world_model/ai_infrastructure/engineering_question_model_source.py
---

# FINDING-010-015：live Gateway 用大写常量拒绝了合法的小写 investigation operation

## Observation

候选 commit `b8360a306d775d693c33d99ac34e558706c55f64` 的第一次真实 `V-WEB-000` 尝试在 Question Understanding 后失败关闭。页面显示
`Engineering QA investigation Result has no current operation`；terminal receipt 证明只发生两次 DeepSeek HTTP dispatch，
Question Understanding `COMPLETED`，Initial Investigation 以 `STRUCTURED_OUTPUT_INVALID` 拒绝，retry/provider switch 均为 0。

Provider 保存的第二个 exact output 已符合 closed Schema：`operation` 为合法枚举值 `search`，evidence class 为 `SOURCE`，query 为
`JWT`，并绑定当前 Ledger entry。失败不是模型遗漏 operation，也不是 Source、TLS、credential 或 revision 问题。

## Evidence and root cause

- `InvestigationOperation.SEARCH/READ/PARSE.value` 与 closed JSON Schema 固定为 `search/read/parse`；`FINISH` 固定为大写；
- `EngineeringQuestionModelEgressPolicy._next_roles` 却把继续调查的三个值写死为 `SEARCH/READ/PARSE`；
- 本地 structured strategy 测试直接走 Application role adapters，没有经过 live egress role-progress policy，因此 58 项冻结前测试没有覆盖
  这个交界；
- terminal transport audit：2 HTTP dispatch、1 次成功 TLS handshake、connection reuse 1、credential resolution 2、retry 0、Provider
  switch 0、Production Activation `NOT_EXECUTED`；候选没有被伪写成可用。

根因是 `local-implementation / systemic`：所有合法非 FINISH initial/verification investigation 输出都会被 live Gateway 拒绝，不是单题、
单工程或 Prompt 偶发问题。

## Decision and disposition

`_next_roles` 改为直接比较 authoritative `InvestigationOperation` enum values，不新增大小写归一化、不放宽 Schema，也不改写 Provider
输出。新增 regression 同时覆盖 initial/verification 的 `search/read/parse/FINISH` 角色转移。

System Contract、Schema 和领域枚举原本一致且正确；本次只让 live policy 回到既有语义，因此处置到代码与测试，不需要 System 文档或
ADR。旧 candidate 与其一次性 live run 永久保持 FAIL；修复后必须重新测试、重新提交 clean candidate，并用新 exact subject/run grant
执行，不能重试或覆盖旧证据。

## Verification

修复后的五组相关模块测试 40/40 PASS，全部 8 个 ITER-010 Engineering QA 模块 59/59 PASS，文档 391/391 PASS，compile 与
`git diff --check` PASS。允许 AF_UNIX 的 full regression 共 1109 项，其中 1104 PASS；唯一 4 FAIL + 1 ERROR 的测试 identity、结果
类型和 marker 精确等于 `FINDING-008-020` / `FINDING-010-013` 的历史 hold，没有新增失败。真实 Web 仍须在新 clean candidate 上使用
剩余授权调用额度的新 run 重新证明。
