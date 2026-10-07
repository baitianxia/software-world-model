---
id: PROJECT-REFERENCE-AGENT-IMPLEMENTATION-HISTORY
kind: implementation-reference
status: historical
authority: historical-evidence
owners: [engineering, project]
depends_on: [SYS-ARCH-BASELINE]
code: []
tests: []
coding_input: false
source_path: docs/system/architecture/decisions/ADR-018-conversational-engineering-agent.md
as_of: 2026-10-01
---

# agent implementation history

以下内容从 `docs/system/architecture/decisions/ADR-018-conversational-engineering-agent.md` 的实现/运行记录原样移出，保留当时措辞；其中“当前”“下一步”“须执行”均为历史语境，不是现行任务、架构决策或能力验收。读取最新工作状态应回到 [current](../current.md)。

## Product-validation strategy（历史原文）

曾经的实现计划要求先形成贯通世界模型认知、主工程 Agent、受控源码、Evidence/Citation、fresh Reviewer 和多轮 Chat 的浏览器 MVP
候选，再与异质问题和外部编码 Agent 比较；后续还计划运行多路因果对照、全量回归和硬化。该顺序、`CONTINUE` 触发和具体 Gate 是项目验证
策略，不是 ADR-018 的架构语义；它们不能授权开发、暂停开发或证明产品已验收。

## ADR-018 Consequences（历史原文）

ITER-010 的当前交付单位是完整浏览器 MVP 候选，而不是独立页面、局部知识 Profile、单轮回答或单个测试 PASS。第一次完整体验交付之后，
异质问题与 current Codex 比较立即在同一候选上进行；只有用户 `CONTINUE` 才进入完整四路消融、全量回归和硬化。这样把方向反馈提前，
但不把“可体验”误报为“已验收”，也不降低任何最终质量边界。候选答案失败时，必须先沿 Source truth、知识构建/准入、认知投影/查询、
Conversation 理解、Agent 调查、Evidence Package、答案综合、独立审核和 Delivery/UI 分层定位 first divergence，再对最早有证据的 Owner 层
实施一个通用修复批次；禁止用工程名、题目文本、关键词或固定答案补丁碰对单题。

系统需要新的 Conversation/Turn/Agent Work State 合同、Agent 工具协议、上下文选择与压缩策略，以及面向多轮对话的资格和产品验证。旧
`ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3` 的代码和运行证据继续作为可复用安全/证据资产和历史基线，但不能证明本 ADR 已实现。

