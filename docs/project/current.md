---
id: PROJECT-CURRENT
kind: project-current
status: current
authority: current-development
owners: [project]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, PROJECT-GOVERNANCE-DEVELOPMENT-DESIGN, PROJECT-GOVERNANCE-PLAN-EXECUTION, ROADMAP-M-002, ITER-010-INDEX, ITER-010-SLICE-001, ITER-010-RESULT-V-MVP-EXPERIENCE-001, ITER-010-RESULT-V-USER-DIRECTION-DECISION-001, FINDING-010-161, FINDING-010-163, FINDING-010-165, FINDING-010-178, FINDING-010-179, FINDING-010-180, FINDING-010-181, FINDING-010-182, FINDING-010-183, FINDING-010-184, FINDING-010-185, FINDING-010-186, FINDING-010-187, FINDING-010-188, FINDING-010-189, FINDING-010-190, FINDING-010-191, FINDING-010-192, ITER-010-PDR-010, ITER-010-PDR-011, ITER-010-PDR-012, SYS-ADR-017, SYS-ADR-018, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, ITER-011-INDEX]
code: []
tests: []
as_of: 2026-08-30
active_iteration: ITER-010-INDEX
active_slice: ITER-010-SLICE-001
worktree_status: iteration-010-slice-001-product-first-browser-chat-build
strategy_relation: dual-core-world-model-cognition-and-conversational-lead-engineering-agent
live_model_path: preferred-execution-profile-first-fallback-only-on-trusted-unavailability
plan_revision_ref: ITER-010-PDR-012
next_action: ITER-010-ACTION-USER-DIRECTION-DECISION-001
next_action_case_id: V-BROWSER-CHAT-MVP-BUILD-001
---

# 当前工作上下文

## 当前结果

ITER-010 / SLICE-001 已恢复为持续产品开发。当前唯一目标不是继续建设治理设施，也不是把“页面能运行”冒充 MVP，而是尽快交付答案质量
合格、普通用户可直接使用的无认证浏览器 Chat MVP：

- 软件世界模型提供 exact revision 上真实、版本化的软件认知，不能以 Maven 模块/依赖或 locator 列表冒充；
- 主工程 Agent 以认知为起点，根据 Coverage/Gap 受控读取源码、文档、配置或测试，并根据观察重规划；
- 每个 Turn 形成自然答案、可打开 Citation 和 fresh independent Review；
- 同一 Conversation 支持追问、纠正、深入或总结，新 Conversation 隔离；
- 不包含工程、问题、关键词、符号、类、方法、fixture 或 Oracle 特判。

## 持续授权与工作计划

当前公开 mall exact revision、只读 Source、既有执行配置、披露、预算和 loopback evaluation 仍在 active standing authority 内。它是产品
编码和范围内外调的权限来源；新的问题、Turn、运行或同范围工作计划调整不重复申请授权。只有私有/新 Source、新接收方或账户、扩大
披露/预算、外部写入、非 loopback、Production 或破坏性操作才属于 scope delta。

Manifest current action 只是工作计划和可信路径的兼容镜像，不得因答案、格式或测试失败撤销上述授权。普通失败留在同一开发动作：先定位
Source → 世界模型构建/查询 → Agent → Evidence/Answer → Review → Web 的最早偏差，再做通用修复和异质复验。

## 唯一下一开发动作

run-075 已以 fresh clean product 复验 run-074 的 Maven/启动链失败题并形成 `SUCCEEDED / ACCEPTED`，也完成订单创建、同 Conversation
库存失败追问和新 Conversation 省略指代隔离 probe。它延续已交付的 `requires_result=false`“开发体验候选”，仍不是 MVP、质量 PASS、方向
PASS 或完成；其中库存追问存在标题分类错误且 fresh Reviewer 漏判，角色重分配题又在 Source budget/reference contract 矛盾处失败。

当前仍在同一个 `ITER-010-ACTION-BROWSER-CHAT-MVP-BUILD-001` 内继续质量资格：以 `FINDING-010-185/186/188/189/191/192` 的 clean successor 复验角色重分配题、
容器语义审核、空上下文复数指代、失败分层显示和未参与修复的异质题，再与 actual current Codex 强基线判断绝对和相对质量。只有系统自身重大错误为 0、逐题
相对 Codex 无物质退步、总体严格更优，且至少一项重要价值来自非 locator 世界模型认知时，才能称为 MVP 并交给用户判向。失败继续同一
开发闭环，不新建迭代、PDR、失败 Result 或授权请求。全量回归、跨工程、hidden 和工程夯实仍不得成为 MVP 前置。

Manifest 中含 `MVP` 的既有动作/Case 技术 ID 仅为可信父兼容标识，不构成 MVP 资格或完成声明；MVP 资格只由上述绝对质量与同题 Codex
比较共同决定。

当前状态：AUTHORIZED / REWORK / PDR-012 / PRODUCT DEVELOPMENT ACTIVE / LOOPBACK EVALUATION / NON-PRODUCTION。

