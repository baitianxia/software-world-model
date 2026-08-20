---
id: FINDING-008-026
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai, architecture, engineering, quality, project]
depends_on: [ITER-008-SLICE-001, FINDING-008-025, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY]
code: [src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, src/software_world_model/ai_infrastructure/model_egress_gateway.py, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_policy.json, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_qualification.py, validation/structure_world_model_iteration_008/capability]
tests: [tests/test_world_model_answer_strategy.py, tests/test_model_egress_gateway.py, tests/test_iteration_008_capability_harness.py, tests/test_iteration_008_capability_qualification.py]
iteration: ITER-008
classification: system-contract
disposition: capability-selected-semantic-authority-before-provider-rendering
target: SYS-CONTRACT-AI-MODEL-GATEWAY
---

# FINDING-008-026：每次模型调用只应接收当前 Capability 的语义 authority

## Observation

clean candidate `e3cc34fdd830498414480684151944139ca9489c`（tree
`0d83e59ed273c2f6c01dba977f2089576eda2da2`）的 run-017 Conformance 绑定 preflight/authorization/result
`sha256:7dbff2868c58e8582e44e3fd989282430dc762d13c529607ab6f4a0a3c2a9dad` /
`sha256:901b6a9158beae9fab35f921e6617939859908d5349c67a2d62fbaba7ea96875` /
`sha256:f17c58dd13ece22e3bf7da216119fb2e00d552fed7bd31e9bec23accb98d02f4`，恰好完成 2 requests / 12/12
PASS。唯一 response identity 为 `deepseek-v4-pro`，tokens 为 407/68；verified TLS 1/1、connection reuse 1、HTTP/credential
resolution 2/2，unknown/retry 为 0。

同候选 Capability 绑定 freeze/authorization
`sha256:38d07801b13fa581fc7d82120cc1bd319202862b76a79b044895b2a96fb86deb` /
`sha256:d4f9518043a0c6c030e3a74b60267f50216f43efb5ebd4d69dd35216f41dad2f`。它完成前 9 Case / 21 requests，且 run-016
失败的 `WM-JSS-I8-PATH-EXISTS-007` 已按原 Oracle 完整 PASS；第 22 个已完成 request 在
`WM-JSS-I8-MAX-FOUR-010:call-1` 被 frozen evidence ledger 正确拒绝。failure/terminal digest 为
`sha256:9877b420f138743bb948c2f9e02f5d7095863ab86678a3acf3b191994364793d` /
`sha256:c1c50229d3dbc5b6e5f5803532aa68c67c53b1d7fc69689ad24b64e709705a59`；授权已消费，没有 retry、Qualification、Web、canary
或 Activation。

该问题是 “Trace authentication through failure recording and successful session issuance.”，冻结 evidence obligation 为
`method_implementations`。模型 output digest
`sha256:7f7fa43da40543cbb34ce25eb98092c721e2ff03df1cf2737d385ef5f1d24515`，却选择 `path_exists`，并在原问题词之外追加
`order/return/throw/audit`。原始问题中 `trace/through` 描述要解释的业务流程，不是询问“是否可达”的二元图判断。

## Evidence and root cause

失败时 transport 仍为 TLS attempts/success 1/1、reuse 21、HTTP/credential resolution 22/22、post-dispatch unknown 与 retry 0；
模型 identity、JSON shape 和 Usage 均正常。因此该失败不是模型不可用、网络回归、Adapter envelope 或 Application transition 问题。

`@12` 虽声明其他 capability section inactive，实际 Authorized Input Manifest 仍发送完整 8,853 字符 monolithic prompt，其中同时包含
不可用的 legacy Query Planning、Draft、Review、Investigation 和 Review clarification。失败调用 input tokens 为 2,479；其额外
`order/return/throw/audit` 均存在于同一 system authority 的非 Investigation 文本。仅靠自然语言声明“inactive”没有形成可机械验证的
输入隔离，也使 “through” 在 graph reachability 与 implementation workflow 两种含义之间受到其他 section 干扰。

run-017 对旧 PATH-EXISTS Case 的恢复同时证明 `FINDING-008-025` 的单一 DeepSeek system authority 与显式 reachability 规则有效；
不能因为新歧义而回退该适配、放宽 evaluator、在 Application 读取问题文本，或加入 Case/工程/Oracle 特判。缺口位于 Gateway
semantic authority 的 capability 选择边界。

