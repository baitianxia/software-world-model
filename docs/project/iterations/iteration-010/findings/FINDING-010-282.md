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

后续复核发现上述局部修正仍未改变 `available_actions`，且通过 observation 正文
substring 判断边界，不能作为受信状态。commit `d9b905e` 改为从当前 ToolResult 的
`result_ref + evidence_digest + authority receipt` 精确绑定的 `BROKER_DECISION` 结构化
`reason` 派生内部 `source_exhausted` 状态；同一 Turn 的 model view 与执行侧一致关闭
三类 Source fuse 耗尽后的 SEARCH/READ，保留 cognition/FINISH，下一 Turn 重新初始化。
新增的投影回归检查覆盖 source action 不可见、候选列表为空、正常路径不受影响；定向
测试 44/44 通过。该修正仍只闭合 fail-closed 边界，尚未提供 fresh C1 运行证据。

## Fresh run-242 boundary verification

以 clean `3b3376d` / tree `579c5b0d83413b8cc1dd004141ab986e1a6c25a0` 启动新的受控
run-242；配置使用同一公开 mall exact revision、既有双 Provider route、预算和真实
HTTPS pricing capture（`2026-09-13T18:25:52Z`，内容 digest
`sha256:755aa9b488d1185cba016ca4de3b3b6b8f593f5e13e5f9f961305289a5c8d242`）。listener
与 health 校验通过，terminal 记录 3 Conversation、3 Turn、36 dispatch（Ark 4、
DeepSeek 32），post-dispatch unknown 与 replay 均为 0。

run-242 q1 的 sealed model manifests 逐步显示：在 SOURCE fuse boundary 之后，后续
Agent model view 的 `available_actions` 实际为 cognition actions + `READ_SOURCE`/`FINISH`
（当仍有合法 cognition-derived read 时），而在所有 Source candidates 不可执行后最终
收敛为仅 `FINISH`；没有再次出现 SEARCH_SOURCE。q1 仍因 Reviewer 请求补证时 Source
tool budget 已关闭而 `NOT_ACCEPTED/BUDGET_EXHAUSTED`，q2、q3 的 Turn 均为
`ACCEPTED`。这证明 boundary projection 修正 live 生效，但不构成 C1 的原题加两个
异质问题闭环；剩余最早问题是 q1 在达到全局 Source fuse 前未取得足够证据，仍需从
通用 Agent/检索规划层继续定位，不能增加预算或题目规则。

进一步对账发现 q1 首次 Search 已有 literal hits，但 `filename_candidate_count=0` 时
Worker 仍把全部 fallback corpus 扫到 56 文件。后续修正为在非空 path-ranked cohort
已完成且已有 literal hit 时返回显式 `PARTIAL`，把未扫描 corpus 保留为 Coverage 边界；
这与既有 exact-stem early-stop 共用同一 Source search 机制，不改变 Fuse 上限、Result
modality、Citation identity 或 Broker contract。Source/Conversation/Agent/Cognition
定向测试共 76/76 通过；需要在 clean successor fresh run 中确认 q1 的剩余 Source read
预算和 Reviewer 闭环。

## Fresh run-245 and consumed-candidate correction

在 clean `46ffab3` / tree `06d42a71c53e72d38c42f0d1b68cbc23c12ac2e2` 上运行 run-245；
listener、health 和真实双 Provider Web dispatch 均完成，3 Conversation、3 Turn，
terminal 为 `STOPPED_AFTER_DISPATCH`，无 post-dispatch unknown 或 replay。q1 仍以
`BUDGET_EXHAUSTED` fail-closed：Source search 后成功读取 1、11、13、15、16，但
Agent 随后再次提交已消费的 read_index 16，未取得 answer/citation/review 闭环。

最早责任层定位为 Application-owned candidate consumption bookkeeping：候选是否已
消费仅由 Citation locator 对账，某些受控 Source read 的 locator 形态未与原 candidate
稳定归一化，导致同一 read_index 仍出现在模型可选集合。commit `c7a4697` 增加内部
非版本化的已执行 read_index 集合，并在 unread candidate projection 与执行校验中共同
排除；不新增 Agent 协议、Schema、Prompt、预算或题目逻辑。定向测试
`tests.test_lightweight_engineering_agent` + `tests.test_capability_cognition` 44/44
通过。run-245 仍不构成 C1/C2/Alpha 证据，需在 successor clean run 复验。

## Fresh run-250 and model-view consumption projection

run-250 使用 fresh official pricing capture (`2026-09-13T23:03:33Z`，页面 digest
未变) 并实际启动 loopback listener。输入审计显示 q1/q2 在同一 Conversation，q3 为
同一 Conversation 的澄清 Turn，q4/q5 为新问题和新 Conversation。q2、q3、q5
分别完成 `ACCEPTED/SUCCEEDED/AUTHORIZED`、真实 Citation 与独立 Review `APPROVED`；
q1 因重复 Source proposal、q4 因 Source fuse 关闭而 fail-closed，故该轮不是 C2
完成证据。

q1 的最早偏差进一步定位到同一 Agent 的 `model_view`：已消费 read_index 集合此前
只用于 Application 执行校验，未传入模型视图的 unread candidate projection。后续
successor 将既有内部 `executed_source_read_indexes` sidecar 传给
`LightweightAgentStepRequest`，仅影响 Application-owned candidate visibility，不增加
版本化协议、Prompt、预算、Provider 或题目规则；定向测试 44/44 通过。需在 clean
successor fresh run 复验 q1 与 C2 五轮链。

## Run-253 planning audit and search completeness correction

run-253 的 q1 model-facing manifest 显示，Source Search `updateRole` 只产生了
`UmsAdminController.java` 的两个 literal hits；其余可读候选是 controller/mapper 的
旧 cognition navigation，缺少实际 `UmsAdminServiceImpl#updateRole` 实现。Agent 因而在
读取 `12,1,2,3,4,5` 后 FINISH，Reviewer 才指出关键事实和 Citation 缺失，且 Source
fuse 已关闭。最早责任层是 Source search ranking/early-stop，而非重复消费。

successor 删除了针对“无 filename candidate 但已有 literal hit”而提前截断 fallback
corpus 的分支，恢复在既有 `maximum_files` 内继续扫描，以便 method-name 查询能发现
不含查询词于路径名中的实现文件；不改变 Source fuse、预算上限、结果 modality、Broker
或任何 Agent-facing schema。Source/Conversation/Agent/Cognition 定向测试 76/76
通过。需以当前 clean successor fresh C1 运行确认实现候选、引用及 Reviewer 闭环。
