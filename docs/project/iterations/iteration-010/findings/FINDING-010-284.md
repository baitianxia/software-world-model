---
id: FINDING-010-284
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, knowledge, quality]
depends_on: [FINDING-010-283]
code: [src/software_world_model/application_services/lightweight_engineering_agent.py]
tests: [tests/test_lightweight_engineering_agent.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: code-tests-only-no-system-contract-change
target: src/software_world_model/application_services/lightweight_engineering_agent.py
---

# FINDING-010-284：cognition ordinal 与 Source read ordinal 的内部对齐

run-275 的 q1 证明宽 cognition 页可暴露目标方法，但非 SOURCE 实体会被从
受控 Source read 选项中省略，导致模型把 cognition ordinal 当作 read ordinal
而触发 `CONTROL_STATE_DENIED`。Application 现在仅在 sidecar 提供唯一可信
`origin_cognition_index` 时将该选择归一化到实际 `read_index`；Citation、源码
版本、权限、预算和 fail-closed 行为不变，歧义选择仍拒绝。run-275 的 q2/q3
已真实完成读取但整体质量仍未接受；新的 C1 successor 仍需验证 q1 补证闭环。
