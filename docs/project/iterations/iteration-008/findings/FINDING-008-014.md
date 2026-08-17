---
id: FINDING-008-014
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [architecture, application, ai, engineering, quality]
depends_on: [ITER-008-SLICE-001, FINDING-008-002, FINDING-008-013, SYS-ADR-015, SYS-CONTRACT-AI-CAPABILITY-EVALUATION, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY]
code: [src/software_world_model/application_services/bounded_world_model_investigation.py, src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, src/software_world_model/interface/world_model_product.py, validation/structure_world_model_iteration_008/capability/manifest.py]
tests: [tests/test_bounded_world_model_investigation.py, tests/test_world_model_answer_strategy.py, tests/test_iteration_008_capability_harness.py, tests/test_iteration_008_capability_qualification.py]
iteration: ITER-008
classification: system-contract
disposition: compile-semantic-intent-and-repair-product-faithful-qualification
target: SYS-ADR-015
---

# FINDING-008-014：run-006 暴露 authority 编译边界与产品不一致的资格状态

## Observation

`1.3.2` clean candidate `6e443a324d2289321457b6d828163d0dc9005300`（tree
`8ceb39e78eace1faac5280a867ebbd40a668e500`）以 DeepSeek Conformance run-006 preflight
`sha256:03d02deffe7afe7601536b68630ce98accf723799f50d7e168f1cb1815247990` 和 single-use authorization
`sha256:6698dac638ad69bab63b21c94a95b4770af614ae3649a74fe05f84dfb6b7d117` 恰好执行 2 次 request；12/12 Case PASS，唯一模型 identity
为 `deepseek-v4-pro`，input/output tokens 为 375/76，result digest 为
`sha256:b80972ae436dc5523b645bfb7efebc9b5c815141190f2fd7642320d8089bdf50`。raw prompt/response 未持久化，授权已消费。

同候选 Capability run-006 绑定 freeze
`sha256:e2e40a3c7dc9ca6d82e6f38fca0d6ced2fa2384f38f4cdd17222e1977246a767` 与 authorization
`sha256:04331503340ec4c9fb275f72f51179f090c7dcc5b730c7446c2d4481e0b611a3`，无 retry 地完成全部 39 次 Provider request 与 18 个
Case，`unknown_count=0`。唯一模型 identity 为 `deepseek-v4-pro`，input/output tokens 为 126228/10227。closed Result 的
result/document/terminal digest 分别为
`sha256:85a51dc5c4182f99a9c9adaca9becbba213811d211e452b72a1d5dcda0f99692`、
`sha256:fa38bc981ed37efbe1b77642be4819e3d7cf45f0198bb50362371689356773d3` 与
`sha256:884d6a35fdd3372a2af55ff206e11752ff4995385ee5d86a9f0a2b3828205cf5`。12/18 Case PASS；失败为
`N-CANDIDATES-003`、`RESULT-DRIVEN-BATCH-004`、`DECLARED-INVENTORY-005`、`BUDGET-EXHAUSTION-011`、
`NEGATIVE-COMPLETE-014` 与 `NEGATIVE-QUERY-UNKNOWN-015`，因此没有 Capability Qualification 或 Production Activation。

## Evidence and root cause

run-006 normalized output 证明 Prompt 澄清已修复 legal finish、max-four 和 Review；剩余偏差却不能再归为单纯语言歧义：

- `N-CANDIDATES` 与 `RESULT-DRIVEN-BATCH` 的 operation 语义正确，但模型重新生成 opaque Entity Ref 时出现重复字符漂移。要求模型
  复制平台已经掌握的 Snapshot、Result、Entity、trace 与固定 bounds，把 authority 数据错误地交给了概率输出层；
- `StructureViewService.declared_method_inventory` 只接受 `JAVA_TYPE`。旧 Oracle 却从 candidate 的 `JAVA_METHOD` Ref 直接期望
  inventory；产品可达路径实际必须是 method Ref → `direct_neighborhood(INCOMING, DECLARES_METHOD)` → JAVA_TYPE Ref → inventory；
- 旧 budget Case 的第 3、4 回合读取同一份 method-batch previous Result，却按回合序号分别期待 inventory 与 direct relation，违反
  “只根据 immediately preceding sealed Result”不变量；
- 旧 negative Case 在零候选 Result 中构造了产品不会返回的 `scope_entity_ref`，先期待一次 inventory 再 FINISH；真实
  `implementation_candidates` 零候选 Result 没有该 Ref；
