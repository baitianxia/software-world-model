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

## Verification Matrix

每轮按 Outcome 列出 Case、级别、输入、预期、证据位置、执行状态和阻断含义。缺失、未运行或证据过期均不是 PASS。
