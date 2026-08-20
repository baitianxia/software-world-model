---
id: FINDING-008-027
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai, application, engineering, quality, project]
depends_on: [ITER-008-SLICE-001, FINDING-008-026, SYS-CONTRACT-AI-CAPABILITY-EVALUATION, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY]
code: [src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_policy.json, validation/structure_world_model_iteration_008/capability]
tests: [tests/test_world_model_answer_strategy.py, tests/test_iteration_008_capability_harness.py, tests/test_iteration_008_capability_qualification.py]
iteration: ITER-008
classification: system-contract
disposition: product-realistic-semantic-constraint-and-question-origin-check
target: SYS-CONTRACT-AI-CAPABILITY-EVALUATION
---

# FINDING-008-027：Search-term 资格只能要求问题拥有的概念

## Observation

clean candidate `51c8ac369b29b609d6a5dcf53f55370a0cb49f04`（tree
`10abd04fd45fdd13a156fac9349a7a6e21690d8b`）的 run-018 Conformance 绑定 preflight/authorization/result
`sha256:5e1d00112eb592e68b3e8861c1a99a8d88d83b38e0456e05badc436d3b477934` /
`sha256:eb8b08aea2f44cafb0fbbfef4ceabb35160cf7dc4d6e7851ae366d728f6341c2` /
`sha256:e5ac81e07a36badc53c34699e262168b2ca2052d1503d9d25e2ea71eb37f4727`，恰好完成 2 requests / 12/12
PASS。Capability 绑定 freeze/authorization
`sha256:93cef5a0c2315ed6bc603ee6a9ae5a327a120d5bb3781010f85f8d3f75ac059d` /
`sha256:b41bad4b7a56553b9601b102cc856a7db3c35b8157a5cb13671dbe860b9f3d2a`，无 retry 地完成全部 40 requests / 18 Case，
但只有 16/18 PASS。result/closed-document/terminal digest 为
`sha256:6cd3f4f821c44240f60bf8a88f49c85d23ceaba5eb4a316ccfb10ecface2459e` /
`sha256:4fe292ac028d96cbb8f92026ebcbbb81573d54a5626c82c75ab39517f7999f04` /
`sha256:39a86a2d17d7952ba5467b52c5af2244b0a7103dcf90ab3b3880a6fcc0e8cbf2`；没有 Qualification、Web、canary 或 Activation。

`WM-JSS-I8-RESULT-DRIVEN-BATCH-004` 与 `WM-JSS-I8-REF-PROVENANCE-013` 的 operation、typed projection、第二步
candidate Result binding 和三个 exact method Ref 全部命中 Oracle；`projection_exact=true`、unauthorized reference 与 material error
均为 0。两者唯一 finding 都是首轮 `CALL_1:SEMANTIC_CONSTRAINT_NOT_SATISFIED`：

- RESULT-DRIVEN-BATCH 的问题只要求解释 authentication failure/success flow；模型返回
  `authentication/failure/success/flow`，旧 suite 却额外要求原问题没有出现也没有规定的 `return/throw`；
- REF-PROVENANCE 的问题明确包含 complete implementations、returned authentication candidate；模型只返回
  `authentication/candidate`，遗漏了问题拥有的 `implementation` concept，但后续 Ref provenance 本身完全正确。

## Evidence and root cause

transport 为 TLS attempts/success 1/1、connection reuse 39、HTTP/credential resolution 40/40、unknown/retry 0；唯一模型 identity 为
`deepseek-v4-pro`，input/output tokens 73,874/2,584。run-017 的 PATH-EXISTS 与 MAX-FOUR 偏差在 run-018 均已 PASS，因此本次不是
Provider availability、TLS、Adapter single-system rendering、capability prompt selection、argument compiler、Application transition 或
Ref authority 回归。

