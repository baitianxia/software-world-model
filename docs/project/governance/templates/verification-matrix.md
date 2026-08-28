---
id: ITER-NNN-VERIFICATION
kind: iteration-verification
status: not-run
authority: planned-verification
owners: [quality]
depends_on: [ITER-NNN-PROPOSAL]
code: []
tests: []
iteration: ITER-NNN
product_goal_gate: V-000
product_goal_outcome: user-visible-general-source-qa-delta
product_goal_evaluation: independent-hidden-plus-live-ad-hoc
product_goal_result_id: pending
plan_revision_ref: ITER-NNN-PDR-NNN
current_action_ref: ITER-NNN-ACTION-COMPLETE-EXPERIENCE-NNN
current_action_case_id: V-MVP-EXPERIENCE-NNN
---

# Iteration NNN Verification Matrix

| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |
|---|---|---|---|---|---|---|
| V-000 | 本轮相对 baseline 可测缩短通用源码问答 MVP 差距，并在答案质量上严格超过 current Codex | product / comparison | 未参与实现的真实工程；独立持有的 held-out 和现场问题；exact current Codex identity/protocol；双方密封答案；随机匿名映射；独立盲评量表 | 系统绝对质量 PASS；逐题无物质退步；总体答案质量差值严格为正；全体打平 FAIL；次级效率指标不得补偿；同一正式 Web 可人工验证 | pending | not-run / blocking |
| V-PUBLIC-SOURCE-AUTHORITY-NNN | standing authority 范围内无需逐 run/逐题人工授权，同时每次外部分派有 exact receipt | security / authority | human standing authority；公开性/许可证；revision policy；exact clean revision；只读 allowlist；route/预算/调度/有效期/loopback scope；scope-delta 负测 | 范围内直接执行且每次在 Source disclosure/network/credential 前生成 one-use receipt；receipt 不扩权；scope mismatch 失败关闭；只有真实 delta 申请最小授权 | pending | not-run / prerequisite |
| V-CHAT-EXPERIENCE-NNN | 第一条完整浏览器主链可操作即交付 | product / first operable browser delivery | exact version；重复启动命令；固定 loopback 地址；目标工程/revision；代表性语义 Conversation；新对话隔离和故障输入 | 用户可持续操作完整世界模型—Agent—源码—Evidence/Citation—独立审核—Web 主链；版本/限制可见；单题失败不关闭服务；第一次达成立即交付；`requires_result=false`、不移动游标、不等待 Codex 比较 | pending | not-run / blocks first-delivery claim, not ongoing development or cursor |
| V-MVP-EXPERIENCE-NNN | 同一已交付候选完成严格方向证据并形成最终 handoff | product / final result handoff | `V-CHAT-EXPERIENCE-NNN` 同一候选；至少 3 个异质问题、至少 2 个 unseen；actual current Codex fresh 隔离答案；独立 source evidence/evaluator；或一次通用修复仍失败的完整证据 | 比较完成并如实报告绝对质量、逐题差异、总体结论与非 locator 贡献；或证明一次通用修复后同类重大失败仍存在；`requires_result=true`，密封一次 Result 并移动到 `V-PREVIEW-NNN` | pending | not-run / blocks final direction handoff, not first delivery |
| V-CHAT-NNN | 同一 Conversation 支持语义追问、纠正、总结和新对话隔离 | product / conversation | 至少三轮语义链及新对话负测；逐轮 evidence/review trace | 目标与已确认上下文守恒；纠正替换旧解释；总结基于当前上下文；新对话不泄漏旧指代 | pending | not-run / part of V-MVP-EXPERIENCE-NNN |
| V-FAILURE-TRUTH-NNN | 产品失败如实、隔离且不以降质答案冒充成功 | product / reliability | Provider/source/review/引用失败；未知边界；下一次正常输入 | 当前 Turn 失败关闭；服务和 Conversation 可继续；没有伪造引用、静默跳过 Reviewer 或错误网络分类 | pending | not-run / part of V-MVP-EXPERIENCE-NNN |
| V-DIRECTION-QUALITY-NNN | 完整体验后，同一候选在异质问题上达到严格质量下限 | product / post-experience comparison | 至少 3 个异质真实问题，其中至少 2 个 unseen；system 与 actual current Codex fresh 隔离密封答案；独立 exact-source evidence；独立 evaluator | 系统绝对质量 PASS；逐题无物质落后；总体质量严格超过 current Codex；至少一项非 locator 世界模型贡献；平局、重大错误或 unresolved 均 FAIL | pending | not-run / blocks direction PASS and hardening, not first handoff |
| V-ROOT-CAUSE-NNN | 答案失败按最早偏差归因后只做通用修复 | engineering / diagnosis | failure trace；可证伪假设；最小复现；至少两个未参与修复的相邻案例；一个有界 live canary | 修改发生在假设之后；没有单题特判；相邻案例通过；同签名一次修复仍复现时进入架构职责评审 | pending | not-run / blocks quality PASS, not ongoing development |
| V-PREVIEW-NNN | 用户基于完整体验和严格比较决定方向 | product / user decision | `V-MVP-EXPERIENCE-NNN` 最终 Result；`V-DIRECTION-QUALITY-NNN` 结论或一次通用修复仍失败证据；限制可见 | 用户给出 `CONTINUE / REWORK / REDIRECT / REJECT`；receipt 只记录方向且 action 自环；`CONTINUE` 后仍需新 PDR、明确用户授权与可信父 cutover 才能解锁 hardening、full regression、hidden、跨工程和四路因果消融 | pending | not-run / blocks next plan revision |
| V-FOUR-ARM-NNN | `CONTINUE` 后隔离世界模型认知的因果贡献 | product / causal ablation | direct evidence；同 Agent 仅源码；同 Agent 世界模型认知+源码；current Codex；同题、exact identities、密封答案、独立 source truth/evaluator | 世界模型臂绝对质量 PASS，逐题无物质退步，总体正 margin，且有非 locator 贡献；Codex 与 direct evidence 都不是 Oracle | pending | locked until CONTINUE plus new PDR, explicit authorization and trusted-parent cutover |
| V-HARDEN-NNN | `CONTINUE` 后完成 full regression、hidden、跨工程和工程夯实 | product / acceptance preparation | accepted experience candidate；user CONTINUE receipt；held-out/cross-project suite；full suite | 契约、安全、兼容、性能、hidden、跨工程和 full regression 达到正式验收标准 | pending | locked until CONTINUE plus new PDR, explicit authorization and trusted-parent cutover |
| V-REFLECT-NNN | 根据体验、比较和 Finding 作出架构复盘 | architecture / reflection | complete experience Result；quality report；root-cause findings；user decision | 关键假设逐项 disposition；系统文档同步；没有用单题成功替代方向证据 | pending | not-run / blocking acceptance |
| V-001 | <claim> | unit / contract / product | <exact identity> | <result> | pending | not-run / blocking |

