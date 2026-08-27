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
---

# Iteration NNN Verification Matrix

| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |
|---|---|---|---|---|---|---|
| V-000 | 本轮相对 baseline 可测缩短通用源码问答 MVP 差距，并在答案质量上严格超过 current Codex | product / comparison | 未参与实现的真实工程；独立持有的 held-out 和现场问题；exact current Codex identity/protocol；双方密封答案；随机匿名映射；独立盲评量表 | 系统绝对质量 PASS；逐题无物质退步；总体答案质量差值严格为正；全体打平 FAIL；次级效率指标不得补偿；同一正式 Web 可人工验证 | pending | not-run / blocking |
| V-ALPHA-ACCESS-001 | 答案质量闭合前先交付真实可操作产品入口 | product / first user handoff | 固定启动命令、loopback 页面、请求通路、版本/限制、Provider/失败状态；声明 Chat 时包含消息历史和新对话 | 页面立即交付用户；Provider 未配置、未资格或失败如实显示而不阻塞页面；Access PASS 不产生 Chat/Quality/Comparison PASS | pending | not-run / blocking |
| V-TIMEBOX-001 | 首个持续 Web Alpha 遵守微检查点、root-cause-first、授权连续性和轻量 live-attempt 停止规则 | product / delivery | 从 Slice 授权后的第一次产品代码变更计时；exact commit、本轮冻结的用户交付出口、外部 dispatch、failure-signature ledger、earliest-divergence hypothesis、本地复现与相邻案例、active/pending grant identity、exact approval request receipt、等待期间本地工作 | 60 分钟页面、180 分钟持续 Alpha；240 分钟无 Alpha 时停止扩域、hardening、full regression 和无新证据的外部重跑，但继续最小体验恢复；active grant 直接复用，权限 gap 在 exact freeze 后直接申请，批准后自动继续；只有 exact request 已发出且独立安全工作穷尽才可等待；每点立即交付，计划/测试/文档不算用户可见增量 | pending | not-run / blocking |
| V-DEEPSEEK-IDLE-001 | 所有 planned DeepSeek dispatch 只在冻结闲时窗口或一次性 exact peak override 下发生 | operations / dispatch admission | `DEEPSEEK_DISPATCH_ADMISSION@1`；trusted injected clock 的窗口边界与 latest-start duration；无/有 exact override；Ark success 与 fallback-ineligible failure；跨窗口 run；official schedule missing/changed；run receipt 和逐 request audit | 允许窗口内且最坏质量链可在窗口结束前完成才准入；其余时间无 exact override 时在 Provider socket/descriptor/TLS/credential/HTTP 前关闭且相关计数为 0；普通 route/canary grant 不能绕过；每个 request 重验时间/override 并回指 receipt；窗口结束后不创建新 request；质量链不裁剪；等待期间 Ark/local 继续 | pending | not-run / blocking |
| V-EXPERIENCE-001 | 首次方向体验是真正可持续操作的版本 | product / browser | <exact-version-single-launch-command-fixed-loopback-address-diverse-visible-cases-and-controlled-failure> | 可重复启动；版本和限制可见；问题真实经过产品链；失败后服务继续接受输入；声明 Chat 时具备消息历史与新对话 | pending | not-run / blocking |
| V-CHAT-001 | 主工程 Agent 在同一 Conversation 完成语义多轮 Chat | product / conversation | 固定工程/revision 的五轮追问、纠正和总结脚本；随后新对话中的无指代问题 | Agent 守恒目标并按观察重规划；追问解析正确；纠正取代旧解释；每轮独立证据/审核；新对话不泄漏旧指代并在歧义时澄清 | pending | not-run / blocking |
| V-COMP-ALPHA-001 | 首个持续 Web Alpha 的答案质量严格超过 current Codex | product / blind comparison | 一条原失败题及另外至少两个相邻或异质问题，后两题中至少一条为产品冻结后现场输入；fresh Codex 先密封；系统不可见；随机匿名 A/B；独立 evaluator 读取 exact evidence | 冻结问题全部完成并分类；系统绝对质量 PASS；每题不低于 Codex；blind-paired answer-quality margin > 0；部分题可打平但全体打平、both-fail、unresolved/invalid 均 FAIL；成本、时延或复用不得补偿 | pending | not-run / blocking |
| V-PREVIEW-001 | 用户在可持续 Alpha 上实际体验并决定是否进入夯实 | product / directional-preview | <V-EXPERIENCE-001-and-V-COMP-ALPHA-001-results-diverse-visible-cases-and-new-live-input> | 独立技术复核和严格 Codex 对照先通过；用户给出 CONTINUE、REWORK、REDIRECT 或 REJECT；非 CONTINUE 时禁止 hardening | pending | not-run / blocks hardening, not acceptance evidence |
| V-XD-001 | `<prior-acceptance-id>` 与 `<current-slice-id>` 在同一问题中组合 | product / integration | <stage-appropriate-exact-cross-domain-case> | <evidence-bound-answer-or-honest-gap> | pending | not-run / blocking |
| V-WEB-001 | `<current-slice-id>` 通过正式 Web 执行 `V-XD-001` | product / browser | <exact-web-subject> | <manual-user-visible-result> | pending | not-run / blocking |
| V-ADHOC-001 | `<current-slice-id>` 通过正式 Web 接受现场临时问题并覆盖 `V-XD-001` | product / browser | <user-owned-live-question-protocol> | <manual-user-visible-result> | pending | not-run / blocking |
| V-REFLECT-001 | `<current-slice-id>` 根据产品证据复盘关键方案假设并作出继续或停止决定 | architecture / reflection | <exact-slice-result-assumptions-findings-and-stage-applicable-baseline-signal-or-comparison> | <complete-review-and-explicit-decision> | pending | not-run / blocking |
| V-001 | <claim> | unit / contract / CC / CE / product / activation | <exact identity> | <result> | pending | not-run / blocking |

