# Iteration 001 OpenAI Responses no-tools Adapter Profile

| 元数据 | 值 |
|---|---|
| Profile ID | SWM-ADAPTER-OAI-RESPONSES-001 |
| Version | 0.1.0 |
| Status | Selected — Conformance Required |
| Implementation Consumer | [SWM-IMP-ITER-001](../Implementation_Plan_Iteration_001.md) |
| Design Baseline | [SWM-DBM-ITER-001-REV-002](../../../detailed-design/governance/Design_Baseline_Manifest_Iteration_001_Revision_002.md) |
| Implementation Baseline | [SWM-IBM-ITER-001-REV-002](../Implementation_Baseline_Manifest_Iteration_001_Revision_002.md) |
| Conformance Fixture | [CC-MODEL-NO-TOOLS-001](../conformance/CC-MODEL-NO-TOOLS-001.md) |
| Shared Error Projection | [ITER-001-SHARED-ERROR-CLASSIFICATION](ITER-001-Shared-Error-Classification.md) |
| Provider Boundary | OpenAI `POST /v1/responses` over direct HTTPS |
| Adapter Envelope | `openai-responses-no-tools@0.1.0` |
| Applicable Runtime Mode | `NO_EXTERNAL_ACCESS` |
| Decision Date | 2026-08-05 |

> 本 Profile 是 Iteration 001 的 Provider-specific 实现选择，不改变 `AI-PROVIDER-ADAPTER-01`。`Selected` 只表示已选定待实现方案；CC-MODEL-NO-TOOLS-001 通过且模型 Strategy 完成独立 CE / Activation 前，任何模型输出都没有生产资格。

## 1. 选择结论

首个切片使用 OpenAI Responses REST API 的无会话、纯输入模式，不使用 Codex、Agents SDK、Assistants、Provider Conversation、托管 Tool 或文件附件。选择直接 HTTPS Adapter，是为了让平台能够在分派前构造并审计完整 JSON Envelope；具体 HTTP Library 不属于本 Profile。

本选择成立的边界是：

- Adapter 只支持 `NO_EXTERNAL_ACCESS`，不实现 `DECLARED_PROVIDER_TOOL_SET`。
- Platform Tool Proposal 是普通 Structured Output；不向 Provider 注册任何 Tool。
- 每个 Model Call 都是新的无会话请求，不继承 Provider 侧历史。
- 只允许 Manifest 内联文本进入 Provider；来源内容先由平台读取并形成授权片段。
- 模型质量、Prompt 和具体模型版本由 Capability Evaluation 决定，不由 Adapter 固定。

## 2. 固定请求 Envelope

### 2.1 必须字段

| 字段 | 固定语义 |
|---|---|
| `model` | 来自已冻结 Model Configuration 的 exact Reference；不得由 Prompt 或模型输出决定 |
| `input` | 只由 Authorized Input Manifest 与 Prompt Rendering Contract 生成的有序 `input_text` 消息 |
| `tools` | 精确为空数组 `[]` |
| `tool_choice` | 精确为 `none`；Provider 不接受该组合时 Conformance 失败，不静默删除 |
| `parallel_tool_calls` | `false` |
| `store` | `false` |
| `background` | `false` |
| `stream` | `false`；首切片只接收完整响应 |
| `truncation` | `disabled`；输入超限必须失败，不能由 Provider 静默丢弃旧项 |
| `text.format` | Capability 声明的 strict JSON Schema；纯文本 Capability 也必须显式选择 `text` |
| `max_output_tokens` | 来自 child Resource Allocation |
| `reasoning` | exact Strategy Configuration；不得使用调用期动态默认值 |
| `metadata` | 只含无敏感值的 Model Call ID、Capability ID、Manifest Digest 和 Baseline ID |

HTTP Header 必须包含唯一 `X-Client-Request-Id = Model Call ID`；响应的 Provider `x-request-id` 可得时一并记录。Authorization Secret 只存在于传输配置，不进入 Manifest、Request Digest、Telemetry 或原始请求审计副本。

### 2.2 必须缺失的字段与内容

以下字段不得出现在请求中：

