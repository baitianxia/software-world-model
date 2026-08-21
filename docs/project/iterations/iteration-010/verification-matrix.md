---
id: ITER-010-VERIFICATION
kind: iteration-verification
status: not-run
authority: planned-verification
owners: [quality]
depends_on: [ITER-010-PROPOSAL]
code: []
tests: []
iteration: ITER-010
product_goal_gate: V-000
product_goal_outcome: user-visible-general-engineering-qa-delta
product_goal_evaluation: independent-hidden-plus-live-ad-hoc
product_goal_result_id: not-executed
---

# ITER-010 Verification Matrix

| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |
|---|---|---|---|---|---|---|
| V-000 | 本轮相对 rejected baseline 可测缩短通用工程问答差距并累计复用既有 World Model 能力 | product / comparison | 三个唯一 Slice Result；最终隐藏 10+2；现场题；成熟源码 Agent；预提交 reuse-value protocol | 重大错误 0；逐结论不退步；价值阈值 PASS；同一 Web 直接回答、层级匹配、Citation 正确；Source 只在 retrieval worker | not-executed | NOT-RUN / blocking |
| V-PRE-001 | exact product baseline 与 ITER-009 rejected 产品结论被准确分离 | readiness / baseline | commit `1fb997bab6444523f82ebf1a514a1abbf79656c7`、tree `1369ce932c778c57a118123e8257ede476229d73`、predecessor Result | 技术资产复用；不继承 Acceptance/live grant/qualification；dirty baseline 禁止 | Git object/tree/branch inspection；Proposal/Manifest/Readiness | PASS / readiness blocking |
| V-PRE-002 | ITER-009 用户反馈被判为系统性架构/产品方向证据而非单题文风 | readiness / evidence | `ITER-009-RESULT-SLICE-001-STOP-REDIRECT`、ROADMAP Candidate、现场答案与用户裁决 | baseline gap 是默认实现走读、Reviewer 层级 Gate 缺失和 Source-off 通用问答边界，不按个别问题修 Prompt | Proposal Trigger、Result、Candidate | PASS / readiness blocking |
| V-PRE-003 | ENGINEERING_QA、严格 WORLD_MODEL 和显式 DIRECT 三种模式的迁移顺序已冻结 | readiness / architecture | ADR-013/014/015、新 ADR-016 target、owning Contract list、V-ARCH-001 | 先 Finding/ADR/Contract/docs gate，后产品实现；无 silent fallback；严格 WORLD_MODEL 保留 | Proposal、Readiness、Slice1 Phase0 | PASS / readiness blocking |
| V-PRE-004 | 初始授权没有扩大 live、Source disclosure、credential、Provider、browser、hidden 或 Production 权限 | readiness / security | planning receipt `1b327024…`、architecture receipt `5cdb7000…`、Manifest authorization | 只允许 System/governance/product code 与本地确定性测试；所有 live/disclosure 另取 exact grant | Readiness、Manifest、Slice1 相同禁止面 | PASS / readiness blocking |
| V-PRE-005 | hidden、成熟 Agent、reuse-value、burn 和 direction-preview 规则在编码前冻结 | readiness / comparison | final 10+2、early 5+2；原样复用 ITER-009 已由 `6ca47f7d…` 接受的 Agent/rubric/cache/value protocol、ratio-ppm at-most 250000、reuse horizon 12 | 首段 preview 可先执行；后续 hidden/comparison 不能取消；协议未重命名，披露后产品变化烧毁输入 | Proposal、Manifest bindings | PASS / readiness blocking |
| V-PRE-006 | A1—A5、逐 Slice Reflection、混合协议资源/质量边界和 current fileset 可机械核对 | readiness / architecture | Proposal assumption catalog、Manifest bindings、System fileset、answer_protocol | 假设累积；每项 deferred 有 early falsifier；调用/资源为高安全上限且不得削减 checklist/evidence/review | Proposal、Manifest、Readiness、docs gate | PASS / readiness blocking |
| V-BASELINE-001 | Slice1 实际开发 subject 仍是 exact baseline 且没有未记录产品变化 | development / baseline | Git ancestry/tree、worktree、predecessor Result | baseline 可复现；任何变化归属 Slice1；旧运行 identity 不继承 | not-executed | NOT-RUN / blocking |
| V-ARCH-001 | 新模式先取得正式架构与 Contract Owner，旧模式边界不被静默改写 | architecture / contract | FINDING-010-001、SYS-ADR-016、Product Success、runtime/Agentic/Evidence/World Model/Response/Source/Security/Browser、Manifest fileset、docs gate/tests | ENGINEERING_QA 明确为 upfront hybrid；strict WORLD_MODEL source-off 与 DIRECT identity 保留；所有 current docs/code mapping 一致 | not-executed | NOT-RUN / blocking |
| V-QINTENT-001 | Question Understanding 忠实表达用户目标、受众、抽象层级、物质结论和证据需求 | application / contract | 用途/架构/运行/故障/影响/实现、多条件、改述、不同受众 fixture | 原问题约束不丢失/新增；无题型/工程/关键词/符号路由；输出 schema 可审计 | not-executed | NOT-RUN / blocking |
| V-HYBRID-001 | 原 checklist 与 Snapshot hints 共同形成 upfront 检索并密封混合 Evidence Package | application / integration | relevant/partial/zero/irrelevant Snapshot；exact revision source/docs/config/tests；conflict fixture | World Model 提示/缩小候选但不是 recall Gate；zero/irrelevant Snapshot 不阻断受控 Source；一个包保留完整 provenance/conflict | not-executed | NOT-RUN / blocking |
| V-ISOLATION-001 | retrieval worker、Answer 与 Reviewer 权限物理/应用隔离 | security / isolation | source injection、path/symlink/write/exec/network/secret probes；role package/import/mount audit | worker 仅 allowlisted read；Source 视为不可信；Answer/Reviewer repo/source/tool attempt=0；非法动作失败关闭 | not-executed | NOT-RUN / blocking |
| V-ANSWER-001 | Preview 跨类型问题先给直接、层级匹配的答案，代码细节按需 | product / answer | 一个真实工程 4 条不同覆盖维度问题、exact Package、结论级 rubric | 至少 3 supported 且覆盖至少 2 个非实现维度；重大错误 0；每个物质结论 Citation；无内部诊断平铺 | not-executed | NOT-RUN / blocking |
| V-REVIEW-001 | 独立 Reviewer 阻断未直接回答、层级错误、遗漏、无关、不可用和 grounding/Citation 缺口 | application / review | 对抗 Draft fixture、original question、Question Understanding、sealed Package | 每类偏差返回具体 finding/action；Slice1 未实现自动修复时失败关闭；无笼统 code 放行 | not-executed | NOT-RUN / blocking |
| V-LIMIT-001 | Preview 在证据不足时交付诚实 limitation 或失败关闭 | application / boundary | 可回答、证据不足、预算耗尽 fixture | 不伪造、不把未查到写成不存在；完整补检索/重封/重答/重审生命周期留给 V-RERETRIEVE-002 | not-executed | NOT-RUN / blocking |
| V-SEC-001 | Slice1 exact revision、allowlist、untrusted Source、Provider disclosure、Secret、预算与 Web 安全成立 | security / integration | drift、oversize、injection、unauthorized fragment/provider、review tamper、outcome unknown、non-loopback probes | 全部失败关闭；request retry/provider switch/source write/update/silent fallback=0；合法本地确定性路径完成 | not-executed | NOT-RUN / blocking |
| V-XD-001 | 同一 ENGINEERING_QA 答案组合 ITER-006 accepted Snapshot 知识与 query-time 新来源 Evidence | product / integration | declaration/`CALLS` Result + repository document/config/test/source conclusion；无符号自然问题 | 一个 Package、一个 Draft/Review/Delivery；结论分别绑定正确来源；不是两个正文拼接 | not-executed | NOT-RUN / blocking |
| V-WEB-001 | Slice1 从真实 product-owned ENGINEERING_QA loopback Web 执行 V-XD-001 | product / browser | exact freeze/live grant、普通用户无认证、4 条任务和至少一条现场题 | 页面交付答案/limitation与可打开 Citation；诊断折叠；console clean；非回放/CLI/validation-only | not-executed | NOT-RUN / blocking |
| V-PREVIEW-001 | 在全面夯实前取得真实用户方向裁决 | product / directional-preview | V-WEB-001、4 个不同覆盖维度、现场题、非验收/非生产标识 | 用户能判断是否像工程问答助手并决定 CONTINUE/REDIRECT/REJECT | not-executed | NOT-RUN / blocking |
| V-REFLECT-001 | Slice1 复盘架构迁移、真实 preview 和 A1—A3 | architecture / reflection | Slice1 exact Result、A1—A5、owned Cases、Findings、用户新 decision receipt | A1—A3 exact Verdict；A4/A5 early signal；完整决策 CONTINUE/REDIRECT/REJECT | not-executed | NOT-RUN / blocking |
| V-GENERAL-002 | 同一协议跨第二工程、不同命名/结构/来源仍不依赖特判 | product / generalization | 第二真实工程、改述、不同目录/框架、source/doc/config/test mixes | 问题层级正确；无 project/question/keyword/symbol/class/method/fixture/oracle branch | not-executed | NOT-RUN / blocking |
| V-RERETRIEVE-002 | rewrite、补检索、新包与重新审核生命周期机械闭合 | application / contract | omission、unsupported inference、citation gap、specific evidence gap、no-progress cases | 同包最多一次 rewrite；补检索最多一次且重封；每个 final Draft 绑定当前包 Review；不可修复关闭 | not-executed | NOT-RUN / blocking |
| V-ASYNC-002 | 知识沉淀不阻塞或改写当前问答 | application / knowledge | approved Package/Answer、async proposal success/reject/failure | Delivery 独立完成；异步路径重新走 Update/Admission/Publication；任何结果不追认/撤销原答案 | not-executed | NOT-RUN / blocking |
| V-HARDEN-002 | Package、coverage、conflict、pagination、预算、revision 和 trace 上界闭合 | application / reliability | truncation/pagination/conflict/oversize/cycle/drift/stale package/ref matrix | 无漏页、越权、无界循环、旧包审批或伪完整；超限准确 limitation 或 fail closed | not-executed | NOT-RUN / blocking |
| V-SEC-002 | 第二段保持 Source/role/Provider/Secret/loopback 与 no-retry 隔离 | security / integration | 合法/非法 end-to-end probes、Gateway disclosure/transport audit | 合法路径完成；非法全部失败关闭；Answer/Reviewer source=0，write/update/fallback/retry/secret exposure=0 | not-executed | NOT-RUN / blocking |
| V-XD-002 | 第二工程同一答案组合 accepted Snapshot 与本轮多来源 Evidence | product / integration | accepted declaration/`CALLS` + new doc/config/test/source evidence、无符号题 | 同一 answer/limitation 和 Citation 完成真实组合 | not-executed | NOT-RUN / blocking |
| V-WEB-002 | Slice2 从同一真实 Web 执行 V-XD-002 | product / browser | product-owned loopback Web、第二工程、exact qualification/run grant | answerable/boundary 用户可见；Citation 可核对；无平行入口 | not-executed | NOT-RUN / blocking |
| V-CANARY-002 | Slice2 通过独立第二工程 5 answerable + 2 boundary canary | product / independent-hidden | Slice2 code freeze 后用户披露 exact project/suite；burn rule | 5/5 supported、2/2 boundary、重大错误 0、无特判；披露后产品变化=0 | not-executed | NOT-RUN / blocking |
| V-NEG-EARLY-002 | bounded absence 与 coverage limitation 在第二工程保持区分 | product / early falsification | canary 两类 boundary、不同命名/入口/同义改述 | 三层完整才 absence；否则具体 limitation；无关证据 FAIL | not-executed | NOT-RUN / blocking |
| V-COMP-EARLY-002 | 正式验收前与成熟源码 Agent 比较质量并测量 World Model 复用价值 | product / comparison | canary same revision/questions、frozen Agent/rubric/cache/value、Agent first sealed | 重大错误 0、逐结论不退步、source-exposure ratio-ppm at-most 250000；报告可重放 | not-executed | NOT-RUN / blocking |
| V-DIAG-002 | 对同一问题逐层定位首次偏差 | architecture / diagnostic | Source truth、World Model、Question Understanding、retrieval、Package、Draft、Review、Web exact refs | 每层独立 verdict；首次偏差决定分类；不从最终答案猜根因 | not-executed | NOT-RUN / blocking |
| V-REGRESSION-002 | accepted scope、strict WORLD_MODEL、DIRECT 与 Preview 主线无退步 | regression / product | ITER-003—006 accepted oracles、Slice1 Result、current full suite | accepted behavior与三模式隔离保持；无新增 fallback/入口分叉 | not-executed | NOT-RUN / blocking |
| V-REFLECT-002 | Slice2 复盘跨工程、合同、安全、Agent/value 与 A1—A4 | architecture / reflection | Slice1/2 Results、A1—A5、Findings、用户新 decision receipt | A1—A4 exact Verdict；A5 early verdict；CONTINUE/REDIRECT/REJECT | not-executed | NOT-RUN / blocking |
| V-HIDDEN-003 | 最终两个未见工程 10 answerable + 2 boundary 验证泛化 | product / independent-hidden | final code freeze 后用户披露 exact projects/suite；至少 8 no-symbol、每工程至少 3 | answerable 10/10、boundary 2/2、重大错误 0、披露后产品变化=0 | not-executed | NOT-RUN / blocking |
| V-COMP-001 | 最终 ENGINEERING_QA 不低于成熟源码 Agent 且证明复用价值 | product / comparison | same revision/questions/resources、Agent sealed baseline、frozen rubric/cache/value protocol | 逐结论不退步、重大错误 0、ratio-ppm at-most 250000、exact report 可重放 | not-executed | NOT-RUN / blocking |
| V-SEC-003 | 最终产品链保持全部授权、安全、role 和 disclosure 边界 | security / product | final hidden/live sessions、source/Gateway/transport/package/Citation audit | Source only retrieval worker；Answer/Reviewer source=0；write/update/fallback/secret/hidden retry=0；loopback | not-executed | NOT-RUN / blocking |
| V-XD-003 | 最终问题在同一答案链组合 accepted Snapshot 与多来源 Evidence | product / integration | final hidden no-symbol cross-source question、accepted Result、新 protocol | 同一正式答案和 Citation 支持旧+新能力 | not-executed | NOT-RUN / blocking |
| V-WEB-003 | Slice3 从同一正式 ENGINEERING_QA Web 执行 final suite | product / browser | exact frozen Web、final 10+2、run grant | 页面交付答案/limitation/Citation；console clean；与内部链相同 | not-executed | NOT-RUN / blocking |
| V-ADHOC-001 | 用户从正式 Web 提出两条现场问题 | product / browser | product freeze 后现场题；至少一条 no-symbol 且跨域 | answerable supported；真实 boundary 正确；Citation 可核对；无 fallback | not-executed | NOT-RUN / blocking |
| V-REGRESSION-003 | 最终候选保持 accepted scope与 Slice1/2 结果 | regression / product | prior oracles、两个 Slice Results、full suite | 无新增失败、能力降级、source leak 或三模式分叉 | not-executed | NOT-RUN / blocking |
| V-010 | 本机验证和 Acceptance 不产生 Production Activation | activation | exact final Iteration Result | NOT_EXECUTED | not-executed | NOT-RUN / blocking |
| V-REFLECT-003 | 最终复盘 A1—A5 并由用户裁决 | architecture / reflection | 三个 exact Slice Results、10+2、现场题、Agent/value、安全、Findings | A1—A5 exact Verdict；只有全部 SUPPORTED 与用户新 ACCEPT 才能申请 Acceptance | not-executed | NOT-RUN / blocking |

## Freeze and scoring rules

- Slice1 preview 使用一个真实工程 4 条不同覆盖维度问题和至少一条现场题；至少 3 supported、至少 2 个非实现维度。它只决定方向。
- Slice2 early canary 与最终 10+2 互不复用，在所属 Slice code freeze 后由用户披露；披露后任何产品/Prompt/schema/route/disclosure 改动
  烧毁输入并保留失败 Result。
- 最终 10 条 answerable 是 supported 分母，Gap 不计 PASS；2 条 boundary 单独要求 2/2。
- 成熟源码 Agent 先运行并密封；同 revision、问题、rubric 和资源。World Model reuse metric 只在质量 Gate 已满足后裁决，不能用降低
  Source bytes 或模型调用换取错误/遗漏。
- 调用次数和成本不构成质量裁剪目标；高安全上限触发失败关闭，不能删除 checklist、Evidence、Citation 或独立 Review。
- 每个 `V-REFLECT` PASS 只表示复盘完整。Slice1/2 需要新的 `CONTINUE` 才能授权下一段；最终需要新的 `ACCEPT` 才能接受迭代。
- Product Result 必须聚合三个唯一 Slice Result；测试数量、模型调用成功、旧 Web result 或旧资格不能替代。
