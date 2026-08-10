---
id: ITER-002-PROPOSAL
kind: iteration-proposal
status: accepted
authority: project-proposal
owners: [product, engineering]
depends_on: [SYS-PRODUCT-SUCCESS, SYS-ARCH-INVARIANTS, SYS-QUALITY-ACCEPTANCE]
code: [src/software_world_model, validation]
tests: [tests]
iteration: ITER-002
coding_input: false
---

# ITER-002 Proposal：通用工程问答质量闭环

## Trigger and evidence

本机浏览器体验暴露了系统性问题：回答可能扩张用户问题、混入英文内部诊断模板、把同一调用链的先后顺序压缩为错误命题，或用某个工程的约定文件和题型词作为调查捷径。当前工作区已形成针对根因的未资格化代码变化，旧的 Strategy `1.38.0` 资格不再适用。

## Outcome and users

普通用户无需认证即可在仅回环地址开放的浏览器中连接任意本地 Git 工程，并用自然语言提出任意工程问题。系统以语言、框架、工程名称和题型中立的方式调查源码，给出与问题对应、顺序正确、来源可追溯的答案；证据不足时只陈述相关缺口或限制。

## Scope / non-goals

范围包括需求保持、通用来源调查、逐 Need 的事实复核、调用与返回后行为的顺序审计、答案复核、浏览器展示与会话隔离、预算强制和真实模型验收。

非目标包括认证、多租户、生产网络部署、写入用户工程、联网检索、特定语言解析器、特定项目问答规则、Schema Evolution 和生产 Activation。

## Adopted system IDs

- `SYS-ARCH-INVARIANTS`
- `SYS-CONTRACT-SOURCE-ARTIFACT`
- `SYS-CONTRACT-KNOWLEDGE-FACT`
- `SYS-CONTRACT-KNOWLEDGE-ADMISSION`
- `SYS-CONTRACT-KNOWLEDGE-PERSISTENCE`
- `SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE`
- `SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE`
- `SYS-CONTRACT-APPLICATION-AGENTIC-TASK`
- `SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING`
- `SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL`
- `SYS-CONTRACT-AI-MODEL-GATEWAY`
- `SYS-CONTRACT-AI-CAPABILITY-EVALUATION`
- `SYS-QUALITY-ACCEPTANCE`
- `SYS-OPS-LOCAL-BROWSER`

## Development slices and dependencies

本轮只有一个纵向切片：从任意本地 Git 工程和自然语言问题，经问题检查清单、来源调查、密封证据、答案控制，到浏览器展示和独立验收。根据 `FINDING-002-024` 与 `SYS-ADR-013`，正式知识沉淀改为非阻塞的独立能力。切片复用 exact Ark Adapter Conformance；任何 Strategy 行为变化都必须重新执行通用能力评估与产品留出验证。

## Risks and unknowns

- 同一基础模型的结构化输出存在随机失败，必须有有界重试且不能把偶发一次失败误判为实现结论。
- 增加独立复核会提高调用次数和 Token 消耗，必须在分派前强制预算。
- 长调用链容易把调用、被调内部行为和返回后的调用方行为合并，导致顺序不可能成立。
- 浏览器可读性优化不能改变正式 Claim 的权威边界。

## Verification and acceptance

先运行文档检查、相关单元与接口测试、完整测试套件；再用 exact Ark Conformance 输入运行六类通用能力评估；最后在冻结陌生工程问题上执行系统路径并由 Codex 基于源码独立判断正确性、遗漏和顺序。机械测试、能力评估、产品验证和本机启用互不替代。

## Authorization decision

用户已明确要求继续开发、优化为适用于任何工程和任何问题，并在 2026-08-09 再次表示“同意，无需确认”。本 Proposal 因此接受，但生产启用和外网发布仍不在授权范围。