- 顶层 `instructions`；全部指令必须作为 Authorized Input Manifest 中可双向覆盖的 `input_text` Item 渲染，不能存在第二条未入 Manifest 的输入通道。
- `conversation`、`previous_response_id`、Provider Conversation / Thread ID。
- `prompt`、Provider 托管 Prompt Reference 或任何服务端模板变量。
- `context_management`、Provider 侧 Compaction 或自动历史管理。
- `include` 中的 Tool、File、Web、Computer、MCP 或 Retrieval 输出请求。
- `input_file`、`file_id`、`file_url`、`input_image`、`image_url`、Vector Store、File Search 或附件引用。
- Web Search、File Search、Computer Use、Code Interpreter、MCP、Connector、Function、Custom Tool、Tool Search、Namespace 或 Programmatic Tool 定义。
- Provider 可解释为外部资源地址的自定义扩展字段。

Adapter 使用字段 allowlist 序列化，不对任意调用方 Map 做透传。SDK 或 Provider 新增默认字段时，只有 Profile 升级并重新通过 Conformance 后才能进入 Envelope。

### 2.3 输入闭包

Gateway 在分派前生成 Canonical Provider Request，并验证：

1. 每个 `input_text` 都能一一映射到 Manifest Item、Content Digest 和 Rendering Step。
2. Canonical Request Digest 覆盖完整消息、字段名、字段值、顺序、Schema、模型和资源参数。
3. 除传输 Secret 外，实际发送 Body 与已签发 Isolation Receipt 中的 Request Digest 完全一致。
4. 文件路径、URL 或 Artifact Reference 只可作为被授权的普通文本语义出现；Adapter 不解析、打开或展开它们。
5. Manifest 的“缺失、拒绝、未知”不能由 Provider 历史、附件或检索补齐。

## 3. 响应与生产资格

Adapter 只规范化 Provider 响应，不判断领域正确性。完成响应至少记录：

- Provider Response ID、`x-request-id`、请求/完成时间和状态。
- 响应返回的 `model`、请求 Model Reference 与二者关系。
- 输出 Item 类型、Structured Output 解析状态、拒绝、截断和终止原因。
- Input / Output / Reasoning / Cached Token Usage 以及 Usage Completeness。
- Canonical Response Digest 和加密原始响应 Reference。

以下任一条件使本次调用不能产生领域结果：

- 响应包含任何 Tool Call、Tool Output、File / Web / Computer / MCP Item 或未知 Output Item 类型。
- 返回的 `tools` 非空，或实际 Envelope 与 Isolation Receipt 不一致。
- 状态不是可证明的完成，输出被截断、拒绝、无法按 Schema 解析或数据策略拒绝。
- Provider Response Model 与请求 / Qualification Policy 不匹配。
- Provider Outcome 或 Usage 无法确定且上游 Contract 不接受该分类。

Provider 安全拒绝是合法的模型调用结果类型，但不是合法领域 Proposal / Candidate / Assessment / Answer。Capability Owner 只能把它归为受控失败。

## 4. 模型身份政策

Responses API 的响应含 `model` ID，但本 Profile 不把任意返回字符串自动解释为不可变模型指纹。

| 情况 | Replay Classification | 生产处理 |
|---|---|---|
| Provider 文档明确支持的 pinned snapshot；请求与响应 ID 相符；exact ID 已被 CE 覆盖 | `PINNED` | 可进入 post-call Eligibility |
| 响应能返回比请求别名更具体且 Provider 声明可区分的 Revision | `OBSERVED_MUTABLE` | exact Revision 必须具有独立有效 CE；否则拒绝并使旧资格失效 |
| 滚动别名、响应只回显别名、或无法证明实际 Revision | `UNRESOLVED_MUTABLE` | Iteration 001 的生产知识与回答 Capability 一律拒绝 |

`x-request-id` 是请求追踪身份，不是模型指纹。Adapter 不生成自定义 hash 冒充 Provider Model Revision，也不把“调用日期 + alias”拼成伪版本。

具体 Model Reference 不在本 Profile 中冻结。它必须由后续 Strategy Definition 选择，并在 CC 证明 Adapter 身份分类正确、CE 证明质量后才可 Activation。

