# Iteration 001 真实模型 Provider 配置记录 001

| 元数据 | 值 |
|---|---|
| Configuration ID | `SWM-IMP-LIVE-PROVIDER-CONFIG-001` |
| Date | 2026-08-07 |
| Status | `CODING PLAN @8 LIVE CC / GENERAL CAPABILITY / PRODUCT VALIDATION PASS` |
| Provider | `VOLCENGINE_ARK` |
| Protocol | `OPENAI_COMPATIBLE_CHAT_COMPLETIONS` |
| Adapter | `openai-chat-completions-no-tools@8` |
| Next Gate | `Explicit scoped activation decision` |

## 1. 已应用配置

| 配置项 | 当前值 | 处理方式 |
|---|---|---|
| Base URL | `https://ark.cn-beijing.volces.com/api/coding/v3` | 用户配置的北京地域Coding Plan OpenAI兼容基地址 |
| Endpoint | `https://ark.cn-beijing.volces.com/api/coding/v3/chat/completions` | Adapter从Base URL确定性追加`/chat/completions`；Host、Path、Query和用户信息严格校验 |
| Model Reference | `glm-5-2-260617` | 作为exact请求值冻结；项目不自行推断名称后缀的语义 |
| API Key | `env:ARK_API_KEY` | 只保存Secret Reference；真实值仅在HTTP分派前从环境解析 |
| Output | `json_object` + 确定性Schema System Message + 应用侧closed Schema复验 | 当前模型明确拒绝`json_schema`；完整Schema仍进入线协议并在返回后严格复验，不降级为未验证文本 |
| Thinking | `thinking.type=disabled` | GLM-5.2默认思考会产生独立`reasoning_content`；本Profile固定关闭，且CC逐请求验证 |
| JSON Normalization | `IDENTITY`或受限单围栏规范化 | 只提取唯一JSON围栏；尾随文本、多围栏和结构化前缀失败关闭，结果记录Normalization类型 |
| Tools / Session | `tools=[]`、`tool_choice=none`、`stream=false`、单次完整请求 | 不启用Provider Tool、历史会话、附件或托管检索 |
| Network Route | direct HTTPS；忽略ambient `HTTP_PROXY` / `HTTPS_PROXY` | 防止Bearer凭据进入非配置代理，并符合Adapter直连边界 |
| TLS Trust | Python默认CA；缺失时加载可读的操作系统CA Bundle | 始终保持证书校验；不得使用unverified context或关闭Hostname验证 |

当前非敏感配置指纹为`sha256:420f553a3ce0075818550e08cb1351ce69eaf9871c5a0257aecf88b7b32b88fd`。该摘要覆盖Provider、协议、Adapter、Base URL、实际Endpoint、请求Model Reference、预期实际Model Fingerprint和Secret Reference名称，不覆盖API Key值。

## 2. “OpenAI兼容”的准确边界

火山方舟支持用OpenAI兼容客户端或等价HTTP Envelope访问API，但兼容性仍按接口族区分：

- 本配置使用Coding Plan Base URL `/api/coding/v3`；Adapter实际POST到`/api/coding/v3/chat/completions`，对应Chat Completions的`messages`、`max_tokens`、`choices`和`usage.prompt_tokens/completion_tokens`。
- 项目原有OpenAI Adapter使用`/v1/responses`，对应`input`、`max_output_tokens`和`output` Item；两种Envelope不能直接互换。
- Adapter会拒绝非`chat.completion`响应、非`stop`终止、Tool Call、Refusal、缺失身份、非法JSON和Schema不匹配。
- 方舟与GLM官方资料均定义`thinking.type=disabled`；当前Adapter把它作为固定协议字段，不接受单次调用覆盖。
- Provider响应中的`model`仅作为实际返回身份记录；在Live CC和Capability Evaluation前，不自动视为已评测的不可变模型指纹。

