---
id: FINDING-010-002
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [product, architecture, application, quality]
depends_on: [FINDING-010-001, ITER-009-RESULT-SLICE-001-STOP-REDIRECT]
code: []
tests: []
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: preserve-world-model-concept-and-move-question-time-source-investigation-under-model-led-broker-controlled-ledger-sealed-flow
target: SYS-ADR-016
---

# FINDING-010-002：世界模型概念不变，修正提问期调查职责

## Observation

初版 ITER-010 计划把 World Model 描述为“工程地图、手册和检索入口”，并把提问期源码读取预先收敛为一次检索计划和密封
Evidence Package。该描述便于解释，却把软件世界模型缩窄成了文档投影；一次性先封包也会让回答模型失去高级工程师根据前一步结果
继续调查的能力。用户明确指出：软件世界模型应提供大模型对系统的认知，而不是只提供文字手册；读取源码回答问题更适合由大模型
主导。

## Evidence and root cause

- 项目既有世界模型从始至终表达软件在 exact Context、Scope、Schema、Snapshot 上的实体、关系、行为、约束、状态、证据、覆盖和未知
  边界，手册或地图只是这种认知的一个投影；
- `FINDING-010-001` 正确识别了严格 Source-off 路径不能独自承担默认工程问答，但其初版处置仍把检索看成 Answer 前的一次固定准备；
- 一次性检索无法可靠处理“读到入口后再沿调用关系追踪”“发现配置覆盖后再核对测试”这类结果驱动调查；
- 让模型直接拥有文件系统、Shell、网络或仓库权限又会破坏 exact revision、只读、allowlist、审计和失败关闭。

根因是提问期编排职责划分不准确，分类为 `architecture / systemic`，不是修改 World Model 的产品概念，也不是给个别题目增加检索规则。

## Decision and disposition

用户以 `codex-user-message:sha256:d3b60bdaa52d96ced3c653a8dcd54fabff41beb7f23f0bf691e6983ebb9437bc` 于
`2026-08-21T08:23:25Z` 要求按讨论结果重新制定计划并更新文档。正式计划采用以下边界：

- World Model 保持为软件在 exact Context/Scope/Schema/Snapshot 上持久、版本化、可验证、可更新的外部认知模型；手册、地图和检索入口
  只是面向人或任务的投影；
- 独立 Investigation LLM 读取不可变原问题、exact World Model Cognition Context 和当前 append-only Evidence Ledger，根据每一步结果
  自适应提出下一步 search/read/parse/finish；
- Source Broker 校验并编译模型提议，隔离 Retrieval Worker 只执行 exact-revision、allowlist、read-only、audited 操作；模型没有直接
  文件系统、Shell、网络、credential 或写权限；
- 调查完成或安全上限触发后，Application 才密封 Question Evidence Package；`support/citation` 仅含 admissible entries，`boundary/audit`
  强制保留 Gap/Failure/Partial/Conflict/Unknown 等非支持记录且不能支持肯定 Claim；seal 证明完整性、来源和版本，不把内容自动变成真；
- Answer 在全新上下文中只读密封 Package 生成答案；独立 Reviewer 同样无直接 Source 权限，但可返回绑定 Checklist/Claim/evidence
  class/need 的 versioned Verification Request Proposal；它不规划操作。新的 Verification Investigation 在全新上下文读取 gap + current
  Package/Ledger，根据每步 Result 自适应提议并经 Application/Broker/Worker 校验执行；它不回初始 Investigation LLM，随后追加新 Ledger
  Revision，密封新 Package，再完整 Answer 和 Review；
- 不允许按工程、题目、关键词、符号、类名、方法名、fixture 或 Oracle 特判；资源上限只是安全熔断，不能裁剪问题清单、证据要求、
  Citation 或独立审核质量。

该决定已处置到 `SYS-ADR-016`（其 `derived_from` 显式引用本 Finding）和 Engineering Question Answering Contract，不推翻世界模型概念，
也不改变严格 `WORLD_MODEL` Source-off 评测模式。本 Finding 不依赖处置目标或 Proposal，避免 Finding → ADR/Proposal → Finding 环；
`FINDING-010-001` 的“默认工程问答需要受控回源”结论继续有效，本 Finding 取代其一次性检索/手册式解释。

## Authorization consequence

本收据只授权重新制定计划与更新文档，不授权产品代码。此前 `1b327024… + 5cdb7000…` 绑定的是修正前的 Slice1 设计，不能自动扩展到
模型主导的自适应调查和 Reviewer 独立补证。因此 ITER-010 保持选中规划状态，但所有 Slice 均为 `proposed / coding_input=false`，
`PROJECT-CURRENT` 不设置活动开发 Slice。后续明确开发请求可在不重复讨论方向的情况下完成 Readiness 授权。

## Verification after disposition

重制计划由 `V-ARCH-001`、`V-INVESTIGATE-001`、`V-BROKER-001`、`V-LEDGER-001` 和 `V-REVIEW-001` 验证：世界模型定义保持、调查模型
结果驱动、Broker/Worker 权限隔离、调查后密封、Reviewer 独立补证和新包重答重审均须机械成立。本 Finding 不预报产品实现、模型调用、
Web 体验或验收结果。
