---
id: FINDING-010-218
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, source, quality]
depends_on: [FINDING-010-217, ITER-010-PDR-012, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/application_services/conversational_engineering_tools.py]
tests: [tests/test_engineering_question_answering.py, tests/test_conversational_engineering_tools.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: restrict-question-module-search-prefixes-to-current-evidence-class
target: SYS-CONTRACT-SOURCE-ARTIFACT
---

# FINDING-010-218：run-094 暴露 question module prefix 混入其他 Evidence Class

## Observation and execution evidence

`FINDING-010-216/217` candidate 已提交为 product commit/tree
`fda5bbe7ce1f094b8e63864f675b2d49d490fd71 / 7c59e27f4a114075f267f91a7c2db1d7a29c61dc`。唯一 validated launcher 完成
`run-094-mvp-experience` 的 4 个隔离 Conversation、5 个冻结 Turn，terminal 状态为 `STOPPED_AFTER_DISPATCH`。terminal/runtime/
public-source authority digest 分别为
`sha256:d6bdef3743b5f5f96229eb671df5dc93fb58fe15032c4254f7a77cd0cba580b1`、
`sha256:2e61b898d1e17ddab46b8b146c6b0f8c61380edff199edd91836064359cc220f`、
`sha256:865d57bf5f3d16a8196acce1242cbf976658cf4ecf540cbcd7c10b5988325876`。

Ark 的 4 个 real dispatch 全部形成 sealed `429 / AccountQuotaExceeded`，每个非 Clarification Turn 都合法激活既定 DeepSeek fallback。
DeepSeek 21 个 dispatch 中 20 个完成、1 个为 `REMOTE_DISCONNECTED / PROVIDER_OUTCOME_UNKNOWN`；总 dispatch `25`，各 Turn 为
`13 / 2 / 7 / 0 / 3`，retry、人工审批和 Production Activation 均为 0。Q1 以 2 个 exact Source Citation 取得
`SUCCEEDED / ACCEPTED`，证明 backtick fragment closure 已真实通过；Q2 按 outcome unknown no-retry 失败，Q3 为
`SUCCEEDED / REVIEWED_LIMITATION`，Q4 为零 dispatch Clarification，Q5 为 `FAILED / AGENT_PROTOCOL_VIOLATION`。

turn-scope/pricing-capture/session/launch/terminal/Ark DB/DeepSeek DB 文件 SHA-256 分别为：

- `a31f55283d676842bbf98fdd8c3c7e7b2bc9a35123ec9bef944997e03ad87196`
- `331a6a0f3ac90cddbbccd05796468265cbc45555d5a835d87333b144368f39e2`
- `c176dc50abd02324dd56bab82d1cb43504b8adb9ca36d7991054dc89b83db1a0`
- `04b864c57d2245c9efe2bc1f6c91cdf02d78e55f61276c5fdd0c55cbb20ace56`
- `55335726fef425a0ed9280defdafd793803c82bca0ef3c728070f5cb1fd2dd1c`
- `66cc3b450146a3a32b1520ad126bc88fccf04e56b61be733dab22c52b6db08b7`
- `140f1c3cfe621d96b7f9ff867f9c0057cb8263f09093c337c2b4d4f5052f8050`

## Exact first divergence

Q5 的 first DeepSeek call 合法执行 World Model Query；second DeepSeek call 返回 closed、可解码的
`SOURCE_SEARCH(SOURCE, ElasticsearchRepository)`。因此失败不在 Provider、structured output、模型 action shape或 route。

`FINDING-010-217` 初版 helper 先从完整 Request `source_allowlist` 识别 `mall-search`，又直接把该 scope 下的全部 allowlist prefix 作为
SOURCE Search restriction。真实 Session 的完整 allowlist 同时包含 `mall-search/src/main/java`、`mall-search/pom.xml` 与
`mall-search/src/test/java`，后两者分别属于 BUILD_CONFIGURATION 和 TEST。Broker 随后按设计逐项重验 current SOURCE Profile/class，
正确拒绝跨 class prefix；Application 把该 DomainError 密封为 `AGENT_PROTOCOL_VIOLATION`。初版 deterministic fixture 只有 SOURCE 与顶层
README，没有同 module 的 POM/TEST path，故未覆盖真实多 class Session shape。

## Decision and disposition

这是 `system-contract / systemic` Finding，不按 mall、题号、query、Provider 或具体 path 特判。

1. exact top-level scope 仍只从 immutable original question 与完整 sealed Request `source_allowlist` 识别；识别 scope 不授予权限。
2. scope 到 prefix 的映射必须只从 current operation 的 Source Profile evidence-class allowlist 选择。Application 通过 Request-bound Broker
   API取得候选，Broker 再用同一 original question、Request allowlist 与 current evidence-class allowlist 独立重算 exact match。
3. 一个 module 下其他 Evidence Class 的 path 既不能混入当前 operation，也不能因被过滤而扩大 SOURCE 权限。cognition exact-path precedence、
   `COMPILED_SOURCE_OPERATION@3` identity、rotation、`56/64` fuse、reserved READ、route、fallback、freshness、retry 与 Production 边界不变。
4. regression 把同一 module 的 SOURCE、BUILD_CONFIGURATION 与 TEST prefixes 同时放入 sealed Request，证明 SOURCE Search 只密封
   `src/main/java`，并证明 BUILD_CONFIGURATION 的 scope 单独映射到该 module POM。六模块 `154/154`、相邻十五模块 `229/229` 项定向测试
   PASS；fresh run-095 仍须验证真实完整链，run-094 不追认为质量或 MVP PASS。

该变化细化既有 Source Broker/Application owner，不改变组件职责或 wire schema，故不需要新 ADR或升级
`COMPILED_SOURCE_OPERATION@3`。本 Finding 与同步后的 `SYS-CONTRACT-SOURCE-ARTIFACT`、
`SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 是 current system write-back。
