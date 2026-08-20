---
id: FINDING-008-039
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [quality, engineering, project]
depends_on: [ITER-008-SLICE-001, FINDING-008-038, ITER-008-VERIFICATION]
code: []
tests: [tests/test_iteration_008_slice1_freeze.py]
iteration: ITER-008
classification: local-implementation
disposition: hermetic-formal-freeze-test-fixture
target: tests/test_iteration_008_slice1_freeze.py
---

# FINDING-008-039：formal freeze 测试不得依赖未跟踪的 workspace baseline 路径

## Observation

run-027 资格证据写回提交 `173da886b6a9bf16065130837a4e85350478948f` 后，从不含未跟踪 `var/` 的全新 clean
producer 启动 formal `run-008-freeze`。CLI 已通过显式 `--baseline-stage` 接收并实际校验 accepted ITER-006 stage，但 focused
集合中的 `test_candidate_stage_uses_the_bounded_answer_and_gateway` 仍自行读取 producer 相对路径
`var/iteration-006/live/run-008/candidate-stage`。该路径在 clean Git worktree 中不存在，测试因此以
`accepted ITER-006 baseline stage digest drifted` ERROR 关闭；focused 为 88 PASS / 1 ERROR，formal report 尚未形成。

run-008 在 focused 阶段停止，未进入 candidate-package、full regression、grant 或 Web；外部模型调用为 0，hidden canary 与
Production Activation 均未执行。失败目录永久保留且不得沿用为正式 freeze。

## Evidence and root cause

实际 freeze 路径先使用调用方显式提供的 baseline 完成 `_candidate_stage`，说明 accepted baseline 本身没有漂移。唯一错误来自 unit
test 的第二份隐式输入：测试把主工作区本机 `var/` 当作仓库 fixture。它在日常主工作区运行时被历史 evidence 目录偶然满足，在真正
clean producer 中不可重放。

这是验证测试的本地实现问题，不改变产品 `src`、模型 Prompt/Strategy、Capability Qualification、System Contract 或正式 baseline
digest。run-027 Qualification 仍绑定相同 `1.5.10/@19/@1.4.11` product identity；不能通过向 clean producer 复制未跟踪 evidence
来掩盖测试依赖。

## Decision and disposition

1. unit test 在自己的 `TemporaryDirectory` 中构造最小 stage 结构，并把该自包含 fixture 的 tree digest 临时绑定到
   `_candidate_stage`；测试仍验证四个 packaged role、bounded answer workload 与 bounded Gateway workload 的真实复制结果；
2. formal CLI 的生产路径不变，仍在测试前使用显式 `--baseline-stage` 校验 accepted ITER-006 exact tree digest；因此没有降低
   baseline Gate，也没有新增环境 fallback；
3. run-008 保留为未形成 report 的失败尝试。修复提交后只能创建未来路径 `run-009-freeze`，不得复用 run-008 目录；
4. 该处置只修改测试，故 run-027 Conformance/Capability 不失效；新的 formal freeze 仍必须重新运行 focused、candidate-package、
   full regression、docs 与 unauthorized-prelisten 全套门禁。

## Verification and closure

新 hermetic fixture 的单项回归 1/1 PASS；同一不含 `var/iteration-006` 的 clean producer 中 formal focused 89/89 PASS，直接证明
测试不再依赖本机历史 evidence。`git diff --check` PASS。完整 candidate-package/full/docs/unauthorized-prelisten 结果由新的
run-009 formal freeze 统一形成；在其 PASS 前 V-PRE-008、V-003 与 V-WEB-001 继续 blocking。

本 Finding 以 tests-only 处置闭合：现有 formal freeze 已拥有显式 accepted baseline digest Gate，没有新的 System 或 iteration
语义决定。
