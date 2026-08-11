---
id: FINDING-004-001
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-004-SLICE-001, ITER-004-VERIFICATION]
code: [validation/structure_world_model_iteration_004/interactive_browser.py]
tests: [tests/test_iteration_004_interactive_browser.py]
iteration: ITER-004
classification: local-implementation
disposition: validate-the-published-evaluation-only-environment
target: validation/structure_world_model_iteration_004/interactive_browser.py
---

# FINDING-004-001：Citation 校验使用了错误的环境枚举

## Observation

第一次真实 Citation GET 已产生合法、密封且无网络的 Projection，但交互 runner 把环境预期写成
`EVALUATOR_ONLY`；accepted Projector 实际发布的是 `EVALUATION_ONLY`，因此正确 Projection 被本机入口拒绝。

## Evidence

- accepted Citation Projection 的 `schema`、`status`、result/seal binding、network count 与 answer return port 均正确；
- 失败只发生在 launcher 的环境字符串比较，不涉及 accepted Answer/Gateway/Projector package；
- 修正后的当前 session 对两个 Result 的 Projection digest
  `sha256:45024d95c0ff3b1d5b48cf7d46afc7715e8bf897d98b6ffa4f67ebb3c112cbff` 与
  `sha256:5eeb8c799c89cb4181e3cd67def001b1413d39819df4dd096d78aaec9a055826` 独立 GET 均通过。

## Impact and classification

这是 launcher 本地验证条件的实现错误，不改变 Citation Contract、accepted product 或跨模块枚举，分类为
`local-implementation`。

## Decision and disposition

校验 exact `EVALUATION_ONLY`，保留其他 request/result/seal/digest、零网络和无 answer return port 条件。增加成功验签、
wrong request/result 与 projection tamper 的回归测试，不放宽任何 Citation 能力边界。

## Verification after disposition

交互 runner 与 HTTP adapter 聚焦测试 11/11 PASS；真实浏览器打开独立 Citation 对话框成功，console 无 error。
Production Activation 未执行。
