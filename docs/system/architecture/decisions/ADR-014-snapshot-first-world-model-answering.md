---
id: SYS-ADR-014
kind: system-decision
status: accepted
authority: normative
owners: [architecture, application, knowledge, quality]
depends_on: [SYS-ADR-003, SYS-ADR-005, SYS-ADR-009, SYS-ADR-013, SYS-PRODUCT-VISION]
code: [src/software_world_model/application_services, src/software_world_model/knowledge_engine, src/software_world_model/interface]
tests: [tests]
---

# ADR-014：软件世界模型回答只读 exact Snapshot

## Context

直接读取源码的受控调查可以生成高质量答案，但若浏览器问题始终触发该路径，回答不会证明已发布知识被复用，也不会推动无人提问时的知识更新。把这种回答标为“软件世界模型回答”会让产品名称、数据流和验收对象不一致。

另一方面，把所有开放问题都强制经过知识形成、准入和发布，会把多个概率阶段重新串入同步关键路径。软件世界模型需要证明的是已声明 Coverage 内的正式状态能够被独立构建、更新和复用，而不是让每个问题临时重建整个模型。

## Decision

在本 ADR 拥有的 Snapshot-only 与 Direct 边界内，系统公开区分两个不可混淆的模式：

- `WORLD_MODEL`：入口把每个 `CURRENT` 至多解析一次，随后固定一个 exact Snapshot，或为比较任务固定同一 Scope 下的有序 exact Snapshot Read Set。回答只读取该 Read Set 中的正式知识、Coverage、View Limitation/Knowledge Gap 和 Support Map；模型如参与生成或审核，也只能读取这些固定结果。
- `DIRECT_INVESTIGATION`：按 ADR-013 调查 exact 授权来源并使用密封 Evidence Packet。它是独立的直接源码调查能力、诊断手段和产品对照，不是世界模型命中。

`WORLD_MODEL` 不得访问 Source Integration、创建新 Artifact/Evidence Packet、触发 Knowledge Update，或因 Read Set 不足而静默进入 `DIRECT_INVESTIGATION`。不足时返回明确 Knowledge Gap；更新由人工命令、计划任务或来源事件通过独立 Knowledge Update 发起，成功后由新的请求选择新 Snapshot。提问次数为零不能阻止已配置更新机制运行。

ADR-016 新增的 `ENGINEERING_QA` 是第三个独立请求身份。它在执行前就显式声明 World Model Cognition Context 与 exact-revision 自适应受控调查的组合边界；因此既不是本契约中 `WORLD_MODEL` 的回源，也不是 Knowledge Gap 后的静默 Direct fallback。该模式把世界模型作为 AI 的持久系统认知，而不是只当作手册或检索缓存；这不改变本契约的 Source-off 语义。

Interface 必须展示实际模式、Scope、source revision、Snapshot、View、Coverage、View Limitation/Knowledge Gap 和引用。任何直接调查切换都需要新的显式用户动作和独立结果身份，不能替换原世界模型回答记录。

引用正文不进入 Snapshot Read Bundle 或 answer worker。View/Query Result 密封后，受控应用边界中的 trusted Citation Observation Broker 才能按 Result 自身的 typed Evidence allowlist 从 Knowledge owner 重读 exact 自包含 observation，并物化一个与 Result、allowlist 和 manifest digest 绑定的 disposable Citation Store。独立 Citation Projector 只读取该 seal 和 Store，不直接挂载权威数据库或完整 Evidence Store；Store 不拥有 Evidence 或 Result，删除后只能从同一密封输入重新物化。Projector 输出只供浏览器或隔离评测展示 Sink 使用，不得回流 Requirement、Plan、Query、Draft、Review、模型或答案进程。

## Alternatives

- 所有同步问题统一 Evidence-first：回答质量可以成立，但无法证明软件世界模型的构建、复用和更新价值。
- 知识不足时透明回源：用户可能得到答案，却无法知道答案来自 Snapshot 还是临时源码调查，验收也会产生假阳性。
- 每个问题先同步更新再回答：重新引入长概率链和高失败放大，不符合独立更新与复用目标。

## Consequences

世界模型只能回答已发布 Coverage 支持的问题，对未知保持诚实；直接调查可以覆盖更开放的问题，但必须明确标记。Knowledge Update 必须成为与提问独立的产品能力。Product Validation 需要让回答进程只挂载无 Evidence payload 的 exact Snapshot Read Bundle，在默认拒绝网络中仅允许经 exact Model Egress Gateway 访问固定 Provider endpoint，关闭 Source/权威数据库/Evidence Store 后重启并证明仍可回答；Citation Projector 只能获得 Result-scoped disposable Store，不能以展示需要扩大为权威 Store 读取。两条路径同时与受控 Direct Investigation 及成熟源码 Agent 基线分别计量。

## Supersedes / migration

本决定收窄 ADR-013 中“所有同步软件问答统一走 Evidence-first”的部分；ADR-013 继续拥有显式直接源码调查模式。ADR-016 取代了“产品公开只有上述两种模式”和“普通工程聊天默认进入 `WORLD_MODEL`”的解释，但不取代本 ADR 对严格 `WORLD_MODEL` 的 Snapshot-only、Source-off、no-update 和 no-fallback 边界。
