---
id: FINDING-002-018
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-002-SLICE-001, FINDING-002-017]
code: [src/software_world_model/ai_infrastructure/agentic_knowledge_strategy.py]
tests: [tests/test_agentic_knowledge_strategy.py]
iteration: ITER-002
classification: iteration-design
disposition: preserve-exact-adjacent-fragment-overlap
target: ITER-002-SLICE-001
---

# FINDING-002-018：顺序片段的最小词边界重叠会丢失正向证据

## Observation

Strategy `2.0.199` 的产品运行建立 132 条模型调用记录，其中 131 条完整、1 条 Provider 结果未知。验证器因此正确拒绝整轮；但运行仍完成知识、充分性和答案阶段，形成了可用于诊断的候选答案。该答案再次把调用和返回后行为合并，机械答案审核却批准。

事实顺序独立审核已识别 `renderInclude` 事实中的真实调用返回跨度：调用片段为“调用 template.reload”，时间连接片段为“后再”，后续行为片段为“再调用 applyDocxPolicy”。三个片段都逐字来自同一正式事实，语义顺序成立，但时间连接片段的末字同时是后续行为片段的首字。

## Evidence / reproduction

证据位于 `var/product-generic-v199-suite205-positive-sequence-evidence/`。运行数据库中 `FACT_SEQUENCE_ANALYSIS` 共 37 次调用；`model_call_0d4c08fdc39547ffae511c0872cf271a` 返回上述跨度，同时把全部引用留在原子列表。`FINDING-002-017` 的正向证据优先规则已消除重复原子标签，但解析器只从时间连接片段结束位置之后查找后续行为，因此找不到从连接片段内部最后一个字开始的精确后续短语，并在允许忽略无效跨度的审核路径中静默删除该跨度。

同轮最终答案仍把 `ElementProcessor` 的策略查找与返回后分支合并，也把 `renderInclude` 的 `reload` 调用与返回后的 `applyDocxPolicy` 合并；因此即使没有那条 Provider 结果未知，该答案也不能由 Codex 独立验收。

## Impact

这是自然语言片段边界的通用问题，不依赖中文、Java、工程名或具体方法名。时间连接词和后续动作短语可能共享一个最小词素；把“精确文本”误解为“片段绝不重叠”，会让已经找到的正向质量缺陷在进入独立争议裁决前消失。多次否定审核随后看似形成一致结论，但它们没有反驳被平台先删除的证据。

## Classification rationale

问题位于平台的通用顺序证据解析和合并边界，属于当前切片的 iteration-design 修订。它不是调用次数不足，也不能通过增加次数或针对留出工程添加规则解决。

## Decision and disposition

保持调用片段与时间连接片段不重叠。后续行为优先从连接片段结束后查找；若找不到，只允许它从连接片段内部开始，并同时满足：重叠内容是连接片段的精确后缀和后续行为的精确前缀，且后续行为必须延伸到连接片段之外。这样只规范化相邻自然语言的最小词边界，不接受操作片段重叠、逆序、虚构文本、纯标点或没有独立后续行为的跨度。

规范化后的正向跨度继续进入现有独立报告计数和争议裁决，不由单次模型判断直接形成拆分结论。Prompt 明示优先返回不重叠片段，并说明仅允许上述精确词桥重叠。

## Verification after disposition

新增回归测试覆盖通用英文连接词与后续动作共享词桥的情形，并用失败运行的原始审核输出重放，确认 `renderInclude` 跨度现在被保留。Strategy 升级为 `2.0.200`；`2.0.199` 的能力资格和产品运行不能继承。
