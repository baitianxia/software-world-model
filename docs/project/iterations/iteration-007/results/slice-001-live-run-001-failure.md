---
id: ITER-007-RESULT-SLICE-001-LIVE-RUN-001-FAILURE
kind: iteration-result
status: failed-preserved
authority: execution-evidence
owners: [engineering, quality, security, product]
depends_on: [ITER-007-RESULT-SLICE-001-PRODUCT-CANDIDATE-FREEZE-RUN-001, FINDING-007-006]
code: [src/software_world_model/interface/__init__.py, src/software_world_model/interface/world_model_runtime.py, src/software_world_model/interface/world_model_runtime_assets/java_source_semantics_answer_workload.py]
tests: [tests/test_iteration_007_slice1_freeze.py, tests/test_world_model_evaluation_grant.py]
iteration: ITER-007
---

# ITER-007 SLICE-001 Live run-001 Failure

## Decision

首次正式 Web 现场运行 **FAIL**。页面和 health 正常启动，但用户对“登录流程是怎样的？”先后发起四个独立 POST；每个请求只执行
一次 controller attempt、无 retry，并在 `ANSWER` 阶段因 `ModuleNotFoundError` 失败关闭。没有 Answer、Citation 或可判定产品
结果；`V-WEB-001`、`V-XD-001` 和用户正确性 verdict 均未通过。

## Exact evidence

- product freeze report digest：
  `sha256:1f3f79084ccc2feeaf6fb03c7d807c153e11d62f8316ff8945e477d0c7027bfc`；
- live grant digest：
  `sha256:764c93cdbfa5806c7420c19cae89b360a5273d9f1b3727915c3d2a3a334d152e`；
- startup receipt status `ready`，dispatch policy
  `THREE_ORDERED_CALLS_PER_QUESTION_NO_HIDDEN_RETRY`，evaluation subject commit/tree
  `c01d9e3478ba581988db15bacc3a4534ba7818b7` / `e496dd7e918324efadcfbe222e4ceb0ba965a0a5`；
- request terminal digests：
  `sha256:3461b4f8f013147bdbfd3101560a82f90d0da63ed7ad38e3d063da7b9b8254c9`、
  `sha256:be3fdc6b203f669027194554c83d69d7ddbf900289aa221855b032acbf9742ec`、
  `sha256:891ca9781eb8b0cf6fa022e2e10c0e7d81eea7ed993b9490acddd446795aeaf0`、
  `sha256:578306707e29d2cd0c209e52cf3ae22de2283965fc158c5b13471368a7d6e9a2`；
- 每个 terminal：`status=FAILURE`、`failure_stage=ANSWER`、`attempt_count=1`、`selective_retry_count=0`；
- 每个 Answer role report：`failure.type=ModuleNotFoundError`，operation audit PASS、禁止项全 0；
- 四个 Gateway database 的所有 `ai_model_call_*` 表均为 0 行，所以没有 TLS/HTTP/model request、没有 token 使用，也没有
  Provider response。每次只发生三个 supervisor-owned TCP descriptor provisioning，随后 Gateway 等待 Answer 并失败关闭。

## Disposition

根因与修复规则见 `FINDING-007-006`。run-001 session、grant、四个 terminal 和 Gateway DB 全部原地保留，不删除、不覆盖、不把
用户重复点击描述为 controller retry。现有服务已停止。修复后的代码必须通过 exact isolated entrypoint import、full regression、
docs check 和新 product freeze；新体验需要新的 post-freeze grant/session。

Production Activation 与 Git stage/commit/push 均未执行。
