---
id: FINDING-010-281
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, quality]
depends_on: [FINDING-010-280]
code: [src/software_world_model/application_services/lightweight_engineering_agent.py]
tests: [tests/test_lightweight_engineering_agent.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: project-existing-executable-action-subset
target: src/software_world_model/application_services/lightweight_engineering_agent.py
---

# FINDING-010-281：run-229 的失败证据与拒绝 READ 记账

## Observation

在产品 `4f8baafe5e30513d782b5f6aa969139613ad83fe`、Source exact revision
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` 上，run-229 串行完成三个独立问题并正常关闭 listener。角色分配问题和库存问题均进入
fresh Reviewer 并获得 `APPROVED`；用户注册问题第一次和第二次 Reviewer 均为 `REWRITE`，随后触发既有一次完整 rewrite 上限并
fail-closed。Reviewer 的 APPROVED 不代替独立技术质量验证：角色分配答案实际讨论角色菜单/资源分配而非用户角色重分配，库存答案未读实现、
主要交付 Unknown。因此不能把这两次 APPROVED 称为两个问题已正确解决。

## Evidence and disposition

注册轨迹的第二次 Agent 输入保留了 7 条 Reviewer finding 和未读 Source candidates；没有反馈丢失的证据。第一次答案在证据不足时提前
FINISH，Reviewer 返回 `REWRITE`；同一 Agent 修订后仍被要求 REWRITE，应用层按既有一次整体 rewrite 契约失败关闭。这个 terminal code
本身不是需要放宽 rewrite 预算的实现缺陷。部分 Reviewer 意见涉及缺证据，但不能通过解析其正文改写 verdict。

库存问题的另一项更早机械偏差可以复现：DeepSeek input manifest 第 7 步的 observation 6 明确为
`ENGINEERING_AGENT_SOURCE_BOUNDARY@1 / REJECTED / SOURCE_FILE_FUSE_EXHAUSTED`，对应
`broker_decision_47ed1c4ca739e6b1c1e8c33f4f7b15cb`。`TOOL_OBSERVATION` 事件名不证明 Worker 执行；Broker 在 compile 阶段即拒绝该 READ。
但轻量 Agent 只对 SEARCH 检查当前 typed Broker rejection，READ 仍被算为已执行、无进展的工具操作。

局部修复复用现有受信 ledger 校验：SEARCH/READ 均仅在全部结果的当前 Broker decision（subject ref 与 evidence digest 精确匹配）为
REJECTED 时不扣工具和无进展 fuse。已授权的空结果仍扣预算；没有匹配证据不能获得该豁免；混合结果保守地视为执行过。
Broker 的 Source 文件、字节、操作 fuse 和禁止重复 dispatch 规则不变，尤其不能恢复 run-229 已耗尽的 Source 文件预算。
此修复只更正应用层实际执行记账，不增加接口或改变 Source/Review 的跨模块语义。更早的多次搜索耗尽文件预算以及语义规划缺口仍未闭合。

## Verification

run-229 的 terminal receipt 为 `STOPPED_AFTER_DISPATCH`，3 Conversation / 3 Turn，DeepSeek HTTP dispatch 30 次，Ark HTTP dispatch 0 次
（3 次 pre-dispatch TLS 失败），两路 post-dispatch unknown 均为 0。该运行绑定旧候选 `4f8baaf`，不是新修复的运行证据。

`test_read_broker_rejection_is_not_an_executed_no_progress_read` 在修复前失败（剩余工具预算 0，期望 1），修复后通过；同一测试的已授权空
READ 分支仍消耗预算。整个轻量 Agent 定向集为 28 项通过。原问题与两个异质问题仍须在 clean 新候选上复验；不宣布 C1、C2 或 Alpha 完成。

## Follow-up run-232

修复提交 `dce438f`（拒绝 READ 记账）及 `1ebd53c`（重复提案不充满 Tool fuse）后的 clean candidate `1ebd53c90c94c76cc75128846bbbb328cc0c0fef`
在 run-232 重新执行三题。原题 q1 在两次重复 `SEARCH_SOURCE` 被拒后继续读取 5 个候选，最后因真实 `MORE_EVIDENCE` 而在工具熔断处
失败；这证明重复提案没有再伪造预算耗尽，但也暴露 Source candidate 排序/证据规划仍使预算被低价值读取消耗。q2 用户注册仍在两次
`REWRITE` 后按既有上限关闭，q3 库存进入 `APPROVED`。该结果支持继续修复 Agent evidence planning，不支持放宽预算、rewrite 上限或
Provider/Prompt/Schema。

## Candidate projection follow-up

离线审计显示 `role` 查询前 12 项可被 TYPE 实体填满，而同一 snapshot 中存在带有该 token 的方法实体（例如
`getRoleList`）及完整 relation/provenance。仅改变全局 TYPE/METHOD 优先级会破坏复合标识符查询的既有声明锚点，因此候选修复只在宽首屏
全为 TYPE 且存在同 token METHOD 时，将一个方法保留在该首屏末位；查询词、路径、项目和问题均未进入实现。交换实现同时保存候选索引，避免
Python 左值求值导致“交换”实际无变化。`tests/test_capability_cognition.py::test_broad_type_page_keeps_matching_method_visible` 与轻量 Agent 定向集通过。
该修复仍需在原始 `MORE_EVIDENCE` 轨迹和两个异质任务上取得 fresh 运行证据，不能据此宣布 C1 或 Alpha。