当前 live checkpoint：`FINDING-010-178` 已确认 run-068 的前两步按修复后的 `World Model → exact Source target` 执行；其后
run-068/069 遇到 raw Ark HTTP error，run-070 又遇到 Ark pre-HTTP unavailable。run-070 的 DeepSeek `DENIED_PRICING_CHECK` 直接来自
超过 900 秒 freshness 上限的旧 pricing check，不是周末窗口拒绝。

`FINDING-010-179` 已纠正执行准备结论与 fallback 闲时日历：`Asia/Shanghai` 周六、周日全天属于闲时，工作日继续使用三个既有时段；
相邻闲时连续计算，因此周五 `18:00` 至周一 `09:00` 不会因午夜换日被误阻断。当前不再处于“只能等待外部环境”的 hold；下一 fresh run
使用 policy `ITER-010-PDR-007@2` 和 900 秒内的官方 pricing check，Ark 成功时继续 primary，Ark 产生可信 unavailable verdict 时可直接进入
既有 DeepSeek fallback。standing authority、计划游标和 Production 边界均不改变。

`FINDING-010-180` 已封存 run-071 的新最早偏差：首步 World Model 已给出 `UmsAdminServiceImpl` 等 exact declaring type/source path，Primary
仍以宽泛 `login` 首搜 56 个文件，并在后续 search/read 后耗尽 `64/64` Source file fuse；真正的 service target 因而没有执行。第 14 个 Ark
dispatch 最终以 post-dispatch `REMOTE_DISCONNECTED / PROVIDER_OUTCOME_UNKNOWN` 关闭，DeepSeek 0，页面如实失败。current local candidate 升为
`conversational-engineering-agent@8 / ENGINEERING_AGENT_PRIMARY_INPUT@8`：non-empty、non-truncated cognition target projection 将第一次
Source search 约束到 exact declaring-type literal；定向 Tool/Model suite `38/38` PASS。fresh Browser successor 仍待新 identity 验证，不能把
该本地候选或 run-071 追认为开发体验、质量或 MVP PASS。

`FINDING-010-181` 又封存 run-072 的 successor 证据：exact `UmsAdminServiceImpl` 首搜已生效，但 Search 为声明全 Evidence Class 覆盖仍读取
56 个文件；service read 1、`UmsAdminController` Search 6、controller read 1 后精确耗尽 `64/64`。剩余 action budget 仍为 3，但 Source
catalog 已撤销，`AdminUserDetails` repair 因而被拒；页面如实 `AGENT_MODEL_CALL_REJECTED`。Ark 7 次 TLS/HTTP 全成功，DeepSeek 0，故无
fallback 正确。current local candidate 现以 `COMPILED_SOURCE_OPERATION@2` 把同一 cognition projection 的 canonical paths 密封为
Broker-validated Search-only scope；无模型 path/READ authority、无 fuse 提高，受影响四模块 `102/102` PASS。fresh Browser successor 仍待新
product/run identity，run-072 不取得开发体验、质量或 MVP PASS。

`FINDING-010-182/183` 已封存 run-073 的两个独立根因。Search-only scope 真实把第一次
`SOURCE_SEARCH(UmsAdminServiceImpl)` 收窄到 1 个文件，但后续普通 `JwtTokenUtil` Search 达到单次 56-file scan 上限时仍误报
`SOURCE_FILE_FUSE_EXHAUSTED`；整轮实际只用 `59/64` 且 catalog 仍有两个 Source operation，Agent 因而提前放弃
`UmsAdminController` HTTP 入口证据。随后同一 Package 的修订稿已获第二次 fresh Reviewer `APPROVED`，Response Control 又因错误要求
successor Work State 等于 Package 首次封装状态而拒绝 Delivery，页面如实 `AGENT_PROTOCOL_VIOLATION`。Ark 10 次 TLS/HTTP 全成功、
DeepSeek 0、retry 0、Production 未执行。current local candidate 已分离 Search operation-local 与 whole-Turn codes，并保持 immutable
Package origin 跨同包 rewrite；相关八模块 `225 tests / 3 skipped / 0 failure`。fresh Browser successor 仍待新 product/run identity，
run-073 不取得开发体验、质量或 MVP PASS。

`FINDING-010-184 / run-074` 已把上述 local candidate 贯通为真实三轮开发体验：登录 Conversation 三个 Turn 以 Ark `14/9/4` 次 dispatch
全部 `SUCCEEDED / ACCEPTED`，独立分类删除题又以 Ark 7 次成功；该三轮页面已经作为非 MVP 开发体验候选交付。第五个 Maven/启动链题在
Ark 5 次后因 `SOURCE_SEARCH.arguments` 的单个 malformed item 必须重建为两个 sealed-template item、却被旧 array-length copy obligation
拒绝而失败；同一 repair 还把既存 `—` 释义为 `-`。run-074 总计 Ark dispatch/TLS/credential/HTTP `39/39/39/39`，DeepSeek 0、retry 0、
unknown 0、Production 未执行，故不是 Ark 不可用。current local candidate 以 `ENGINEERING_AGENT_OUTPUT_PREFLIGHT@5` 仅允许完全没有既存
allowlisted item value 的 invalid array 子树重建，并在 Proposal decode 前恢复其余 prior exact value；受影响组合 `141/141` PASS。fresh
clean successor 仍须复验失败题并完成 current Codex 质量比较，不能把首个可操作链或本地修复称为 MVP。

