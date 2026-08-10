---
id: ITER-002-RESULT-CAPABILITY
kind: iteration-result
status: pass
authority: evidence
owners: [quality]
depends_on: [ITER-002-VERIFICATION, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
code: [src/software_world_model/ai_infrastructure/evidence_answer_strategy.py, src/software_world_model/ai_infrastructure/evidence_capability_evaluation.py, validation/evidence_answer_capability_iteration_002]
tests: [tests/test_evidence_answer_strategy.py]
iteration: ITER-002
---

# ITER-002 Result：Capability Evaluation

## Claim and scope

该结果证明 Evidence-first Strategy `1.0.0` 在 exact Ark no-tools 配置下通过十类冻结职责及反例评估。它只授权同一实现、配置、模型身份、Adapter、Suite 和有效期内的本机后续验证，不替代陌生工程 Product Validation 或 Activation。

## Exact inputs / baseline

- Suite：`general-evidence-answer-2026-08-10@1.3.0`，digest `sha256:0f06bd1572df8c7996b8a6c4eccd908e7193dcd12c06a0aa0b7296bedbdbb421`。
- Conformance：`ccrun_66bbedf18020445c9df5fac11526fda1`，result digest `sha256:dee384a90d89193952a83959ba9e9fed9e07faa2edbfabf13b094f47d740668f`。
- Provider：Volcengine Ark OpenAI-compatible Chat Completions；request model `glm-5-2-260617`，observed identity `glm-5.2`。
- 原始证据：`var/evidence-capability-v8-live/`。十类输出、十份审核草稿和十份 Codex 独立复核均已封存；所有 Provider 请求结果确定。

## Execution and evidence

十类能力为：问题保持、只读来源调查、带引用的自然答案生成、独立答案审核、固定 Evidence Packet 重写、证据缺口分类、响应语言审核、时间顺序审核、未证实意图审核、相关性与可读性审核。Codex 逐项对照冻结 Oracle，确认正例成立，并确认审核能拒绝语言错误、顺序颠倒、无依据目的、自检措辞与题外细节。所有规则只引用问题—证据—答案协议，没有工程、文件名、编程语言或题型分支。

## Result, failures and limitations

对 exact Evidence-first `1.0.0` subject 的结果为 `CAPABILITY_EVALUATION_PASS`。Result ID 为 `evaluation_result_26fdfbbea40b4c87aede82270eed68dd`，Result digest 为 `sha256:2273872f7cb8da02eb3da7c1c6c6096e8cbc865037877c02385da4e02e2c0f01`，Qualification digest 为 `sha256:3d529903152c6485372dbfe6671d3adffab72496e4c3c6a23a18a6766abacd54`，有效至 `2026-08-16T19:17:05.882130Z`。输入/输出 Token 为 `13288 / 1384`，observed model 为 `glm-5.2`。它本身不授权生产。

## Findings and system write-back

运行前后产生的审核语言、顺序、意图、相关性和角色契约修正发现已登记至 `FINDING-002-026`—`FINDING-002-030`，并处置到 Evidence Answering Contract、通用保护、能力反例及代码测试；没有未处置 Finding。

## Validity / supersession

Strategy、Prompt、Schema、模型身份、Adapter、配置、Suite 或有效期变化即失效。旧正式知识路径的资格均为不可变历史证据，不授权 Evidence-first 实现。
