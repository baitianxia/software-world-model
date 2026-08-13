---
id: ITER-006-RESULT-LIVE-RUN-008
kind: iteration-result
status: accepted
authority: execution-evidence
owners: [engineering, quality, security]
depends_on: [ITER-006-RESULT-PRODUCT-CANDIDATE-FREEZE-RUN-008, ITER-006-RESULT-JAVA-CAPABILITY-RUN-002, ITER-006-RESULT-LIVE-RUN-007, FINDING-006-012]
code: [validation/structure_world_model_iteration_006/live_authorize.py, validation/structure_world_model_iteration_006/live_comparison.py, validation/structure_world_model_iteration_006/live_evaluator.py, src/software_world_model/interface/world_model_runtime.py, src/software_world_model/interface/world_model_runtime_assets/gateway_authorized_workload.py]
tests: [tests/test_world_model_gateway_authorization.py, tests]
iteration: ITER-006
---

# ITER-006 Live run-008 Result

## Decision

`run-008` 已按用户 exact 授权完整执行，三路 Product Comparison 为 **PASS**。controlled Direct、Mature Source Agent 与
World Model 各 6/6 terminal SUCCESS；冻结 independent evaluator 返回 `PASS`、`blockers=[]`，World Model 六题均为
`eligible=true`、`major_error=false`、`completeness_ppm=1000000`，逐题不低于两条 eligible baseline 中较强者。

每题每路只执行一个 external task，controller retry 均为 0；Direct 与 World Model 各有 6 个可观测 Provider call，Mature
Source Agent 的内部 Provider call 继续按 CLI 边界记录为不可观测。没有筛除失败、补写缺失输出或复用旧 grant。V-008 已闭合；
V-009 由 exact 相同 UI 文件的既有人工浏览器证据与本次正式产品端点、Gap、Citation 成功证据组合闭合。Iteration 尚未获得
用户最终 Acceptance，不能由本 Result 自动标记完成。用户随后于 `2026-08-13T11:45:33+08:00` 接受本 Result 已证明的
窄范围，最终裁决见 [Iteration 006 Acceptance](acceptance.md)；该后续裁决不改变本节记录的 run-008 执行事实。

## Exact authorization and single-use seals

- 用户消息 SHA-256：
  `sha256:dc727d3adbe4d3614918d64d8b79897fc0481fda6d2d34580ce6387568612153`；
- authorization reference：
  `codex-user-message:sha256:dc727d3adbe4d3614918d64d8b79897fc0481fda6d2d34580ce6387568612153`；
- authorization time：`2026-08-12T17:00:26+08:00`；
- comparison authorization：
  `sha256:15ca4deb5bc7bfb88b1eae17eafd5dea11f68046953a6de5b56c30e2f38631be`；
- disclosure authorization：
  `sha256:0cdc87a8c2716a67bd141d325cf66e7e95a8f52305039eccb4db955db811387c`；
- evaluation grant：
  `sha256:ff508b30b478a78fd2ff0f7fa8f4af85cf190b23a0f5f540bd3d0c3cca25532c`。

该授权精确绑定 freeze report `sha256:a036921c…`、suite `sha256:0793db73…`、disclosure set
`sha256:1ffb8aa6…`、candidate stage `sha256:862fdb8d…` 与 Java capability proof `sha256:65d18436…`。授权及 grant
raw SHA-256 分别为 `9691daf2…` / `682bbd17…`。它已由本次 18 个 external task 消费，不得重试或用于其他 suite；run-003、
capability 与 run-007 grant 均未复用。

## Baseline-first execution and populations

controller 先完成 Direct，再完成 Codex，并在任何 World Model result 前生成 baseline seal
`sha256:f85585e8e6298c2e80bd3c5923e93449c289eab51389ec4b75dc0c651ba15961`；seal 中两条 baseline 各 6 条结果、
`world_model_result_count_at_seal=0`。随后才启动产品服务并执行 World Model。

| Surface | Population digest | Success / failure | 调用边界 |
|---|---|---:|---|
| controlled Direct / Ark | `sha256:a224f80d1cc7072bd93d23eec5f35f1255b162ff536adca5a2a4aa1ef1d9e323` | 6 / 0 | 6 task、6 fresh completed call、6 unique request、0 retry |
| Mature Source Agent / Codex | `sha256:dc87d3b708d33a7b24c5f26458bf1ff18e555a94022c56a84bea7dfb0f97aacd` | 6 / 0 | 6 isolated `codex exec`、exit code 全 0、0 retry；Provider call=`null` |
| World Model / Ark | `sha256:cbebca5c452f6a09589ddf0d5b4a7889daa8bf1d3cf560ec93716aaa0de6a920` | 6 / 0 | 6 task、6 call、6 network operation、0 retry |

三份 population raw SHA-256 分别为 `3ff8c159…`、`5fd32c20…`、`53f89e7e…`。Direct 的 write-once evidence root
由 controller 记录为 `controlled-direct/population.json/`，其 population 文件为该目录内的 `population.json`；这一实际路径
被 baseline seal 精确引用，没有移动或重写原始证据。

## Independent comparison

comparison report
`sha256:857085c49f7b7ab5a7ccaaa698d5f4288ca7f876aa71dad25052f1780f4861e7`（raw SHA-256 `9a0e942c…`）为
`PASS`，`blockers=[]`、`failures_filtered=false`、`missing_outputs_interpolated=false`。World Model 六题完整度均为
1,000,000、重大错误 0。

baseline 的 terminal SUCCESS 不等同于 evaluator 语义 PASS：Direct 有 4 题、Mature 有 3 题因 exact token/outcome marker
缺失被标记 major error；这些差异均保留。World Model 没有相同缺口，并在所有题上达到或超过 stronger eligible baseline。

## Product, isolation and browser evidence

正式 loopback 产品启动 receipt 为
`sha256:c79bea93abd33b52fda9d13e82d901b9e596b8629b5935a87f2ed7d25e97c0ea`，startup preflight
`sha256:c8c43f16…`、Gateway authorization receipt `sha256:49838dd6…`、grant、suite、stage、launcher 与 Provider subject
全部 exact 匹配。六份内部 Answer summary 与六份 Gateway summary 均为 PASS：

- 6 个 model call ID、6 个 Provider request digest 均唯一；Gateway 记录 6 次 HTTPS dispatch 与 6 个 `RESULT`；
- Answer 的 Source、Evidence payload、authority database、baseline、product suite 与 Oracle access 合计全部为 0；
- Gateway dispatch process DNS operation 为 0，credential value 未记录；
- 六份正式问题 terminal 均为 attempt 1、selective retry 0，并完成 11 个独立 Citation projection。

run-008 的正式 `/health` 与六个 `/v1/world-model/questions` 请求全部 HTTP 200，覆盖 supported、supported negative、ordered diff
与 Knowledge Gap。run-003 已在 in-app Browser 人工确认 1280×720 布局、三个动态 Java Read Set、Coverage copy、Citation GET
与空 console；其 `world_model_browser_ui.py` raw SHA-256 `9cc1387f…` 与 run-008 grant 中的 exact UI 文件相同。本次不为浏览器
重复提交任何题目，而以同一正式端点的六个成功 terminal 与 11 个当前 Citation projection 补齐 live product 证据。

服务已正常停止；`127.0.0.1:55129` listener 与 `/private/tmp/swm-i6r8-live` 下 AF_UNIX socket 文件均不存在。Production
Activation、Git stage/commit/push 均未执行。用户后续 Acceptance 只接受本 Result 已证明的窄范围，且不得推导 Production
Activation。
