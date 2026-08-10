---
id: FINDING-002-007
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-002-SLICE-001]
code: [src/software_world_model/ai_infrastructure/agentic_knowledge_strategy.py]
tests: [tests/test_agentic_knowledge_strategy.py, tests/test_product_holdout_world_answer.py]
iteration: ITER-002
classification: iteration-design
disposition: added-exhaustive-classification-and-negative-challenge
target: ITER-002-SLICE-001
---

# FINDING-002-007：空顺序结果缺少穷举证明

## Observation

事实阶段的两个顺序分析都可返回空 `call_return_spans`，却没有声明每条引用都已检查。答案阶段随后发现同一事实把帮助方法调用与返回后行为合并，但此时正式事实已经发布，答案重排无法拆分它，只能重复失败。

## Evidence / reproduction

Suite `2.0.4` 的第一次运行在约 33 次调用时以 `answer draft exhausted bounded contract retries` 停止。运行数据库显示事实阶段最终接受两个空 span 结果；答案阶段六次分析反复识别 `DocumentProcessor.process`、`findPolicy` 或 `DelegatePolicy.invoke` 周围的调用返回边界，但事实引用不可修改。

## Impact

这是通用的负向审核不完备问题，可能影响任何语言和框架的调用链。增加答案重试或总调用数不能修复已经发布的合并事实。

## Classification rationale

变化改进本轮 Strategy 的审核协议和回退位置，不改变正式知识 Owner 或外部接口，因此归类为 iteration-design。

## Decision and disposition

顺序协议升级为 `agentic-sequence-analyzer@6`：除发现的 span 外，每个 Need 必须穷举列出 atomic references；atomic 与 combined 必须无交集且并集等于完整引用集。事实阶段使用一个主分析和两个互不可见的独立审核，第二个独立审核明确挑战空 span 的负向结论。任何审核发现 span 都进入事实拆分修复，不能延迟到答案阶段。

## Verification after disposition

新增单元测试拒绝未穷举的 atomic 分类，并更新离线适配器验证三次事实顺序审核。Strategy 变为 `2.0.161`，旧 `2.0.160` 能力资格立即陈旧；V-005 和 V-006 必须按新身份重跑。
