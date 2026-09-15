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
disposition: rework-required-before-c1
target: src/software_world_model/application_services/lightweight_engineering_agent.py
---

# FINDING-010-284：cognition ordinal 与 Source read ordinal 的内部对齐

run-275 的 q1 证明宽 cognition 页可暴露目标方法，但非 SOURCE 实体会被从
受控 Source read 选项中省略，导致模型把 cognition ordinal 当作 read ordinal
而触发 `CONTROL_STATE_DENIED`。一次尝试的 Application ordinal alias 已撤回，
不作为产品能力或验证证据；当前状态是 capped cognition/read-option projection
缺口。当前修复在 Agent-facing cognition projection 中对 SEARCH 页每个重复
Source path 保留一个稳定代表（detail/traverse 不过滤），保留底层快照、cursor、Citation identity 与 Source 权限不变，使
cognition-facing ordinal 与受控 path option 域一致。run-275 的 q2/q3 已真实
完成读取但整体质量仍未接受；新的 C1 successor 仍需验证 q1 补证闭环。
The projection now uses one deterministic representative for every repeated
canonical Source path in a SEARCH page (including TYPE+single METHOD and
TYPE+multiple METHOD cases); detail/traverse remain unfiltered. This is an
intentional cognition-page omission with the underlying snapshot total/cursor
unchanged, and must not be described as pagination of the omitted sibling.
