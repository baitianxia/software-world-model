---
id: FINDING-008-032
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai, engineering, quality, project]
depends_on: [ITER-008-SLICE-001, FINDING-008-031, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING]
code: [src/software_world_model/application_services/bounded_world_model_investigation.py, src/software_world_model/ai_infrastructure/deepseek_chat_adapter.py, src/software_world_model/ai_infrastructure/model_egress_gateway.py, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_policy.json, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_qualification.py]
tests: [tests/test_bounded_world_model_investigation.py, tests/test_deepseek_chat_adapter.py, tests/test_model_egress_gateway.py, tests/test_iteration_008_capability_harness.py, tests/test_iteration_008_capability_qualification.py]
iteration: ITER-008
classification: system-contract
disposition: application-owned-question-term-compilation
target: SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY
---

# FINDING-008-032：问题原词保留属于 Application 参数编译，不属于 Provider wire

## Observation

exact clean candidate `c925496f5ae752f93c92f49e4aeae0bc0ac7be8a`（tree
`e82ad3c809e027f8b94a9f1430216fc6025e3d1b`）的 run-022 preflight
`sha256:0799476577f8fb40b95a351cedeeec045972c942959f6e3d34336478df9ff67a` 已 PASS。其 Conformance
authorization/result/terminal digest 为
`sha256:24fb1890502de9eae4061eeb0b8012afb86ea769eb47eefbf9c0ff3d6c7bcac0` /
`sha256:f1ca95cad091efef15960e29a0ce7f196540b70ae318c7906a48254a6afc31bb` /
`sha256:ddced0061202015a2246833755a36cbe790e510d767691aa816b0aa5e242b18e`，精确 2 calls / 12 Case PASS。

同候选 Capability freeze/authorization digest 为
`sha256:b1003abf30ae9a7a13c3bbe54b16df76fdd7c34843aa47dbf710a52c7dfd73ef` /
`sha256:722fc1064e0200f602fd5d6b9685767cfb079319986d86c6d9b1e95bc0f1ca5a`。运行无 retry 地完成 40 calls / 18 Case，
16 Case PASS、2 Case FAIL；result/closed-document/terminal digest 为
`sha256:e47b0ade3ce8571c29f263c41e70fbf8711ad3fcfd3a34ceb6b9bfd1562dfc1c` /
`sha256:49a22c816f9ae074fb517e1dbeef2cd5bd651bfa7bea753558a27d07fb2d339d` /
`sha256:1de7e3870666df154f012324bfbfec5404d32c983e510567dcded5e09ef636ad`。没有形成 Capability Qualification；两份授权均已消费，
不得 retry。formal product、hidden canary、SLICE-002 与 Production Activation 均未执行。

## Evidence and root cause

这不是 endpoint、TLS、credential、模型 identity 或 JSON shape 故障。Conformance transport 为 TLS 1/1、reuse 1、HTTP/credential
2/2；Capability 为 TLS 1/1、reuse 39、HTTP/credential 40/40；两阶段 outcome unknown 与 retry 都为 0。Adapter `@5` 的显著性重述
使 PATH-EXISTS 首轮保留了 `reach`，但没有稳定履行同一通用约束：

1. CYCLE-PROGRESS 的问题是 `Explain all methods that contribute to authentication.`；模型填满 12 项认证相关 normalization，
   仍省略问题直接写出的 `methods`，首轮 semantic constraint FAIL；
2. REF-PROVENANCE 的问题直接包含 `implementations` 与 `candidate`；模型只返回 `authentication/candidate`，仍省略
   `implementations`，首轮 semantic constraint FAIL；
3. 两个 Case 的 operation、evidence ledger、第二步 transition、candidate binding 与 exact Ref projection 均正确。失败只来自
   `search_terms` 对原问题直接 Latin 词项的保留，且 Adapter 重述无法确定性修复。

