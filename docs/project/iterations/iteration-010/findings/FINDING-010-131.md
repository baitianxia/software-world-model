---
id: FINDING-010-131
kind: implementation-finding
status: superseded
authority: development-evidence
owners: [application, source, ai, security, quality]
depends_on: [FINDING-010-130]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: iteration-design
scope: systemic
disposition: preserve-v7-as-unaccepted-symptom-experiment
target: ITER-010-PDR-005
superseded_by: FINDING-010-133
---

# FINDING-010-131：v7 查询与审核提示只是未接受的症状实验

## Observation

run-042 后的本地 dirty candidate 把 model strategy/prompt 升到 `@7`、Primary input 升到
`ENGINEERING_AGENT_PRIMARY_INPUT@7`、Review input 升到 `ENGINEERING_AGENT_REVIEW_INPUT@3`。它新增两类提示：Source query
优先使用可能命中 path 的工程 symbol，以及 Reviewer 以 exact current request 限定 materiality。

聚焦测试只断言这些字段被写入 model input，并没有执行真实答案、Reviewer 校准或两个未参与修复的异质问题。该候选也没有比较唯一
Maven cognition、Agent 源码调查、答案综合和 Reviewer 各层，因此不能证明其命中了 earliest divergence。

## Superseding evidence

`FINDING-010-132/133` 证明 run-042 至少同时存在 Maven-only cognition 不适用于行为问题、Agent 未读取授权来源中的决定性事实和 Reviewer
批准不完整 Limitation 三类故障。将所有失败归结为查询排序与审核 scope 缺少因果依据；特别是“诚实 explicit scope 必须被尊重”若没有
独立 Need/Source truth 校验，还可能让 Agent 自行缩窄 scope 后被 Reviewer 错误放行。

## Decision and disposition

- v7 代码和测试保留在当前 worktree 作为未接受实验，不删除、不追认为 System truth，也不作为新开发对话的起点；
- Engineering Conversation Contract 撤销 `FINDING-010-131` 的来源关系和 v7 微策略；
- 不因领域 Prompt/role input 改动重复执行 Ark/DeepSeek Provider Conformance；
- `V-LAYER-ATTRIBUTION-001` 完成后，只允许把被反事实证据支持的最小部分重新设计到对应 Owner 层；其余部分拒绝。

本 Finding 由 `FINDING-010-133 / ITER-010-PDR-005` 取代。它不授权代码继续修改、Provider/model、Source disclosure、Browser 或
Production Activation。
