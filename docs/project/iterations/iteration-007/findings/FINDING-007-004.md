---
id: FINDING-007-004
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [quality]
depends_on: [ITER-007-VERIFICATION, FINDING-007-003]
code: [validation/structure_world_model_iteration_007/capability/evaluator.py]
tests: [tests/test_iteration_007_capability_qualification.py]
iteration: ITER-007
classification: verification
disposition: match-ordered-concepts-by-monotonic-occurrence
target: ITER-007-VERIFICATION
---

# FINDING-007-004：首个别名出现位置会误判正确的动作顺序

## Observation

run-001 的 Draft direction Case 回答“保存前先调用 validate……随后调用 persist……最后返回”。动作顺序与 sealed typed
Result 完全一致，但独立 evaluator 把句首用于问题 framing 的“保存”当成 persist 动作，只比较每组别名第一次出现的位置，错误
产生 `SOURCE_ORDER_CHANGED`。

## Evidence

- `WM-JSS-CE-DRAFT-DIRECTION-008` 的 authoritative atoms 是 validate → persist → return；模型正文也按该顺序；
- 旧 evaluator 对 persist 概念组取全文最早的“保存”，其位置早于 validate，因而产生 false positive；
- 同一算法无法区分“某别名在 framing 中先出现”与“动作真的逆序”。

## Impact and classification

这是独立资格判定器的 false-negative，会使正确产品输出无法获得资格，分类为 `verification`。它不改变 Query Result、产品语义或
Case 期望顺序。

## Decision and disposition

按概念组顺序做单调 occurrence 匹配：每一组选择位于前一已匹配概念之后的最早别名。这样句首 framing 别名不会抢占后续真实
动作；真实 persist → validate → return 逆序仍因找不到单调序列而失败。禁止删除 `SOURCE_ORDER_CHANGED` Gate 或改成无序包含检查。

## Verification after disposition

- 新回归覆盖句首“保存前”且 validate → persist → return 的正确答案并要求 PASS；
- 原逆序答案“先返回，再保存，最后校验”继续 FAIL；
- 全 12 个合成期望输出仍由独立 stdlib evaluator 判定 PASS。
