---
id: ITER-008-VERIFICATION
kind: iteration-verification
status: not-run
authority: planned-verification
owners: [quality]
depends_on: [ITER-008-PROPOSAL]
code: []
tests: []
iteration: ITER-008
product_goal_gate: V-000
product_goal_outcome: user-visible-general-source-qa-delta
product_goal_evaluation: independent-hidden-plus-live-ad-hoc
product_goal_result_id: not-executed
---

# Iteration 008 Verification Matrix

| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |
|---|---|---|---|---|---|---|
| V-000 | 本轮相对 baseline 可测缩短通用源码问答 MVP 差距，并与既有能力完成跨域组合 | product / comparison | 未参与实现的真实工程；独立评测方/用户持有且实现阶段不可见的 held-out 自由问题；验收现场临时问题；旧+新知识跨域问题；成熟源码 Agent protocol；预提交差异化价值阈值 | 支持率提高；重大错误为 0；逐题完整性不退步；差异化价值阈值 PASS；提问时 Source/Update/Direct fallback=0；同一正式 Web 可人工验证 | not-executed | **NOT-RUN / blocking** |
| V-PRE-001 | 新架构决定仍以 World Model 为知识权威，Agent 只负责受限调查 | readiness / architecture | `SYS-ADR-015`；raw `sha256:ed325cc4…a9e` | 拒绝单方法固定选择、无界展开和源码 Direct；明确 Snapshot、Agent、平台、Reviewer Owner | ADR accepted；Owner/data flow/alternatives/supersession 均闭合 | **PASS / readiness blocking** |
| V-PRE-002 | 所有相关 System Contract 与机械门禁在编码前一致 | readiness / contract | Manifest `ITER-008-SYSTEM-CONTRACT-SET@1` 12-file digest；后续 System 变化只允许由 implementation Finding 和显式 redirect 重冻结 | 有界可变调查、三层完整性、负向结论、Draft/Review 和失败语义无冲突；docs gate PASS | 原 readiness fileset PASS；`FINDING-008-019/021/022/023/024/025/026/027/028/029` 分别按实现证据重冻结 Owner、evidence subsumption、dispatch 前 Provider route selection、persistent verified TLS/零 request retry、DeepSeek 单一 system authority、capability-selected semantic authority、产品真实的 search-term constraint、精确 historical-hold freeze gate 与 cross-script source-identifier adaptation；当前 digest `sha256:58288f15…19a0` | **PASS / readiness blocking** |
| V-PRE-003 | exact baseline 与 ITER-007 待复用技术资产被诚实冻结 | readiness / baseline | commit `38ebed20…5877`；tree `28ad8091…44ac`；baseline report `sha256:8cf4faa5…1e83` | 只把 ITER-005/006 Acceptance 列为 accepted；ITER-007 资产重新验收；工作树与输入可重建 | 916 sandbox PASS + affected AF_UNIX 7/7 authorized-surface PASS + demo 121/121；ITER-007 保持 unaccepted | **PASS / readiness blocking** |
| V-PRE-004 | 调查预算、安全禁止面和资格协议在开发前可机械验证 | readiness / security | budget protocol raw `sha256:edb492b7…1012`；2—4 investigation、总调用 4—6、bytes/time/support/trace 与 operation allowlist | 超限失败关闭并给明确 Limitation；Agent 看不到 Repository/Source/raw Evidence/Update/Direct；新 Strategy 资格协议可重放且必须在实现后另行执行 | 预算/禁止面/variable-call Gateway 规则已进入 ADR/Contract；旧三调用资格明确不可继承 | **PASS / readiness blocking** |
| V-PRE-005 | 早期 canary、最终隐藏项目和用户逐 Slice 授权协议已冻结 | readiness / product | hidden protocol raw `sha256:5936ab02…9c01`；early 1+2；final 2 projects/4+2；burn/disclosure/Web 规则 | 每组在对应代码冻结前不可见且互不复用；用户先只授权 SLICE-001，PASS Result 后再决定 SLICE-002 | user-held marker 与一次性披露/burn rule 已冻结；SLICE-002 仍 proposed | **PASS / readiness blocking** |
| V-PRE-006 | 成熟源码 Agent 对照有可重复的逐题裁决、成本口径和正向价值阈值 | readiness / comparison | Agent `sha256:66078a61…9e1d`；rubric `sha256:6fe156f6…2c1b`；cache `sha256:d3b10942…8ff8`；value `sha256:5f79ff12…a6d4`；用户 receipt `sha256:eb381cfd…7221` | baseline 与计算规则在编码前密封；四类成本分开统计；actual 可由 exact report 重放；不得在看到结果后更换 Agent、rubric 或价值阈值 | ratio-ppm、at-most 250000、reuse horizon 12；零重大错误/逐 Need-Claim 不退步为前置 | **PASS / readiness blocking** |
| V-PRE-007 | 关键架构假设、最早反证和逐 Slice 复盘规则在编码前冻结 | readiness / architecture | Proposal A1—A8 catalog `sha256:1248eae8…171c`；Manifest/Readiness 同 digest；V-DIAG/互补 boundary/Reflection binding | Manifest/Readiness/Result 绑定同一假设摘要且 Expected 不可事后改写；第一段对 A1—A6 下 Verdict，A7/A8 只作早期反证，最终覆盖全部；区分“复盘完成”与“方案通过”；无 CONTINUE 不得授权下一段 | exact catalog、conditional falsifier、Owner 和新消息规则已冻结 | **PASS / readiness blocking** |
| V-PRE-008 | 正式产品 freeze 如实区分 raw regression 与已处置的历史环境 hold | readiness / verification | deterministic qualification `@2`；`FINDING-008-020/028`；五个 exact test ID、V-009 reason 与 prepared digest | raw PASS 正常通过；raw FAIL 仅在 4 FAIL + 1 ERROR、五项各执行一次、原因精确且其余测试全 PASS 时形成 preserved-hold gate PASS；任何漂移阻断且不能推导 Acceptance/Activation | parser/runtime/authorize 定向 22/22 PASS；首次 full 因未重算 System digest 出现第六项失败并被正确阻断；重算后 1021/1026，唯一五项精确 hold，gate `PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD` | **PASS / formal freeze blocking** |
| V-001 | Snapshot 在问题前由零问题更新形成，提问不改变知识状态 | update / isolation | exact revision、Build Objective、Snapshot/Bundle digest、before/after authority state | 问题和 suite 不进入 Update；问答前后 CURRENT/Snapshot/Bundle identity 不变 | not-executed | **NOT-RUN / blocking** |
| V-002 | Agent 根据结果执行多个 typed World Model 查询而非固定单方法消歧 | application / capability | 多候选、0 候选、最小预算和非法操作 corpus | 每一步由前一步 typed result 支持；可跨候选和方法继续；非法/超限失败关闭；trace 完整 | exact candidate `6dc7a9e4…` 的 run-019 曾以 40 calls / 18/18 PASS，但 formal Web 暴露英文-only qualification 未覆盖中文产品输入；`FINDING-008-029` 将活动 identity 升级为 `1.5.6/@15`，run-019 不可继承。新 18-case/40-call Capability 尚未执行 | **NOT-RUN / blocking** |
| V-003 | 公开登录流程回归形成多方法 supported answer | product / regression | frozen LoginService Snapshot；“登录流程”及等价释义 | 组合 `authenticate`、两次 `recordFailure()`、异常与 `issueSession()` 成功路径；有 Support/Citation | formal Web `run-001` 的唯一 DeepSeek call 返回合法 `登录/流程` intent，但 ASCII-only Query tokenizer 失败关闭；terminal `sha256:1cca15fa…f0f`，无 answer/Citation/retry。`FINDING-008-029` 修复与新资格进行中 | **FAIL / blocking** |
| V-004 | 公开下单流程回归不产生无关登录支持 | product / regression | 同一 frozen LoginService Snapshot；“下单流程”及等价释义 | 三层完整性足够才给 bounded absence；否则给具体 Limitation；任何情况都不得引用登录方法作支持 | not-executed | **NOT-RUN / blocking** |
| V-XD-001 | `ITER-006-RESULT-ACCEPTANCE` 与 `ITER-008-SLICE-001` 在同一答案链组合 | product / integration | 无符号多方法问题；accepted declaration/`CALLS` 与 implementation semantics | 同一 Need/Support chain 同时引用 accepted `CALLS` 和重新验收的 branch/return/throw，不是正文拼接 | not-executed | **NOT-RUN / blocking** |
| V-SEC-001 | 有界调查的授权、预算、Snapshot fence 与 Reviewer 隔离失败关闭 | security / integration | unauthorized operations、stale Snapshot、oversize result、budget exhaustion、review tamper probes | 全部拒绝且无 fallback；合法多步 trace 可完成；Reviewer 独立审查漏查和无依据结论 | not-executed | **NOT-RUN / blocking** |
| V-SOURCEOFF-001 | 回答进程只能查询 World Model，不能读源码或触发更新 | isolation / security | Repository、Source、Artifact/Evidence、authority DB denied；operation audit | answerable/Gap 正常；Source/Update/Direct/raw Evidence attempt 均为 0 | not-executed | **NOT-RUN / blocking** |
| V-WEB-001 | 完整调查链从正式产品 Web 可人工体验 | product / browser | product-owned Web、真实资格模型、登录/下单和一条跨域题 | 页面显示答案/Gap、Coverage、Citation；console clean；与内部测试同一链；无 validation-only launcher | 正式 Web 已执行登录题但返回 502/`EXECUTION FAILED CLOSED`；首次偏差为 Query tokenizer，未继续下单或跨域题。旧 freeze/session 保留为失败证据，新 identity 必须重新 freeze | **FAIL / blocking** |
| V-CANARY-001 | SLICE-001 在继续加固前通过真正隐藏的早期产品 Gate | product / independent-hidden | 代码冻结后才披露、且不复用为最终评测的一份小型真实 Java 工程；至少 1 条无符号多方法 answerable 与 2 条互补 boundary | 同一正式 Web 给出 supported answer、一个可证明 bounded absence 和一个 Coverage 不足的具体 Limitation；Source/Update/Direct=0；披露后产品变更 0 | not-executed | **NOT-RUN / blocking** |
| V-NEG-EARLY-001 | 在大量加固前验证三层完整性在最小闭包上至少可成立，而不是统一返回 Limitation | product / early falsification | hidden complete-coverage absence + incomplete-coverage limitation；命名/同义词/不同入口反例 | 完整最小闭包由三层独立 Oracle 给 bounded absence；不完整闭包只能 Limitation；任一不成立立即 REDIRECT | not-executed | **NOT-RUN / blocking** |
| V-DIAG-001 | 对同一问题逐层定位首次偏差，避免把表示、Query、Agent 或 Web 问题混为一谈 | architecture / diagnostic | Source ground truth、Snapshot atom/Coverage、typed-query result、trace、Draft/Review、Web delivery exact refs | 每层有独立 verdict；首次偏差决定问题分类；不得仅从最终答案失败反推根因 | not-executed | **NOT-RUN / blocking** |
| V-COMP-EARLY-001 | 在大量加固前确认最小 World Model 方案既不低于成熟源码 Agent，又达到预提交正向价值阈值 | product / early comparison | early canary 同 revision、同 1+2 问题、同冻结 rubric/资源/时延成本阈值；预提交 value metric/threshold/reuse horizon/cache policy；Agent 先运行并密封 | 重大错误为 0、逐 Need/Claim 不退步、boundary 无无关证据且价值阈值 PASS；Slice Result 的 exact JSON report/digest/input digest/独立裁决收据可重放；任一失败立即停止 | not-executed | **NOT-RUN / blocking** |
| V-REFLECT-001 | SLICE-001 根据 Web、canary、逐层诊断和 early Agent 对照复盘架构，而不是因技术链 PASS 自动继续 | architecture / reflection | Proposal A1—A8；SLICE-001 exact Result、Finding 与成本/质量/价值证据 | A1—A6 逐项记录 exact Evidence/verdict；A7/A8 early FAIL 时追加结构化行；Reflection PASS 只表示复盘完整；全部到期假设 SUPPORTED、用户 decision receipt 与 CONTINUE 同时成立才可申请下一段授权 | not-executed | **NOT-RUN / blocking** |
| V-NEG-001 | 负向结论分别证明查询、表示和业务发现三层完整性 | knowledge / correctness | full/truncated pages、complete/incomplete disposition、同义词/不同命名/不同入口反例 | 三层 Oracle 全 PASS 才允许 bounded absence；任一层不足只能 Limitation；分页结束不得冒充业务召回完整 | not-executed | **NOT-RUN / blocking** |
| V-HARDEN-001 | 分页、progress/cycle、预算和 Reviewer 在多步调查中稳定失败关闭 | application / security | multi-page、repeated query、oversize result、budget exhaustion、review omission/tamper matrix | 无漏页、死循环、无界展开或 fallback；超限有具体 Limitation；Reviewer 能拒绝漏查和错误否定 | not-executed | **NOT-RUN / blocking** |
| V-XD-002 | `ITER-006-RESULT-ACCEPTANCE` 与 `ITER-008-SLICE-002` 在最终问题中组合 | product / integration | 最终无符号多方法问题；accepted declaration/`CALLS` 与重新验收的 implementation semantics | 同一 Need/Support chain 同时引用两类知识，并由最终 Web 与现场题共同执行 | not-executed | **NOT-RUN / blocking** |
| V-WEB-002 | 加固后的完整链从同一正式产品 Web 执行最终验证 | product / browser | product-owned Web、真实资格模型、final hidden suite、`V-XD-002` | hidden/Agent comparison/现场题均走同一产品链；答案/Gap/Citation 可人工核对；console clean | not-executed | **NOT-RUN / blocking** |
| V-HIDDEN-001 | 两个未见真实工程的 4+2 自由问题验证泛化 | product / independent-hidden | 产品代码冻结后披露的 exact real projects/suite；2 multi-method；3 no-symbol；2 boundary | answerable 4/4 supported；boundary 2/2；重大错误 0；披露后产品变更 0；Gap 不算 answerable PASS | not-executed | **NOT-RUN / blocking** |
| V-COMP-001 | World Model 回答逐题不低于成熟源码 Agent，并证明预提交的差异化价值 | product / comparison | 同 revision、同问题、等价资源与 cache policy；sealed Agent baseline；frozen Need/Claim rubric、value metric/unit/direction/numeric threshold/reuse horizon/protocol 与 independent adjudicator | 逐 Need/Claim 不退步；重大错误 0；Agent 可答而 World Model Gap/遗漏直接 FAIL；actual 按冻结方向达到阈值且 exact report 可重放；争议按冻结规则裁决 | not-executed | **NOT-RUN / blocking** |
| V-ADHOC-001 | 用户从正式 Web 现场提出 2 条未披露问题并执行 `V-XD-002` | product / browser | SLICE-002 product code freeze 后用户临时题；至少 1 条无符号名且跨域 | answerable 给 supported 跨域答案，真实 boundary 给正确 Gap/Limitation；无 fallback | not-executed | **NOT-RUN / blocking** |
| V-REGRESSION-001 | ITER-003—006 已接受能力不因新协议退步 | regression / product | accepted Result Oracles 与 current full suite | Workspace/Update/Snapshot/View/Web/Citation/Java static call accepted scope 保持；无旧 Direct 路径兜底 | not-executed | **NOT-RUN / blocking** |
| V-009 | 本机 PASS 不产生 Production Activation | activation | exact Iteration Result | `NOT_EXECUTED` | not-executed | **NOT-RUN / blocking** |
| V-REFLECT-002 | 最终验证后复盘方案价值并决定接受、转向或拒绝 | architecture / reflection | 两段 exact Result、最终 4+2、现场题、成熟源码 Agent 对照、可重放正向价值报告、四类成本、全部 Finding | 复核 A1—A8 与复杂度/收益；质量仅持平但数值价值阈值未达时禁止 ACCEPT；必须有用户 decision receipt；回写能力路径和下一阻断 | not-executed | **NOT-RUN / blocking** |

