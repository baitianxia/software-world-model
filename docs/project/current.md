---
id: PROJECT-CURRENT
kind: project-current
status: current
authority: current-development
owners: [project]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ITER-001-INDEX]
code: []
tests: []
as_of: 2026-08-07
active_iteration: none
active_slice: none
worktree_status: unqualified-drift
strategy_relation: differs-from-accepted-1.38.0
live_model_path: closed
---

# 当前工作上下文

## 开发授权

**当前没有活动开发迭代或已授权 Development Slice。** Iteration 001 的 pre-Git 历史记录在本机体验范围给出完成裁决；提交 `476517b` 是随后建立的重构前快照，不是原始运行身份。生产启用未执行且是独立决策。Roadmap 中任何 Candidate 都不能直接作为编码输入。

下一次开发开始前必须：选择一个有证据的 Outcome，建立新的 Iteration Proposal、Manifest、Development Slice 和 Verification Matrix，完成 Readiness Review，再更新本文件的 `active_iteration` 与 `active_slice`。

## 当前系统与实现状态

| 范围 | 状态 | 证据边界 |
|---|---|---|
| Iteration 001 历史裁决 | Completed / pre-Git attestation | 版本化旧记录登记 production `288 / 288 PASS`、Demo `121 / 121 PASS`；原 production 日志及 exact Git identity 未版本化 |
| 重构前 Git 快照 | Mechanical PASS | `476517b5baf62abcc5a6ddda30b33335d262a8f3` 在本次迁移的独立临时 checkout 上为 production `290 / 290`、Demo `121 / 121`；这是新机械复验，不替代历史 CE/Product 证据 |
| 当前未提交工作区 | **UNQUALIFIED DRIFT** | Strategy 实现与已验收的 `1.38.0` 不同；精确当前版本由代码拥有且不在文档中复制，该变化不属于活动 Iteration |
| Ark Adapter Contract Conformance | PASS / exact subject | `openai-chat-completions-no-tools@8`；原 Result 有效至 `2026-09-05T21:04:18.073701Z`，但不能替代 CE |
| 六类通用 Capability Evaluation | Historical PASS / current worktree stale | 只适用于实现摘要 `sha256:8973e072…9f301` 的 Strategy `1.38.0`；日期上限为 `2026-08-14T03:14:25.299718Z`，实现漂移已先使其不能授权当前工作区 |
| 两个陌生工程六题 Product Validation | Historical PASS / current worktree stale | 绑定同一 `1.38.0` 实现；日期上限为 `2026-08-14T03:40:46.485258Z`，不能用于当前工作区 |
| `local-browser` | Historical local decision / current live path closed | 历史 local-browser Activation 绑定 Strategy `1.38.0` 与资格，但未绑定 Git commit，且本机复制的 Product attestation 是重新签发记录；当前工作区重新取得完整证明与 Activation 前不得启用真实模型路径 |
| Production Activation | **NOT EXECUTED** | 不得由任何前置 PASS 自动推导 |

精确结果见 [Iteration 001 Results](iterations/iteration-001/results/README.md)。PASS 是不可变历史结果，不等于当前资格；到期或实现、配置、模型、Adapter、输入发生漂移后必须重新验证。当前 Strategy 漂移已经触发这一边界，不需要等待日期到期。

一次使用漂移后的脏工作区代码、复制的本机 Activation DB、原 CC Result 和 dummy Secret 的无网络启动预检，在 Provider 调用前以 `STRATEGY_CONTRACT_MISMATCH: exact strategy version is not registered` 失败关闭；并发版本继续变化后复验仍得到相同结果。这直接验证旧 local-browser Activation 不能被当前 Strategy 加载；它不是新的 CE、Product Validation 或 Activation。

## 下一决策

[生产启用](roadmap/candidates/production-activation.md)、[Schema Evolution](roadmap/candidates/schema-evolution.md) 和 [Semantic View](roadmap/candidates/semantic-view.md) 都只是候选。当前没有证据决定它们的顺序，也没有自动创建 Iteration 002。

## Agent 读取范围

没有活动 Slice 时，Agent 可以读取和分析当前资料，但不得从 Roadmap 或本文推断任何写入、编码或 Proposal 创建授权。只有用户明确授权一项变化后，才按[迭代生命周期](governance/iteration-lifecycle.md)建立最小迭代输入。
