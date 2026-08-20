---
id: FINDING-008-029
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai, application, engineering, quality, project]
depends_on: [ITER-008-SLICE-001, FINDING-008-027, FINDING-008-028, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
code: [src/software_world_model/application_services/structure_view.py, src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_policy.json, validation/structure_world_model_iteration_008/capability]
tests: [tests/test_java_source_semantics.py, tests/test_world_model_answer_strategy.py, tests/test_iteration_008_capability_harness.py, tests/test_iteration_008_capability_qualification.py]
iteration: ITER-008
classification: system-contract
disposition: cross-script-source-identifier-adaptation-and-live-qualification
target: SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY
---

# FINDING-008-029：中文产品问题通过 Proposal 后被 ASCII-only Query 拒绝

## Observation

正式 product freeze `run-001-freeze` 已以 `SWM-ITER-008-SLICE-001-CANDIDATE-FREEZE@2` PASS，随后正式 Web 对公开问题
`登录流程是怎样的？` 执行同一 bounded product chain。DeepSeek 唯一一次已完成 request 返回 closed intent：
`implementation_candidates`、search terms `登录/流程`、`method_implementations` evidence。Adapter、TLS、HTTP、JSON schema、
operation、evidence request 和 argument compiler 均成功，但 Answer role 以 `DomainError` 失败关闭，HTTP terminal 为 502；没有 retry、
Provider fallback、Source/Update/Direct、Citation 或 Production Activation。

## Evidence and root cause

失败运行位于 `var/iteration-008/slice-001/run-001-live-session/requests/000001-e19d37020906/runs/01`。terminal document digest 为
`sha256:1cca15fad283152f9594565bf432bea110bfd2d4472529e078ee0cef32c14f0f`；Gateway DB 只包含一个 COMPLETED
`deepseek-v4-pro` call，output digest 为 `sha256:b6b2748886aaf25850c6a2ff6ba98bfced75f114c958401d2e7873408f38c4ad`。

使用该 DB 的 exact sealed input/output 和同一 `ordered.json` / `snapshot-1.json` 做零网络重放后，
`compile_investigation_intent` 与 `InvestigationProposal.from_mapping` 均 PASS；首次偏差在
`StructureViewService.implementation_candidates`。`_feature_tokens` 以 `[^0-9A-Za-z]` 切分，导致两个合法 Unicode term 都没有 token，
抛出 `IMPLEMENTATION_SEARCH_TERM_EMPTY: implementation search term has no canonical identifier token`。

这与 `SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY` 已冻结的 NFC → camel/snake/digit boundary → Unicode casefold 规则直接冲突，
属于 systemic implementation defect，而不是 DeepSeek 不可用或输出 shape 不兼容。进一步审查表明 run-019 的 18-case Qualification
全部使用英文 `original_question`；它证明了英文 semantic intent，却没有证明正式中文 Web 输入能产生 source-identifier translation。
即使下游正确接受 Unicode token，仅以 `登录/流程` 搜索英文 Java identifier 也只能形成零候选，不能满足公开 V-003。

## Decision and disposition

1. `StructureView` 实现 Contract 已有的 Unicode identifier tokenization；non-Latin term 不再在 Query 边界异常退出，index 与 query
   继续使用同一 deterministic normalization，不增加 stemming、embedding、工程词典或答案特判。
2. Investigation integration prompt 明确 cross-script adaptation：non-Latin 问题的每个 material retrieval concept 至少提供一个 common
   English source-identifier translation；原文 term 可以并存，但不能是唯一检索表达。该规则不授权 project symbol、hidden synonym
   或问题未要求的机制。
3. Capability Definition 保持 18 Case / 40 calls / 18/18 / no-retry，但把一个既有首轮 Case 的完整中文等价问题作为 model-visible
   input，并继续以其同一 question-owned English concept groups 判定翻译；不新增 LoginService、产品答案、Source 或 evaluator hint。
4. 活动 identity 升级为 capability/Strategy `1.5.6`、prompt/vocabulary `@15`、bounded egress policy `@1.4.4`、suite/oracle
   `@1.5.6`。Adapter `@4`、Conformance fixture `1.2.0`、compiler `@6`、Provider、temperature、persistent TLS、Case count、call count、
   threshold 与 no-retry 不变。run-019 与当前 product freeze/Web failure 永久保留，不能复用为新 identity 的资格或产品 PASS。

System Contract 已写回 `SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY`、`SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING` 与
`SYS-CONTRACT-AI-CAPABILITY-EVALUATION`。本 Finding 的主处置 Owner 是 Implementation Query；Capability 变化是同一跨 script
产品边界的验证闭包。

## Verification and closure

- Unicode tokenizer 必须覆盖 mixed-script camel/digit split，并证明 `登录/流程` 不再触发 invalid-argument；
- Prompt/contract tests 必须绑定 cross-script source-identifier translation，且继续禁止 Provider、Case、工程和 symbol patch；
- fake transport 必须仍完整执行 40 calls / 18 Case 并 18/18 PASS；
- 新 clean candidate 必须重新完成 2-call Conformance 与完整 40-call Capability，第一 Case 的中文输入及 English concept constraint
  必须由真实模型 PASS；
- 通过后重新执行 deterministic/full/docs freeze 和正式 Web 登录/下单回归；在此之前 V-003/V-WEB-001 保持 FAIL/NOT-RUN，hidden
  canary、SLICE-002 与 Production Activation 继续阻断。

本地处置已闭合：相关 contract/capability/runtime/product 回归 128/128 PASS；fake transport 仍恰好执行 40 calls / 18 Case 并由同一
independent evaluator 18/18 PASS；current documents 333/333、`compileall`、`git diff --check` PASS。允许 AF_UNIX 的完整执行面为
1022/1027，raw exit 1，唯一 4 FAIL + 1 ERROR 的测试身份与原因仍精确属于 `FINDING-008-020`，本 Finding 没有新增完整回归失败。

新确定性 identity 为 prompt program `sha256:d016ed3207b97ebbf098e92c3d4674d311aaa825b297c98bb4b08032c73574d2`、Strategy
implementation `sha256:4a83df22f535dc8fa1712b3fc04f7a6ee3960263070ed5366ab18b3692446fa0`、output schema
`sha256:9c2f3505c87d677d416c277ea853649f3bf865ffd7dfcaeaea6bc708e080e775`、policy raw
`sha256:2aa073a7f870e4e4c63b10dd4050a39f77cc2d38265cbdc9215c0a22fe09822e`、qualification resource policy
`sha256:979b43971ae628a562a40cf935968578f52a00923f2bdded1757f31f19fcf052`、suite/oracle raw
`sha256:28ec89103f1d23cf0fabe47db2028fcb6534421436829412b85448ea70ddc292` /
`sha256:14605eaa002c6e771cfba0352a84281f50223e2eab4f4a651f12922f4b47b856`，bounded Gateway workload raw
`sha256:ac0cf321990b463d6924bf5ce395bb039d5e7a07bfaa946da8ae51934403f49c`。ITER-008/ITER-007 System fileset digest 为
`sha256:58288f15d0f733cb531289269a9ce80acba193d39912aa2600f50413a96619a0` /
`sha256:6a68490ec022bd5421e16e340381fe3d2df0b7cc8f314650a59fff2dad31e760`。

Finding 已处置到 System Contract、代码、测试与资格输入；尚未形成新 live Qualification 或产品 PASS。下一步只能从 clean exact
candidate 重新执行 Conformance/Capability Gate，不能重试旧 Web session。
