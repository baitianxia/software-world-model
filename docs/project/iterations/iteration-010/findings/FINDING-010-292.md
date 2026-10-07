---
id: FINDING-010-292
kind: implementation-finding
status: dispositioned
authority: implementation-evidence
owners: [project, engineering, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-EXECUTION-PLAN-CURRENT, ITER-010-PDR-014]
code: [validation/iteration_010_mvp/direction_check.py]
tests: [tests/test_iteration_010_direction_check.py]
iteration: ITER-010
classification: iteration-design
disposition: iteration-design
target: ITER-010-SLICE-001
---

# FINDING-010-292：唯一执行计划与旧监督阶段收敛

## Observation

当前执行计划已经使用四项用户价值任务，但 PDR、Readiness、Verification、Manifest 和方向检查器仍残留 Phase A/B/C/D 的当前状态语义。
旧方向报告还能把非空 evidence 字段解释为能力具备并推进阶段；这不能证明浏览器体验或答案质量。

## Evidence

- 原方向检查器硬编码旧提交并返回 `next_phase`；当前改为从 `project/current.md` 读取当前任务，不根据证据字段晋级。
- 当前报告明确是静态风险信号，产品进展记为 `NOT_ASSESSED`；提供的 evidence reference 不作真实性背书。
- 旧 `var/direction-phase-c-latest.json` 与当前 HEAD、计划、上下文不匹配，报告校验拒绝把它当作当前证据。
- 本次未修改冻结的架构目录，也未发起外部模型调用。

## Decision / Disposition

以活动 Slice 为唯一主处置：任务顺序只由 `EXECUTION-PLAN-CURRENT.md` 拥有；PDR、Readiness、Verification 的旧阶段限定为历史映射。
Manifest 的旧 action/phase 兼容身份不产生等待授权或晋级语义。监督是否实际运行必须由可观察 heartbeat 证明，不能用文档声明替代。

本次收敛不代表产品闭环已完成：默认无参页面仍是 Access，实际 Agent 会话需要 artifact；世界模型、Agent、源码和浏览器端到端能力仍须按 TASK-1 取得真实证据。

## Verification

- `docs.py check`、`plan-shape-check.py`、`plan_gate.py snapshot`、架构锁和 `git diff --check` 通过。
- 方向检查器定向测试 13/13 通过；相邻 Chat/Artifact/CLI/Browser/WorldModel 测试 54/54 通过。
- 早期复核曾发现 `tests.test_docs_gate` 有 1 项失败、3 项跳过：测试把当前非旧协议
  Manifest 的历史运行字段当作必校验字段。
- 后续修复后，`tests.test_docs_gate` 当前为 92 项通过、3 项跳过。新增的三方执行身份检查同时确认
  PROJECT-CURRENT、执行计划和 Manifest 的计划 ID、当前任务、计划形状、决策引用和迭代身份一致。
  修复方式是将
  `first_live_chat_turn_result` 和 `deterministic_successor_canary_source_file_budget`
  明确作为历史运行字段：当前 `qualified-candidate` 不再把它们当作现行协议字段，旧
  `implemented-*` 状态仍由其专属校验负责；没有恢复旧协议或删除校验器。
- 当前状态已明确标为 `PRE_DEVELOPMENT_REPAIR`；Codex heartbeat `iter-010` 已创建但按用户停止要求暂停，
  当前仍为 `SUPERVISION_UNVERIFIED`，不启动产品开发。
