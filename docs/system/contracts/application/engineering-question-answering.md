---
id: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
kind: system-contract
status: current
authority: normative
owners: [application, source, quality, security]
depends_on: [SYS-ADR-016, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING, SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/application_services/engineering_question_cognition.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py, src/software_world_model/interface/engineering_qa_source.py, src/software_world_model/interface/engineering_qa_live.py, src/software_world_model/interface/engineering_qa_preview_cli.py, src/software_world_model/interface/engineering_qa_alpha_cli.py, src/software_world_model/interface/engineering_qa_browser.py, src/software_world_model/interface/engineering_qa_browser_ui.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_cognition.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py, tests/test_engineering_qa_source.py, tests/test_engineering_qa_live.py, tests/test_engineering_qa_preview_cli.py, tests/test_engineering_qa_alpha_cli.py, tests/test_engineering_qa_browser.py]
---

# Engineering Question Answering

## Purpose and scope

本契约定义 `ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3`：默认工程问答从 exact 软件世界模型取得持久的系统认知，由独立 Investigation LLM 根据原问题和每一步调查结果自适应决定下一步来源调查，再由受控 Source Broker / Retrieval Worker 执行。调查结束后才密封 Question Evidence Package，Answer 与 Reviewer 在隔离新上下文中只使用该包完成回答与审核。`@3` 在原 checklist 之下增加逐证据的 material observation closure，防止宽泛检查项被一个代表性事实伪闭合。

软件世界模型是软件系统在精确 Scope、Context、Schema 和 Snapshot 上持久、版本化、可验证、可更新的外部认知模型，独立于任何 LLM 会话或隐藏状态。它不是手册、地图或缓存；这些只是面向人、UI 或特定任务的投影。本契约改变的是问答使用认知和来源的方式，不改变世界模型的定义、正式知识路径或 `WORLD_MODEL` 的 Source-off 语义。

`ENGINEERING_QA` 是独立 Application 用例，不是 `WORLD_MODEL` 的回源分支，也不是 Knowledge Gap 后静默调用 `DIRECT_INVESTIGATION`。严格世界模型问答和直接调查继续由各自契约拥有。

## Ownership

- Application 拥有 immutable Engineering Question Request、Question Understanding Revision、Question Checklist、World Model Cognition Context、Investigation Attempt、Evidence Ledger/Revision、Question Evidence Package/Revision、恢复决定和不可变 Result。
- Knowledge Use / View 拥有 exact Snapshot 的正式查询结果、Coverage、Conflict 与 Unknown；它不拥有来源权限，也不决定调查是否结束。
- Question Understanding LLM 只提交对原问题的结构化理解 Proposal；初始 Investigation LLM 只提交 Investigation Step 和 Finish Proposal；独立 Verification Investigation LLM 只针对 Reviewer 的具体 gap 提交新的自适应 Step/Finish Proposal。三者都不拥有来源操作、Ledger、Package、事实、权限或答案放行，后者不得复用初始调查或 Reviewer 会话。
- Source Broker 拥有 Proposal 的策略校验、registered operation 编译与单次执行授权；隔离 Retrieval Worker 只执行 Broker 已批准的 exact-revision 只读操作。两者都不拥有问题结论、Package 密封或答案。
- Response Control 拥有 Draft Revision、Review Attempt/Decision、Authorization 和 Delivery。Reviewer 只提交 Review / Verification Request Proposal，不能执行补证或自行放行。

## Request and role boundary

