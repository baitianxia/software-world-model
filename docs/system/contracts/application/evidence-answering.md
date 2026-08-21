---
id: SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING
kind: system-contract
status: current
authority: normative
owners: [application, quality]
depends_on: [SYS-CONTRACT-SOURCE-ARTIFACT, SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-AI-CAPABILITY-EVALUATION, SYS-ADR-013, SYS-ADR-016]
code: [src/software_world_model/application_services/evidence_answer.py, src/software_world_model/ai_infrastructure/evidence_answer_strategy.py, src/software_world_model/interface/runtime.py]
tests: [tests/test_evidence_answer.py, tests/test_evidence_answer_strategy.py, tests/test_browser_chat_interface.py]
---

# Direct Evidence Answering

## Purpose and scope

本契约定义显式 `DIRECT_INVESTIGATION`：保持原问题、调查 exact 授权源码、密封任务级证据、生成自然答案并独立复核。它不负责把证据发布为跨任务正式知识，也不得被标记为 `WORLD_MODEL` 回答。

ADR-016 的 `ENGINEERING_QA` 会复用受控来源操作、密封和独立审核原则，但它同时绑定 World Model Result/Gap，并使用独立 Question Evidence Package 与 Request/Result/Qualification 身份。它不是调用本服务的静默 fallback；本契约的余下规则仍只适用于显式 `DIRECT_INVESTIGATION`。

## Ownership

Evidence Answering Application Service 拥有不可变 Question Checklist、Evidence Packet 和来源调查编排；Source Integration 独占来源操作与 Artifact；Response Control 拥有 Answer Draft Revision、Review Decision 和最终放行。模型角色只提交结构化 Proposal。

## Invariants

1. Question Checklist 保留 original request、响应语言、全部物质性问题、条件、比较、关系和输出约束；它不能根据当前已发现证据删减问题，也不能注入工程或题型模板。
2. 每个来源动作由平台针对 exact Scope、Binding、Target、Revision、Tool 参数和预算重新授权。Evidence Packet 只接收成功或明确 partial 的 Source Operation/Artifact，并绑定 Checklist Digest、Target Digest、Operation Reference、内容 Digest、定位和实际内容。
3. Evidence Packet 密封后不可改写。补充调查形成具有新 Digest 的新 Packet；旧 Packet 和审核结果不伪装成新包的审核。
4. SUPPORTED Answer Section 至少引用一项当前 Packet Evidence，且其全部实质内容必须由引用支持；UNKNOWN Section 不得携带虚假 Evidence Reference。Answer Text 不能成为自身证据。
5. 生成角色无来源工具；审核角色无来源工具、生成 rationale 或隐藏上下文。审核必须从 original request 独立重建检查项，并分别提交 Question Fidelity、Evidence Grounding、Request Completeness、Response Language、Relevance/Readability 五项检查；不能用某一项正确抵消另一项失败。Evidence Grounding 必须逐项核对时间顺序，并区分源码直接呈现的机制与未记载的目的、动机或因果解释。Relevance/Readability 必须拒绝面向系统的自检说明、审核措辞、机械证据转储和没有回答原问题的源码细节。
6. `REWRITE_REQUIRED` Finding 必须指向同包已有 Evidence；Response Control 只把同一 Packet、旧 Draft 和具体 Finding 交给生成角色。`MORE_EVIDENCE_REQUIRED` 必须指出具体证据缺口，由 Application 决定是否执行针对性调查。
7. 只有五项审核检查全部通过且 Finding 为空的 `APPROVED` Draft 可以形成 Authorized Evidence Answer。任一失败检查必须绑定具体 Finding。Provider 已完整返回但生成或审核输出违反 JSON、Schema 或应用语义约束时，对应角色只能在固定职责输入下有界提交完整替换对象；因输出截断触发的修正必须压缩表达并保留全部物质内容，不能用删除检查项或证据换取合法形状，也不能规范化成平台猜测的答案。审核 Unknown、修正无进展或耗尽、重复来源动作及安全熔断均失败关闭，不降级为未经审核答案。
8. 调用配额不构成质量裁剪策略；实现可以用高安全熔断阻止失控循环，但不得因剩余调用数减少检查清单、证据要求或独立审核。
9. Evidence Packet 与 Answer Draft 默认只对当前问题有效。异步知识沉淀必须重新进入 Knowledge Update、Admission 与 Publication，不能继承回答审核作为正式知识资格。
10. 请求、结果、Telemetry 与浏览器必须保留 `DIRECT_INVESTIGATION` 模式身份。世界模型查询失败不能静默调用本服务；任何切换都需要新的显式请求和独立结果。

## Recovery and implementation boundary

幂等标识、Model Execution Reference 和 Source Operation Reference 必须稳定；已分派外部结果未知时不得盲目重发。具体 DTO、最大安全熔断和显示投影由代码与测试定义，但不能改变以上授权、固定输入和审核边界。
