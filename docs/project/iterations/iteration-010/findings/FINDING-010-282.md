---
id: FINDING-010-282
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, quality]
depends_on: [FINDING-010-281]
code: [src/software_world_model/application_services/lightweight_engineering_agent.py]
tests: [tests/test_lightweight_engineering_agent.py]
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

代码对账显示，Source search 返回的新 literal 候选与较早 cognition navigation
候选共存时，旧排序可把 cognition sibling 放在 direct search 命中之前。排序是否是
run-240 低价值读取的充分原因仍是待验证假设；不能从候选顺序推断模型一定会选择它。

## Disposition

这是 Agent 在 Reviewer 缺口后的证据优先级/规划问题，继续定位同一通用层；不得增加
预算、修改 Prompt/Schema、放宽 Reviewer 或加入题目特判。run-240 仅作为 fresh
失败证据，不满足 C1/C2/Alpha。

当前修正仅在既有 Application ordering sidecar 能证明候选来自最新一次
`SOURCE_SEARCH` 调用且 modality 为 literal/full Source 时，将该 direct hit 排在旧
cognition navigation sibling 前；不删除候选、不改变 read index、Citation identity、
预算或模型协议。该排序是导航启发式，不授予答案证据支持。

## Multi-observation correction

独立监督发现 `28d561c` 的最大 observation index 不是调用身份：同一搜索的 SUPPORT
之后可能跟 BOUNDARY，候选登记在 SUPPORT 而最大 index 属于 BOUNDARY。
`test_source_search_priority_binds_support_and_boundary_invocation` 在该提交上实际得到
历史候选在前的 `[1, 2]`，而期望最新搜索候选在前的 `[2, 1]`。

修正由 `_execute_action` 在核对同一 ToolResult 与各 authority receipt 的 request digest
后，汇总本次 SUPPORT 的完整 Citation digest，并一次更新内部 sidecar。空搜索或拒绝
结果也清除历史命中标记；不再用全局 observation 次序猜测调用边界。测试同时覆盖
SUPPORT+BOUNDARY、多次搜索、空结果以及非提升候选的相对顺序/身份守恒。
这是局部登记实现纠错，不改变跨模块契约。live C1 仍须在 clean 新候选上复验。
