---
id: FINDING-010-016
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-003, FINDING-010-015]
code: [src/software_world_model/ai_infrastructure/openai_responses_adapter.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_openai_responses_adapter.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: align-provider-visible-array-constraints-local-schema-validation-and-domain-finish-invariants
target: src/software_world_model/ai_infrastructure/openai_responses_adapter.py
---

# FINDING-010-016：FINISH closed Schema 未表达并重验非空证据引用

## Observation

修复 live role progression 后，candidate `50b08b542e5ea33bed30cdd99e32540f68b1abc7` 的第二次真实 `V-WEB-000` 尝试完成
Question Understanding 与三次 Initial Investigation dispatch，随后页面以
`Engineering QA initial investigation output violates the domain contract` 失败关闭。第四个 Provider output 是字段完整、无额外 key 的
`FINISH`，但 `check-3`、`check-4`、`check-5` 的 `evidence_references` 为空。

领域 `ChecklistDisposition.create` 一直正确要求每个 disposition 至少绑定一个 evidence 或 boundary reference；当证据不足时，UNKNOWN
也必须引用记录该边界的 Ledger entry。Provider-visible investigation Schema 却只声明普通 string array，角色 Prompt 也只要求诚实
disposition，没有写明 UNKNOWN/CONFLICT/FAILURE 同样禁止空引用。共享 `OutputSchemaDefinition` 又没有机械重验已经在其他 Schema 中使用的
`minItems` / `uniqueItems`，因此 Gateway 把该输出记录为 `COMPLETED`，直到领域适配才失败关闭。

## Evidence and root cause

- run `web-v-web-000-004` 的 terminal receipt：4 HTTP dispatch、1 次成功 TLS handshake、connection reuse 3、credential resolution 4、
  retry 0、Provider switch 0、Production Activation `NOT_EXECUTED`；
- 保存的第四个 exact output 使用 `operation=FINISH`，六个 checklist disposition 中三个给出空数组；
- closed Schema 的 `evidence_references` 原为无 cardinality/uniqueness 约束的 `_STRING_ARRAY_SCHEMA`；
- `OutputSchemaDefinition._validate_output` 原来只遍历 array items，不检查 `minItems`、`maxItems` 或 `uniqueItems`；
- Application 没有接纳该无引用输出，安全边界正确失败关闭，但 closed-schema 审计语义与领域 contract 不一致，并浪费了已经授权的 live
  dispatch。

根因是 `local-implementation / systemic`：任何声明 array cardinality 的 Provider output 都可能绕过 shared local schema validator；任一
Initial/Verification Investigation 的空引用 FINISH 又会在较晚的领域适配处失败。

## Decision and disposition

investigation output Schema 升级为 `@2`，为每个 finish disposition 的 `evidence_references` 声明 `minItems: 1` 与
`uniqueItems: true`。共享 closed-schema validator 同步验证 array bounds、定义合法性与 uniqueness；Prompt identity 升级为 `@2`，明确
所有 FINISH outcome 都必须引用当前输入中的 exact evidence/boundary entry，并在已有 search locator 足以缩小未知时优先 read/parse。

不自动补造引用、不把空数组归一化成某个 Ledger entry，也不放宽领域 Contract。System Contract 原本已经要求 exact closed schema、
boundary/audit 分区和逐结论证据，本次只让 Provider schema、共享 validator 与既有领域 invariant 对齐，因此处置到代码与测试，不改 System
语义或 ADR。由于共享 DeepSeek implementation manifest 包含 `openai_responses_adapter.py`，旧 Conformance Result 在此变更后必须按现有
规则视为 stale；再次 live 前须取得新的 exact 2-call qualification。

## Verification

新增回归验证合法单引用、空数组、重复数组与非法 bounds；同时冻结 Initial/Verification Schema `@2` 的非空唯一引用约束及 Prompt
`@2` 的 boundary-reference 指令。三组直接相关模块 28/28 PASS；扩展后的 ITER-010 focused 69/69、docs 393/393、`py_compile` 与
`git diff --check` PASS。允许 AF_UNIX 的 full discovery 共 1112 项，其中 1107 PASS；唯一 4 FAIL + 1 ERROR 的 exact identity、类型和
marker 与 `FINDING-008-020` 的历史 hold 相同，没有新增失败。新的 live qualification/run 仍须在 clean candidate 上执行。
