---
id: ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST
kind: roadmap-candidate
status: candidate
authority: planning-only
owners: [product, project, architecture, application, quality]
depends_on: [SYS-PRODUCT-SUCCESS, SYS-ADR-015, SYS-ADR-016, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, ITER-009-RESULT-SLICE-001-STOP-REDIRECT]
code: []
tests: []
coding_input: false
---

# Candidate：世界模型认知引导的自适应工程问答

## Trigger and evidence

ITER-009 已证明本机 Web、World Model 调查、独立 Review、Limitation 和 Citation 可以运行，但真实答案被方法、分支、调用顺序和内部诊断
主导，整体体验像代码走读。后续讨论又发现，初版 ITER-010 虽允许提问期回源，却把 World Model 缩写成“手册/地图”，并在 Answer 前
一次性生成 Evidence Package，仍不能让模型像高级工程师一样根据已读内容决定下一步调查。

这包含两个必须分开的判断：

- 软件世界模型的概念没有改变。它仍是软件在 exact Context、Scope、Schema、Snapshot 上持久、版本化、可验证、可更新的外部认知，
  包含实体、关系、行为、约束、状态、证据、覆盖和未知边界；手册、地图只是投影；
- 需要改变的是提问期职责：大模型主导自适应调查，平台控制实际读取，调查结束后才形成回答证据包。

## Outcome

普通用户通过同一个本机 Web 提出自然工程问题。系统先向独立 Investigation LLM 提供不可变原问题与 exact World Model Cognition
Context；模型根据每次调查结果决定下一步需要搜索、读取、解析还是结束。Source Broker 校验并编译提议，隔离 Retrieval Worker 只执行
授权 exact revision 上 allowlisted、read-only、audited 的操作。所有结果进入 append-only Evidence Ledger，调查结束后才密封 Question
Evidence Package。

Answer 在全新上下文中只读取密封 Package，先回答用户目标，再按需解释代码。独立 Reviewer 从原问题重新检查答案；它没有文件系统、
Shell、网络、credential 或直接 Source 工具，但可以指出具体、可验证的证据缺口。Application/Broker 获准补证后形成新 Ledger Revision、
新 Package、新 Answer 和新 Review。Package 是 Answer/Reviewer 唯一允许采信和引用的事实支持集合；seal 证明完整性、来源和版本，不使
内容自动成为真。

## General protocol

1. 固定原问题、用户目标、受众、期望抽象层级、物质结论、exact repository/revision、World Model Cognition Context、allowlist、
   disclosure policy 和安全上限。
2. Investigation LLM 基于原问题、认知上下文和当前 Ledger 自适应提出下一项抽象读操作；它不能提交 shell、网络请求或扩大权限。
3. Source Broker 验证语义、路径、版本、操作、大小和 disclosure，编译为唯一合法的只读操作；Retrieval Worker 只执行已批准操作并把
   locator、digest、bytes、结果和截断状态追加到 Ledger。
4. 只有 Investigation `FINISH` 经 Application 校验，或达到安全上限失败关闭时，Ledger 才结束；随后密封本题 Package。不能预先用
   World Model 命中决定是否允许读 Source，也不能先封包再让调查模型受限猜测。
5. Answer 只读当前 Package；每个物质结论绑定包内证据，未知和限制说明已确认、未确认及缺少什么。
6. Reviewer 独立检查直接回答、抽象层级、正确性、完整性、相关性、可用性、Citation 和未知边界。表达问题可在同包针对性重写；具体
   证据缺口形成绑定 Checklist/Claim/evidence class/need 的 versioned Verification Request Proposal，不回初始 Investigation LLM；
   Application/Broker 重新校验编译后必须生成后继 Ledger/Package 并完整重答重审。
7. 高质量 Ledger/Package/结论可在回答完成后异步提议进入正常 Knowledge Update/Admission/Publication；同步回答不等待知识沉淀。

任何实现不得包含工程名、题目文本、关键词、符号、类名、方法名、fixture 或 Oracle 特判。用途、架构、运行、故障、影响、流程和实现
只是验证覆盖维度，不是产品路由。资源和调用上限只用于安全熔断；达到上限必须失败关闭或给出经审核的准确 Limitation，不能删除调查、
证据、Citation 或审核要求。

## Staged validation

### Stage 1：最小真实纵切与方向体验

先实现一条真实闭环：World Model Cognition Context → 自适应 Investigation LLM → Source Broker → Retrieval Worker → append-only Ledger →
调查后密封 Package → Answer → independent Review；至少包含一条 Reviewer 具体补证后生成后继 Package、重答、重审的路径。然后在一个
真实工程和同一 product-owned loopback Web 上，用 4 条不同维度的自然问题及至少一条用户现场问题验证方向；至少 3 条 supported，
至少覆盖 2 个非实现维度。

首版只需要足以判断职责分工、答案层级和真实可用性的最小安全边界，不提前完成第二工程、大规模性能、异常穷举、完整 hidden、成熟
源码 Agent 对照和正式验收。用户决定 `CONTINUE / REDIRECT / REJECT`；没有 `CONTINUE` 不进入夯实。

### Stage 2：跨工程和工程化夯实

方向确认后验证第二工程、来源冲突、Ledger/Package 生命周期、复杂补证、资格、Provider disclosure、安全、性能、完整回归、early hidden
canary、成熟源码 Agent 对照和 World Model 复用价值。修复必须落在通用表示、Broker policy、调查或审核合同，不能落在问题/工程分支。

### Stage 3：正式验收

产品代码冻结后执行最终未见工程 10 answerable + 2 boundary、两条现场题和独立对照。重大错误为零、逐结论完整性不低于成熟源码 Agent、
Citation 支持重要结论；所有 Source 操作与 Ledger 对账，模型直接 Source/写/网络权限为零，用户最终决定是否接受。

## Stop conditions

- 世界模型被降级为文档缓存、手册或关键词索引，或被用作 query-time Source recall 硬门禁；
- 调查不是由先前结果驱动，仍是一次性固定检索或固定调用链；
- Investigation/Answer/Reviewer 获得直接文件系统、Shell、网络、credential、仓库写或未审计工具权限；
- 默认答案仍是代码走读，或只有题目、工程、关键词、符号、fixture/Oracle 特判才能改善；
- Ledger 可被回写、包在调查完成前密封、旧 Review 批准新 Package，或 seal 被误当作内容真实性；
- Reviewer 无法独立指出并触发具体补证，或调用上限被用于跳过调查、Citation 或审核；
- supported 结论有重大错误，或用户决定 `REDIRECT / REJECT`。

本 Candidate 和本轮重制计划只属于规划输入，不授权产品代码、Provider/model 调用、Web 运行、隐藏披露或 Production Activation。
