---
id: FINDING-010-200
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, source, ai, quality, operations]
depends_on: [FINDING-010-199, ITER-010-PDR-012, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_engineering_question_answering.py, tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: reject-path-navigation-literals-before-content-search-and-require-replan
target: SYS-CONTRACT-SOURCE-ARTIFACT
---

# FINDING-010-200：run-078 已贯通 Ark→DeepSeek，目录名却被当成源码正文检索词并触发假限制

## Observation

fresh Browser `run-078-mvp-experience` 绑定 exact product
`37d406a567f928521676c54a8d61e697638338d1 / 6a691538bb4af5d5b53eeda463ca3e30b784a45f` 与 mall exact Source
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7 / 047d79d8588b76013c260f3f1a9565707301a60a`，按冻结顺序提交 5 个 Turn。
它首次真实证明 current availability-only route 可在 Ark typed pre-HTTP unavailable 后自动进入已获周末闲时 admission 的 DeepSeek；整个
Session 没有人工重复审批或 retry。

第二题询问 `mall-portal` 普通订单创建时优惠券失败的副作用。Ark 首个 call 在 HTTP 前形成可信 unavailable，DeepSeek 随即执行 4 个 call，
Turn 最终交付 `SUCCEEDED / REVIEWED_LIMITATION`。但 Primary 唯一 Source 动作把授权目录段 `mall-portal` 直接作为 case-sensitive content
literal。Worker 为此检查 56 个 SOURCE 文件、命中 0，并形成 operation-local `SOURCE_SEARCH_FILE_LIMIT_REACHED`；模型随后在 action budget
仍可用、Source 仍可用时直接声称只能知道 Maven module，未改用源码中可能逐字出现的业务/类型/方法 literal。第三题在同一 Conversation
使用 `generateOrder` / `OmsPortalOrderService` 已能继续源码检索，证明失败不是 Source 授权、Profile、exact revision 或 DeepSeek 能力缺失。

## Evidence and first divergence

- Turn 1 角色重分配题执行 Ark 11 次，前 10 次完成，第 11 次 post-dispatch
  `REMOTE_DISCONNECTED / PROVIDER_OUTCOME_UNKNOWN`；页面如实 `FAILED / AGENT_MODEL_OUTCOME_UNKNOWN`，DeepSeek 0。未知外部结果不是
  可信 unavailable，故未 fallback 正确。
- Turn 2 优惠券题执行 Ark 1 次 typed pre-HTTP unavailable，随后 DeepSeek 4 次完成；页面交付
  `SUCCEEDED / REVIEWED_LIMITATION` 和独立 Delivery Authorization。DeepSeek action `SOURCE_SEARCH` 的 exact query 为 `mall-portal`；其结果记录
  `examined_file_count=56 / match_count=0 / SOURCE_SEARCH_FILE_LIMIT_REACHED`，下一 call 立即起草限制说明。
- Turn 3 同 Conversation 追问订单项批量插入失败：Ark 4 次完成后 1 次 typed pre-HTTP unavailable，DeepSeek 第 1 次真实 dispatch 又以
  post-dispatch unknown 关闭；页面 `FAILED / AGENT_MODEL_OUTCOME_UNKNOWN`，没有 retry 或再次 route，正确保留未知结果。
- Turn 4 在 fresh Conversation 提交“这些失败也会回滚吗？”，Application 以
  `SUCCEEDED / APPLICATION_INPUT_CLARIFICATION`、Provider dispatch 0 关闭，证明 Conversation 隔离仍成立。
- Turn 5 的 `mall-search` Elasticsearch 导入/更新/删除题以 Ark 7 次交付 `SUCCEEDED / ACCEPTED`、9 个 Citation 和独立 Delivery
  Authorization；答案精确识别 Controller、数据库读取、`EsProduct` document、repository
  save/delete 及远端 ES 一致性边界。
- terminal receipt digest 为 `sha256:085fb06982c67e84a205c4f37d5c7a2e8ff5aa0f6754601aac125926a5233a7a`，terminal 文件
  SHA-256 为 `0370ec0a1a6db1d03b5a8cbcd38e2a3573762a7970b00cb1a50bb218826de289`；它密封 4 Conversation、5 Turn、29 Provider
  dispatch、human approval request 0、retry 0 与 Production `NOT_EXECUTED`。Ark 为 24 dispatch：21 completed、2 typed pre-HTTP
  unavailable、1 post-dispatch unknown；DeepSeek 为 5 dispatch：4 completed、1 post-dispatch unknown。DeepSeek admission 为
  `ALLOWED_OFF_PEAK`，命中 `SATURDAY-SUNDAY 00:00-24:00`。
- turn-scope 与 Session config 文件 SHA-256 分别为
  `f5483f857933ef7c7da372a83651f85825efa692eb02b6437d45e6fdcde6a480` 和
  `e49085ade73e2a8b5b52079b833ae7f4b80a17b8638d89b0f0dbc5fc37d2f594`；public Source Session authority digest 为
  `sha256:76e0268e9376c34052d5b1e7b27cf3bec7c31007fd6c4b518c676c2d78ff5677`。
- first model defect 是把 Source scope 名当作 content literal；first systemic divergence 是 Broker 已持有 evidence-class exact allowlist，
  却仍把等于其中目录段的 query 编译给 Worker并消费 56-file scan。run-078 真实验证了 typed pre-HTTP fallback，但没有触发新建的 sealed
  HTTP-status availability 路径；后者仍只有合同测试证据，不能冒充 live 覆盖。

## Classification and disposition

这是 `system-contract / systemic` Finding；修复任何工程、模块名、目录层级、业务词、语言、Provider 或冻结问题，不按 `mall-portal` 特判。

1. content `SEARCH` query 必须是可能在目标 evidence 正文逐字出现的短 literal；若它精确等于 current evidence-class allowlist 的一个
   canonical path segment（module、directory 或 file name），Broker 必须在 Worker、file/byte usage 和 locator 签发前以
   `SOURCE_SEARCH_QUERY_EQUALS_PATH_SEGMENT` 拒绝。路径仍只是导航 metadata，不能因处于授权范围就取得正文证据资格。
2. 该拒绝是 operation-local、无 Worker evidence 的可重规划 Boundary，不是 Source authorization denial、whole-Turn fuse 或 Provider
   unavailable。它不消费 Source file/byte budget，也不扩大 allowlist、Profile、revision、operation 或 action budget。
3. Primary input 必须投影 sealed latest Broker decision。只要 Source action 仍合法且 completion policy 仍要求补证，该被拒 Search 不满足
   Source follow-up；同一 query 已进入 exact repetition denylist，Primary 必须选择另一个来自问题、Cognition、Observation 或 Finding 的
   source-native content literal，不能用该拒绝交付假 Limitation。
4. Broker guard 与 Primary completion policy 分层闭合：前者独占权限和执行前编译，后者只负责根据受信 Boundary 重规划；模型仍没有 path、
   Repository、FS、Shell、网络、凭据或 write authority。两个直接回归及两份完整受影响测试文件 `82/82` PASS，外调 0；fresh exact
   Browser successor 必须复验冻结五题，run-078 不取得质量或 MVP PASS。
