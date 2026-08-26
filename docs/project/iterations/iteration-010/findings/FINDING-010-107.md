---
id: FINDING-010-107
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, source, ai, security, interface, operations, quality, project]
depends_on: [FINDING-010-106, SYS-ADR-018, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: systemic
disposition: preserve-first-live-five-turn-chat-failure-and-block-quality-gates
target: ITER-010-VERIFICATION
---

# FINDING-010-107：首次真实五轮 Engineering Chat 全部失败，新对话只隔离但未澄清

## Observation and authority

用户以 `codex-user-message:sha256:bec7f0796899a81422ea013a34e2e7f10121515a8c9f72503f75cbfc8121a662`
授权 exact product commit `eb835f58b75831fc6f2c5a2513a13f32bdb3f7fe` / tree
`e5508f17f99201876ecf932550e1bd30f67127d0` 和 `mall`
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` / tree
`047d79d8588b76013c260f3f1a9565707301a60a` 的 owner-private Session、固定
`127.0.0.1:8765` 五轮 Chat 与新对话泄漏负测。授权允许 published Maven World Model、Conversation Context、Work State、Agent/Reviewer
Ledger 和本轮需要的 Java/README/POM/Test evidence 按 Ark→DeepSeek 披露；`src/main/resources`、credential value、hidden、Slice2/3 与
Production Activation 明确排除，同 Provider request retry 固定为 0。

owner-private `run-035-chat-alpha` artifact 在 listener 前证明 Source read、credential resolution、Provider dispatch、Conversation 和 Turn
均为 0；artifact、launch/terminal receipt 与两个 Gateway SQLite 主文件最终均为 `0600`。Browser 控制台没有 warning/error，listener
随后收到正常停止并 exit 0。

## Execution evidence

同一 Conversation `conversation_fd2629d7a8464aed9e4782cf4737a932` 的五轮现场结果为：

| Turn | 固定问题 | 终态 | logical Provider dispatch |
|---|---|---|---:|
| 1 | 登录流程是怎样的？ | `FAILED / AGENT_NO_PROGRESS_LIMIT_REACHED` | 4 |
| 2 | 它失败时会记录什么？ | `FAILED / AGENT_NO_PROGRESS_LIMIT_REACHED` | 4 |
| 3 | 我指的是认证失败，不是权限不足。 | `FAILED / AGENT_NO_PROGRESS_LIMIT_REACHED` | 3 |
| 4 | 那 401 和 403 分别由谁产生？ | `FAILED / AGENT_MODEL_OUTCOME_UNKNOWN` | 4 |
| 5 | 总结一下，只保留用户能看到的流程。 | `FAILED / AGENT_NO_PROGRESS_LIMIT_REACHED` | 5 |

五轮没有一个 Answer、Citation、Review 或 Delivery 成功。terminal receipt
`sha256:7bf6a2553cb952db281e56d8c15924476359e522f26148fff082178a8d0ac1ba` 密封 2 Conversation、6 Turn、20 logical dispatch、retry 0 和
Production Activation `NOT_EXECUTED`。Ark 记录 13 logical dispatch，其中 verified TLS success / actual HTTP dispatch 为 11，另外 2 次在
credential resolution 和 HTTP 前以 TLS failure 关闭；DeepSeek 为 7 次 HTTP dispatch、connection reuse 5，其中 1 次
`REMOTE_DISCONNECTED / PROVIDER_OUTCOME_UNKNOWN`，没有 request retry。

“新对话”产生独立 `conversation_225f41e640874fd696d2ed0e44187869`，页面先显示 revision 1、`EMPTY CONTEXT`、无旧消息；这证明 transcript
隔离成立。随后提交省略指代“它呢？”时 Provider dispatch 保持 0，但结果是
`FAILED / AGENT_PRE_DISPATCH_REJECTED` 和通用熔断文案，而不是要求用户明确对象。因此泄漏负测只通过“没有继承旧 Conversation”和“零
dispatch”，没有通过澄清要求。

## Root-cause evidence

- live Source Profile 合法登记 519 个 Java entry；每次 `SOURCE_SEARCH` 只按既有顺序读取安全上限 64 个文件，match count 始终为 0，随后
  返回 `PARTIAL / SOURCE_FILE_FUSE_EXHAUSTED / SOURCE_RESULT_HAS_NO_ITEMS`。达到上限是正确的安全关闭，不能调高来改写结果。
- model-facing Chat tool catalog 把 query 描述为 literal **或 semantic** proposal，Primary Agent 因而持续提交中文或英文语义描述；Worker
  实际只做大小写敏感的 literal line match。模型在已经收到 Boundary 后仍处于 `INVESTIGATING` 并重复 search，最终触发 no-progress。
- Session Disclosure Authority 只允许五个 Provider Turn。泄漏 probe 是第六个 Application Turn；由于没有可信 pre-dispatch referent policy，
  路由仍尝试创建 Provider attempt，随后被 Session Authority 拒绝。零 dispatch 来自预算拒绝，不是正确的歧义识别。

## Decision and disposition

`V-CHAT-EXPERIENCE-001`、`V-CHAT-001`、`V-CHAT-QUALITY-001` 和 `V-CHAT-XD-001` 均更新为 `FAIL / blocking`；Access-only
`V-ALPHA-ACCESS-001` 的既有 PASS 不变。该 run 永久保持失败证据，不能由后续修复追认。

Source literal-search 契约与 bounded candidate ordering 由 `FINDING-010-108` 处置；新 Conversation 的 binding-owned pre-dispatch
澄清由 `FINDING-010-109` 处置。修复后的代码只能成为新的 local candidate；再次外部验证必须绑定新的 exact product commit/tree、artifact
和 Session Authority，不复用本次 grant 或 Provider input。
