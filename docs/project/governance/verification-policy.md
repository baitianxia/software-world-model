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

## 四路产品价值与 Current Codex 强基线协议

从 `ITER-010-PDR-009` 起的当前 ITER-010 及所有后续产品迭代，最早方向门必须在任何与方向无关的产品加固前冻结并隔离四路：直接相关
证据、同 Agent 仅源码、同 Agent 世界模型认知+源码、current Codex。

1. 任何一路模型答案都不是 Oracle、rubric 作者或 adjudicator；事实边界由原问题和同一授权 exact revision 上的独立 exact-source ledger
   提供。直接相关证据路是复杂度 control，不经过 World Model、Agent 或检索协议。
2. 前三路固定同一 Provider/model/configuration、问题、语言和输出边界；两个 Agent 路还必须固定同一 Agent/Prompt/tools/permissions/
   budget/cache/state/Reviewer，唯一变量是 eligible World Model Cognition。
3. 对照前冻结 Codex 客户端/二进制、实际模型、reasoning、工具、权限、Source scope、问题与 revision；每题使用 fresh 隔离任务，答案在
   向系统披露前密封。任一身份漂移烧毁并重跑基线。
4. 四路都不得读取其他路的答案、世界模型产物或既有 verdict；全部答案先密封，再随机匿名。独立评测方不得参与答案生成，也不得看到
   来源标签、生成 trace 或先前 verdict。
5. `PASS` 要求目标系统绝对质量门全部通过、逐题不得输给任一路 control、相对 current Codex 的总体盲评质量差值严格为正，并证明至少
   一项非 locator 世界模型贡献。全体打平、任一重大错误/物质遗漏、双方失败、无法裁决或盲化无效均失败；成本、时延、调用次数、缓存
   与复用只能另报，不能补偿答案质量。
6. Provider 不参与答案优劣比较。前三路整批使用同一 preferred execution profile；首个答案形成前该 profile 不可用时整批 `INVALID`
   并重新冻结，禁止混用 preferred/fallback execution profiles 或在同一批并行测试两个路由角色。具体 Provider/model 名称只能出现在冻结的
   execution profile 和执行收据中，不是比较协议、action 或 Case 的规范性语义。

## Verification Matrix

每轮按 Outcome 列出 Case、级别、输入、预期、证据位置、执行状态和阻断含义。缺失、未运行或证据过期均不是 PASS。
