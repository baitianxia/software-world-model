---
id: FINDING-002-022
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-002-SLICE-001, FINDING-002-006, FINDING-002-015, FINDING-002-021]
code: [src/software_world_model/ai_infrastructure/agentic_knowledge_strategy.py]
tests: [tests/test_agentic_knowledge_strategy.py]
iteration: ITER-002
classification: iteration-design
disposition: separate-minimality-from-add-only-completeness-and-seal-support
target: ITER-002-SLICE-001
---

# FINDING-002-022：下游再次精简会删除已证明的必要答案内容

## Observation

Strategy `2.0.203` 的产品运行完成 107 次模型调用并机械封存答案。Codex 对冻结源码独立复核后拒绝验收：答案没有陈述 `XWPFTemplate.compile` 通过 `resolver.resolveDocument` 解析模板元素，也只说嵌入文档阶段调用 `applyDocxPolicy`，没有说明该阶段再次选择 `DocxRenderPolicy`、计算数据并调用策略。原始问题明确要求元素如何解析以及策略如何调用。

## Evidence / reproduction

证据位于 `var/product-generic-v203-suite205-persistent-answer-repair/`。正式快照已经包含完整事实：`knowledge_fact_e57d2d7776b09f19f4413d4dc80d381b` 陈述 compile 的解析调用，`knowledge_fact_7b2ac47c79c358c9796a21502607642c` 陈述嵌入文档策略的实际调用。充分性输出却没有选择这两条，并把推理摘要当成包含了前提事实中未写入摘要的细节。其后答案选择又从充分性已选的六条记录中删除两条，尽管充分性最小性审核刚认定它们对策略选择与调用是必要的。答案最小性、答案完整性和两次最终语义审核均重复放行同一遗漏。

## Impact

这是跨工程、语言和题型的系统性完整性风险：一个推理记录的前提可能比推理命题包含更多用户明确要求的细节；下游若把前提内容隐式算入推理，或对已经最小化的支持集再次做语义删除，都会产生来源中有答案但最终展示缺失的假完整结果。增加相同形式的批准调用不能修复这类职责重叠。

## Classification rationale

变化调整当前切片内部的充分性与答案编排，不改变对外接口或正式知识记录语义，归类为 iteration-design。

## Decision and disposition

充分性先执行删除式最小性审核，再执行两次独立、只允许增加的完整性审核。完整性审核必须从原始请求建立逐项语义覆盖，推理只覆盖自身命题，不能隐式继承前提中未写入命题的文字；两轮审核都必须保留上一轮全部支持，只能补入完整读集中独有且用户确实要求的记录。

充分性最终支持集成为答案阶段的封存边界。答案选择、答案最小性和答案完整性审核可以调整顺序，但不得删除任何封存记录。若顺序审核确认某条封存事实无法单点排序，系统必须失败关闭并要求上游发布拆分事实，不能通过删除该记录产生不完整答案。本决定替代 `FINDING-002-021` 中“答案阶段排除无法排序记录”的处置部分；该 Finding 关于修复详情传递和顺序缺陷须独立确认的其余决定继续有效。

## Verification after disposition

新增测试验证充分性完整性审核能补回初始选择遗漏的必要记录、答案阶段删除封存支持时会修复重试，以及无法排序的封存支持不会被静默删除。Strategy 升级为 `2.0.204`；`2.0.203` 的能力资格和机械封存产品结果不能授权新实现。
