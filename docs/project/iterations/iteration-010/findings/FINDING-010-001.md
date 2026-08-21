---
id: FINDING-010-001
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [product, architecture, application, quality]
depends_on: [ITER-009-RESULT-SLICE-001-STOP-REDIRECT, SYS-PRODUCT-SUCCESS, SYS-ADR-014, SYS-ADR-015]
code: []
tests: []
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: define-explicit-engineering-qa-hybrid-evidence-mode-while-preserving-strict-world-model
target: SYS-ADR-016
---

# FINDING-010-001：严格 Source-off WORLD_MODEL 不能独自承担默认通用工程问答

## Observation

ITER-009 Slice1 的真实本机 Web 可以执行多轮 World Model 调查、Draft、独立 Review、Limitation 和 Citation，但用户体验是答案像代码走读
或代码实现说明。随后用户进一步质疑：为什么在提问时不读取源码。两项反馈共同说明，问题不是单个措辞，而是默认产品路径把“证明
预构建 World Model 可独立回答”的评测边界当成了普通用户工程问答的唯一数据边界。

## Evidence and root cause

- `ITER-009-RESULT-SLICE-001-STOP-REDIRECT` 保留了三条真实 Web 结果和用户 `REDIRECT`：正文被方法、分支、调用顺序、源顺序和返回值
  主导；Reviewer 没有把是否直接回答与抽象层级匹配作为阻断条件；
- `SYS-PRODUCT-SUCCESS` 当前把通用源码问答 MVP 与“提问时不读取 Source”绑定；
- `SYS-ADR-014` 明确规定 `WORLD_MODEL` 只读 exact Snapshot，知识不足不回源；
- `SYS-ADR-015` 只允许 Agent 在 no-payload Bundle 上做有界 typed 查询，并明确拒绝 Answer Agent 读取 Source；
- `SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING` 和 Local Browser 把上述边界落实为 Answer role 的强隔离。

这些约束对严格 `WORLD_MODEL` 的复用/隔离验证是正确的，但它们不能同时作为默认通用工程问答的召回边界。工程用途、启动方式、配置、
故障、变更影响等信息可能位于源码、README、构建配置或测试中，尚未形成正式 World Model facet；把 Snapshot 命中作为 query-time Source
检索的硬门禁，会系统性地产生 Gap 或把现有实现知识机械展开。问题分类为 `architecture / systemic`，不是 local Prompt 或 Web 展示缺陷。

## Decision and disposition

用户以 `codex-user-message:sha256:5cdb7000ba36328f5caa27727c6b689ad4e98e7ad13eca72837fa020d0c270c9` 于
`2026-08-21T07:10:28Z` 接受新的明确边界：

- 新默认 `ENGINEERING_QA` 是显式、自适应调查主路径，不是 `WORLD_MODEL` 失败后的静默 `DIRECT_INVESTIGATION` fallback；
- World Model 是软件系统持久、版本化外部认知；工程地图、手册、可复用证据和检索提示只是其任务投影，并且不是 query-time Source
  recall Gate；
- 检索计划同时来自不可变 original-question checklist 与 Snapshot hints；Snapshot 为零、无关或 Coverage 不足不能阻断同一授权 exact
  revision 的受控 Source/doc/config/test 检索；
- Investigation LLM 根据 prior Ledger Result 提出下一步；Source Broker/隔离 Retrieval Worker 只读授权来源，结果追加到 Ledger，调查结束
  后才形成密封 Evidence Package；Source 按不可信输入处理；Answer 与 Reviewer 无 repo/Source 工具；
- Package 是 Answer/Reviewer 唯一可采信和引用的支持集合，但 seal 不赋予内容真值；Reviewer 若给出具体
  `MORE_EVIDENCE_REQUIRED`，Application/Broker 才能在相同 authorization/revision/预算内形成后继 Ledger/Package/Answer/Review；
- live 前必须单独冻结哪些片段可发给哪个 exact Provider/model/role；初始开发授权不允许外发；
- 严格 `WORLD_MODEL` Source-off 模式与显式 `DIRECT_INVESTIGATION` 继续保留，三者身份、结果和资格不得混淆；
- 高质量证据/结论的知识沉淀在 Delivery 后异步进入正常 Admission/Publication，不阻塞当前回答。

主要处置目标是新 `SYS-ADR-016`。同一环境准备变更同步更新 Product Success、runtime flow、Agentic Task、新 Engineering Question
Answering Contract、Evidence/World Model/Response/Source、安全、Browser 和治理检查器/测试，使架构、Contract、Manifest 与 docs gate 原子
一致。`SYS-ADR-016.derived_from` 只记录本 Finding 的来源追溯，不作为反向 `depends_on`；本 Finding 不依赖 Proposal/ADR-016，避免处置链
形成依赖环。

## Verification after disposition

处置的机械验证由 `ITER-010 / V-ARCH-001` 拥有：新 ADR/Contract 必须 current/accepted，fileset digest 精确，strict WORLD_MODEL 与
DIRECT 旧边界回归继续 PASS，ENGINEERING_QA 的 mode、Owner、allowlist、package、role isolation、supplemental retrieval、Provider
disclosure 和 failure-closed 语义可由文档检查与确定性测试验证。

当前 Finding/系统文档处置不包含产品实现、credential 读取、Provider/model call、live Web/browser、hidden input 或 Production；这些
结果不能在本 Finding 中预报 PASS。

后续用户讨论进一步修正了提问期调查职责和“手册”比喻，见 `FINDING-010-002`；本 Finding 关于默认工程问答需要受控回源的根因结论
继续有效。
