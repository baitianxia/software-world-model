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

ITER-010 随后真正实现了持久 World Model Cognition → 结果驱动 Investigation → Broker/Worker → append-only Ledger → 调查后 Package →
Answer/Review，并从同一 loopback Web 完成公开题和现场题。调查、隔离、Citation 与失败关闭技术资产成立，但现场登录答案仍由
Controller/Service/Filter 方法顺序主导，独立 Reviewer 无 Finding 批准。旧记录把用户要求自行复核和修复的消息推断为 `REDIRECT`；
`ITER-010-PDR-001` 已纠正为同轮 `REWORK`。`FINDING-010-028` 证明最早共同偏差不是回源或页面，而是自由文本抽象层级、扁平 Claim
Answer 和没有可执行方向质量 invariant 的 Review 合同。

这包含两个必须分开的判断：

- 软件世界模型的概念没有改变。它仍是软件在 exact Context、Scope、Schema、Snapshot 上持久、版本化、可验证、可更新的外部认知，
  包含实体、关系、行为、约束、状态、证据、覆盖和未知边界；手册、地图只是投影；
- 需要改变的是提问期职责：大模型主导自适应调查，平台控制实际读取，调查结束后才形成回答证据包。

第三个判断是：调查协议正确不等于答案协议正确。返工不能继续把“答案优先”只写在 Prompt 中；同一 Slice 必须以最小通用机制让
Understanding、Answer、Application acceptance、Reviewer 和页面对答案层级形成一致判断。typed Answer Hierarchy 是可选实现，不是
体验前必须完整建设的新架构；行为上至少要区分：

- 直接回答用户目标；
- 用户可见流程、影响、条件或建议；
- 诚实未知与限制；
- 只在用户明确询问或为理解不可缺少时展开的实现证据。

每一层需要稳定角色、顺序与展开条件；Citation 仍绑定物质结论。Reviewer 必须能针对“没有先回答”“默认正文被实现步骤主导”或“关键
流程副作用遗漏”生成绑定 Answer 层/Claim 的 rewrite/reject Finding。不得用类名隐藏、字符占比、题目关键词或登录流程特判冒充结构。

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

### Stage 1：持续 Web Alpha

复用 ITER-010 已跑通的 World Model Cognition → 自适应 Investigation → Broker/Worker → Ledger → Package 技术资产，首先把同一产品变成
一条固定命令可启动、固定本机地址、同一会话连续自由提问的 Alpha。普通体验者不需要拼装逐题 freeze、grant 或内部 run 参数；页面显示
产品/工程精确版本和已知限制，坏题只关闭当前请求。自由问题必须真实经过世界模型与源码调查链，不能回放预制答案。

在这个出口内同时做答案和 Reviewer 的最小通用修复，以原失败题和至少两个相邻或异质问题回归，至少一题不是实现走读题，并加入受控失败
证明服务继续可用。独立评测先裁决重大错误、遗漏、引用和特判；用户随后在同一持续版本自由体验并决定 `CONTINUE / REWORK / REDIRECT /
REJECT`。非 `CONTINUE` 只暂停晋级并默认在同一 Slice 返工，不自动新建 Iteration。

### Stage 2：跨工程和工程化夯实

Alpha 确认后才验证第二工程、来源冲突、Ledger/Package 生命周期、复杂补证、资格、Provider disclosure、安全、性能、完整回归、early
hidden canary、成熟源码 Agent 对照和 World Model 复用价值。修复必须落在通用表示、Broker policy、调查或审核合同，不能落在
问题/工程分支。

### Stage 3：正式验收

产品代码冻结后执行最终未见工程 10 answerable + 2 boundary、两条现场题和独立对照。重大错误为零、逐结论完整性不低于成熟源码 Agent、
Citation 支持重要结论；所有 Source 操作与 Ledger 对账，模型直接 Source/写/网络权限为零，用户最终决定是否接受。

## Stop conditions

- 世界模型被降级为文档缓存、手册或关键词索引，或被用作 query-time Source recall 硬门禁；
- 调查不是由先前结果驱动，仍是一次性固定检索或固定调用链；
- Investigation/Answer/Reviewer 获得直接文件系统、Shell、网络、credential、仓库写或未审计工具权限；
- 默认答案仍是代码走读，或只有题目、工程、关键词、符号、fixture/Oracle 特判才能改善；
- Answer 仍只有无法区分直接答案、用户可见解释、限制和可选实现证据的扁平 Claim，或 Reviewer/Application 无法拒绝实现细节主导；
- Ledger 可被回写、包在调查完成前密封、旧 Review 批准新 Package，或 seal 被误当作内容真实性；
- Reviewer 无法独立指出并触发具体补证，或调用上限被用于跳过调查、Citation 或审核；
- supported 结论有重大错误时当前问题失败并进入 `REWORK`；只有用户明确改变方向、核心架构被异质问题证伪或达到预提交无进展上限，
  才进入转向评审；用户明确决定 `REJECT` 时停止。

本 Candidate 和本轮重制计划只属于规划输入，不授权产品代码、Provider/model 调用、Web 运行、隐藏披露或 Production Activation。
