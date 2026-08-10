---
id: FINDING-002-023
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-002-SLICE-001, FINDING-002-006, FINDING-002-015, FINDING-002-022]
code: [src/software_world_model/ai_infrastructure/agentic_knowledge_strategy.py]
tests: [tests/test_agentic_knowledge_strategy.py]
iteration: ITER-002
classification: iteration-design
disposition: separate-proof-boundary-from-minimal-visible-answer
target: ITER-002-SLICE-001
---

# FINDING-002-023：充分性证明集合不等于应逐条展示的答案集合

## Observation

Strategy `2.0.204` 通过六类能力评估后，在陌生工程产品任务中完成 159 次模型调用且没有 Provider 结果未知，但最终语义审核拒绝答案。候选答案把充分性证明中的 18 条正式记录全部逐条展示，其中同时包含关系推理与其前提事实，重复陈述 compile→render、普通元素分派、嵌入文档延迟处理和异常包装；一条分派事实还附带用户未问的文本框恢复细节。

## Evidence / reproduction

运行证据位于 `var/product-generic-v204-suite205-sealed-support-completeness/`，运行数据库为 `runtime/document-render-two-stage-pipeline/system-40a0301535b1792825438347b85153d38a8e16ce2d02992182837a9e9b7cccf1.sqlite3`。所有 159 个调用均为 `COMPLETED`。最终审核明确指出 `claim:N1:4`、`claim:N1:9`、`claim:N1:11` 和 `claim:N1:18` 分别重复已有事实，并指出文本框处理超出原问题范围；平台以 `CONTROL_STATE_DENIED` 失败关闭，未封存错误答案。

## Impact

这是与工程、语言和题型无关的职责边界问题。充分性证明可以合理保留关系命题及其前提，以便证明没有遗漏；如果答案层必须把每个证明记录都变成独立可见句子，完整性会退化为证据转储，造成重复、题外信息和较差的阅读顺序。反过来，答案层若无约束地精简，又会重现 `FINDING-002-022` 的关键遗漏。

## Classification rationale

变化只调整当前切片内部的证明与展示职责，不改变正式知识、充分性证明或外部接口语义，归类为 iteration-design。

## Decision and disposition

充分性最终支持集仍是封闭的证据边界，但不再要求每条证明记录成为独立可见答案。答案选择必须从原始问题建立逐项语义台账，并从该边界中选择文字上完整覆盖问题的最小、不重复子集：推理只能覆盖自身命题，不能隐式携带前提细节；关系摘要与前提事实重复时只保留能增加独立请求内容的一方；证明专用前提和题外细节不得仅因位于支持集中而展示。

答案最小性审核可从完整证明边界删除可见重复项。随后执行两次独立、只增不减的完整性审核；每次必须保留上一轮已选答案，只能补入其自身可见文字能唯一恢复缺失请求项的记录。顺序审核只处理最终可见子集，无法排序的已选记录仍须失败关闭，不能用删除隐藏缺陷。本决定替代 `FINDING-002-022` 中“答案层不得删除任何封存支持记录”的处置；该 Finding 关于充分性两次只增不减审核、推理不继承未显示前提文字以及失败关闭的其余决定继续有效。

调用次数和 Token 总量仍只是高位安全熔断，不能用来省略两次完整性审核或最终语义审核。

## Verification after disposition

新增和调整测试验证证明支持可以包含不需展示的重复记录、答案最小性可删除重复、两次完整性审核只能补充不能删除，以及请求中的连接关系会被补回。Strategy 升级为 `2.0.205`；相关 189 项测试和完整 435 项回归均通过。六类真实模型职责随后由 Codex 独立复核并取得当前 Strategy 的 PASS 资格。陌生工程产品复测仍需对“把冻结开源工程源码片段发送给火山用于验证”取得本次明确授权后执行。
