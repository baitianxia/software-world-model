---
id: FINDING-010-280
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, quality]
depends_on: [FINDING-010-279, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/lightweight_engineering_agent.py]
tests: [tests/test_lightweight_engineering_agent.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: project-existing-executable-action-subset
target: src/software_world_model/application_services/lightweight_engineering_agent.py
---

# FINDING-010-280：动作呈现必须与已有执行限制一致

## Observation

run-202 的第 9 步 fresh Review 返回 MORE_EVIDENCE，第 10 步 Primary 选择 SEARCH_SOURCE，随后被已有 unread-cognition-Source guard 拒绝；
第 11 步 READ_SOURCE 成功后耗尽的是外层 Agent step，而不是 Tool action fuse。候选排序已经把未读接口声明提前，但 `available_actions` 仍把
执行器会拒绝的搜索/遍历列为可用。这是 Application 向同一个 Agent 呈现可执行状态的不一致，不证明需要扩大预算或改变 Provider/答案协议。

## Evidence

- `abf2db9` 的 `model_view()` 无条件按 cognition/tool enablement 展示动作；执行器另行检查 MORE_EVIDENCE 或 Application no-progress 与未读
  typed Source candidate。相同状态下两者的可用动作不一致。
- 新增 deterministic production-executor 测试在固定 6 Agent steps、4 Tool actions 内重现：修复前 `NOT_ACCEPTED`，修复后补读另一个 Source，
  第二次 fresh review 后 `ACCEPTED`，没有被拒绝的搜索或额外 Tool dispatch。它验证机械闭环，不替代三个真实问题的 N1 证据。
- fresh `run-206-c1-action-projection` 在当前提交上实际启动 listener 并完成 1 个原始问题 Turn（12 次 Provider dispatch）；轨迹显示动作投影已收窄，
  但 Agent 仍在补证阶段选择普通未读候选，最终 `BUDGET_EXHAUSTED`。因此该运行是当前最早 Agent 规划缺口的反证，不计入 N1 成功。
- 测试保留普通 cognition/search、无候选、无 typed sidecar、全部已读、Tool fuse 关闭及 no-progress 状态；Candidate/Citation/Observation 不变。

## Disposition

只抽取已有 guard 的共同状态计算，使原有 `available_actions` 在该状态下排除重复 Source search，同时保留 `READ_SOURCE/FINISH` 以及 cognition
自身的查询/关系/详情动作，用于在 typed sidecar 不足时继续定位相关声明；执行端保留同一 guard。不新增字段、版本、
提示词、答案检查、预算或源码规则，也不自动选择/读取候选。既有反馈标记只识别 Application 自己的状态，不解析问题或 Reviewer 正文语义。
这是现有执行限制的本地一致性修复，不改变系统契约。run-202 及两个异质真实任务仍须 fresh 验证；本 Finding 不宣布 N1、Phase C 或 Alpha 完成。
