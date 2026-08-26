---
id: FINDING-010-120
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, source, ai, security, quality]
depends_on: [FINDING-010-116, FINDING-010-119, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: project-source-read-copy-domain-by-canonical-resource-and-terminal-source-authority
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-120：Source Read 合法域必须按 canonical resource 而不是匹配行投影

## Root cause and decision

run-038 证明 v3 虽关闭伪造 locator 与 exact action 重复，却仍把一个 Source Search receipt 中同一文件的多个 line citation 当成多个可读
资源。`locator_reference` 是一次读取的 opaque authority，但 progress/file fuse 的语义属于 canonical resource；二者不能混成同一去重键。

`ENGINEERING_AGENT_PRIMARY_INPUT@4.tool_reference_policy` 现在只从 current-Turn `SOURCE_SEARCH / SUPPORT` Observation 的受信
authority receipt 构造 resource catalog：

- `path:Lx`、`path:Lx-Ly` 与 `path:Lx-y` 的 canonical resource 都是 `path`；非 line locator 以自身作为 resource identity；
- 每个 canonical resource 至多投影一个未使用 `source_read_option`，并携带 opaque reference、display locator、resource locator、
  evidence class、modality、Citation content digest 和来源 Observation ID；
- 任意 reference 已读取后，该 canonical resource 的所有其他 line reference 都从 legal domain 移除；decoder 从原 action history、
  Observation 和 receipt 重算并拒绝绕过；
- 没有未使用 resource option 时，`SOURCE_READ` 从 effective tool catalog 移除；
- 受信 Ledger prefix 已出现 `SOURCE_OPERATION_FUSE_EXHAUSTED`、`SOURCE_FILE_FUSE_EXHAUSTED` 或
  `SOURCE_BYTE_FUSE_EXHAUSTED` 的 rejected Broker Decision 时，Source Search/Read 从 effective tool catalog 移除，未使用 option 也不再
  暴露。World Model operation 不受 Source authority terminal state 影响。

这不是 Application 代替模型选择文件：每个不同 resource 仍由主 Agent 在 sealed catalog 中选择；Application 只拥有 legal set 的计算与
校验。fallback attempt 继续 fresh，不继承 primary 的 action/resource catalog。

## Verification and disposition

测试以同一资源两个 line Citation 和另一个资源证明 catalog 只保留两个 option；读取第一个 reference 后同文件另一 reference 同时退出，
另一个资源仍可用。另一个 Case 以可重算 Ledger receipt 证明 terminal Source file denial 后 Source Search/Read 消失而 World Model query
保留。与 `FINDING-010-121` 联合的 Model/Agent 组合 31/31、Session/Tool/Route/Browser 相邻组合 84/84 和 `py_compile` PASS。

该变化不提高 Source file/byte/operation、Agent step、Review、Provider dispatch、retry 或 wall-time fuse。它更新 current Engineering
Conversation system truth，并把 strategy/prompt/Primary input identity 升级到 v4；run-038 双 Provider qualification 因此只保留历史证据。
