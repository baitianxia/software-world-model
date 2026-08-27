# 治理模板

复制最小模板并替换占位符，不要预建没有消费者的空文档：

- `iteration-proposal.md`
- `iteration-index.md`
- `manifest.yaml`
- `development-design-index.md`
- `development-slice.md`
- `findings-index.md`
- `verification-matrix.md`
- `readiness-review.md`
- `implementation-finding.md`
- `system-adr.md`
- `project-decision.md`
- `iteration-result.md`
- `results-index.md`
- `iteration-acceptance.md`

模板不属于当前权威索引，也不作为示例内容的事实来源。替换所有 `NNN`、`<...>` 和 `pending` 后再运行文档检查；不得复制上一轮的 Commit、模型、Digest、测试数字或有效期。

## 最小落位

| 目标位置 | 模板 |
|---|---|
| `iterations/iteration-NNN/README.md` | `iteration-index.md` |
| `iterations/iteration-NNN/proposal.md` | `iteration-proposal.md` |
| `iterations/iteration-NNN/manifest.yaml` | `manifest.yaml` |
| `iterations/iteration-NNN/verification-matrix.md` | `verification-matrix.md` |
| `iterations/iteration-NNN/readiness-review.md` | `readiness-review.md` |
| `iterations/iteration-NNN/development-design/README.md` | `development-design-index.md` |
| `iterations/iteration-NNN/development-design/SLICE-NNN-*.md` | `development-slice.md` |
| `iterations/iteration-NNN/findings/README.md` | `findings-index.md` |
| `iterations/iteration-NNN/findings/FINDING-NNN-*.md` | `implementation-finding.md` |
| `iterations/iteration-NNN/results/README.md` | `results-index.md` |
| `iterations/iteration-NNN/results/<type>.md` | `iteration-result.md` |
| `iterations/iteration-NNN/results/acceptance.md` | `iteration-acceptance.md` |

先以 `proposed` 状态完成 Proposal、Manifest、Slice、Verification 与 Readiness。得到用户明确授权后，把 Proposal 与 Readiness
改为 `accepted` 并填写授权字段，把 Iteration Index、Manifest 和当前 Slice 改为 `authorized`，将 Index/Slice 的 `coding_input` 改为
`true`，最后原子更新 `project/current.md` 的 Iteration/Slice 指针以及 `plan_revision_ref`、唯一 action/Case 镜像和 `depends_on`。在这之前
不得把模板存在本身解释为授权。

每个新 Iteration 还必须完整填写模板中的 `Product-goal alignment`：绑定 `SYS-PRODUCT-SUCCESS`，说明相对通用源码问答 MVP
的 baseline gap、与既有能力的累积组合、由独立评测方或用户持有且实现阶段不可见的 held-out 自由问题增量、跨域问题、
最早可证伪价值 Gate、该 Gate PASS 后的最早正式 Web 体验点、验收现场临时问题和停止条件。任何一项仍为占位符时不得通过
Readiness；孤立 Profile/View/组件的
完成不能替代该门禁。

每轮还必须绑定 Roadmap 中从最终目标反推的能力步骤，列出前置接受/失败证据、本轮通过后用户在正式 Web 上能新做什么，
以及下一个最早阻断差距。不得用“新组件已完成”、“为后续打基础”或没有 Web 用户能力变化的风险下降替代这四个字段。

从 ITER-008 起，每轮还必须冻结关键方案假设、最早反证和备选路线；Manifest、Readiness 与 Result 用同一个 Proposal 假设表摘要
锁定原文，不能在看到结果后改写。每个 Slice 恰好绑定一个 `V-REFLECT-NNN`。Slice 的固定顺序是最早可证伪价值 Gate、该 Gate
绑定的 exact Result、Gate PASS 后的正式 Web/本阶段适用验证、方案复盘和 `CONTINUE / ACCEPT / REWORK / REDIRECT / REJECT`；体验
Alpha 使用可见输入，Alpha `CONTINUE` 后的 hardening 才承担 early hidden。缺少复盘，或中间段决定不是 `CONTINUE` 时，不得授权下一
Slice；机械测试 PASS 不能替代方案判断。

当前及未来产品计划的最早产品动作必须是最早可证伪价值 Gate，而不是 Web、Prompt/Reviewer 调整、Provider canary、hardening 或 full
regression。先以外部调用 0、产品代码 0 的 freeze action 冻结三条异质真实工程问题、四路 runner、独立 exact-source truth ledger、答案
密封与随机匿名、盲化 rubric、实际模型/工具/权限身份和 Result Schema；其 PASS 后才可执行四路严格质量 Gate：