1. Request 在任何 World Model 查询、来源读取或模型调用前固定 `ENGINEERING_QA`、protocol identity、original question、response language、exact repository/Binding/revision、source path/content allowlist、Binding-scoped versioned Source Profile ref/digest、World Model Snapshot/Read Set selector、registered operation set、访问权限、高安全资源熔断、Provider disclosure policy 和不可变请求摘要。Source Profile 由受信配置拥有 evidence class → path capability；模型、问题和来源内容不能创建或修改分类。`CURRENT`/`latest` 只能在入口解析一次；开始后不得切换模式、revision、Scope、Source Profile 或 Source Target。
2. Question Understanding 必须保留原问题全文以及全部条件、比较、关系和输出约束，并记录 goal、audience、受控 `DIRECT / USER_VISIBLE_EXPLANATION / IMPLEMENTATION_DETAIL` 抽象层级、material conclusion checklist、evidence needs 和响应语言。它必须选择满足原问题的最低细节级别；流程/生命周期问题的 checklist 必须包含用户可见阶段、结果及重要状态变化或副作用，不能用类、方法或调用顺序替代这些结论。模型不得把问题改写为更容易回答的问题；Application 校验完整性，不以当前证据删除尚未解决的 Need。
3. World Model Cognition Context 必须来自固定 Read Authority，至少绑定 exact Scope、Context、Schema、Snapshot/Read Set、source revision、typed Result、Entity/Relation/Behavior/Constraint/State、Coverage、Support、Conflict、Unknown、locator 与 digest。它是世界模型对当前任务的只读认知投影，不是另一个事实库。
4. World Model source revision 与 Request repository revision 必须 exact 相等。显式版本比较问题可以使用分区的 exact Read Set，但每个分区必须独立绑定对应 Source revision。未对齐或无法证明相等的 Result 只能标记 `UNALIGNED_REVISION` 并作为候选导航，不能直接支持当前 revision 的 Claim；相关内容必须在 Request revision 上重新核实。
5. Question Understanding、Investigation、Answer 和 Review 是分离角色。每个模型步骤使用精确输入 allowlist、closed output schema、Strategy/Prompt 身份和独立收据；输出收据必须绑定当前 role、fresh role context、input Manifest digest 与 output schema ref/digest。模型只提交 schema 允许的语义字段，request/package/draft digest、attempt、Ledger ID/generation/revision/prefix 等权威坐标由可信适配层从当前状态补入并由 Application 重验，不能由模型回显取得权威。Provider 会话记忆、隐藏 rationale、未密封工具结果或上一角色私有输出不得成为正式输入。
6. 在任何真实 Provider dispatch 前，Application/Gateway 必须验证 current exact Provider、model、endpoint、configuration、role、secret reference、允许外发的 Cognition Context/Ledger/Package 字段或片段、redaction 和完整 input digest 已单独密封并授权。用户级 run grant 必须绑定 exact immutable Request、evaluation subject、Provider binding、Prompt/output contract、角色集合、总调用上限和授权消息；它本身不能直接 dispatch。每个运行时动态形成的角色输入还必须密封完整 Gateway Manifest、所有 model-visible 字段路径与片段摘要、payload bytes、schema/Prompt 和 full input digest，并由受信边界把 run grant 收窄为恰好一次 dispatch 的 role disclosure authorization。Gateway 在 credential resolution/HTTP 前独立重验同一 run grant、root Request、完整 role payload、Provider/qualification 和由前一结构化 Result 决定的角色顺序。真实 Web launcher 还必须在 listener 前证明自身从 clean exact product candidate 加载，绑定 published Bundle semantic/file digest、exact Source/Profile/Request/run authority，并先密封零分派 launch receipt；退出时密封逐角色、Gateway 与 transport terminal audit。任一授权、输入或 Result 只能消费一次；dispatch 后异常、outcome unknown、identity drift 或 replay 不 retry、不切 Provider。Secret value、secret reference 和授权 receipt 都不得进入模型消息。历史开发、Conformance、Capability、Product 或浏览器授权不能推导这次来源内容披露。
7. 持续本机 Web 必须在 listener 前密封 `ENGINEERING_QA_SESSION_AUTHORITY@1`：固定 clean exact product candidate、loopback origin、工程/
Binding/revision、World Model Read Authority、Source Profile/global + class allowlist、registered operations、Provider/model/endpoint/
configuration/qualification/secret reference、角色 Prompt/schema、redaction、有效期、每题及整会话 question/dispatch/bytes/wall-time 熔断和
`NOT_EXECUTED` Production 状态。Session Authority 只授权这个闭合边界，不授权未知问题或任何 dispatch。页面必须显示外发边界；用户
点击提交时，受信 ingress 密封 exact UTF-8 question bytes/digest、session authority digest、提交时刻和 disclosure acknowledgement，
并签发 server-owned unique request/run identity。System Owner 只能由该 `Question Submission Receipt` 与固定模板编译 exact Request 和
per-question run grant；客户端不得提交 request ID、grant、Provider 或来源参数。每个动态角色输入继续按第 6 条收窄为 one-use 授权。
重复 receipt、会话漂移/过期/总熔断耗尽必须在 credential/HTTP 前拒绝；单题失败不停止 listener，且不得污染或复用另一题的 Ledger、
Package、Review、Citation 或授权。浏览器问题 POST 必须在 receipt 前满足 exact loopback same-origin、`application/json` 和可用时的
`Sec-Fetch-Site: same-origin`；CORS 响应不可读不能充当副作用防护。工程、revision、Source/Provider 边界变化必须停止并新建 Session
Authority。