根因是 Owner 放置错误。Provider Adapter 可以保证 Provider wire、schema 与 message rendering 兼容，但不应读取领域问题并承担
检索参数完整性。Application 已拥有 untrusted proposal 的校验、normalization、authority 参数编译和 12-term query bound；对问题中
直接出现的 ASCII identifier-shaped content token 做机械保留不需要 Source、工程词典、模型推理或 Provider 分支，因此应在该边界
确定性完成。模型仍负责跨 script 翻译和通用词形/identifier normalization。

## Decision and disposition

1. `java-source-semantics-investigation-argument-compiler` 升级为 `@7`。对完全 ASCII 的原问题，Application 用版本化 closed tokenizer
   拆分 word/camel identifier part，排除 function/discourse/authority/budget 词和 closed negated-presentation clause；
   保留下来的 question-owned term 在模型 normalization 之前进入 query，以 Unicode casefold 去重并共同受 12 项上限约束。
2. raw 模型 `search_terms` 仍先独立执行 1—12、非空与去重校验；raw Provider output 与 digest 保持原样审计。编译结果只改变正式
   Application query argument，不追溯改写 Provider response。非 ASCII 问题不做平台翻译，继续使用模型给出的 common English
   source-identifier translation；不得加入工程、Case、symbol 或 evaluator 词典。
3. DeepSeek Adapter 移除 schema-specific lexical-coverage adaptation 并升级为
   `deepseek-chat-completions-no-tools@6`，保留已资格的单一 leading system message 与 generic closed-schema rendering。`@5` 的语义
   不得复用。Gateway policy 升级为 `@1.4.7`；Configuration fingerprint 变为
   `sha256:70c3839f13d68434e6853afa994b8b83d85860a5037ab0371e112cd542716ae7`。
4. Provider-independent Prompt/Vocabulary、Strategy、suite/oracle 保持 `1.5.7/@16/@1.5.7`，18 Case / 40 calls / 18/18、typed
   operation Oracle、persistent TLS 与 no-retry 不变。现有 Contract 已要求直接 Latin material term 保留；本次是把该不变量放到
   能确定性执行的 Owner，而不是放宽资格或为 run-022 改题。

本 Finding 取代 `FINDING-008-031` 的 Adapter-owned 处置；run-021 与 run-022 的历史事实、失败 verdict 和已消费授权继续原样保留。

## Verification and closure

新增 compiler 回归覆盖 run-022 的 12-term 饱和输出、REF-PROVENANCE、前置/后置 negated presentation clause 与非 ASCII
cross-script 输入；相关 compiler/Strategy/Adapter/Capability/Gateway/freeze 回归 127/127 PASS，fake transport 完整执行 40 calls / 18 Case / 18/18
PASS。run-022 原始首轮输出经新 compiler 的零网络 replay 后，CYCLE-PROGRESS 与 REF-PROVENANCE 均满足原冻结 semantic groups；该
replay 不改写 run-022 verdict，也不替代新 live Qualification。

current documents 336/336、`compileall`、`git diff --check` 与 task-file credential-shaped secret scan PASS。允许 AF_UNIX 的完整
执行面为 1024/1029，raw exit 1；唯一 4 FAIL + 1 ERROR 的 test identity 与 failure marker 精确属于 `FINDING-008-020`：三项
V-009 Conformance implementation drift FAIL、一项同源 ERROR，以及一项 frozen Codex prepared-binary digest FAIL。没有新增
failure/error；该事实不冒充 raw full-suite PASS。

当前确定性 identity 为：

