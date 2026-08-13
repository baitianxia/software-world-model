---
id: ITER-006-RESULT-LIVE-RUN-007
kind: iteration-result
status: failed
authority: execution-evidence
owners: [engineering, quality, security]
depends_on: [ITER-006-RESULT-PRODUCT-CANDIDATE-FREEZE-RUN-007, ITER-006-RESULT-JAVA-CAPABILITY-RUN-002, FINDING-006-012]
code: [validation/structure_world_model_iteration_006/live_comparison.py, validation/structure_world_model_iteration_006/live_evaluator.py, src/software_world_model/interface/world_model_runtime.py, src/software_world_model/interface/world_model_runtime_assets/gateway_authorized_workload.py]
tests: [tests/test_iteration_006_live_evaluator.py, tests/test_world_model_gateway_authorization.py]
iteration: ITER-006
---

# ITER-006 Live run-007 Result

## Decision

`run-007` 已按用户 exact 授权完整执行，结果为 **FAIL**。controlled Direct 与 Mature Source Agent 各 6/6 terminal SUCCESS；
World Model 六题均完成一次 Ark model call，但外层 exact postcondition 全部在 `ROLE_POSTCONDITION` 拒绝，因此公开 terminal 为
6/6 FAILURE。冻结 evaluator 正常生成 FAIL report，没有筛除失败或插值。

根因不是 capability qualification、Provider、网络或模型输出失败，而是授权 Gateway wrapper 的摘要键冲突：Java qualified
baseline 新增自己的 `document_digest`；wrapper 将其放入外层摘要输入后，又用外层同名 `document_digest` 覆盖。外层 verifier
从可见文档移除最终 digest 后无法重建被覆盖的 baseline digest，按设计失败关闭。详见 `FINDING-006-012`。

本次每题每路一次，controller/selective retry 均为 0。授权已消费，不得用于验证修复。V-008 仍 FAIL、V-009 仍 PARTIAL，
Slice/Iteration 没有被接受。

## Exact authorization and seals

- 用户授权引用：
  `codex-user-message:sha256:38431ec0df7e4bde600b7a5239992755a2cb1579907c0e551908cd1d78060e77`；
- authorization time：`2026-08-12T15:33:43+08:00`；
- comparison authorization：
  `sha256:18c7ad7b69d19f753005e4a30a523d57bd2a88e4376a304143b6ae6738f9a1ab`；
- disclosure authorization：
  `sha256:f6be8bcfd13b8b8472a6f5af8bccb6b37c865824f3c55139e3ffd2ba4bfea5e3`；
- evaluation grant：
  `sha256:0275a01617e39cbfd65759c30d2b31b0bf247ce95a957d63e1cdc4f32f328998`；
- baseline seal：
  `sha256:011d205ae7f160ae69425cabba37d2e8cdf0e2e59a474abec8e89fe03589c079`，且
  `world_model_result_count_at_seal=0`；
- startup receipt：
  `sha256:e6949fd3d13d9594d4ff500d11e4d75d71f15018e1b31b4cacc175f11c7908a4`。

授权、grant、baseline seal 与 startup receipt 的 raw SHA-256 分别为 `21802ef8…`、`3863308a…`、`1bd24825…`、
`acd1b1e9…`。这些机器证据只保存在本机 `var/iteration-006/live/run-007-live-explicit/`。

## Three populations

| Surface | Terminal | External task / Provider call | Population digest |
|---|---:|---:|---|
| controlled Direct / Ark | 6 SUCCESS | 6 task / 6 observable calls | `sha256:cd4e431c9019970468c35c942df86e7e6bb78c94c53e2cfc70cffc1c425064ac` |
| Mature Source Agent / Codex | 6 SUCCESS | 6 task / CLI provider calls unobservable | `sha256:9328316f7884b1a61246d16e886d224fc195848778adb686a7181e3ad33c48bf` |
| World Model / Ark | 6 FAILURE | 6 task / 6 completed internal calls | `sha256:b138b568a5f27f99020f7a29c4e30d7d881d27cb9d33699f2d1df6e4d014654e` |

World Model 的六份内部 Answer summary 均为 PASS：Provider/network count 各 1，六个 model call ID 与 Provider request digest 均
唯一；能力集合覆盖两个 generic planning 及另外四种 required capability。合计 source、Evidence payload、product suite、product
Oracle access 均为 0。六份 Gateway summary 均记录资格 proof `sha256:65d18436…`、一次 HTTPS dispatch、一次 RESULT、无 DNS、
credential value 未落盘。外层 terminal 各只有一个 attempt，failure stage 全为 `ROLE_POSTCONDITION`，无 Citation projection。

因为 HTTP verified terminal 没有返回 `provider_call_count=1`，冻结 comparison population 必须记为 unknown/null；evaluator 因此同时
产生“call count is not exactly one”和“terminal failed”两个 blocker/题。内部 completed call evidence不能追溯改写冻结 population。

## Comparison report and root cause

comparison report 为 `FAIL`，digest
`sha256:5a76882fef9a6694d03e4486ee3c413b8f546600ee0a4633d1a46ec32d077377`；raw SHA-256 为 `73533725…`。
`failures_filtered=false`、`missing_outputs_interpolated=false`、Production Activation `NOT_EXECUTED`。

Java qualified baseline summary 带有自身 digest；wrapper 生成的可见外层 summary digest 为 `sha256:d75f5864…`，但按外层 schema
从可见 core 重建得到 `sha256:fad9bc5e…`。旧 Maven baseline 没有 `document_digest` 字段，因此既有 legacy 测试和 run-003 未覆盖
这个 Java-only 冲突。最小本地修复排除 baseline 的同名 digest，并新增 Java baseline 回归；15/15 Gateway focused tests PASS。

服务已停止，loopback listener 与 Gateway socket 均不存在。Production Activation、Git stage/commit/push 均未执行。