当前 Access scaffold 已通过真实浏览器验证。Application-owned 主工程 Agent bounded loop、跨 Turn Work State revision、closed-catalog
工具 Proposal/Observation、双分区 Package、fresh Review Finding 回路和 exact Delivery binding 已形成
`AGENT_EXECUTOR_LOCAL_CANDIDATE`；其 Agent/Reviewer 证据仅来自确定性 fake ports。trusted evidence-tool adapter 又复用现有 World Model
projector 与 Source Broker/Worker，并把 support/boundary Observation、可重算的逐 Turn append-only Ledger prefix 和 Citation receipt 接成
`EVIDENCE_TOOLS_LOCAL_CANDIDATE`；该证据只来自确定性 World Model fixture 与临时 Git exact search/read。单 Provider primary Agent/fresh
Reviewer 的 separate no-tools Prompt、closed role input/output、逐 dispatch exact Disclosure/Gateway receipt、失败计数和 non-dispatching
candidate preflight 又形成 `MODEL_BOUNDARY_LOCAL_CANDIDATE`；成功输出仅由 pure decoder fixture 证明，真实 Gateway 测试使用的 offline
Adapter 被明确拒绝为非 live。后续实现已把 Draft 实际引用的 authority Citation 接入不可变 Turn Result 与 Browser expandable projection，
形成 `CITATION_BROWSER_PROJECTION_LOCAL_CANDIDATE`；它尚待新的 exact product identity 在真实三轮 Browser successor 中复验，不能由本地
fixture 追认为 live 或质量合格。双 Provider、真实 transport、fixed launcher 与后续 Chat 的 current 集成/执行状态以 Engineering
Conversation 合同的“当前配置实例与历史实现证据”为准，本段早期 deterministic fixture 不单独拥有其状态。后续
`FINDING-010-170` 又把同一 Turn 的重复 World Model Cognition snapshot 改为 exact-item append-only delta，并让一次同 profile repair 明确识别
JSON object 前叙述；`FINDING-010-172` 又补齐 current Request-bound prior full-source revalidation locator；`FINDING-010-173` 要求
closed-shape repair 只按 trusted exact field allowlist 重建输出、机械保持所有既有 allowlisted field value，并禁止 Primary/Reviewer 仅凭路径、package、import、symbol name 或 caller
syntax 推断类型关系/catch coverage、数据库约束、运行时配置或外部副作用。run-063 已真实证明 revalidation locator，但三轮链在后续 closed
output 失败；`FINDING-010-174` 又要求同一个 bounded diagnostic 在唯一 repair 前收集 parent 与 nested closed-shape mismatch，避免 parent
early return 隐藏可机械定位的 child missing field。run-064 只证明该 early-return 缺口并在答案前失败，故当前仍只是
`BOUNDED_CONTEXT_REPAIR_LOCAL_CANDIDATE / CROSS_TURN_SOURCE_REVALIDATION_LOCAL_CANDIDATE /
EXACT_OUTPUT_ALLOWLIST_REPAIR_LOCAL_CANDIDATE / BOUNDED_COMPLETE_SHAPE_DIAGNOSTIC_LOCAL_CANDIDATE`。run-065 随后证明 nested
diagnostic 已生效，但 shape repair 会在补字段时释义既有合法值；同一 run 还证明正文中的 material affirmative conclusion 可在未进入
Claim inventory 时绕过 final Reviewer。`FINDING-010-175` 因此以 `ENGINEERING_AGENT_OUTPUT_PREFLIGHT@4` 投影 exact-copy checklist，并要求
Primary/Reviewer 闭合完整 content-to-claim coverage。run-066 随后取得 Controller/Service current Source，但 Reviewer 把“caller 源码中执行
call expression”混同为对 callee semantics 的断言，并在给出同包收窄方案时仍标记必须补证，最终让正确的 Application 强制 action policy
关闭 Turn。`FINDING-010-176` 因此要求角色区分 invocation/order 与 callee implementation/dynamic semantics，并让 existing-Package rewrite
和真正 material evidence gap 的 remediation 互斥；当前再增加
`EXACT_REPAIR_COPY_DRAFT_CLAIM_CLOSURE_AND_REVIEW_REMEDIATION_LOCAL_CANDIDATE`。run-067 又证明模型若看不到 exact remaining Tool budget，
会先以 broad Source scan、已读 caller-expression search 和辅助资源 read 消耗 Source slot，再对同一 implementation gap 换句式重复查询
World Model，最终在答案前撞上 8-action 上限。`FINDING-010-177` 因而把 exact budget projection、fresh World Model-first、semantic-gap
no-requery 和 unresolved-target Source relevance 纳入主 Agent interface；上限保持 8，零预算只允许基于现有 Evidence 收敛或失败关闭。当前
增加 `BOUNDED_INVESTIGATION_BUDGET_AND_TARGET_RELEVANCE_LOCAL_CANDIDATE`，仍须由 fresh exact Browser successor 验证。

