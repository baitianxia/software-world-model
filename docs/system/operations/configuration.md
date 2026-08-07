---
id: SYS-OPS-CONFIGURATION
kind: system-operations
status: current
authority: operational
owners: [operations, ai]
depends_on: [SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-QUALITY-SECURITY]
code: [src/software_world_model/ai_infrastructure/volcengine_ark_chat_adapter.py, src/software_world_model/interface/provider_cli.py]
tests: [tests/test_volcengine_ark_chat_adapter.py, tests/test_ark_chat_conformance.py]
---

# 非敏感模型配置

当前本地验证使用 `VOLCENGINE_ARK` 的 OpenAI-compatible Chat Completions Envelope：

| 项 | 当前配置 |
|---|---|
| Base URL | `https://ark.cn-beijing.volces.com/api/coding/v3` |
| Endpoint | 由 Adapter 确定性追加 `/chat/completions` |
| Request model reference | `glm-5-2-260617` |
| Adapter | `openai-chat-completions-no-tools@8` |
| Secret reference | `env:ARK_API_KEY` |
| Tools/session/stream | 禁用 |
| Thinking | `thinking.type=disabled` |

请求别名与 Provider 实际返回身份是不同字段，只有符合性和能力结果可以证明其当前匹配。配置、Adapter、Endpoint 或实现变化会使旧资格失效。

```bash
PYTHONPATH=src python3 -m software_world_model.interface.provider_cli status
PYTHONPATH=src python3 -m software_world_model.interface.provider_cli probe
```

`status` 不联网且不得显示密钥；`probe` 只证明最小传输，不替代完整 Contract Conformance、Capability Evaluation 或产品验收。
