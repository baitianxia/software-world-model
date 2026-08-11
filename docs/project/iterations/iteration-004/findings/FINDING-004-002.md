---
id: FINDING-004-002
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, product, quality]
depends_on: [ITER-004-SLICE-001, ITER-004-VERIFICATION]
code: [validation/structure_world_model_iteration_004/interactive_browser.py, src/software_world_model/interface/world_model_browser_ui.py]
tests: [tests/test_world_model_browser.py, tests/test_iteration_004_interactive_browser.py]
iteration: ITER-004
classification: verification
disposition: retain-pre-dispatch-failure-and-accept-only-visible-fail-closed-behavior
target: ITER-004-VERIFICATION
---

# FINDING-004-002：一个新 fixture 自由问题没有形成 Answer Result

## Observation

真实浏览器对 `EXACT_FIXTURE_VALID` 提交一个新的自由问题时，accepted Answer workload 在 `ANSWER` 阶段以
`DomainError` 失败；Gateway 没有 dispatch Provider，页面正确显示失败关闭。随后在同一 service session 选择
`EXACT_B` 提交另一个新问题成功。

## Evidence

- session root：`var/iteration-004/interactive/20260811T082338Z-6d81d16b6104/`；
- failure receipt：`requests/failure-000003.json`，request-id digest
  `sha256:ba17cf7a813e6131029c1ecd65a1e315aa3bdf087a02d171c496246ac9ad2115`；
- terminal digest：`sha256:5995e4b1a0b316b0c60a2b33700cb0694e6a6a232974fcd1ddd1a996e897b57b`，
  `failure_stage=ANSWER`、attempt=1、retry=0；
- Gateway summary `provider_call_count=0`，Answer role audit PASS、Source/Evidence/越界操作均为 0；
- 浏览器没有暴露内部异常、没有 Direct fallback，并保持发送按钮与错误状态一致。

## Impact and classification

本轮承诺自由文本能够提交，并承诺成功 Result 或明确失败关闭；它没有证明 accepted Maven Structure product 对任意新文本
都必然生成答案。修改 accepted Answer package 会使 ITER-003 资格失效，超出本轮 launcher 授权。因此分类为
`verification`，作为产品可靠性限制和负向 UI 验收保留，不能把该 terminal 改写成成功。

## Decision and disposition

保留原始 failure receipt/terminal；V-006 同时核对 loading、成功 Result、Knowledge Gap 与失败关闭。ITER-004 只接受
本机交互接线和诚实边界，不扩张为“任意问题必答”。后续若要提高 fixture 问题成功率，必须以新的 product iteration
重新取得 Capability/Product qualification，而不是在 launcher 中重试、改写问题或调用 Direct。

## Verification after disposition

同一 session 的 supported、Knowledge Gap 与真实浏览器问题分别以一次 Provider call、零 retry 成功；完整回归
761/761 PASS。Production Activation 未执行。