方舟官方Chat API资料确认了API Key Bearer鉴权与Chat Envelope结构：[ChatCompletions API](https://api.volcengine.com/api-docs/view?action=ChatCompletions&serviceCode=ark&version=2024-01-01)。[火山引擎Coding Plan接入说明](https://developer.volcengine.com/articles/7615528054736945158)确认OpenAI兼容Base URL为`/api/coding/v3`，并说明它与在线推理`/api/v3`的计费和模型范围不同。旧Endpoint上的探测不能证明`glm-5-2-260617`在Coding Plan网关可用；exact Model资格必须由新Probe和CC确定。

## 3. 命名含义

| 名称 | 含义 |
|---|---|
| `ARK` | 火山方舟（Volcengine Ark）模型服务；不是API Key本身。 |
| `VOLCENGINE_ARK` | 平台内部Provider Type，用于与`OPENAI`等Provider明确区分。 |
| `OPENAI_COMPATIBLE_CHAT_COMPLETIONS` | 请求/响应Envelope兼容Chat Completions；不表示使用OpenAI运营的Endpoint，也不表示兼容Responses API。 |
| `CC` | Contract Conformance，契约符合性验证。 |
| `CC-ARK-CHAT-NO-TOOLS-001` | 方舟Chat Adapter的专用CC Fixture；`001`是该Fixture的稳定编号，不是测试通过次数。 |
| `CE` | Capability Evaluation，判断exact Model / Prompt / Strategy是否达到业务Capability门槛；不与CC共用结论。 |
| `OUTCOME_PENDING` | 已分派外部调用结果尚不能证明；不能写成失败、零Usage或PASS。 |
| `LIVE_CURRENT` | Adapter已加载当前、摘要可验证且未过期的Live CC资格；不表示业务模型已通过CE。 |
| `no-tools` | Provider侧工具集合必须为空；平台工具或知识操作仍由平台自身控制。 |
| `model_ref` | 请求使用的模型引用；此处为`glm-5-2-260617`。 |
| `actual_model_fingerprint` | Provider响应实际返回的`model`身份；在资格策略中必须与已评测记录匹配。 |
| `Secret Reference` | 指向密钥存放位置的引用，如`env:ARK_API_KEY`，不包含密钥值。 |
| `ccrun_*` | 一次CC运行的不可变ID；随机后缀不表示Case数量或PASS次数。 |
| `jwtrun_*` | 一次JWT Run Configuration或World执行的不可变ID；必须同时使用Digest辨识内容。 |

## 4. 使用入口

查看配置不会访问网络，也不会输出密钥：

```bash
PYTHONPATH=src python3 -m software_world_model.interface.provider_cli status
```

密钥应先在本地终端或Secret Manager中注入。由于当前密钥曾通过聊天明文发送，应先在方舟控制台轮换，再注入新值；不得把它写进仓库、CLI参数或SQLite。

注入后执行最小传输探测：

```bash
PYTHONPATH=src python3 -m software_world_model.interface.provider_cli probe
```

`probe`只验证鉴权、Endpoint、Chat Envelope、Schema约束JSON响应、返回身份和Usage，不会把结果提升为生产资格。网络结果未知时CLI返回结构化`PROVIDER_OUTCOME_UNKNOWN`和受控原因码；Provider明确返回HTTP错误时保留安全的`http_status`、Provider Error Code / Type和Request ID，不输出Python traceback、响应原文、Provider Message或底层敏感信息。当前Coding Plan Probe、完整接口符合性验证、通用能力评估和六题产品验收均已PASS；后续只剩显式生产启用决策。

Provider、Endpoint、Adapter、Fixture或实现摘要变化后，使用以下入口重新执行方舟专用CC：

```bash
PYTHONPATH=src python3 -m software_world_model.interface.provider_cli conformance \
  --result-directory ./var/conformance \
  --operator local-operator
```

该命令执行两次真实调用，并以只创建不覆盖方式保存sanitized Result。Fixture与Result Schema见[CC-ARK-CHAT-NO-TOOLS-001](conformance/CC-ARK-CHAT-NO-TOOLS-001.md)。CC PASS后CLI仍报告`production_eligible=false`，因为CC命令不读取或回写下游JWT CE与Strategy Activation；后续资格必须从独立CE Registration判断。

## 5. 当前证据与剩余门禁

- Adapter、配置、Transport、Probe和CC运行器已有自动化测试；精确全量计数以最新回归输出为准。
- 当前进程只通过`env:ARK_API_KEY`解析凭据；配置、日志、CC和JWT产物均不保存或回显值。
- 已封存并复验当前`CC-ARK-CHAT-NO-TOOLS-001`的PASS Result；只有显式加载该结果的Adapter才会进入`LIVE_CURRENT`，未加载时仍默认为`OFFLINE_FIXTURE`。

当前Coding Plan @8 Live CC Result为`ccrun_66bbedf18020445c9df5fac11526fda1`，Result Digest为`sha256:dee384a90d89193952a83959ba9e9fed9e07faa2edbfabf13b094f47d740668f`。两次请求的12项Case全部PASS，聚合Usage为Input 318 / Output 72 tokens；请求模型别名为`glm-5-2-260617`，两次实际响应身份均为`glm-5.2`。配置指纹为`sha256:420f553a3ce0075818550e08cb1351ce69eaf9871c5a0257aecf88b7b32b88fd`。

当前接口符合性结果已绑定六类通用能力证明和六题产品验收记录；Codex作为独立评审来源重读项目源码并逐项比较两侧答案。接口符合性、能力评估、产品验收和生产启用仍是独立门禁，前三项通过不会自动触发生产启用。

历史@7和@5真实结果继续保留，但加载器会因实现摘要、Adapter版本或配置指纹变化拒绝它们。当前@8接口符合性产物仍保留`production_eligible=false`，因为接口验证不能替代下游能力证明、产品验收或显式启用。生产启用仍未执行。

旧在线推理Endpoint下的Direct Draft、Oracle和Run Configuration保留为历史证据，但其Adapter Version与配置指纹不再匹配当前@7，不能继续用于World Run。旧Endpoint曾明确返回`HTTP 403 / AccountOverdueError / Forbidden`；当前Coding Plan Probe已PASS，证明旧错误不能外推到新网关。

## 6. 连接故障修正记录

首次用户侧探测返回`ProviderOutcomeUnknown`。无凭据可达性检查证明：ambient代理路径尝试连接`127.0.0.1`并被拒绝；绕过代理后Endpoint完成DNS与TLS并返回预期未鉴权`401`。修正代理后第二次探测返回`TLS_FAILURE`；进一步检查证明实际Python为`/Users/baitianxia/.local/bin/python3`，其OpenSSL没有默认CA File或CA Path，而`/etc/ssl/cert.pem`可用。显式使用该系统CA后Python完成TLS并返回预期诊断`401`。因此问题分类为“环境代理配置 + Python CA缺失 + CLI错误投影缺陷”，不是已有证据能够证明的API Key或模型错误。

修正后方舟和OpenAI直连Transport均不再继承环境代理；Python没有默认CA位置时会加载可读的操作系统CA Bundle，且不会关闭证书或Hostname验证。方舟CLI会把连接拒绝、DNS、证书验证、TLS、Timeout、远端无响应断开和一般Network Failure投影为受控原因码。真实Direct运行进一步证明GLM默认Thinking会产生独立`reasoning_content`并在长结构化生成中触发远端断开；@5按方舟与GLM官方契约固定`thinking.type=disabled`后，CC与Direct均成功完成。
