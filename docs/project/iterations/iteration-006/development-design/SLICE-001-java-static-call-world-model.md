---
id: ITER-006-SLICE-001
kind: development-slice
status: completed
authority: historical-development
owners: [engineering]
depends_on: [ITER-006-PROPOSAL, ITER-006-READINESS, SYS-CONTRACT-KNOWLEDGE-JAVA-STATIC-CALL-MODEL, SYS-CONTRACT-APPLICATION-BEHAVIOR-VIEW]
code: [src/software_world_model]
tests: [tests]
iteration: ITER-006
coding_input: false
---

# SLICE-001：Java 静态调用 Snapshot → Behavior View → 产品 Web 问答

## Status and dependencies

本 Slice 已由用户于 `2026-08-12T09:18:11+08:00` 授权。依赖新 Java Static Call Model 与 Behavior View Contract，以及
现有 Schema、Update、Publication、Use、World Model Answering、Security 和 Local Browser Contract。

当前 [Implementation Verification Result](../results/implementation-verification.md) 已闭合 deterministic code/contract/product
Gate；[Live run-003](../results/live-run-003.md) 已在明确授权后执行。两套 baseline 各 6/6，World Model 4/6；新增 Java
generic operation vocabulary 被继承的 ITER-003 exact qualification 正确拒绝，冻结 evaluator 又暴露失败-terminal crash。
V-008 FAIL、V-009 PARTIAL，本 Slice 未被接受。

根因修复已从 [Java Capability Candidate Freeze](../results/java-capability-candidate-freeze.md) 进入
[Capability run-002](../results/java-capability-run-002.md)：八个 synthetic case 8/8 PASS、恰好 8 个唯一 Ark request、无 retry，
Java proposal 1.1.0 已形成时效内 `PASS_VALID` qualification。该授权已消费且没有发送产品问题、源码或 Evidence payload。

[Product Candidate Freeze run-007](../results/product-candidate-freeze-run-007.md) 随后重新冻结六题 suite 并通过本地安全门；用户
exact 授权的 [Live run-007](../results/live-run-007.md) 已执行，但仍为 FAIL。两套 baseline 各 6/6；World Model 六次 Ark call
均完成，却因授权 wrapper 把 Java baseline seal 与外层 seal 使用同名 `document_digest` 而在 `ROLE_POSTCONDITION` 全部拒绝。
最小本地修复不能追溯改写 run-007；它已进入全新
[Product Candidate Freeze run-008](../results/product-candidate-freeze-run-008.md)，完成 56/56 focused、18/18 Answer package、
836/836 full regression、docs 与未授权安全门。用户随后 exact 授权的 [Live run-008](../results/live-run-008.md) 已完成：
Direct/Codex/World Model 各 6/6 SUCCESS，comparison PASS、blocker 0、无 retry/filter/interpolation。用户随后于
`2026-08-13T11:45:33+08:00` 接受 exact run-008 的窄范围结果；本 Slice 已完成并转为历史设计，最终裁决见
[Acceptance](../results/acceptance.md)。该裁决不接受当前评测页面为正式最终 Web Chat，也不扩张到系统用途、架构意图或
通用源码问答。Production Activation 未执行。

## Current vs expected behavior

当前 Workspace 只构建 `MAVEN_REACTOR_STRUCTURE@1`；Snapshot/View/Product 只认识 software system、module、contains 与
POM-local depends-on。Java 方法或调用问题正确地成为 Gap。

预期行为是在新 SYSTEM Scope 上选择 Java Profile，独立读取 exact revision 的完整 Java source root，发布声明和静态调用
正式知识，生成相同 Catalog transport 下的 no-payload Bundle。产品根据 Bundle Profile 选择通用 Entity candidate、邻域、
路径和 diff operation；Answer worker 不读取 Source 或 Evidence payload。

## System contracts and invariants

- 新 Schema `INITIAL` 采用；已有 CURRENT 上仍禁止切换 Schema。
- Maven Profile 的 allowed entity/predicate/modalities 是显式冻结集合，不能使用扩展后的 enum 全集。
- Java method Root 由 owning Scope、declaring type 和规范化 signature 决定；revision/path/locator 只属于 State/Support。
- 调用边方向为 caller → callee，modality 永远是 `JAVA_SOURCE_STATIC_CALL@1`。
- 只有完整扫描和唯一解析才能发布 `COMPLETE` Coverage；未知或歧义不是“无边”。
- View 只读 Bundle，Result 携带 Profile、modality、Coverage、Support Map、limitations 和 evidence allowlist。
- Web 请求不能创建 Update、读取 Git 或退回 Direct Investigation。

## Interfaces and affected code

- Knowledge graph primitives、Schema registry 与 persisted typed records；
- Java source collector/evaluator、独立 replay verifier 和更新编排；
- Workspace profile、SQLite migration、Bundle/Catalog transport；
- Behavior View operation 与 source-off CLI；
- World Model product catalog/interpreter/planner/draft/reviewer 与现有 WSGI/UI；
- profile-versioned proposal Strategy/Prompt/vocabulary、独立 capability suite/evaluator、qualification loader 与 exact Java
  Model Egress Gateway policy；
- focused contract/integration/isolation/product tests 和 iteration validation fixture。

优先复用现有 Owner 和 Port；不新增顶层 Orchestrator。历史类名中含 `Structure` 或 `Maven` 时保持兼容，但新公开字段必须显式
携带 Profile，不能靠 root path 猜模式。

## Compatibility, data and security boundaries

旧数据库通过单向兼容 migration 为 Workspace 增加 Profile 默认值，旧行等价于 `MAVEN_REACTOR_STRUCTURE@1`；旧 bundle 和
Catalog schema 保持可读。Java Workspace 与 Maven Workspace 不混成同一 Read Set。Source payload 只存在于 Source/Update
和正式 Evidence owner；Bundle、Catalog、View、模型输入仍无 payload。无新 Secret 或网络能力。

## Open questions and implementation risks

- 若无需第三方依赖的 parser 不能对冻结 fixture 提供可证明完整性，应缩小 Profile 或让 build 失败，而不是加入 heuristic。
- 若通用 graph persistence 把 Schema shape 绑定到 Python enum 全集，必须先消除该隐式耦合并增加 Maven regression。
- run-003 已证实 Java vocabulary 必须独立资格化；该八题资格现为 `PASS_VALID`。run-007 又证实 Java baseline document seal 在
  wrapper 重封装时必须去除同名字段，不能形成不可重建的隐藏 hash input。该修复已在 run-008 完成全新零 Provider freeze 与
  exact 三路 live PASS；用户随后接受该窄范围结果，本 Slice 已完成。Production Activation 仍是独立且未授权的边界。

## Acceptance scenarios

1. R1 发布类型/方法/声明/调用；Source-off inventory、direct calls 和 path 与独立 Oracle 一致。
2. R2 删除/新增方法或调用；有序 diff 精确区分 Root membership 与 State change，R1 Read Set 不漂移。
3. R3 含 Profile 不支持或歧义调用；更新失败，R2 CURRENT 与两个已登记 Read Set 可继续查询。
4. 评论、字符串和方法体中的标识符文本不产生虚假声明/调用。
5. 运行时分派、反射或“为什么这样设计”的问题返回 Gap；不访问 Source。
6. Bundle/Catalog/Support/Citation 任一 digest 或 locator tamper 均失败关闭。
7. 正式产品 Web 展示 supported 与 Gap，问题前后 Update/CURRENT/Source Operation 不变。

## Findings

链接本轮的 [Findings](../findings/README.md) 与[实现发现回写规则](../../../governance/implementation-feedback-policy.md)。
