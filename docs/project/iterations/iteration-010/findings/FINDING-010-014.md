---
id: FINDING-010-014
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [quality, engineering]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, ITER-006-RESULT-ACCEPTANCE]
code: [src/software_world_model/application_services/java_static_call.py]
tests: []
iteration: ITER-010
classification: verification
scope: general
disposition: preserve-the-real-project-profile-boundary-and-require-declaration-calls-evidence-for-v-xd-001
target: ITER-010-VERIFICATION
---

# FINDING-010-014：mall 的受限 Java Profile 不能替代 declaration/CALLS 跨域 Gate

## Observation

Slice1 首次为可见验证工程 `mall` 的 exact HEAD `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` 构建持久 World Model 时，
`JAVA_STATIC_CALL_GRAPH@1` 没有形成可查询 Snapshot。把 `pom.xml` 误作 Java source root 的 run-001 以
`JAVA_SOURCE_SET_EMPTY` 失败关闭；修正为 `mall-admin/src/main/java` 的 run-002 又在第一个 Spring Boot 注解类
`MallAdminApplication.java` 以 `JAVA_TOP_LEVEL_CLASS_REQUIRED` 失败关闭。

同一 revision 的 `MAVEN_REACTOR_STRUCTURE@1` run-003 正常发布 Snapshot
`structure_snapshot_5033a7fc944141d08ecd5ad3879ce1ba` 与 Read Set
`read_set_1066594bf8d1709ad7ce4c0d926083ed`，但它只证明模块与 Maven 依赖认知，不能被重标为 Java declaration/`CALLS`。

## Evidence and classification

- 两个失败 Attempt 都发生在 Source 读取和 Profile evaluator 内，没有 Provider、问题或浏览器调用；
- `JAVA_STATIC_CALL_GRAPH@1` 的已接受范围本来就是冻结语法子集，不覆盖注解、继承、接口等完整现代 Java；真实工程拒绝与既有
  Contract 一致，不是应在 Slice1 放宽 parser 的局部 bug；
- Maven run-003 在 exact revision 上以 10 次只读 Source operation、158481 bytes 发布 8 个 module entity 与内部 dependency
  relation，Owner verifier/admission、Bundle、Catalog 均成功；
- 当时的项目判断是 Maven cognition 足以继续 `V-WEB-000` 的最早链路体验，但不满足 `V-XD-001` 明确要求的 accepted
  declaration/`CALLS` 输入。run-035—042 与后续用户体验已经反证“足以用于工程行为问答”这一判断；历史执行事实保留，当前产品判断由
  `FINDING-010-132` 取代。

## Decision and disposition

本 Slice 保留 Profile 真实边界，不给 `mall` 增加项目特判，也不把 Maven relation 冒充 Java `CALLS`。历史 `V-WEB-000` 的链路
Result 不改写；当前恢复后，Maven-only 不再有资格进入行为问题的 World Model 完整认知臂。`V-XD-001` 和
`V-COGNITION-ELIGIBILITY-001` 在获得同工程可接受的实现/行为认知前保持 blocking，不能由 Web 可启动或 Source 最终命中顺带写成 PASS。

该发现处置到 `ITER-010-VERIFICATION`。既有 System Contract 已准确说明 Java Profile 的语法与 Coverage 边界，因此无需改写 System
truth；若后续 Slice 要让该真实工程满足 `V-XD-001`，必须另行扩展并验证通用 Java Profile，而不是在当前题目或项目上旁路失败关闭。

## Verification

运行证据保存在 ignored runtime 的 `var/iteration-010/slice-001/run-001-preview`、`run-002-preview` 与 `run-003-preview`。正式 Result
只能引用其 exact Attempt/Snapshot/Read Set 摘要，不能把 runtime 目录当规范或提交到产品基线。