后续 `FINDING-010-180/181/182/183` 又依次把 cognition-derived first Source target、trusted Search-only path scope、Search
operation-local Boundary 与 whole-Turn fuse、以及 same-Package rewrite 的 immutable origin/current Delivery chain 闭合。fresh
`run-074` 首次形成并交付真实三轮语义 Conversation，另一个独立分类删除问题也成功；Maven/启动链问题则暴露新的 repair 合同矛盾：初始
`SOURCE_SEARCH.arguments` 只有一个完全不含 allowlisted item field 的 invalid object，合法 repair 必须从 sealed action template 重建为两个
`name/value` item，但 `@4` projection 仍把原 array 长度 `1` 当作 copy obligation，且模型同时把既存文本中的 `—` 释义为 `-`，所以安全
guard 必然拒绝。`FINDING-010-184` 因而把 final preflight 升为 `ENGINEERING_AGENT_OUTPUT_PREFLIGHT@5`：只有 schema-invalid array 的全部
item 都没有任何既存 allowlisted value 时，该子树才不形成 copy obligation并可从 current sealed schema/domain/template 重建；只要存在一个
合法 item value，原长度、顺序与 sibling 守恒不变。对其余可对齐既存值，Application 在 Proposal decode 前只执行版本化的 prior-exact
restoration，再重验机械相等；它不生成 missing field、不映射 unexpected field、不重建 invalid subtree，也不授予事实、Tool、Review 或
Delivery 权限。raw repair 漂移仍不获授权，无法恢复或 downstream contract 不成立仍失败关闭。当前增加
`SCHEMA-INVALID-ZERO-COPY-SUBTREE-REBUILD_AND_EXISTING-VALUE-RESTORATION_LOCAL_CANDIDATE`，fresh Browser successor 仍须验证失败题与异质题。

fresh `run-075` 已让 Maven/启动链旧失败题以 Ark 8 次形成 Answer/Review/Delivery，证明 `FINDING-010-184` 越过真实失败点；但两个新系统性
偏差继续阻止质量资格。角色重分配题的最新 Source receipt 已达 `64/64`，effective catalog 只剩 `WORLD_MODEL_QUERY`，model-facing
`source_read_options` 却继续暴露未读 controller locator，repair 复制 dangling `SOURCE_READ` 后被正确拒绝；`FINDING-010-185` 因而要求
Application 投影 `ENGINEERING_AGENT_SOURCE_FILE_BUDGET@1`，并让 executable read options 与 effective catalog 在 exhausted 状态共同关闭，
同时不伪造 Broker terminal denial。订单追问又把消息发送放在“数据库写入一定未发生”的标题下，但 Claim 只枚举调用顺序，fresh Reviewer
遂对窄 Claim 全部 `SUPPORTED`；`FINDING-010-186` 因而把 heading/table/list 的 category、scope、condition、certainty、negation 纳入完整
assertion 与 Claim inventory，Reviewer 必须以容器语境重建 assertion，漏 qualifier 用 global Finding、错误 qualifier 用 concrete defect。
当前增加 `SOURCE-BUDGET-REFERENCE-CATALOG-COHERENCE_AND_INHERITED-CONTAINER-ASSERTION-CLOSURE_LOCAL_CANDIDATE`；fresh Browser successor 与
独立技术复核仍是质量阻断。

fresh `run-076` 的角色重分配题已完成前 9 个 Ark call、真实 Source Search/Read 和 Answer Draft，证明旧 dangling locator divergence 已被
越过；Application 随后正确阻断 BOUNDARY observation 被 Claim 当作 support。repair 与后四个冻结 Turn 的首个 call 连续返回 raw
`PROVIDER_HTTP_ERROR`，但没有 availability owner 的受信 unavailable verdict，故已获周末闲时 admission 的 fallback profile 保持零 dispatch。
该 run 没有交付答案，不能验证容器语义或质量。它还证明 EMPTY CONTEXT policy 漏掉“这些/那些/此类”等复数/类别指示，Browser 又只显示
execution-stage code；`FINDING-010-188/189` 已分别闭合 Provider 前通用 Clarification 与 execution/raw-provider 分层显示，不改变 Agent、
route 或 fallback architecture。fresh exact Browser successor 仍是唯一产品证据。

