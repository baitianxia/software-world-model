---
id: ITER-010-RESULT-V-CHAT-EXPERIENCE-001-PDR005-DIRECTION-CANARY
kind: iteration-result
status: failed-direction-canary-and-scheduling-rework
authority: execution-evidence
owners: [product, engineering, quality, security, ai, interface]
depends_on: [ITER-010-PDR-005, ITER-010-PDR-006, ITER-010-PDR-007, ITER-010-SLICE-001, ITER-010-VERIFICATION, ITER-010-RESULT-V-COGNITION-ELIGIBILITY-001, SYS-ADR-017, SYS-ADR-018, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/conversational_engineering_tools.py, src/software_world_model/application_services/engineering_question_cognition.py, src/software_world_model/application_services/java_source_semantics.py, src/software_world_model/interface/engineering_chat_session_artifact.py]
tests: [tests/test_conversational_engineering_tools.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_question_cognition.py, tests/test_java_source_semantics.py]
iteration: ITER-010
case_id: V-CHAT-EXPERIENCE-001
case_verdict: FAIL
scheduling_verdict: DEEPSEEK_SCHEDULING_POLICY_FAIL
decision: REWORK
acceptance: NOT_ACCEPTANCE
production_activation: NOT_EXECUTED
---

# ITER-010 PDR-005 Direction Canary Result

## Verdict

`FAIL / REWORK / NOT_ACCEPTANCE`。唯一一次授权的 PDR-005 direction canary 已在真实 loopback Web、真实 Ark primary 与
ADR-017 条件式 DeepSeek fallback 上执行并停止。冻结的五个 Provider-eligible Turn 中只有未见结构题形成
`ACCEPTED` 答案；语义链的前两轮失败，第三轮只形成未回答实现流程的 `REVIEWED_LIMITATION`，未见购物车行为题也失败。因而
`V-CHAT-EXPERIENCE-001 / V-CHAT-001 / V-CHAT-QUALITY-001 / V-CHAT-XD-001` 均未通过。

该 run 还在北京时间 `2026-08-27 11:19–11:27` 高峰窗口执行 DeepSeek `18` 次 HTTP dispatch，且没有 fresh 官方检查、窗口判定或
exact peak override receipt；PDR-007 因而另判
`DEEPSEEK_SCHEDULING_POLICY_FAIL / NOT_DIRECTION_ACCEPTANCE_EVIDENCE`。这个调度 FAIL 与下述产品质量 first divergence 独立，二者均不
能由另一个局部 PASS 覆盖。

失败 Turn 保持 Conversation `ACTIVE`、完整历史可见；全新 Conversation 的“它呢？”在 Application 层澄清且 Provider dispatch 0，
故 Turn 隔离和 leakage 子 Gate PASS。该局部安全/交互通过不能追认为 Chat 或答案质量通过，也不解锁 comparison、hardening、full
regression、Slice2/3、hidden、Acceptance 或 Production。

## Exact candidate, input, and authority freeze

- product candidate：commit `a4bfd6acabc6d9ae8a8201f6f03cfa24b43765b8`，tree
  `8e1fdbb962bd9ec2b6812e28135e7ecefb074277`；clean detached worktree
  `/private/tmp/swm-iter010-canary.OvFUXe/candidate`；两处未接受 v7 dirty 文件未进入 candidate；
- project：`mall@0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`；Source 只允许 Java、README、POM 与
  `src/test/java`，所有 `src/main/resources`、配置凭据与写操作排除；
- World Model：Maven + Java ordered multi-Profile authority
  `sha256:bf8a416f6866bce7015946aac6ee2e19073d897ca33a76ffc76316f4eb643792`；
- Session Configuration `@2`：
  `var/iteration-010/slice-001/run-043-pdr005-direction-canary/session.json` /
  `sha256:b9e239b9c96b6e93c3fe69d3778adce6f5751f74de4e206aac5c99b99a539f90`；
- frozen inputs：同目录 `inputs.json` /
  `sha256:532ba616feb1fe84c95f3cfcd59321303678481c48c518dae0327105e350a94e`；启动后未修改；