1. 直接相关证据，使用与系统臂相同的生成模型，但不经过世界模型、Agent 或检索协议；
2. 同一主 Agent + 仅源码；
3. 同一主 Agent + 世界模型认知 + 源码，且相对第 2 路只有认知开关不同；
4. current Codex fresh 隔离任务，保留实际 client/model/reasoning/tools/permissions。

直接证据和 Codex 都不是 Oracle 或裁判；事实只来自独立 source-truth ledger，独立 evaluator 不参与答案生成。第 3 路必须先通过绝对
质量门，再逐题不输第 1、2、4 路，总体严格超过 current Codex，并证明至少一项可验证的非 locator 世界模型贡献。全体打平、任一物质
退步、双方失败、无法裁决或盲化失效均为 `FAIL`；成本、时延、调用数、缓存或复用不得补偿质量。严格 Codex 下限对当前及未来计划
立即生效，不得再以 ITER-012、兼容期或 Web Alpha 为理由 deferred。

产品计划仍必须把“Gate PASS 后的可体验 Alpha、工程夯实、正式验收”分开。四路 Gate PASS 后的第一个 Web Slice 才用真实入口和小而
多样的问题与现场输入形成非验收 Alpha；只有 Alpha 的 `CONTINUE` 后才安排全面契约、回归、性能、hidden canary 和正式验收。安全、
权限、Secret 与失败真实性不能延后，但不得把完备证明材料误作方向 Gate 或 Alpha 的前置目标。

首次方向体验必须是真正可持续操作的版本：精确版本可重复启动、固定本地地址、版本和限制可见，且单题失败不关闭服务。一次性验证
运行或只能回答启动前冻结问题的页面不算体验版本。连续提交独立问题只证明持续 Q&A；若声明 Chat，Manifest 必须使用
`ENGINEERING_CHAT_EXPERIENCE@1` 和 `CONVERSATIONAL_ENGINEERING_AGENT@1`，冻结追问、纠正、总结、逐轮证据/审核及新对话隔离，
并用至少五轮语义链验证。阻断失败默认记录为 `REWORK`，只阻止 PASS、晋级和 hardening；现有本地开发授权覆盖通用修复时保持当前
Slice active。同一目标和总体架构下继续同一 Slice；只有 scope/Owner 变化、用户明确暂停或本地授权失效时才暂停并申请恢复。只有明确
用户转向、核心架构证伪或达到预提交无进展上限才允许 `REDIRECT`。

若本轮采用模板中的 `EXPERIENCE_FIRST_DELIVERY@1`，它只约束四路 Gate PASS 后的 Web 交付：从该 Web action 获授权后的第一次产品代码
变更起，60 分钟页面可启动、180 分钟用户可连续操作，240 分钟仍未达到即停止扩张、hardening、full regression 和无新证据的外部重跑
并缩围复盘，但继续本地根因归因和最小体验纵切。Access PASS 只决定 availability，不替代答案 Quality PASS，也不能越过四路价值 Gate。

所有当前及未来活动产品 Iteration 都必须使用 `schema_version: 2` 和 `DEVELOPMENT_PLAN_EXECUTION_CONTROL@1`。Manifest 必须且只能有一个
`current_action`，完整绑定 plan revision、Slice、Case、Result ID/path、前置、coding/external 权限、允许/禁止路径、六类 locks，以及
`PASS / FAIL / INVALID` 的唯一后继。所有直接后继必须在 base Manifest 的 `next_action_contracts` 中逐字段预注册；候选只能原样提升，
不能自行扩权。迁移不能由手写 Result frontmatter 单独触发：Result 必须使用完整 sealed evidence metadata，并同时绑定预注册路径上的
JSON 收据、原始字节摘要、受保护 runner identity、exact `produced_case_ids` 和机械聚合 Verdict；缺一项或使用 verdict 别名都失败关闭。

当前树用 `python3 scripts/docs.py check` 校验文档闭合；开发前运行 `python3 scripts/plan_gate.py snapshot`，交付和合并前还必须运行
`python3 scripts/plan_gate.py diff --base <trusted-base-ref>`，由 trusted base action 审核 diff 白名单、Result/JSON 收据和单步迁移。候选
Manifest/Result 不能授权自己的 diff；计划修订必须另有 Finding、accepted PDR 和 exact 用户授权引用，不能在同一变更中补造成功证据。

若 policy 是在既有失败 Result 密封后才采用，只能把这些 exact Result ID 写入 `historical_pre_policy_result_refs`。它们继续接受历史完整性
和 paused REWORK 检查，但不追溯补造新字段，也不能满足新的体验 Gate；恢复授权后的 successor Result 不得列入该清单。