`FINDING-010-185/186 / run-075` 已给出新的最早偏差。Maven/启动链旧失败题以 Ark 8 次成功，证明 `@5` repair 已通过真实 successor；订单
创建题也成功，同 Conversation 的库存失败追问与新 Conversation 省略指代 probe 分别完成语义追问和零 dispatch Clarification，故
`V-CHAT-001` 的显式隔离定义已有真实证据。库存追问却把 `cancelOrderSender.sendMessage` 放在“数据库写入一定尚未发生”的标题下，Claim
只枚举调用顺序，fresh Reviewer 对 10 个窄 Claim 全部 `SUPPORTED`，所以质量仍 FAIL。角色重分配题在 latest Source receipt `64/64` 时
effective catalog 已撤销 Source operation，`source_read_options` 却保留 controller locator，same-profile repair 提议 dangling READ 后被拒。
run-075 总计 Ark dispatch/TLS/credential/HTTP `31/31/31/31`，DeepSeek 0、retry/unknown 0、Production 未执行，明确不是 Ark 不可用。
current local candidate 现投影 `ENGINEERING_AGENT_SOURCE_FILE_BUDGET@1` 并让 budget/options/catalog 同步，同时要求 Claim/Reviewer 审核
heading/table/list 继承的 category、scope、condition、certainty、negation；无 AF_UNIX 依赖的受影响组合 `127/127` PASS。扩展 141 项 raw
为 135 PASS + 1 FAIL + 5 ERROR，六项均是 sandbox 禁止本机 socket 的环境噪声；fresh successor 仍待执行。

`FINDING-010-187/188/189 / run-076` 随后证明角色重分配题已越过旧 Source contradiction：前 9 个 Ark call 完成真实
World Model、Source Search/Read 和 Answer Draft，Application 又正确拒绝把 BOUNDARY observation 当作 Claim support。其 repair 与后四个
冻结 Turn 的首个 call 连续得到 raw `PROVIDER_HTTP_ERROR`；没有 availability owner 的受信 unavailable verdict，因此 DeepSeek 虽通过
周末 `ALLOWED_OFF_PEAK` admission 仍保持 0 dispatch，行为正确。五个 Turn 均未交付，不能验证答案/Reviewer 质量。新 Conversation 的
“这些失败也会回滚吗？”还暴露复数指代 marker 缺口，页面又只显示 stage `AGENT_MODEL_CALL_REJECTED` 而未展示已保留的 raw Provider
字段。current candidate 已通用补齐单数/复数/类别指示 Clarification，并让 Browser 分层显示 execution 与 raw Provider evidence；定向
Conversation/Browser `20/20` PASS、外调 0。fresh successor 仍是唯一产品验证，run-076 不取得 MVP 或质量 PASS。

`FINDING-010-190 / run-077` 已真实验证上述两个 UI/Application 修复：角色重分配题的首个 Ark call 再次 raw
`PROVIDER_HTTP_ERROR`，页面同时显示 execution-stage 与 raw Provider 两层；新 EMPTY CONTEXT 的原句“这些失败也会回滚吗？”则以
`APPLICATION_INPUT_CLARIFICATION`、Provider dispatch 0 成功。run-076/077 已连续形成 6 次相同 raw signature 且没有 trusted
unavailable verdict，故不再提交剩余外部题；DeepSeek 的周末 `ALLOWED_OFF_PEAK` 只证明 admission 可用，不授予 fallback authority。
run-077 密封 2 Conversation、2 Turn、Ark 1、DeepSeek 0、retry 0、Production 0 并优雅停止。当前继续本地质量归因与证据闭合；只有
materially new availability evidence 或新的 product divergence 才启动下一外调，不能把等待或重复 HTTP 失败冒充开发进展。

`FINDING-010-191` 已利用 run-076 尚未交付的 Draft 继续完成本地质量归因：Primary 把 Cognition coverage gap 误称为授权边界，并在只读
producer-side 角色更新实现时断言 consumer-side 登录态权限刷新。current contract/prompt 现要求 Primary 与 Reviewer 分开 authority、
coverage、tool、runtime state，以及 producer invocation、callee effect、consumer-visible lifecycle；模型边界直接 `28/28`、相邻
Application/Conversation/Browser/Candidate/Session 组合 `77/77` PASS、外调 0。
该修复仍须 fresh Browser 的异质工程题验证，不能把本地 Prompt/policy 测试称为答案质量 PASS。

`FINDING-010-192` 又把 first divergence 前移到 World Model evidence-tool adapter：global Coverage/Gap 已进入 BOUNDARY，却同时被复制进
model-facing SUPPORT 顶层。当前 SUPPORT 只投影 novel affirmative item 与 per-item coverage；global coverage/conflict/unknown 只进入
BOUNDARY，正式 Context/Ledger/receipt 仍完整绑定。相邻七模块 `91/91` PASS、外调 0；该通用投影修复仍待 fresh Browser 质量复验。
