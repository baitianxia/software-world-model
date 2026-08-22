---
id: ITER-011-VERIFICATION
kind: iteration-verification
status: not-run
authority: planned-verification
owners: [quality]
depends_on: [ITER-011-PROPOSAL, ITER-010-RESULT-SLICE-001-STOP-REDIRECT]
code: []
tests: []
iteration: ITER-011
product_goal_gate: V-000
product_goal_outcome: user-visible-general-source-qa-delta
product_goal_evaluation: independent-hidden-plus-live-ad-hoc
product_goal_result_id: pending
---

# ITER-011 Verification Matrix

## Readiness and execution cases

| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |
|---|---|---|---|---|---|---|
| V-000 | 本轮相对 baseline 可测缩短通用源码问答 MVP 差距，并与既有能力完成跨域组合 | product / comparison | 未参与实现的真实工程；独立评测方/用户持有且实现阶段不可见的 held-out 自由问题；验收现场临时问题；旧+新知识跨域问题；成熟源码 Agent protocol；预提交差异化价值阈值 | 支持率提高；重大错误为 0；逐题完整性不退步；差异化价值阈值 PASS；提问时 Source/Update/Direct fallback=0；同一正式 Web 可人工验证 | not-executed | NOT-RUN / blocking |
| V-PRE-001 | exact redirect predecessor、technical product subject 与新 planning input 被准确分离 | readiness / baseline | commit `ff60e105…`、technical subject `8632904d…`、ITER-010 redirect Result | 技术资产保留；方向失败和旧 grant 不继承；新 plan 从 clean exact identity 冻结 | not-executed | NOT-RUN / readiness blocking |
| V-PRE-002 | ITER-010 方向失败按系统性答案/审核根因进入新 Iteration | readiness / evidence | ITER-010 Result、FINDING-010-027/028、Roadmap Candidate | 不重开 rejected Iteration，不按登录题或 Prompt 文风打补丁 | not-executed | NOT-RUN / readiness blocking |
| V-PRE-003 | 四段顺序把两次真实可验证出口放在全面夯实之前 | readiness / product | Proposal、四 Slice、Manifest checkpoint bindings | Slice1 1+1 探针；Slice2 3—5+现场 Alpha；Slice3 才 hardening；Slice4 验收 | not-executed | NOT-RUN / readiness blocking |
| V-PRE-004 | planning receipt 不被当作开发、live 或方向决定授权 | readiness / authorization | receipt `7711b359…`、Manifest/Readiness/Current | 全部 Slice proposed/coding false；active none；旧 grants 不复用 | not-executed | NOT-RUN / readiness blocking |
| V-PRE-005 | hidden、comparison、burn、质量门和成本口径只在对应后段冻结执行 | readiness / comparison | Slice3 early 5+2、Slice4 final 10+2、三臂 proposed protocol | Slice1/2 不被 hidden/comparison 阻断；Slice3 前新收据冻结；最终输入保持独立 | not-executed | NOT-RUN / readiness blocking |
| V-PRE-006 | A1—A4 与四个独立 Reflection/用户决定机械绑定 | readiness / architecture | Proposal assumption table、Manifest bindings、四 Slice | 每段独立出口；success decision 顺序为 CONTINUE、CONTINUE、CONTINUE、ACCEPT | not-executed | NOT-RUN / readiness blocking |
| V-BASELINE-001 | Slice1 subject 与 predecessor identity 精确，所有变化归属新 Slice | development / baseline | Git ancestry/tree/worktree、ITER-010 Result | clean exact candidate；旧 run identity 和 grant 不继承 | not-executed | NOT-RUN / blocking |
| V-ARCH-001 | answer hierarchy、Application acceptance 与 Reviewer quality Gate 有正式 Owner 且独立性不下降 | architecture / contract | ADR-016、Engineering QA/Response Control/Security contracts、Manifest | current System docs 与实现语义一致；无只存在于 Slice/代码的架构规则 | not-executed | NOT-RUN / blocking |
| V-HIERARCHY-001 | typed hierarchy 先直接回答用户目标，并在原问题或物质结论需要时表达可见流程/影响；实现、限制按条件展开 | application / answer | 一条代表题所需的最小正例、层级错配反例与改述反例 | 代表题 material checklist 完整；反例被拒；无固定标题/字数比例；无题目/工程/符号特判 | not-executed | NOT-RUN / blocking |
| V-REVIEW-001 | Application 与独立 Reviewer 按同一版本化 contract/schema、不同 checklist 阻断层级错配、重大遗漏、无据 Claim 和错误 Citation | application / review | immutable original question、Application checklist、独立重建 Reviewer checklist、正反 Draft、exact Package、独立上下文 | Reviewer 先发现两份 checklist 漏项；不合格必有具体 Finding 并失败或重写重审；合格可批准；Reviewer 不继承 checklist 结论或 verdict | not-executed | NOT-RUN / blocking |
| V-SEC-001 | 方向探针保持最小真实安全、授权、Secret、Citation 和失败真实性 | security / product | exact revision/disclosure/run grants、source injection、non-loopback、retry probes | read-only、模型 direct source/tool/credential 为 0、Secret 不泄露、retry/switch 0、非法路径关闭 | not-executed | NOT-RUN / blocking |
| V-XD-001 | 探针代表题在同一答案组合 accepted Cognition 与 query-time Source Evidence | product / integration | 一条冻结代表题、accepted capability、exact Package | 结论分别绑定正确来源，不形成两个正文或模式 fallback | not-executed | NOT-RUN / blocking |
| V-WEB-001 | 探针代表题从同一 product-owned loopback Web 完整执行 | product / browser | exact product/live freeze、V-XD-001 | 答案或 Limitation、可打开 Citation、折叠诊断、console clean、非回放 | not-executed | NOT-RUN / blocking |
| V-ADHOC-001 | Slice1 freeze 后用户从同一 Web 现场提出一题 | product / browser | user-owned exact live question receipt | 同一产品链交付可核对答案或诚实 Limitation，无临场产品修补 | not-executed | NOT-RUN / blocking |
| V-PREVIEW-001 | 在 Alpha/夯实前取得方向探针用户裁决 | product / directional-preview | V-WEB-001、V-ADHOC-001、独立质量裁决、非验收标识 | 独立评测先裁决正确性/完整性/Citation/边界/特判；用户看过实际结果后决定 CONTINUE、REDIRECT 或 REJECT | not-executed | NOT-RUN / blocking |
| V-REFLECT-001 | Slice1 复盘 A1 和 A2—A4 early signals | architecture / reflection | exact Slice1 Result、Cases、Findings、user decision receipt | A1 exact Verdict、其余 early signal、完整诊断与显式决定 | not-executed | NOT-RUN / blocking |
| V-ALPHA-002 | 一轮系统性最小迭代后，3—5 跨维度准备题显示答案优先方向可用 | product / alpha | 同一真实工程至少三个问题维度、至少两题非实现维度 | 预冻结质量阈值 PASS、重大错误 0、无特判；不冒充跨工程泛化验收 | not-executed | NOT-RUN / blocking |
| V-SEC-002 | Alpha 保持 exact/read-only/disclosure/Secret/loopback/no-retry 最小边界 | security / product | Alpha exact freezes 和合法/非法 live probes | 合法路径完成；非法路径失败关闭；旧 grant 不复用 | not-executed | NOT-RUN / blocking |
| V-XD-002 | Alpha 至少一题组合 accepted Cognition 与同一真实工程的多来源 Evidence | product / integration | exact Alpha question、World Model、source/doc/config/test evidence | 同一层级匹配答案与 Citation，不按题型路由 | not-executed | NOT-RUN / blocking |
| V-WEB-002 | 3—5 条 Alpha 准备题从同一产品 Web 执行 | product / browser | exact Alpha freeze/live grants | 每题交付答案/Limitation和可打开 Citation；console clean；非平行入口 | not-executed | NOT-RUN / blocking |
| V-ADHOC-002 | Alpha freeze 后用户至少现场提出一题 | product / browser | user-owned exact onsite question receipt | 同一质量和安全链交付，无产品代码临场修改 | not-executed | NOT-RUN / blocking |
| V-PREVIEW-002 | 用户根据完整 Alpha 独立决定是否进入工程化夯实 | product / directional-alpha | V-ALPHA-002、V-WEB-002、V-ADHOC-002、独立质量裁决、已知限制 | 独立评测先裁决技术质量；用户决定 CONTINUE、REDIRECT 或 REJECT；非 CONTINUE 时 Slice3 禁止启动 | not-executed | NOT-RUN / blocking |
| V-REFLECT-002 | Slice2 复盘 A1/A2 和 A3/A4 early signals | architecture / reflection | exact Slice1/2 Results、Cases、Findings、user decision receipt | A1/A2 exact Verdict、其余 early signal、完整诊断与显式决定 | not-executed | NOT-RUN / blocking |
| V-GENERAL-003 | 同一协议跨工程、命名、目录、框架和来源组合泛化且无特判 | product / generalization | 多工程与改述 fixtures、Source mixes | 用户层级正确；无 project/question/keyword/symbol/class/method/fixture/oracle branch | not-executed | NOT-RUN / blocking |
| V-RERETRIEVE-003 | 复杂缺口的独立多步补证形成后继 Ledger/Package/Answer/Review | application / contract | omission、citation gap、no-progress、unrepairable cases | prior Result 驱动；不回初始上下文；新包重答重审；不可修复关闭 | not-executed | NOT-RUN / blocking |
| V-PERSIST-003 | 持久 Ledger/Package 在中断、恢复、损坏和陈旧 identity 下正确 | application / reliability | restart/crash/truncation/concurrency/stale package fixtures | 精确恢复或失败关闭；历史不回写；旧 Review 不批准新包 | not-executed | NOT-RUN / blocking |
| V-CONFLICT-003 | conflict、partial、unknown、duplicate provenance 与 absence/coverage boundary 不混淆 | application / evidence | source/cognition conflicts、duplicate observations、coverage fixtures | 非支持条目不支持肯定 Claim；去重不丢 provenance；限制精确 | not-executed | NOT-RUN / blocking |
| V-HARDEN-003 | pagination、truncation、oversize、cycle、drift 和高安全熔断完整闭合 | application / reliability | 完整异常矩阵及 package/call/operation/bytes/time/no-progress bounds | 无漏页、越权、无界循环、伪完整或质量裁剪；超限真实失败 | not-executed | NOT-RUN / blocking |
| V-SEC-003 | 工程化链保持完整 Source/role/Provider/Secret/loopback 隔离 | security / integration | 合法/非法 end-to-end probes、Gateway/transport audit | direct source/tool/credential 为 0；write/fallback/retry/secret exposure 为 0 | not-executed | NOT-RUN / blocking |
| V-PERF-003 | 预提交的时延、tokens、Source bytes 和资源上限可测且不降低质量 | quality / performance | fixed workloads、cold/warm policy、exact cost counters | 阈值 PASS；超限失败关闭；不删除 checklist/Evidence/Citation/Review | not-executed | NOT-RUN / blocking |
| V-XD-003 | hardening canary 同一答案组合 accepted Cognition 与多来源 Evidence | product / integration | hidden-question canary、exact source/world-model identities | 支持结论与限制均绑定正确来源 | not-executed | NOT-RUN / blocking |
| V-WEB-003 | Slice3 canary 从同一真实 Web 交付 | product / browser | exact hardening candidate、V-XD-003、live grant | 页面与内部链同一；答案/Limitation/Citation可人工核对 | not-executed | NOT-RUN / blocking |
| V-CANARY-003 | 新冻结问题集的 5 answerable + 2 boundary 完整通过 | product / independent-hidden | Slice3 code freeze 后 user-held suite；burn rule | 5/5 supported、2/2 boundary、重大错误 0、披露后产品变化 0 | not-executed | NOT-RUN / blocking |
| V-NEG-EARLY-003 | bounded absence 与 coverage limitation 保持区分 | product / early falsification | canary 的两类 boundary 和改述 | 完整性不足只给具体 limitation；无关证据 FAIL | not-executed | NOT-RUN / blocking |
| V-COMP-EARLY-003 | 三臂 early comparison 判断完整 Cognition 的独立价值 | product / comparison | 新收据冻结 full cognition、locator control、成熟 Agent 及同题同预算协议 | 完整与 Agent 先过质量门；完整再达预提交质量或非 locator 成本增益；计建模成本 | not-executed | NOT-RUN / blocking |
| V-DIAG-003 | 对同一问题逐层定位首次偏差 | architecture / diagnostic | Source 到 Web 的 exact refs | 每层独立 verdict；首次偏差决定分类，不从最终答案猜根因 | not-executed | NOT-RUN / blocking |
| V-REGRESSION-003 | accepted scope、三模式、Probe/Alpha 与 full suite 无退步 | regression / product | prior accepted oracles、Slice1/2 Results、current full suite | 无新增失败、能力降级、Source leak 或入口分叉 | not-executed | NOT-RUN / blocking |
| V-REFLECT-003 | Slice3 复盘 A1—A3 与 A4 early comparison | architecture / reflection | exact Slice1—3 Results、Cases、Findings、user decision receipt | A1—A3 exact Verdict、A4 early verdict、完整诊断与显式决定 | not-executed | NOT-RUN / blocking |
| V-HIDDEN-004 | 最终两个未见工程 10 answerable + 2 boundary 验证泛化 | product / independent-hidden | final code freeze 后 user-held projects/suite；至少 8 no-symbol | 10/10 supported、2/2 boundary、重大错误 0、披露后产品变化 0 | not-executed | NOT-RUN / blocking |
| V-COMP-004 | 最终三臂复验证明 ENGINEERING_QA 质量与完整 Cognition 增益 | product / comparison | final same revision/model/questions/budget/cache/rubric 三臂协议 | 自身质量 Gate、Agent 对照和预提交增益全部 PASS，成本完整可重放 | not-executed | NOT-RUN / blocking |
| V-SEC-004 | 最终产品链保持全部授权、安全、role 和 disclosure 边界 | security / product | final hidden/live sessions、Gateway/Source/Package audit | direct source/tool/credential 为 0；write/fallback/secret/retry 为 0；loopback | not-executed | NOT-RUN / blocking |
| V-XD-004 | 最终问题在同一答案链组合 accepted Cognition 与多来源 Evidence | product / integration | final hidden no-symbol cross-source question | 同一正式答案和 Citation 支持旧+新能力 | not-executed | NOT-RUN / blocking |
| V-WEB-004 | Slice4 从同一正式 Web 执行 final suite | product / browser | exact final candidate、10+2、run grants | 页面交付答案/Limitation/Citation；console clean；与内部链相同 | not-executed | NOT-RUN / blocking |
| V-ADHOC-004 | 用户从 final freeze 后 Web 提出两条现场问题 | product / browser | user-owned live question protocol；至少一条 no-symbol/cross-domain | answerable supported；真实 boundary 正确；Citation 可核对；无 fallback | not-executed | NOT-RUN / blocking |
| V-REGRESSION-004 | 最终候选保持 accepted scope 与前三个 Slice Result | regression / product | prior oracles、三个 Slice Results、full suite | 无新增失败、能力降级、source leak 或三模式分叉 | not-executed | NOT-RUN / blocking |
| V-010 | 本机验证和 Acceptance 不产生 Production Activation | activation | exact final Iteration Result | NOT_EXECUTED | not-executed | NOT-RUN / blocking |
| V-REFLECT-004 | 最终复盘 A1—A4 并由用户裁决 | architecture / reflection | 四个 exact Slice Results、10+2、现场题、comparison、安全、Findings | A1—A4 exact Verdict；全部 SUPPORTED 且用户新 ACCEPT 才可申请 Acceptance | not-executed | NOT-RUN / blocking |