授权连续性必须作为每个开发模板的必填规则：Slice 本地开发授权、人类 `PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY@1`、系统派生 exact
Authorized Input Manifest/one-use disclosure/dispatch receipt 与一次性 scope-delta grant 分离。公开开源、来源/许可证可确认、允许的
revision selection policy、每次运行的 exact revision、clean、allowlisted、只读测试工程，在 standing authority 已批准的 Provider/model/endpoint/credential account route、预算、调度、
有效期和 loopback `EVALUATION_ONLY` Sink 内运行时，新的 run、问题或 Turn 不再逐次请求用户授权。每次动作仍在 Source disclosure、
network 和 credential 前派生 exact receipt 并回指 standing authority；receipt 只用于门禁和审计，不能自行授权，缺失或失配必须失败关闭。

只有私有/来源或许可证未知/仅本机存在/dirty 数据、超出 approved upstream/revision selection policy/allowlist、新外部接收方或 route identity、预算增加、
超出 fallback admission policy 的调度范围或需要一次性 override、外部写入、非 loopback 暴露、Production Activation 或其他明确排除项才申请最小 exact delta。pending delta 不重复，批准后
自动继续，等待时继续全部独立安全工作。只有阶段交付、actual delta request 已发出且独立工作穷尽、用户明确停止/转向/拒绝，或不可
绕过的安全禁止才允许结束开发回合；`WAITING_EXACT_GRANT` 必须同时保持
`IN_PROGRESS`。

live attempt 按“同一 sealed version 的一个有界用户交互单元发生任一外部 dispatch”计一次；Chat 按 Turn 分别计数。同 failure signature 最多重试一次，连续两次
没有用户可见增量即停止外部重跑；已开始的问题仍保留完整质量链。Provider route 必须 preferred-first，并由 standing external authority
预授权 preferred/fallback execution profiles、两个角色的 disclosure scope、预算和 admission policy；session/Turn 只生成 exact machine receipt，
不重复请求用户授权。preferred route 因 Provider/模型能力 outcome 没有 authorized answer 时，可透明启动最多一个独立 fallback-route attempt；用户不重提，
fallback 从原交互输入与 exact cognition 重跑全链，Chat 同时携带当前 Turn 的 exact relevant Application-sealed Conversation Context，不复用中间产物，
迟到 preferred-route 结果只隔离审计。所有 planned fallback-route 调用必须经过该 execution profile 引用的 admission plugin；run receipt 与每个新
request 的准入条件/一次性 exact override 重验必须早于 Provider socket/connected descriptor、TLS、credential 和 HTTP；缺失时相关计数为 0。完整最坏质量链必须能在准入范围结束前完成，准入失效后不创建新 request；无法完成独立审核时失败关闭。等待准入不停止 preferred-route-only 或本地开发，成本不得降低答案质量。通用模板不得写死 Provider/model 名称，具体名称只能出现在当次 execution profile 配置和执行收据中。

失败修复必须 root-cause-first：按 Source truth、World Model cognition、conversation/task understanding、Agent work state/plan、tool
observation/evidence、answer、independent review、Web 查找最早偏差；无可证伪假设不得改 Prompt/Schema/Contract。先本地最小复现并通过两个未参与修复的相邻案例，再用一个有界 live
canary；同签名修一次仍复现即评审架构职责。Alpha 前只运行 targeted impact/startup/safety，full regression 只能在 `CONTINUE` 后
hardening 和正式验收前运行。

Manifest 还必须冻结评测工程/版本、held-out suite、baseline Result、四路 protocol/identity/rubric/cache policy 和授权软件来源
范围的 exact digest，以及前后支持题数。最早方向 Gate 的 current Codex 协议和严格答案质量阈值不得 deferred；只有完整 hidden suite 可
使用明确、失败关闭的 deferred/user-held marker，并最迟在拥有正式复验的 hardening 或 final Slice 授权前替换为 exact freeze，不能反向
阻塞早期可见结果。完成时 `V-000` Evidence 必须引用本轮一个带完整 `product_goal_*` 元数据的 PASS Result，不能填写
普通文字、机械测试 Result 或风险实验 Result 代替。

current Codex 是强外部基线，不是 Oracle 或 adjudicator；四路各自 exact identity 均须冻结。第 2/3 路以相同 Agent、Prompt、工具、
预算、cache 和 Reviewer 隔离世界模型的因果贡献，第 1 路提供复杂度控制；不得把这四路拆成互不阻断的 Web 对照与后置消融。

机械 Gate 只能验证这些对象之间的闭合关系。Readiness 仍必须由用户查看 exact 冻结输入和案例后作语义判断；随机 digest、
看似正确的字段名或自报 PASS 不能证明候选真的形成通用源码问答增量。跨域 Case、正式 Web 和现场临时问题之间的关系以
Manifest 的结构化 binding 为准，不从正文是否碰巧出现某个 ID 推断。
