---
id: FINDING-010-180
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [FINDING-010-177, FINDING-010-178, FINDING-010-179, ITER-010-PDR-012]
code: [src/software_world_model/application_services/conversational_engineering_tools.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_tools.py, tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: cognition-derived-first-source-target-binding
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-180：World Model-first 之后仍可宽搜并耗尽 Source file fuse

## Observation

fresh Browser `run-071-mvp-experience` 绑定 exact product
`8c6f7bbbd03d31ac495d645dfce28675dbf40bb7 / ce6154e24eceacfae5e02b17f5e071cbea5b9c1e` 与 mall exact Source
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7 / 047d79d8588b76013c260f3f1a9565707301a60a`。Turn 1 的第一步正确执行
`WORLD_MODEL_QUERY`；query-relevant projection 已包含 `UmsAdminServiceImpl`、`UmsAdminController`、`MallSecurityConfig` 等九个 Java
declaring type 及 exact `source_path`。第二个 Primary invocation 却仍提出 `SOURCE_SEARCH(query=login)`。该宽搜检查 56 个文件并返回 20
个匹配；紧接着 `SOURCE_SEARCH(query=JwtTokenUtil)` 又检查 7 个文件，Controller full read 再消耗 1 个文件，累计精确达到
`64/64` Source file fuse。

模型随后提出真正命中实现缺口的 `SOURCE_SEARCH(query=UmsAdminServiceImpl)`，但此时 effective catalog 已只剩
`WORLD_MODEL_QUERY`，所以该输出只能进入一次 closed-output repair，不能执行 Source。后续 Draft/Review 确认密码校验和 JWT 生成仍缺
实现证据；Primary 又以不同措辞查询不完整 World Model，最终在第 8 个 Tool action 后准备收敛。第 14 个 Ark dispatch 已发送 HTTP bytes
后收到 `REMOTE_DISCONNECTED`，正确密封为 `PROVIDER_OUTCOME_UNKNOWN`，Turn 以 `AGENT_MODEL_OUTCOME_UNKNOWN` 失败关闭。

最后一次 transport failure 是 terminal 直接原因，但最早产品偏差发生在第二个调用：`FINDING-010-177` 只把“首步 World Model”和
“优先 source-native target”写入 prompt/decoder policy，没有把 current cognition 已给出的精确声明类型投影为首个 Source search 的 closed
copy domain。模型因此仍能合法选择宽泛 member word，并在真正 implementation target 出现前耗尽扫描预算。

## Evidence and first divergence

- Browser Conversation `conversation_5b5fd9d9121a4a49aa55d7b1a9656d57` 的 Turn 1 页面如实显示
  `FAILED / AGENT_MODEL_OUTCOME_UNKNOWN / Provider dispatch 14 / Citation 0 / Delivery Authorization NOT PRESENT`。
- Ark Gateway 密封 14 个 Manifest、13 个 completed output；顺序为 9 个首次 Primary call、1 个 independent Review、4 个 Review 后
  Primary call。三个 Primary call 是受控 closed-output repair，不是同 request retry；terminal receipt 仍为 request retry 0。
- 第一次 World Model SUPPORT 的 32 个 query-matched item 中，`STRUCTURE_ENTITY_STATE` 已给出九个 declaring type/source-path 对；其中
  `com.macro.mall.service.impl.UmsAdminServiceImpl` 明确绑定
  `mall-admin/src/main/java/com/macro/mall/service/impl/UmsAdminServiceImpl.java`。随后实际 action 却是字面量 `login`。
- 三个 Source operation 的 sealed result 分别是：`login` search `56 files / 20 matches`、`JwtTokenUtil` search
  `7 files / 2 matches`、`UmsAdminController.java` full read `1 file`。exact service search 只存在于被拒 model proposal，没有执行。
- terminal digest `sha256:fc561e8fab5834b0db14792bceb05915ba6e3dff7ff18a44f037c34f05274a3f` 密封 Ark dispatch 14、TLS
  handshake success 14、HTTP dispatch 14、post-dispatch outcome unknown 1、DeepSeek dispatch/TLS/credential/HTTP 0、Production
  `NOT_EXECUTED`。`PROVIDER_OUTCOME_UNKNOWN` 不满足 ADR-017 的可信 unavailable verdict，因此没有 fallback 是正确行为。

## Classification and disposition

这是 `system-contract / systemic` Finding；修复不能硬编码 mall、登录、类名、问题或 Oracle：

1. `ENGINEERING_AGENT_WORLD_MODEL_SUPPORT@3` 从 query-relevant `STRUCTURE_ENTITY_STATE` 投影版本化
   `ENGINEERING_AGENT_COGNITION_SOURCE_SEARCH_TARGETS@1`。只有 Java declaring type、exact `source_path` 与 `.java` 文件 stem 一致时才生成
   literal option；投影携带 cognition item/revision identity，但明确 `grants_source_authority=false`。
2. current `conversational-engineering-agent@8 / conversational-engineering-agent-no-tools-prompt@8 /
   ENGINEERING_AGENT_PRIMARY_INPUT@8` 把 non-empty、non-truncated target projection 密封到 `tool_reference_policy`。该修复沿用 current
   协议族，由 exact prompt/input/request digest 区分新旧字节；在本 Turn 尚未执行任何
   Source action 时，第一次 `SOURCE_SEARCH.query` 的 `allowed_exact_values` 是这些 literal 的 exhaustive copy domain；decoder 从原
   Observation 重算并拒绝 `login` 之类域外值。
3. target projection 只约束第一次 cognition→Source 导航，不替代 Agent 对 material gap 的选择，也不把 locator 变成 path authority。
   一次 Source action 后，Agent 仍可根据新 Source Observation/Review Finding 提出新的短字面量；Broker 继续独占 Profile、allowlist、revision、
   operation/file/byte fuse 和 exact operation 编译。
4. projection 缺失或被有界截断时不伪装 exhaustive domain，保留原有短字面量 proposal 路径及 Broker backstop；malformed current schema
   则以 authority inconsistency 失败关闭。
5. 本地定向 Tool/Model suite `38/38` PASS，覆盖精确 Java declaring-type projection、宽泛首搜拒绝、合法 exact target 接受，以及第一次
   Source action 后允许基于新观察继续选择字面量。fresh Browser successor 仍须用新 product/run identity 验证完整三轮；本 Finding 不把
   run-071 的断线或未完成 Draft 追认为质量证据。
