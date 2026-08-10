---
id: FINDING-003-016
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-003-SLICE-001, FINDING-003-015, ITER-003-VERIFICATION]
code: [src/software_world_model/ai_infrastructure/world_model_answer_strategy.py, validation/structure_world_model_iteration_003/v009]
tests: [tests/test_world_model_answer_strategy.py, tests/test_iteration_003_v009.py]
iteration: ITER-003
classification: iteration-design
disposition: clarify-partial-coverage-status-contract-and-requalify-entire-v009-input-set
target: ITER-003-SLICE-001
---

# FINDING-003-016：第二轮 V-009 暴露了 PARTIAL coverage 的 status 歧义

## Observation

checkpoint `4f884a28c954de8b7edf555092fe08b81bce47ef` 上的 exact Adapter
Conformance 再次 PASS；随后七个 closed CE Case 各运行一次，最终仍为 6 PASS、1 FAIL、0
UNKNOWN。唯一失败项 `WM-CE-GAP-004` 已正确返回 owner 枚举 `STRUCTURE_VIEW` /
`KNOWLEDGE_USE`，但在 `coverage=PARTIAL` 且 `pagination_complete=true` 时把
`need_assessment.status` 返回为 `SATISFIED_SUPPORTED_NEGATIVE`，冻结 Oracle 要求
`KNOWLEDGE_GAP`。

Strategy `1.0.1` 的 Prompt 已说 PARTIAL coverage 不能成为 supported negative，也使用了
“separate KNOWLEDGE_GAP need_assessment”措辞，但没有逐字段声明
`need_assessment.status=KNOWLEDGE_GAP`，也没有明确 coverage 对 pagination completeness 的优先级。
独立 evaluator 因 exact projection mismatch 及 `SUPPORTED_NEGATIVE` / `LIMITATION_HIDDEN`
forbidden events 判 FAIL 是正确行为；不得通过选择性重跑或输出后处理掩盖。

## Evidence

- input freeze：`ITER-003-V009-EXACT-INPUTS@1.0.1`，digest
  `sha256:b4a90907704ffdd888d63718c7118182c8565d0df66d63f35b425d26e2ee1293`；
- Conformance binding：`sha256:17b3ffa926041032e44714ef17c2126f9cb142fe80c954b8d7ee993d86b20868`，
  两个 Provider 请求均 PASS；
- closed Result：`evaluation_result_9f02ae0784aa4ab8879fe836b7ccff64` /
  `sha256:58933ff893e1dd808009ef7de28968831285c19a1e9fcb9f9ad90caef1f8aa3e`；
- 原始证据目录：`var/iteration-003/v009/4f884a28c954de8b7edf555092fe08b81bce47ef/`；
- FAIL normalized output 与独立 review 均已 O_EXCL 密封；没有 qualification proof，baseline 未运行。

## Impact and classification

该发现只澄清本轮通用 proposal Prompt 对既有 System 语义的编码，并要求新 checkpoint 上完整重跑
Conformance 与全部七 Case；不改变 System Contract、suite、Oracle 或 evaluator，故分类为
`iteration-design`。第二轮 FAIL 与第一轮 FAIL 都是正式开发证据，必须永久保留。

## Decision and disposition

Strategy 从 `1.0.1` 升为 `1.0.2`，Prompt 从
`snapshot-first-world-model-proposal-prompt@2` 升为 `@3`。只对
`VIEW_LIMITATION_AND_KNOWLEDGE_GAP` 增加三项通用约束：coverage 优先于 pagination
completeness；两个对象的 `status`、`code`、`owner` 都使用 exact 字段和值；PARTIAL coverage
禁止输出 `SATISFIED_SUPPORTED_NEGATIVE`。不修改 schema、suite、Oracle、Evaluator、Provider、
Adapter、Model、Tool 或 resource policy，也不在模型输出后做修正。

新 `ITER-003-V009-EXACT-INPUTS@1.0.2` 显式绑定第二轮 FAIL；`@1.0.1` 又保留到首轮的
predecessor 链。Prompt/Strategy/input freeze 已漂移，因此第二轮 Conformance binding 不可复用，必须从
新的 enclosing clean checkpoint 重新运行两调用 Conformance，再一次性运行全部七 Case。只有新 Result
达到 7 PASS、FAIL/UNKNOWN=0 且 Validity `VALID` 才能进入两条 baseline。

## Verification after disposition

单元测试验证 PARTIAL 优先级、两个 exact status/owner 和禁止 supported-negative 的 Prompt 合同；fake
transport 的完整 V-009 harness 必须从新 input freeze 形成 7/7 PASS。真实重跑结果写入新的 immutable
checkpoint 目录，不覆盖前两轮证据。
