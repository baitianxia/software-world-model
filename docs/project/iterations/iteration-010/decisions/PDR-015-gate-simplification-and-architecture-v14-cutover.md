---
id: ITER-010-PDR-015
kind: project-decision
status: accepted
authority: project-decision
owners: [project, architecture, engineering, quality]
depends_on: [ITER-010-PDR-014, FINDING-010-298, SYS-ADR-021, PROJECT-GOVERNANCE-PLAN-EXECUTION]
code: [scripts/docs.py, scripts/plan_gate.py]
tests: [tests/test_docs_gate.py, tests/test_plan_gate.py]
iteration: ITER-010
decision: GOVERNANCE
decision_ref: local-user-direction-2026-10-14-gate-simplification
effective_scope: ITER-010-SLICE-001
coding_input: false
---

# PDR-015：门禁瘦身与架构 V1.4 治理切换

## Decision

用户于 2026-10-13/14 明确同意：(1) 按 FINDING-010-298 / SYS-ADR-021 修订架构基线至 V1.4 及相关系统文档；(2) 修订开发治理规则；
(3) 把检查脚本瘦身为通用检查。本决定是这些变更的治理动作，不改变产品目标、standing authority 或当前产品任务。

## 门禁变更

- `scripts/docs.py` 从约 1.68 万行收敛为约 1 千行，只保留：front matter、ID、依赖解析与循环、系统/项目分离、链接、Finding、迭代验收、
  `PROJECT-CURRENT` 一致性和生成索引。ITER-010 专用的动作规格、阶段转移、Provider 路线、Result/证据状态机与 Manifest 字段校验全部移除。
- `scripts/plan_gate.py` 从约 3.8 千行收敛为约 500 行，只执行 `plan-execution-enforcement` 的最小机械边界：基础动作的路径允许/禁止、
  门禁文件只能在 governance 动作下修改、目标 Manifest 结构有效、不新增明显密钥。不再要求 Result 封存、runner 身份重放或计划修订谱系。
- 对应测试 `tests/test_docs_gate.py`、`tests/test_plan_gate.py` 重写为覆盖上述通用规则。
- 旧实现完整保存在 Git 历史（`codex/development` 的 `dfdcf6d` 及之前）中，不再作为当前门禁。

## 一次性切换

旧 `plan_gate.py` 要求修订计划的基础动作必须是已封存 PASS Result 的 governance 动作；当前基础动作是尚无 Result 的产品动作，因此
在旧门禁下不存在合法的切换路径。本次切换提交需要用户一次性绕过本地 pre-commit（例如 `git commit --no-verify`），并在同一提交中
安装新门禁。之后的提交由新门禁按本决定校验：本切换提交把 `current_action` 设为 governance 动作；下一次提交把它恢复为
`next_action_contracts.browser_chat_mvp_build` 中的产品动作。架构冻结锁需要用户另行确认重新冻结。

## Consequences

- 治理和系统文档变更必须在 governance 动作下进行；产品动作仍不得修改系统或架构文档。
- 门禁不再承载迭代状态；时间盒、同签名停止和无进展上限由执行计划和用户检查点执行。
