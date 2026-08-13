---
id: FINDING-006-013
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [product, project, quality]
depends_on: [ITER-006-SLICE-001, ITER-006-RESULT-LIVE-RUN-008, SYS-PRODUCT-SUCCESS]
code: [src/software_world_model/interface/world_model_product.py, scripts/docs.py]
tests: [tests/test_docs_gate.py]
iteration: ITER-006
classification: system-contract
disposition: require-product-goal-alignment-and-cumulative-general-source-qa-gate
target: SYS-PRODUCT-SUCCESS
---

# FINDING-006-013：局部 Profile PASS 不能证明正在接近通用源码问答 MVP

## Observation

ITER-006 run-008 已证明 `JAVA_STATIC_CALL_GRAPH@1` 的六类封闭问题可以通过正式 Web、Source-off Snapshot 和真实模型链正确
回答；在本次人工验收反馈中，用户继续询问系统用途、总体介绍、架构和业务问题时只能得到 Gap。该结果与本轮授权范围一致，却暴露
出当前迭代选择方法可以让一个孤立 Profile 的局部 Gate 全部通过，而产品仍只能回答少量预定类别的问题。

## Evidence / reproduction

- `ITER-006-PROPOSAL` 明确只形成 Java 类型、方法声明和唯一静态调用，并把业务意图、运行时行为等排除在外；
- `ITER-006-VERIFICATION` 的 live suite 只有方法清单、直接调用、静态路径、图差异和 Coverage Gap，run-008 的 6/6 PASS
  不能外推为自由问题覆盖；
- `ProductQuestionInterpreter._analyze_java()` 与 `ProductNeedKind` 只把自然语言路由到封闭的 inventory、direct call、path、diff
  和 Gap 操作；它不能动态组合 Maven 结构、Java 调用与更丰富的源码行为知识；
- 最终用户验收前的独立交互会话进一步证明评测 UI 不能外推为通用 Chat：Ark TLS 失败只显示通用 fail-closed terminal；
  “列出当前 Read Set 中的 Java 类型和声明方法”因未点名具体 `JAVA_TYPE` 而被路由成空 Query Plan/Knowledge Gap；页面的
  `FlowService` 示例没有随随机 Read Set 的真实类型变化；
- 当前 `SYS-PRODUCT-SUCCESS` 在本 Finding 前只规定正确性、权威和不退步，没有把“基于预构建世界模型的通用源码问答”
  及能力累积写成迭代选择的强制产品门槛。

## Impact

如果继续按“每轮增加一个 Profile/View，再只验证该 Profile 的封闭问题集”选择迭代，后续可以产生更多局部 PASS，却仍需要
用户知道系统当前支持哪几个题型。这会让切片目标替代产品目标，并重复出现投入大量开发后才发现 Web 体验没有接近通用问答
的情况。

## Classification rationale

这是长期产品成功标准和迭代选择 Gate 缺失，不是 Java parser 或 Answer wrapper 的局部缺陷，分类为 `system-contract`。主要
规范归属为 `SYS-PRODUCT-SUCCESS`；`PROJECT-GOVERNANCE-ITERATION-LIFECYCLE`、Roadmap 选择规则和治理模板同步落实该门槛。

## Decision and disposition

`SYS-PRODUCT-SUCCESS` 增加当前 MVP 定义：对未参与开发的真实工程，基于提问前构建的 fixed Snapshot 支持自由表述的源码
工程问题，动态组合既有知识，答案有证据或诚实 Gap，提问时无 Source/Update/Direct fallback，并逐题不低于成熟源码 Agent。

迭代生命周期从下一轮选择开始强制填写目标差距、累积路径、独立持有且实现阶段不可见的 held-out 自由问题增量、跨域组合
问题、最早正式 Web 体验点、现场临时问题和停止条件。孤立 Profile/View/组件不能单独成为产品 Iteration Outcome；
Verification 模板新增阻断 `V-000`，要求报告相对 baseline 的通用问答增量。

ITER-006 的 run-008 结果保持不变，仍可作为 Java 静态调用子集的窄范围技术证据；它不能被解释为产品 MVP、正式最终 Web
Chat 或通用源码问答已经完成。用户最终 Acceptance 明确保留这些限制，不把交互失败追溯写入冻结 run-008，也不授权在本轮
继续修复。Production Activation 仍未执行。

## Verification after disposition

- 产品成功标准、迭代生命周期、Roadmap 选择规则及 Proposal/Manifest/Readiness/Slice/Verification/Acceptance 模板已同步；
- `scripts/docs.py` 从 `ITER-007` 起在 Proposal 被接受时即检查累计组合、隐藏 held-out、现场问题、跨域案例与 `V-000`；
  Manifest 以结构化 binding 关联既有能力、本轮 Slice、跨域问题、正式 Web 和现场问题；完成态要求 `V-000` 以及每个绑定
  Case 都以本轮 Product Result 的 case-specific Evidence 保持 `PASS / blocking`，不能靠正文 ID 或汇总计数伪造闭环，也不能
  等到开发激活后才发现偏离；
- 门禁专项测试 26/26、完整测试 848/848 与 261 份 current 文档检查均 PASS；本次没有修改或重跑 run-008 的任何密封输入、
  输出或裁决。
