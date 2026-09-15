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
disposition: code-and-tests-only
target: src/software_world_model/application_services/lightweight_engineering_agent.py
---

# FINDING-010-284：cognition ordinal 与 Source read ordinal 的内部对齐

run-275 的 q1 暴露宽 cognition 页与受控 Source read 目录使用不同索引域，
且同一路径实体经去重后可能不在可读目录中；不是非 SOURCE 实体被错误删除。
一次尝试的 Application ordinal alias 已撤回，不作为产品能力或验证证据；当前
在 READ_SOURCE 选择边界保留 rejected selection，并向同一 Agent 提供一次机械
binding feedback，不重绑定 candidate identity。
run-276 的三个全新会话已验证原始 q1 的非法索引可重规划到有效 Source read，
并完成真实 Citation、fresh Reviewer 与授权交付；q2/q3 异质问题同样通过。
定向集成测试 `test_missing_source_read_index_replans_once_then_fails_closed` 覆盖
模型视图中的非法 read index：记录 `READ_INDEX_UNAVAILABLE` 并对重复动作
fail-closed；未增加模型可见字段，也不重绑定 candidate identity。C2 浏览器编排
仍待验证。
