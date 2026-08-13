---
id: FINDING-006-012
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality, security]
depends_on: [ITER-006-SLICE-001, ITER-006-VERIFICATION]
code: [src/software_world_model/interface/world_model_runtime_assets/gateway_authorized_workload.py]
tests: [tests/test_world_model_gateway_authorization.py]
iteration: ITER-006
classification: local-implementation
disposition: exclude-qualified-baseline-digest-from-authorized-wrapper-core
target: src/software_world_model/interface/world_model_runtime_assets/gateway_authorized_workload.py
---

# FINDING-006-012：Java baseline digest 被外层授权摘要同名字段覆盖

## Observation and evidence

run-007 World Model 六题都完成一次 Ark call，Answer/Gateway role report、operation audit 和内部 summary 均 PASS，但外层六个 terminal
全部在 `ROLE_POSTCONDITION` 失败。`_verify_answer_gateway` 的业务、安全、资格与计数条件均满足，唯一不可重建项是授权 Gateway
summary 的 `document_digest`。

Java qualified baseline `swm.iter-006.java-gateway-workload@1` 与旧 Maven baseline 不同，它带有自己的 `document_digest`。wrapper
构造 `summary_core` 时保留该字段，计算外层 digest 后又用外层 `document_digest` 覆盖同名键。因此被哈希的 baseline digest 不在
最终文档中；verifier 按外层 schema 删除最终 digest 后无法重建。run-007 的一份实际 summary 存储 `sha256:d75f5864…`，从可见
core 重建为 `sha256:fad9bc5e…`，精确证明该冲突。

## Classification and disposition

外层授权摘要从来不应暴露或依赖被包装文档的同名 seal；wrapper 已经把 baseline identity 通过 exact entrypoint hash、freeze
digest、qualification 与 policy 字段重新绑定。最小修复是在复制 baseline fields 时同时排除 `document_digest`，不放宽任何
postcondition、不改变 qualified Java baseline、不修改 Strategy/Prompt/policy，也不重跑 run-007。

新增 Java baseline 回归以一个带自身 digest 的真实形状验证最终外层文档可由 visible core 精确重建，并继续绑定
`QUALIFIED_CAPABILITY_BASELINE_ONLY`。Gateway focused tests 15/15 PASS；修复后 wrapper raw SHA-256 为
`ca853a9ab6cc0d9c84dc9549e977590eb1aae7deae3292f4eef47752f8d078d6`。这是本地实现缺陷，系统的 exact seal / fail-closed 语义
无需改变。

全新 run-008 将该 wrapper exact hash 密封进 protected stage；随后六题 World Model 的 Gateway/Answer summary 与外层
postcondition 全部 PASS，六个 terminal 均 SUCCESS。comparison `sha256:857085c4…` PASS，证明处置已在新的授权 population 中
闭合，同时不追溯改变 run-007 的六个失败事实。
