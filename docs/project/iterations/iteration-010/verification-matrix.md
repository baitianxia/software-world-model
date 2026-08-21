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
| V-000 | 本轮相对 rejected baseline 可测缩短通用工程问答差距并证明完整 World Model Cognition 的独立价值 | product / comparison | 三个唯一 Slice Result；最终隐藏 10+2；现场题；完整认知、locator-only/empty 同链、成熟源码 Agent 三臂；新收据预提交 protocol | 完整认知与成熟 Agent 先过零重大错误/boundary/逐结论质量门；完整认知再相对 locator control 达到预提交质量或非 locator 调查成本增益；计建模成本/复用周期；同一 Web/Citation/Source 隔离成立 | not-executed | NOT-RUN / blocking |
| V-PRE-001 | exact product baseline 与 ITER-009 rejected 产品结论被准确分离 | readiness / baseline | commit `1fb997bab6444523f82ebf1a514a1abbf79656c7`、tree `1369ce932c778c57a118123e8257ede476229d73`、predecessor Result | 技术资产复用；不继承 Acceptance/live grant/qualification；dirty baseline 禁止 | Git object/tree/branch inspection；Proposal/Manifest/Readiness | PASS / readiness blocking |
| V-PRE-002 | ITER-009 用户反馈被判为系统性架构/产品方向证据而非单题文风 | readiness / evidence | `ITER-009-RESULT-SLICE-001-STOP-REDIRECT`、ROADMAP Candidate、现场答案与用户裁决 | baseline gap 是默认实现走读、Reviewer 层级 Gate 缺失和 Source-off 通用问答边界，不按个别问题修 Prompt | Proposal Trigger、Result、Candidate | PASS / readiness blocking |
| V-PRE-003 | ENGINEERING_QA、严格 WORLD_MODEL 和显式 DIRECT 三种模式及新自适应调查职责已冻结 | readiness / architecture | FINDING-010-002、ADR-013/014/015/016、owning Contract list、V-ARCH-001 | World Model 概念不变；ENGINEERING_QA 使用 Investigation→Broker/Worker→Ledger→seal→Answer/Review；无 silent fallback | Proposal、Readiness、Slice1 Phase0 | PASS / readiness blocking |
| V-PRE-004 | 最新收据只授权重制计划，没有扩大产品代码、live、Source disclosure、credential、Provider、browser、hidden 或 Production 权限 | readiness / authorization | planning receipt `d3b60bda…`、此前设计绑定的 `1b327024… + 5cdb7000…`、Manifest authorization | 所有 Slice proposed/coding false；active slice none；产品开发与所有 live/disclosure 另取授权 | Readiness、Manifest、Current、Slice1 | PASS / readiness blocking |
| V-PRE-005 | hidden、成熟 Agent 历史输入、三臂消融授权边界、burn 和方向体验顺序明确 | readiness / comparison | final 10+2、early 5+2；旧 `6ca47f7d…` Agent/rubric/cache/source-bytes protocol；新增 `engineering_qa_ablation` proposed mapping | 首段 preview 可先执行；新三臂 protocol/digest/阈值不得伪用旧收据，Slice2 前须新用户收据；披露后产品变化烧毁输入 | Proposal、Manifest bindings | PASS / readiness blocking |
| V-PRE-006 | A1—A5、逐 Slice Reflection、自适应调查、证据分区、独立补证调查和资源/质量边界可机械核对 | readiness / architecture | Proposal assumption catalog、Manifest 三 nested mappings、System fileset、answer_protocol | prior-result/Broker/Ledger/seal 精确；support/citation 与 boundary/audit 不混；Slice1 仅 preview 一次补证，后续无永久一轮上限；answerable 超限 FAIL | Proposal、Manifest、Readiness、docs gate | PASS / readiness blocking |
| V-BASELINE-001 | Slice1 实际开发 subject 仍是 exact baseline 且没有未记录产品变化 | development / baseline | Git ancestry/tree、worktree、predecessor Result | baseline 可复现；任何变化归属 Slice1；旧运行 identity 不继承 | not-executed | NOT-RUN / blocking |
| V-ARCH-001 | 新模式先取得正式架构与 Contract Owner，世界模型概念及旧模式边界不被静默改写 | architecture / contract | FINDING-010-001/002、SYS-ADR-016、Product Success、runtime/Agentic/Evidence/World Model/Response/Source/Security/Browser、Manifest fileset、docs gate/tests | ENGINEERING_QA 明确为 adaptive investigation；World Model 保持持久外部认知；strict WORLD_MODEL source-off 与 DIRECT identity 保留 | not-executed | NOT-RUN / blocking |
| V-QINTENT-001 | Question Understanding 忠实表达用户目标、受众、抽象层级、物质结论和证据需求 | application / contract | 用途/架构/运行/故障/影响/实现、多条件、改述、不同受众 fixture | 原问题约束不丢失/新增；无题型/工程/关键词/符号路由；输出 schema 可审计 | not-executed | NOT-RUN / blocking |
| V-COGNITION-001 | World Model 作为 exact、持久、版本化、可验证、可更新的软件外部认知进入问答 | architecture / knowledge | context/scope/schema/snapshot、实体/关系/行为/约束/状态/evidence/coverage/unknown fixtures | 手册/地图只作为投影；认知不退化为 cache/hints；coverage 不足不成为 Source recall Gate | not-executed | NOT-RUN / blocking |
| V-INVESTIGATE-001 | Investigation LLM 根据 prior Ledger Result 自适应提出下一步并合法结束 | application / investigation | 至少两步依赖链、partial/zero cognition、no-progress、premature finish、改述 fixture | 每步引用 prior result/progress；不是 upfront 固定计划；无题目/工程/关键词/符号/类/方法/fixture/oracle 分支 | not-executed | NOT-RUN / blocking |
| V-BROKER-001 | Source Broker/Worker 在模型无直接 Source 权限下编译并执行受控读操作 | security / integration | 合法抽象 proposal、path/symlink/write/exec/network/secret/disclosure probes、exact revision drift | Broker policy 决定唯一合法操作；Worker execution only；所有模型 direct FS/Shell/network/credential/source=0；完整操作/bytes/outcome audit | not-executed | NOT-RUN / blocking |
| V-LEDGER-001 | Evidence Ledger 只追加，调查结束后才密封双分区 Package，identity 与 seal 语义正确 | application / evidence | append/overwrite、finish/stop、admissible/rejected、gap/failure/partial/conflict/unknown、old/new revision fixtures | 历史不可改；未 finish 不 seal；support/citation 仅 admissible；boundary/audit 强制保留且不得支持肯定 Claim；seal 非 truth；旧 Review 不批新包 | not-executed | NOT-RUN / blocking |
| V-ISOLATION-001 | Investigation、Answer、Reviewer 与实际 Source 权限物理/应用隔离 | security / isolation | source injection、path/write/exec/network/secret probes；role package/import/mount audit | 只有 Broker/Worker 受控读；Source untrusted；Investigation/Answer/Reviewer 直接 repo/source/tool access=0；非法动作失败关闭 | not-executed | NOT-RUN / blocking |
| V-ANSWER-001 | Preview 跨类型问题先给直接、层级匹配的答案，代码细节按需 | product / answer | 一个真实工程 4 条不同覆盖维度问题、exact Package、结论级 rubric | 至少 3 supported 且覆盖至少 2 个非实现维度；重大错误 0；每个物质结论 Citation；无内部诊断平铺 | not-executed | NOT-RUN / blocking |
| V-REVIEW-001 | Reviewer 阻断缺陷并以具体 gap 启动独立 Verification Investigation | application / review | 对抗 Draft、current Package/Ledger、specific/invalid gap、两步结果驱动补证 fixture | Reviewer 不提可执行操作；新调查用新上下文读 gap+current Package/Ledger，经 Application/Broker/Worker 多步适应；不回初始调查；新包重答重审 | not-executed | NOT-RUN / blocking |
| V-LIMIT-001 | Preview 在调查或证据不足、安全熔断耗尽时保持诚实 | application / boundary | 可回答、证据不足、合法补证、无进展、上限耗尽、answerable/boundary fixture | 不伪造、不把未查到写成不存在；Slice1 最多一次补证；answerable 因熔断未回答计 FAIL；boundary 仅可独立审核 Limitation 或 fail closed | not-executed | NOT-RUN / blocking |
| V-SEC-001 | Slice1 exact revision、allowlist、untrusted Source、Provider disclosure、Secret、预算与 Web 安全成立 | security / integration | drift、oversize、injection、unauthorized fragment/provider、review tamper、outcome unknown、non-loopback probes | 全部失败关闭；request retry/provider switch/source write/update/silent fallback=0；合法本地确定性路径完成 | not-executed | NOT-RUN / blocking |
| V-XD-001 | 同一 ENGINEERING_QA 答案组合 ITER-006 accepted World Model 认知与 query-time 新来源 Evidence | product / integration | declaration/`CALLS` Result + repository document/config/test/source conclusion；无符号自然问题 | 同一 Ledger/Package/Answer/Review；结论分别绑定正确来源；不是两个正文或模式拼接 | not-executed | NOT-RUN / blocking |
| V-WEB-000 | Slice1 在完整夯实前交付最早可体验的真实 Web 微纵切 | product / browser | exact freeze/live grant、普通用户无认证、一条 World Model + query-time Source 代表问题 | 最小真实链可用；exact revision/read-only/untrusted Source/support-citation 分区/Citation/独立 Review 全部成立；非回放/CLI | not-executed | NOT-RUN / blocking |
| V-WEB-001 | 微纵切后从同一 product-owned ENGINEERING_QA loopback Web 执行完整方向体验 | product / browser | V-WEB-000 后 exact freeze/live grant、4 条任务和至少一条现场题 | 页面交付答案/limitation与可打开 Citation；诊断折叠；console clean；持久恢复/复杂矩阵未完成不冒充 Acceptance | not-executed | NOT-RUN / blocking |
| V-PREVIEW-001 | 在全面夯实前取得真实用户方向裁决 | product / directional-preview | V-WEB-001、4 个不同覆盖维度、现场题、非验收/非生产标识 | 用户能判断是否像工程问答助手并决定 CONTINUE/REDIRECT/REJECT | not-executed | NOT-RUN / blocking |
| V-REFLECT-001 | Slice1 复盘架构迁移、真实 preview 和 A1—A3 | architecture / reflection | Slice1 exact Result、A1—A5、owned Cases、Findings、用户新 decision receipt | A1—A3 exact Verdict；A4/A5 early signal；完整决策 CONTINUE/REDIRECT/REJECT | not-executed | NOT-RUN / blocking |
| V-GENERAL-002 | 同一协议跨第二工程、不同命名/结构/来源仍不依赖特判 | product / generalization | 第二真实工程、改述、不同目录/框架、source/doc/config/test mixes | 问题层级正确；无 project/question/keyword/symbol/class/method/fixture/oracle branch | not-executed | NOT-RUN / blocking |
| V-RERETRIEVE-002 | 独立补证调查在复杂 gap、冲突、重复和 no-progress 上机械夯实 | application / contract | omission、unsupported inference、citation gap、specific/duplicate/conflicting gap、持久恢复、no-progress cases | 新上下文读 gap+Package/Ledger 并多步结果驱动；不回初始调查；同包 rewrite/新包严格区分；去重恢复正确；不可修复关闭 | not-executed | NOT-RUN / blocking |
| V-ASYNC-002 | 知识沉淀不阻塞或改写当前问答 | application / knowledge | approved Package/Answer、async proposal success/reject/failure | Delivery 独立完成；异步路径重新走 Update/Admission/Publication；任何结果不追认/撤销原答案 | not-executed | NOT-RUN / blocking |
| V-HARDEN-002 | Investigation/Verification Investigation、持久 Ledger/Package、coverage/conflict/dedup 和安全熔断闭合 | application / reliability | recovery/truncation/pagination/conflict/oversize/cycle/no-progress/drift/stale package；revision/call/ops/bytes/wall-time/no-progress fuses | 无漏页、越权、无界循环、历史回写、旧包审批或伪完整；无永久一轮补证 cap；answerable 超限 FAIL，boundary 准确 limitation 或 fail closed | not-executed | NOT-RUN / blocking |
| V-SEC-002 | 第二段保持 Source/role/Provider/Secret/loopback 与 no-retry 隔离 | security / integration | 合法/非法 end-to-end probes、Gateway disclosure/transport audit | 合法路径完成；非法全部失败关闭；模型 direct source/FS/Shell/network=0，write/update/fallback/retry/secret exposure=0 | not-executed | NOT-RUN / blocking |
| V-XD-002 | 第二工程同一答案组合 accepted Snapshot 与本轮多来源 Evidence | product / integration | accepted declaration/`CALLS` + new doc/config/test/source evidence、无符号题 | 同一 answer/limitation 和 Citation 完成真实组合 | not-executed | NOT-RUN / blocking |
| V-WEB-002 | Slice2 从同一真实 Web 执行 V-XD-002 | product / browser | product-owned loopback Web、第二工程、exact qualification/run grant | answerable/boundary 用户可见；Citation 可核对；无平行入口 | not-executed | NOT-RUN / blocking |
| V-CANARY-002 | Slice2 通过独立第二工程 5 answerable + 2 boundary canary | product / independent-hidden | Slice2 code freeze 后用户披露 exact project/suite；burn rule | 5/5 supported、2/2 boundary、重大错误 0、无特判；披露后产品变化=0 | not-executed | NOT-RUN / blocking |
| V-NEG-EARLY-002 | bounded absence 与 coverage limitation 在第二工程保持区分 | product / early falsification | canary 两类 boundary、不同命名/入口/同义改述 | 三层完整才 absence；否则具体 limitation；无关证据 FAIL | not-executed | NOT-RUN / blocking |
| V-COMP-EARLY-002 | 正式验收前用三臂同题消融判断完整 World Model Cognition 的独立价值 | product / comparison | 新用户收据冻结 protocol；完整 Cognition、locator-only/empty 同链、成熟 Agent；same revision/model/questions/budget/cache/rubric；Agent first sealed | 完整认知与成熟 Agent 零重大错误/boundary 正确且完整认知逐结论不退步；再相对 locator control 达预提交质量或 non-locator cost 增益；计建模成本/复用周期 | not-executed | NOT-RUN / blocking |
| V-DIAG-002 | 对同一问题逐层定位首次偏差 | architecture / diagnostic | Source observation、World Model Cognition、Question Understanding、Investigation、Broker/Worker、Ledger/Package、Draft、Review、Web exact refs | 每层独立 verdict；首次偏差决定分类；不从最终答案猜根因 | not-executed | NOT-RUN / blocking |
| V-REGRESSION-002 | accepted scope、strict WORLD_MODEL、DIRECT 与 Preview 主线无退步 | regression / product | ITER-003—006 accepted oracles、Slice1 Result、current full suite | accepted behavior与三模式隔离保持；无新增 fallback/入口分叉 | not-executed | NOT-RUN / blocking |
| V-REFLECT-002 | Slice2 复盘跨工程、合同、安全、Agent/value 与 A1—A4 | architecture / reflection | Slice1/2 Results、A1—A5、Findings、用户新 decision receipt | A1—A4 exact Verdict；A5 early verdict；CONTINUE/REDIRECT/REJECT | not-executed | NOT-RUN / blocking |
| V-HIDDEN-003 | 最终两个未见工程 10 answerable + 2 boundary 验证泛化 | product / independent-hidden | final code freeze 后用户披露 exact projects/suite；至少 8 no-symbol、每工程至少 3 | answerable 10/10、boundary 2/2、重大错误 0、披露后产品变化=0 | not-executed | NOT-RUN / blocking |
| V-COMP-001 | 最终三臂消融证明 ENGINEERING_QA 质量与完整 Cognition 增益 | product / comparison | final same revision/model/questions/budget/cache/rubric；完整 Cognition、locator-only/empty 同链、成熟 Agent；frozen ablation protocol | 完整认知与成熟 Agent 先过质量门；完整认知再相对 locator control 达质量或 non-locator cost 增益；建模成本按冻结复用周期摊销；exact report 可重放 | not-executed | NOT-RUN / blocking |
| V-SEC-003 | 最终产品链保持全部授权、安全、role 和 disclosure 边界 | security / product | final hidden/live sessions、source/Gateway/transport/Ledger/package/Citation audit | Source only via Broker/Worker；所有模型 direct source/FS/Shell/network=0；write/update/fallback/secret/hidden retry=0；loopback | not-executed | NOT-RUN / blocking |
| V-XD-003 | 最终问题在同一答案链组合 accepted Snapshot 与多来源 Evidence | product / integration | final hidden no-symbol cross-source question、accepted Result、新 protocol | 同一正式答案和 Citation 支持旧+新能力 | not-executed | NOT-RUN / blocking |
| V-WEB-003 | Slice3 从同一正式 ENGINEERING_QA Web 执行 final suite | product / browser | exact frozen Web、final 10+2、run grant | 页面交付答案/limitation/Citation；console clean；与内部链相同 | not-executed | NOT-RUN / blocking |
| V-ADHOC-001 | 用户从正式 Web 提出两条现场问题 | product / browser | product freeze 后现场题；至少一条 no-symbol 且跨域 | answerable supported；真实 boundary 正确；Citation 可核对；无 fallback | not-executed | NOT-RUN / blocking |
| V-REGRESSION-003 | 最终候选保持 accepted scope与 Slice1/2 结果 | regression / product | prior oracles、两个 Slice Results、full suite | 无新增失败、能力降级、source leak 或三模式分叉 | not-executed | NOT-RUN / blocking |
| V-010 | 本机验证和 Acceptance 不产生 Production Activation | activation | exact final Iteration Result | NOT_EXECUTED | not-executed | NOT-RUN / blocking |
| V-REFLECT-003 | 最终复盘 A1—A5 并由用户裁决 | architecture / reflection | 三个 exact Slice Results、10+2、现场题、Agent/value、安全、Findings | A1—A5 exact Verdict；只有全部 SUPPORTED 与用户新 ACCEPT 才能申请 Acceptance | not-executed | NOT-RUN / blocking |

