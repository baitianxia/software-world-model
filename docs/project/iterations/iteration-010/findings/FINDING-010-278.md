---
id: FINDING-010-278
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, quality, security]
depends_on: [FINDING-010-275, FINDING-010-276, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/lightweight_engineering_agent.py]
tests: [tests/test_lightweight_engineering_agent.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: bounded-citation-repair-per-immutable-observation-prefix
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-278：多 Observation 的 Citation ordinal 必须按局部域受控重规划

## Observation

`run-158-phase-c-loopback` 的 q5 在 fresh Reviewer 返回 `MORE_EVIDENCE` 后读取了新的 interface Source。Primary 随后把
`citation_index=2`、`citation_index=3` 当作跨 Observation 的全局 ordinal；但每个已读取的 Observation 都只暴露自己的局部
`citation_index=1`。Application 正确在 fresh Reviewer 前拒绝该选择并以 `CONTROL_STATE_DENIED` 结束。原有“一次重规划”状态若只按
Turn 计数，会把新增 Observation 后的合法修复机会错误地耗尽；若放宽校验或自动重编号，则会伪造 Citation provenance。

## Evidence

- `/Users/baitianxia/project/software-world-model/var/iteration-010/slice-001/run-158-phase-c-loopback/terminal.json` 的 terminal file SHA-256 为
  `sha256:5c9bc0da0d83e61fc4c1224a5a8de6c8253b1864740644e61f3b1c74cf63cf14`，terminal digest 为
  `sha256:74a060cdb6a0defd60545695649cd0d582153fee54833f0fd6c7a59adefab1ae`；q1/q2/q4 已进入 fresh Reviewer，q3 为零调用澄清，q5
  的 33 次 dispatch 在非法局部 binding 前停止。
- 监督 lane 的
  `run-158-primary-citation-binding.json`（file SHA-256
  `sha256:87095371e919527eed49b1aa2f90af7ba78826197c67812636da5f7cd80e7760`）记录 q5 的 selected pairs
  `obs4/1, obs3/2, obs5/3`，而 observations 3、4、5 的实际 Citation domain 均为 `[1]`，并确认没有重试、过滤、重编号或合成
  Citation；最早责任层是 Application Agent citation binding。
- `tests.test_lightweight_engineering_agent` 新增异质夹具覆盖：多个 Source Observation 各自从局部 index `1` 开始、第一次全局式
  选择后同一主 Agent 的一次重规划、同一 prefix 的第二次非法选择 fail-closed，以及 Reviewer `MORE_EVIDENCE` 产生新 Observation
  prefix 后的一次新的受控重规划；19 项定向测试通过。

## Disposition

保持 `_resolve_citations` 的严格局部 ordinal 校验，不由 Application 自动映射、替换、重编号或合成 Citation。Application 以当前有序
Observation 的不可变 prefix（每项的 `observation_index` 与 digest）作为内部计数键；同一 prefix 只允许一次机械 citation-binding
replan，并保留原 selection、model receipt、rejected answer 与既有 findings。Primary 可在该机会中继续读取源码；真实新增 Observation
形成新 prefix 后，才获得一个新的同范围 replan。新 prefix 的次数仍受既有 Agent step/tool/review fuse 限制，第二次对同一 prefix
非法时继续 `CONTROL_STATE_DENIED`，不进入 Reviewer 或 Delivery。

该修复只使用现有 Agent feedback 字段和既有 Source/Citation identity，不增加版本化 Agent option、输入输出 schema、Prompt、Provider、
Reviewer 重试、预算或题目/工程特判。Owner `SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 同步这一 prefix 边界；真实 fresh
successor 仍需证明 q5 能在补证后进入 fresh Reviewer，并与三个异质问题及一个语义追问组成可体验 loopback Web 链。本 Finding 不宣告
Phase C 完成或 `ADVANCE`。
