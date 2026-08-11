---
id: ITER-003-PROPOSAL
kind: iteration-proposal
status: completed
authority: historical-project
owners: [product, engineering]
depends_on: [ITER-002-RESULT-ACCEPTANCE, SYS-PRODUCT-VISION, SYS-ADR-014, SYS-CONTRACT-KNOWLEDGE-STRUCTURE-MODEL, SYS-CONTRACT-APPLICATION-STRUCTURE-VIEW, SYS-QUALITY-ACCEPTANCE]
code: [src/software_world_model, validation/structure_world_model_iteration_003]
tests: [tests]
iteration: ITER-003
coding_input: false
---

# ITER-003 Proposal：Structure World Model 纵向闭环

## Trigger and evidence

ITER-002 证明受控 Evidence-first 源码调查能在六个问题上与直接源码基线打平，但没有证明正式知识被构建、更新或用于回答。开发前反例还发现：现有 Fact 缺少 typed target Entity、Entity ID 受 revision/Evidence 影响、Publisher 会把被删除关系继承到新 Snapshot。继续做 UI 或 Agent 会产生可演示但不可信的世界模型。

## Outcome and users

用户在没有提问的情况下，也能对一个 exact Maven Git revision 手动构建或更新 Structure World Model；关闭 Source Provider 后，回答进程只凭不含 Evidence payload 的 exact Snapshot Read Bundle 重启，仍能在浏览器查询模块、内部直接依赖、路径和版本差异，逐项查看 Coverage 与证据引用。引用正文由隔离 Citation Projector 展示；提问不触发更新，也不静默读取源码。

## Scope / non-goals

范围仅包括 Local Git、单个新 Knowledge Scope、`MAVEN_REACTOR_STRUCTURE@1`、Maven reactor child modules 与本地声明的直接内部依赖、typed Relation Fact、稳定 Root/State、`REPLACE_COVERAGE`、Structure View、独立手动更新、Snapshot-only 浏览器问答及直接调查对照。

非目标包括 Behavior/Business/History、全语言全问题、自动 Scheduler 或来源事件、跨 Scope 多源融合、已有 Scope 的跨 Schema 迁移、传递依赖知识、认证、网络部署和 Production Activation。自动更新仍是后续能力，但本轮更新入口必须与提问解耦。

## Adopted system IDs

- `SYS-ADR-014`
- `SYS-ARCH-INVARIANTS`
- `SYS-CONTRACT-KNOWLEDGE-ENTITY`
- `SYS-CONTRACT-KNOWLEDGE-FACT`
- `SYS-CONTRACT-KNOWLEDGE-STRUCTURE-MODEL`
- `SYS-CONTRACT-KNOWLEDGE-SNAPSHOT-PUBLICATION`
- `SYS-CONTRACT-KNOWLEDGE-PERSISTENCE`
- `SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE`
- `SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE`
- `SYS-CONTRACT-APPLICATION-STRUCTURE-VIEW`
- `SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING`
- `SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL`
- `SYS-CONTRACT-AI-MODEL-GATEWAY`
- `SYS-CONTRACT-AI-CAPABILITY-EVALUATION`
- `SYS-QUALITY-ACCEPTANCE`
- `SYS-OPS-LOCAL-BROWSER`

## Development slices and dependencies

本轮只有一个纵向 Slice。它内部使用阻断 Gate：授权后先以 G0 Result 复核全部冻结资产；G1 用可查看 CLI 证明 typed relation、稳定身份和删除语义；G2 证明 no-payload Read Bundle、受控 Entity candidate resolution 与双进程引用隔离；G3a 无外部分派实现完整权威链，形成 exact checkpoint 后才做 CC/closed CE，并在 G3b 前先密封同模型 Direct Source 与成熟 Codex Source Agent 两条 baseline；G3b 才运行隔离评测浏览器；G4 执行重复人工产品验收。任何 Gate 失败都停止后续层，不以增加 UI、Prompt 或名称匹配掩盖知识内核问题。

新 Profile 只在没有 CURRENT 的新 Scope 执行 `INITIAL` adoption。exact Schema、Evaluation Context 与 Canonicalization 分别为 `MAVEN-REACTOR-STRUCTURE@1.0.0`、`MAVEN-EVALUATION-CONTEXT@1.0.0`、`MAVEN-REACTOR-CANONICALIZATION@1.0.0`；三个 Definition 和 digest 已进入 Manifest。复用旧 Scope 会触发未启用 Schema Evolution，不属于本轮。

## Risks and unknowns

- Maven effective coordinates 的继承、属性解析和歧义必须失败关闭，不能按 artifactId 或路径猜测。
- root project 单独建模为 `SOFTWARE_SYSTEM`，reactor child module 计数明确排除 root；root 与 child 的直接依赖声明都必须扫描，不能用未覆盖来证明“没有依赖”。
- `REPLACE_COVERAGE` 必须只删除声明 Coverage 内的旧成员，不能误删其他知识。
- Snapshot-only 答案可能诚实返回 Gap；不得用源码 fallback 把 Gap 伪装为世界模型成功。
- 模型生成存在概率波动，必须重复冷启动、保留全部失败并设置高位熔断。
- 把公开冻结工程片段发送给外部 Provider 仍需要在 live Gate 前确认披露范围；本地确定性开发不依赖该权限。

## Verification and acceptance

验证以 `mall` 的 A1→B→A2 exact 图、版本化 Maven 正/负 fixture、悬空/歧义/重叠 Coverage 反例、同名 Entity resolution 和真正隔离工作树/数据库/Evidence Store 的 Source-off 重启为主线。exact 问题套件、措辞变体、运行时随机身份/拓扑与不受支持的“为什么”问题共同防止硬编码；产品只能看到 question input，Oracle/expected/两条 baseline results 仅评测器可见。每题至少运行五次并包含冷启动。Structure Coverage 支持题逐题重大错误为零，正确性与完整性不得低于 G3b 前按冻结协议密封的两条源码 Agent baseline 中更强者；why 题只验诚实 Knowledge Gap，不要求追平可回源路径。每个 Gate 必须保存独立、可人工查看且绑定 exact checkpoint 的 Result。

## Authorization decision

用户于 2026-08-10 明确要求“开发 ITER-003”，据此接受本 Proposal 并授权 `ITER-003-SLICE-001`。授权治理提交 Q 后仍只能执行 G0；绑定 Q 的 `ITER-003-RESULT-G0` 提交为 PASS 后才可修改产品代码并开始 G1。外部模型披露、Production Activation 和本轮非目标不因编码授权而自动获得授权。
