---
id: FINDING-010-282
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, quality]
depends_on: [FINDING-010-281]
code: [src/software_world_model/application_services/lightweight_engineering_agent.py]
tests: []
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: project-existing-executable-action-subset
target: src/software_world_model/application_services/lightweight_engineering_agent.py
---

# FINDING-010-282：run-240 fresh C1 仍暴露证据规划耗尽

## Observation

在 clean product `2b8e3b9185caf4629418ed5c45a822b72973a66c`、公开 mall exact
Source revision `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` 上，run-240 真实启动
loopback Chat，3 个 Conversation、3 个 Turn、36 次 provider dispatch，未发生
post-dispatch unknown 或重放。

q1 原始角色重分配问题完成 cognition→Source READ→fresh Reviewer；Reviewer 在
step 11 给出 `MORE_EVIDENCE`，随后因固定工具预算已关闭而 fail-closed。
q2 Turn 获得 `ACCEPTED`，但该 logical run 的总体体验仍 `NOT_ACCEPTED`。
q3 真实执行后 Agent step budget exhausted。q1 的重复 SEARCH_SOURCE 被应用层拒绝
后，模型转而读取当前合法候选；没有发现 stale candidate 泄漏或拒绝记账错误。

## Disposition

这是 Agent 在 Reviewer 缺口后的证据优先级/规划问题，继续定位同一通用层；不得增加
预算、修改 Prompt/Schema、放宽 Reviewer 或加入题目特判。run-240 仅作为 fresh
失败证据，不满足 C1/C2/Alpha。
