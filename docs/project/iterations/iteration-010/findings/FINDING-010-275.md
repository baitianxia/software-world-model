---
id: FINDING-010-275
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, quality, security]
depends_on: [FINDING-010-273, FINDING-010-274, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/lightweight_engineering_agent.py]
tests: [tests/test_lightweight_engineering_agent.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: bounded-agent-replan-for-invalid-finish-citation-selection
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-275：FINISH 的非法 Citation 选择需要一次受控主 Agent 重规划

## Observation

`run-145-phase-c-loopback` 的 q4 已完成 cognition 查询和多次受控 Source READ。Primary 在 `FINISH` 同时选择了五个真实
`SOURCE_READ` Observation 与一个没有 Citation 的 `SEARCH_COGNITION` Observation。Application 的 `_resolve_citations` 正确拒绝该选择并以
`CONTROL_STATE_DENIED` fail-closed，但在拒绝前没有让同一个主 Agent 根据当前 Observation domain 修正其 ordinal selection，因此 fresh
Reviewer 没有被调用。相同的 citationless cognition selection 已在此前多个 run 重现；这不是 cognition construction、Source Broker/Worker、
Provider 或 Reviewer 的最早偏差。

## Evidence

- `run-145-phase-c-loopback/ark-gateway.sqlite3` 的 q4 call #18 是合法 typed `FINISH`，选择包含 `obs1/1`；`obs1` 是
  `SEARCH_COGNITION` 且 `citations=[]`。同一 Turn 在拒绝后没有 `INDEPENDENT_REVIEWER` dispatch。
- `_resolve_citations` 继续保留原有 fail-closed authority；新增 executor-level fixture 覆盖 cognition + 多个有效 Source READ 夹一个
  citationless selection、Source-only 越界 selection，以及第二次仍非法的 selection。
- 定向 `tests.test_lightweight_engineering_agent` 为 `7/7 PASS`；`tests.test_conversational_engineering_tools`、
  `tests.test_lightweight_engineering_model` 与 `tests.test_iteration_010_direction_check` 合计 `28/28 PASS`。

## Disposition

在现有 capability-oriented lightweight Agent loop 中，typed decision 已通过既有 decoder 后，Application 对非法 observation/Citation
ordinal 生成私有机械拒绝记录，保留完整原 selection（含 offending pair），不进入 Reviewer、不交付、不静默过滤或替换 Citation；向同一
Primary 复用既有 `rejected_answer` / `review_findings` 输入字段反馈当前 binding domain，并允许至多一次正常 replan/FINISH。第二次仍非法继续
抛出 `CONTROL_STATE_DENIED`。该修复不增加版本化 Agent 协议、Prompt、Schema、Provider、Reviewer 或题目规则，也不改变 cognition provenance
或 Citation authority；只有 Worker 实际 Source Observation 仍能形成可交付 Citation。

Owner `SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 已补充上述 lightweight executor 边界，并明确该一次性 replan 不削弱 decoder 和
最终 fail-closed 约束。真实 loopback successor 仍需验证 q4 能进入 fresh Reviewer，并与 q1/q2/q3/q5 一起形成完整 Phase C 证据。
