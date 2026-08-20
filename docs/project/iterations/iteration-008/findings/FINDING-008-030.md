---
id: FINDING-008-030
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai, application, engineering, quality, project]
depends_on: [ITER-008-SLICE-001, FINDING-008-029, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
code: [src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_policy.json, validation/structure_world_model_iteration_008/capability]
tests: [tests/test_world_model_answer_strategy.py, tests/test_iteration_008_capability_harness.py, tests/test_iteration_008_capability_qualification.py, tests/test_model_egress_gateway.py]
iteration: ITER-008
classification: system-contract
disposition: question-semantic-equivalence-and-evidence-intent-adaptation
target: SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING
---

# FINDING-008-030：run-020 暴露跨脚本 Oracle 假阴性与 evidence intent 提示歧义

## Observation

exact clean candidate `5bdf83b3931f2aa9f3065f23593c4e0bf3da7030`（tree
`b7f69fbff52d54216050c73157a865d5d57b8b13`）的 run-020 零调用 preflight
`sha256:3afe56e2ce253b30f81494d1cafea2b1a2fe43c42a4696ea4b9b899cc70cddba` 已 PASS。其 DeepSeek Conformance
以精确 2 calls PASS，result digest 为
`sha256:e20eef6cad6267fc9ef203c7cfc136f4f8537ef6b0c74a652b5ed1ecaa00c0eb`，实际模型 `deepseek-v4-pro`、
temperature 0、thinking disabled、1 次 verified TLS handshake、1 次 connection reuse、0 retry，valid until
`2026-09-19T10:17:22.817950Z`。

随后 Capability freeze
`sha256:07982a4e689f3eeac7ddd5cb5eb7828b60200428019dba530d397fae3f6c02f4` 的单次授权运行在第 33 个 request
停止。13 个 Case / 32 个 provider request 已完成；第 14 个 Case 首次 request 已完成但在本地 evidence-obligation 校验失败，
因此 attempted request count 为 33。failure digest 为
`sha256:b227f51378b7d5cfb94f13853d662949fce19a47a27b1b61a3b890d5dc2ed445`，terminal digest 为
`sha256:011425a39a26d9bbdcde4c1cf03d1660af2765337bd9444208aae652b5682a1d`。授权已消费且不可 retry；hidden
canary、formal product、SLICE-002 与 Production Activation 均未执行。

## Evidence and root cause

这不是网络、credential、Provider shape 或模型 identity 故障。run-020 的 33 个 HTTP dispatch 共用 1 次 verified TLS handshake，
32 次连接复用，credential resolution 33/33，pre/post-dispatch failure、outcome unknown 和 retry 都为 0。失败来自两项本地适配边界：

1. 中文首 Case 的真实 normalized search terms 为 `invalid / credential / authentication / exception / log / success / return /
   session`，已经为全部物质概念提供 common English identifier translation；operation 与 `method_implementations` evidence request 也正确。
   旧 semantic group 却只接受 `record|audit` 表达“记录”，把通用 identifier translation `log` 误判为遗漏。该 Case 的
   normalized result digest 为 `sha256:f6042f70d9c5fc1c2f673960d1ffa8940190cb83cc6977a8ebcb828cb00589c4`；旧 verdict 保持 FAIL，
   不能被新 Oracle 追溯改写。
2. 英文 Case 007/012/013 分别省略显式 relation `reach`、code-artifact noun `method` 与 `implementation`，虽然 operation 或宽泛
   topic 已表达相关语义。`@15` Prompt 的“source-identifier term”措辞没有足够明确 operation/topic 不能替代原问题显式检索概念。
3. 第 14 个问题 `Does the authorized scope implement purchase-order cancellation?` 的模型 output 正确选择
   `implementation_candidates` 与 `purchase/order/cancellation/cancel`，却把 evidence request 选成 `path_exists`。旧 Prompt 把
   `whether/can/does one concept reach another` 写作 reachability 判据，模型把一般疑问词 `Does` 本身错误提升为 reachability；问题实际请求
   implementation existence，应收敛到 `method_implementations`。

根因是 systemic prompt/qualification semantic adaptation 缺口，而不是要求 DeepSeek 改成另一种输出。旧 run-020 永久保留原 FAIL；
修正只能形成新版本 Definition 后重新执行，不能追加 Oracle option 或复用授权来改变旧 verdict。

## Decision and disposition

1. bounded Investigation Contract/Strategy 升级为 `1.5.7`、Prompt/Vocabulary `@16`。Latin-script 问题的每个显式 material
   retrieval concept 必须保留直接词形，不能用 broader topic synonym 或 evidence operation 代替。
2. `path_exists` 只在问题显式命名 reachability/call-path connectivity 时使用；一般疑问形式 `whether/can/does` 本身不构成
   reachability，implementation existence 使用 `method_implementations`。不新增工程、Case、symbol 或 Provider 特判。
3. suite/oracle 升级为 `@1.5.7`。中文 Case 的“记录”equivalence group 在新运行前冻结为
   `record|audit|log|logging`；其余 18 Case、40 calls、typed projections、threshold、budget、no-retry、Provider 与 Adapter 不变。
   这是 System 允许的 question-derived translation 集合，不接受任意新词，也不回写 run-020 verdict。
4. bounded egress policy 升级为 `@1.4.5`。旧 `1.5.6/@15/@1.4.4` 的 Conformance PASS 只证明 Adapter；run-020 Capability FAIL
   不能授权 product Gateway。新 identity 必须从 clean exact candidate 重新完成 2-call Conformance 与 40-call Capability。

System Contract 已同步写回 `SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING` 与
`SYS-CONTRACT-AI-CAPABILITY-EVALUATION`；主处置 Owner 为 World Model Answering。

## Verification and closure

本地相关 contract/capability/runtime/freeze/Gateway 回归 115/115 PASS；fake transport 再次完整执行 18 Case / 40 calls 并
18/18 PASS；current documents 334/334、`compileall`、`git diff --check` 与 task-file credential-shaped secret scan PASS。允许
AF_UNIX 的完整执行面为 1022/1027，raw exit 1，唯一 4 FAIL + 1 ERROR 的测试 identity 与原因仍精确属于
`FINDING-008-020`，没有新增失败。新确定性 identity 为：

- prompt program `sha256:9047c3b7f14d710f5ddeb124293a02d8e7da369d5834ea9437b17ec4c27a705f`；
- Strategy implementation `sha256:bfd90d1dfc26ab913778fad39b8183b0b34d6860762ce082e4abcfc113db7f95`；
- policy raw `sha256:cb9cea5f56b294fcdfb66aeb346c2e0a09c3e19e77fe6b7a647c6c99eaf2de27`；
- qualification resource policy `sha256:a5f2a26219b41e9c610378717eb95515162434d1b06e170d00e12e4ca81f049e`；
- suite/oracle raw `sha256:68900e343fb04076ad9ceab99aea29eaa11cbdb254b28c28298169d791d8e6de` /
  `sha256:3c20ce70181fd6c9e974d34b7ff597afbf5cc0f149a1efe0541f6ff10ae669e7`；
- bounded Gateway workload raw `sha256:af5059c2b7ed34ac25817995570bb7d7f174f46e117752d7535141992e2ce3c3`。

System fileset digest 为 ITER-008
`sha256:5d0f8c9a3c5b06e81e3c5729f7b50242044e28b8c0f8ef54dbcdbc67f0eed0b9`、ITER-007
`sha256:f6ea0d60e4d39d77ac3e950f3de27551072f65b018a19a79d24705eb30507e9e`。

Finding 的代码、System 与本地验证处置已闭合；V-002 仍为 NOT-RUN/blocking，直至新 clean candidate 的 live Conformance/Capability
正式 PASS。通过前不得生成新的 formal product PASS、继续 Web 第二题、执行 hidden canary 或 Production Activation。
