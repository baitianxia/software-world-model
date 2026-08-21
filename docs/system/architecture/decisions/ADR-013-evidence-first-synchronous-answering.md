---
id: SYS-ADR-013
kind: system-decision
status: accepted
authority: normative
owners: [architecture, application, quality]
depends_on: [SYS-ADR-002, SYS-ADR-003, SYS-ADR-006, SYS-ADR-010]
code: [src/software_world_model/application_services/evidence_answer.py, src/software_world_model/ai_infrastructure/evidence_answer_strategy.py]
tests: [tests/test_evidence_answer.py, tests/test_evidence_answer_strategy.py, tests/test_browser_chat_interface.py]
---

# ADR-013：直接源码调查采用证据优先路径

## Context

把一次用户问答先转换为正式 Fact、Inference、Sufficiency Proof 和逐条 Answer Claim，会让多个模型阶段共同决定答案应包含什么。复杂问题容易在事实最小化、完整性、顺序和答案最小化之间反复失效；即使源码已正确读取，用户仍可能得到机械平铺的证明记录，或因一个中间结构化阶段失败而完全没有答案。

正式知识适合跨任务复用和长期治理，但它的准入、发布和快照一致性成本不应成为“直接调查源码”这一独立能力的固定关键路径。直接调查与软件世界模型回答是不同产品模式。

## Decision

显式 `DIRECT_INVESTIGATION` 模式执行：原问题理解与检查清单、受授权只读源码调查、密封 Evidence Packet、自然答案生成、独立答案审核，以及在同一 Evidence Packet 上按具体 Finding 定向重写。

Evidence Packet 是绑定 exact 来源目标、来源操作、Artifact 内容和原问题检查清单的任务级权威输入，但不是正式 Fact 或 Snapshot 成员，不能直接取得跨任务复用资格。生成角色只能读取密封包；审核角色从原问题独立重建检查项并逐项校验正确性、完整性、引用、条件、关系、相关性和可读性。若现有证据足够，重写必须保持 Packet Digest 不变；若审核证明证据不足，Application 只进行针对性授权调查并密封新 Packet。任何审核未知、未通过或不收敛都失败关闭。

Knowledge Update、Admission、Publication 和 Knowledge Use 保留为显式或后台知识沉淀能力。直接调查回答通过审核后可以异步提议沉淀，但回答成功不依赖该异步结果，Evidence Packet 也不能绕过正式知识准入。

`WORLD_MODEL` 模式不适用本决定：它只能读取 exact Snapshot 与其派生只读 View，不得读取 Source、创建 Evidence Packet、触发 Knowledge Update 或在知识不足时静默回退到本模式。`WORLD_MODEL` 的精确边界由 ADR-014 拥有；ADR-016 另行定义事先声明 World Model + Source 组合证据的 `ENGINEERING_QA`，不改变本模式语义。

## Alternatives

- 继续扩展正式知识优先链路的修复次数：保留了根因，阶段间约束和失败面继续增长。
- 让一个模型一边调用源码工具一边直接完成答案：实现较短，但检索、生成和自审共享盲点，不能满足独立复核。
- 取消正式知识系统：会损失跨问题复用、长期一致性和正式知识治理，不符合平台目标。

## Consequences

直接调查路径的核心对象减少为检查清单、Evidence Packet、Answer Draft 和 Review Finding，答案可以综合多条源码证据自然表达。知识沉淀从该模式的时延和可用性边界中移出，但需要独立调度、去重和准入。Capability Evaluation 与 Product Validation 必须覆盖检索完整性、固定证据重写、缺证据补检索、独立审核和用户可读答案；模型调用次数或成本不能成为跳过审核或发布未通过答案的理由。

本决定不再规定所有同步软件问题的统一主路径；该部分由 ADR-014 收窄。