同一 run-076 的 pre-delivery Draft 后续审计又发现 Primary 把 Cognition coverage gap 写成“超出当前授权”，并在只读 producer-side
`UmsAdminServiceImpl` 时推断 consumer-side 登录态权限刷新；Source Profile 实际仍授权相关 Java，且该 Turn 还剩一个合法 action。
`FINDING-010-191` 因而要求 Primary/Reviewer 分开 authority、coverage、tool 和 runtime state，并把 producer invocation、callee effect 与
consumer-visible lifecycle 作为不同证据义务。该 local candidate 只由 exact artifact/source 对照和定向测试支持，尚未取得 fresh
Primary/Reviewer live 质量证据。

继续向上游审计同一 Draft 的 exact model input 后，`FINDING-010-192` 把 first divergence 前移到 World Model evidence-tool adapter：正式
Cognition Context 的 global Coverage/Gap 已正确进入 BOUNDARY，却又被复制进 model-facing SUPPORT 顶层，使 Primary 可只引用 SUPPORT ID
而使用 Boundary 语义。当前决策要求 SUPPORT 只携带 novel affirmative item 及其 per-item coverage；global coverage/conflict/unknown
继续绑定正式 Context、Ledger 和 receipt，但 model-facing 内容只进入 BOUNDARY。Primary/Reviewer policy 仍保留为独立下游 guard。

`FINDING-010-193` 进一步分开 audit retention 与 answer disclosure：Ledger/Package 继续完整保留 Boundary，但 Primary 只向用户报告仍限制
current material requirement 的具体边界。后续 full SUPPORT 已闭合的 Search/budget/Provider acquisition diagnostic，以及没有限制具体
requested conclusion 的 global inventory/coverage metric，只留在 audit；Reviewer 对其 user-visible 泄漏返回无需补证的 relevance Finding。

`FINDING-010-194` 证明仅移除 SUPPORT 顶层 global Coverage 仍不足：原 `dimensions` 还混入 typed `COVERAGE/UNKNOWN` eligibility metadata。
当前 `ENGINEERING_AGENT_WORLD_MODEL_SUPPORT@4` 在 adapter 机械限制 affirmative dimensions 为
`ENTITY/RELATION/BEHAVIOR/CONSTRAINT/STATE`，并让 counts、Citation refs 与 Source target 同域；`COVERAGE/EVIDENCE/UNKNOWN` 只保留正式
Context/receipt/audit 身份，metadata-only Context 形成 Boundary。

`FINDING-010-195` 又把 run-076 的商品、营销和通用 Controller 噪声定位到更早的 Application query projection：结构 discriminator、公共
`source_path` 前缀、function token 和任何正分尾部被误当成 relevance。current 决策要求 cohort-aware、representation-free 的确定性排序：
path 只贡献 basename，公共 exact token 不作 anchor，prefix-only 与弱尾部在已有强 exact match 时关闭；正式 Snapshot、Coverage、authority、
Source 权限和 incomplete Profile 边界均不改变。

`FINDING-010-196` 继续关闭 answer synthesis/review 的普通邻接扩张：Primary 与 Reviewer 对每个 user-visible affirmative detail 和 Boundary
执行 counterfactual relevance test，删除后 requested conclusions 仍完整时必须省略，且不得为 Draft 自己引入的细节扩大调查。path、package、
import、symbol 或 directory convention 也不能证明 code-generation/tool provenance；真正 material 的 provenance 结论必须有 direct current
SUPPORT。该规则不让 Application 按关键词删句，也不改变 Tool、Source、Evidence 或 Delivery authority。

`FINDING-010-197` 又关闭 multi-Profile projection 的 cross-scope 泄漏：当 original User Message 精确点名 sealed Source allowlist 的
top-level scope 时，Application 在 relevance ranking 前排除 formal Coverage root 与它完全不相交的非 repository-wide Profile，其
affirmative item 与 Profile gap 都不得进入该 query Context；repository-wide partial Profile 仍可参与。selector 只来自原始问题与 allowlist
的 exact boundary match，模型 query 不能改写；mismatch 作为 Coverage Boundary 披露，不冒充授权拒绝。Snapshot、Read Authority、Manifest、
Source Profile 和 Broker authority 均保持不变。
