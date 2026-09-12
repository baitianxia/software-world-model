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

## Follow-up observation

`run-207-c1-cognition-replan` 在 `5498d0a` 上以 6 次 dispatch 失败：两次重复 cognition 搜索被拒绝，后续 FINISH 经一次 Citation binding
rejection 后进入 fresh Review，收到 MORE_EVIDENCE 时 Tool fuse 已关闭。它不是 `b13c046` 的验证证据。

`b13c046` 的动作类别屏蔽实现和原说明不符：集合实际在 REVIEW_GAP_UNREAD_SOURCE 分支添加，而非 REPEATED_ACTION；移除发生于 Tool
执行前且只针对同种动作，不是成功执行其他动作后恢复。新增回归测试证明：拒绝一个已读候选后，仍有真实未读候选，但 READ_SOURCE 整类
从可用动作消失。因此撤销该类别屏蔽，只保留已有精确 action fingerprint 防重及候选排序；修复前该测试失败、撤销后通过。
这是对错误实现和报告的纠正，不是 N1 闭合。原问题与两个异质 fresh 轨迹仍未齐全。

在 `96dd66d` 后续补丁中，现有 cognition Observation 内容现在携带本次已执行调用的
`execution_provenance`（action、query/cursor 或 entity/relation/direction/depth）。该元数据不进入顶层 Agent schema、Evidence 或 Citation，
并由确定性测试验证 search/traverse/detail 三类输入均可追溯。它针对的是 Agent 看不到自身调用参数的通用观察缺口，而不是提示词或答案规则。

`run-208-c1-provenance` 已绑定 `071789b` 并实际启动 loopback；首个原问题在 Provider dispatch 前收到 `LIVE_INTEGRATION_HELD`，随后
DeepSeek admission 也被拒绝，Turn 为 `NOT_ACCEPTED`，无真实 Provider HTTP dispatch。该结果是外部准入失败，按既有 cadence 重试，不能作为
Agent 能力或 N1 证据，也不重放该请求。

`run-209-c1-provenance` 在同一快照上实际完成三个独立 Conversation：原始权限分配问题与注册/角色关系问题均为 `ACCEPTED`，各有 4 个真实
Citation，且轨迹均包含 `MORE_EVIDENCE → APPROVED` 的 fresh review 闭环；库存/缓存异质问题完成 cognition 与 Source 读取后，在第 8 次
调用前触发 DeepSeek 准入拒绝，未进入 fresh review。该运行使原问题加一个异质问题通过，但 N1 仍缺第二个异质 fresh-review 证据。

同时为 `5498d0a` 的 cognition 重规划补充实际执行器测试：MORE_EVIDENCE 后分别执行 search、traverse、detail，随后读取另一份 Source，
在固定 7 Agent steps、5 Tool actions 内进入第二次 fresh review；三条本地路径均通过，未新增接口字段或放大生产预算。run-207 的旧 listener
已在确认 6 个调用全部 COMPLETED、1 个 Turn 完成后退出，生成真实 terminal receipt；没有在途调用或重放。

`run-210-c1-inventory` 仅重试前一运行未完成的库存/缓存问题；该 Turn 在 exact 当前 product commit 上为 `ACCEPTED`，4 个 Citation，轨迹包含
`SEARCH_COGNITION → SEARCH_SOURCE/READ_SOURCE → REWRITE → fresh REVIEW(APPROVED)`，11 次 Ark dispatch，listener 已实际启动并安全收尾。
结合 run-209 的原问题和注册/关系问题，原问题加两个异质任务现均有独立 fresh-review 成功轨迹；这些运行证据仍须监督方按 N1 规则核验，不能由开发方自行宣布 ADVANCE。
## Run-211 C2 safety-boundary evidence (2026-09-12)

The current exact-Source artifact-backed loopback listener was started with HEAD
`aa902dc2ead63cadd981a5af498bbd1a9f2f51c0` and returned `/health` 200. A
fresh first Turn was accepted by the loopback endpoint, then closed fail-closed
before an answer or citation was authorized: Ark recorded
`LIVE_INTEGRATION_HELD` and the fallback route recorded
`CONTROL_STATE_DENIED`. The Conversation remained active for later turns.
This is retained as external admission evidence, not replayed as a
post-dispatch unknown and not treated as C2 completion.

## Run-213 fresh pricing and Provider boundary evidence (2026-09-12)

Run-213 used a fresh official pricing fetch at `2026-09-11T23:57:52Z`
(content SHA256 `755aa9b488d1185cba016ca4de3b3b6b8f593f5e13e5f9f961305289a5c8d242`).
The Ark-first attempt failed during TLS before HTTP; the fallback passed the
fresh pricing gate and completed one verified HTTP request, which returned HTTP
`402` (`invalid_request_error`) and produced no eligible model output. The
Turn therefore closed fail-closed without Answer/Citation. This identifies the
current earliest live failure as Provider HTTP/output eligibility, not cognition,
Source, or Web integration; no Provider or Prompt change is authorized by this
evidence.