## Decision and disposition

活动 Proposal Contract 将每个 capability 的 exact prompt 作为同一版本化 prompt program 的独立 entry。Strategy 在构造 Manifest 前按
sealed capability 选择唯一 entry，并记录 `capability-prompt-selection@1` transformation；Gateway 与 capability runner 同时校验 stage、
transformation 和所选内容 digest。Investigation 不再接收 legacy Query Planning、Draft 或 Review 文本；Draft 与 Review 也互相隔离。
DeepSeek Adapter 随后仍按 `FINDING-008-025` 把这一条 semantic authority 与 closed schema 合并成一个 leading system message。

Investigation 通用语义进一步明确：只有显式请求 whether/can/does/reachable 的二元答案才使用 `path_exists`；要求 trace、explain 或
describe 一个 workflow through actions/outcomes 时使用 `method_implementations`，除非问题另行明确请求二元可达性；`through` 本身不取得
reachability 解释权。每个 search term 必须对应原问题概念或其常见 inflection/translation/identifier normalization，返回前删除只来自
instruction 的 term。

活动身份升级为 capability/Strategy `1.5.4`、prompt/vocabulary `@13`、bounded egress policy `@1.4.2`、suite/oracle `@1.5.4`。
Adapter `deepseek-chat-completions-no-tools@4`、Conformance fixture `1.2.0` / Result `@2`、compiler `@6`、18 Case、40 calls、18/18
threshold、temperature 0、persistent TLS 和 no-retry 均保持不变。run-017 失败证据永久保留；新身份必须从 clean exact candidate
重新完成 Conformance 与完整 Capability，之后才可形成 product freeze。

## Verification and closure

- Contract test 绑定三个 capability prompt 的 exact 覆盖与互斥，Investigation wire 中不得出现 legacy/Draft/Review section；
- Gateway test 绑定 `capability-prompt-selection@1`，对 transformation 或所选 prompt digest 漂移失败关闭；
- capability live runner 对每个 role 重新校验所选 prompt，而不是 aggregate prompt；
- 新 suite/policy/freeze/qualification/runtime 身份拒绝 `1.5.3/@12/@1.4.1`；Oracle 内容、Case、调用数与 evaluator 不放宽；
- targeted、fake 40-call、完整回归、docs、compile/diff/secret scan 在 clean candidate 前重新执行；live 结果只在实际发生后追加。

当前确定性 identity 为 prompt program
`sha256:17246787b881a7fbc6a2e4af75fd3956c5d1ccba34d83ad411dc28bdd86f6dcf`、Strategy implementation
`sha256:40ac379f93e28792024eb50c985cf5a9ba208f979f9dfec0a0c3ad4f14fa9776`、policy raw
`sha256:7baffe44a9e8d7146953036fc934675fa317cc5164d4e8c0b838875ea10fdb4d`、resource policy
`sha256:df872af8bb17988ecc2a2ae06182a0a342e45d405b228445625b45ab943c3f2f`、suite/oracle raw
`sha256:835318bdca4a8a8b30c79825dec16db4517d8365bf19575faea55e5099124cf1` /
`sha256:2bf8d87f9562d68ab74aafeeba217bc2e4dde8f33c50b242762557f126912ba2`，product workload
`sha256:5892e0f6b0587bf6fb8c783143ce15a43d76252b4c4bbbfa52e11880c26728e4`。DeepSeek/Capability/Gateway/runtime 相关回归
121/121 PASS，fake transport 恰好 40 calls / 18 Case 并由 independent evaluator 18/18 PASS。完整执行面 1017 项中 1012 项
通过；唯一 4 failure + 1 error 的测试名与原因仍完全属于 `FINDING-008-020` 已密封的 ITER-003 Codex CLI/runtime exact-binary
drift，本轮没有新失败。current documents 330/330、`compileall`、diff check 与路径级 secret pattern scan PASS；更新后的
`ITER-008-SYSTEM-CONTRACT-SET@1` digest 为
`sha256:0143229ee22d1db3962e6bc6fedf7982fea96642fe84d1f116667f3b144219a5`。Finding 已处置到
`SYS-CONTRACT-AI-MODEL-GATEWAY`、活动设计、代码和测试，live requalification 仍是独立 blocking Gate。