## Freeze and scoring rules

- Slice1 先执行 V-WEB-000 一题最小真实纵切，再执行一个真实工程 4 条不同覆盖维度问题和至少一条现场题；至少 3 supported、至少 2 个
  非实现维度。exact revision、只读、不可信 Source、Citation、独立 Review 在微检查点不可延后；持久恢复、复杂冲突/去重和完整异常矩阵
  在 `CONTINUE` 后进入 Slice2。
- Slice2 early canary 与最终 10+2 互不复用，在所属 Slice code freeze 后由用户披露；披露后任何产品/Prompt/schema/route/disclosure 改动
  烧毁输入并保留失败 Result。
- 最终 10 条 answerable 是 supported 分母，Gap 不计 PASS；2 条 boundary 单独要求 2/2。
- 新三臂消融当前 `proposed / not authorized`；旧 `6ca47f7d…` 只保留成熟 Agent/rubric/cache/source-bytes 历史输入，不能冻结新增 Arm、
  protocol、digest 或阈值。Slice2 前须新用户收据。执行时三臂同 revision/model/questions、模型与来源 budget、cache policy/state、rubric/
  evaluator；完整认知与成熟 Agent 先过质量 Gate，locator control 失败不能降低完整认知门。增益再按预提交质量或 normalized non-locator
  investigation cost 判定，并单列 World Model build/update/storage/Provider 成本及冻结复用周期。
- Slice1 每题最多一次独立 Verification Investigation 只服务快速 preview。Slice2/3 禁止永久固定一轮，以预密封 package revision、model
  call、Broker operations、source bytes、wall-time、no-progress 熔断控制；answerable 因熔断未答计 FAIL。
- 调用次数和成本不构成质量裁剪目标；高安全上限触发失败关闭，不能删除 checklist、Evidence、Citation 或独立 Review。
- 每个 `V-REFLECT` PASS 只表示复盘完整。Slice1/2 需要新的 `CONTINUE` 才能授权下一段；最终需要新的 `ACCEPT` 才能接受迭代。
- Product Result 必须聚合三个唯一 Slice Result；测试数量、模型调用成功、旧 Web result 或旧资格不能替代。