两个失败属于同一 search-term 语义边界的两种缺口。活动 Prompt 同时要求保留问题概念并删除 instruction-only term，但“general
feature terms”与按词面删除的措辞不足以明确：一个词即使也出现在 instruction 中，只要语义来源是原问题，就仍是 question-owned。
这使模型把显式 `implementation` 当成泛化请求词过滤。另一方面，旧 RESULT-DRIVEN-BATCH semantic constraint 源自早期固定
Query Planning checklist，把一种可能的 failure/success 实现方式 `throw/return` 当成唯一必要检索概念；它与当前 System Contract
“search term 从原问题提出、不得推断未请求具体机制”的边界冲突，是产品不真实的 evaluator 假阴性，不是模型遗漏。

这项证据不允许删除 REF-PROVENANCE 的显式 concept 要求、放宽 typed operation projection、Ref provenance、Case、18/18 threshold、
预算、完整性或 no-retry；也不能在 Application 中加入问题、Case、Oracle 或工程特判。

## Decision and disposition

`SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY` 明确 term provenance 按原问题语义来源而不是 Prompt vocabulary overlap 判断；常见词形、
翻译与 identifier-like normalization 仍允许，但 abstract outcome 不自动取得具体 return/throw 解释权。
`SYS-CONTRACT-AI-CAPABILITY-EVALUATION` 明确 semantic constraint 只能要求 System Contract 与产品输入可证明拥有的概念，不能把一种
可能实现机制提升为唯一等价表达。

Investigation Prompt 采用通用 origin check：不得把多概念问题压缩为 broad topic；返回前只重读 original question 并覆盖每个 material
retrieval concept；只有没有对应 question concept 的 term 才删除，同时禁止推断未请求的具体执行机制。资格 suite 保留
REF-PROVENANCE 的 `authentication + implementation + candidate` 约束；RESULT-DRIVEN-BATCH 只要求问题实际拥有的
`authentication + failure + success`。其两步 operation Oracle、typed projection、18 Case、40 calls、18/18 threshold 与 evaluator
算法不变；oracle 文件只因 exact suite identity 绑定而版本化，不改 operation 内容。

活动身份升级为 capability/Strategy `1.5.5`、prompt/vocabulary `@14`、bounded egress policy `@1.4.3`、suite/oracle `@1.5.5`。
Adapter `deepseek-chat-completions-no-tools@4`、Conformance fixture `1.2.0` / Result `@2`、compiler `@6`、temperature 0、persistent
verified TLS 和 no-retry 均不变。run-018 永久保留为 16/18 FAIL；新身份必须从 clean exact candidate 重新完成 Conformance 与完整
Capability，18/18 前不进入正式 product Web。

## Verification and closure

- Contract test 绑定 question-origin check、无 unrequested mechanism 推断和新 exact identity；
- suite regression 绑定 RESULT-DRIVEN-BATCH 不再要求 `return/throw`，并继续要求 REF-PROVENANCE 的显式
  `implementation/candidate`；
- fake transport 仍须执行 exact 40 calls / 18 Case 并由同一 independent evaluator 18/18；
- targeted、完整回归、docs、compile/diff/secret scan 与确定性 digest 在 clean candidate 前重算；
- live run-019 必须使用全新 exact freeze 和已存在的持续授权，不能重评或重试 run-018。

System Contract 写回后的 `ITER-008-SYSTEM-CONTRACT-SET@1` digest 为
`sha256:948647adf5e857ea1a782ab04396c92bfa5a51e8a26b7d35ab6dca984f67aaa4`；共享 current contracts 使 ITER-007 fileset 同步重算为
`sha256:cec082d84da104e8c632bd395b5a29acf4b68e15f743bb5d4683fa69b8e0331b`。

