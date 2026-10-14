---
id: SYS-ADR-021
kind: system-decision
status: accepted
authority: normative
semantic_owner: SYS-ARCH-BASELINE
authority_scope: decision-rationale-only
owners: [architecture, product, application, knowledge, source, quality, security]
depends_on: [SYS-ADR-005, SYS-ADR-009, SYS-ADR-010, SYS-ADR-018, SYS-ADR-020]
derived_from: [FINDING-010-298]
code: [src/software_world_model/knowledge_engine, src/software_world_model/application_services, src/software_world_model/source_integration]
tests: [tests]
---

# ADR-021：以认知优势和 Agent 能力为一等架构关注点

## Context

架构基线 V1.3 对正式知识的权威、准入、发布和答案审核规定完整，但产品价值门要求的是：同一 Agent 下 World Model + Source
优于 Source-only，并在独立盲评中胜过 current Codex。评审（FINDING-010-298）发现，基线没有说明世界模型凭什么让答案更好；
默认 Chat 实际使用的认知绕过了正式准入；Agent 的只读能力弱于对照基线；Turn 证据终态即释放，阻断了评测复现和知识结晶；
Reviewer 只能检查包内一致性；回答路径过多；价值门只衡量架构贡献最少的维度。

## Decision

1. **认知优势成为架构章节。** 基线新增“认知表示与检索”（6.10）：世界模型按 L0 符号与结构、L1 关系、L2 行为路径、
   L3 职责与能力语义、L4 业务语义分层；检索采用精确符号、字面/正则、结构遍历和语义相似的混合方式，由绑定 Snapshot 的
   Cognition Retrieval Projection 提供；Knowledge Update 支持按 revision 差量的增量构建。认知投资优先放在“提问时现场推导昂贵或
   不可能”的知识上（跨文件路径、全库聚合、多来源联合、历史），而不是复制单文件即可读到的内容。
2. **分级准入。** 正式准入分为确定性通道与模型通道。已激活确定性抽取 Strategy 产出、带精确来源锚点的 Candidate，由 Knowledge
   Verifier 做机械核验（Schema、锚点可复现、抽样重放）后准入；模型产出的 Fact/Inference 仍需独立语义审核。两条通道都必须经过
   Candidate、Admission 和 Snapshot Publication。默认 Chat 中计为“世界模型认知”的内容必须来自已发布 Snapshot；未经发布的
   源码派生索引只能作为来源导航，按来源观察计入。
3. **只读工具对等。** Source Broker/Worker 为默认 Chat 提供与主流编码 Agent 读取能力对等的只读工具目录：全树路径列举、
   字面/正则搜索、按路径与行段读取、exact revision 上的历史与 blame、结构化解析查询。工具可以由隔离沙箱中的注册只读命令实现
   （无网络、无写入、临时文件系统、固定 checkout）；模型不获得任意 shell。read candidate 只服务 Citation 身份，不再是读取前置条件。
   资源熔断以 token、时延和字节为主，并保留无进展检测；预算耗尽时由主 Agent 基于已有证据形成带限制说明的答案并照常复核。
4. **Turn Trace。** 当前 Turn 的 Ledger、Package、Draft、Review 在终态后转为非权威 Turn Trace，由 Application 按保留策略
   保存（有期限、可删除、受访问控制），用于审计、评测复现和知识结晶。Turn Trace 永远不能成为后续 Turn 的证据、Citation 或
   Agent 输入。
5. **知识结晶。** Application 可从已审核、具复用价值的 Turn Trace 形成 Crystallization Proposal，交给 Knowledge Update；后者必须
   重新读取来源、形成 Candidate 并准入发布，Trace 正文不作为正式 Evidence。
6. **Reviewer 核验读取。** Reviewer 可以经同一 Broker/Worker 发起有界只读核验读取（重读被引用位置、针对遗漏的定向搜索），记录在
   独立的 Review Verification 记录中。核验观察不进入答案 Package、不能支持 Draft Claim；Reviewer 仍不作答、不生成替代 Draft、
   不放行。Finding 返回主 Agent，由主 Agent 自行取得证据。
7. **回答路径收敛。** 默认 Engineering Chat 是唯一产品回答路径。严格 `WORLD_MODEL` 与 Source-only 保留为评测与归因 Profile；
   `DIRECT_INVESTIGATION` 和 Evidence-first 问答降为兼容 Profile，不再新增功能；正式 Knowledge Use 保留为 CLI/Agent 程序化接口。

## Consequences

- 世界模型投入可以按“对答案的增益”而不是“对治理的完备”排序，并可归因。
- 确定性知识进入正式路径的成本显著降低，消除双轨。
- Agent 能力上限不再被管控机制压低；只读、exact revision、无网络和审计边界保持不变。
- 需要新增 Turn Trace 保留策略、Cognition Retrieval Projection 和差量构建，存储和实现成本上升。
- Reviewer 的成本和时延增加；其核验能力受独立预算约束。

## Alternatives

- 维持 V1.3、仅调优检索排序与预算：已被多轮 Finding 证明只能改善原题。
- 把解析索引直接定义为世界模型：失去准入与发布底座，价值归因不可信。
- 引入第二份独立答案作为复核：破坏生成与审核分离，且无法定位缺口。

## Supersedes / migration

- 修订基线 1.5、4.8、4.12（新增）、6.4、6.10（新增）、7.2、7.5—7.7、8.2、8.4、8.5（新增）、9.3、10.2、13 与第 14 节审计记录。
- 修订附录 `invariants.md`（INV-008/016/019）、`data-and-consistency.md`、`runtime-flows.md`、`components.md`，以及
  `quality/security-boundaries.md` 和 `product/success-criteria.md`。
- 部分修订 ADR-018：Turn 结束后“释放完整正文”改为转为 Turn Trace；Reviewer“不访问任何工具”改为可做有界只读核验读取。
  ADR-018 的主 Agent、证据分区、跨 Turn 不复用证据和独立审核原则不变。
- `contracts/application/engineering-conversation.md` 已按本决定重写为跨模块语义（约 18KB）；原全文含协议版本、decoder、排序权重与预算数值等
  局部规则，归档至 `docs/project/implementation-reference/engineering-conversation-contract-pre-v1.4.md`，这些规则今后由代码与测试拥有。
