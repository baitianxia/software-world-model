---
id: FINDING-008-012
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai, architecture, engineering, quality]
depends_on: [ITER-008-SLICE-001, FINDING-008-010, FINDING-008-011, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
code: [src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_policy.json, validation/structure_world_model_iteration_008/capability/manifest.py]
tests: [tests/test_world_model_answer_strategy.py, tests/test_model_egress_gateway.py, tests/test_iteration_008_capability_harness.py, tests/test_iteration_008_capability_qualification.py]
iteration: ITER-008
classification: iteration-design
disposition: version-and-expose-canonical-bounded-proposal-contract
target: ITER-008-SLICE-001
---

# FINDING-008-012：完整 Capability 运行暴露 model-visible Proposal Contract 不充分

## Observation

修复 `FINDING-008-011` 后的 DeepSeek Conformance requalification 恰好执行 2 次请求并 PASS；其 Result 路径为
`var/iteration-008/capability/run-003-conformance-result/CC-DEEPSEEK-CHAT-NO-TOOLS-001-ccrun_bd3d72cf9895446a9dc455c81cb59bcd.json`，
result digest 为 `sha256:627ff4c9329f3e09d33b3b0d6b1ec5624d33006ab189f0fc9ea8a3ad22516438`，唯一 response model identity 为
`deepseek-v4-pro`。

其后的 Capability run-003 绑定 freeze
`sha256:05267d91cfe87347f48dab62f7b51c0268bf6908d9470f1fe5e075571c677ce8`，在第 25 次 dispatch 以
`TLS_FAILURE / PROVIDER_OUTCOME_UNKNOWN` 密封关闭：attempted request 为 25、completed request 为 24、completed case 为 11，
没有 retry。该失败只保留网络结果未知，不能裁决业务能力。随后使用 Adapter 同一 CA fallback `/etc/ssl/cert.pem` 的独立
credential-free 对照连续 5 次完成 verified TLS 1.3 handshake，说明通用 Python 默认 CA 探针的证书失败不代表 Adapter 路径失败；
也不能把 run-003 的已消费授权重试为业务证据。

新的 Capability run-004 绑定 freeze
`sha256:946952576429932cd9fc8d979ad16d2d520f346d9f0a660376691063ed2c9292`，无 retry 地完成全部 39 次 Provider request 与全部
18 个 Case，`unknown_count` 为 0，唯一模型 identity 为 `deepseek-v4-pro`，input/output tokens 为 88047/10249。closed Result
`var/iteration-008/capability/run-004-capability-result/closed-evaluation-result.json` 的 result digest 为
`sha256:b2308facc71a051d644fbbb78f07551f840d0c1b2790610de4d86c2e46f3ccca`，document digest 为
`sha256:6d698e8474c4ae3e3aa1f6705e5d7b4d2b2f6857602c7c923dedad554a11c876`。只有
`WM-JSS-I8-FIRST-CANDIDATES-001` 与 `WM-JSS-I8-DRAFT-017` PASS，其余 16 个 Case FAIL，因此没有 Capability Qualification 或
Production Activation。

## Evidence and root cause

逐 Case 的 sealed output 与 unchanged Oracle 对照显示，主要偏差不是 Provider transport：

- 多数调查输出给未选 operation 的 nullable 字段填入 Snapshot、search term、limit、direction 或 graph bounds，违反 exact
  contract projection；部分输出还把平台提供的 `step_index` 自增，而不是原样回显；
- `prompt@4` 只要求 graph bound 显式，却没有向模型给出本 evaluation contract 使用的 canonical `CALLS` direction/predicate 与
  depth/path/expansion 值；它也没有列出每个 operation 的 exact relevant/irrelevant field matrix；
- candidate batch 有时只选部分 canonical Ref，或在 path、inventory、budget-progress 场景提前 `FINISH`，说明“根据 typed Result
  继续调查”没有被收敛为可执行的通用状态规则；
- 负向 Case 的 finish reason 没有稳定区分 query-result、representation 与 business-discovery-recall 三层完整性；独立 Reviewer
  甚至在 discovery recall 为 `UNKNOWN` 且 Draft 断言不存在时返回 `APPROVE`。

其中 exact step echo 和三层完整性已经存在于 System Contract，`prompt@4` 也有较弱的总括要求；但 exact operation field shape、
本闭包 graph bounds 和基于 Result/问题意图的下一步规则没有完整进入 model-visible contract。Oracle 却按这些 canonical 值做 exact
projection。这是 iteration proposal/evaluation contract 不充分，而不是把 16 个模型输出分别解释为 16 个产品缺陷，也不能通过降低
Oracle、减少 Case、接受无关字段或对 DeepSeek/题目/工程加分支来修复。

## Impact and classification

System Contract 已经规定模型接收 capability schema/operation vocabulary、Application 重验 typed operation、调查按 sealed Result 推进、
Ref 保持 provenance、负向结论需要三层 COMPLETE、Reviewer 对完整性失败关闭。本 Finding 没有改变这些系统语义；它把既有不变量和
evaluation 需要的 canonical operation defaults 完整投影到模型可见 Proposal Contract。因此分类为 `iteration-design`，主处置写回
`ITER-008-SLICE-001`，无需修改 `docs/system/` 或新增 ADR。

该变更影响 Prompt、Strategy、proposal vocabulary、egress policy 与 Capability input identity。旧 Conformance PASS 与 run-003/004
Capability evidence永久保留，但不得授权新候选；新候选必须重新经过同候选 Conformance 和完整 Capability Gate。

## Decision and disposition

将 active bounded contract 版本化为：

- capability/Strategy `1.3.1`；
- `java-source-semantics-world-model-prompt@5`；
- `java-source-semantics-world-model-vocabulary@5`；
- bounded model-egress policy `@1.0.1`；
- suite/oracle identity `@1.3.1`，但保留原 18 Case、39 calls、Oracle verdict、禁止事件、metric、阈值和 no-retry 规则。

新 Prompt 以 Provider-independent 规则明确：平台 step/trace 原样回显；未使用字段为 null/empty；candidate canonical batch 选择；
inventory/direct/path/all-path 的 Ref provenance、field shape 与 graph bounds；声明清单、全部有界关系和 result-driven progress 的确定性
选择；以及 FINISH/Review 对三层完整性的失败关闭。不得加入 Provider、Case ID、项目、类、方法、答案、隐藏同义词或 fixture 特判。

## Verification after disposition

- contract/policy/capability focused 回归 39/39 PASS；包含 bounded investigation、World Model Answer/Product、evaluation grant、
  DeepSeek Adapter/Conformance/diagnostic 与 Capability harness/qualification 的受影响范围回归 115/115 PASS；
- full discovery 975/975 PASS；执行中仍有既有 SQLite connection `ResourceWarning`，但没有 test failure/error，进程退出码为 0；
- `python3 scripts/docs.py check` 对 316 份 current documents PASS，`git diff --check` PASS；
- suite/oracle 仍为 18 Case / 39 calls，fake transport exact count 与 verifier 回归包含在上述 PASS 中；正式 runtime 仍保持 Ark。

上述验证闭合后才形成 clean exact candidate，并使用用户当前明确的自主执行授权生成新的 2-call DeepSeek Conformance freeze；PASS 后
再生成一次新的 39-call Capability freeze。任一 live 运行仍不 retry，不继承旧授权，不提前执行正式 Web、hidden canary、SLICE-002 或
Production Activation。
