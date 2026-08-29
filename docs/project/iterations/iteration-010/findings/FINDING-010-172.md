---
id: FINDING-010-172
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, source, ai-infrastructure, quality]
depends_on: [FINDING-010-169, FINDING-010-170, FINDING-010-171, ITER-010-PDR-012]
code: [src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/application_services/conversational_engineering_tools.py, src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_tools.py, tests/test_conversational_engineering_model.py, tests/test_engineering_question_answering.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: revalidate-prior-delivered-full-source-as-current-turn-evidence
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-172：跨 Turn 只禁止旧证据复用而没有当前 Turn 重验入口会制造虚假 Unknown

## Observation

fresh `run-062-mvp-experience` 绑定 exact product
`64b821238e02d9cd80e4f3e28bfbac12d8e75a7a / 56fa2a0cb41520a2556e52f66b8442a3ba6abe1b` 与 mall exact Source
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7 / 047d79d8588b76013c260f3f1a9565707301a60a`。冻结 Turn 1 以 7 次 Ark
dispatch 得到 `SUCCEEDED / ACCEPTED`：页面显示自然中文答案、41 个 Citation、fresh Review 和 Delivery Authorization；Browser 实际展开的
完整 `UmsAdminController.java` Citation 显示 exact source revision、content digest 与 citation digest，完整
`UmsAdminServiceImpl.java` 也进入已交付 Citation 集合。

同一 Conversation 的冻结 Turn 2 问“用户名不存在”和“密码错误”是否写入上一轮所指登录日志。模型从相关 Context 正确解析指代，且首个
Work State 已提出与源码一致的待验证假设：两类异常均发生在 `insertLoginLog` 前。但 current Turn 没有任何读取上一轮 exact full-source
Citation 的合法 opaque locator；旧 Observation IDs 按合同未披露，旧 Answer 也正确地没有事实权威。Agent 因而依次以
`insertLoginLog / Asserts.fail / passwordEncoder` 做三次 literal content SEARCH，分别只得到无 item 的 PARTIAL boundary，最终耗尽 64-file
whole-Turn fuse。它只能交付 `SUCCEEDED / REVIEWED_LIMITATION`，错误地声称两个失败分支均无法确认，且页面 Citation 为 0。该结果技术闭合，
但相对当前 exact Source 是重大质量错误，因此三轮开发体验链仍未形成，不能提交 Turn 3 或宣称候选/MVP。

## Evidence and first divergence

- Turn 1 的已交付 Answer/Citation/Review refs 分别为
  `agent_answer_f5c8bc8c62ec4b7498ac312e8a7fb8af`、41-item Turn Citation projection、
  `agent_review_c0d6e6d8b340472ab659849d5305a9aa`；其中完整 Service source 已包含
  `loadUserByUsername → passwordEncoder.matches/Asserts.fail → generateToken → insertLoginLog` 的可核对实现。
- Turn 2 的 7 个 Ark call 均为 completed object output，input token 从 `7,228` 到 `58,283`；fresh Reviewer 对 limitation 通过，但 Package
  只有 World Model support/boundary 和三次 Source Search boundary，没有 full Source support，因此 Citation=0。问题不在 structured output、
  route、network、Reviewer identity 或 Citation UI。
- Conversation Context 只携带上一轮自然答案与 reviewed conclusion ref，previous Work State 明确投影
  `prior_turn_observation_reuse_authorized=false`。这正确关闭了“把旧答案/Observation 当事实”的路径，却没有实现
  `SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 已要求的“历史 exact Evidence 作为 candidate，经当前 Turn 重新校验并纳入当前
  Package”。最早偏差位于 Application/Source Tool boundary，不是 Agent 最终 limitation 文案。
- 优雅停止后的 terminal receipt digest 为
  `sha256:0b0221beb41e09eeab297bfa211e364dc6887f496d366b7ec1f94b625269c135`，密封 Conversation/Turn `1/2`、Ark dispatch
  `14`、DeepSeek dispatch `0`、request retry `0`、human approval request `0` 和 Production `NOT_EXECUTED`。

## Classification and disposition

这是 `system-contract`：修复新增的是跨 Turn Evidence 重新取得的通用能力与安全语义，不是登录题、类名、成员名或搜索排序特判。

1. Application 只从同一 Conversation 的成功、已获 Delivery Authorization Turn 中选择已交付的 full-resource Source Citation；必须匹配
   current repository revision，并按 canonical resource 去重、最多 16 项。旧 Citation 只贡献 path/content/modality/origin identity，不进入
   current observations、Package 或 Claim copy domain。
2. Source Tool 使用 current exact Request、attempt、Source Profile、evidence class 与 path 重新签发 direct opaque locator；模型只能从
   `tool_reference_policy.source_read_options` 复制 reference，不能提交 path。相关 follow-up 应先读该有界 locator，再考虑消耗 directory
   SEARCH fuse。
3. Broker 在 READ 时重新验证 allowlist/Profile/revision/operation/budget；Worker 返回的 full path、coverage、modality 和 content digest 必须
   与 prior exact Citation 一致，否则失败关闭。成功后才产生新的 current-Turn SUPPORT Observation、Ledger Result、Citation 和 Package
   closure；旧 Answer/Review/Observation 仍没有事实权威。
4. preissued direct locator 也属于“未读 exact locator”：只剩一个 source-file slot 时，model-facing catalog 与 Broker 都必须保留 READ、拒绝
   SEARCH。新 Conversation 没有 prior Turn candidate；失败 attempt、search line hit、World Model citation 与不同 revision 均不能生成该能力。

该修复沿用 current `conversational-engineering-agent@8 /
conversational-engineering-agent-no-tools-prompt@8 / ENGINEERING_AGENT_PRIMARY_INPUT@8` 协议族；现有
`tool_reference_policy.source_read_options` 与 SOURCE_READ output shape 不变，每次 call 仍由新的 exact prompt/input/request digest 区分字节。
确定性测试证明：第一 Turn 先 search+read 并只交付
full-resource Citation，第二 Turn 无 SEARCH 直接重验同一文件；current Ledger 记录 prior Citation origin，但 Source file usage 仅 `1/64`，
新 Citation reference 与旧 reference 不同而 content digest 相同。Tool/Model/Engineering QA 组合 `84/84` PASS；这是本地证据，外部 dispatch
为 0；相关 Agent/Tool/Model/routing/Browser/candidate/launcher/runtime/artifact/CLI 组合 `94/94` PASS，文档 `578` 项检查 PASS，plan
snapshot 与 candidate diff 均 PASS。这些结果不追认 run-062。fresh Browser successor 必须使用新的 clean product/run identity 重新执行冻结
三轮，问题 4/5 继续保持 unseen。
