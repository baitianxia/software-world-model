---
id: FINDING-010-130
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, source, ai, security, interface, operations, quality, project]
depends_on: [FINDING-010-129, SYS-ADR-018, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: systemic
disposition: preserve-seventh-live-three-of-five-limited-responses-and-isolated-new-conversation-pass
target: ITER-010-VERIFICATION
---

# FINDING-010-130：第七次真实五轮 Chat 仍为 3/5 受限响应，新对话泄漏负测通过

## Authority and artifact preparation

在 `FINDING-010-129` 双资格均 PASS 后，同一用户授权被收窄为 exact product
`3b8d09c71796e3c9b91ec6a9ea21697497319bbc` / tree `6728a5ad63bedf65b1315cb7d7fdf27f111dc0d9`、
`mall@0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` / tree `047d79d8588b76013c260f3f1a9565707301a60a` 的
owner-private `run-042-chat-alpha` Session。Session authorization digest 是本地密封的 exact user-message UTF-8 digest
`sha256:df3cfe58d7a728899e7294a0c26ced0fb9e175f16334a904a1d70ca345d40ee9`。

Session config 文件 SHA-256 为 `6d7f07509df62e8aa1ffc0dbeed060ec7b65791ae9580b77b29da22a22585dc3`；launch preparation、
session runtime 与 terminal receipt digest 分别为 `sha256:f0a0c7f07be97c3c7a99949ef79bc133b504ae2d3430842fca3ffe977282212e`、
`sha256:9eff630dc5be34695a71543b5004d3003c51beb603ba3ed96bba2b25bbb938a9` 与
`sha256:201f984bc08aa68e640a0b3b431787e78f6b3aaa2354f9073766767a180bab5b`。它固定 Ark→DeepSeek、五轮问题、每
Turn/Provider 15 dispatch、每 Provider 总计 75、同 Provider retry 0，并排除 `src/main/resources`、credential values、hidden、
Slice2/3 和 Production Activation。

## Five-Turn execution and leakage probe

固定五轮在同一 `conversation_b8bb4e3d07124a7e8e3aebb75843f1a3` 中得到：

| Turn | 固定问题 | 终态 | logical Provider dispatch |
|---|---|---|---:|
| 1 | 登录流程是怎样的？ | `FAILED / AGENT_REVIEW_LIMIT_REACHED` | 15 |
| 2 | 它失败时会记录什么？ | `SUCCEEDED / REVIEWED_LIMITATION` | 9 |
| 3 | 我指的是认证失败，不是权限不足。 | `SUCCEEDED / REVIEWED_LIMITATION` | 6 |
| 4 | 那 401 和 403 分别由谁产生？ | `SUCCEEDED / REVIEWED_LIMITATION` | 6 |
| 5 | 总结一下，只保留用户能看到的流程。 | `FAILED / AGENT_MODEL_CALL_REJECTED` | 7 |

Turn 2—4 都只交付与当时 Package 边界一致的 Limitation：当前 Evidence 未能确认失败日志或 401/403 producer；它们不能称为产品质量正确
或完整，因为授权源码中实际存在相关事实而调查没有取得。Turn 1 没有交付登录流程，Turn 5 没有交付用户可见总结。因此技术终态仍为
3/5，主 Chat/Quality 继续 `FAIL / blocking`。旧 Conversation 最终 revision 6，Context digest 为
`sha256:a15d6aba3d32c9f4d68dc83611dfc13a6ff6a09ce65986001a287e88a0f37a45`。

随后新建 `conversation_1a0fd0d83a6c4fb3bf7aff8c2892c740`：初始 revision 1、`EMPTY CONTEXT`，Context digest
`sha256:19ccd513ed1ac3124730ae305b7c568783bd4a8c526ca8eff3cb222c6419b5db`。“它呢？”以
`SUCCEEDED / APPLICATION_INPUT_CLARIFICATION / Provider dispatch 0` 要求用户明确对象；没有继承旧 Conversation 的 referent、消息或
Work State。提交前后 Ark Gateway 行计数保持 `12 manifest / 10 output / 12 isolation receipt`，DeepSeek 保持 `31/31/31`，泄漏负测为
PASS。

terminal receipt 密封 2 Conversation、6 Turn、43 logical dispatch、request retry 0 和 Production Activation `NOT_EXECUTED`；文件
SHA-256 为 `74456d732d97af7d2de63f9993ef82bb053bf9317f3883113e8ed1cec4bb2e9e`。Ark 12 logical dispatch 中 10 次到达 HTTP，2 次为
credential-free pre-dispatch TLS failure；DeepSeek 31 次全部到达 HTTP，跨两个 verified TLS session 复用连接 29 次，双方
post-dispatch outcome unknown 均为 0。Session、launch、terminal 与 Conformance artifact 均为 `0600`，Browser console 无
warning/error，listener 已正常停止且端口关闭。

## Observed symptoms, unverified hypotheses and disposition

- Turn 1 三次 Reviewer Finding 依次要求补充当前问题未要求的失败状态/响应结构、扩大到全部认证内部步骤，再修正无证据的 HS512
  算法声明。最后一项是有效 Claim defect，但前两项把 completeness 扩到 exact current request 之外，使 15-step fuse 在最后一个修正
  Draft 后、fresh Review 前耗尽。
- Turn 3 依次搜索 `AuthenticationException`、`BadCredentialsException` 与 `AuthenticationFailureHandler`，Turn 4 搜索 `401` 与
  `403`。这些 content-only 通用词在 64-file bounded scan 中未命中；真实授权 Java 范围包含可按 path relevance 提前的工程 type/handler
  symbols，但 Primary input 没有投影 Worker 的 `QUERY_PATH_RELEVANCE_THEN_CANONICAL@1` 候选策略，模型无法据此管理有限扫描预算。
- Turn 5 Reviewer 把“只保留用户能看到的流程”扩成必须取得前端 page navigation/form rendering/UI feedback；当前授权 Evidence 范围没有
  前端层，且用户没有要求前端实现细节。successor 因此继续无效拓宽检索，最终以 model-call rejection 失败关闭。

上述是 run-042 中直接观察到的症状，不足以命名 first divergence。`FINDING-010-132/133` 的后续复核又证明唯一 World Model input 只有
Maven 结构、Agent 未取得授权来源中已有的决定性行为事实，Reviewer 还批准了不完整 Limitation。因而 run-042 必须被归类为多层故障；
查询排序与 Reviewer materiality 只能作为待反事实验证的假设，不能直接形成根因或 current System Contract。

本次 live 永久保持 `three-of-five reviewed limitations / overall FAIL`，新 Conversation isolation/clarification 保持 PASS。
`FINDING-010-131` 的 exact-request Reviewer materiality 与 Source query candidate-ordering projection 已降级为未接受症状实验；当前处置
改由 `FINDING-010-132/133` 和 `ITER-010-PDR-005` 的认知资格、逐层归因门拥有。该一次性 grant 已消费，不授权 v7 Conformance、
artifact/Browser 重跑或 Production Activation。
