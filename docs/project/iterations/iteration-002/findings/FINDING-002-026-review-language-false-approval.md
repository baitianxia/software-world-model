---
id: FINDING-002-026
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-002-SLICE-001, FINDING-002-024]
code: [src/software_world_model/application_services/evidence_answer.py, src/software_world_model/ai_infrastructure/evidence_answer_strategy.py]
tests: [tests/test_evidence_answer_strategy.py, validation/evidence_answer_capability_iteration_002/suite.json]
iteration: ITER-002
classification: system-contract
disposition: require-explicit-independent-review-checks
target: SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING
---

# FINDING-002-026：独立审核会在事实完整时漏判响应语言

## Observation

陌生 Java 工程产品验证中，中文问题取得了事实完整、引用正确但全文为英文的 Draft。独立审核仍返回 `APPROVED`，说明只要求一个聚合决定和自由 Finding 时，模型可能让事实正确性掩盖响应语言这一独立质量维度。

## Evidence

`document-render-two-stage-pipeline` 的密封输入为中文，Evidence-first 输出为英文；对应审核调用没有要求逐项提交判断，最终错误放行。该行为与工程、框架和具体问题无关，是聚合审核协议的系统性弱点。

## Decision and disposition

审核输出改为必须逐项提交 Question Fidelity、Evidence Grounding、Request Completeness、Response Language、Relevance/Readability 五项布尔检查。只有全部为真且 Finding 为空才能批准；任何失败项都必须产生可执行 Finding。能力评测增加中文请求配英文答案的反例，要求审核返回定向重写，而不是加入语言或工程专用回答逻辑。