## Adaptive investigation and Evidence Ledger

1. 初始 Investigation Step 只读 immutable original question、已接受的 Question Understanding/Checklist、受信 Request 控制字段和 World Model Cognition Context。后续 Step 还可读取 Application 密封的当前 Evidence Ledger prefix。世界模型为 Investigation LLM 提供系统认知起点；零结果、无关内容或 Coverage 不足是显式认知状态，不得阻断原问题驱动的受权调查。
2. Investigation LLM 每一步只能提出一个版本化 schema 中注册的 `search`、`read`、`parse` 或 `FINISH` Proposal，并说明它对应的 Checklist/evidence need、预期消除的未知及与当前 Ledger 的关系。Proposal 可以根据前一步 Result 改变后续方向，实现真正的自适应多步调查；它没有直接工具句柄，不能执行操作、修改 allowlist/revision/预算、删除 Need 或把 `FINISH` 变成平台事实。
3. Source Broker 必须把 Proposal 和其中的 evidence class 当作不可信建议，重新解析 locator、拒绝模型命令和 URL、验证 exact Binding/revision/regular-file/global allowlist/Source Profile identity/class-specific allowlist/registered operation/参数/remaining fuse，并编译 caller 不可伪造的 Source Operation。read/parse locator 必须由当前 Ledger 签发且属于相同 class capability；非法、无进展、重复或越界 Proposal 形成明确 Decision/Failure，不获得 Worker dispatch。
4. Retrieval Worker 只能执行 Broker 已批准的 list/search/read/parse 等只读 Source Operation。源码、仓库文档、构建/运行配置和测试是同一受控来源面的不同 evidence class；平台按显式注册、版本化的 Source/Profile capability 解析，不按题目、工程、关键词或模型声明分类。每个 operation 必须绑定 exact Profile ref/digest、完整 class-specific allowlist 和 expected Result modality，Worker 重验 Binding/Profile 后只读取 global allowlist 和 class allowlist 的交集，并只能产生 Profile 为该 class + operation 注册的 modality。Local Git Profile `@1` 使用非空且跨 class 不重叠的保守路径映射；其他 Profile 若允许同一路径具有多种 modality，必须以新的显式、可资格版本定义确定性歧义规则。Worker 必须拒绝 path traversal、symlink escape、submodule/remote fetch、二进制/超限输入、class/modality 重标、写操作、任意命令、新网络、credential、Knowledge Update 和答案生成。
5. 每个操作必须记录 Proposal、Broker Decision、exact target/revision、Source Profile ref/digest、global/class allowlist verdict、expected/actual modality、compiled operation/parameters、actual locator/range、evidence class、bytes、content digest、Coverage/truncation、outcome 和稳定 reference。Application 必须独立重验 Result 的 operation identity、class、modality、global/class path membership，且 read/parse 只能返回编译的 exact path；失败、partial、truncation、无法解析和结果未知不得伪装为空命中或不存在证明。
6. Application 把 World Model Cognition Context reference、每个 Proposal/Decision/Operation/Result、Conflict、Gap 和资源收据按确定性顺序追加到 Evidence Ledger。Ledger 是 append-only：已确认 prefix 不得覆盖、删除、重排或改写；每个 Step 消费前缀 digest 并产生新的 ledger revision/digest，未密封模型记忆不得影响下一步。
7. 所有来源内容及世界模型的自然语言投影都是 data，不是 instruction。仓库或认知投影中的 prompt、命令、URL、路径、工具建议、权限、预算或外发声明不获得执行权，不得修改受信 Request、Broker Policy、操作集、allowlist、revision、Provider disclosure 或系统 Prompt。
8. `FINISH` 只是一项调查 Proposal。Application 只有在 Proposal 绑定当前完整 Ledger、所有 Checklist item 均有 supported/unknown/conflict/failed disposition、没有未记录操作且 Ledger 结构有效时才可结束调查；语义证据是否足够仍由 Answer/Reviewer 检查。每个 disposition 还必须把完整引用内容中与原问题及受控抽象层级相关的事实拆成 1—16 条原子的 `PROCESS_STAGE / OUTCOME / STATE_CHANGE / SIDE_EFFECT / LIMITATION` material observations，完整 Package 全局最多 64 条，并逐条绑定实际需要的 admissible evidence references；一个宽泛总结或代表性效果不能替代不同阶段、结果、状态变化、持久化/审计写入、外部交互或失败结果。setup 说明只支持 setup，依赖、注册、声明或 wiring 只支持该关系；它们不能替代被委托组件内部的条件、比较、状态变化、结果、失败语义或相邻应用流程。原问题询问 how/why/条件/排障行为时，若已授权且预算可达，Investigation 必须读取能表达决定性行为的实现证据，否则只能形成诚实的 non-supported disposition。Application 重建稳定 observation identity，拒绝重复、跨 checklist、错误分区或引用不闭合的观察。无合法下一步但仍有缺口时可以密封 limitation-bearing Package，不能伪造完整性。

