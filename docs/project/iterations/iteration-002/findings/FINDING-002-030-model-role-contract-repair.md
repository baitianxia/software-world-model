---
id: FINDING-002-030
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-002-SLICE-001, SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING]
code: [src/software_world_model/ai_infrastructure/evidence_answer_strategy.py]
tests: [tests/test_evidence_answer_strategy.py, tests/test_product_holdout_evidence_answer.py]
iteration: ITER-002
classification: system-contract
disposition: bounded-role-contract-repair
target: SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING
---

# FINDING-002-030：完整模型响应仍可能因截断或语义缺项违反角色契约

## Observation

复杂产品问题中，答案生成结果曾因输出长度结束而留下不完整 JSON；另一次审核结果虽然形状接近合法，却提交了没有绑定证据的重写 Finding。Provider 请求均有确定结果，失败位于角色输出契约，不是网络结果未知。

## Impact

若第一次可修正输出直接终止问答，会把模型表达波动变成用户可见故障；若平台自行补字段或删除内容，又会伪造模型判断并可能降低完整性。只修生成角色也不足以保证独立审核可靠。

## Decision and disposition

生成与审核角色统一采用有界契约修正：固定原问题、Evidence Packet 和角色职责，携带精确错误及终止原因，要求提交完整替换对象。截断修正只能压缩表达，不能删除物质内容、证据或审核维度；语义缺项也必须由对应角色重新判断。无进展、耗尽或 Provider 结果未知仍失败关闭。
