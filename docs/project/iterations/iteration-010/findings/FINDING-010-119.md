---
id: FINDING-010-119
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, source, ai, security, interface, operations, quality, project]
depends_on: [FINDING-010-118, SYS-ADR-018, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: systemic
disposition: preserve-fourth-live-one-of-five-limitation-and-isolated-new-conversation-pass
target: ITER-010-VERIFICATION
---

# FINDING-010-119：第四次真实五轮 Chat 仅 1/5 形成受限响应，新对话泄漏负测通过

## Authority and execution evidence

在 `FINDING-010-118` 双资格均 PASS 后，同一用户授权被收窄为 exact product
`743942d2593615c5c481110465d7d7faaf41d958` / tree `748902ce407c434e10f4926cf84b1240a2666424`、
`mall@0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` / tree `047d79d8588b76013c260f3f1a9565707301a60a` 的
owner-private `run-038-chat-alpha`。Session authorization digest 为
`sha256:338979f81e29b0d53ddcc86fc5d35cc3a78f6cd671d977a864b5142d62dc352a`，config 文件 SHA-256 为
`b909c2538249027238530ee0b6b69b28a2e140dcd4d8d3e08a333d425cb71ba2`。它固定 Ark→DeepSeek、五轮问题、每
Turn/Provider 15 dispatch、每 Provider 总计 75、同 Provider retry 0，并排除 `src/main/resources`、credential values、hidden、
Slice2/3 和 Production Activation。

固定五轮在同一 `conversation_36eba3cb41cb451b9eb6329a0c5a5039` 中得到：

| Turn | 固定问题 | 终态 | logical Provider dispatch |
|---|---|---|---:|
| 1 | 登录流程是怎样的？ | `FAILED / AGENT_NO_PROGRESS_LIMIT_REACHED` | 8 |
| 2 | 它失败时会记录什么？ | `FAILED / AGENT_NO_PROGRESS_LIMIT_REACHED` | 6 |
| 3 | 我指的是认证失败，不是权限不足。 | `FAILED / AGENT_MODEL_OUTCOME_UNKNOWN` | 2 |
| 4 | 那 401 和 403 分别由谁产生？ | `FAILED / AGENT_NO_PROGRESS_LIMIT_REACHED` | 8 |
| 5 | 总结一下，只保留用户能看到的流程。 | `SUCCEEDED / REVIEWED_LIMITATION` | 5 |

Turn 5 诚实说明当前 Source 证据不足，并经 fresh Review 与 Delivery Authorization 交付；它不是用户所需流程答案，因此五轮 Chat/Quality
仍为 `FAIL / blocking`，不能把 1 个技术成功 Turn 记为 canary PASS。旧 Conversation 最终为 revision 6、5 Turn、10 message，Context
digest 为 `sha256:f6194a9d0ae016310a5edba940900634f5953f68e882eaa43dbc939134d2c03c`。

随后新建 `conversation_409bc8e5e71441e1afdc13d948cbe6fb`：初始 revision 1、`EMPTY CONTEXT`，Context digest
`sha256:578dcc88ce1eb4aa7972facd9fb241e4cd90a8160882d103e25f1b373b5aca9d`。“它呢？”以
`SUCCEEDED / APPLICATION_INPUT_CLARIFICATION / Provider dispatch 0` 要求用户明确对象；没有继承旧 Conversation 的 referent、消息或
Work State，泄漏负测为 PASS。

terminal receipt `sha256:89b42e466989118588fddf41d094284e68e13a716a9ec68c3ba527f2adc471ae` 密封 2 Conversation、
6 Turn、29 logical dispatch、request retry 0 和 Production Activation `NOT_EXECUTED`；文件 SHA-256 为
`e4573196fdaaf2915888e46f222d6087925b0d78392e5ea4190deb8756739fe6`。Ark 16 logical dispatch 中 12 次到达 HTTP，4 次为
credential-free pre-dispatch TLS failure；DeepSeek 13 次到达 HTTP，1 次 post-dispatch remote disconnect/outcome unknown，均未重试。
所有 artifact 主文件为 `0600`，listener 已正常停止且端口关闭。

## Earliest deviations and disposition

- Source Search 的 Citation catalog 把同一 canonical resource 的多个 line locator 暴露为不同 `SOURCE_READ` option。模型可合法选择同一
  文件的另一行 reference；Broker file fuse 已消费时，这些 option 仍停留在 model-facing legal domain，造成无效行动。
- 一个 no-hit Search 可以消费整个 Turn 的 Source file capacity；后续不同 literal 虽不构成 exact action repetition，却已不可能取得新
  Source evidence。连续两次无进展后 Application 直接失败，没有给主 Agent 一次只基于现有 SUPPORT/BOUNDARY 形成 Answer 或诚实
  Limitation、再经 fresh Review 的机会。
- Turn 5 证明现有 Limitation/Review/Delivery 路径可用；所以修复对象是 legal action domain 与 no-progress completion transition，不是提高
  Source、Agent、Review、Provider 或 retry fuse。

本次 live 永久保持 `one-of-five reviewed limitation / overall FAIL`，新 Conversation isolation/clarification 保持 PASS。前两项分别由
`FINDING-010-120` 和 `FINDING-010-121` 处置。该一次性 grant 已消费，不授权 v4 Conformance、artifact、Browser 重跑或 Production
Activation。
