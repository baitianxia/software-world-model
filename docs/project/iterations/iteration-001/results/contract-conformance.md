---
id: ITER-001-RESULT-CONFORMANCE
kind: iteration-result
status: pass
authority: evidence
owners: [ai, quality]
depends_on: [ITER-001-SLICE-004]
code: [src/software_world_model/ai_infrastructure/volcengine_ark_chat_adapter.py, src/software_world_model/interface/provider_cli.py]
tests: [tests/test_ark_chat_conformance.py, tests/test_volcengine_ark_chat_adapter.py]
iteration: ITER-001
valid_until: 2026-09-05T21:04:18.073701Z
---

# Ark Chat Contract Conformance Result

## Exact subject

| Field | Value |
|---|---|
| Provider | `VOLCENGINE_ARK` |
| Protocol | `OPENAI_COMPATIBLE_CHAT_COMPLETIONS` |
| Adapter | `openai-chat-completions-no-tools@8` |
| Adapter implementation digest | `sha256:b0eed0252ab7bfd723bf9cb06b0e48d3ccd2e1c6f6d51ee2c26cdc027509d774` |
| Request model reference | `glm-5-2-260617` |
| Observed model identity | `glm-5.2` |
| Non-sensitive config digest | `sha256:420f553a3ce0075818550e08cb1351ce69eaf9871c5a0257aecf88b7b32b88fd` |

## Result

Run `ccrun_66bbedf18020445c9df5fac11526fda1` 的两次真实调用与 12 项 Oracle 全部 PASS；完成时间为 `2026-08-06T21:04:18.073701Z`，Result Digest 为 `sha256:dee384a90d89193952a83959ba9e9fed9e07faa2edbfabf13b094f47d740668f`，日期有效上限为 `2026-09-05T21:04:18.073701Z`。

该结果证明 exact Adapter/Endpoint/配置在运行时符合 no-tools Chat Contract。它不证明通用业务能力、产品价值或生产资格；Provider CLI 摘要明确报告 `production_eligible=false`，CC Result 本身不授予生产资格。

## Supersession and limitations

历史 @5/@7、旧 Endpoint 和 OpenAI Responses Profile 结果不匹配当前 subject，不能加载。Adapter、配置、Endpoint、实现摘要、请求/实际模型身份或 Fixture 变化后必须重跑。

原始 sanitized Result 位于本机 `var/`，不在 Git。版本化原始说明由基线 `476517b` 保存，可用 `git show 476517b:docs/implementation/iteration-001/Live_Provider_Configuration_001.md` 与 `git show 476517b:docs/implementation/iteration-001/conformance/CC-ARK-CHAT-NO-TOOLS-001.md` 查看。
