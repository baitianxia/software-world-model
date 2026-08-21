---
id: FINDING-010-010
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, knowledge, quality]
depends_on: [ITER-010-SLICE-001, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING]
code: [src/software_world_model/application_services/engineering_question_cognition.py]
tests: [tests/test_engineering_question_cognition.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: project-an-exact-persistent-structure-read-bundle-into-the-bounded-engineering-qa-cognition-context
target: src/software_world_model/application_services/engineering_question_cognition.py
---

# FINDING-010-010：协议已有 Cognition port，但产品尚无持久化 World Model 投影器

## Observation

首轮纵切定义了 `WorldModelCognitionProjector` Protocol，测试 fixture 也能构造 Cognition Context；但产品代码没有 Adapter 可以把既有
`StructureViewService` 与已验证 `StructureSnapshotReadBundle` 装载到 Engineering QA。若直接进入 Web 组合，只能继续使用测试投影或把
世界模型降格为手写摘要，无法满足 A1/V-COGNITION-001。

## Evidence and root cause

- 既有世界模型已经拥有 exact Scope/Context/Schema/Snapshot、source revision、typed entity/relation/behavior/state/evidence 和 Coverage；
- Engineering QA Service 只依赖抽象 projector，没有读取 Source 或数据库的权限，职责边界正确；
- 缺口位于两个已存在的 Application/View 合同之间：没有生产 Adapter 验证 Bundle identity、Read Authority 与 Request
  Binding/revision 后形成 bounded Cognition Context；
- 根因不是世界模型缺少认知，也不是需要问题期重新建模，而是新用例的只读投影组合尚未实现。

规范已经明确该投影语义，因此分类为 `local-implementation / systemic`。

## Decision and disposition

- 新增 `StructureBundleWorldModelCognitionProjector`，只接受 exact `StructureViewService`、已验证的 no-payload Read Bundle 与其
  Snapshot identity；
- Read Authority 摘要绑定 session、read set、有序 bundle、Snapshot/Bundle digest、Binding 与唯一 source revision；Request 的
  Binding、revision 和 authority digest 任一漂移均在读取前失败关闭；
- 以与问题无关的确定性顺序投影 Coverage、Entity、Relation/Behavior、Literal/State 与 Evidence metadata，不读取 Source/raw payload，
  不按问题关键词裁剪；
- 在 Request `maximum_world_model_bytes` 内用确定性前缀和显式 retained/total Unknown 表达截断，不静默丢失 Coverage；
- 对 schema/profile 没有表达的 constraint、relation、behavior 或 literal 保留显式 Unknown，不能从缺项推导仓库不存在。

## Verification

测试使用真实 Structure fixture 验证 exact bundle 形成带版本 schema 的 aligned Cognition、错误 Binding 失败关闭、8192-byte 上限下确定性
截断与显式 retained/total，以及最终 Package 同时包含 `WORLD_MODEL_COGNITION` 和 `EXACT_REVISION_SOURCE` 支持条目。
