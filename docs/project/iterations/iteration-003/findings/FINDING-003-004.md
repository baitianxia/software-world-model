---
id: FINDING-003-004
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-003-SLICE-001, SYS-CONTRACT-KNOWLEDGE-EVIDENCE, SYS-CONTRACT-KNOWLEDGE-STRUCTURE-MODEL]
code: [src/software_world_model/application_services/maven_structure.py]
tests: [tests/test_maven_structure.py]
iteration: ITER-003
classification: local-implementation
disposition: bind-resolution-provenance-and-profile-closure
target: src/software_world_model/application_services/maven_structure.py
---

# FINDING-003-004：Maven 证据链与跨 POM profile 判定可能产生伪 COMPLETE

## Observation

对 evaluator 初版做反例审计时发现，dependency Entity/Relation 的 Evidence 没有完整绑定实际 parent、property、dependencyManagement 与 endpoint POM 来源链；profile 相关性只看当前 POM，父 POM profile 定义被子模块结构字段引用时仍可能输出 COMPLETE。

## Evidence

- billing 到 shared 的解析依赖 services parent、libraries parent、dependencyManagement/property 与 endpoint POM，但初版输出只保留部分 consumer Evidence。
- 在父 POM profile 中覆盖子模块所引用的结构属性，可复现 `RELEVANT_PROFILE_UNSUPPORTED` 未触发；无关 sibling profile 则不应导致误拒。

## Impact and classification

Slice 已冻结 Evidence 完整性与 fail-closed profile 规则，System 语义无需改变；问题局限于 Maven evaluator 的 provenance collection 和 property-resolution ancestry，因此属于 local implementation。

## Decision and disposition

Entity、Relation、exclusion 分别保存其真实 consumer、parent、management/property 与 target endpoint chain；profile 相关性沿真实 property ancestry 和递归引用 closure 计算。正向 fixture 精确断言 provenance，反例同时覆盖父 profile 拒绝与无关 sibling 接受。
