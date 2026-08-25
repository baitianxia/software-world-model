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
| V-ALPHA-ACCESS-001 | 首选 Provider 的访问与策略能力当前可用；Access 不冒充答案质量 | integration / provider access | Session 前密封 Ark→DeepSeek ordered route、双方 disclosure scope；Ark/DeepSeek exact credential reference、endpoint/model/configuration、Conformance、策略能力资格和 active hold；独立 attempt ledger | Ark 优先；Ark attempt 因冻结的 Provider/模型能力结果终态结束且没有 authorized answer 时，最多透明启动 1 个 DeepSeek attempt；用户不重提；fallback 从原交互输入和 exact cognition 重跑完整链，Chat 同时携带当前 Turn 的 exact relevant Application-sealed Conversation Context，不混中间产物；迟到 Ark 结果隔离；同 Provider retry=0；Access PASS 不能使质量 Case PASS | pending | not-run / blocking |
| V-TIMEBOX-001 | 首个持续 Web Alpha 遵守时间盒、root-cause-first 和轻量 live-attempt 停止规则 | product / delivery | 从 Slice 授权后的第一次产品代码变更计时；exact commit、事件时间、页面/Alpha 收据、外部 dispatch、failure-signature ledger、earliest-divergence hypothesis、本地复现与相邻案例 | 60 分钟页面、180 分钟持续 Alpha、240 分钟硬停止；首次体验前资格≤1、smoke≤1、full regression=0；先定位 Source→cognition→conversation/task understanding→Agent plan→tool evidence→answer→independent review→Web 最早偏差；无可证伪根因不得改 Prompt/Schema/Contract；本地最小复现+2 个未参与修复的相邻案例后仅 1 个有界 canary；同签名修复一次仍复现即架构职责评审 | pending | not-run / blocking |
| V-EXPERIENCE-001 | 首次方向体验是真正可持续操作的版本 | product / browser | <exact-version-single-launch-command-fixed-loopback-address-diverse-visible-cases-and-controlled-failure> | 可重复启动；版本和限制可见；问题真实经过产品链；失败后服务继续接受输入；声明 Chat 时具备消息历史与新对话 | pending | not-run / blocking |
| V-CHAT-001 | 主工程 Agent 在同一 Conversation 完成语义多轮 Chat | product / conversation | 固定工程/revision 的五轮追问、纠正和总结脚本；随后新对话中的无指代问题 | Agent 守恒目标并按观察重规划；追问解析正确；纠正取代旧解释；每轮独立证据/审核；新对话不泄漏旧指代并在歧义时澄清 | pending | not-run / blocking |
| V-COMP-ALPHA-001 | 首个持续 Web Alpha 的答案质量严格超过 current Codex | product / blind comparison | 一条原失败题及另外至少两个相邻或异质问题，后两题中至少一条为产品冻结后现场输入；fresh Codex 先密封；系统不可见；随机匿名 A/B；独立 evaluator 读取 exact evidence | 冻结问题全部完成并分类；系统绝对质量 PASS；每题不低于 Codex；blind-paired answer-quality margin > 0；部分题可打平但全体打平、both-fail、unresolved/invalid 均 FAIL；成本、时延或复用不得补偿 | pending | not-run / blocking |
| V-PREVIEW-001 | 用户在可持续 Alpha 上实际体验并决定是否进入夯实 | product / directional-preview | <V-EXPERIENCE-001-and-V-COMP-ALPHA-001-results-diverse-visible-cases-and-new-live-input> | 独立技术复核和严格 Codex 对照先通过；用户给出 CONTINUE、REWORK、REDIRECT 或 REJECT；非 CONTINUE 时禁止 hardening | pending | not-run / blocks hardening, not acceptance evidence |
| V-XD-001 | `<prior-acceptance-id>` 与 `<current-slice-id>` 在同一问题中组合 | product / integration | <stage-appropriate-exact-cross-domain-case> | <evidence-bound-answer-or-honest-gap> | pending | not-run / blocking |
| V-WEB-001 | `<current-slice-id>` 通过正式 Web 执行 `V-XD-001` | product / browser | <exact-web-subject> | <manual-user-visible-result> | pending | not-run / blocking |
| V-ADHOC-001 | `<current-slice-id>` 通过正式 Web 接受现场临时问题并覆盖 `V-XD-001` | product / browser | <user-owned-live-question-protocol> | <manual-user-visible-result> | pending | not-run / blocking |
| V-REFLECT-001 | `<current-slice-id>` 根据产品证据复盘关键方案假设并作出继续或停止决定 | architecture / reflection | <exact-slice-result-assumptions-findings-and-stage-applicable-baseline-signal-or-comparison> | <complete-review-and-explicit-decision> | pending | not-run / blocking |
| V-001 | <claim> | unit / contract / CC / CE / product / activation | <exact identity> | <result> | pending | not-run / blocking |

V-000 不能由新增 Profile/View 的封闭题集、测试数量或旧能力回归替代。测试、CC、CE、Product Validation 与 Activation 不得
互相替代。每项 Result 必须绑定 exact subject、运行身份、限制和有效期。完成时每个 Manifest 绑定的 `V-XD`、`V-WEB`、
`V-CANARY`、`V-ADHOC`、`V-REFLECT` 行都必须为 `PASS / blocking`，Evidence 必须精确填写
`<拥有该 Case 的 Slice Result ID>#<case-id>`；最终 Product Result 依赖并聚合全部唯一 Slice Result。只让 V-000 或汇总计数
PASS 不算完成。`V-REFLECT PASS` 只表示复盘完整，不表示方案通过；继续或接受必须由 Result 的独立 decision 字段表达。

`V-COMP-ALPHA` 与首个持续 Web Alpha 属于同一 Slice，不能拆成体验前的新阶段，也不能用后续 hidden Result 回填。current Codex 是强基线
候选，不是 Oracle 或裁判；事实来自同一 exact revision 的授权证据。最终 `V-000` 必须在 held-out 套件重跑严格比较，不能复用 Alpha。

`V-ALPHA-ACCESS` 只证明当前 Provider 可访问且具备本策略要求的资格；页面 availability 不依赖答案质量 PASS，`V-TIMEBOX` 因此不能等待
完整质量回归后才开始。Access 也不能替代 `V-COMP-ALPHA` 或本 Slice 的答案质量 Case；只有质量 PASS 才可进入 hardening。时间盒和
live-attempt 限制发生在问题之间，已经开始的问题必须保留完整调查、答案、Citation 和独立审核链。
