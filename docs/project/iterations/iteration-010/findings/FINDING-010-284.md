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
缺口。已撤回会删除 cognition 实体的 projection 方案；当前改为在 READ_SOURCE
选择边界保留 rejected selection 并向同一 Agent 提供一次机械 binding feedback，
第二次在 immutable prefix 下立即 `CONTROL_STATE_DENIED`，不引入 ordinal alias。
run-275 的 q2/q3 已真实完成读取但整体质量仍未接受；新的 C1 successor 仍需
验证 q1 补证闭环。
