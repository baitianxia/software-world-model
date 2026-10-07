---
id: PROJECT-REFERENCE-ENGINEERING-CONVERSATION-HISTORY
kind: implementation-reference
status: historical
authority: historical-evidence
owners: [engineering, project]
depends_on: [SYS-ARCH-BASELINE]
code: []
tests: []
coding_input: false
source_path: docs/system/contracts/application/engineering-conversation.md
as_of: 2026-10-01
---

# engineering conversation history

以下内容从 `docs/system/contracts/application/engineering-conversation.md` 的实现/运行记录原样移出，保留当时措辞；其中“当前”“下一步”“须执行”均为历史语境，不是现行任务、架构决策或能力验收。读取最新工作状态应回到 [current](../current.md)。

## 当前配置实例与历史实现证据

当前 ITER-010 配置把 Ark 映射到 `preferred` execution profile，把 DeepSeek 映射到 `fallback` execution profile；以下具体名称、状态和运行
记录只描述当前配置实例与历史实现证据，不定义本契约的 route 分支、质量、授权或 Agent 语义。

当前独立 Chat Access 已提供 Application-owned Conversation/Turn/Message、不可变 Revision、完整页面消息历史、“新对话”隔离与失败
Turn 后 Conversation 继续，并已通过真实 browser Access Case。Application-owned bounded executor 也已在确定性 fake ports 上密封跨 Turn
Work State revision、工具 Observation、support/boundary Package、Answer、fresh Review 与 Delivery Authorization；协议错绑、缺证后无新
Observation 重写、无进展和资源熔断只关闭当前 Turn。trusted evidence-tool adapter 已复用现有 World Model projector、Source Broker 与
Retrieval Worker；同一动作可分别密封 support/boundary，每条 Observation 携带 exact Turn/Tool/revision、Application 可重算的完整
append-only Ledger entry chain/prefix 与 Citation content digest，Source READ 只接受本 Turn 先前签发的 opaque locator。状态为
`ACCESS_BROWSER_PASS / AGENT_EXECUTOR_LOCAL_CANDIDATE / EVIDENCE_TOOLS_LOCAL_CANDIDATE / MODEL_BOUNDARY_LOCAL_CANDIDATE /
PROVIDER_ROUTE_COMPOSITION_LOCAL_CANDIDATE / PROVIDER_RUNTIME_COMPOSITION_LOCAL_CANDIDATE /
SESSION_RUNTIME_COMPOSITION_LOCAL_CANDIDATE / ARTIFACT_SESSION_V3_ADMISSION_LOCAL_PASS /
ARK_TRANSPORT_SESSION_AUDIT_LOCAL_CANDIDATE / PUBLIC_SOURCE_STANDING_AUTHORITY_DERIVATION_LOCAL_CANDIDATE /
SEVENTH_LIVE_CHAT_THREE_OF_FIVE_LIMITATIONS_OVERALL_FAIL / NEW_CONVERSATION_LEAKAGE_PASS /
V7_UNACCEPTED_SYMPTOM_EXPERIMENT / V8_SEMANTIC_NEED_QUERY_LOCAL_CANDIDATE / RUN043_QUALITY_REWORK /
SESSION_AUTHORITY_REQUIRED / NOT_PRODUCTION`。单 Provider Agent/Reviewer 已使用 separate closed no-tools contracts、逐调用 one-use
Disclosure 和 typed Gateway receipt；pre-dispatch、fresh dispatch、outcome unknown 与 replay 的计数由 Application 重验，Turn/Browser 只保存
receipt digest reference。Application-owned generic preferred→fallback router（当前配置实例映射 Ark→DeepSeek）、committed Work State repository、两 attempt receipt、logical Turn 汇总与
non-starting fixed Browser composition 已通过本地确定性 Gate；预检没有创建 attempt、启动 listener、解析 credential、读取 Source 或 dispatch。
Provider runtime composition 已使用生产 Ark/DeepSeek Adapter 与 credential-lazy transport，但只消费本地构造的 typed qualification identity。
non-starting Session runtime 又把两条 Provider runtime、exact evidence authority、per-attempt fresh Tool/Response Control、共享 committed
   Work State、Conversation 与 Browser 组合成一个对象图；preparation 没有创建 attempt、读取 Source、解析 credential、dispatch 或启动 listener。
