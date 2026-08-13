---
id: ITER-006-RESULT-LIVE-RUN-003
kind: iteration-result
status: failed
authority: execution-evidence
owners: [engineering, quality]
depends_on: [ITER-006-VERIFICATION, ITER-006-RESULT-LIVE-CANDIDATE-FREEZE, ITER-006-FINDINGS]
code: [validation/structure_world_model_iteration_006/live_comparison.py, validation/structure_world_model_iteration_006/live_evaluator.py]
tests: [tests/test_iteration_006_live_evaluator.py]
iteration: ITER-006
---

# ITER-006 Live run-003 Result

## Decision

`run-003` 在用户明确授权后完成三路 population，但结果为 **FAIL**：controlled Direct 与 Mature Source Agent 均为 6/6
SUCCESS；World Model 为 4/6 SUCCESS，method inventory 与 positive path 两题在 Provider 调用前被 exact Model Egress
qualification 拒绝。失败全部保留、controller retry 为 0，没有补跑或插值。

冻结 evaluator 随后又因失败 terminal 的空 completeness 触发 `TypeError`，没有生成正式 comparison report。这个 evaluator
缺陷已为下一次 freeze 修复，但不能追溯改变 run-003。V-008 因两个 World Model terminal failure 已明确失败；V-009 只取得
部分真实浏览器证据。Slice 与 Iteration 均未接受。

## Exact authorization and immutable inputs

用户授权消息绑定为
`codex-user-message:sha256:4f48e0d516569900219dada7447c7610ebec5c91e617935c6a1ee2dc5fabc5c3`，授权时间
`2026-08-12T03:40:58Z`。消息明确点名火山引擎 Ark、OpenAI Codex、run-003 suite、三路 payload boundary 与
`EVALUATION_ONLY`，并排除 Production Activation、提交和推送。

- suite：`sha256:32de10fb1c13c3317c23c624c3fabfdafd909e8d6c4d9e23bad77b8f804aab60`；
- comparison authorization：`sha256:12e57e9f2e328fe790379b624988cc726516e037bf77aea52632f516ea5ca4bf`；
- disclosure authorization：`sha256:101b1726e64ee75443a222d3c750e8f11771697ca1a9246e142b3348d811c51b`；
- evaluation grant：`sha256:cb575bc2c70d12284f468cd7a6cb67996fecfeb00235e34dec4a6471056d9e0c`；
- baseline seal：`sha256:f6547fe737c068b82dd332986f99444d84bd1ea2d45788dc503f184ca5434b05`，且
  `world_model_result_count_at_seal=0`。

## Three populations

| Surface | Terminal | External task | 可观测 Provider call | Population document digest |
|---|---:|---:|---:|---|
| controlled Direct / Ark | 6 SUCCESS, 0 FAILURE | 6 | 6 | `sha256:47802efaf44fcb61770a127fb9945d2ffab5241980e390dca03509eb57fdb657` |
| Mature Source Agent / Codex | 6 SUCCESS, 0 FAILURE | 6 | CLI boundary 不可观测 | `sha256:f62e27acc35067290d31ea4173f3ade54cd3fb4690c2700bbeeab2659ea8ba8e` |
| World Model / Ark | 4 SUCCESS, 2 FAILURE | 6 | 4；另 2 个在 dispatch 前拒绝 | `sha256:b37b6754aaae00da165b16ccb25eba6335924c0b661bd19a8f3c25a79813cbb5` |

World Model 的成功项为 direct call、supported negative、ordered diff 与 runtime Knowledge Gap；失败项为：

- `WM-006-001` / request `iter006-wm-006-001`：HTTP 502，public body 精确为
  `WORLD_MODEL_EXECUTION_FAILED`，isolated terminal `failure_stage=ANSWER`；
- `WM-006-003` / request `iter006-wm-006-003`：同一失败边界。

两者 Gateway audit 的 response digest 可由 `QUALIFICATION_INVALID` 精确重建，Model Gateway SQLite 均无 call revision，
隔离 operation audit 均为 PASS。根因是候选 generic proposal 已加入 `declared_method_inventory`，而继承的 exact
ITER-003 qualification 只允许旧 Maven operation vocabulary；详见 `FINDING-006-008`。

## Evaluator and browser evidence

冻结 evaluator `sha256:2f186c9d…` 在读取完整三路 population 后因 `int(None)` 退出，未生成 report；该异常不筛除 population
failure。修复后的 evaluator `sha256:a014efee…` 及回归只服务下一次 freeze，详见 `FINDING-006-009`。

修复后的本地验证为：Java/Behavior/evaluator focused tests 18/18 PASS；完整 suite 820/820 PASS（99.227 秒）；文档检查
251/251 current documents PASS，`git diff --check` PASS。完整套件仍只出现 implementation Result 已记录的既有 SQLite
`ResourceWarning`。这些 PASS 证明 evaluator 修复没有引入本地回归，不会把 run-003 V-008 改写为 PASS。

真实 in-app Browser 在 `1280×720` 下确认正式首页 `READY · 1d194f963`、三个动态 Java Read Set、Java Coverage copy、无横向
溢出且 console 为空。浏览器还对已成功的 `iter006-wm-006-002` Citation URL 发出 GET，产品服务记录 HTTP 200 / 7614
bytes；对应独立 projection `status=PASS`、`network_operation_count=0`、`answer_return_port=false`，含 10 条非空 Java
locator/observation。Browser client 不展示原始 JSON，且为了不超出“每题每 surface 一次”的冻结授权，没有从 UI 再提交重复
问题，因此 V-009 仍是 PARTIAL，不写成 PASS。

## Safety and next gate

所有外部调用均限于授权的 `EVALUATION_ONLY`。World Model 只披露 original question + no-payload Structure；Direct/Codex 才
接收对应 exact sealed Java closure。listener 已正常停止；Production Activation、Git stage/commit/push 均未执行。

不得重试或复用 run-003 grant。下一 live run 的前置条件是：版本化 Java generic proposal Strategy/Prompt、全新的 closed
capability qualification、修复后 evaluator、新候选/suite freeze，以及用户对新 suite 的独立披露授权。
