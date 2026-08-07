# Iteration 001 Volcengine Ark Chat Completions no-tools Adapter Profile

| 元数据 | 值 |
|---|---|
| Profile ID | `SWM-ADAPTER-ARK-CHAT-001` |
| Version | `1.3.0` |
| Status | `Implemented — Coding Plan @7 Live Conformance PASS` |
| Provider | `VOLCENGINE_ARK` |
| Protocol | `OPENAI_COMPATIBLE_CHAT_COMPLETIONS` |
| Base URL | `https://ark.cn-beijing.volces.com/api/coding/v3` |
| Endpoint | `POST https://ark.cn-beijing.volces.com/api/coding/v3/chat/completions` |
| Adapter Version | `openai-chat-completions-no-tools@7` |
| Conformance Fixture | [CC-ARK-CHAT-NO-TOOLS-001](../conformance/CC-ARK-CHAT-NO-TOOLS-001.md) |
| Validation Type | Adapter Contract Conformance；不是模型 Capability Evaluation |

## 1. 固定边界

本 Profile 是火山方舟Coding Plan Chat Completions的Provider-specific实现选择，不改写历史在线推理或OpenAI Responses Profile。用户配置的是OpenAI兼容Base URL；本Adapter确定性追加`/chat/completions`形成唯一允许的实际POST Endpoint。不同网关虽然都可称为“OpenAI兼容”，但计费范围、模型资格和请求边界不能共用Adapter Version或Conformance Result。[火山引擎Coding Plan接入说明](https://developer.volcengine.com/articles/7615528054736945158)明确区分Coding Plan `/api/coding/v3`与在线推理`/api/v3`。

请求只允许以下顶层字段：

`model`、`messages`、`tools`、`tool_choice`、`parallel_tool_calls`、`stream`、`n`、`max_tokens`、`thinking`、`response_format`。

固定值和约束如下：

- `tools=[]`、`tool_choice=none`、`parallel_tool_calls=false`。
- `stream=false`、`n=1`；只接收一个完整 Choice。
- `thinking.type=disabled`；避免GLM深度思考内容占用输出预算并在长结构化结果返回前触发上游断开。调用方不能覆盖该值。
- `response_format.type=json_object`；Adapter把注册的完整closed JSON Schema确定性编码为首个System Message，平台收到对象文本后再次按同一closed Schema校验。Coding Plan上的当前模型已实测明确拒绝`response_format.type=json_schema`，因此不得继续发送该不兼容参数，也不得降级为无Schema自由文本。
- 请求`model`必须逐字等于冻结别名`glm-5-2-260617`；调用方不能在单次请求中改模型。Coding Plan实测响应身份为`glm-5.2`，两者作为请求身份与预期实际身份共同进入配置指纹和Live CC，其他响应身份失败关闭。
- `messages`只由本次显式输入渲染；不发送 Conversation、Previous Response、托管 Prompt、Context Management、附件或检索引用。
- `X-Client-Request-Id`由 Provider Request Digest 派生；Bearer Secret 只在传输层加入 Header，不进入请求摘要或 Recording Transport。
- Transport 忽略ambient代理，使用直连HTTPS；TLS证书与Hostname校验始终开启。

Chat Completions Envelope没有使用本实现可证明关闭的Provider持久化开关。因此“本次请求不携带会话引用”只证明请求无会话继承，不等同于Zero Data Retention；账户级保留、训练和地域政策属于独立部署配置。

## 2. 响应边界

Adapter只接受：

- `object=chat.completion`；
- 精确一个`index=0`的Choice；
- Assistant Message包含非空JSON文本；
- 纯JSON按`IDENTITY`处理；仅当整体为单一`json` Markdown围栏，或围栏前只有不超过512字节且不含`{}[]`/其他围栏的非结构文本时，确定性提取围栏内对象，并记录Normalization类型；尾随文本、多围栏、其他语言标签仍失败关闭；
- `finish_reason=stop`；
- 不含`tool_calls`、`function_call`、`audio`或非空`refusal`；
- 返回非空`model`与Response / Request ID；
- Usage中`total_tokens = prompt_tokens + completion_tokens`，否则Usage保持不完整，不能伪装成零。

Transport还会把远端在无HTTP响应时主动断开归类为`PROVIDER_OUTCOME_UNKNOWN / REMOTE_DISCONNECTED`，不得输出堆栈或把未知结果当作失败后自动重放。

Provider返回的`model`是实际观察身份。只有方舟专用CC Result通过、该身份被结果覆盖且结果当前有效时，加载器才会生成`ArkChatConformanceQualification`，并允许Adapter进入`LIVE_CURRENT`。手工填写一个Result Reference或Model字符串不能提升等级。

## 3. 失效依赖

以下任一变化使既有CC结果失效并要求重跑：

- Fixture、Adapter源文件、HTTP序列化或本地Schema Validator变化；
- Endpoint、Provider协议、非敏感配置指纹或Secret Reference名称变化；
- 请求或实际返回Model身份变化；
- no-tools、无会话、Schema约束JSON Object、Usage或Request ID行为变化；
- 结果超过30天有效期。

CC PASS只证明Adapter/Provider边界符合本Profile。模型是否能完成JWT影响分析仍由独立CE判断；二者都通过后还需要显式Strategy Activation。

## 4. 命名说明

| 名称 | 含义 |
|---|---|
| `ARK` | Volcengine Ark，火山方舟服务。 |
| `CHAT` | Chat Completions接口族；区别于Responses接口族。 |
| `no-tools` | Provider工具集合为空；不禁止平台在Provider调用之外执行受控Source Tool。 |
| `Profile` | 实现必须遵守的Provider-specific请求/响应规则，不是一次运行结果。 |
| `Qualification` | 已验证且未过期的资格对象；它只允许进入下一道门禁，不等于生产激活。 |
