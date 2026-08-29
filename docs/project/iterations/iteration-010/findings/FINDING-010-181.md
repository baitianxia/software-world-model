---
id: FINDING-010-181
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, source-integration, quality]
depends_on: [FINDING-010-180, ITER-010-PDR-012]
code: [src/software_world_model/application_services/__init__.py, src/software_world_model/application_services/conversational_engineering_tools.py, src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/interface/engineering_qa_source.py]
tests: [tests/test_conversational_engineering_tools.py, tests/test_engineering_qa_source.py, tests/test_engineering_question_answering.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: trusted-cognition-target-path-scoped-source-search
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-181：精确类型 Search 仍以全类路径扫描耗尽 Source file fuse

## Observation

fresh Browser `run-072-mvp-experience` 绑定 exact product
`ee1a132403351f1a04a2e4634a192e831e45d867 / 2249e2af660235067941f4bcd954e4e574370de0` 与 mall exact Source
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7 / 047d79d8588b76013c260f3f1a9565707301a60a`。Turn 1 已验证
`FINDING-010-180` 的 closed target domain 生效：World Model 后第一个 Source proposal 不再是宽泛 `login`，而是 exact
`SOURCE_SEARCH(query=UmsAdminServiceImpl)`。但是 Search Worker 即使先检查文件名 stem 与 query 精确一致的候选，也继续扫描整个已授权
Evidence Class 来声明全局覆盖。第一次 Search 因而读取 56 个文件，随后整读 service 读取 1 个文件；第二次 exact
`UmsAdminController` Search 又读取剩余 6 个文件，整读 controller 再读取 1 个文件，累计正好达到 `64/64`。

第六个 Primary invocation 的 action budget 仍余 3，但 effective catalog 已机械移除全部 Source operation，只剩
`WORLD_MODEL_QUERY`。该 invocation 准备继续 exact `SOURCE_SEARCH(query=AdminUserDetails)`，初始输出因遗漏 `action.operation` 进入一次
same-profile JSON syntax repair；repair 保留同一语义 action，却仍不在 current effective catalog 内，因此 Application 正确拒绝该输出。
页面如实显示 `FAILED / AGENT_MODEL_CALL_REJECTED / Provider dispatch 7`，Conversation 保持 `ACTIVE`。

这次失败证明“模型必须复制精确 declaring type”只解决了目标选择，没有解决执行范围：Projection 已同时拥有 exact `source_path`，但
Application 丢弃该导航元数据，Worker 只能把字面量 Search 当成全 Evidence Class 覆盖扫描。提高 64-file fuse、停止检查其他文件或直接把
cognition path 变成 READ capability 都会掩盖权限/覆盖语义，不能作为修复。

## Evidence and first divergence

- Browser Conversation `conversation_f8ce72e50d114948a3d6c586461493da` 的 Turn 1 页面记录
  `FAILED / AGENT_MODEL_CALL_REJECTED / Provider dispatch 7`；没有 Answer、Citation、Review 或 Delivery。
- Ark Gateway 的第二个 role input 把第一次 `SOURCE_SEARCH.allowed_exact_values` 密封为
  `AdminUserDetails / UmsAdminController / UmsAdminServiceImpl / MallSecurityConfig / UmsAdminService`；实际输出精确选择
  `UmsAdminServiceImpl`，证明 FINDING-010-180 的 decoder/closed domain 没有回归。
- 两个 Search 的密封 Coverage 分别为 `56 files / 2 matches` 与 `6 files / 2 matches`，两个 full READ 各 1 file；第五次 Tool action 后
  Resource receipt 达到 `64/64`。下一 Primary input 的 `tool_action_budget.remaining=3`，但 `tool_catalog` 只含 World Model。
- 第六个 Ark output 以 `STRUCTURED_OUTPUT_INVALID` 记录缺失 `action.operation`；第七个 fresh repair output 恢复完整
  `SOURCE_SEARCH(AdminUserDetails)`，但 current catalog 已无 Source，故 model receipt 为 dispatched rejected。该拒绝是产品安全边界，不是
  Provider unavailable。
- terminal digest `sha256:946b6bee65bca53d9258e800e80dabdc3b5dbfeed69e961eec93991959493a25` 密封 Ark dispatch/TLS/credential/HTTP
  `7/7/7/7`、request retry 0、post-dispatch unknown 0；DeepSeek dispatch/TLS/credential/HTTP 全 0，Production `NOT_EXECUTED`。
  当前周六 DeepSeek admission 虽为 `ALLOWED_OFF_PEAK`，Ark 全部成功完成 HTTP，因此没有 fallback 是正确行为。

## Classification and disposition

这是 `system-contract / systemic` Finding；修复保持模型无 path authority，并保留 Broker/Worker 的 exact-revision 与 fuse Owner：

1. Tool Adapter 只在 non-empty、non-truncated、实际已投影给 Primary 的
   `ENGINEERING_AGENT_COGNITION_SOURCE_SEARCH_TARGETS@1` 中保留 `literal → canonical source paths`。这些路径不进入模型 action，不生成
   READ locator，也明确 `grants_read_authority=false`。
2. 当后续 `SOURCE_SEARCH` 的 `SOURCE` query 精确等于已保留 literal 时，Application 把对应路径作为 trusted Search-only scope 交给
   Broker。Broker 只接受 canonical、unique、最多 64 项、`.java` stem 与 query 精确一致，且同时落在 Request allowlist 与 Source Profile
   的路径；任何漂移以 authority inconsistency 失败关闭。
3. `COMPILED_SOURCE_OPERATION@2` 把 `search_path_scope` 纳入 operation ID/digest，并把 `maximum_files` 进一步收紧到 scope 大小。Worker 仍在
   exact Git revision 上执行 case-sensitive literal content Search，只检查该 scope 并签发实际命中项的 opaque locator；scope path 在
   exact tree 缺失时返回 `SOURCE_SEARCH_PATH_SCOPE_INCONSISTENT`，不回退成全库扫描。
4. 没有可信 target scope 的普通 Source Search 保持原 `QUERY_PATH_RELEVANCE_THEN_CANONICAL@1` 行为；后续新 Source Observation 发现的
   symbol 仍可按既有短字面量 contract 调查。该修复不提高 action/file/byte 上限，不改变 Source Broker policy `@2`、Provider 路由、披露、
   fallback 或 Production 边界。
5. 三条新增关键回归先 PASS：Broker 接受 exact scope/拒绝 query-path mismatch，Worker 在 21 个授权 Java 文件中只检查 1 个目标文件，
   Tool Adapter 的 cognition→Source 链把 scope 与 non-authority Ledger receipt 一并密封。随后四个受影响模块共 `102/102` PASS。fresh
   Browser successor 仍须使用新 product/run identity 验证完整三轮；run-072 不取得开发体验、质量或 MVP PASS。
