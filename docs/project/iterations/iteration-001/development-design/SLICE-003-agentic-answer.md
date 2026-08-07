---
id: ITER-001-SLICE-003
kind: development-slice
status: completed
authority: historical-development
owners: [application, interface]
depends_on: [ITER-001-SLICE-002, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL]
code: [src/software_world_model/application_services, src/software_world_model/interface/agentic_runtime.py]
tests: [tests/test_knowledge_use.py, tests/test_natural_task.py, tests/test_agentic_runtime.py, tests/test_response_control.py]
iteration: ITER-001
migration: reconstructed-from-existing-iteration-records
---

# SLICE-003：Agentic 回答闭环

## Outcome

自然语言任务被冻结为 Requirement/Need，经固定 Snapshot Read Session 判断充分性；缺口触发受控更新并在新 Snapshot 全量重评，最终答案由独立 Review 复核后幂等交付。

## Required system semantics

- Agent 只经 Application Services，不接触 Core、Store 或 Source Tool；
- Requirement 不得弱化，每个 Need/Joint 都有 Proof 或 Gap；
- Answer 阶段关闭 Source/Artifact/Evidence Quote 和模型历史旁路；
- Answer Candidate、Review、Authorization 与 Delivery 分离；
- Task Revision、Use Epoch 和资格漂移使旧授权失效。

## Affected implementation

Natural Task、Task Control、Knowledge Use、Response Control、Agentic Runtime 与 HTTP/browser presenter；管理 CLI 只覆盖底层管理和知识查询用例。

## Non-goals

通用自治 DAG、无限 Agent Loop、答案文本补齐 Gap、Orchestrator 拥有最终放行。

## 阅读与回写

当前语义见 [Knowledge Use](../../../../system/contracts/application/knowledge-use.md)、[Agentic Task](../../../../system/contracts/application/agentic-task.md)和[Response Control](../../../../system/contracts/application/response-control.md)；实现发现进入本轮 [Findings](../findings/README.md)。

## Acceptance

逐 Need 完整性、分页/权限不形成错误否定、更新后全量重评、取消恢复、重复交付、stale candidate、未蕴含 Claim 和失败响应审核均有正反例。
