---
id: PROJECT-CURRENT
kind: project-current
status: current
authority: current-development
owners: [project]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, PROJECT-GOVERNANCE-DEVELOPMENT-DESIGN, PROJECT-GOVERNANCE-PLAN-EXECUTION, ROADMAP-M-002, ITER-010-INDEX, ITER-010-SLICE-001, ITER-010-RESULT-V-MVP-EXPERIENCE-001, ITER-010-RESULT-V-USER-DIRECTION-DECISION-001, FINDING-010-161, FINDING-010-163, FINDING-010-165, FINDING-010-178, FINDING-010-179, FINDING-010-180, ITER-010-PDR-010, ITER-010-PDR-011, ITER-010-PDR-012, SYS-ADR-017, SYS-ADR-018, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, ITER-011-INDEX]
code: []
tests: []
as_of: 2026-08-29
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

使用已有 run-052/053 trace 和当前代码确定最早可证实的产品偏差，完成一条非 POM/Maven 问题的真实三轮浏览器 Conversation。世界模型
必须产生可观察的非 locator 认知贡献；认知不足时主 Agent 必须按 Gap 只读源码；最终页面必须显示自然答案、Citation 和本轮 fresh Review。

该链一旦可操作，立即启动在 http://127.0.0.1:8765/ 作为“开发体验候选”交给用户，requires_result=false；它不等待 current Codex
比较，但也不得称为 MVP、质量 PASS、方向 PASS 或完成。交付开发体验候选后不暂停、不等待新的用户决定，立即在同一候选上用至少两个
未参与修复的异质问题和 current Codex 强基线完成质量资格判断。只有系统自身重大错误为 0、逐题相对 Codex 无物质退步、总体严格更优，
且至少一项重要价值来自非 locator 世界模型认知时，才能称为 MVP 并交给用户判向。失败继续同一开发闭环，不新建迭代、PDR、失败 Result
或授权请求。全量回归、跨工程、hidden 和工程夯实仍不得成为 MVP 前置。

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
