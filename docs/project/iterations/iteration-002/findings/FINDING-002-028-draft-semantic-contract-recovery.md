---
id: FINDING-002-028
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-002-SLICE-001, SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING]
code: [src/software_world_model/ai_infrastructure/evidence_answer_strategy.py]
tests: [tests/test_evidence_answer_strategy.py]
iteration: ITER-002
classification: system-contract
disposition: bounded-complete-draft-replacement
target: SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING
---

# FINDING-002-028：生成结果满足 JSON Schema 但违反答案段语义约束

## Observation

本机端到端测试中，模型返回了结构完整的 Answer Draft，但把 `UNKNOWN` 段与 Evidence ID 同时提交。Adapter 的 JSON Schema 只能验证字段形状；应用层正确拒绝“未知内容声称有证据”，但生成角色没有获得修正机会，浏览器直接返回 `STRUCTURED_OUTPUT_INVALID`。

## Impact

这是所有工程和问题都可能遇到的模型契约恢复缺口，不是特定源码或题型问题。直接放宽 `UNKNOWN` 的证据限制会破坏证据语义；直接向用户暴露第一次可修正的模型格式错误又降低正常体验可靠性。

## Decision and disposition

保持 `SUPPORTED` 必须引用证据、`UNKNOWN` 不得引用证据的强约束。对于 Provider 已完整返回、JSON Schema 已通过、但应用层 Answer Draft 语义校验失败的结果，生成角色在固定 Checklist 和 Evidence Packet 下执行有界的完整对象替换；每次使用新的稳定执行引用并携带精确拒绝原因。修正耗尽仍失败关闭，且不得把无效草稿送入独立审核。
