---
id: FINDING-010-111
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, source, ai, security, interface, operations, quality, project]
depends_on: [FINDING-010-110, SYS-ADR-018, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: systemic
disposition: preserve-second-live-five-turn-failure-and-separate-product-deviations-from-transport-failures
target: ITER-010-VERIFICATION
---

# FINDING-010-111：第二次真实五轮 Chat 仍全部失败，但新对话澄清已通过

## Authority and execution evidence

用户以 `codex-user-message:sha256:096a1bc724f89db2fd2ca59e47ad4807a0981209e27d13fca6884062a097de03`
授权 exact product commit `999616d24f793e139f20ea821c3069fdaff57a39` / tree
`ec3179c1efb5df02c77f4be1d60a5e694dcc7380` 和 `mall`
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` / tree
`047d79d8588b76013c260f3f1a9565707301a60a` 的 owner-private artifact、固定五轮 Chat 与新对话泄漏负测。授权继续排除
`src/main/resources`、credential values、hidden、Slice2/3 和 Production Activation，同 Provider request retry 为 0。

`run-036-chat-alpha` 在 listener 前保持 Source、credential、Provider、Conversation 和 Turn activity 为 0；Browser 刷新后显示 exact
product/source identity。固定五轮在同一 Conversation 中得到：

| Turn | 固定问题 | 终态 | logical Provider dispatch |
|---|---|---|---:|
| 1 | 登录流程是怎样的？ | `FAILED / AGENT_NO_PROGRESS_LIMIT_REACHED` | 6 |
| 2 | 它失败时会记录什么？ | `FAILED / AGENT_MODEL_OUTCOME_UNKNOWN` | 6 |
| 3 | 我指的是认证失败，不是权限不足。 | `FAILED / AGENT_NO_PROGRESS_LIMIT_REACHED` | 7 |
| 4 | 那 401 和 403 分别由谁产生？ | `FAILED / AGENT_MODEL_OUTCOME_UNKNOWN` | 3 |
| 5 | 总结一下，只保留用户能看到的流程。 | `FAILED / AGENT_MODEL_CALL_REJECTED` | 2 |

五轮仍没有 Answer、Citation、Review 或 Delivery，故 Chat/Quality/XD Gate 继续 FAIL。随后新建的 Conversation 使用不同 identity，初始
revision 1、消息/Turn/Work State 均为空；“它呢？”以
`SUCCEEDED / APPLICATION_INPUT_CLARIFICATION / Provider dispatch 0` 要求明确组件、流程或请求。旧 Conversation 没有被修改或继承，
`FINDING-010-109` 的泄漏负测修复取得首次真实 PASS。

terminal receipt `sha256:77988477bc8143658c78211761bd5b072b69ea7cc8f839eac806009b869ac0a7` 密封 2 Conversation、
6 Turn、24 logical dispatch、request retry 0 和 Production Activation `NOT_EXECUTED`。Ark 为 14 logical dispatch，其中 TLS/HTTP/
credential success 11、pre-dispatch TLS failure 3、post-dispatch outcome unknown 1；DeepSeek 为 10 logical dispatch，其中 HTTP/credential
9、TLS success 2、connection reuse 7、pre-dispatch TLS failure 1、post-dispatch outcome unknown 2。所有 artifact/receipt/SQLite 主文件均为
`0600`，Browser console warning/error 为 0，listener 已优雅停止且端口关闭。

## Earliest deviations

- Turn 1 的 DeepSeek isolated fallback 在大目录 SEARCH 后只剩一个 exact READ 名额；第一个 READ 成功，第二个及其重复请求被 Broker
  拒绝并连续 no-progress。`FINDING-010-110` 的单名额修复没有覆盖真实多文件工程流程，属于同 failure signature 复现，必须升级为架构
  职责处置，不能继续把保留数从 1 改成另一个题目常量。
- Turn 3 的 Ark primary 已取得 World Model、Search 和 Read observations 并形成 `RESPONSE_READY` Draft，但一个 affirmative Claim 同时把
  `BOUNDARY` observation 当作 support。closed decoder 正确以 structured-output invalid 拒绝，Reviewer 未被调用；DeepSeek fallback 随后
  重复无命中的 literal search 并触发 no-progress。
- Turn 2/4/5 还包含独立 transport failure：pre-dispatch TLS unavailable、post-dispatch remote disconnect/outcome unknown，以及 TLS
  acquisition fuse 后的 integration hold。零重试和 outcome-unknown 关闭均按策略工作，不能把这些外部失败改写为答案质量或产品 PASS。

## Disposition

本次 live run 永久保持 `FAIL / blocking`，但新 Conversation leakage Case 更新为 PASS。Source scan/Turn total budget 的架构职责由
`FINDING-010-112` 处置；模型 Draft 可引用 observation domain 由 `FINDING-010-113` 处置。两项修复改变当前 model strategy/prompt/input
identity，旧 Ark/DeepSeek Conformance 不得继续资格化 successor；下一次 live 前必须先取得 fresh 双 Provider Conformance，再冻结新的 exact
product commit/tree、artifact 和 Session Authority。本次 grant 已消费，不授权任何重跑或 Production Activation。