- 产品 progress receipt 原来没有向模型投影三层完整性 verdict，资格 fixture 却直接提供该数据；因此 negative decision 的输入并不
  等同正式产品；
- System 一方面冻结 Investigation 最少 2 次模型调用，另一方面要求 FINISH 前至少 2 个 executed Result，使最短正常路径成为
  2 query + FINISH，即 3 次 Investigation。一个已执行的完整零候选 Result + 显式 FINISH 本应形成合法 2-call boundary；旧规则让
  冻结下界不可达。

根因同时跨 Owner 边界、接口语义与资格真实性：模型应决定语义意图，Application 应编译 authority 参数；qualification 必须只构造
正式产品可达的 previous Result 和进度输入。继续增加“逐字符复制”提示不能修复该架构责任倒置。

## Impact and classification

这项修复改变 Agent/Application 的职责分界、`FINISH` 合法前置条件、progress receipt 与 Implementation Query 的有效组合路径，属于
`system-contract`。主处置写入 `SYS-ADR-015`；`SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING` 与
`SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY` 同步投影。run-006 仍是有效失败证据，但不能授权新版本。

## Decision and disposition

将活动 bounded contract 版本化为 capability/Strategy `1.4.0`、prompt/vocabulary `@7`、bounded egress policy `@1.1.0`、
suite/oracle `@1.4.0`，并登记 argument compiler
`java-source-semantics-investigation-argument-compiler@1`：

当前 suite/oracle raw digest 分别为
`sha256:89886e756010d1ca2dc1791b265b3bce5366b51ba8db1ed8765fa8238a0512db` 与
`sha256:d04c3a96da27ae81b3d51c7c6f65c75fa5d51feb9f5e0b616f75fb095730fb7f`；policy raw digest 为
`sha256:8e8dc5ae95daa2b85eae165595980e45e7507fbca5cb8ec4085eed5dee6f1184`。

1. 模型的 Investigation 输出只包含 `operation`、`search_terms`、`relation_intent` 与 `finish_reason`；
2. Application 从 exact sealed input deterministic 编译 step/trace/Snapshot、Result binding、Entity Ref、direction/predicate 与固定 graph
   bounds，再由既有 typed proposal validator 和 View executor 校验执行；模型不再输出或复制 authority identifiers；
3. product progress receipt 增加平台计算的三层 completeness projection，但不暴露评测 Oracle identity；
4. FINISH 允许发生在至少一个 executed Result 之后，仍占用一次模型调用，因此 Investigation 2—4、total 4—6 与 no-retry envelope
   不变；
5. suite/oracle 保留 18 个 Case、原 metric、18/18 threshold、forbidden events 与 no-retry，但用产品可达状态替换伪造 fixture。
   declared inventory 走 declaring-type hop；budget 每轮只消费前一轮 Result；negative boundary 直接由真实零候选 Result 进入 FINISH。
   为显式覆盖这些合法转换，总调用数由 39 调整为 41。

本处置不降低 Oracle verdict、不增加 Provider/Case/工程/符号特判，也不改变 Source-off、Snapshot、Support 或三层负向证明边界。
run-006 后停止相同 prompt 重试；本次只完成离线架构、契约与 deterministic verification，不发起新的 Provider 调用，不执行正式 Web、
hidden canary、SLICE-002 或 Production Activation。新的 live requalification 必须等该候选 clean commit 后独立开始。

## Verification after disposition

- deterministic compiler 回归覆盖 exact opaque argument 编译、`DECLARES_METHOD` declaring-type hop、JAVA_TYPE inventory、一个 executed
  Result 后 FINISH、真实 method-batch 的 JAVA_METHOD path endpoint 选择与完整 trace replay；
- affected contract/policy/capability/product/runtime 回归 117/117 PASS；18-case fake transport 资格闭包恰好消费 41 次并 18/18 PASS，
  验证模型 intent 经同一个 production compiler 形成 exact evaluator proposal；
- full discovery 978/978 PASS，退出码为 0；仅出现仓库既有 SQLite connection `ResourceWarning`，没有 failure/error；
- `python3 scripts/docs.py check` 对 318 份 current documents PASS，`git diff --check` PASS；
- 正式 runtime 仍保持 Ark，Capability Qualification 与 Production Activation 均为 `NOT_EXECUTED`。
