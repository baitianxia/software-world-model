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

## Fresh run-241

在 clean `8cea04c11a94fad603c1e8ade5cffe76847112a6`（tree
`8d711a947716f3397c8da7d75e13a68ebc146592`）上，run-241 通过 listener、product/tree
和 fresh 官方 pricing 校验，真实完成 3 Conversation、3 Turn、38 provider dispatch，
无 post-dispatch unknown 或重放。q1 实际读取了 11、15、16；逐步 model manifest 显示
这些仍是 cognition/path candidates，未出现可识别的本轮 `LITERAL_TEXT_SEARCH_HIT`
read candidate，因此不能据此声称 direct-hit 排序已被 live 证实。之后仍出现重复
READ/no-progress（13、2），q1
fail-closed 为 `BUDGET_EXHAUSTED`。q2 Turn `ACCEPTED`，q3 仍因 Agent step budget
exhausted 失败。Source Search 结果进入受控 read candidate 的构造链仍需核对；Agent
在同一预算内对重复/低进展候选的收敛也未闭合，
故 C1/C2/Alpha 继续 `REWORK`。

## Run-241 source-fuse audit and fail-closed correction

对 run-241 的 SQLite model manifest 逐次核对 q1/q3：首次 `SOURCE_SEARCH` 的
`coverage.match_count` 为 0，返回的是 `IDENTIFIER_PATH_NAVIGATION_CANDIDATE`，而非
literal claim-support；后续 `SOURCE_READ` 的 Broker boundary 明确为
`SOURCE_FILE_FUSE_EXHAUSTED`。因此本次失败的最早责任层是 Source 检索预算耗尽后的
Application action projection，而不是 read-candidate 构造丢失。

commit `179aae0` 在既有内部 `_reserved_unread_cognition_candidates` 状态计算中对该
可信 boundary fail-closed，避免将不可执行 locator 继续投影为保留 READ 动作；没有新增
Agent 协议、版本化 schema、Prompt、预算或题目规则。定向测试 44/44 通过。该修正只消除
错误的不可执行动作投影，尚不构成 C1/C2/Alpha 证据。