## Freeze and scoring rules

- 公开 LoginService 只用于回归，不计入早期 canary 或最终 4+2。
- 早期 canary 与最终两个隐藏工程互不复用；每组身份、源码和问题在对应 Slice 产品代码冻结前对实现方不可见。披露后任何产品
  修改都会保留失败并烧毁该组 projects、suite、baseline 与 target，重试必须全部更换。
- 4 条 answerable 是 supported 分母，Gap 不计 PASS；2 条 boundary 单独要求 2/2。
- 成熟源码 Agent 必须在 World Model 输出前运行并密封；双方使用同 revision、同问题和预先冻结的等价资源上限。逐 Need/Claim
  rubric、重大错误、独立裁决、争议/同分/失败规则必须在代码冻结前固定。
- 成本分别报告 World Model 建模、单题问答、多题摊销和源码 Agent 调查；不能用其中一种口径替代另一种。
- Readiness 前必须冻结一项可测的 World Model 正向差异化价值指标、PASS 阈值、复用问题数和成熟源码 Agent 的缓存/复用政策；
  只能报告成本、质量打平或事后更换指标均不构成 A6 PASS。
- SLICE-001 的 1+2 early canary 也必须先密封成熟源码 Agent 同题结果；它用于尽早证伪方案，不计入最终 4+2。
- 每个 Reflection Case 的 PASS 只表示复盘资料和决策完整，不替代所属 Slice 的产品 Case PASS。中间 Slice 还必须决定
  `CONTINUE`，最终 Slice 必须决定 `ACCEPT`；否则分别转入 `REDIRECT/REJECT`。
- 最终 Product Result 必须逐项绑定本 Matrix，不能用测试总数或模型调用成功替代产品正确性。
