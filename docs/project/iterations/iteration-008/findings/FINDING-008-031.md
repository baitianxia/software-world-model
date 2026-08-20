---
id: FINDING-008-031
kind: implementation-finding
status: superseded
superseded_by: FINDING-008-032
authority: development-evidence
owners: [ai, architecture, engineering, quality, project]
depends_on: [ITER-008-SLICE-001, FINDING-008-030, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING]
code: [src/software_world_model/ai_infrastructure/deepseek_chat_adapter.py, src/software_world_model/ai_infrastructure/model_egress_gateway.py, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_policy.json, src/software_world_model/ai_infrastructure/bounded_java_source_semantics_model_egress_qualification.py]
tests: [tests/test_deepseek_chat_adapter.py, tests/test_deepseek_chat_conformance.py, tests/test_model_egress_gateway.py, tests/test_iteration_008_capability_harness.py, tests/test_iteration_008_capability_qualification.py]
iteration: ITER-008
classification: system-contract
disposition: deepseek-active-stage-lexical-coverage-wire-adaptation
target: SYS-CONTRACT-AI-MODEL-GATEWAY
---

# FINDING-008-031：DeepSeek 必须在适配层保留 active-stage lexical coverage

## Observation

exact clean candidate `0e6b60f166e37e1397c483260ee70b6ad9f91cb8`（tree
`9c24a0eb2ae552131a26b651296f791ebe27daba`）的 run-021 零调用 preflight
`sha256:4b1675d55c1e387876cf512258c99978527cf53079acc373e936c5656491bfd4` 已 PASS。其 Conformance authorization/result digest 为
`sha256:23bda2528122855768b0c0045d3f4f9fa1420ac7457feb9ec9e451a2faee106f` /
`sha256:bc28d3d358bcff18487a098480a8a94fcae1827d2ae539ad0d284ea8b2126813`，精确 2 calls PASS。

同候选 Capability freeze/authorization digest 为
`sha256:732fbdc3e75b951cc1397fc68334ac40e7ff1b7f4cfe616ccdbd6deeedb29158` /
`sha256:ce4ee5b4b8678318c401292ac1a0936ebc79e400f48b46e1b08ee52c94fd635e`。运行无 retry 完成全部 40 个 Provider
request 和 18 个 Case，15 Case PASS、3 Case FAIL、unknown 为 0；closed result/result/document digest 为
`sha256:4757153bab4b9ce1b5bd7c616cdbc5934686539ae70723f376e6ca7247d7d60e` /
`sha256:6096b6b3be57d4dd3083c65d3408b655eb11415a5f4047485ff3e2bfb862437e`。没有生成 Qualification、formal product、hidden
canary 或 Production Activation，授权已消费且不可 retry。

## Evidence and root cause

这不是网络、credential、模型 identity、JSON shape、operation 或 Application compiler 故障。Capability transport 为 1 次 verified
TLS handshake、39 次连接复用、40/40 HTTP dispatch 与 credential resolution，pre/post-dispatch failure、outcome unknown 和 retry
均为 0。run-020 暴露的中文 equivalence 与 implementation-existence intent 已在 run-021 PASS；全部 later-step typed projection、exact
Ref 和 evidence transition 也继续 PASS。

三个失败只发生在首轮 `search_terms` lexical coverage：

1. PATH-EXISTS 问题明确包含 `reach`，模型给出 `authentication/session/issuance/static/calls`，但把 relation 只表达为
   `evidence_requests.path_exists`；
2. CYCLE-PROGRESS 问题明确包含 `methods`，模型只给出 `authentication/authenticate/auth`，把 artifact noun 只表达为
   `method_implementations`；
3. REF-PROVENANCE 问题明确包含 `implementations` 与 `candidates`，模型给出 `authentication/candidate`，把 implementation noun
   只表达为 operation/evidence request。

活动 `1.5.7/@16` Provider-independent Prompt 已明确 operation/topic 不能代替显式 material term；继续改写同一上游语义、放宽
Oracle 或在返回后静默补词都会分别造成 Provider 泄漏、资格降级或模型输出审计失真。根因是 DeepSeek 对长 system authority 的字段间
语义压缩：它把 `search_terms` 当摘要，并认为其他 JSON 字段可满足该字段自己的 lexical-coverage obligation。这是
Provider message rendering 的系统性兼容边界。

