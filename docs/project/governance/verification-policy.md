---
id: PROJECT-GOVERNANCE-VERIFICATION
kind: project-governance
status: current
authority: project-governance
owners: [quality]
depends_on: [SYS-QUALITY-ACCEPTANCE, PROJECT-GOVERNANCE-ITERATION-LIFECYCLE]
code: [validation]
tests: [tests]
---

# Verification Policy

## 证据类型不能互相替代

| 类型 | 回答的问题 | 不能证明 |
|---|---|---|
| Unit/Contract Test | 本提交的局部和跨模块机械行为是否符合 | 真实 Provider、模型能力、用户价值 |
| CC — Contract Conformance | exact Adapter/Provider 是否满足接口契约 | 业务任务是否做得好 |
| CE — Capability Evaluation | exact Model/Prompt/Tool/Strategy 是否达到某能力门槛 | 端到端产品不退步或生产已启用 |
| Product Validation | 用户旅程在冻结未见输入上是否达到产品下限 | 所有未来输入或生产安全 |
| Activation | 哪个资格在何种环境和范围可被使用 | 资格本身正确或永久有效 |

## 运行治理

1. 输入、Oracle、资源限制和失败条件在运行前冻结；评审依据不能提前泄露给生成路径。
2. 生成与评审来源独立；无法独立时必须披露限制，不能声称独立验证。
3. Result 绑定 exact implementation identity、配置、Adapter、模型实际身份、Prompt/Tool/Strategy、输入 Digest 和有效期；仓库已版本化时同时绑定 Git commit。若运行时没有 Git 身份，必须如实标记缺失，不能用后来创建的提交回填。
4. `OUTCOME_UNKNOWN` 不得改写为 FAIL、零 Usage 或 PASS；迟到结果按原 Run 身份解析。
5. 失败、过期、stale 和 superseded 结果继续保留，但不能支持新 Activation。
6. 原始运行证据默认位于 `var/` 且不受 Git 管理；版本化 Result 必须明确它是摘要/attestation，并给出本机证据身份与保留限制。
7. Result 不能反向定义 System Contract；发现契约错误时走 Implementation Finding 和 System 修订。

## Current Codex 强基线协议

从 `ITER-010-PDR-002` 后首个新建产品迭代起，产品问答最低门必须包含系统与运行时 current Codex 的同题独立盲评：

1. Codex 只是强外部基线候选，不是 Oracle、rubric 作者或 adjudicator；事实边界是原问题与同一授权 exact revision 上可核验的软件证据。
2. 对照前冻结 Codex 客户端/二进制、实际模型、reasoning、工具、权限、Source scope、问题与 revision；每题使用 fresh 隔离任务，答案在
   向系统披露前密封。任一身份漂移烧毁并重跑基线。
3. 系统不得读取 Codex 答案，Codex 不得读取世界模型产物、系统答案、本项目对话或既有 verdict。两份答案均先密封，再随机匿名为 A/B。
4. 独立评测方不得参与任一答案生成，也不得看到来源标签、生成 trace 或先前 verdict；它读取原问题与 exact evidence，允许判定系统更好、
   打平、Codex 更好、双方失败或无法裁决。
5. `PASS` 要求冻结的全部问题均已完成并进入唯一逐题分类，分类计数与冻结题数严格相等；系统绝对质量门全部通过、逐题没有物质性退步，
   且预提交盲评量表的总体答案质量差值严格为正。全体打平、双方失败、无法裁决或盲化无效均失败；成本、时延、调用次数、缓存与复用
   指标只能另行报告，不能补偿答案质量。
6. current Codex 产品基线不与世界模型因果消融混用。只有 full cognition 与 locator-only/empty control 才要求相同系统模型、链路、预算
   和 cache。

## Verification Matrix

每轮按 Outcome 列出 Case、级别、输入、预期、证据位置、执行状态和阻断含义。缺失、未运行或证据过期均不是 PASS。