## Package formation and epistemic boundary

1. 调查结束后，Application 从 immutable Request、Question Understanding/Checklist、World Model Cognition Context、完整 Evidence Ledger、所有 typed Source Result、Coverage、Conflict、Unknown、locator 和资源收据密封 Question Evidence Package。调查过程中不存在供 Answer 使用的临时 Package。
2. 每个 Package 保持一个不可变身份与 seal，但必须包含两个显式分区：
   - `support/citation`：仅包含按 modality、Context、Coverage 与 Support 校验通过的 admissible entries；只有该分区可以支持肯定 Claim 与 Claim Citation；
   - `boundary/audit`：必须保留 Boundary、Gap、Failure、Partial、Conflict、Unknown、Rejected Decision 和 Resource Receipt；它可以约束结论或形成带标签的 Boundary/Audit Reference，但不得支持或引用为肯定 Claim。
3. 每个 Package 至少绑定：
   - Package/Revision ID、protocol identity 与 digest；
   - immutable Request、original question、Question Understanding 和 Checklist digest；
   - exact repository/Binding/revision、Source Profile ref/digest、World Model Read Authority/Bundle digest 和 source-revision alignment verdict；
   - Evidence Ledger ID/revision/final prefix digest 及有序 Proposal/Decision/Operation/Result references；
   - 每个 entry 的 origin class、modality、Context、locator、content/result digest、Coverage/truncation、Support、Conflict/Unknown 和 disclosure class；
   - 每个 Checklist disposition 的原子 material observations、稳定 observation identity、observation kind 与 evidence references；
   - 未满足 Checklist item、失败/partial/unknown outcome、资源收据、package manifest 与 seal digest。