`blocking` 只阻止对应 Case 的 PASS 声明、晋级、扩域、hardening 或 exact external action，不自动结束开发目标。活动 Slice 的本地授权仍
覆盖修复时保持 `IN_PROGRESS / coding_input=true`。结束开发回合必须有阶段交付，或已有 actual exact request 且独立安全工作穷尽，或
用户明确停止/转向/拒绝，或不可绕过的安全禁止。

V-000 不能由新增 Profile/View 的封闭题集、测试数量或旧能力回归替代。测试、CC、CE、Product Validation 与 Activation 不得
互相替代。每项 Result 必须绑定 exact subject、运行身份、限制和有效期。完成时每个 Manifest 绑定的 `V-XD`、`V-WEB`、
`V-CANARY`、`V-ADHOC`、`V-REFLECT` 行都必须为 `PASS / blocking`，Evidence 必须精确填写
`<拥有该 Case 的 Slice Result ID>#<case-id>`；最终 Product Result 依赖并聚合全部唯一 Slice Result。只让 V-000 或汇总计数
PASS 不算完成。`V-REFLECT PASS` 只表示复盘完整，不表示方案通过；继续或接受必须由 Result 的独立 decision 字段表达。

`V-COMP-ALPHA` 与首个持续 Web Alpha 属于同一 Slice，不能拆成体验前的新阶段，也不能用后续 hidden Result 回填。current Codex 是强基线
候选，不是 Oracle 或裁判；事实来自同一 exact revision 的授权证据。最终 `V-000` 必须在 held-out 套件重跑严格比较，不能复用 Alpha。

`V-ALPHA-ACCESS` 只证明真实产品入口和请求通路已经交给用户操作；页面 availability 不依赖答案质量 PASS，`V-TIMEBOX` 因此不能等待
完整质量回归后才开始。Provider 资格状态必须真实显示，但不是页面交付前置。Access 也
不能替代 `V-COMP-ALPHA` 或本 Slice 的答案质量 Case；只有质量 PASS 且用户 `CONTINUE` 才可进入 hardening。时间盒和
live-attempt 限制发生在问题之间，已经开始的问题必须保留完整调查、答案、Citation 和独立审核链。
`V-DEEPSEEK-IDLE` 发生在 Provider 外部网络之前，并独立于 Provider 资格和 fallback eligibility；任何 peak-without-override dispatch 都使该
Case `FAIL / blocking`，不能通过补写收据追认。失败只阻断 DeepSeek 外部动作及其依赖 Gate，不结束本地 Slice 开发。