- 用户明确外发授权本地 UTF-8 digest：
  `sha256:6a3fd9b7c2c2d6a2a89f9677bbd24f97d62fd2fda1df8fbcd3ed2d38ee897676`；Session 绑定
  `authorized_at=2026-08-27T03:18:23Z`、`expires_at=2026-08-27T07:18:23Z`。此前较宽的 direction grant
  `15a8f810…` 没有被当作敏感源码衍生内容外发授权；安全审批拒绝的首次启动命令没有创建 listener、credential resolution 或 dispatch；
- Ark qualification Result digest
  `sha256:10e4b875b933b12b848b8b08dafa7d59bc5770fb18ec0ae19f455a18ce9944e2`；DeepSeek qualification
  Result digest `sha256:85cfe117920bccd403c96578e42f49dc5eca1afcb551b20c707a14eb41e8dd3b`；HTTP retry 固定为 0。

## Browser-observed questions and outcomes

| Conversation / Turn | Frozen input | Browser result | Provider dispatch |
|---|---|---|---:|
| `conversation_697fed8e97204557b40e2d7a7785594f` / 1 | 管理员登录从用户名和密码到 token 的完整实现流程，并区分 World Model、Source 与 Unknown | `FAILED / AGENT_REVIEW_LIMIT_REACHED` | 13 |
| same / 2 | 用户名不存在或密码错误分别走到哪里；要求只基于当前对话继续 | `FAILED / AGENT_MODEL_OUTCOME_UNKNOWN` | 5 |
| same / 3 | 合并前两轮为维护者总结，列方法调用和未确认失败边界 | `SUCCEEDED / REVIEWED_LIMITATION`；只说明证据不足，未形成登录流程答案 | 5 |
| `conversation_3230f2363248492281ebe661eaa5dbd3` / 1 | `mall-portal` 的仓库内直接依赖 | `SUCCEEDED / ACCEPTED`；准确给出 `mall-security` 与 `mall-mbg`，并绑定 Maven Snapshot | 3 |
| `conversation_b76dced8576d48a181c6461bf1599d22` / 1 | 购物车数量更新组件、商品不存在/库存不足的状态与失败边界 | `FAILED / AGENT_MODEL_OUTCOME_UNKNOWN` | 2 |
| `conversation_57b5e37965c243b8ad7c0d74a57f31de` / 1 | 新 Conversation：“它呢？” | `SUCCEEDED / APPLICATION_INPUT_CLARIFICATION`；要求明确组件、流程或请求 | 0 |

五个 Provider-eligible Turn 合计为 `1 ACCEPTED + 1 REVIEWED_LIMITATION + 3 FAILED`。第一组在同一 Conversation 中保留了三轮消息与
Context revision，失败 Turn 也没有关闭 Conversation；但它没有形成用户可用的事实链，三个消息存在不等于语义 Chat 质量通过。两个未见
异质问题中只有结构题通过，行为/失败边界题失败。leakage probe 前后 Gateway root 计数均为 Ark 10、DeepSeek 18。

## First-divergence evidence

本次最早可重复偏差在 `Cognition projection/query`，不是 Web，也不是 Maven 结构知识缺失：

1. 登录题首个主 Agent 输出已经用英文 `evidence_need` 明确提出 admin login controller、security configuration 与 token generation，
   但密封的 `WORLD_MODEL_QUERY` action `arguments=[]`；实际 Cognition payload 的 query 仍是中文 original question。
2. Java Snapshot 实际存在
   `UmsAdminServiceImpl.login(String,String) -> String` 的 exact entity，source path 为
   `mall-admin/src/main/java/com/macro/mall/service/impl/UmsAdminServiceImpl.java`；live projection 却返回 36 项
   （29 ENTITY、3 BEHAVIOR、3 COVERAGE、1 UNKNOWN）而漏掉该 `login` 方法。命中的同类项主要是 `refreshToken`、
   `updateLoginTimeByUsername` 和无关方法关系，不能支持完整登录流程。
3. 随后的 literal Source search 检查 56 个文件后截断，只返回 20 项；前 17 项是生成模型中的 `loginType` 字段/criterion，最后 3 项才是
   `UmsAdminController` 的 `/login`、controller method 与 `adminService.login(...)`。Agent 最终只读取
   `UmsAdminController.java`、`UmsMemberLoginLog.java`、`UmsMemberLoginLogExample.java`，没有读取已被 controller 调用且决定行为的
   `UmsAdminServiceImpl.java`。