artifact Session loader 现可从一个 owner-private closed document 绑定 product/source Git identity、ordered profile-specific published
World Model authorities、Source Profile、Ark→DeepSeek qualification identity、两个 private Gateway repositories 与 Session authority；
current `@4` 在逐 Profile 重验 expected file/Bundle digest、Profile/Schema/Source Binding/selected Snapshot 并形成 Capability Manifest 后，
还要求在 Provider network/credential 前重验公开 upstream、clean HEAD、exact commit/tree、license object、standing scope 和 DeepSeek
admission，再派生 exact Session/Turn/call 摘要链且记录人工重复审批数 0；`@3` admission、`@2` 多 Profile 与 `@1` 单 Profile 配置继续
只读兼容，但不能取得 current standing-authority preparation 状态。唯一 `--session-config` selector 让固定
`127.0.0.1:8765` 命令消费该组合，并在 listener 前/停止后分别密封 launch/terminal receipt；terminal 已验证 Ark/DeepSeek transport audit。
PDR-014 `@5` 在完整继承 `@4` standing scope 的同时，额外固定一个 `JAVA_CAPABILITY_COGNITION@1` private artifact 的 path、digest、snapshot
ID 和 exact Source revision/tree；只有全部重算一致才启用 `WORLD_MODEL_SOURCE_LIGHTWEIGHT_AGENT`，否则在 listener、credential 与 Provider
dispatch 前失败关闭。没有该字段的 `@4` 继续形成同 Agent source-only 消融臂。
Ark HTTP 前 transport unavailable 也已通过 Gateway owner-typed 为 availability raw evidence，但受信 availability-owner verdict 尚未闭合，不得追认为 fallback eligibility。历史 fresh Ark 与 DeepSeek Conformance 已分别以
exact clean identity、2/2 request 和 strict Session audit PASS，并按各自 exact identity 用于多个 owner-private mall artifact Session。`run-035-chat-alpha` 与
`run-036-chat-alpha` 均真实启动 listener、执行 Browser 五轮 Chat、消费受限 Source/Provider 并优雅停止，但五轮各自 5/5 失败；run-036 的
新 Conversation probe 已以 Application clarification、零 dispatch 和空 Context 通过泄漏负测。run-037 在 fresh 双资格后仍为 0/5；v3
tool copy domain 与 Reviewer assessment 随后形成。`run-038-chat-alpha` 再次取得 fresh 双资格并执行五轮，其中仅 Turn 5 以 reviewed
Limitation 技术成功，整体仍为 1/5 / Quality FAIL；v4 随后关闭 Source resource domain 与 no-progress completion。`run-040-chat-alpha`
在 v4 fresh 双资格后仍只有 Turn 2 的 reviewed Limitation，整体 1/5 / Quality FAIL；v5 随后把 previous Work State Observation IDs 移出
current Turn copy domain，并要求 `requires_evidence` Review successor 只能提交 exact tool action。`run-041-chat-alpha` 已让 Turn 1
Answer 与 Turn 3/4 reviewed Limitation 技术成功，但 Turn 2 重复 exact Source action、Turn 5 在 empty SUPPORT domain 复述 prior
Answer，故整体仍为 3/5 / Quality FAIL。v6 successor 把 response kind 与 tool argument 的 current feasible domain 就地密封；
strategy/prompt/Primary input identity 再次改变，所以 run-041 只保留为执行证据。`run-042-chat-alpha` 已在 v6 对应 route 资格后执行：
Turn 2/3/4 为 reviewed Limitation，Turn 1 review limit、Turn 5 model-call rejection，仍为 3/5 / Quality FAIL；新 Conversation
clarification/隔离/零 dispatch 继续 PASS。后续 v7 的 path-relevance prompt guidance 与 review-scope policy 没有经过逐层因果归因或跨题
验证，只是已停止的本地症状实验，不能成为 current Contract、Conformance 失效原因或下一次 live 重跑入口。run-043 随后把 first
divergence 定位到 semantic `evidence_need` 未进入 Cognition query；current v8 已在 Application 边界本地闭合该绑定，并以两个未参与修复
的异质问题做真实 bundle 诊断。run-043 的答案质量和 DeepSeek 峰时调度 FAIL 均保持；领域 Prompt 变化本身不触发 ADR-017 Provider
Conformance。`run-060/061/062` 又依次暴露同 Turn 重复 Cognition、closed operation repair 诊断和跨 Turn full-source 重验缺口；
`FINDING-010-170/171/172` 已分别形成 `BOUNDED_CONTEXT_REPAIR_LOCAL_CANDIDATE / CLOSED_TOOL_DIAGNOSTIC_LOCAL_CANDIDATE /
CROSS_TURN_SOURCE_REVALIDATION_LOCAL_CANDIDATE`。run-063 已真实证明 revalidation locator 在 Turn 2 生成相同 content digest 的新
current-Turn Citation，但同一答案又包含 indirect type-relation overclaim 且 Reviewer 漏判，Turn 3 的 initial/repair output 连续把
input-only `work_state_ref` 加入 closed output。`FINDING-010-173` 已形成 `EXACT_OUTPUT_ALLOWLIST_REPAIR_LOCAL_CANDIDATE`。run-064 随后
证明 parent mismatch 的 early return 会隐藏同份 output 的 nested missing field；`FINDING-010-174` 已形成
`BOUNDED_COMPLETE_SHAPE_DIAGNOSTIC_LOCAL_CANDIDATE`。run-065 Turn 1 真实成功但 material narrative conclusion 未进入 claims 且 Reviewer
漏判，Turn 2 的 nested diagnostic 正确、shape repair 却改写既有合法值而被机械守恒拒绝；`FINDING-010-175` 已形成
`EXACT_REPAIR_COPY_AND_DRAFT_CLAIM_CLOSURE_LOCAL_CANDIDATE`。run-066 又在 current Controller/Service Source 已足够证明 caller
invocation/order、Draft 已声明 callee semantics 未知时，被 Reviewer 错标为强制补证；Application 正确执行 tool-action-only successor 并
在 Primary 未服从时失败关闭。`FINDING-010-176` 已形成
`CALL_EXPRESSION_EVIDENCE_AND_REVIEW_REMEDIATION_LOCAL_CANDIDATE`。完整三轮仍须新 exact product identity 的 fresh Browser successor 验证，
不能追认这些失败 run 或把局部技术成功称为 MVP。
run-067 随后在 fresh Turn 跳过 World Model，以 broad Source search、已读 caller expression search 和辅助 Mapper read 消耗 Source slots，
再对同一 service implementation gap 连续换句式查询 World Model；第九个 Primary call 提出第九项 Tool action，Application 在执行前以
8-action 上限失败关闭，仍无 Draft/Review/Delivery。`FINDING-010-177` 已形成
`BOUNDED_INVESTIGATION_BUDGET_AND_TARGET_RELEVANCE_LOCAL_CANDIDATE`：Primary input 精确投影 remaining budget，零预算撤销 catalog 并要求
收敛；fresh 无 revalidation 调查机械要求 World Model-first；同义 gap requery 与不命中 unresolved target 的 Source 选择被明确禁止。上限
保持 8，不以扩容掩盖路径漂移；fresh exact Browser successor 仍是唯一产品验证。
run-085 随后完成 52 次 Ark HTTP dispatch，其中 51 次完成、1 次在发出后成为 `PROVIDER_OUTCOME_UNKNOWN`；没有 HTTP 前 trusted
unavailable，故 DeepSeek 0 正确。Q4 fresh Conversation 零 dispatch Clarification 继续通过，其余工程 Turn 未交付。Q1 暴露 Reviewer nested
`challenge_id` 与 existing-value repair 缺口；Q3 暴露 Boundary evidence binding 被误作 raw metadata 全文披露，并继发空 Boundary
`LIMITATION` 与 action/phase 冲突；Q5 的 action argument shape 和 required-action branch 漂移耗尽既有 15 次 authority。
`FINDING-010-208` 已形成 current `@13/@7/@8` nested closed-shape、trusted branch、binding/disclosure 和 untrusted typed-error candidate；
144 项定向测试 PASS，fresh run-086 仍须证明真实 Answer/Review，run-085 保持质量 FAIL。
run-086 随后完成 49 次 Ark HTTP dispatch，其中 47 次完成、2 次在发出后成为 `PROVIDER_OUTCOME_UNKNOWN`；没有 HTTP 前 trusted
unavailable，故 DeepSeek 0 正确。Q4 fresh Conversation 零 dispatch Clarification 继续通过，其余工程 Turn 未交付。Q2 暴露 final
preflight 未重复 exact SUPPORT/BOUNDARY ID domains；Q3 暴露 Review successor 只收到 Findings/digest、没有收到 exact rejected Draft，
使同包重写的 Claim inventory 从 `5 → 10 → 7 → 13` 扩张并产生新缺陷。`FINDING-010-209` 已形成 current `@14/@7/@9` exact rejected-Draft
edit base、targeted rewrite 与 redundant reference-domain preflight candidate；144 项定向测试 PASS，fresh run-087 仍须证明真实 Answer/Review，
run-086 保持质量 FAIL。
run-087 随后由 Ark 10 个完成 call 与 4 个 sealed `429 / AccountQuotaExceeded` call 触发合法 DeepSeek fallback；DeepSeek 42 个完成 call、
1 个 post-dispatch `REMOTE_DISCONNECTED / PROVIDER_OUTCOME_UNKNOWN`，retry/人工审批/Production 仍为 0。Q4 fresh Conversation 零 dispatch
Clarification 继续通过；Q1/Q2/Q5 均以 Review limit 失败，Q3 按 unknown no-retry 失败。Q1 的 exact rejected Draft Claim inventory 保持
`4 → 5 → 6 → 6 → 6`，证明 `FINDING-010-209` edit base 已真实生效；新的 first divergence 是 Reviewer 把 exact-revision provenance、grouped
Claim 与已明确 local order 按 phrase 重复拆分。Q2/Q5 又证明 generic global-completeness Claim exception 与 `LIMITATION` 零 Claim branch
互相冲突，且 opaque Boundary binding 被误作必须在正文披露。`FINDING-010-210` 已形成 current `@15/@8/@10` semantic Claim coverage、
response-kind-aware rewrite 与 hidden Boundary binding candidate；144 项定向测试 PASS，fresh run-088 仍须证明真实 Answer/Review，run-087
保持质量 FAIL。
run-088 随后由 Ark 4 个 sealed `429 / AccountQuotaExceeded` call 触发合法 DeepSeek fallback；DeepSeek 52 个完成 call、1 个
post-dispatch `REMOTE_DISCONNECTED / PROVIDER_OUTCOME_UNKNOWN`，retry/人工审批/Production 仍为 0。Q4 fresh Conversation 零 dispatch
Clarification 继续通过；Q1/Q5 在下一 Reviewer 前耗尽 authority，Q2 达到 Review limit，Q3 按 unknown no-retry 失败。新的 first
divergence 是 comprehensive Reviewer 逐轮只报一个 defect并重复 Finding identity，focused Reviewer 让 closed assessment body 与
decision/Finding 自相矛盾，Primary 又未在一个 replacement 中解决全部 ordered Findings。`FINDING-010-211` 已形成 current
`@16/@9/@11` complete-Draft audit、focused exact closure、Reviewer-authored decision repair、未引用 duplicate local-code disambiguation 与
all-Findings rewrite candidate；146 项定向测试 PASS，fresh run-089 仍须证明真实 Answer/Review，run-088 保持质量 FAIL。
run-089 由 Ark 4 个 sealed `429 / AccountQuotaExceeded` call 再次触发合法 DeepSeek fallback；DeepSeek 27 个完成 call、1 个
post-dispatch `REMOTE_DISCONNECTED / PROVIDER_OUTCOME_UNKNOWN`，retry/人工审批/Production 仍为 0。Q4 fresh Conversation 零 dispatch
Clarification 继续通过；Q1 的 focused closure guard 正确拒绝 Reviewer 矛盾 body，但同-profile repair 原样复制；Q3 在 World Model 与 Source
Search Boundary 已允许 Limitation 时仍连续复制 forbidden exact query；Q5 的 Primary 两次返回 exact rejected Draft，comprehensive Reviewer 又在
Limitation 上要求 Claim、误报已有 Boundary binding 并把 Search/interface 当实现证据。`FINDING-010-212` 已形成 current
`@17/@10/@12` changed-replacement guard、typed closed-contract convergence directive、actual focused index diagnostic 与 response-kind-aware
Limitation review candidate；147 项定向测试 PASS，fresh run-090 仍须证明真实 Answer/Review，run-089 保持质量 FAIL。
run-090 的 Ark 33 个 call 中 31 个完成、1 个 pre-dispatch TLS failure、1 个 post-dispatch unknown；Q3 fallback 因 pricing evidence 超过
900 秒在 DeepSeek credential/TLS/HTTP 前关闭，DeepSeek dispatch 0，retry/人工审批/Production 仍为 0。Q4 fresh Conversation 零
dispatch Clarification 继续通过；Q1 的 coherent closed-contract repair 回退到 non-JSON prefix 后旧单向 category gate 未使用第二个 repair
slot，Q2 的 audit-only relevance assessment 缺 Finding code且 generic repair 原样返回。`FINDING-010-213` 已形成 current
`@18/@11/@13` distinct-category final repair、单义 audit-only diagnostic/typed closure 与 final-preflight directive candidate；模型边界 34
项测试 PASS，相邻定向集与 fresh run-091 仍须证明真实 Answer/Review，run-090 保持质量 FAIL。
run-091 的 Ark 38 个 call 中 37 个完成、1 个 post-dispatch `REMOTE_DISCONNECTED / PROVIDER_OUTCOME_UNKNOWN`，不存在可信 pre-dispatch
unavailable verdict，故 DeepSeek dispatch/credential/TLS/HTTP 全为 0；retry、人工审批和 Production 仍为 0。Q4 fresh Conversation 零 dispatch
Clarification 继续通过；Q1 以零 Citation 的混合事实/边界 Limitation 被错误交付，Q2 补证 action 后丢失完整 Review correction baseline 并在下一
focused Review 前耗尽 authority，Q3 的 cognition-literal repair 原样重复非法 query，Q5 按 post-dispatch unknown no-retry 失败。
`FINDING-010-214` 已形成 current `@19/@11/@14` 补证后全 Findings 保留、Limitation 零 SUPPORT、material cognition-literal replan 与
resolved-candidate final-preflight 冗余 candidate；fresh run-092 仍须证明真实 Answer/Review，run-091 保持质量 FAIL。
run-092 的 Ark 53 个 call 全部完成，TLS/credential/HTTP 均为 `53/53/53`；不存在 raw failure 或 trusted pre-dispatch unavailable verdict，
故 DeepSeek 全链路 0 是 preferred route 持续可用时的正确结果。Q3 以 1 个 exact Source Citation 和 fresh Review/Delivery 成功，Q4 fresh
Conversation 零 dispatch Clarification 继续通过；Q1/Q2/Q5 分别耗尽 dispatch 或 Review authority。三题共同 first divergence 是
Reviewer 在明确“Draft 未披露、也未绑定 resolved Search diagnostic”时仍可返回 audit-only disposition 并制造无可删除对象的 global Finding；
replacement Draft 后同一 Finding 重现。`FINDING-010-215` 已形成 current `@20/@12/@15` exact
`draft_disclosed_fragments[]`、reference/fragment/disposition 三向闭合与 no-op audit-only rejection candidate；73 项 Agent/Tool/Model 测试
PASS，相邻定向集与 fresh run-093 仍须证明真实 Answer/Review，run-092 保持质量 FAIL。
run-093 随后以 Ark 3 个 sealed 429 合法自动激活 DeepSeek 并完成 28 个 fallback dispatch，证明备用路线与 standing authority 正常；Q1
暴露 exact fragment 的 inline-code backtick presentation mismatch，Q2/Q5 暴露 original-question module scope 未进入 Source Search且多个
query 重扫 canonical fallback 前缀。`FINDING-010-216/217` 已形成 current `@21/@13/@16` backtick-only normalization 与
`COMPILED_SOURCE_OPERATION@3` Broker-recomputed prefix/rotating fallback contract；六模块 154 项、相邻十五模块 229 项定向测试 PASS，fresh run-094 仍须证明真实
Answer/Review，run-093 保持质量 FAIL。
run-094 随后以 Ark 4 个 sealed 429 合法自动激活 DeepSeek；DeepSeek 20 个 call 完成、1 个 post-dispatch unknown，retry、人工审批与
Production 均为 0。Q1 以 2 个 exact Citation 取得 ACCEPTED，证明 backtick fragment closure 真实通过；Q4 零 dispatch Clarification 继续
通过。Q5 的合法 `SOURCE_SEARCH(SOURCE, ElasticsearchRepository)` 暴露 question module prefix 初版把同 module POM/TEST paths 混入
SOURCE restriction，Broker 按 class 正确失败关闭。`FINDING-010-218` 已把 scope 识别保留在完整 Request allowlist，同时只从 current
evidence-class allowlist 选择 prefix；wire schema、route、rotation 与全部 fuse 不变。六模块 154 项、相邻十五模块 229 项定向测试 PASS，fresh run-095 待验证；
Q2 的 post-dispatch unknown 与 Q3 limitation 不被追认为 product quality PASS。
run-095 随后再次以 Ark 4 个 sealed 429 合法自动激活 DeepSeek；DeepSeek 27 个 call 完成、1 个 post-dispatch unknown，Q1/Q5
ACCEPTED、Q4 零 dispatch Clarification，证明 evidence-class-only prefix closure 已真实通过。Q2 在 Q1 后闲置约 141 秒时复用已失效的
DeepSeek keep-alive 并按 no-retry 失败；Q3 的 focused Reviewer 把全部 disclosed Boundary 判为 material/null code，却又返回额外
Finding，generic repair 原样重复后失败。`FINDING-010-219/220` 分别形成 credential/HTTP 前的 stale-or-60-second-idle session rotation，
以及 retained Finding 绑定 exact challenge 或删除 unbound Finding 并 APPROVE 的专用 repair closure。相邻十七模块 255 项定向测试 PASS；
DeepSeek Adapter exact bytes 已恢复并由 current Conformance loader 重新核验通过；Engineering Chat runtime transport ref `@3` 与 run-096
仍须证明真实 stale/idle rotation、Answer/Review，run-095 保持质量 FAIL。

run-104 在 current standing scope 内由 Ark 两个 sealed 429 触发 DeepSeek fallback：Q1 的 DeepSeek 14/14 calls 完成并由 exact 15-call
logical Turn fuse 失败关闭；Q2 首个 DeepSeek dispatch 返回 sealed HTTP 402，Q4 fresh Conversation 仍以零 dispatch Clarification 通过，
同签名停止边界因此未发送 Q3/Q5。Q1 的最早偏差是 comprehensive Review 把阶段性脱敏的空 Boundary arrays 当成真实 absence，在
add/delete binding、Claim 与 SUPPORT 要求之间振荡。`FINDING-010-233` 已形成 current `@30/@20/@24` presence-only count projection：
保留可信 Boundary 存在性但不披露 exact value、不转移 focused ownership；模型协议 `37/37`、相邻定向测试 `137/137` PASS。DeepSeek 402 只作 Provider availability evidence，不作代码
quality verdict；run-104 保持 Quality FAIL。

旧
`ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3` 继续是兼容协议，不能作为本契约主 Agent 或 Chat 资格证据。
