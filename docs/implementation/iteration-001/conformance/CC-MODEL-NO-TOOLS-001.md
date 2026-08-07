# CC-MODEL-NO-TOOLS-001 — OpenAI Responses Adapter Conformance Fixture

| 元数据 | 值 |
|---|---|
| Case ID | CC-MODEL-NO-TOOLS-001 |
| Version | 0.1.0 |
| Status | Defined — Not Executed |
| Target Profile | [SWM-ADAPTER-OAI-RESPONSES-001@0.1.0](../contracts/ITER-001-OpenAI-No-Tools-Adapter-Profile.md) |
| Design Baseline | [SWM-DBM-ITER-001-REV-002](../../../detailed-design/governance/Design_Baseline_Manifest_Iteration_001_Revision_002.md) |
| Implementation Baseline | [SWM-IBM-ITER-001-REV-002](../Implementation_Baseline_Manifest_Iteration_001_Revision_002.md) |
| Shared Error Projection | [ITER-001-SHARED-ERROR-CLASSIFICATION](../contracts/ITER-001-Shared-Error-Classification.md) |
| Contract | AI-PROVIDER-ADAPTER-01、AI-ISOLATION-RECEIPT-01 |
| Validation Type | Contract Conformance；不是 Design Validation 或 Capability Evaluation |

> 本 Fixture 定义如何证明 Adapter 符合 no-tools Contract。没有实现 Commit、Provider Configuration Revision、exact Model Reference 和原始结果时，不得把状态改为 Passed。

## 1. 固定运行输入

每次 Run 必须固定：

- Implementation Commit / Artifact Digest、Adapter Profile / Envelope Version。
- Provider Endpoint、Organization / Project Configuration Revision 和数据政策声明。
- exact 请求 Model Reference、Provider 返回 Model ID 和 Replay Classification Policy。
- Prompt Renderer、Authorized Input Manifest、Structured Output Schema 和全部参数 Digest。
- Case Fixture Revision、网络代理 / HTTP Capture 配置和执行时间。
- Design Baseline、测试操作者、原始结果位置和 Result Digest。

Secret 只由测试运行时注入，不进入 Fixture、Manifest 或结果正文。

## 2. 测试装置

装置由三个可替换部分组成：

1. **Recording Transport**：在 TLS 调用边界前捕获 Adapter 生成的 Method、URL、非 Secret Header 和 Body，并计算 Canonical Request Digest。
2. **Provider Test Project**：不配置 Conversation、File、Vector Store、Connector、MCP 或 Provider Agent；配置 Revision 被固定。
3. **Canary Fixture**：创建未进入 Manifest 的随机文件名、路径和高熵内容，同时在 Manifest 中提供不同的授权片段。Canary 输出检查只是辅助；权威 Oracle 是实际请求闭包和不存在外部访问通道。

## 3. 必须通过的 Case

| Case | 操作 | 机械 Oracle |
|---|---|---|
| CC-NT-01 Envelope allowlist | 让调用方提交包含未知字段、顶层 `instructions`、Provider Prompt / Conversation / Tool 的恶意扩展，并把独有 Canary 放入该旁路字段 | Adapter 在 PREPARED 前拒绝；Recording Transport 没有发送；不存在 Manifest 外指令通道 |
| CC-NT-02 Empty provider tools | 执行一个 Platform Tool Proposal Capability | Body 精确包含 `tools=[]`、`tool_choice=none`、`parallel_tool_calls=false`；Proposal 只在 Structured Output 中出现 |
| CC-NT-03 Stateless call | 连续执行两个 Context，在首个 Context 放入独有随机片段 | 两个请求均无 conversation / previous / prompt / context management，`store=false`；第二个 Request Digest 不含首个片段 |
| CC-NT-04 Manifest closure | Manifest 中授权多个片段并放置未授权 Canary | 实际每个 input item 与 Manifest 双向覆盖；Body 不含 Canary；Receipt Digest 等于实际 Body Digest |
| CC-NT-05 No attachment expansion | 以 input file、URL、image、file ID、vector store 或路径展开形式调用 | Adapter 在分派前失败关闭，不上传、不读取、不发送远程引用 |
| CC-NT-06 Output item denylist | 模拟 / 捕获 Tool、Web、File、Computer、MCP 或未知 Output Item | Adapter 隔离原始响应；不返回可供领域封存的 Completed Result |
| CC-NT-07 Structured outcome | 分别产生 valid、schema-invalid、refusal、max-token incomplete、content-filter outcome | 只有完整且 shape-valid 的响应进入领域校验；其余有精确失败分类 |
| CC-NT-08 Model identity | 使用 pinned ID、滚动 alias 和响应 ID 不匹配 Fixture | 只按 Profile 表格形成 PINNED / OBSERVED_MUTABLE / UNRESOLVED_MUTABLE；不制造伪指纹 |
| CC-NT-09 Unknown dispatch | 在请求发送后、响应 Header 前断开网络 | 原 Call 为 OUTCOME_UNKNOWN，保留 X-Client-Request-Id；不以同一 Call ID 重发、不按零 Usage 结算 |
| CC-NT-10 Secret hygiene | 捕获正常、失败、超时和重试日志 | Authorization / API Key 不在 Request Digest、Telemetry、异常正文或 Fixture Result 中 |
| CC-NT-11 Provider echo | 对真实 Provider 完成最小调用 | Response 的 tools 为空、没有 Tool Item，model / usage / request ID 按 Profile 被记录；不以回答内容正确代替隔离证明 |
| CC-NT-12 Sink denial | 对任一失败 Case 尝试写 Proposal、Candidate、Assessment、Answer 或生产缓存 | 所有生产 Sink 依据缺失 /无效 Eligibility 拒绝，且没有可观察污染 |

## 4. 反例与防作弊规则

- 仅在 Prompt 中写“不要使用工具”不算通过。
- 仅检查 Response 没有 Tool Event 不算通过。
- Canary 没出现在输出不算证明不可访问；模型可能没有选择泄露。
- 空工作目录、只读权限或测试操作者声称未打开文件不算 Provider 隔离。
- 结构化 JSON 有效不算领域 Contract 有效。
- 滚动 alias 在一次调用中返回稳定字符串不算 pinned snapshot。
- 测试 Project 未配置 File / MCP 不替代实际请求字段 allowlist；两者都必须成立。

## 5. 通过、失效与产物

全部 CC-NT-01 至 CC-NT-12 通过后，才可以封存不可变 Conformance Result。Result 至少包含：

- `PASS | FAIL`，不使用推测性的部分通过。
- 12 个 Case 的 exact Outcome、原始 Capture / Log Reference 和 Digest。
- 实现 Commit、Profile、Endpoint、Provider Project Configuration、Model Reference 和运行环境。
- 支持的 Runtime Access Mode、输入类型、Output Schema 和 Model Identity Classification。
- 结果有效期与失效依赖。

任一 Adapter / SDK / HTTP 序列化、Provider API、Endpoint、Project Policy、Envelope、模型身份字段或数据保留语义发生变化，Result 进入 Stale 并重跑受影响 Case。质量、正确性和任务完成率变化进入 CE，不修改本 CC 的 Oracle。

## 6. 当前结论

Fixture 已定义；validation-only Adapter、Recording Transport 与12类离线机械Oracle已经实现并通过回归。当前工作区没有VCS Commit，也尚未形成冻结的实现Artifact Digest、Provider资格配置、exact Model Reference、Live Capture和不可变Result，因此当前结论仍为 `NOT_EXECUTED`。离线Fixture结果不得登记为本CC的PASS；该状态阻止任何模型Strategy获得生产Activation。
