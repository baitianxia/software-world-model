---
id: FINDING-010-132
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [knowledge, application, architecture, product, quality]
depends_on: [FINDING-010-014, FINDING-010-130, SYS-CONTRACT-KNOWLEDGE-STRUCTURE-MODEL, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE]
code: []
tests: []
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: separate-narrow-profile-completeness-from-engineering-cognition-eligibility
target: SYS-ADR-018
---

# FINDING-010-132：Maven 模块与依赖不能取得工程行为认知资格

## Observation

`mall@0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` 的 `JAVA_STATIC_CALL_GRAPH@1` 在 run-001/002 未形成可查询
Snapshot；`FINDING-010-014` 已保留其 `JAVA_SOURCE_SET_EMPTY / JAVA_TOP_LEVEL_CLASS_REQUIRED` 失败。随后成功发布并被
run-035—042 实际装载的认知只有 `MAVEN_REACTOR_STRUCTURE@1` Snapshot
`structure_snapshot_5033a7fc944141d08ecd5ad3879ce1ba` / Read Set
`read_set_1066594bf8d1709ad7ce4c0d926083ed`。

该 Snapshot 的 exact Coverage 只列 `SOFTWARE_SYSTEM / MAVEN_MODULE` 与 `CONTAINS_MODULE / DEPENDS_ON`；Bundle 包含 8 个
Entity 和 15 个 Relation Fact，行为、声明、调用、状态、异常、配置和 literal facet 均不存在。run-042 的 Session config 仍把这一
Snapshot 作为唯一 `cognition_snapshot_id`，却用它回答登录流程、认证失败日志和 401/403 责任问题。

## Impact and classification

Maven 结构产物本身没有错误：它能回答模块组成和 POM 本地内部依赖。但 Profile `COMPLETE` 只证明其窄 Coverage 完整，不能推出当前问题
所需的软件认知完整。此前把该 Snapshot 称为 `full cognition`，并让它进入行为问题的完整认知对照臂，是认知资格定义和执行绑定的系统性
错误；不是增加 Maven 解析字段或为 mall 添加特判可以解决的问题。

## Decision and disposition

- 世界模型概念不变，仍是实体、关系、行为、约束、状态、来源、Coverage、Conflict 与 Unknown 的版本化系统认知；
- 工程 Conversation 必须以 Capability Manifest 固定同一 exact revision 上一个或多个 profile-specific Read Authority，并在问题前独立
  判断各 material Need 的认知资格；
- Maven-only 只可标为 `maven-structure-only` 或窄结构/locator control，不得标为 full/engineering cognition；
- 对行为、流程、职责、配置、状态或故障问题，可体验纵切至少需要结构与实现/行为认知，并保留缺失维度的 explicit Gap；
- Source 命中可以支持当前 Turn，但不能回填为世界模型覆盖或贡献。

该发现处置到 ADR-018 的 Cognition Binding/Eligibility 澄清，并同步 Structure Model、Knowledge Update/Use、Product Success、Acceptance
与 Engineering Conversation 的现行语义；不创建混合 Profile Snapshot/Read Set，也不放宽 Schema Adoption。

## Verification after disposition

ITER-010 新增 `V-COGNITION-ELIGIBILITY-001`。通过条件不是“成功发布任一 Snapshot”，而是三个预提交异质问题分别得到 Need→认知维度/
query capability 或 explicit Gap 的机械结果；行为问题不得由 Maven-only 取得 eligible verdict，问题相关投影不得对不同问题机械返回同一
整包记录。
