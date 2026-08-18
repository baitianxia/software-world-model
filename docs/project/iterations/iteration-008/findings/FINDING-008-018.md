---
id: FINDING-008-018
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [architecture, engineering, ai, quality, project]
depends_on: [ITER-008-SLICE-001, FINDING-008-014, FINDING-008-017, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
code: [src/software_world_model/application_services/bounded_world_model_investigation.py, src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, src/software_world_model/ai_infrastructure/model_egress_gateway.py, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_policy.json, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_qualification.py]
tests: [tests/test_bounded_world_model_investigation.py, tests/test_world_model_answer_strategy.py, tests/test_iteration_008_capability_qualification.py, tests/test_model_egress_gateway.py, tests/test_iteration_008_capability_harness.py]
iteration: ITER-008
classification: iteration-design
disposition: operation-discriminated-semantic-slot-projection
target: ITER-008-SLICE-001
---

# FINDING-008-018：Application 必须按 operation 解释模型语义槽位

## Observation

run-009 的第 18 个 Provider response 已正确选择 `all_simple_paths`。旧 compiler 随后读取固定 JSON envelope 中只对
`direct_neighborhood` 有意义的 `relation_intent=BOTH_CALLS`，并在执行任何 path query 前失败。该 path 的两个 exact Ref、固定
`CALLS` predicate、depth、expansion 与 path 上限本来全部由 Application 从 sealed Result 和 policy 编译；该 relation slot 不参与
typed path proposal，也没有权限影响。

用户消息 `codex-user-message:sha256:375246d919e8541021acd7b319f13d5af928794ff23a022ae01a82531a09a8e2`
明确作出协议 redirect decision：“是你适配模型 不是模型适配你”。这终止了 `FINDING-008-017` 的等待状态，也否定了把固定序列化槽位
误当成每个 operation 都拥有语义的集成方式。

## Evidence and root cause

模型输出 schema 为兼容 constrained JSON，一直要求四个固定字段：`operation`、`search_terms`、`relation_intent`、`finish_reason`。
但产品 Contract 的 Owner 边界是模型只选 semantic operation，Application 编译 authority argument。旧
`java-source-semantics-investigation-argument-compiler@2` 在识别 operation 后仍全局解析四个 slot，并要求所有非适用 slot 精确为空；
这把传输 envelope 当成未声明的交叉字段约束，职责倒置地让模型维护平台内部 tagged-union normalization。

回归 corpus 证明 operation-discriminated projection 可以保持 exact authority：

- `implementation_candidates` 只解释并界定、去重 `search_terms`；
- `direct_neighborhood` 只解释注册过的 `relation_intent`；
- `FINISH` 只解释非空 `finish_reason`；
- `method_implementations`、`declared_method_inventory`、`path_exists` 与 `all_simple_paths` 不解释任何辅助模型 slot；
- 非适用 slot 的允许值被确定性丢弃后，所得 proposal 与 canonical empty-slot 输入逐字段相同；
- 所选 operation 的适用 slot、合法 transition、sealed Result/Ref provenance、predicate、bounds、budget、progress 与 closed outer shape
  继续严格验证。

因此这是通用 anti-corruption/compiler 缺陷，不是 DeepSeek、某个 Case、问题文本或工程的特判。raw model output 仍由原始 output digest
和运行证据审计；丢弃非适用 slot 不会隐藏或伪造 Provider response。

## Impact and classification

System 已规定“模型只提 semantic intent、Application deterministic 编译 typed argument”，Owner 与安全不变量没有变化；本次是在
ITER-008 内修正该边界的实现解释，主分类为 `iteration-design`，目标为 `ITER-008-SLICE-001`。模型可见 schema、Prompt、operation
set、18 Case、41-call 上限、Oracle、18/18 threshold、no-retry、Provider temperature 和 Production Activation 均不改变。

compiler 的 acceptance semantics 已变化，所以旧资格不能继承。argument compiler 升级为
`java-source-semantics-investigation-argument-compiler@3`；bounded Gateway policy 升级为 `@1.1.2` 并绑定新 compiler/file digest。
capability/Strategy、prompt/vocabulary 与 suite/oracle 分别保持 `1.4.1`、`@8` 和 `@1.4.1`，避免把集成层修复伪装成新的 Prompt
调参或评测放宽。

## Decision and disposition

采用 operation-discriminated semantic-slot projection。compiler 必须先验证 closed envelope、sealed authority、step 和注册 operation，
再只解析该 operation 拥有的 semantic slot；所有 typed authority 字段继续由平台生成。相关 slot 缺失或非法仍失败关闭，非适用 slot
不得改变 operation、transition 或 typed projection。

run-009 保留为旧 compiler `@2` 的失败证据，不 retry。完成 deterministic/full/docs 验证并形成 clean exact candidate 后，允许以全新
freeze 执行一次同候选 DeepSeek 2-call Conformance 和一次完整 18-case Capability requalification；这是一项经显式 redirect 授权的
新协议候选，不复用旧 freeze/authorization。未达到 18/18 仍不得进入正式 Web、hidden canary、SLICE-002 或 Production Activation。

## Verification after disposition

- operation-specific compiler 回归覆盖 candidate、method batch、direct neighborhood、FINISH 和 run-009 的
  `all_simple_paths + BOTH_CALLS` 反例；canonical 与 projected typed proposal exact equal。
- relevant relation/finish slot 的负向回归仍以 `DomainError` 失败关闭；candidate term 的 12 项 bound/casefold 首次顺序去重保持。
- Gateway policy ref、compiler ref 和 policy file digest 一致绑定，旧 compiler qualification 会因 drift 失效。
- 定向 compiler/contract/policy/fake-live-harness 54/54 PASS；fake transport 使用 run-009 原始残留字段反例完整执行 41 requests /
  18 Case 并 18/18 PASS；full discovery 982/982 PASS，仅有既有 SQLite connection `ResourceWarning`。
- current documents 322/322、`git diff --check` 与 credential-shaped secret scan PASS。
- live Conformance/Capability、正式 Web、hidden canary 与 Production Activation 在 clean candidate 形成前均保持未执行。