`blocking` 阻止对应声明或阶段晋级，不自动停止长运行开发动作。首次完整体验前只执行 targeted impact、startup、safety 和 failure-truthfulness；不得因 strict comparison、full regression、hidden 或 hardening 尚未执行而推迟 `V-CHAT-EXPERIENCE-NNN` 的无 Result 即时交付。

`V-DIRECTION-QUALITY-NNN` 在首次交接之后执行，并使用同一候选。current Codex 是强外部基线，不是 Oracle 或裁判；事实来自 exact source evidence。比较 FAIL 时保持当前 Slice，先用 `V-ROOT-CAUSE-NNN` 定位最早偏差并做一次通用修复。

用户 `CONTINUE` 之前，`V-FOUR-ARM-NNN` 和 `V-HARDEN-NNN` 必须保持 locked/not-run。不得把它们倒置为第一次完整浏览器体验的前置条件。

每个 active Matrix 必须让 Manifest 的唯一 current action Case 解析为一行。首次可操作浏览器交付不生成 Result、不迁移游标；Result 只用于最终方向 handoff 或证明一次通用修复仍失败后的游标迁移，并绑定 exact evidence bytes 与预先冻结的最小 runner。普通提交、失败、测试或 Provider dispatch 不生成 Result。方向 receipt 只记录决定；`CONTINUE` 的真正解锁需要新 PDR、明确用户授权和可信父 cutover，本地消息 digest 不是平台认证授权。standing authority 不能替代每次 runtime receipt，receipt 也不能替代真实 scope-delta 人工授权。