4. 未见结构题包含精确 `mall-portal` symbol，Maven Profile 在一次 World Model observation 后直接形成正确答案；这证明 Session binding、
   Web delivery 与窄结构投影本身工作，不能把失败归因于页面壳或整个 World Model 未装载。

因此本 run 反证了“只要 original-question Need 具备行为维度资格，当前 lexical projection 就足以把自然语言问题关联到相关 Java cognition”
这一隐含假设。Source path-relevance 没有修复上游遗漏，反而在宽 `login` 命中下把有限 scan/read 预算消耗到生成模型。Reviewer limit 与
transport outcome unknown 是独立下游失败，不能用来覆盖该 first divergence。处置见 `FINDING-010-138`。

## Provider, transport, and safety audit

- terminal：4 Conversation、6 Turn、28 logical dispatch、request retry 0；每个 Provider-eligible Turn 分别为
  `13/5/5/3/2 <= 15`，Ark `10 <= 75`，DeepSeek `18 <= 75`；
- Ark：10 logical dispatch、8 HTTP dispatch、10 TLS handshake attempt、8 success、2 credential 前 TLS failure、credential
  resolution `8/8`、outcome unknown 0、retry 0；
- DeepSeek：18 logical/HTTP dispatch、2 TLS handshake success、connection reuse 16、credential resolution `18/18`、
  `REMOTE_DISCONNECTED` outcome unknown 2、retry 0；
- 上述 DeepSeek dispatch 全部发生在冻结高峰窗口且没有 `DEEPSEEK_DISPATCH_ADMISSION@1`；这是当前审计中的调度违规，不因调用上限被
  遵守而变为合规；
- exact Source full read 只有三个上述 Java 文件；没有读取 `src/main/resources`，没有 Source write、credential value logging、hidden、
  Production Activation 或第二个 canary session；
- `session.json`、`inputs.json`、两个 Gateway、launch 与 terminal 都为 `0600`。terminal content digest
  `sha256:47911a98133acbe3fd1abe635be1df94e9ee89270922ac3e1d4aa78dd26eaaec`，file digest
  `sha256:941ddbe781bb9cc8b44291d03e7bd21880d26ef1f318b127b3adc9d507c13f1c`；Gateway file digests 分别为
  Ark `sha256:5290b9f0145581c6f0a62ec2afbf1834bfd1a307180950192ae3d54db00074d4`、DeepSeek
  `sha256:25398e4b32edd840e1e0a1b1422c7df7b527d45e01aeebfbf07faf432c771834`；
- listener 已在 probe 后优雅停止，`127.0.0.1:8765` 不再监听；Production 为 `NOT_EXECUTED`。

## Case disposition and remaining gate

| Case | Verdict from this Result | Reason |
|---|---|---|
| `V-CHAT-EXPERIENCE-001` | FAIL / REWORK | 页面与多轮历史可用，但真实语义链没有形成可用答案 |
| `V-CHAT-001` | FAIL / partial mechanics only | failed-Turn continuation 与新对话隔离成立，语义事实连续性未成立 |
| `V-CHAT-QUALITY-001` | FAIL | 3/5 Turn 失败，1/5 仅 Limitation；异质行为问题未回答 |
| `V-CHAT-XD-001` | FAIL | 没有一个获批答案组合问题相关 Java cognition 与 Source；结构题只用 Maven cognition |
| leakage sub-Gate | PASS | 新 Conversation 澄清、空 Context、Provider dispatch 0、计数不变 |
| run-level DeepSeek schedule | FAIL | 北京时间高峰 HTTP 18，且无 official-check/window/override receipt |
| `V-PREVIEW-002` | NOT-RUN | comparison、独立假设复核和用户方向决定均未发生 |

本次没有运行 full regression；这是 PDR-005/PDR-006 明确排除项，不是验证遗漏。后续 clean `03520eb…` 已通过本地 DeepSeek admission
Case，clean `3a6089f…` 又闭合 F138 的 semantic need 查询并冻结 successor；这些后继证据不追溯改写本 run。重新 live 前仍必须取得新的
exact one-shot grant，并在允许窗口用 current `@3` artifact 形成 fresh receipt。comparison、hardening 和 full regression 继续锁定，直到
用户作出允许它们的决定。
