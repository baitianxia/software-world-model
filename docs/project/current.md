---
id: PROJECT-CURRENT
kind: project-current
status: current
authority: current-development
owners: [project]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ITER-001-INDEX, ITER-002-INDEX, ITER-002-SLICE-001]
code: []
tests: []
as_of: 2026-08-10
active_iteration: ITER-002-INDEX
active_slice: ITER-002-SLICE-001
worktree_status: authorized-verification-pass-dirty
strategy_relation: differs-from-accepted-1.38.0
live_model_path: evidence-first-capability-pass-product-pass-local-browser-active
---

# 当前工作上下文

## 开发授权

**当前活动开发是 [Iteration 002](iterations/iteration-002/README.md) 的 [SLICE-001：通用工程问答可验收](iterations/iteration-002/development-design/SLICE-001-generic-repository-answer-quality.md)。** 用户已明确授权继续开发并免除非必要的逐步确认。授权范围是本机、无认证、任意本地 Git 工程的通用浏览器问答及其验证；生产启用、外网发布和写入用户工程不在范围内。

## 当前系统与实现状态

| 范围 | 状态 | 证据边界 |
|---|---|---|
| Iteration 001 历史裁决 | Completed / pre-Git attestation | 版本化旧记录登记 production `288 / 288 PASS`、Demo `121 / 121 PASS`；原 production 日志及 exact Git identity 未版本化 |
| 重构前 Git 快照 | Mechanical PASS | `476517b5baf62abcc5a6ddda30b33335d262a8f3` 在本次迁移的独立临时 checkout 上为 production `290 / 290`、Demo `121 / 121`；这是新机械复验，不替代历史 CE/Product 证据 |
| 当前未提交工作区 | **AUTHORIZED / LOCAL ACCEPTANCE PASS** | 同步聊天已迁移到 Evidence-first Strategy `1.0.0`；当前差异仍未提交，精确 subject 由基线 `cd8abad…` 与工作区差异共同表示 |
| Ark Adapter Contract Conformance | PASS / exact subject | `openai-chat-completions-no-tools@8`；原 Result 有效至 `2026-09-05T21:04:18.073701Z`，但不能替代 CE |
| 十类通用 Capability Evaluation | **PASS / CURRENT STRATEGY** | Evidence-first Strategy `1.0.0` 的问题保持、只读调查、证据综合、独立审核、同包重写、缺口分类、响应语言、时间顺序、未证实意图、相关性与可读性全部由 Codex 对冻结 Oracle 独立复核；Result `evaluation_result_26fdfbbea40b4c87aede82270eed68dd`，Qualification `sha256:3d529903…acd54`，有效至 `2026-08-16T19:17:05.882130Z` |
| 陌生工程 Product Validation | **PASS / CURRENT STRATEGY** | `poi-tl` 与 `transmittable-thread-local` 六个冻结任务、33 个验收维度全部正确完整；系统路径与直接源码基线正确率/完整率均为 `1.000 / 1.000`，重大错误为 `0`；Attestation `product_validation_dc02535f3c837cc0b469e14f51fef93d` |
| `local-browser` | **ACTIVATED / EXPERIENCE PASS** | 本机 Activation `activation_decision_af90ea83192f441eb7140a011340221c` 绑定当前能力资格和产品证明；真实页面已连接冻结 `poi-tl`，正确回答超时与异常传播问题且展示经复核状态和源码位置 |
| Production Activation | **NOT EXECUTED** | 不得由任何前置 PASS 自动推导 |

当前精确结果见 [Iteration 002 Results](iterations/iteration-002/results/README.md)，旧系统结果见 [Iteration 001 Results](iterations/iteration-001/results/README.md)。PASS 绑定其精确 subject；到期或实现、配置、模型、Adapter、输入发生漂移后必须重新验证。

迁移前曾使用漂移后的工作区、复制的 Activation DB、原 CC Result 和 dummy Secret 做无网络预检，并在 Provider 调用前以 `STRATEGY_CONTRACT_MISMATCH` 失败关闭。这证明旧 local-browser Activation 不能跨 Strategy 继承；当前 Activation 是在 Evidence-first 重新资格化和产品证明后独立创建的。

## 当前决策顺序

Iteration 002 的机械测试、十类能力评估、陌生工程产品验证和本机浏览器体验均已形成 PASS 结果。下一项决策是是否接受并关闭本轮；[生产启用](roadmap/candidates/production-activation.md)、[Schema Evolution](roadmap/candidates/schema-evolution.md) 和 [Semantic View](roadmap/candidates/semantic-view.md) 仍只是候选，不因本轮 PASS 自动进入开发或启用。

## Agent 读取范围

Agent 只把 `ITER-002-SLICE-001` 作为当前编码输入，并按其引用读取 System 文档。实现发现写入本轮 Findings；超出本机通用问答范围的变化不得从 Roadmap 推断授权。
