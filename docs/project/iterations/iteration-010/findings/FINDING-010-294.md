---
id: FINDING-010-294
kind: implementation-finding
status: dispositioned
authority: implementation-evidence
owners: [project, engineering, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-EXECUTION-PLAN-CURRENT, ITER-010-PDR-014]
code: [src/software_world_model/ai_infrastructure/lightweight_engineering_model.py]
tests: [tests/test_lightweight_engineering_model.py]
iteration: ITER-010
classification: local-implementation
disposition: code-and-tests
target: src/software_world_model/ai_infrastructure/lightweight_engineering_model.py
---

# FINDING-010-294：Agent 提示词把证据路径错误固定为世界模型优先

## Observation

当前执行计划要求 Agent 根据问题和已有观察，在世界模型与精确版本源码之间自主选择并往返；但实际轻量 Agent 的步骤提示词曾要求在组合模式下先执行 `SEARCH_COGNITION`，再进入源码。这会把架构和任务计划规定的自主调查退化为固定流水线，无法让简单的源码定位问题直接从源码开始，也会把后续偏差错误归因到知识或排序。

## Evidence

- 修复前的 `_STEP_PROMPT` 明文包含 `start with SEARCH_COGNITION`。
- 该提示词由当前 `ModelBackedLightweightEngineeringAgent` 直接发送给首选 Provider；它不是历史记录，也不是仅测试用语。
- `EXECUTION-PLAN-CURRENT.md` 的 TASK-1 明确禁止把“先世界模型、后源码”实现成固定顺序。

## Decision / Disposition

这是通用 Agent 行为偏差，不按工程、问题或关键词增加特判。步骤提示词改为：每次依据用户问题和已有观察选择动作；世界模型用于结构、关系、行为、覆盖和未知问题；源码用于精确实现证据；两条路径可因观察到的缺口相互往返。保留现有动作、工具权限、证据和审核边界，不修改架构文档或答案协议。

## Verification

- `tests.test_lightweight_engineering_model` 与 `tests.test_lightweight_engineering_agent`：39/39 PASS。
- 定向断言确认提示词不再包含固定首步要求，并明确允许按观察在 Cognition 与 Source 之间移动。
- 该修复只证明当前 Agent 提示词不再强制顺序；它不证明默认浏览器入口已经接入该 Agent，也不关闭 FINDING-010-293。
