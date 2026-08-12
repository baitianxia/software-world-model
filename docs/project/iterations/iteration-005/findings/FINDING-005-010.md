---
id: FINDING-005-010
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-005-SLICE-002, ITER-005-VERIFICATION]
code: [validation/structure_world_model_iteration_005/slice2_comparison.py, validation/structure_world_model_iteration_005/slice2_freeze.py, validation/structure_world_model_iteration_005/slice2_evaluator.py]
tests: [tests/test_iteration_005_slice2_comparison.py, tests/test_iteration_005_slice2_evaluator.py]
iteration: ITER-005
classification: verification
disposition: seal-controlled-direct-response-envelope
target: ITER-005-VERIFICATION
---

# FINDING-005-010：controlled Direct 的响应信封不足以承载已密封复杂问题

## Observation

`run-005` 和 `run-006` 均在相同的 complex exact-diff case 上得到 1000 output token、`finish_reason=length` 的
controlled Direct terminal。`run-006` 还出现一个内容完整但因 answer 内未转义 ASCII 双引号而无法解析的 JSON terminal，
以及一个独立的 `PROVIDER_OUTCOME_UNKNOWN` terminal。comparison controller 按协议保留全部失败，independent evaluator 因
四题缺少两条 eligible baseline 而返回 `FAIL`。

## Evidence

- `run-005` `WM-005-005` terminal `sha256:e717948f9c5b63ebb4fabf290eb4e4dfcd127b6aa0babc734db770caa52f0197`：
  `output_tokens=1000`、`STRUCTURED_OUTPUT_INVALID`；
- `run-006` `WM-005-005/006` 的 Gateway outputs 均为 `output_tokens=1000`、`termination_reason=length`，文本在 JSON
  字符串结束前截断；
- `run-006` `WM-005-001` 为 `termination_reason=stop`、`output_tokens=852`，但 answer 正文中的 ASCII 双引号未转义，
  JSON decoder 在字符 1311 失败；
- `run-006` `WM-005-004` 在一次 dispatch 后进入 `OUTCOME_UNKNOWN`，没有响应或 usage；该项不是 token/serialization
  缺陷，必须继续作为单次无重试 surface failure 保留；
- `run-006` comparison report
  `sha256:278c7c3c52141314318071b9e275864bb5907bada3d8c5fe12f34f837b040ea1` 精确列出四个 baseline eligibility
  blocker；World Model 九题均成功且独立评分完整。

## Impact and classification

1000-token 上限已被两个独立随机 run 的复杂题击穿，而 prompt 没有显式要求 JSON-only 与双引号转义。它让 V-009 衡量的
不只是回答质量，还混入了本可预防的 baseline 输出封装失败，属于本轮 comparison 的 `verification` 缺陷，不改变 Product、
Gateway 或 System contract。Provider outcome unknown 是 no-retry 协议下的真实外部失败，不属于本 Finding 的修复范围。

## Decision and disposition

- controlled Direct 的 prompt/schema ref 升为 `@2`；明确只返回 `{\"answer\":\"...\"}`、无 fence/尾随文本，并转义
  answer 内部双引号；
- 每题最大输出预算由 1000 提高到 4096；问题、POM closure、Provider、单次 external task、exact 1 Provider call、0 retry、
  baseline-first 和 evaluator 均保持不变；
- held-out suite 的 `CONTROLLED_DIRECT` protocol 显式密封 `max_output_tokens_per_case=4096` 与 response contract，
  evaluator 和 runner 在漂移时失败关闭；
- 新增测试证明实际 execution context 使用该预算和 prompt，并证明 evaluator 拒绝 protocol budget drift；
- 不重试、不覆写 `run-005/run-006`；代码变化后生成全新随机 suite，再按新 suite 单独授权和执行。

主要处置进入 `ITER-005-VERIFICATION`；代码与测试实现该已密封的验证协议，不建立跨 Iteration 的 System 质量规则。
`run-007` 已把新 response envelope 密封进 suite `sha256:04f50cae8392296d8173921e56063abded7d66c33c17d97019d50ac965b9f884`，
并通过 51 focused、13 staged Answer、801 full regression 与未授权短路；live dispatch 仍等待该 suite 的独立用户授权。
