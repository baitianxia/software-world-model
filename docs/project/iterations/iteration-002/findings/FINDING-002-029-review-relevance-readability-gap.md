---
id: FINDING-002-029
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-002-SLICE-001, SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING]
code: [src/software_world_model/ai_infrastructure/evidence_answer_strategy.py, validation/evidence_answer_capability_iteration_002]
tests: [tests/test_evidence_answer_strategy.py]
iteration: ITER-002
classification: system-contract
disposition: independent-relevance-readability-role
target: SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING
---

# FINDING-002-029：来源正确不等于回答相关且可读

## Observation

陌生工程产品运行曾生成来源可核对的答案，却包含“回答语言与原始请求一致”这类面向审核者的自检说明，并附带原问题没有要求的源码事实。已有来源闭合和语言检查都不能拒绝这种输出。

## Impact

这是问题—证据—答案协议的通用质量缺口。若只检查每句话是否有来源，系统仍可能把内部审核记录或无关事实展示给用户，重现旧架构的机械知识转储问题。

## Decision and disposition

把相关性与可读性设为独立审核维度：拒绝自检说明、审核措辞、机械证据平铺和未回答原问题的细节；任何失败必须返回可执行 Finding。能力套件增加独立反例，证明该维度不能被来源正确、内容完整或响应语言正确所抵消。规则只依赖原问题与证据，不含工程、语言或题型特例。
