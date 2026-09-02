---
id: FINDING-010-276
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, quality, security]
depends_on: [FINDING-010-275, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/lightweight_engineering_agent.py, src/software_world_model/ai_infrastructure/lightweight_engineering_model.py]
tests: [tests/test_lightweight_engineering_agent.py, tests/test_lightweight_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: bounded-same-agent-replan-for-action-shape-rejection
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-276：可解析但分支字段混用的 Agent 决策需要受控恢复

## Observation

真实 loopback 的 Primary 有时返回合法 JSON，却把不属于所选 action 的字段保留为非空值。run-150 的 `READ_SOURCE` 同时携带了
`read_index=1` 与 `cognition_index=1`，run-155 的 `FINISH` 携带了 `cognition_index=1`；两次都由严格 decoder 在 fresh Reviewer 前以
`STRUCTURED_OUTPUT_INVALID` 拒绝。该失败发生在 Agent/model boundary，不是 Provider transport、World Model cognition、Source Broker/Worker 或
Reviewer 缺陷。若直接把失败当作 Turn 终点，同一个 Agent 的调查状态会因无害的 action-shape 漂移而丢失，降低浏览器纵切的可重复性。

## Evidence

- `/Users/baitianxia/project/software-world-model/var/iteration-010/slice-001/run-155-phase-c-loopback/terminal.json`：Ark 3/3 TLS 与 HTTP
  dispatch 完成、retry=0；q1 三个 Primary 输出中最后一个为可解析 `FINISH`，同时含 `cognition_index: 1`，无 Reviewer dispatch。terminal
  digest 为 `sha256:af7421087d6dee67ce4e4a46e0abf4e84dd867292b1ca30a219bf6da96719444`。
- `/Users/baitianxia/project/software-world-model/var/workspaces/supervision/docs/project/iterations/iteration-010/supervision/runtime/run-150-primary-shape.json`
  （file SHA-256 `sha256:dd50a23d92b0225174dc4e40a19f14626200c2719f90cf3170a8ddcb0ef1eda3`）记录 `READ_SOURCE` 的
  `cognition_index`/`read_index` 字段冲突；`/Users/baitianxia/project/software-world-model/var/workspaces/supervision/docs/project/iterations/iteration-010/supervision/runtime/run-155-primary-finish-shape.json`
  （file SHA-256 `sha256:0b944a29f61855a59f09ba70b2235b6479b32d08b9b014ad4bc7c8be1882219b`）记录 `FINISH` 的 `cognition_index` 冲突。
  两次均保持 strict decoder 和 raw/规范化 Provider output。
- 本次修正的私有方向证据 `/Users/baitianxia/project/software-world-model/var/iteration-010/slice-001/run-155-phase-c-loopback/direction-progress-evidence.json`
  以 mode `0600` 密封，file SHA-256 为 `sha256:96e7fea11f79bc92a0064b879272d3f7a5584ddf07e7e35e304258db73256f0b`；对应
  `direction-report-action-shape-3.json` 的 file SHA-256 为
  `sha256:f9885dbab1d27af3fd94b060682ecf3e8c330f2d386dc58fc1f077e68d4bea79`，direction verdict 为 `PASS`、violations 为空。
- 本地 executor fixture 覆盖一次恢复、原 rejected receipt 保留、同一 primary 使用现有反馈字段继续，以及第二次仍拒绝时 fail-closed；model
  fixture 覆盖 `FINISH` 携带 `cognition_index` 仍先被 typed decoder 拒绝。

## Disposition

`LightweightAgentDecision.from_payload` 继续严格拒绝 action-specific 字段组合，不静默清字段、不替换 action、不把无效输出当答案。
模型边界只为该明确的 branch inconsistency 标记一个内部可恢复类别；executor 保存 rejected receipt 与机械 trajectory event，并通过已经存在的
`review_findings` 输入字段告知同一主 Agent：沿用当前 Observation，令未使用字段为 null。若此前已有被拒绝答案或审核/Citation binding findings，
机械诊断追加到既有反馈并保留原答案，要求同一 Agent 一次处理全部反馈。最多发起一次新的正常 primary dispatch；这不是同一 Provider 请求重试，
也不改变 World Model、Observation、Citation、答案或 Reviewer 契约。第二次同类失败及其他结构化失败继续
`STRUCTURED_OUTPUT_INVALID` fail-closed，不进入 Reviewer/Delivery。该实现没有新增版本化 Agent 协议、Prompt、Provider、题目规则或答案语义检查。

Owner `SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 已同步上述边界。真实 fresh successor 仍需在原题和异质问题上证明恢复后可进入
Source READ、真实 Citation、fresh Reviewer 与 loopback Web；本 Finding 不宣告 Phase C 完成。
