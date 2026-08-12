---
id: ITER-005-RESULT-SLICE-002-RUN-006
kind: iteration-result
status: live-quality-gate-failed-preserved
authority: execution-evidence
owners: [engineering, quality]
depends_on: [ITER-005-VERIFICATION, ITER-005-SLICE-002, FINDING-005-009, FINDING-005-010]
code: [src/software_world_model/interface/world_model_http.py, src/software_world_model/interface/world_model_browser_ui.py, validation/structure_world_model_iteration_005/slice2_comparison.py, validation/structure_world_model_iteration_005/slice2_evaluator.py]
tests: [tests/test_world_model_browser.py, tests/test_iteration_005_slice2_comparison.py, tests/test_iteration_005_slice2_evaluator.py]
iteration: ITER-005
---

# SLICE-002 Run-006 Live Evaluation

## Decision

`run-006` 的真实 `EVALUATION_ONLY` 比较按密封顺序完成，但 V-009 quality gate 返回 `FAIL`，因此不接受 SLICE-002 或
ITER-005。World Model 9/9 成功，Mature Source Agent 9/9 成功，controlled Direct 5/9 成功；独立 evaluator 因四题缺少
两条 eligible baseline 阻断。所有 failure terminal 原样保留，没有重试、筛选、插值或补跑。Production Activation
`NOT_EXECUTED`。

## Authorization and sealed order

用户授权原文只覆盖 `run-006` 的 9 个问题与 Maven POM 源码闭包，限制为火山引擎 Ark 和 OpenAI Codex 的
`EVALUATION_ONLY`，并明确禁止 Production Activation。授权 reference 为
`codex-user-message:sha256:9840fb8f38156a188d7d9fa750b59be70b2284d44d10aca52f94d688a4b2dcfa`，authorization document
`sha256:44df77341be1fe5106db0d72fafd7f8721718213da7212f8423fb75c7a659e15`，绑定 suite
`sha256:ece08225c5902d33e805330a51443e0abd1ddb198a8c90aba4cc418201623e31`。

controller 先完成 controlled Direct，再完成 Mature Source Agent，并在首个 World Model result 前生成 baseline seal
`sha256:b85bb4fffa4f124fada2235495d7f1e5621d53b173a887dce43fc0cc1b914326`；seal 时两条 baseline 各 9 条、World Model 为 0。

## Population and evaluator evidence

| Surface | Population digest | Success / failure | 调用边界 |
|---|---|---:|---|
| controlled Direct | `sha256:8cb40242f7c7a7112d4a01d4b5d313b75a38e875c1e3492210d1eaef0dc79272` | 5 / 4 | 每题 1 external task、0 retry；每个 terminal 1 Provider request |
| Mature Source Agent | `sha256:6757bb658eb99f56c5c3370a6c3d7f798056822d18c4bdb70ea4654b457f2ee2` | 9 / 0 | 每题 1 exact `codex exec`；内部 Provider call 不可观测 |
| World Model | `sha256:fbd3f574527e3a263cc553e60840d1508cef28de30eb35f477fbd3a43b5bfb20` | 9 / 0 | 每题 1 Provider call、1 network op、0 retry |

independent comparison report
`sha256:278c7c3c52141314318071b9e275864bb5907bada3d8c5fe12f34f837b040ea1` 为 `FAIL`。World Model 九题均
eligible、重大错误为 0、完整性为 1,000,000；blocker 精确为 `WM-005-001/004/005/006: both baseline outputs must be
eligible`。

Direct 失败证据分为：`WM-005-005/006` 在 1000 output token 上以 `length` 截断；`WM-005-001` 在 stop terminal 中输出
answer 内未转义 ASCII 双引号，形成无效 JSON；`WM-005-004` 一次 dispatch 后进入 `PROVIDER_OUTCOME_UNKNOWN`。前三项的
系统性 response-envelope 缺陷由 `FINDING-005-010` 处置；outcome unknown 按 no-retry protocol 保留。

## Real-browser acceptance

正式产品入口以 exact candidate/grant 启动，health、startup receipt 和 preflight 均通过。真实 in-app browser 在 1280 px
viewport 完成以下核对：

- READY identity 为 `19c60da17`，动态 Catalog 显示三个 exact Read Set，Production Activation 显示未执行；
- 三张长 identity 卡宽度约 139.5 px，均留在约 436.5 px 的 grid parent 内；第三张卡可以通过普通语义 click 选中，证明
  `FINDING-005-009` 的 `minmax(0,1fr)`/换行修复有效；
- supported request `wm-fedb0927-0100-41e4-bedc-eb902dd4e276` 在 R2 Read Set 返回 `SUPPORTED`，page
  `sha256:4a1d8de7d493f690f2293f9d474a52bf5b0f41d5fb99452011a325f442dafea2`，Provider/Network/Retry=`1/1/0`；
- Citation `structure_view_result_7559d1571fe840dd0a0bc0f92442d4ac` 可独立打开，显示 result seal、projection seal 与 exact
  POM observations；
- Gap request `wm-8d492bc1-450d-42af-9531-3c4cff8e3fea` 返回
  `CHANGE_INTENT_OUTSIDE_STRUCTURE_COVERAGE`，page
  `sha256:5ce785b20b1f03add7375817635f0f5d660dae65f864c218ae26522537cccd5c`，Provider/Network/Retry=`1/1/0`；
- 浏览器 console 无错误；服务在验收后正常停止。

浏览器 PASS 只闭合 V-007 的实际交互证据，不能覆盖 V-009 comparison `FAIL`。后续任何新 suite 都必须重新取得 exact
披露授权并重新执行完整 gate；本 Result 不授权 Production Activation。