4. Package 是当前 Question Revision 中 Answer 和 Reviewer 唯一允许消费的证据与边界集合，但“进入包”不等于“可支持肯定结论”。未进入当前 Package 的 Source 内容、搜索印象、模型参数知识、会话记忆、rationale、旧 Package 或旧 Review 均不能支持结论。
5. Package seal 只证明内容集合的身份、完整性、顺序、provenance、revision 和未被篡改，不把内容变成真：search candidate 只证明命中，源码/配置只证明该 revision 的静态实现，文档只证明记录的用法或意图，测试只证明静态预期或已密封执行观察，World Model entry 只证明已发布认知及其 Context/Coverage，模型 Proposal 不构成事实。肯定 Claim 仍必须逐项绑定 `support/citation`；`boundary/audit` 只能说明边界、失败、冲突或未知。
6. 无显式受控解析规则时，任一 origin class 不自动胜出；不兼容内容保留在 `boundary/audit` 为 Conflict，不能被 Investigation、Answer 或 Reviewer 静默消解。Question Evidence Package 不是 Fact、Inference、Snapshot member 或跨任务正式知识。
7. Package 密封后不可追加、替换、重排或改写。任何补证必须以旧 Ledger 作为不可变 prefix 创建新 Ledger Revision，追加新的完整调查记录，再密封具有新 ID/Digest 的完整 Package；不得修改旧包。

## Answer, independent review and recovery

