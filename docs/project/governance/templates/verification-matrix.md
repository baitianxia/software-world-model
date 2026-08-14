---
id: ITER-NNN-VERIFICATION
kind: iteration-verification
status: not-run
authority: planned-verification
owners: [quality]
depends_on: [ITER-NNN-PROPOSAL]
code: []
tests: []
iteration: ITER-NNN
product_goal_gate: V-000
product_goal_outcome: user-visible-general-source-qa-delta
product_goal_evaluation: independent-hidden-plus-live-ad-hoc
product_goal_result_id: pending
---

# Iteration NNN Verification Matrix

| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |
|---|---|---|---|---|---|---|
| V-000 | 本轮相对 baseline 可测缩短通用源码问答 MVP 差距，并与既有能力完成跨域组合 | product / comparison | 未参与实现的真实工程；独立评测方/用户持有且实现阶段不可见的 held-out 自由问题；验收现场临时问题；旧+新知识跨域问题；成熟源码 Agent protocol；预提交差异化价值阈值 | 支持率提高；重大错误为 0；逐题完整性不退步；差异化价值阈值 PASS；提问时 Source/Update/Direct fallback=0；同一正式 Web 可人工验证 | pending | not-run / blocking |
| V-XD-001 | `<prior-acceptance-id>` 与 `<current-slice-id>` 在同一问题中组合 | product / integration | <hidden-cross-domain-case> | <evidence-bound-answer-or-honest-gap> | pending | not-run / blocking |
| V-WEB-001 | `<current-slice-id>` 通过正式 Web 执行 `V-XD-001` | product / browser | <exact-web-subject> | <manual-user-visible-result> | pending | not-run / blocking |
| V-ADHOC-001 | `<current-slice-id>` 通过正式 Web 接受现场临时问题并覆盖 `V-XD-001` | product / browser | <user-owned-live-question-protocol> | <manual-user-visible-result> | pending | not-run / blocking |
| V-REFLECT-001 | `<current-slice-id>` 根据产品证据复盘关键方案假设并作出继续或停止决定 | architecture / reflection | <exact-slice-result-assumptions-findings-and-baseline-comparison> | <complete-review-and-explicit-decision> | pending | not-run / blocking |
| V-001 | <claim> | unit / contract / CC / CE / product / activation | <exact identity> | <result> | pending | not-run / blocking |

V-000 不能由新增 Profile/View 的封闭题集、测试数量或旧能力回归替代。测试、CC、CE、Product Validation 与 Activation 不得
互相替代。每项 Result 必须绑定 exact subject、运行身份、限制和有效期。完成时每个 Manifest 绑定的 `V-XD`、`V-WEB`、
`V-CANARY`、`V-ADHOC`、`V-REFLECT` 行都必须为 `PASS / blocking`，Evidence 必须精确填写
`<拥有该 Case 的 Slice Result ID>#<case-id>`；最终 Product Result 依赖并聚合全部唯一 Slice Result。只让 V-000 或汇总计数
PASS 不算完成。`V-REFLECT PASS` 只表示复盘完整，不表示方案通过；继续或接受必须由 Result 的独立 decision 字段表达。
