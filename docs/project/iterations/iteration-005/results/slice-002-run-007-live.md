---
id: ITER-005-RESULT-SLICE-002-RUN-007
kind: iteration-result
status: ready-for-user-acceptance
authority: execution-evidence
owners: [engineering, quality]
depends_on: [ITER-005-VERIFICATION, ITER-005-SLICE-002, ITER-005-RESULT-SLICE-002-CANDIDATE-FREEZE, FINDING-005-010]
code: [src/software_world_model/interface/world_model_http.py, src/software_world_model/interface/world_model_browser_ui.py, src/software_world_model/interface/world_model_product.py, src/software_world_model/interface/world_model_runtime.py, validation/structure_world_model_iteration_005/slice2_comparison.py, validation/structure_world_model_iteration_005/slice2_evaluator.py]
tests: [tests/test_world_model_http.py, tests/test_world_model_browser.py, tests/test_world_model_evaluation_grant.py, tests/test_world_model_gateway_authorization.py, tests/test_world_model_product.py, tests/test_iteration_005_slice2_comparison.py, tests/test_iteration_005_slice2_evaluator.py, tests]
iteration: ITER-005
---

# SLICE-002 Run-007 Live Evaluation

## Decision

`run-007` 的 exact `EVALUATION_ONLY` live gate 为 **PASS**。controlled Direct、Mature Source Agent 与 World Model 三条
population 均为 9/9 成功；独立 evaluator 对九题均判定 World Model eligible、重大错误为 0、完整性为 1,000,000，且
逐题不低于两条可评 baseline 中较强者。正式产品 Web 入口的 supported、Citation、动态 Read Set 选择、Coverage Gap 与
console 人工核对也全部通过。

该 Result 闭合 SLICE-002 的 V-006—V-010，因而 SLICE-002 与 ITER-005 已达到**等待用户验收**状态；它们尚未被用户接受，
本文件也不自行产生 Acceptance。Production Activation 始终为 `NOT_EXECUTED`。

## Exact authorization and sealed order

用户授权绑定 held-out suite
`sha256:04f50cae8392296d8173921e56063abded7d66c33c17d97019d50ac965b9f884` 的 9 个问题和 exact Maven POM
源码闭包，只允许发送至火山引擎 Ark 与 OpenAI Codex 用于 `EVALUATION_ONLY`，并明确禁止 Production Activation。
authorization reference 为
`codex-user-message:sha256:14fb67f7fa2aee866b0f1603923fad996908f44873f37cb6ed8a9594650c7c4f`；authorization
document 为 `sha256:a33d65377f9aec8c249a3351f484c226a0cf501b1694ad1dbbf0c73a6f3411de`，授权时间为
`2026-08-11T22:08:23Z`。product evaluation grant 为
`sha256:bfeecc85a626113acf6d1ac594d368ceba32737e02b1d44392040eac84d18158`，其中 disclosure authorization 为
`sha256:6a74fa211da15797c7db88f2087f0a0c427e2e48aef7e5a818b3596e39768ee3`。

controller 先执行 controlled Direct，再执行 Mature Source Agent，并在首个 World Model result 前生成 baseline seal
`sha256:cd193c00db86e069eb72c9f1dec17cedbc987424921cd5682d576f0653640d23`。seal 时间为
`2026-08-11T22:17:02.999109Z`，两条 baseline 各有 9 条结果，World Model result count 为 0；之后才启动产品入口并执行
World Model population。全部 terminal 原样保留，没有重跑、筛选或插值。

## Population and independent evaluator

| Surface | Population document digest | Success / failure | 调用边界 |
|---|---|---:|---|
| controlled Direct | `sha256:a9c3e586c86202b1f29b1d489229ba6ce38ef3c79512c10a9d42969c1934e429` | 9 / 0 | 每题 1 external task、1 Provider call、0 controller retry；4096-token 严格 JSON-only `@2` envelope |
| Mature Source Agent | `sha256:1b8783e0e969855126363d97854ec48cc9b0ffffa7089f7b1951cf8e46254261` | 9 / 0 | 每题 1 exact `codex exec` task、0 controller retry；内部 Provider call 不可观测并记录为 `null` |
| World Model | `sha256:f5b5b19e4065eb02b4db2fa647fc32a0824b3299e4363fc875c7a205adbde11d` | 9 / 0 | 每题 1 external task、1 Provider call、0 retry |