## Freeze and scoring rules

- Slice1 只执行 1 条代表题 + 1 条现场题；Slice2 只执行 3—5 条跨维度准备题 + 至少 1 条现场题。两者都必须真实 Web、Citation、独立
  Review、最小安全与 exact freeze，但都不是 Acceptance。
- Slice1 user `CONTINUE` 只允许申请 Slice2；Slice2 user `CONTINUE` 是 Slice3 开发的硬前置。Reflection PASS 不能替代用户决定。
- persistence、复杂补证、conflict/dedup、完整安全性能、full regression、hidden 和三臂在 Slice1/2 明确禁止作为阻断项；它们由 Slice3 持有。
- Slice3 canary 和 Slice4 final suite 分别在所属 code freeze 后披露；披露后产品/Prompt/schema/route/disclosure 变化烧毁输入并保留 Result。
- 最终 10 条 answerable 是 supported 分母，Gap 不计 PASS；2 条 boundary 单独要求 2/2；重大错误必须为 0。
- 三臂 protocol、阈值、budget、cache、rubric 和复用周期须在 Slice3 前以新用户收据冻结。完整 Cognition 与成熟 Agent 先过质量 Gate，
  locator control 失败不能降低完整 Cognition 门槛；建模/更新/存储/Provider 成本必须计入。
- 调用次数不构成质量裁剪理由；安全熔断超限失败关闭，不能删除 checklist、Evidence、Citation 或独立 Review。
- 每个 Slice Product Result 必须拥有本 Slice Case、exact freeze、限制、Reflection 和用户 decision；最终 V-000 聚合四个唯一 Result。
