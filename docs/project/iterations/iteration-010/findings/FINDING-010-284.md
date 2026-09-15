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

run-277/run-279 的两个异质无命中轨迹进一步确认：重复的未执行搜索提案也属于
无进展，不能绕过既有 `maximum_consecutive_no_progress` 收敛熔断。Application
现对重复提案使用同一熔断，不增加 Agent step、Tool、Provider 或 Reviewer 预算；
达到阈值后保留原始轨迹并 fail-closed，避免模型在相同查询上旋转。
定向测试 `test_repeated_no_progress_searches_close_fuse_without_extra_tool_dispatch`
固定验证该行为：一次实际搜索后，重复提案不再产生 Tool dispatch，熔断关闭并
进入经审核的 limitation；现有重复读取形状也继续通过。
异质夹具 `test_cognition_empty_then_repeated_source_search_also_closes_fuse`
进一步覆盖 cognition 无命中后转入 Source 搜索的相同收敛边界。
