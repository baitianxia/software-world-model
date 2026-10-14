---
id: FINDING-010-298
kind: implementation-finding
status: dispositioned
authority: implementation-evidence
owners: [project, architecture, product, engineering, quality]
depends_on: [SYS-ARCH-BASELINE, SYS-PRODUCT-SUCCESS, SYS-ADR-018, FINDING-010-282]
code: [src/software_world_model/knowledge_engine/capability_cognition.py, src/software_world_model/application_services/java_capability_cognition.py, src/software_world_model/application_services/lightweight_engineering_agent.py]
tests: [tests]
iteration: ITER-010
classification: system-contract
disposition: current-system-contract-and-architecture
target: SYS-ARCH-BASELINE
scope: systemic
---

# FINDING-010-298：架构评审——管控规定充分而认知优势机制缺位

## Observation

2026-10-13 对架构基线 V1.3、ADR-018/020、产品愿景与成功标准做了整体评审，并对照了当前代码和 ITER-010 Finding。结论是：知识
治理底座（分层准入、Scope/Context/Snapshot、不可变发布、生成与审核分离、模块化单体）合理；但相对当前产品价值门
（同一 Agent 下 World Model + Source 优于 Source-only，并在盲评中胜过 current Codex），架构存在以下系统性缺口。

## Evidence

1. **认知优势机制缺位。** 基线对权威、准入、发布有完整规定，但没有定义预先构建哪些认知、按什么抽象层组织、如何检索、
   如何随 revision 增量更新；语义/向量检索仅为“可选 Projection”。代码中 `knowledge_engine` 约 8.7k 行，占 `src` 约 174k 行的 5%；
   Agent 实际使用的 `CapabilityCognitionIndex` 只有 5 类实体、5 类关系，检索为分词与停用词表的字面匹配。
2. **世界模型双轨。** 基线要求 World Model Cognition 来自正式 Snapshot，但默认 Chat 使用的 `CapabilityCognitionSnapshot` 由
   `application_services/java_capability_cognition.py` 直接从源码构建，没有经过 Candidate、Knowledge Verifier 或 Snapshot Publication。
   说明完整的模型审核式准入对确定性解析结果过重，产品绕开了它。
3. **Agent 读取能力弱于对照基线。** Source 读取必须先成为本 Turn 签发的 read candidate，并受小额调用/文件熔断约束。FINDING-010-282
   及前后多条 Finding 的失败签名集中在 `BUDGET_EXHAUSTED`、`REPEATED_ACTION`、`SOURCE_FILE_FUSE_EXHAUSTED`，修复方式是排序
   sidecar、候选屏蔽和计划失效等局部补丁。对公开、exact revision、只读的来源，这些约束削弱了必须胜过 Codex 的 Agent。
4. **证据生命周期与目标冲突。** 基线 10.2 要求 Turn 终态后释放 Ledger/Package/Draft/Review 正文且不保存答案与证据绑定，
   这与可追溯性、盲评复现以及 4.8“按复用价值从真实任务结晶知识”相冲突；世界模型只能经冲突维护任务从使用中成长。
5. **复核无法发现包外遗漏。** Reviewer 不能访问任何来源，只能核对 Draft 与 Package 的一致性；而成功标准要求物质遗漏为零。
6. **回答路径过多。** 正式 Knowledge Use、严格 `WORLD_MODEL`、严格 `DIRECT_INVESTIGATION`、默认 Engineering Chat 四套回答范式并存，
   各有契约，增加了实现与验证面。
7. **成功标准与架构优势错位。** 价值门只比较单仓库答案质量且“逐题不低于”一个持续变化的外部基线；少量题目下统计脆弱，
   而架构的真实优势（跨会话复用、多来源联合、成本）不进入任何评价维度。

## Root cause

架构把可信性与权威作为主要设计对象，没有把“世界模型为什么能让答案更好”作为一等架构关注点；同时对低风险的只读公开来源沿用了
与高风险来源相同的强管控，使系统在价值门最关心的维度上缺少设计支撑。

## Decision / Disposition

接受架构变更 `SYS-ADR-021`，并在同一变更中增量修订架构基线至 V1.4、受影响附录、安全边界与产品成功标准：

- 新增“认知表示与检索”章节，定义分层认知、混合检索投影、差量构建和认知投资原则；
- 正式知识准入分为确定性通道与模型通道，Chat 使用的世界模型认知必须来自已发布 Snapshot；
- Source Broker/Worker 提供与主流编码 Agent 读取能力对等的只读工具目录，read candidate 不再是读取前置条件；
- Turn 证据改为非权威的 Turn Trace，按保留策略保存，用于审计、评测复现和知识结晶，仍不得作为后续 Turn 证据；
- Reviewer 可经同一 Broker 执行有界只读核验读取，但仍不作答、不补证进答案包、不放行；
- 默认 Engineering Chat 为唯一产品回答路径，其他 Profile 收敛为评测/兼容或程序化接口；
- 产品价值门分为归因门与强基线门，并把复用与成本列为独立报告维度（不补偿质量）。

详细 `engineering-conversation` 契约中与上述决定冲突的条款列入 ADR-021 的迁移清单，在实现迁移时逐项改写。

## Falsifiable acceptance evidence

1. 默认 Chat 中被计为“世界模型贡献”的每个观察都能追溯到已发布 Snapshot 成员；直接由源码构建、未发布的索引只计为来源观察。
2. 同一问题集上，Agent 只读工具目录覆盖：全树路径列举、正则/字面搜索、按路径与行段读取、exact revision 上的历史/blame、结构化解析查询；
   不再出现“合法路径因未签发 candidate 而不可读”的失败签名。
3. 任一已交付 Turn 都能在保留期内由 Turn Trace 重放其证据、Draft 与 Review，且后续 Turn 的 Package 中不出现前一 Turn 的 Observation。
4. 至少一次知识结晶从 Turn Trace 提议、经 Knowledge Update 重新读取来源并发布新 Snapshot 成员。
5. 价值门按 `SYS-PRODUCT-SUCCESS` 的分层定义执行并保留全部失败记录。

## Alternatives rejected

- 继续在现有约束内逐题修复检索排序与预算：已有多轮证据显示只能改善原题，不能形成通用能力。
- 放弃正式准入、直接把解析索引称为世界模型：会失去可追溯与不可变发布底座，并使价值归因不可信。
- 让 Reviewer 生成第二份答案：破坏生成与审核分离，也不能定位缺口责任层。
