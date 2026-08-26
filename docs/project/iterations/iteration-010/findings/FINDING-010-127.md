---
id: FINDING-010-127
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, source, ai, security, interface, operations, quality, project]
depends_on: [FINDING-010-126, SYS-ADR-018, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: systemic
disposition: preserve-sixth-live-three-of-five-responses-and-isolated-new-conversation-pass
target: ITER-010-VERIFICATION
---

# FINDING-010-127：第六次真实五轮 Chat 提升到 3/5，新对话泄漏负测通过

## Authority and artifact preparation

在 `FINDING-010-126` 双资格均 PASS 后，同一用户授权被收窄为 exact product
`6e97bc1c0c02be858212c39da11ac42e099c365e` / tree `fd54821e212b3022e318436d9e96b93af11505c6`、
`mall@0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` / tree `047d79d8588b76013c260f3f1a9565707301a60a` 的
owner-private `run-041-chat-alpha` Session。Session authorization digest 是本地密封的 exact user-message UTF-8 digest
`sha256:bed1ccdca788bfaad0c1f8581f538b19d7007da81388a8c8763968f6fdbce8c6`。

Session config 文件 SHA-256 为 `33d7a7abedfb0231a697a67533d4147d42d356a35bc3088776c2dc9e1d732d09`；launch preparation、
session runtime 与 terminal receipt digest 分别为 `sha256:9b572741c0b9e0408015ac5aa0621e089233edbd6e677bbe50ab02cc057ebd24`、
`sha256:da097b5e64cec065927e9ced1263243596f70c1cecb33cad15d6fe3b37adf5eb` 与
`sha256:20efa9280f328fcd7caa3a328c3d84e8961c0738dfafd17283bd82bbedb11010`。它固定 Ark→DeepSeek、五轮问题、每
Turn/Provider 15 dispatch、每 Provider 总计 75、同 Provider retry 0，并排除 `src/main/resources`、credential values、hidden、
Slice2/3 和 Production Activation。

## Five-Turn execution and leakage probe

固定五轮在同一 `conversation_e37f83e35ac445719f3219cd84273c38` 中得到：

| Turn | 固定问题 | 终态 | logical Provider dispatch |
|---|---|---|---:|
| 1 | 登录流程是怎样的？ | `SUCCEEDED / ACCEPTED` | 8 |
| 2 | 它失败时会记录什么？ | `FAILED / AGENT_MODEL_CALL_REJECTED` | 3 |
| 3 | 我指的是认证失败，不是权限不足。 | `SUCCEEDED / REVIEWED_LIMITATION` | 8 |
| 4 | 那 401 和 403 分别由谁产生？ | `SUCCEEDED / REVIEWED_LIMITATION` | 7 |
| 5 | 总结一下，只保留用户能看到的流程。 | `FAILED / AGENT_MODEL_CALL_REJECTED` | 2 |

Turn 1 首次形成经 fresh Review/Delivery 的登录流程 Answer；Turn 3/4 则诚实说明本次受限证据不能确认认证失败日志以及 401/403 的具体
产生组件。三轮技术响应是相对 run-040 的真实增量，但固定五轮要求每轮成功，且 Turn 5 没有交付用户可见流程总结，因此主
Chat/Quality 仍为 `FAIL / blocking`。旧 Conversation 最终 revision 6，Context digest 为
`sha256:a3bb31d415719ccc6809b4912c4df56f94ae13fbf9b28e54940b13936cfb08ab`。

随后新建 `conversation_95e30c56ff9e47748ff156cdba565716`：初始 revision 1、`EMPTY CONTEXT`，Context digest
`sha256:4a556a7744b19a81b55a06f432faba326b588e52cb5d4e2ea3d2b5d9c32c7676`。“它呢？”以
`SUCCEEDED / APPLICATION_INPUT_CLARIFICATION / Provider dispatch 0` 要求用户明确对象；没有继承旧 Conversation 的 referent、消息或
Work State，泄漏负测为 PASS。

terminal receipt `sha256:20efa9280f328fcd7caa3a328c3d84e8961c0738dfafd17283bd82bbedb11010` 密封 2 Conversation、
6 Turn、28 logical dispatch、request retry 0 和 Production Activation `NOT_EXECUTED`；文件 SHA-256 为
`8ba75fa201083b08ea1f966193081e235b51660016bd671cefc98313ef577fa8`。Ark 12 logical dispatch 中 7 次到达 HTTP，5 次为
credential-free pre-dispatch TLS failure；DeepSeek 16 次全部到达 HTTP，复用同一 verified TLS connection 15 次，双方 outcome unknown
均为 0。所有 artifact 文件为 `0600`，listener 已正常停止且端口关闭。

## Earliest deviation and disposition

- Turn 2 首个 DeepSeek step 已执行 `SOURCE_SEARCH`，第二个 step 又逐字提交相同 evidence class 与 query。Primary input 虽在
  `tool_reference_policy` 列出 prior action 和三个未使用 Source Read locator，但对应 `tool_catalog` 参数位置没有直接投影禁止值；closed
  decoder 正确以 exact action repetition 拒绝，没有执行第二次 Source 操作。
- Turn 5 的 current Turn observations 与 SUPPORT copy domain 都为空，但 `completion_policy.allowed_response_kinds` 仍列出 `ANSWER`。
  DeepSeek 因而复述旧 Conversation 答案并生成三个没有 support ID 的 Claim；Gateway/decoder 正确密封为
  `STRUCTURED_OUTPUT_INVALID`，没有把 prior Answer 当作 current Turn Evidence。

本次 live 永久保持 `three-of-five technical responses / overall FAIL`，新 Conversation isolation/clarification 保持 PASS。两个最早偏差由
`FINDING-010-128` 处置；它不删除或放宽 decoder、Evidence、Source、Agent、Review、Provider、retry、fallback 或 wall-time
校验。该一次性 grant 已消费，不授权 v6 Conformance、artifact/Browser 重跑或 Production Activation。