## 5. 隔离 Receipt 的签发条件

Gateway 只有在以下前置检查全部通过时签发 `AI-ISOLATION-RECEIPT-01`：

1. Adapter Profile、Provider Endpoint、Envelope Version 和适用 CC Result 精确匹配且未过期。
2. Runtime Access Mode 为 `NO_EXTERNAL_ACCESS`，Platform Proposal Mode 为 `NONE` 或 `DECLARED_PLATFORM_PROPOSAL_ONLY`。
3. Canonical Envelope 通过字段 allowlist、禁止内容扫描和 Manifest 双向覆盖。
4. 会话、附件、托管 Prompt、Tool、Provider 检索和 Provider 历史字段均不存在。
5. 结构化输出 Schema、Model Identity Policy、Allocation 与数据分类均被 Adapter 支持。
6. Request Digest 已冻结，后续 Transport 只能增加不进入模型输入的认证与追踪 Header。

Adapter Configuration、Provider API 行为、Endpoint、Envelope、模型身份语义或数据政策变化后，现有 CC Result 立即 Stale；不能只更新 SDK 后继续使用旧 Receipt。

## 6. Outcome 与重试

- HTTP 响应明确返回 Provider 错误时，按 Shared Error Classification 形成已知失败。
- 在无法确认 Provider 是否收到请求时，Model Call 进入 `OUTCOME_UNKNOWN`；不得立即以同一 Model Call ID 重发。
- 恢复使用原 `X-Client-Request-Id` 和可得的 `x-request-id` 查询 / 人工解析原 Attempt。Provider 没有可用解析能力时保持未知。
- 新物理尝试必须取得新的 Model Call ID、child Allocation 和 Request ID；原 Attempt 的 Outcome / Usage 保留。
- Adapter 不在不同模型、Endpoint 或 Provider 间自动回退。

## 7. 数据与保留边界

`store: false` 用于关闭 Response 对象的默认存储和后续会话引用，但不等价于 Zero Data Retention，也不证明 Provider 没有安全、滥用监控或短期缓存。组织级数据政策、区域、保留和训练使用设置必须由独立 Provider Configuration / Conformance 校验。

原始 Prompt 和 Response 是否由平台保存由平台数据分类与保留政策决定；Telemetry 只保存 Digest、Usage、状态和受控引用。API Key、授权 Header 和用户敏感内容不得进入普通日志。

## 8. 官方接口依据与限制

本选择核对了 2026-08-05 的官方资料：

- [Responses create reference](https://developers.openai.com/api/reference/resources/responses/methods/create)：请求显式声明 Tool、会话、存储、截断、输出格式和模型，响应返回 Model ID、Tool 清单和 Usage。
- [Conversation state](https://developers.openai.com/api/docs/guides/conversation-state)：`store: false` 支持无状态调用；`conversation` 和 `previous_response_id` 会引入 Provider 侧历史，因此本 Profile 禁用。
- [Using tools](https://developers.openai.com/api/docs/guides/tools)：Web、File、MCP、Function 等能力都通过 Tool 注册进入模型调用，因此本 Profile 固定空 Tool 集并禁止相关输入。
- [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)：输出 Schema 是形状约束，仍需处理 refusal、incomplete 和 content filter；它不能替代领域校验。
- [API overview](https://developers.openai.com/api/reference/overview)：Provider 支持 `X-Client-Request-Id` / `x-request-id` 追踪，并建议用 pinned model version 与 eval 控制模型行为变化。

官方接口定义不能单独证明租户配置、实际传输实现和 Provider 行为符合本 Profile，所以本选择保持 `Conformance Required`。

## 9. WP-0 决定

- Adapter 方案：已选择。
- Provider no-tools Conformance Fixture：已建立，但尚未执行。
- 具体生产 Model / Prompt / Strategy：不属于 Adapter Profile，等待 Capability Evaluation。
- WP-1 准入：Adapter 选择与 Fixture 定义已经满足 WP-0 文档门禁；Adapter 实现进入 WP-2 后必须先通过 CC 才能被生产激活。
