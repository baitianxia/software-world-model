---
id: FINDING-010-092
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai, operations, project, quality]
depends_on: [ITER-010-SLICE-001, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-OPS-CONFIGURATION, FINDING-010-090]
code: []
tests: []
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: transparent-qualified-ark-primary-deepseek-fallback
target: SYS-ADR-017
---

# FINDING-010-092：当前 live 路径没有落实 Ark 优先、DeepSeek 备用策略

## Observation and evidence

用户以 `codex-user-message:sha256:47a3421d48fe3f36000e45696ea9c41b49b7e362332bc724306c10ca42fe119c`
明确模型策略：Ark 是优先 Provider；DeepSeek token 成本较高，批量运行应尽量放到 DeepSeek 定义的非高峰时段。同轮后续纠正进一步
收紧为：用户只提交一次 logical question；只有 Ark attempt 已密封终止、没有 authorized answer 且存在可信分类的 Provider/model
availability 或 capability reason 时，系统才可透明启动一个独立 DeepSeek fallback attempt。

当前文档和实现身份尚未形成这个可验证闭环：`SYS-OPS-CONFIGURATION` 记录当前 Ark 配置，而 ITER-010 Engineering QA 的已封存运行与
`SYS-OPS-LOCAL-BROWSER` 仍固定 DeepSeek Session Configuration。Model Gateway 当前禁止 request dispatch 后跨 Provider，却尚未把
“session 预授权 Ark → DeepSeek 有序 route；同一 logical question 的 primary attempt 失败后透明执行独立 fallback attempt”定义为当前
产品 route policy。因而不能把历史 Ark 失败、旧资格或 DeepSeek 已配置解释为 fallback 依据，也不能要求普通用户理解 Provider、重提问题
或重新启动 session。

DeepSeek 官方定价页截至本次复核仍写明峰谷策略“即将采用”，生效日期以正式通知为准；它把北京时间每日 `09:00–12:00`、
`14:00–18:00` 定义为高峰。因此计划上的非高峰窗口为 `00:00–09:00`、`12:00–14:00`、`18:00–24:00`，但在每次批量运行前仍必须
重新检查官方页面并记录当时是否已经生效，不能把未来政策冒充当前折扣。官方来源：
<https://api-docs.deepseek.com/zh-cn/quick_start/pricing/>。

## Decision and disposition

- `SYS-ADR-017` 和 `SYS-CONTRACT-AI-MODEL-GATEWAY` 定义 Ark 为 primary、DeepSeek 为唯一 fallback。Session authorization 在任何问题
  dispatch 前预封有序 route，以及两个 Provider 各自的 credential/disclosure/qualification scope；普通用户只提交一次 logical question。
- Ark attempt 必须先形成独立密封 terminal。只有 Provider 不可用、Provider HTTP/outcome unknown/output invalid，或模型结果未通过独立
  Review 这类明确的 Provider/model capability reason 才能启动一次 DeepSeek attempt；Application、Source 或 Security 失败不得换模型掩盖。
- DeepSeek attempt 拥有独立 identity、Manifest、Ledger、Package、Answer、Review 和 audit，并从 immutable original question 与同一
  World Model Cognition 重新运行完整链；不得拼接 Ark 的半成品、Ledger、Package、Draft 或 Review。迟到的 Ark 结果必须隔离，永不覆盖
  fallback 或最终 logical-question result。同一 Provider retry 为 0，每个 logical question 最多一个 fallback attempt。
- Ark unavailable/capability evidence 必须绑定当前 Adapter、Configuration、endpoint、model、credential reference、产品身份、attempt 和
  时间边界；旧 run、过期资格或不同 identity 的失败不能复用。`OUTCOME_UNKNOWN` 可在 primary attempt 终止并封存后触发 fallback，但
  必须记录可能发生的重复计费风险。
- 同 identity 且仍有效的 Conformance 可以复用。Answer Prompt、领域 Schema 或其他不改变 Adapter/Configuration/transport/rendering
  identity 的产品变化，不得仅为了“fresh”再次消耗 Conformance token；identity 漂移或有效期结束时才重跑。
- DeepSeek 批量调用默认只在上述北京时间非高峰窗口启动，并在开始前密封 official-pricing check。若官方策略尚未生效，记录
  `NOT_YET_EFFECTIVE`，不得声称获得非高峰价格；若官方定义变化，以当次记录为准。
- 成本只决定是否开始一个问题或批次。问题一旦开始，不能以余额、token 目标或时间段为由删减 Evidence、Citation、独立 Review 或降低
  质量门槛。一题 canary 未达到技术和答案质量条件时，不启动三题批量回归。
- 当前代码尚未证明上述透明双 attempt route 和 Conformance reuse 已实现；在对应确定性证据形成前，System/Operations 文档必须明确标记
  偏差，不能把本 Finding 写成运行 PASS。