## Decision and disposition

1. DeepSeek Adapter 升级为 `deepseek-chat-completions-no-tools@5`。只有 active output schema 精确为 bounded Investigation intent
   且 Gateway 已提供 leading system authority 时，Adapter 才在同一个 system message 末尾追加无损的 Provider execution
   adaptation：首轮 `search_terms` 是独立 lexical-coverage list，不能由 `operation/evidence_requests` 代替；later step 仍必须为空。
2. 该 adaptation 不包含题目、Case、工程、symbol、具体词例或 Oracle，不引入其他 capability instruction，也不修改 Provider 返回值。
   Draft/Review 与 generic schema 不接收该段。上游 Strategy、Prompt/Vocabulary、compiler、suite/oracle 保持
   `1.5.7/@16/@6/@1.5.7`，18 Case / 40 calls / 18/18 与 no-retry 不变。
3. `SYS-CONTRACT-AI-MODEL-GATEWAY` 明确：Provider-specific rendering 可以对当前 active stage 做版本化、语义等价的显著性重述，但
   不能新增语义或执行 response post-processing；通用 wire 由 Adapter Conformance 证明，schema-specific semantic branch 还必须由
   exact Capability Qualification 证明。
4. bounded egress policy 升级为 `@1.4.6`。Conformance fixture `1.2.0/@2` 无变化，但 Adapter implementation/version 与
   configuration fingerprint 已变化，旧 Conformance 仍然失效；新 clean candidate 必须重新完成 2-call Conformance 和完整 Capability。

## Verification and closure

Adapter 与相关 DeepSeek/Gateway/Capability/runtime/freeze 回归为 152/152 PASS；沙箱内 AF_UNIX 失败已在允许本地 socket 的执行面
重跑并全部 PASS。fake transport 端到端测试另确认精确 40 calls / 18 Case / 18/18 PASS。Adapter 测试同时证明 generic schema 不接收
adaptation、Investigation schema 恰好接收一次、消息仍只有一个 leading system authority，且 adaptation 不改变 user message 顺序。
current documents 335/335 PASS。

允许 AF_UNIX 的完整执行面为 1023/1028，raw exit 1；唯一 4 FAIL + 1 ERROR 的 test identity 与 failure marker 仍精确属于
`FINDING-008-020`：三项 V-009 Conformance implementation drift FAIL、一项同源 ERROR，以及一项 frozen Codex prepared-binary
digest FAIL。没有新增 failure/error；该事实不冒充 raw full-suite PASS。

当前确定性 identity 为：

- Adapter `deepseek-chat-completions-no-tools@5`；
- Adapter implementation aggregate `sha256:cbc346caad15193737e5c15a5a48462eea69711e58b523f12bfd3f1b3e19111c`；
- Conformance fixture `1.2.0` / `sha256:98267b7d84dc9224750b39c18d64ccba3a006ce77dae6ed6548e9aca61ba6d49`；
- configuration fingerprint `sha256:31dc8d9bd143ab4c5aee94a5e9cdafdbd19103a645ad40e30893348ab3c2640d`；
- bounded policy raw digest `sha256:889afd1845f573ee0a9565d3fd2f6e69b6c824b72c20138c12cde93da7c407d0`；
- qualification resource policy digest `sha256:d4ed3c84921813f8d504c6c89414b567d8e46429278528d2c3b25b208fb9b528`。
- ITER-008 System fileset digest `sha256:a7ea2772fee6d5e7aeb3e0ad7233afb0f9f9d77ce5a6f34e3db26ce448066440`。

Finding 的 System/code/local-test 处置已闭合；V-002 仍为 NOT-RUN/blocking，直到新 clean candidate 的 live
Conformance/Capability 形成 PASS。通过前不得生成 formal product PASS、继续 Web 第二题、执行 hidden canary 或 Production
Activation。

## Supersession

后续 exact run-022 证明 Adapter `@5` 的显著性重述仍不能稳定保留 `methods/implementations`，因此本 Finding 的
Adapter-owned disposition 已由 `FINDING-008-032` 取代。该 Finding 的 run-021 证据、`@5` 历史实现身份和失败 verdict 不变；活动
处置改为 Application-owned deterministic question-term compilation，且必须以新 identity 重新资格。
