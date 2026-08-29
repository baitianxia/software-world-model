---
id: FINDING-010-177
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai-infrastructure, application, quality]
depends_on: [FINDING-010-176, ITER-010-PDR-012]
code: [src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: bounded-investigation-budget-and-target-relevance
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-177：主 Agent 不知道剩余 Tool action 预算并在同一实现缺口上耗尽调查

## Observation

fresh `run-067-mvp-experience` 绑定 exact product
`c662eb2b9090177f88f6eb629b4dd19b999bdfea / 8b225d99de897dc6a79ac23ddc2fed0d0ec918f6` 与 mall exact Source
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7 / 047d79d8588b76013c260f3f1a9565707301a60a`，用于复验
`FINDING-010-176`。Turn 1 没有先读取已绑定的 World Model cognition，而是先用 `UmsAdminLogin` 做 broad Source search；该操作扫描
56 个文件并返回 19 个 locator。随后 Primary 读取了正确的 `UmsAdminController.java`，却又搜索已经在 Controller full-source 中直接可见的
caller expression `adminService.login`。第二次 search 扫描最后 6 个 Source file slot 且没有命中 service implementation；下一次 read 又从
第一次 search 的共享词汇候选中选择辅助 `UmsAdminLoginLogMapper.java`，而不是当前未解决的 `UmsAdminServiceImpl`。

Source 扫描熔断后，Primary 才连续查询 World Model。第一次 cognition query 已把未解决目标精确到 `UmsAdminServiceImpl` 及登录实现；后续又
分别查询 login call sites、JWT/PasswordEncoder 和 `insertLoginLog`。执行完这四次 World Model action 后，current Turn 已累计 8 个 Tool
action，达到 Application 固定上限。第九个 Primary model call 仍以另一种措辞再次询问 `UmsAdminServiceImpl.login` 的完整 call-site list；
Application 在执行该 action 前以 `AGENT_TOOL_LIMIT_REACHED` 失败关闭。整个 Turn 没有 Draft、Evidence Package/Answer、fresh Review 或
Delivery。

最早的系统缺口不是 8 次上限过低：run-066 曾用较少且目标明确的 `World Model → Source search/read` 路径取得 Controller 与 Service
full-source。run-067 的 sealed Primary input 只给出历史 action 和 catalog，没有把 `maximum / used / remaining` 明确投影为当前 closed
budget，也没有把 fresh investigation 的 World Model-first、同一 material gap 不得换句式重复查询，以及 Source search/read 必须命中当前
未解决 target 写成可验证的调查 policy。模型因此能把“剩余预算”当成不可见资源，并把每个语法不同的 query 当作进展。

## Evidence and first divergence

- Conversation 为 `conversation_2352e293ef6c4b46b7470f51333c99b1`。九次 fresh Ark model call 依次为
  `model_call_1351a52e5ccb4597b1a8c175eb7f96a6`、`model_call_bb3af8b518984d888fcea135731c659b`、
  `model_call_313b9be6ab894b5db73f89f298f2f195`、`model_call_4337a000ec4847fba8a06348c0cb8927`、
  `model_call_f924ce4bff274c3d9d90f0e10b5b2528`、`model_call_95d733121d7246698c7708d253449d5b`、
  `model_call_12d3ed15bcba44c1ab8f9f03bb540c49`、`model_call_72298457f3dc43d4a4210c3556742836`、
  `model_call_536b88706ed443d18957f51c836fa246`。
- 前八份输出形成 `SOURCE_SEARCH(UmsAdminLogin) → SOURCE_READ(UmsAdminController) →
  SOURCE_SEARCH(adminService.login) → SOURCE_READ(UmsAdminLoginLogMapper) → WORLD_MODEL_QUERY × 4` 的已执行 action history。
  第九份输出提出另一项 World Model action，但未执行；因此 provider dispatch 为 9，Tool action 仍精确为 8。Source 的第一次 search receipt
  记录 `examined_file_count=56 / match_count=19`，第二次记录 `examined_file_count=6 / match_count=0` 和
  `SOURCE_FILE_FUSE_EXHAUSTED`。
- 第一次 World Model evidence need 已要求定位 `UmsAdminServiceImpl` 及 password/JWT/login-log implementation；最后一次又要求同一
  `UmsAdminServiceImpl.login` 中 password/JWT/update-login-time 的完整有序 call-site list。它们不完全同字，因此既有 exact-action
  repetition guard 没有拒绝，但后者没有形成新的 material target。
- terminal receipt digest
  `sha256:307042ab77a0e7727838b0cd3d1a4da1577f46b49e38a38cc2dafb946857578e` 密封 Conversation/Turn `1/1`、Ark
  dispatch `9`、DeepSeek dispatch `0`、request retry `0`、human approval request `0` 与 Production `NOT_EXECUTED`。run-067 已停止，
  不得重提交或追认为答案证据。

## Classification and disposition

这是 `system-contract`：它约束任何工程、语言、框架、问题和 symbol 上的 bounded investigation，不按 mall、登录、
`UmsAdminServiceImpl`、具体 query 或 action 序号特判。

1. Application 必须在每个 Primary invocation 从 loop limit 和 exact action history 重算并密封
   `tool_action_budget = {maximum, used, remaining}`。`remaining` 是最多仍可执行的 action 数，不是必须消费的目标。current 上限保持 8；
   不能用提高上限掩盖调查漂移。
2. `remaining=0` 时 effective tool catalog 必须机械变空；普通 successor 必须从 current SUPPORT/BOUNDARY 形成 Draft，不能再提 action。
   若 fresh Review 明确要求 Evidence 而已经没有合法 action，Application 失败关闭，不能恢复权限或用 Draft 绕过 Finding。
3. fresh investigation 在没有 current observation、action history 或 prior exact-source revalidation candidate 时，只要 World Model operation
   可用，第一步必须是 `WORLD_MODEL_QUERY`。Application 在 decoder 重算并拒绝绕过该顺序的 Source proposal；已重签的 prior full-source
   revalidation candidate 不受该首步规则阻断。
4. Primary 的调查 policy 必须说明：同一 material semantic need 的换句式不是新 need；World Model 已明确给出同一 implementation gap 后，
   不得继续询问缺失实现，应转向一个命中该 gap 的 Source target 或保留诚实 Boundary。既有 exact duplicate guard 继续机械执行；本修复不
   假装本地字符串规则能完整判定自然语言语义等价。
5. Source search 应使用由 current cognition/observation 给出的 unread source-native type/member identifier，而不是只存在于已读 caller 的
   expression；Source read 应直接对应 current unresolved material target，不因 mapper、DTO、entity、test 或相邻文件共享词汇就消费
   bounded slot。Broker 仍只拥有 authorization/allowlist/resource backstop，模型选择的语义相关性仍由 sealed role policy 和后续证据审核
   约束。

修复沿用 current `conversational-engineering-agent@8 / ENGINEERING_AGENT_PRIMARY_INPUT@8` 协议族；每个 dispatch 由修复后的 exact
prompt/input digest 区分。确定性 Model suite `24/24` PASS，覆盖初始 `8`、已有 action 后 `7`、耗尽后 `0` 的 budget projection、零预算
tool catalog/Draft enforcement、fresh World Model-first decoder guard，以及 prior exact-source revalidation 例外。该本地证据外部 dispatch
为 0，不追认 run-067。fresh Browser successor 必须使用新的 clean exact product/run identity，固定三轮问题不变，问题 4/5 继续 unseen。