1. Answer 使用隔离的新上下文，只读 original question、accepted Question Understanding 和一个密封 Package；没有 Repository mount、Source/World Model Tool、Evidence Ledger write port、shell、网络、credential、Reviewer 输入、Investigation 私有输出或 Provider 会话历史。
2. Answer 的每个 Claim 必须声明 `DIRECT_ANSWER / USER_VISIBLE_PROCESS / IMPACT_OR_SIDE_EFFECT / IMPLEMENTATION_EVIDENCE / LIMITATION` 之一，并绑定一个或多个 accepted material checklist item。每个表达 Package 实质事实的 Claim 还必须绑定其文本实际表达的 Package material observation identity；唯一例外是答案末尾只陈述已保留 evidence scope/coverage boundary 的 `LIMITATION` Claim，它可以保留必填但为空的 observation-ID 集合，并且只能引用 `boundary/audit`。该例外不得承载 affirmative fact、不得把 supported observation ID 错绑到 limitation，也不能替代任一 Package observation 的默认正文覆盖。恰好一个 `DIRECT_ANSWER` 必须排首位；它可以是有 support 的 affirmative，也可以在真实边界下成为直接、诚实且仍绑定对应 `LIMITATION` observations 的 limitation。默认用户可见正文必须恰好覆盖每个 Package observation 一次；`DIRECT_ANSWER` 保持简洁，后续用户可见 Claim 承载其余阶段、条件、结果与副作用，不得把同一 observation 在直答和分段中重复。Application 按 Claim 顺序构造默认正文：始终保留首次覆盖；后续 Claim 的 observation 若已被完整覆盖，则从默认正文投影到开发者详情；若只与既有覆盖部分重叠则失败关闭，不能静默拆句或丢弃新事实。默认隐藏的 `IMPLEMENTATION_EVIDENCE` 可在必要时复用 observation 提供开发者细节。Application 还必须拒绝角色乱序、任一 checklist 或 observation 未覆盖、用户可见 observation 部分交叠、observation 只出现在默认隐藏的实现详情、supported disposition 没有 affirmative Claim、non-supported disposition 没有 limitation Claim、observation 跨 checklist，或 Claim 未引用该 observation 所需的全部 Package evidence entry。流程阶段、结果、重要状态变化和副作用是用户可见结论，不得降格为可选实现细节。实现证据仅在原问题明确请求或支持 material conclusion 所需时产生；`USER_VISIBLE_EXPLANATION` 的默认正文排除实现证据而在开发者详情保留 typed Claim，`IMPLEMENTATION_DETAIL` 才默认展开，不使用固定标题或字数比例。每个实质肯定结论必须绑定当前 Package `support/citation` 分区中一个或多个具有实际 Support 的 entry，且不得扩张其 Context、modality、Coverage 或时序。Claim Citation 必须回到该分区的稳定 locator/digest；`boundary/audit` 条目只能解释 limitation、failure、conflict 或 unknown，不能支持肯定结论。答案文本、模型 rationale、搜索命中或 Package seal 本身不是证据。
3. 无法推出的内容必须表达为用户可理解的 unknown/limitation：说明已能确认、尚不能确认、缺失的具体证据及影响范围。不得向普通用户机械平铺 operation、ledger、candidate、recall、Profile、authority、proof 或内部 Review 文本。
4. Reviewer 使用另一个隔离的新上下文，只读 original question、accepted Question Understanding、当前 Package 和 Draft；它不继承 Investigation/Answer 会话、rationale 或旧 Review。Reviewer 必须先从 immutable original question 独立形成 material conclusions，再以 closed `checklist_assessment` 列出 accepted Application checklist 的遗漏。它还必须检查相关 Package entry 的完整内容，独立列出绑定 checklist、kind 与 Package evidence entry 的原子 material observations，并分别报告 Application Package observation omission 与默认 Draft observation omission；不得把一个宽泛总结或代表性效果当作其他阶段、结果、状态变化或副作用已经覆盖。coverage-only、空 observation-link 的 limitation 仍须审核真实性与 boundary citation，但如果它不表达原问题要求的 material fact，空 link 本身不得被报告为 Application observation omission。随后分别对 direct answer、abstraction fit、material completeness、implementation-detail budget 返回 `PASS / FAIL`。它还审核逐结论正确性与支持、条件/顺序/异常/冲突/未知、相关性、可读性和可操作性。
5. Reviewer 没有文件系统、Repository、Source workspace、World Model query port、Source Tool、shell、网络、credential、Broker dispatch 或写权限。它只能返回 `APPROVED`、`REWRITE_REQUIRED`、`MORE_EVIDENCE_REQUIRED` 或 `REJECT` Proposal；在 `MORE_EVIDENCE_REQUIRED` 中可以独立形成版本化 Verification Request Proposal，但不能提出或执行路径、命令、`search/read/parse` 操作，也不能自行放行答案。
6. 每个失败项必须绑定 finding code、Question Checklist/Claim/Draft reference、问题说明和唯一合法 action。`REWRITE_REQUIRED` 只适用于当前 Package 已有证据可修复的表达、组织、层级、引用或遗漏；重写保持 Package Digest 不变并进入全新的独立 Review Attempt。
7. `MORE_EVIDENCE_REQUIRED` 只在 Reviewer 标明当前 Package 无法证明的具体 Checklist/Claim、所需 evidence class 和可验证 evidence need 时有效。Application 验证 gap 后启动独立 `Verification Investigation Attempt`。新的 Verification Investigation LLM 使用全新上下文，只读 immutable gap Request、current Package 与 current Ledger prefix；它不回到初始 Investigation LLM，不继承 Reviewer/Answer 会话，并像初始调查一样根据每一步新 Result 自适应提出一个注册 `search/read/parse/FINISH` Proposal。
8. Application/Source Broker 对 Verification Investigation 的每一步都在原 Request exact revision、allowlist、注册操作集与 remaining fuse 内重新校验、解析并编译，Worker 执行后追加新 Ledger Revision。Reviewer 或 Verification Investigation 给出的路径、命令、URL、工具与参数均是不可信建议；后者与所有其他模型一样没有直接 Source/FS/Shell/network/credential/tool authority。
9. 补证后必须密封新 Package，并从头创建 Answer 和独立 Review；旧 Answer、Review 或 Authorization 对新包无效。非验收的最早方向体验可以明确冻结每题最多一次 Verification Investigation 以尽快取得方向反馈，但该临时边界不得进入后续资格/验收协议。
10. 后续 hardening/qualification/acceptance 不得永久固定一轮补证，而必须在 exact run 前预密封 Package Revision、model call、Broker operation、source bytes、wall time 与 deterministic no-progress 高安全熔断。熔断数值必须足以容纳正常的多步、结果驱动补证；达到上限、无进展、不收敛、结果未知或剩余证据不足时不得减少 Checklist/evidence need、略去 Citation/Review dimension、合并角色或交付未批准答案。answerable 问题因此未获批准计 `FAIL`；预先分类的真实 boundary 才可交付经独立审核的准确 Limitation，否则失败关闭。
11. 只有当前 exact Package 上四项方向质量检查全部 `PASS`、Reviewer 独立 checklist 没有发现 Application omission、独立 material observation audit 没有发现 Package 或默认 Draft omission、其他 Review 项通过、Finding 为空且 Authorization 在发送前重验有效的 Draft 可交付。权限失效、输入漂移、包漂移、冲突未处置、无依据结论或审核未通过均失败关闭。

