---
id: FINDING-003-015
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-003-SLICE-001, FINDING-003-014, ITER-003-VERIFICATION]
code: [src/software_world_model/ai_infrastructure/world_model_answer_strategy.py, validation/structure_world_model_iteration_003/v009]
tests: [tests/test_world_model_answer_strategy.py, tests/test_iteration_003_v009.py]
iteration: ITER-003
classification: iteration-design
disposition: clarify-owner-enums-and-requalify-entire-v009-input-set
target: ITER-003-SLICE-001
---

# FINDING-003-015：首轮 V-009 暴露了 Prompt owner 枚举歧义

## Observation

checkpoint `cf376b3f90ef4ff6c83af5218d43e5dc3aa5c9da` 上的 exact Adapter
Conformance PASS；随后七个 closed CE Case 各运行一次，最终为 6 PASS、1 FAIL、0 UNKNOWN。
唯一失败项 `WM-CE-GAP-004` 返回的 `status` 与 `code` 均正确，但把 owner 写成自然语言
`Structure View` / `Knowledge Use`，冻结 Oracle 要求的是平台枚举 `STRUCTURE_VIEW` /
`KNOWLEDGE_USE`。

首轮 Prompt 只写了 “Structure View owns” 和 “Knowledge Use separately owns”，没有声明输出字段
必须使用 exact uppercase enum。模型输出与该自然语言相符，独立 evaluator 仍正确地按 exact projection
判为 FAIL。因此这是 Prompt 合同不充分，不是 evaluator 误判，也不能通过选择性重跑修复。

## Evidence

- input freeze：`ITER-003-V009-EXACT-INPUTS@1.0.0`，digest
  `sha256:822a20fc5df6439f0d0b95d5125a00e8d8240998a71154b27c0572c4b704cf74`；
- Conformance binding：`sha256:16ae77e5a5418e6228eb9b1046c462c41f23785a944e9f7a8f74ad69c08183e0`，
  两个 Provider 请求均 PASS；
- closed Result：`evaluation_result_fcc6a70f04ea41faab9cb9fca837b19c` /
  `sha256:8392c313b2256668fe56cd2bef7c96ec19f33f840fd905cf501b712191c8c988`；
- 原始证据目录：`var/iteration-003/v009/cf376b3f90ef4ff6c83af5218d43e5dc3aa5c9da/`；
- FAIL normalized output 和独立 review 均已 O_EXCL 密封；没有 qualification proof，baseline 未运行。

## Impact and classification

该发现改变 V-009 Strategy/Prompt 的 exact identity，并要求新 checkpoint 上完整重跑
Conformance 和全部七 Case，但不改变 System Contract 或冻结 suite/oracle，故分类为
`iteration-design`。首轮 FAIL 是正式开发证据，不能删除、覆盖或改写成 PASS。

## Decision and disposition

Strategy 从 `1.0.0` 升为 `1.0.1`，Prompt 从
`snapshot-first-world-model-proposal-prompt@1` 升为 `@2`；仅把两个 owner 的输出要求明确为
exact `STRUCTURE_VIEW` 与 `KNOWLEDGE_USE`，不修改 suite、Oracle、Evaluator、Provider、Adapter、
Model、Tool 或 resource policy。

新 `ITER-003-V009-EXACT-INPUTS@1.0.1` 必须显式绑定首轮 FAIL 身份。由于 input freeze 与 Prompt
均漂移，旧 Conformance binding 不可复用；必须从新的 enclosing clean checkpoint 重新运行两调用
Conformance，再一次性运行全部七 Case。只有新 Result 为 7 PASS、FAIL/UNKNOWN=0 且 Validity
`VALID` 才能进入两条 baseline。

## Verification after disposition

单元测试继续验证 exact prompt/strategy digest 与 oracle-free Manifest；fake transport 的完整 V-009
harness 必须从新 input freeze 形成 7/7 PASS。真实重跑结果只能记录为新的 immutable evidence，不能
覆盖首轮目录。