确定性 identity 为 prompt program `sha256:0019eeec2cc7a96008aacf56560b9dca905613c68f35c5caca3891ebc4a1f9b0`、Strategy
implementation `sha256:4aa70b9275802cd3a2cec459c6a5af1407141e95dce56c879df3895216ca8536`、output schema
`sha256:9c2f3505c87d677d416c277ea853649f3bf865ffd7dfcaeaea6bc708e080e775`、policy raw
`sha256:803f55d36ee096371342164f20891a73801afeb359d87e492b33c59e8b174fbe`、resource policy
`sha256:706542ff3f621d5c9b51d6b2232927403535ebc037812dfb726c58e01e5e5f3f`、suite/oracle raw
`sha256:9e7ddae7f335cd889141b231cea6182b43bc05a6674cd8a9be7433792774213b` /
`sha256:8fabaef66384ba4b29855a072905a733159bc1f713ffd1d3bdbb9cbfa55669f7`，product bounded Gateway workload
`sha256:1eaa8bbab9b6d7123e8c2953b0310ae3edd7cbdcffdb38c5657ca531c9525aab`。

相关 DeepSeek/Capability/Gateway/runtime 回归 117/117 PASS；fake transport 恰好执行 40 calls / 18 Case 并由 independent evaluator
18/18 PASS。完整执行面 1018 项中 1013 项通过；唯一 4 failure + 1 error 的测试名和原因仍完全属于 `FINDING-008-020` 已密封的
ITER-003 Adapter/Codex binary drift，本轮没有新失败。current documents 331/331、`compileall`、`git diff --check` 与路径级
credential-shaped secret scan PASS。Finding 已处置到 Capability Evaluation/Implementation Query Contract、活动设计、代码和测试；
live run-019 仍是独立 blocking Gate。

exact candidate `6dc7a9e4c9e24dc901c95088c549441fc1b8497c` / tree `229d11d186e986c8b1746d901f81f574e808b59a`
随后完成 run-019。Conformance preflight/authorization/result/terminal digest 为
`sha256:18cc7ea9e470d1dc983805090f43cc789a7f94dbef1bc6223ca0b32c5c34d4d3` /
`sha256:c36214d5c7418a4e0a0f3b6c507f889125f1ba0dcba4673f5230e5412cc06ebb` /
`sha256:c3ce93867fcc180573fd0c3a7391fb64c866e48839cc31ad5687b76380e1120c` /
`sha256:507ef67670c0ac2c783eac20c0e664671e20c937001c4324975e0dab05a0dc6a`，恰好 2 calls / 12/12 PASS。
Capability freeze/authorization/result/closed-document/qualification-proof/qualification-document/terminal digest 为
`sha256:a7e99c16730c60cd977cec3cee8da0ca330e1b1d437b6f03c0d464540aba386e` /
`sha256:e2a112334c8e2352b5859ceb0134841a1e02a76706da7eadcf00ec2f5ef393ee` /
`sha256:16e9e6bcf5f99ea6b72aff7fb34022d4a02edc4db8660da2a26f66dd4ae5020b` /
`sha256:1742279628348c3ee1be704eb5800763d744d05db8a759358c44d6449c042528` /
`sha256:7e4601073b60602eb4f306f284825677b10c1dfa0db29cb1fd3cee974ad224fc` /
`sha256:b0ec3ad12c343371dd8389d86b37db35039c526e92e2ec880ac106ef8423e556` /
`sha256:a1cd6fb656011a0f8e5ef2ef20d92604cb273035c1b8738685ae02af7216981f`。运行无 retry 地完成 40 calls / 18 Case 并
18/18 PASS；TLS 1/1、reuse 39、HTTP/credential 40/40、unknown/retry 0，有效期到 `2026-08-27T09:09:31.851862Z`。

RESULT-DRIVEN-BATCH 返回 `authentication/failure/success/flow`；REF-PROVENANCE 返回
`authentication/candidate/returned/complete/implementations/inspect`。两者 semantic constraint、operation、typed projection、第二步
Result/Ref provenance 全部 PASS，直接验证了本 Finding 的两项处置。核心 evidence 文件权限 0600，credential-shaped secret scan
无命中；授权均已消费，hidden canary、formal Web 与 Production Activation 均未执行。Finding 的 live closure 完成；V-002 对当前
exact Contract 为 PASS，下一 Gate 是独立 formal product freeze/Web。
