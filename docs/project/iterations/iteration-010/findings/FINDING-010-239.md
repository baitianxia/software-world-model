---
id: FINDING-010-239
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [ai, operations, quality]
depends_on: [FINDING-010-238, ITER-010-VERIFICATION, SYS-CONTRACT-AI-MODEL-GATEWAY]
code: [src/software_world_model/ai_infrastructure/ark_chat_conformance.py]
tests: [tests/test_ark_chat_conformance.py]
iteration: ITER-010
classification: verification
scope: general
disposition: preserve-safe-metadata-and-enumerated-failure-class-for-completed-conformance-responses-rejected-by-closed-output-validation
target: ITER-010-VERIFICATION
---

# FINDING-010-239：Conformance 丢失 completed-but-rejected response 的安全元数据

## Observation and evidence

在 clean `glm-5.3/@9` candidate `61a694ad09923383ffc101896413178a1f294cf8 / 26a69518f32e7e58c82760d20356814c32e92907`
上，fresh Conformance `ccrun_98d71692fe8e4fe5b6265a30ed8a72f2` 发出两个 verified-TLS HTTP request：第一个通过 closed output contract，
第二个 completed response 被 `STRUCTURED_OUTPUT_INVALID` 拒绝。artifact 因只汇总 valid response 而只保留一个 request ID、actual model 与
usage；result digest 为 `sha256:72d68aafbc42d8e50bcb3ce1ac75961e93ad8d167d742aa8d5eab7a61b734592`。

第二个 fresh run `ccrun_6f327181a346478682bed8819802daf4` 的第一个 HTTP response 即被同类 validator 拒绝，因此 artifact 虽准确记录
`request_count=1`、TLS/credential/HTTP 均为 1，却把 actual models、request IDs 与 usage 投影为空/零；result digest 为
`sha256:f98feeed0a22f23e4c495b914d717742b7eb9527c0c8e22807e6104c30926f50`。随后一次固定 probe 在 HTTP 前以
`DNS_RESOLUTION_FAILED` unavailable 结束，零 HTTP，不能改变上述 completed-response 事实。

Adapter 的 `ProviderOutputRejected` 已持有 completed `AdapterResponse`，包括安全 request ID、actual fingerprint、usage、termination 和
output digest；缺口只在 Conformance 汇总层丢弃该对象。raw output/prompt 不需要也不允许进入 artifact。

## Decision and disposition

1. Conformance 仍只把通过 closed contract 的 response 计入 PASS oracle；任何 completed-but-rejected response 继续使本次资格 FAIL，不能被
   当成有效响应或 Provider unavailable。
2. execution/model 汇总改为同时从 valid 与 rejected completed response 投影安全 request ID、actual fingerprint 和 usage；raw output 仍不
   持久化，fixture wire bytes、Adapter request、route 与 eligibility 均不变。
3. `STRUCTURED_OUTPUT_INVALID` 只增加本地枚举分类：`INCOMPLETE_TERMINATION`、`JSON_SYNTAX_ERROR`、`NON_OBJECT_ROOT` 或
   `CLOSED_SCHEMA_MISMATCH`。Provider message/body、model text 与 schema value 均不记录。
4. 单元测试证明 JSON-invalid completed response 的 identity/usage 被保留、原文未泄漏且结果仍为 FAIL。修改进入 Conformance
   implementation aggregate，故须在 clean successor 上重新执行 fresh qualification。