- Adapter `deepseek-chat-completions-no-tools@6`；
- Adapter implementation aggregate `sha256:ea60ce25d9889e0e48772cbbbe5fa574432f1595b2148a6804a1c331f92adff8`；
- Conformance fixture `1.2.0` / `sha256:98267b7d84dc9224750b39c18d64ccba3a006ce77dae6ed6548e9aca61ba6d49`；
- compiler `java-source-semantics-investigation-argument-compiler@7`；
- configuration fingerprint `sha256:70c3839f13d68434e6853afa994b8b83d85860a5037ab0371e112cd542716ae7`；
- bounded policy raw digest `sha256:93fe9ff283edfd157b3b686f60d8cd604e3ce44fea19e9bb169537e7fd29ee16`；
- qualification resource policy digest `sha256:6059387e81f39cca6bebf77f2a401352b72815d5ac4fa3888c4066914a220f4a`。
- System fileset digest：ITER-008 `sha256:5432e30f42c2c821c2e05c916e299b290e0aaf84f1f922a8471c0207cf82cfdf`，
  ITER-007 `sha256:221b193b6b6c7e5b041ce46a3b41992290527952efb583c714311604893c407e`。

System/code/local-test 处置闭合后形成 clean exact candidate
`837171e611ae6e1dd3a0939e446e0658b1d08d6c` / tree `11b4a2a083d1e1c0f239e0a132e61cd125cd12ec`。run-023 Conformance
preflight/authorization/result/terminal digest 为
`sha256:c7c730f556e994c7b3278a35104c47a631e46dd84997122f95c1133783813703` /
`sha256:fbc6a8c70f7d3b6bd19f17e636591459bc10c0ac700b1450838b3ee94264b93c` /
`sha256:16e947ad1aaf698227ae59f06db3ec53caca04eb9f1c46375adf6ae1bd960522` /
`sha256:5eb114c04f745b46137c4408ed16788be92d7979f0e4c1630a9b33ac342077fb`；恰好 2 requests / 12/12 PASS，TLS 1/1、
reuse 1、HTTP/credential 2/2、unknown/retry 0。

同候选 Capability freeze/authorization digest 为
`sha256:7bfd08c6307314a15b7f0d41e666d559154f7906c9818f4296ac5937fb724cae` /
`sha256:fdf3e0e23cc7010225e9d3e952dbc6390e051e7cc63578744d25bbb37ec0b43d`。它无 retry 完成 40 calls / 18 Case / 18/18
PASS，input/output tokens 84,396/2,560；TLS 1/1、reuse 39、HTTP/credential 40/40、unknown/retry 0。result/closed-document/
qualification-proof/qualification-document/terminal digest 为
`sha256:9306f487e79b4594154dd60e8dd55854cc9289b2ce057ed5fea0851baf03ba6d` /
`sha256:d17e6d67aa1ad8eeb0ac320d227faa4003094fc7ff098d72658758c19a62d977` /
`sha256:0c78cb15260a57ceac7d61c9cdcb9301c16854240d52b2186a5d77c4932f0c31` /
`sha256:15f4d4f19bd7acf6183e44db6b5cfa0721ae2b4888bc31718528a8fe4aa148ba` /
`sha256:c2175a9b2d200cf559f855267b8b3a438aa8eaf5472658c141426e2acd525563`。Qualification ref 为
`capability-evaluation:evaluation_result_8f299a82dbdc4d67bda87c77bde013b1`，valid until
`2026-08-27T11:28:37.309517+00:00`。

CYCLE-PROGRESS 首轮 terms 为 `methods/contribute/authentication/authenticate/auth`，REF-PROVENANCE 为
`implementations/returned/authentication/candidate`，PATH-EXISTS 为
`authentication/reach/session/issuance/static/calls`；三者 semantic constraints、typed operation 与 projection 均 PASS。两份
authorization 文件权限为 0600，run-023 证据无 credential-shaped secret 命中；授权均已消费且不可 retry。
hidden canary 未披露，Production Activation 为 `NOT_EXECUTED`。因此本 Finding 的 live qualification 验证也已闭合，
V-002 对当前 exact Contract 为 PASS；下一 Gate 是绑定该 authority chain 的 formal product freeze/Web，不直接执行
hidden canary 或 Production Activation。
