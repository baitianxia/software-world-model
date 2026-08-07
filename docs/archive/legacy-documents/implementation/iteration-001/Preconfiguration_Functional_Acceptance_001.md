# Iteration 001 配置前功能验收 001

| 元数据 | 值 |
|---|---|
| Acceptance ID | `SWM-IMP-PRECONFIG-ACCEPT-001` |
| Date | 2026-08-06 |
| Status | `PASS — READY FOR LIVE CONFIGURATION` |
| Scope | 不使用真实API凭据、不调用真实Provider的本地功能验收 |
| Next Gate | `0R-B Live Adapter Conformance` |

## 1. 验收结论

系统已经具备进入真实Provider配置阶段所需的本地功能闭包。现在配置真实Provider不会再承担“补齐基础产品入口”的职责，而只用于验证Provider边界和模型能力。

该PASS不是Iteration 001产品验收：自然语言Requirement规划、真实模型Tool Proposal / Candidate、Live Provider Conformance、JWT Capability Run和Product Holdout仍未执行。

## 2. 已验收功能

| ID | 功能 | 结果 |
|---|---|---|
| PFA-01 | CLI配置Scope、Local Git Source和Binding，并恢复同一Management Result | PASS |
| PFA-02 | CLI解析exact Revision / Path / Java Symbol / Comparison | PASS |
| PFA-03 | CLI执行有界Knowledge Update并发布Snapshot | PASS |
| PFA-04 | CLI对exact Snapshot执行逐Need Sufficiency并返回Proof / Gap | PASS |
| PFA-05 | loopback HTTP提供Health、Capabilities、Knowledge Update和Task Query | PASS |
| PFA-06 | OpenAI Responses Adapter生成显式空Tools、无会话、`store=false`请求 | PASS |
| PFA-07 | Structured Output由应用再次按closed Schema验证；Tool Output、Refusal、Incomplete和未知身份失败关闭 | PASS |
| PFA-08 | Source、Update、Use和Model Call支持结构化Telemetry、Correlation、资源量及明确Cost状态 | PASS |
| PFA-09 | HTTP请求大小、JSON类型和loopback监听边界失败关闭 | PASS |
| PFA-10 | 生产回归、历史Demo回归和编译检查 | PASS |

HTTP当前不提供认证，因此只允许绑定`127.0.0.1`、`::1`或`localhost`。远程部署、SSO和多租户仍不在本迭代范围内。

## 3. OpenAI Adapter实现依据

Adapter使用Responses API的`POST /v1/responses`，显式发送`tools: []`、`tool_choice: none`、`parallel_tool_calls: false`、`store: false`和`stream: false`。Structured Output使用`text.format`的strict JSON Schema，并在Provider返回后由应用再次执行closed-field、required、type、enum及本地Reference验证。

实现核对了OpenAI官方[Responses API参考](https://developers.openai.com/api/reference/resources/responses/methods/create)、[Structured Outputs指南](https://developers.openai.com/api/docs/guides/structured-outputs)和[GPT-5.6升级指南](https://developers.openai.com/api/docs/guides/upgrading-to-gpt-5p6-sol.md)。当前官方推荐不被硬编码为生产资格；实际Model Reference仍必须在配置、Live CC和Capability Evaluation中形成exact证据。

## 4. 验证证据

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
# Ran 84 tests — OK

PYTHONPATH=demo python3 -m unittest discover -s demo/tests -q
# Ran 121 tests — OK

PYTHONPATH=src python3 -m compileall -q src tests
# exit 0
```

新增验收覆盖：

- `tests/test_openai_responses_adapter.py`
- `tests/test_interface_runtime.py`
- `tests/test_telemetry.py`

## 5. 下一阶段配置输入

进入`0R-B`时才提供并绑定：

1. API凭据的Secret Reference；
2. Provider Project / Organization（如适用）；
3. exact Model Reference及允许的alias→revision观察政策；
4. Prompt Program和Output Schema exact版本；
5. Live Conformance Result存放位置、网络捕获和失效策略；
6. Token、超时、成本和数据分类限制。

配置动作不得把Secret写入SQLite、CLI参数、请求捕获、Telemetry或错误正文。未完成Live CC前，Adapter必须继续保持`OFFLINE_FIXTURE`或Held状态。

## 6. 配置后续记录

2026-08-06 已按用户选择应用火山方舟OpenAI-compatible Chat Completions的非敏感配置，详见[真实模型Provider配置记录 001](Live_Provider_Configuration_001.md)。本验收原始`84 / 84`证据保持不变；后续方舟适配、能力评估机制、专项任务验证、模型角色输入授权、安全恢复、独立比较规则、通用任务模型边界、可恢复模型调用、知识缺口更新重评、六类职责完整评估、任一提示词候选召回、需求、来源、事实与回答的有限修正、重复正文去重、逐任务产品对照、未见项目清单封存和仓库漂移检测、已授权答案准备入口，以及“能力评估与独立产品验收必须同时有效”的启动门禁加入后，当前生产回归为`253 / 253`。当前通用方案已完成真实模型能力评估和Codex独立复核；产品未见项目验收与生产启用仍未完成，因此本记录的原`PASS — READY FOR LIVE CONFIGURATION`结论没有被提升为产品验收。