## Generality and knowledge reuse

Question Understanding、World Model Cognition Context、Investigation Proposal、Broker/Worker、Evidence Ledger、Package、Answer 和 Review 使用同一通用协议。核心代码、Prompt、UI 和评测不得按问题、项目、语言、框架、关键词、符号、约定文件名、fixture 或 Oracle 选择路由、来源、证据或答案。来源类型和语言解析差异只能由显式注册、版本化且通过资格的 Source/Profile capability 处理。

完成 Delivery 后，Application 可把高质量 Package 与已审核结论作为异步 Knowledge Update Proposal 输入。它不继承问答 Review 的正式知识资格，必须重新形成 Artifact/Evidence/Candidate，通过独立 Admission 并原子 Publication。同步答案不依赖该过程，更新成败不改变已交付答案；新的正式认知只在后续 exact Snapshot 中生效。

## Failure and implementation state

未授权模式或外发、revision/allowlist/Source Profile 漂移、越界文件、evidence class 重标、Source instruction 注入、Ledger 覆盖或缺口、未密封输入、无依据结论、无关 Citation、Package seal 被误当真值、冲突静默消解、任一模型直接取得来源权限、静默模式切换、审核未通过或资源耗尽均失败关闭。若 Provider 已完成响应但 closed output schema 拒绝其内容，Gateway 必须保留 completed response identity/usage 供审计，产品边界只在 exact Manifest/Provider/model/configuration/receipt/eligibility 绑定全部成立时传播真实 structured-output failure；不得把它泛化成 qualification drift、重试或继续消费该输出。具体 DTO、注册操作目录、其余高安全数值上限和 UI 投影由代码与测试定义，但不得改变本契约的认知定义、权威、角色、Ledger/Package 边界和失败语义。

`ITER-010 / SLICE-001` 已提供本地确定性的 Request、持久 Structure Read Bundle → bounded Cognition Adapter、Profile-bound Broker/Worker、append-only Ledger、双分区 Package、Answer/Review、一次独立 Verification Investigation、五类 closed role-input/output contract、input/schema-bound output receipt、可信坐标补入、exact run → one-use role disclosure narrowing、Gateway-side role/config/qualification policy、current DeepSeek composition、Session Authority、逐题 server-owned Request/run 与持续 Alpha launcher。返工还实现了受控答案层级、逐 Claim checklist links、默认正文投影、逐 disposition material observations、Claim observation/evidence closure、Reviewer 独立 checklist + observation comparison 和四项方向质量 Gate。确定性 fake transport 不读取 credential、不建立网络且不把 secret/authorization ref 放入 wire；这些证据不构成真实 Provider dispatch、外发执行证据、listener/browser 运行、Capability Qualification、Product Validation、Slice Result、Acceptance 或 Activation 证据。