independent comparison report
`sha256:e7d16fa4f56cf35243f100ffb5cd4b56d950b3bb620a08c273f281ef7e6c0116` 返回 `PASS`，`blockers=[]`、
`failures_filtered=false`、`missing_outputs_interpolated=false`。World Model 九行均为 `eligible=true`、
`major_error=false`、`completeness_ppm=1000000`，没有 forbidden hit 或 missing token。

对照仍诚实保留 baseline 的质量差异：Mature 在 `WM-005-004` 方向错误；Direct 在 `WM-005-007` 缺少
`AMBIGUOUS` outcome marker；Mature 在 `WM-005-008` 缺少 `ZERO` marker；两条 baseline 在 `WM-005-009` 均缺少
`Knowledge Gap` token。World Model 未出现这些错误，并逐题达到或超过 stronger baseline。

## Product startup and real-browser acceptance

正式产品命令只绑定 `127.0.0.1`，startup receipt
`sha256:4ab55e41053c3fbc583b7f4ce397aa8dcd032efeff2e0fc02dca21a313faa8f8`、startup preflight
`sha256:3f2527b6197fd63b028229692bab59e7894508847b1e6baeda0ad2b466a376e3`、Gateway authorization receipt
`sha256:61c332567f8209ef1d913b8bbcf490e8996740492e6723e4348eeef89e293959` 与 Provider subject
`sha256:6373f6d5be8f51c0418d48b14e54e449a9f824a58f33f16274b05da27275e2ce` 全部匹配 exact
commit/tree、suite 与 grant。

真实 in-app browser 通过普通语义操作完成以下核对：

- READY identity 为 `0c2b155d4`，页面显示 `WORLD_MODEL / EVALUATION_ONLY`、三个动态 exact Read Set 和 Production
  Activation 未执行；
- 三张长 identity 卡均位于约 436.5 px 的三列 Grid 内，每张约 139.5 px；第三张 R2 Read Set
  `read_set_fed0740ef3d736d2412376e670ce885c` 可选中；
- supported request `wm-02208ddb-a0c1-4b5f-b926-40acfff1cee1` 返回 `SUPPORTED`，page
  `sha256:7bd6d5d83c7c14f0a98cbdc2490d7efae52e29a1d6be9e55f9d200afea40dfd8`，Provider/Network/Retry=`1/1/0`；
- Citation `structure_view_result_4844fa85f6b64ce9c4f50cf91e3cf0f0` 可独立打开；result seal
  `sha256:ae66d06a975e9c528fb56a3f55fd9f60cdab78050bb486adfe06dcb96a247b9a`、projection
  `sha256:48175a22a480438fe8bb57f44b4681e2c3e0a4cfae033677bb38d4961a617c20` 与 exact POM observations 可见；
- Gap request `wm-344a7ffe-85ef-4123-8e33-b41c599ef165` 返回 `KNOWLEDGE_GAP / CHANGE_INTENT_OUTSIDE_STRUCTURE_COVERAGE`，
  page `sha256:1b591fa7322e54da1bb7d8ddb87514572e784c3d16290f40e2eb3879bd5b4662`，Provider/Network/Retry=`1/1/0`；
- 浏览器 console logs 为 `[]`；验收标签被关闭，本机 listener 在验收后正常停止。

两条浏览器请求均绑定 producer commit/tree `0c2b155d42a272d1b2172f5a82c41179855cd44d` /
`f505499ef4a1891c43eeddb689812a2a660693e7`、exact R2 Read Set，且 `source_access_count=0`、
`evidence_payload_access_count=0`。

## Deterministic qualification and remaining decision

live subject 继承 [Candidate Freeze](slice-002-candidate-freeze.md) 的 51/51 focused、13/13 protected staged Answer、
801/801 full regression 与 docs check PASS。所有十条 Finding 均已处置，旧 `run-006` 的 comparison `FAIL` 和浏览器
`PASS` 仍由独立 Result 保存，没有被覆盖。

当前剩余动作只有用户对 SLICE-002 / ITER-005 Result 作接受、拒绝或后续决策。接受范围仍仅为本机 Maven Structure
World Model `EVALUATION_ONLY`：Scheduler、真 Delta、多源、非 Maven Profile、认证、网络部署、Schema Evolution 和
Production Activation 均不在本 Result 中，Production Activation `NOT_EXECUTED`。
