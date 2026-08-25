---
id: FINDING-010-093
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [product, architecture, application, ai, quality, project]
depends_on: [SYS-ADR-016, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py]
tests: []
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: agent-first-conversational-recovery
target: SYS-ADR-018
---

# FINDING-010-093：当前重流程、薄 Agent 不能充分发挥世界模型和大模型能力

## Observation and evidence

用户以 `codex-user-message:sha256:2f8b92d817ae111401eaaad959a5f786dd3a289763d9b258b38f5a12efd66a90`
指出：系统的两个核心应当分别是准确的软件世界模型，以及能够充分利用世界模型和大模型能力解决用户问题的优秀工程 Agent；当前体验却
主要表现为多层固定知识生产、结构化输出和审核流水线，Agent 本身过于单薄。

当前实现并非没有模型循环，但它把每次调查压缩为一个受控 `search/read/parse/FINISH` Proposal，并由大量固定角色、Schema 和
Application 状态转换共同决定答案如何形成。该边界保证了来源只读、证据身份和独立审核，却没有正式表达一个持续维护用户目标、假设、
调查计划、观察、重规划和完成判断的主工程 Agent。ITER-010 的长期 live 返工又证明：继续给固定角色链增加 Prompt、Schema 和 Review
规则，会消耗大量模型调用，却不必然产生用户可见的工程问题解决能力。

这不是某道题、某个模型或措辞问题，而是系统性架构职责缺口。安全 Broker、逐轮证据、Citation 和独立 Review 仍然必要；需要改变的是
由谁作为“解决问题的大脑”组织这些能力。

## Decision and disposition

- 产品冻结为双核心：软件世界模型提供精确、版本化、可验证、可更新且可跨任务复用的系统认知；主工程 Agent 负责持续理解用户目标、
  维护假设与计划、查询世界模型、按需提出受控源码调查、根据观察重规划并组织答案。
- 平台继续拥有权限、精确版本、Broker/Worker 执行、证据身份、资源熔断和审计。Agent 可以自主决定下一步认知与调查意图，但不能直接
  获得 Repository、filesystem、shell、network、credential、正式知识写入或答案放行权。
- 每个可交付答案继续绑定实际证据并经过独立 Reviewer；Reviewer 检查正确性、完整性、引用、未知边界和对话目标履约，不与主 Agent
  共享生成上下文，也不通过堆叠答案模板代替根因诊断。
- `SYS-ADR-018` 与 `SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 拥有新的默认 Agent/Chat 主线；ADR-016 和旧 Engineering
  Question Answering Contract 保留为历史及兼容实现边界，不能继续冒充目标 Agent 架构。
- ITER-010 以 PDR-004 在同一 Slice 内 `REWORK`，不废弃已有 World Model、Broker/Worker、Ledger/Package、Citation、Review、Web 和
  Provider 路由资产；旧产品编码权威暂停，待新 Readiness 和用户重新授权。

## Verification consequence

方向验证不能再只比较几个彼此独立的最终答案。新的同题三臂必须分开：current Codex 强外部 Agent 基线、使用同一主 Agent 但只允许
受控源码调查的 source-only arm、以及同一主 Agent 使用完整 World Model Cognition 加受控源码调查的 full-cognition arm。三者答案在独立
评测前密封和盲化；完整认知臂既要通过绝对质量门，也要证明世界模型认知不是装饰性 locator。
