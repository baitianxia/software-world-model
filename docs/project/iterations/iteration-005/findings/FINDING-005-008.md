---
id: FINDING-005-008
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [quality, engineering]
depends_on: [ITER-005-SLICE-002, ITER-005-VERIFICATION]
code: [validation/structure_world_model_iteration_005/slice2_evaluator.py, validation/structure_world_model_iteration_005/slice2_comparison.py, validation/structure_world_model_iteration_005/slice2_freeze.py]
tests: [tests/test_iteration_005_slice2_evaluator.py, tests/test_iteration_005_slice2_comparison.py]
iteration: ITER-005
classification: verification
disposition: distinguish-external-task-count-from-observable-provider-call-count-and-freeze-baseline-protocols
target: ITER-005-VERIFICATION
---

# FINDING-005-008：成熟 Source Agent 的内部 Provider 调用次数不可由 CLI terminal 精确观测

## Observation

`run-003` 的独立 comparator 要求三条 comparison population 的每个 terminal 都填写整数 `provider_call_count`。World Model
和 controlled Direct 的 Gateway/transport 拥有该计数，但 exact Codex CLI 的公开 event/terminal 边界只证明一次
`codex exec` 外部任务；它不承诺暴露内部 Provider request 数。若把成熟 Source Agent 的值填写为 `1`，会把协议假设伪装成
观测证据。

同时，`run-003` 只密封了 surface 名称，没有把 controlled Direct 的 exact Provider/payload、成熟 Agent 的 binary/model/
permission profile、baseline-first 执行顺序和失败保留策略作为 held-out suite 的 closed input。这不足以证明 baseline 没有在看到
World Model 结果后被削弱或漂移。

## Evidence

- World Model 的 verified Product terminal 与 controlled Direct 的 owned transport 可机械报告成功 terminal 的 exact
  Provider call count；
- Codex CLI `0.147.0-alpha.1.2` 提供一次 `exec` task 的 exit/event/last-message 边界，但没有等价的内部 Provider call-count
  contract；
- 已准备的 exact binary 为 `/Applications/ChatGPT.app/Contents/Resources/codex`，digest
  `sha256:9f6748b4ab10ffc92c28b9ccedae89e61a302bbc011df7d276ee38f55906e481`；成熟 Agent 继续复用 root deny、exact workspace
  read、network deny、shell environment inherit-none 的权限语义。

## Impact and classification

产品的一次 Gateway 调用不受影响；问题在 comparison evidence schema 和 pre-result baseline freeze。继续使用旧字段会制造错误
审计事实，且旧 suite 不能作为真实披露授权输入。该事实改变 V-009 的验证协议但不改变 System Contract，分类为
`verification`。

## Decision and disposition

- population terminal 分开记录 `external_task_count` 与 `provider_call_count`；成熟 Source Agent 成功 terminal 前者必须为 1，
  后者必须为 `null`，明确表示不可观测；World Model/controlled Direct 成功 terminal 两者都必须为 1；失败时保留未知值，
  不伪造；
- held-out suite 升级为 `SWM-WORLD-MODEL-HELD-OUT-SUITE@2`，内嵌 exact comparison protocols、每个 Read Set 的 POM source
  closure、baseline-first 顺序、一次 task/零 controller retry 和全部失败保留策略；
- 新 comparison controller 在创建 output 或发起 task 前验证 suite-bound user disclosure authorization；controlled Direct 与
  Mature 输入 packet 只含 original question 和 exact POM closure，不含 expected/required/forbidden/Oracle/其他路径结果；
- 两条 baseline population 必须先密封，World Model controller 才接受执行；Production Activation 仍为 `NOT_EXECUTED`。
- World Model controller 在首问前还必须从 loopback `/health` 机械匹配 exact suite/commit/tree；Mature last-message 必须由
  controller 再次按 closed answer/claim/locator/limitation shape 验证，不能只依赖 CLI schema 参数。

`run-005` 以随机 seed `322bf6bacafa42b2598137ac77ff18a9` 完成新封存：suite
`sha256:41df3a3231f14f873e29c9249b7730667b9dec06a113164c3950535a66f1bea0`、independent evaluator
`sha256:7e20e083ec25344a672d4055174c9257172c2a1baaf54e5a01c923305ce14805`、comparison runner
`sha256:7b0a8a6ad0e1a791193aacdfcf0998b4ca1f35a67b946136fb4b0411897b58b2`。exact Codex binary/version/argv parse、
48/48 focused、13/13 staged Answer、798/798 full regression、docs check、未授权 comparison pre-dispatch 与产品 pre-listen
均 PASS；`ARK_API_KEY` 被显式移除，外部调用数为 0。pending comparison authorization digest 为
`sha256:b403574f0c3d6a98ebcd747aca6d8325377b990fd981e83279d249d099253688`。因此本 Finding 已 disposition；这不授权
三条真实披露，也不接受 SLICE-002。
