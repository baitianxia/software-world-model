---
id: FINDING-010-115
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, source, ai, security, interface, operations, quality, project]
depends_on: [FINDING-010-114, SYS-ADR-018, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: systemic
disposition: preserve-third-live-five-turn-failure-and-isolated-new-conversation-pass
target: ITER-010-VERIFICATION
---

# FINDING-010-115：第三次真实五轮 Chat 仍为 0/5，但新对话泄漏负测继续通过

## Authority and execution evidence

在 `FINDING-010-114` 双资格均 PASS 后，用户的
`codex-user-message:sha256:8ebd3650ea8c82ad43dc5015f633cd4e9b0dd3a39a81a6ddfb1566dc6c80d13a` 授权被收窄为 exact
product `d429be6c7e5e43342bf427e394ca5babcc55bcdb` / tree `400d5791e4c443c201765da5f488519093136738`、
`mall@0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` / tree `047d79d8588b76013c260f3f1a9565707301a60a` 的
owner-private `run-037-chat-alpha`。Session config 文件 SHA-256 为
`c0d1bffe494f7e248379dfba5be7071491cdfca062ae2bc183d8acf6e13fa0c0`，固定 5 Turn、每 Turn/Provider 最多 15 logical dispatch、
每 Provider 总计最多 75、同 Provider request retry 0，并继续排除 `src/main/resources`、credential values、hidden、Slice2/3 和
Production Activation。

固定五轮在同一个 `conversation_554a333e2d83406396118b652497cd13` 中得到：

| Turn | 固定问题 | 终态 | logical Provider dispatch |
|---|---|---|---:|
| 1 | 登录流程是怎样的？ | `FAILED / AGENT_REVIEW_LIMIT_REACHED` | 10 |
| 2 | 它失败时会记录什么？ | `FAILED / AGENT_NO_PROGRESS_LIMIT_REACHED` | 8 |
| 3 | 我指的是认证失败，不是权限不足。 | `FAILED / AGENT_MODEL_OUTCOME_UNKNOWN` | 4 |
| 4 | 那 401 和 403 分别由谁产生？ | `FAILED / AGENT_NO_PROGRESS_LIMIT_REACHED` | 4 |
| 5 | 总结一下，只保留用户能看到的流程。 | `FAILED / AGENT_MODEL_OUTCOME_UNKNOWN` | 5 |

五轮均为 `NOT_ACCEPTED / NOT_AUTHORIZED`，没有任何用户可见 Answer、Citation 或 Delivery。内部 evidence、Draft 和 Review activity
按真实终态保留，不能因未交付而抹去；其中 Turn 1 已形成三次独立 Review，但没有获得 APPROVED 或 Delivery Authorization。

terminal receipt `sha256:4ce07cbeca13665f5367992cd7d99509c5143d37c618e4d34bfb59ca1860c8a6` 密封 2 Conversation、
6 Turn、31 logical dispatch、request retry 0 和 Production Activation `NOT_EXECUTED`。Ark 为 11 logical dispatch，其中 verified TLS/
credential/HTTP success 8、credential-free pre-dispatch TLS failure 3、post-dispatch outcome unknown 0；DeepSeek 为 20 logical/HTTP
dispatch，credential success 20、TLS 2/2、connection reuse 18、post-dispatch remote disconnect/outcome unknown 2。两条 route 均低于
75 总上限；每 Turn UI 计数均低于 15。

随后新建 `conversation_4fb31c952a434cab8462492498d233c2`：初始 revision 1、`EMPTY CONTEXT`、message/Turn 0，identity 与旧对话不同。
“它呢？”以 `SUCCEEDED / APPLICATION_INPUT_CLARIFICATION / Provider dispatch 0` 要求明确组件、流程或请求；旧 Conversation 仍保持
revision 6、5 Turn、10 message 和原 Context digest，未被修改或继承。Browser console warning/error 为 0；5 个 artifact 主文件均为
`0600`；listener 已停止且 `127.0.0.1:8765` 端口关闭。terminal 文件 SHA-256 为
`1f71374f177b45175fa8f7522501337aaa76e0a6e886df4a7cb38d748516d152`。

## Earliest deviations

- Turn 1 的 DeepSeek fallback 对同一两个 Claim 连续返回 `FINDINGS`；Review message 自身却明确写出引用的源码“确认”“完全支持”Claim，
  甚至写出“no defect exists”。这是 Reviewer 正向判断没有结构化承载位、decision/Finding 语义无法重算的系统性合同偏差，不是应提高
  review fuse 的证据。
- Turn 2 的 Reviewer 正确要求补充 service implementation evidence；主 Agent 随后重复已执行的 literal `login` Search，并提交不在任何
  current-Turn Search citation 中的伪造 opaque locator。Broker 正确拒绝，两次无进展关闭 Turn。Turn 4 又连续三次提交同一个 `401`
  Search。Application 已知 action history 和合法 locator catalog，却没有把它们投影成 model-facing closed copy domain。
- Turn 3 的 Ark primary 在两个不同 no-hit Search 后遇到 credential-free TLS unavailable，隔离 DeepSeek fallback 首次 dispatch 又为
  outcome unknown；Turn 5 的 Ark primary 在 World Model 和 Source evidence 后返回 JSON 对象前附带长篇分析，closed adapter 正确以
  `STRUCTURED_OUTPUT_INVALID` 拒绝，隔离 DeepSeek fallback 随后 outcome unknown。零重试、outcome-unknown 关闭和 JSON fail-closed 均不得
  放宽或改写为质量结果。

## Disposition

本次 live run 永久保持 `FAIL / blocking`，新 Conversation isolation/clarification Case 保持 PASS。Tool proposal copy domain 由
`FINDING-010-116` 处置，Reviewer claim verdict 与 JSON-only contract 由 `FINDING-010-117` 处置；transport failures 作为外部执行事实保留。
本次 live grant 已消费，不授权任何重跑、successor Conformance 或 Production Activation。
