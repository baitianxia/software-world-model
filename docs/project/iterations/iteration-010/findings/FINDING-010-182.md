---
id: FINDING-010-182
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [source, application, quality]
depends_on: [FINDING-010-181, ITER-010-PDR-012]
code: [src/software_world_model/interface/engineering_qa_source.py, src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_engineering_qa_source.py, tests/test_conversational_engineering_tools.py, tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: distinguish-search-operation-limits-from-whole-turn-source-fuses
target: SYS-CONTRACT-SOURCE-ARTIFACT
---

# FINDING-010-182：单次 Search 局部上限被误报为整轮 Source fuse 耗尽

## Observation

fresh Browser `run-073-mvp-experience` 绑定 exact product
`ebb1a3262d9e79cd7c07fe82e236fd278a8d6ce8 / d25a0dea3781728f11e76c2675e156e918f30e7a` 与 mall exact Source
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7 / 047d79d8588b76013c260f3f1a9565707301a60a`。第一条 scoped
`SOURCE_SEARCH(UmsAdminServiceImpl)` 只检查 1 个可信 target path，随后 full READ 1 个文件，证明 `FINDING-010-181` 的
Search-only scope 已真实生效。

下一条无 cognition scope 的 `SOURCE_SEARCH(JwtTokenUtil)` 按 current per-search maximum 检查 56 个文件并返回 2 个 locator；该 Result
正确保持 `PARTIAL`，但 Worker 把局部终止原因写成 `SOURCE_FILE_FUSE_EXHAUSTED`。此时整轮实际用量只有 `58/64`，随后 full READ
`JwtTokenUtil.java` 后也只是 `59/64`。第六个 Primary input 仍有 3 个 tool action、2 个 Source operation，且
`terminal_source_denial_reason=null`；整轮 Broker 从未拒绝 Source。模型却把同名 failure code 理解为整个 Turn 已耗尽 Source，提前形成
Draft，并把尚未读取的 `UmsAdminController` HTTP 入口留为证据边界。

这不是 fuse 太小，也不是 Search 覆盖应被伪装成 complete。根因是 Worker 的 operation-local scan boundary 与 Broker 的 whole-Turn
resource rejection 共用同一个 terminal code，破坏了已经存在的双层预算语义。

## Evidence and first divergence

- Browser Conversation `conversation_5fa08906990c482ea6ce0a31a2a19083` 的 Turn 1 最终显示
  `FAILED / AGENT_PROTOCOL_VIOLATION / Provider dispatch 10`。该终态还包含独立的 Response Control 缺陷，由
  `FINDING-010-183` 处置；本 Finding 的 first quality divergence 发生在第二次 Source Search Result。
- scoped Search receipt 明确记录 `TRUSTED_COGNITION_TARGET_PATHS / examined_file_count=1 / failure_code=null`；后续普通 Search
  记录 `AUTHORIZED_EVIDENCE_CLASS_ALLOWLIST / examined_file_count=56 / failure_code=SOURCE_FILE_FUSE_EXHAUSTED`，并同时产生 Support
  locator 与 Partial Boundary。
- 第六个 Primary input 密封 `tool_action_budget used=5 / remaining=3 / maximum=8`，catalog 仍含 `SOURCE_SEARCH` 与
  `SOURCE_READ`。模型自己的 `open_items` 仍列出 `UmsAdminController`、`MallSecurityConfig` 和 `AdminUserDetails`，却转入
  `RESPONSE_READY`，证明其停止依据不是 Application 撤销工具。
- terminal receipt digest `sha256:ae7f0e2800d140778adb89740ca29b85b0adb2aaf690e8c3e07b2d28cf28b2ff` 密封 Ark
  dispatch/TLS/credential/HTTP `10/10/10/10`、retry 0、post-dispatch unknown 0；DeepSeek dispatch/TLS/credential/HTTP 全 0，
  Production `NOT_EXECUTED`。terminal 文件 SHA-256 为
  `389c1b13fe58b4a2ac7b96924f5982b01a5810335a4a54cccd17ced0b67d5018`。

## Classification and disposition

这是 `system-contract / systemic` Finding；修复保留所有现有预算和 Coverage：

1. Retrieval Worker 达到 compiled Search operation 的 `maximum_files` 时返回
   `SOURCE_SEARCH_FILE_LIMIT_REACHED`；达到该 operation 的 `maximum_source_bytes` 时返回
   `SOURCE_SEARCH_BYTE_LIMIT_REACHED`。两者只说明本次 Search 为 `PARTIAL`，不表示整轮 Source 已不可用。
2. Source Broker 在整轮实际 file/byte budget 不足时继续使用
   `SOURCE_FILE_FUSE_EXHAUSTED / SOURCE_BYTE_FUSE_EXHAUSTED` 拒绝新 operation；只有这种受信 Broker rejection 才是 terminal
   Source denial。模型端现有 terminal detection 不扩张到 operation-local codes。
3. 不提高 per-search 56、whole-Turn 64、byte 或 action fuse，不减少实际计量，不把 partial 结果提升成 Evidence Class complete，也不改变
   Provider route、fallback、disclosure 或 Production 边界。
4. file/byte 局部上限回归和真实下游边界回归 PASS；包含 Source、Tool、Model、Agent、Artifact Session、CLI 与 docs gate 的受影响组合
   `225 tests / 3 skipped / 0 failure`。fresh Browser successor 仍须使用新 product/run identity；run-073 不取得开发体验、质量或 MVP PASS。
