---
id: ITER-009-VERIFICATION
kind: iteration-verification
status: not-run
authority: planned-verification
owners: [quality]
depends_on: [ITER-009-PROPOSAL]
code: []
tests: []
iteration: ITER-009
product_goal_gate: V-000
product_goal_outcome: user-visible-general-source-qa-delta
product_goal_evaluation: independent-hidden-plus-live-ad-hoc
product_goal_result_id: not-executed
---

# ITER-009 Verification Matrix

| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |
|---|---|---|---|---|---|---|
| V-000 | 本轮相对 baseline 可测缩短通用源码问答 MVP 差距，并与既有能力完成跨域组合 | product / comparison | 未参与实现的真实工程；独立评测方/用户持有且实现阶段不可见的 held-out 自由问题；验收现场临时问题；旧+新知识跨域问题；成熟源码 Agent protocol；预提交差异化价值阈值 | 支持率提高；重大错误为 0；逐题完整性不退步；差异化价值阈值 PASS；提问时 Source/Update/Direct fallback=0；同一正式 Web 可人工验证 | not-executed | NOT-RUN / blocking |
| V-PRE-001 | product baseline、planning commit 和未验收实验被精确分离 | readiness / baseline | product `2cd743b2ba74c5a79cd4d38433830786de09e753`、planning `967e41bcaa25112ea6b18620d0ac8e0aa5a4a42a`、archive `c4ed92ea44383557dd25e6d327569cff13bb6d65` | 新分支只继承 product baseline 和规划；归档 `1.5.12` 不在 ancestry/worktree；dirty worktree 禁止 | Git object/tree/branch inspection；Proposal、Manifest 与 Slice 一致 | PASS / readiness blocking |
| V-PRE-002 | 当前产品证据被正确分类，不把 ITER-008 技术结果误写成 Acceptance | readiness / evidence | run-012 formal report file `sha256:776a3afd5dca957a0bc2bd2b29a36bbea4b943ac2f7caa3d54f836f79fa84e6c`、positive browser result file `sha256:d1a8a9760ecd3673504d1bdd0dc5f4e1dbb6c233f5f2c509888fc6cb40175c91`、boundary terminal file `sha256:c4812a82b576ce79cc8b4be871a10cd038b60f2ccc91c7c34b06068c75abb4eb` | 正向 Web 可用和 Review/Limitation 缺口作为 baseline 事实；不继承 Product Acceptance、旧 grant 或资格 | Proposal Trigger、Readiness evidence classification 与 Results index 一致 | PASS / readiness blocking |
| V-PRE-003 | 方向体验优先的三个 Slice 顺序、授权边界和停止规则已冻结 | readiness / governance | development policy、iteration lifecycle、Proposal、三个 Slice、Manifest reflection bindings | 先真实 Web；用户 CONTINUE 后才夯实；再次 CONTINUE 后才正式验收；每段独立 Result/新授权；REDIRECT/REJECT 停止 | `ITER-009-PROPOSAL`、`ITER-009-SLICE-001/002/003`、Manifest | PASS / readiness blocking |
| V-PRE-004 | 安全、权限、Secret、Provider dispatch 与 Web 运行没有被初始开发授权扩大 | readiness / security | user authorization receipt `sha256:6ca47f7daa8bff61fa53e99d1c19b16098207d45fbf210427c3af19e5c9999ed`、System Contract fileset、Slice1 boundary | 只授权编码和本地确定性测试；live Provider、credential、正式 Web、browser question、hidden disclosure 与 Production 均需后续 exact grant | Readiness、Manifest authorization 和 SLICE-001 明确相同禁止面 | PASS / readiness blocking |
| V-PRE-005 | 成熟源码 Agent 对照、价值阈值、隐藏披露和 burn 规则在编码前冻结 | readiness / comparison | Agent `sha256:66078a61f7c5f25fc72c0c36c004819c99ae01c8465d01229149efc1e5809e1d`、rubric `sha256:6fe156f6f68cdaf572102f9e76feb8953e7e0838ee10ae57b0f11900bc9d2c1b`、cache `sha256:d3b10942f2b9a98f2b9da22bf04dbf2a1a150299a07f33f292da69c875698ff8`、value `sha256:5f79ff127574f2bce75cd31b0e217444ac3c15318bb4c9e435f615dad150a6d4` | ratio-ppm at-most 250000、reuse horizon 12；early/final hidden 输入互不复用；披露后产品变化烧毁 evidence | Proposal 与 Manifest exact frozen values | PASS / readiness blocking |
| V-PRE-006 | 关键假设、最早反证、System Contract set 和回答预算全部可机械验证 | readiness / architecture | Proposal A1—A5 catalog `sha256:3ca13e4768159698cd69092946d820b7e04059fa6292b316c75b5c07cb0a659a`、Manifest reflection/conditional falsifier、`ITER-009-SYSTEM-CONTRACT-SET@1`、2—4 investigation + Draft/Review budget | 每段假设覆盖单调增加且最终全覆盖；每个 deferred assumption 有 owned early blocker；Contract set digest 与文件一致；无 fixed-call 降质 | Proposal、Manifest、Readiness 与 docs gate | PASS / readiness blocking |
| V-BASELINE-001 | Slice1 实际开发 subject 仍从精确 product baseline 开始且不含归档实验 | development / baseline | Git ancestry/tree、worktree status、archive commit diff | product baseline 与 planning-only delta 可复现；无 `1.5.12` 批量继承；任何选择性吸收留到 Slice2 Finding | not-executed | NOT-RUN / blocking |
| V-001 | Snapshot 在问题前由零问题更新形成，提问不改变知识 identity | update / isolation | exact repository revision、Build Objective、before/after authority state | question/suite 不进入 Update；CURRENT/Snapshot/Bundle identity 前后相同 | not-executed | NOT-RUN / blocking |
| V-SOURCEOFF-001 | 回答进程只能读取 no-payload World Model，不读源码或触发更新 | isolation / security | Repository、Source、raw Evidence、Update、Direct denied probes与 operation audit | supported answer 或 Limitation 可完成；Source/Update/Direct/raw Evidence attempt 均为 0 | not-executed | NOT-RUN / blocking |
| V-SEC-001 | 方向体验保持 loopback、授权、Secret、预算、独立审核、零隐藏重试与失败关闭 | security / integration | stale identity、unauthorized operation、oversize/budget、review tamper、outcome unknown、non-loopback probes | 全部失败关闭且无 fallback/retry/secret exposure；合法路径完成；页面只监听 127.0.0.1 | not-executed | NOT-RUN / blocking |
| V-ANSWER-001 | Slice1 supported 多步骤题及无符号改述形成自然、完整、可引用答案 | product / regression | 代码冻结后的正式 Web、同一业务语义的两种自然语言表达、exact evidence package | 重要行为无重大遗漏；答案不平铺内部证明；每项关键结论绑定真实 Citation | not-executed | NOT-RUN / blocking |
| V-LIMIT-001 | Slice1 boundary 形成具体 typed Limitation 而不是内部失败或伪造结论 | product / boundary | evidence insufficient 的真实问题、Draft/Review typed contract、无关证据反例 | 明确说明证据缺口和可支持范围；Reviewer 按 Limitation 语义裁决；无无关登录证据或绝对否定 | not-executed | NOT-RUN / blocking |
| V-XD-001 | `ITER-006-RESULT-ACCEPTANCE` 与 `ITER-009-SLICE-001` 在同一答案链组合 | product / integration | accepted declaration/`CALLS`、Slice1 evidence organization/review delivery、无符号多步骤题 | 同一回答同时依赖 accepted static-call 事实和本轮交付能力，不是正文拼接 | not-executed | NOT-RUN / blocking |
| V-WEB-001 | Slice1 从真实 product-owned Web 执行 `V-XD-001` | product / browser | loopback 页面、普通用户无认证、run-specific grant、全新问题提交 | 用户看到答案或具体限制和可打开 Citation；console clean；不是回放、CLI 或 validation-only launcher | not-executed | NOT-RUN / blocking |
| V-PREVIEW-001 | 在全面夯实前完成最小真实方向体验并取得用户方向结论 | product / directional-preview | `V-WEB-001` 入口、supported 多步骤题、无符号改述、boundary、非验收/非生产标识 | 核心交互、答案组织、引用与限制均可体验；用户决定 CONTINUE、REDIRECT 或 REJECT | not-executed | NOT-RUN / blocking |
| V-REFLECT-001 | Slice1 复盘方向体验、公开基线和 A1—A3 | architecture / reflection | Slice1 exact Result、A1—A5、全部 owned Case、Findings、用户新决策收据 | A1—A3 exact Verdict；A4/A5 early FAIL 时追加结构化反证；Reflection 完整且决定为 CONTINUE、REDIRECT 或 REJECT | not-executed | NOT-RUN / blocking |
| V-ANSWER-002 | Slice2 统一交付 supported answer、bounded negative 与 insufficient coverage | contract / product | 通用 typed fixtures、第二真实工程、sealed evidence package | 三类结果按 evidence state 交付，无题目/工程/关键词/符号特判 | not-executed | NOT-RUN / blocking |
| V-REWRITE-002 | Slice2 独立 Reviewer 的具体 finding 可以驱动一次有界 targeted rewrite | application / contract | material omission、unsupported inference、citation gap、unfixable cases | 同一 evidence package 最多一次 rewrite 且重新 Review；不可修复失败关闭；不是隐藏 retry | not-executed | NOT-RUN / blocking |
| V-HARDEN-002 | Slice2 的 coverage、预算、schema、Ref provenance 与 terminal 语义机械闭合 | application / security | pagination、truncation、oversize、cycle、budget、stale Ref、invalid terminal matrix | 无漏页、越权、无界循环或伪完整；超限返回具体 Limitation 或失败关闭 | not-executed | NOT-RUN / blocking |
| V-SEC-002 | Slice2 保持 Source-off、Secret、授权、Reviewer 隔离和零隐藏 retry | security / integration | 合法与非法 end-to-end probes、Gateway/transport audit | 合法路径完成；非法全部失败关闭；fallback、retry、secret/source exposure 均为 0 | not-executed | NOT-RUN / blocking |
| V-XD-002 | `ITER-006-RESULT-ACCEPTANCE` 与 `ITER-009-SLICE-002` 在第二工程同一答案链组合 | product / integration | accepted declaration/`CALLS`、新 evidence/review/rewrite protocol、第二工程无符号题 | 同一 answer/limitation 与 Citation 组合旧事实和新交付能力 | not-executed | NOT-RUN / blocking |
| V-WEB-002 | Slice2 从同一真实 Web 执行 `V-XD-002` | product / browser | product-owned loopback Web、第二工程、当前 exact qualification/run grant | answerable 与 boundary 均用户可见、Citation 可核对、console clean、无平行入口 | not-executed | NOT-RUN / blocking |
| V-CANARY-002 | Slice2 通过一份 1 answerable + 2 boundary early canary | product / independent-hidden | 代码冻结后用户披露的真实 Java 工程、互补 1+2、burn rule | 三题裁决正确且无特判；披露后产品变化=0；不复用公开方向体验输入 | not-executed | NOT-RUN / blocking |
| V-NEG-EARLY-002 | Slice2 在第二工程保持 bounded negative 与 coverage limitation 区分 | product / early falsification | `V-CANARY-002` 两类 boundary、不同命名/入口/同义词反例 | 证据完整才给 bounded negative；否则具体 Limitation；任何无关证据 FAIL | not-executed | NOT-RUN / blocking |
| V-COMP-EARLY-002 | Slice2 在正式验收前与成熟源码 Agent 比较正确性并测量预提交正向价值 | product / early comparison | `V-CANARY-002` 同 revision/问题、冻结 Agent/rubric/cache/value protocol、Agent 先运行并密封 | 重大错误 0、逐 Need/Claim 不退步、ratio-ppm at-most 250000；exact report 可重放 | not-executed | NOT-RUN / blocking |
| V-DIAG-002 | Slice2 对同一问题逐层定位首次偏差 | architecture / diagnostic | Source truth、Snapshot/Coverage、typed query、evidence package、Draft、Review、Web exact refs | 每层独立 verdict；首次偏差决定分类；不从最终错误猜根因 | not-executed | NOT-RUN / blocking |
| V-REGRESSION-002 | Slice2 不使 accepted 能力和方向体验主线退步 | regression / product | ITER-003—006 accepted oracles、Slice1 exact Result、current full suite | accepted scope、supported answer、Limitation、Web/Citation 全部保持且无新 fallback | not-executed | NOT-RUN / blocking |
| V-REFLECT-002 | Slice2 根据跨工程、通用合同、安全和回归证据复盘 A1—A4 | architecture / reflection | Slice1/2 exact Result、A1—A5、Findings、用户新决策收据 | A1—A4 exact Verdict；A5 early signal；完整决定为 CONTINUE、REDIRECT 或 REJECT | not-executed | NOT-RUN / blocking |
| V-HIDDEN-003 | Slice3 用两个最终未见工程的 4 answerable + 2 boundary 验证泛化 | product / independent-hidden | product code freeze 后用户披露的 exact projects/suite；至少 2 multi-method、3 no-symbol、2 boundary | answerable 4/4 supported、boundary 2/2、重大错误 0、披露后产品变化=0 | not-executed | NOT-RUN / blocking |
| V-COMP-001 | 最终 World Model Web 逐题不低于成熟源码 Agent并达到正向价值阈值 | product / comparison | 同 revision/问题/资源、Agent sealed baseline、冻结 rubric/cache/value protocol | 逐 Need/Claim 不退步、重大错误 0、ratio-ppm at-most 250000、exact report 可重放 | not-executed | NOT-RUN / blocking |
| V-SEC-003 | 最终产品链保持全部授权与安全边界 | security / product | final hidden/live sessions、operation/Gateway/transport/Citation audit | Source/Update/Direct fallback=0、secret exposure=0、hidden retry=0、loopback only、Review 独立 | not-executed | NOT-RUN / blocking |
| V-XD-003 | `ITER-006-RESULT-ACCEPTANCE` 与 `ITER-009-SLICE-003` 在最终问题中组合 | product / integration | final hidden 无符号多方法题、accepted declaration/`CALLS`、accepted candidate evidence/review protocol | 同一正式答案链组合旧+新能力并由 Citation 支持 | not-executed | NOT-RUN / blocking |
| V-WEB-003 | Slice3 从同一正式 Web 执行 `V-XD-003` 与最终 hidden suite | product / browser | exact frozen product Web、final hidden 4+2、run-specific authorization | 页面交付答案或正确 Limitation/Citation；console clean；与内部测试同一产品链 | not-executed | NOT-RUN / blocking |
| V-ADHOC-001 | 用户在 Slice3 从正式 Web 提出两条现场问题并执行 `V-XD-003` | product / browser | product freeze 后用户现场题；至少一条无符号且跨域 | answerable supported，真实 boundary 正确；Citation 可核对；无 fallback | not-executed | NOT-RUN / blocking |
| V-REGRESSION-003 | 最终候选保持 accepted 能力、Slice1/2 产品结果和完整回归 | regression / product | prior accepted oracles、两个 Slice Result、current full suite | 无新增失败、能力降级、Direct 兜底或测试/正式 Web 链分叉 | not-executed | NOT-RUN / blocking |
| V-009 | 本机验证和 Acceptance 不产生 Production Activation | activation | exact final Iteration Result | NOT_EXECUTED | not-executed | NOT-RUN / blocking |
| V-REFLECT-003 | 最终复盘 A1—A5 并由用户决定接受、转向或拒绝 | architecture / reflection | 三个 exact Slice Result、4+2、现场题、Agent 对照、价值/成本/时延、安全、全部 Findings | A1—A5 exact Verdict；只有全部 SUPPORTED 与用户新 ACCEPT 收据才能申请 Acceptance | not-executed | NOT-RUN / blocking |

## Freeze and scoring rules

- `V-PREVIEW-001` 只决定方向，不是 Acceptance evidence；它必须早于全面夯实，但运行安全与 exact authorization 不得延后。
- Slice2 early canary 与最终 4+2 互不复用，且都在所属 Slice product code freeze 后才由用户披露；披露后任何产品变化都会保留失败并烧毁
  该组输入。
- 4 条 answerable 是最终 supported 分母，Gap 不计 PASS；2 条 boundary 单独要求 2/2。
- 成熟源码 Agent 在 World Model 输出前先运行并密封；双方使用同 revision、问题、rubric、资源和 cache policy。质量调用次数不因配额
  目标削减。
- 每个 `V-REFLECT` PASS 只表示复盘完整。`SLICE-001/002` 需要新的 `CONTINUE` 才能授权下一段；最终需要新的 `ACCEPT` 才能接受迭代。
- 最终 Product Result 必须逐 Case 绑定三个唯一 Slice Result；测试数量、模型调用成功、静态回放或旧资格不能替代。
