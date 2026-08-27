---
id: PDR-NNN
kind: project-decision
status: proposed
authority: project-decision
owners: [project]
depends_on: []
code: []
tests: []
iteration: ITER-NNN
decision: <REWORK-REDIRECT-REJECT-or-administrative-decision>
decision_ref: <codex-user-message-sha256-receipt>
coding_input: false
---

# PDR-NNN：<Decision>

## Context and evidence

## Options

## Decision

决定必须区分 `REWORK`（同一总体架构内修复后重试）与 `REDIRECT`（更换总体路线）。问题报告、回答错误或复核要求本身不得作为
`REDIRECT` 依据；转向必须绑定明确用户转向、核心架构证伪或预提交无进展上限已达到。

## Scope and consequences

若本决定改变 `DEVELOPMENT_PLAN_EXECUTION_CONTROL@1` 的动作、顺序、权限、路径、锁或 transition，必须依赖至少一个 exact Finding，
并在 `decision_ref` 绑定 exact 用户授权。新计划先由独立 governance action 取得已密封、digest-bound 的 base PASS Result，再在后续
独立提交中修订；不得在同一 candidate 中同时补 Result/JSON 收据、修改 verifier、放宽计划或迁移动作，候选 Manifest 不能授权自己的 diff。

## Revisit condition
