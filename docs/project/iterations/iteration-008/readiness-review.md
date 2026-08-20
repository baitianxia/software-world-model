---
id: ITER-008-READINESS
kind: iteration-readiness
status: accepted
authority: project-authorization
owners: [project, architecture, quality]
depends_on: [ITER-008-PROPOSAL, ITER-008-VERIFICATION, ROADMAP-M-002, ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-ACCEPTANCE, ITER-007-RESULT-SLICE-001-STOP-DECISION, SYS-ADR-015, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
code: []
tests: []
iteration: ITER-008
authorized_by: user
authorized_at: 2026-08-14T14:50:51+08:00
product_goal_alignment_verdict: accepted
product_goal_alignment_reviewed_by: user
product_goal_alignment_review_ref: codex-user-message:sha256:eb381cfd1532dec61ec5dba26456c52ffa3c7b92e5a9588f40e98a971c797221
critical_assumption_catalog_digest: sha256:1248eae891fcb2198b373db294213d7c3515369507682a6b1b1631a6e977171c
coding_input: false
---

# Iteration 008 Readiness Review

## Reviewed exact inputs

已核对 ITER-005/006 Acceptance、ITER-007 run-004 与停止裁决、`FINDING-007-008/009`、当前 World Model Answering、Implementation
Query、Agentic Task、Knowledge Update/Use、安全与 Web Contract。

事实结论是：World Model 已持有登录题所需的多个方法和实现事实，当前失败点在固定单方法问答协议；但现有规范又明确要求每题
固定 Plan/Draft/Review 三调用，因此不能在不修改架构与 Contract 的情况下直接开发自适应调查循环。

## Product-goal alignment gate

本轮绑定 `ROADMAP-M-002` Step 1，没有改变最终目标，也没有跳去新的知识域。ITER-005/006 是已接受前置；ITER-007 只提供失败
证据和待重新验收的技术资产。本轮结束时必须让用户从同一正式 Web 以无符号自由问题获得多方法实现答案；查询、表示和业务发现
三层完整时给出有界不存在结论，否则给出具体 Limitation。

结论为 **READY / SLICE-001 ONLY**。方向、能力路径、架构、Contract、exact baseline、预算和独立评测协议均已冻结；后续
SLICE-002 仍由 SLICE-001 的产品 Result、Reflection `CONTINUE` 和新用户授权阻断。

## Outcome, scope and non-goals

Outcome 是受限 Agent 只查询提问前构建的 World Model，根据 typed result 自适应调查多个候选和方法，然后在正式 Web 交付答案、
Gap 与 Citation，并逐题不低于成熟源码 Agent。

本轮不扩大 Java 语义闭包，不读取 README/配置，不做多语言、通用自治 Agent、问题驱动更新或 Production Activation。Agent 是查询
控制器，不是新的知识权威；回答事实仍只来自可复用 Snapshot。

## System contracts and unresolved decisions

以下输入已经闭合：

1. 新增 bounded Agentic World Model investigation ADR，明确为何放弃固定单方法消歧，以及 Agent、平台和 World Model 的 Owner；
2. 修订 World Model Answering、Implementation Query、Agentic Task、runtime flow、Gateway、Capability Evaluation 与安全边界；
3. 将查询结果完整性、知识表示 Coverage、业务语义发现召回完整性分别定义；pagination/total/truncated 只证明第一层，只有三层
   都有独立 Oracle 时才允许 bounded absence；
4. 把当前固定三调用文档门禁升级为“有界可变调查 + 单次 Draft + 独立 Review”的机械校验；
5. 冻结每题最大调查步数和模型调用（均至少为 2）、query/result 单步与总字节、总时长、Support 数量、trace 字节、超限行为和 retry 规则；
6. 冻结 ITER-007 技术资产清单和 exact Git baseline，明确哪些代码复用、哪些协议被废弃；
7. 冻结回答 Agent 的禁止面：Repository、源码文件、原始 Evidence、完整 AST、Knowledge Update 和 Direct fallback 均不可见；
8. 冻结逐 Need/Claim 评分表、重大错误定义、独立裁决人、争议与同分规则，并分别统计 World Model 建模成本、单题问答成本、
   多题摊销成本和源码 Agent 调查成本。
9. 冻结 Proposal A1—A8 三列表的 exact 摘要、最早反证、`V-DIAG-001` 逐层归因、SLICE-001 最小 bounded-absence/Limitation 双反例、每个 Slice 的
   `V-REFLECT` 结构化模板、独立决策 Owner 与语义；复盘 PASS 只代表审查完成，`CONTINUE/ACCEPT` 才代表方案可继续或可接受。

闭合证据为 `SYS-ADR-015`、Manifest 的 `ITER-008-SYSTEM-CONTRACT-SET@1` fileset digest、budget digest
`sha256:edb492b7…1012`、成熟 Agent/rubric/value protocol raw digest，以及
`V-PRE-001`—`V-PRE-007` 的 readiness PASS。任何这些文件或 digest 变化都会使本 Readiness stale，不能静默继承授权。

实现证据随后按治理规则形成 `FINDING-008-019`：run-010 证明原 Owner 允许模型提前 FINISH，用户既有显式 protocol redirect 又要求
集成层适配模型。该 system-contract Finding 已在同一已授权 SLICE-001 范围内写回原 12 份 System 输入；预算、Source-off、三层
完整性、18/18、no-retry、Web/canary/Activation 阻断与 Slice 范围均未扩大。重冻结后的
`ITER-008-SYSTEM-CONTRACT-SET@1` exact digest 为
`sha256:206d0b2ecc1dbd82b632b825f2284f7d6971b886840f903b1d6368f29c28331b`；它取代旧 fileset 作为当前实现输入，且必须由最终 docs gate
重算一致后才可形成 clean candidate。这是显式 Finding/redirect revalidation，不是静默继承原 digest。

run-011 又形成 `FINDING-008-021`：强制 candidate discovery 同时充当 terminal evidence class，会让可理解的模型语义选择与平台
保守证据责任冲突，并在非零候选时留下过早结束风险。该 Finding 将 raw candidate evidence alias 无条件向上归一为 method evidence，
不读取问题、工程、Case、Oracle 或未来 Result；预算、三层完整性、Source-off、no-retry 与所有产品阻断不变。写回后的当前
`ITER-008-SYSTEM-CONTRACT-SET@1` exact digest 为
`sha256:11b8b2d56386451802bc64214547abe253d54f26855a1ba7f9428acb43511a54`，并由 Manifest 与 docs gate 共同约束。

run-012 又形成 `FINDING-008-022`：正式 method Result 已承载同方法带 Support/Coverage 的 exact outgoing `CALLS`，因此在没有 path
obligation 时再要求 standalone `direct_neighborhood(OUTGOING_CALLS)` 是重复证据，不是产品能力增量。Application 只按已注册
operation/relation 将该 raw alias 收敛为 method；incoming、both 和与 path 组合的 outgoing direct 继续独立，且不读取问题、工程、
Case、Oracle 或未来 Result。预算上限、三层完整性、Source-off、no-retry 和所有产品阻断不变。写回后的当前
`ITER-008-SYSTEM-CONTRACT-SET@1` exact digest 为
`sha256:1542f20e7b946ee9a5a597ad4f5a2206f8e59ad58ac60ccdb2b2803b913d6987`；共享文档使历史 ITER-007 当前 fileset digest 同步重算为
`sha256:6f470e7cfc7c0812474219a3530e8ad23817fcfddb192647bafedb4fde72d349`，两者均由 Manifest 与 docs gate 机械约束。

run-013 资格 PASS 后形成 `FINDING-008-023`：Capability 使用 DeepSeek，但正式 bounded product policy/runtime 仍固定 Ark，二者不能
跨 Provider 借用资格。用户的 Ark-first/DeepSeek-fallback 要求被收敛为 product dispatch 前的 qualification route selection：按
`VOLCENGINE_ARK → DEEPSEEK` 选择第一个 current exact route，本轮 Ark 没有同 `1.5.2` Contract 资格，因此密封 DeepSeek；任何
request 已分派或 outcome unknown 后不得切换 Provider。该 Finding 把 Model Gateway、runtime flow、安全边界和 ADR 写回同一
System fileset；当前 `ITER-008-SYSTEM-CONTRACT-SET@1` digest 为
`sha256:52cca0748aa399d62b32e34ae1812bb945b6bdd4bda26e12c7d7ee50589ca710`，共享文档使 ITER-007 fileset 同步重算为
`sha256:87fc4011bc86ac11e1660e4b9e29762f1da0c44dac823a28a32c23d1dbfa6769`。

该变更没有扩大 Slice、调用预算或外部授权。它会改变 Gateway connection policy，因此 run-013 继续证明 `1.5.2` Strategy 的
Capability，但其旧 resource policy 不能授权新 product route。新 clean candidate 必须把 exact model-egress policy ref/digest 写入
Capability Definition，并形成全新 Conformance + closed Capability Result；随后才可形成正式 product freeze。

该新 route 的 run-014/015 又形成 `FINDING-008-024`。两轮在失败前的模型 output、typed step 与 independent evaluator 均 PASS，
但分别在第 4、第 10 个独立 TLS session 于 certificate verification 前 EOF；同一时段 credential-free TLS 对照可成功，且 endpoint
明确允许同一 verified connection 连续处理两次 HTTP/1.1 keep-alive request。根因是“一请求一 TLS session”把当前 TUN 的间歇 EOF
放大为 40-call qualification 的系统性失败机会，不是模型或 Oracle 偏差。

Readiness connection contract 因而重冻结为：DeepSeek Adapter `@3`、Conformance fixture `1.1.0` / Result `@2`、bounded egress
policy `@1.4.0` 与 `PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@1`。direct 与 product transport 都只能在 credential/Authorization/HTTP
bytes 前进行最多 3 次 credential-free TLS acquisition；成功 session 可在同一授权 run 内复用，但每个 request 的 Manifest、ID、
body/result digest 与调用审计仍独立。HTTP dispatch 后任何网络失败均 outcome unknown、零 retry。Capability closed Result 必须证明
40 HTTP dispatch、TLS attempts/successes、reuse、credential resolution 与 post-dispatch unknown 计数；product supervisor 只预置 3 个
exact connected descriptor，并闭合 `provisioned = TLS attempts + unused_closed`。旧 run-014/015 均永久失败关闭，新 candidate 必须
重新通过本地门禁、Conformance 与完整 Capability 后才能形成 product freeze。对应重冻结的
`ITER-008-SYSTEM-CONTRACT-SET@1` digest 为
`sha256:b1193e2a97f8c4c8db26dd2d3cbe98ff0b8fb7d6e8414fb15b71d1e0536b5df7`。

该 persistent candidate 的 run-016 已消除网络不确定性：Conformance 2 calls / 12/12 PASS，Capability 第 13 次已完成 request 时仍只有
1 次 verified TLS acquisition、12 次 reuse、13 次 HTTP/credential resolution，unknown/retry 为 0。前 6 Case / 12 calls 全 PASS；
第 7 个 reachability Case 的首轮模型输出包含 `reach/path`，却选择 method evidence，并复制 prompt 示例词，因而被 frozen ledger
正确拒绝。该结果形成 `FINDING-008-025`，证明下一缺口是 DeepSeek semantic instruction rendering，不是 transport、Application
transition 或 evaluator exactness。

Readiness wire contract 再重冻结为 Adapter `deepseek-chat-completions-no-tools@4`、Conformance fixture `1.2.0` / Result `@2`、
capability/Strategy `1.5.3`、prompt/vocabulary `@12`、suite/oracle `@1.5.3` 与 bounded egress policy `@1.4.1`。DeepSeek Adapter 必须把
Gateway semantic prompt 与 closed schema 合并为恰好一个 leading system message；prompt 只应用 sealed capability 对应 section，示例词
不得进入原问题未请求的 search terms，显式 reachability 优先选择 `path_exists`。Application/compiler、18 Case、40 calls、18/18、
persistent TLS 和 no-retry 不变；不得通过问题/Case/Oracle 特判或 evaluator 放宽处置。run-016 授权已消费，新身份必须重新完成本地门禁、
Conformance 与完整 Capability，PASS 前产品 Gate 继续阻断。重冻结后的 `ITER-008-SYSTEM-CONTRACT-SET@1` digest 为
`sha256:c9992a431726a48274355d1075187311471c40bea6efbb51de1c7b3ff9e14968`。

该身份的 run-017 证明单一 DeepSeek system authority 已修复原 PATH-EXISTS 失败，但同时暴露更窄的 Gateway 输入隔离缺口：虽然
prompt 声明其他 section inactive，实际每次仍发送 legacy Query Planning、Draft、Review 和 Investigation 的完整 monolithic 文本。
`MAX-FOUR-010` 的第 22 次 completed request 因而把 workflow trace 误选为 binary `path_exists`，并复制非当前 section 的
`order/return/throw/audit`；此前 9 Case / 21 calls PASS，transport 为 TLS 1/1、reuse 21、HTTP/credential 22/22、unknown/retry 0。
该 run 已按 `FINDING-008-026` 失败关闭，不能重试或拼接。

Readiness semantic-authority contract 再重冻结为 capability/Strategy `1.5.4`、prompt/vocabulary `@13`、suite/oracle `@1.5.4` 与
bounded egress policy `@1.4.2`。一个 prompt program 为三个 capability 分别冻结 entry；Manifest 前按 sealed stage 唯一选择并绑定
`capability-prompt-selection@1`，Gateway 必须校验所选 content digest，不能把自然语言 “inactive” 当作隔离。DeepSeek Adapter `@4`、
Conformance `1.2.0/@2`、compiler `@6`、18 Case / 40 calls、18/18、persistent TLS 与 no-retry 不变；新身份仍须从 clean candidate
重新通过 Conformance 和完整 Capability。相关 121/121、fake 18/18、完整执行面 1012/1017（唯一五项仍为
`FINDING-008-020` 的历史 drift）、docs 330/330、compileall/diff/secret scan 已闭合。更新后的
`ITER-008-SYSTEM-CONTRACT-SET@1` digest 为
`sha256:0143229ee22d1db3962e6bc6fedf7982fea96642fe84d1f116667f3b144219a5`。

该身份的 run-018 Conformance 2 calls / 12/12 PASS；Capability 无 retry 完成 40 calls / 18 Case，TLS 1/1、reuse 39、
HTTP/credential 40/40、unknown/retry 0，但两个首轮 search-term constraint 使 closed result 为 16/18 FAIL。PATH-EXISTS、
MAX-FOUR、operation/compiler/Ref projection 与所有第二步 transition 均 PASS。REF-PROVENANCE 暴露 Prompt 对 question-owned term
来源判断不够明确；RESULT-DRIVEN-BATCH 则证明旧 semantic constraint 把原问题未请求的 `return/throw` 具体机制误作唯一等价表达。

按 `FINDING-008-027`，Readiness search-term 边界重冻结为：term provenance 只按 original question 的语义来源判断，不能因为同词也
出现于 Prompt 就删除；常见 normalization 允许，但不得从抽象 outcome 推断未请求的 execution mechanism。Capability semantic
constraint 只能要求产品输入与 System Contract 可证明拥有的 concept。活动 identity 为 capability/Strategy `1.5.5`、prompt/vocabulary
`@14`、suite/oracle `@1.5.5`、policy `@1.4.3`；operation Oracle、18/40、18/18、Adapter `@4`、compiler `@6`、persistent TLS 与
no-retry 不变。更新后的 `ITER-008-SYSTEM-CONTRACT-SET@1` digest 为 `sha256:948647adf5e857ea1a782ab04396c92bfa5a51e8a26b7d35ab6dca984f67aaa4`。
run-018 永久 FAIL，新身份必须从 clean candidate 完成全新 Conformance 与 Capability；PASS 前全部产品 Gate 继续阻断。

本地重冻结验证为相关 117/117、fake transport 40 calls / 18/18、current documents 331/331、compileall/diff/secret scan PASS；
完整执行面 1013/1018，唯一四个 failure 与一个 error 的名称和原因仍完全属于 `FINDING-008-020` 的 ITER-003 frozen runtime drift。
这些结果不替代 live run-019。

exact candidate `6dc7a9e4…` 的 run-019 随后完成 live Gate：Conformance 2 calls / 12/12 PASS，Capability 40 calls / 18 Case、
18/18 PASS；两阶段 TLS 均 1/1，reuse 1/39，HTTP/credential 2/2 与 40/40，unknown/retry 均为 0。Capability result/qualification
proof/document digest 为 `sha256:16e9e6bc…5020b` / `sha256:7e460107…224fc` / `sha256:b0ec3ad1…e556`，有效期到
`2026-08-27T09:09:31.851862Z`。因此当前 exact Contract 的 V-002 资格阻断已关闭；Readiness 仍要求下一步先形成绑定该 authority chain
的 formal product freeze，公开 Web PASS 后才讨论 early canary/Reflection，且不得执行 Production Activation。

`FINDING-008-028` 已关闭该 formal freeze 自身的门禁表达死锁。ITER-008 bounded route 的确定性 qualification 升级为 `@2`，同时
记录 raw `full_regression_pass` 和独立 gate outcome；只有 `FINDING-008-020` 的五个测试各执行一次、精确 4 FAIL + 1 ERROR、原因
marker 相等且其余当前测试全 PASS，才允许 `PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD`。任一新增/不同失败、skip 或缺失测试仍阻断。
旧 `@1` 继续要求 raw suite PASS；历史断言、1013/1018 的 raw FAIL 事实和 canary/Acceptance/Activation 阻断都未被放宽。
System Owner 写回后的 ITER-008 fileset digest 为 `sha256:80b5393bd767cbc7be60f67ca0bbefbd308e1c7e84b8a522aab8bb016c26b311`；
共享 `local-browser` Contract 使 ITER-007 fileset 同步重算为
`sha256:3f25570e48caa265feb3a3d95cf0441628f36890744c9902a35b1ecac3844819`。
定向 gate/runtime/authorize 22/22 PASS；允许 AF_UNIX 的最终完整执行面为 1021/1026，raw exit 1，唯一 4 FAIL + 1 ERROR 精确匹配
preserved hold，结构化 gate PASS。该证据只关闭 deterministic product-freeze readiness，不替代正式 freeze 或 Web Result。

该 formal freeze 随后实际 PASS，但正式 Web 的 `登录流程是怎样的？` 在一次 DeepSeek call 后以 Answer `DomainError` 失败关闭。
exact sealed input/output 本地重放证明 Proposal/compiler 均有效，首次偏差是 `StructureView` 仍使用 ASCII-only tokenization 拒绝
`登录/流程`；run-019 的英文-only Capability suite 也未证明 cross-script source-identifier translation。按
`FINDING-008-029`，Readiness 再冻结为 Unicode Query normalization + non-Latin material concept 的 common English identifier
translation，并以一个既有首轮 Case 的中文等价 input 做真实模型资格。活动 identity 为 `1.5.6/@15/@1.4.4`、suite/oracle
`@1.5.6`；18 Case / 40 calls / 18/18、Adapter `@4`、compiler `@6`、persistent TLS 和 no-retry 不变。当前
ITER-008/ITER-007 System fileset digest 为 `sha256:58288f15…19a0` / `sha256:6a68490e…e760`；新资格与产品 freeze/Web PASS 前，
run-019 只保留为旧 identity 的历史证据，V-002/V-003/V-WEB-001 继续阻断。
本地相关 128/128、fake transport 40 calls / 18/18、docs 333/333 与完整执行面 1022/1027 已闭合；完整回归唯一五项仍是
`FINDING-008-020` 的 exact historical hold。该证据允许形成 clean qualification candidate，但不构成 live PASS。

该 candidate 的 run-020 preflight `sha256:3afe56e2…cddba` 与 Conformance `sha256:e20eef6c…c0eb` 已 PASS，证明
DeepSeek `deepseek-v4-pro`、Adapter `@4` 与 persistent TLS 当前可用。Capability freeze `sha256:07982a4e…02f4` 在第 33 个已完成
request 后以 `QUALIFICATION_INVALID` 停止：13 Case / 32 calls 已闭合，无 network unknown/retry；旧 cross-script semantic group
错误拒绝 `log`，Prompt 又允许 evidence operation/topic 替代显式 material term，并把一般疑问 `Does X implement Y` 误判为
reachability。`FINDING-008-030` 已将活动 identity 升级为 `1.5.7/@16/@1.4.5`、suite/oracle `@1.5.7`，不改变 18/40/18/18、
Provider、Adapter、预算或 no-retry。run-020 授权已消费且旧 verdict 保持 FAIL；新 clean Conformance/Capability PASS 前
V-002/V-003/V-WEB-001 继续阻断。本地相关 115/115、fake 40 calls / 18/18、docs 334/334 与完整执行面 1022/1027 已闭合；
完整回归唯一五项仍为 `FINDING-008-020` 的 exact historical hold。

同一 `1.5.7/@16` candidate 的 run-021 Conformance 2/2 PASS；Capability 完成 40 calls / 18 Case，15/18 PASS，TLS 1/1、reuse
39、HTTP/credential 40/40、unknown/retry 0。此前中文 equivalence 与 implementation-existence intent 已 PASS；剩余三个失败只是在
首轮把显式 `reach/method/implementation` 当作已被 operation/evidence request 表达的冗余 search term。按
`FINDING-008-031`，Readiness 保持 Provider-independent `1.5.7/@16` 与 suite/oracle `@1.5.7`，将 DeepSeek Adapter 重冻结为
`@5`，只为 active Investigation schema 增加无损 lexical-coverage wire adaptation；bounded policy 升级为 `@1.4.6`。该适配不包含
题目/Case/工程/具体词例，不改写 response，也不进入 Draft/Review。run-021 永久 FAIL；新 Adapter identity 的 Conformance 与完整
Capability PASS 前 V-002/V-003/V-WEB-001 继续阻断。

Adapter `@5` 的 exact candidate `c925496…` 随后执行 run-022。Conformance 2/2 PASS；Capability 无 retry 完成 40 calls / 18 Case，
transport 为 TLS 1/1、reuse 39、HTTP/credential 40/40、unknown 0，但结果为 16/18。PATH-EXISTS 已 PASS；CYCLE-PROGRESS 与
REF-PROVENANCE 仍分别遗漏 direct `methods/implementations`，证明 schema-scoped Provider 重述不是稳定 Owner。按
`FINDING-008-032`，Readiness 将问题直接 ASCII 词项的 closed deterministic merge 固定到 Application compiler `@7`，raw output/digest
保持审计，cross-script translation 保持模型所有；Adapter 移除该领域 adaptation 并重冻结为 `@6`，bounded policy 升级 `@1.4.7`。
Provider-independent `1.5.7/@16`、suite/oracle `@1.5.7`、18/40/18/18 与 no-retry 不变。run-022 永久 FAIL、授权不可 retry；新 exact
identity 的 Conformance/Capability PASS 前 V-002/V-003/V-WEB-001 继续阻断。本地相关 127/127、fake 40-call / 18/18、docs
336/336 PASS；完整执行面 1024/1029 的唯一 4 FAIL + 1 ERROR 仍精确属于 `FINDING-008-020`，没有新增失败。

新 exact candidate `837171e611ae6e1dd3a0939e446e0658b1d08d6c` / tree
`11b4a2a083d1e1c0f239e0a132e61cd125cd12ec` 的 run-023 已完成新资格链。Conformance preflight/result digest 为
`sha256:c7c730f556e994c7b3278a35104c47a631e46dd84997122f95c1133783813703` /
`sha256:16e947ad1aaf698227ae59f06db3ec53caca04eb9f1c46375adf6ae1bd960522`，2 calls / 12/12 PASS；Capability freeze/result digest 为
`sha256:7bfd08c6307314a15b7f0d41e666d559154f7906c9818f4296ac5937fb724cae` /
`sha256:9306f487e79b4594154dd60e8dd55854cc9289b2ce057ed5fea0851baf03ba6d`，40 calls / 18 Case / 18/18 PASS。两阶段 TLS 1/1，
reuse 1/39，HTTP/credential 2/2 与 40/40，unknown/retry 均为 0；Qualification 有效至
`2026-08-27T11:28:37.309517+00:00`。关键 CYCLE/REF/PATH Case 的 direct terms、semantic constraints 与 projection 全部 PASS。

因此 V-002 对当前 `1.5.7/@16/@7/@1.4.7` + Adapter `@6` exact Contract 的资格阻断已关闭。Readiness 仍要求
下一步先从证据写回后的 clean producer 形成绑定该 authority chain 的 formal product freeze，然后执行 V-003/V-004/
V-XD-001/V-SEC-001/V-SOURCEOFF-001/V-WEB-001。公开 Web PASS 前不得披露 early canary 或进入 Reflection，
Production Activation 仍不得执行。

formal run-004/run-005 的 pre-dispatch 实现漂移修复后，run-006 登录题已完成 4 个 DeepSeek HTTP 200、TLS 1/reuse 3、credential
4/4、retry 0；前三个 Investigation PASS，第四个 Draft 已生成正确语义，却在按旧契约复制 4 个 Result ID 与 35 个 support digest
时耗尽 1000-token output 并结构化失败。`FINDING-008-035` 将 terminal exact collection Owner 收回 Application，活动 Contract
升级为 `1.5.8/@17/@1.4.8`、suite/oracle `@1.5.8`，Adapter `@6`、Investigation compiler `@7`、18/40、no-retry 与 output budget
不变。该变化使 run-023 资格不再适用于 current identity；Readiness 的 V-002 再次转为 blocking，必须先完成新 clean candidate 的
Conformance 与完整 Capability，才能重新生成 formal product freeze。run-006 不得 retry；hidden canary 和 Production Activation
仍未执行。

run-024 随后完成新 Contract 的 Conformance 2/2 / 12/12，并在 Capability 中完成 39 responses / 17 Case；Draft 以 104 tokens、
raw 空 terminal authority collection PASS，直接验证 `FINDING-008-035` 的 Owner 修复。第 40 次 Review request 在唯一 TLS session
复用 39 次、运行约 120 秒后收到 `REMOTE_DISCONNECTED`；HTTP/credential 40/40、retry 0，按 outcome unknown 密封。
`FINDING-008-036` 将 connection policy 升级为 `@2`：每条 session 最多 20 dispatch、一次运行最多 3 次 acquisition，轮换发生在
下一次 credential/HTTP 前；Adapter/policy/audit 升级为 `@7/@1.4.9/@2`。上游 `1.5.8/@17`、suite/oracle 与 threshold 不变。
run-024 授权已消费且不能 retry；新 transport identity 的 Conformance/Capability 仍是当前 Readiness blocking Gate。

clean exact candidate `34048ae770944a11aa4e01d0249b90933a30e8c7` / tree
`153c2dc625fd3e72e6b49c6d6cf94be95a3ef894` 的 run-025 随后关闭该 Gate。Conformance 恰好 2 requests / 12/12 PASS，
preflight/result digest 为 `sha256:b5590984ae031142c8fa61da043a25b53defc4b8089041920b2773e4ccdd69f0` /
`sha256:476f4d871ff4e269ca8e0c90a4b84361f390a3346d32deb578a0af0697af0518`；Capability 完成 40 calls / 18 Case /
18/18 PASS，TLS attempt/success `2/2`、reuse `38`、HTTP/credential `40/40`、unknown/retry `0`，每条 session 恰好最多
20 dispatch。Capability result/qualification document/terminal digest 为
`sha256:caf062a2a49fd28e6046937fd10f633c5155f9c47c60565a8d422c2a7b98cc11` /
`sha256:7d3b4ea2c5527f1e621e5d268105626f5ccf06c00cc9e7b74ae3dcea6bea208a` /
`sha256:b0dd529152e6c7e43b231a3d439e65de38ea95542cc173b5a25dbe124564a8d6`，资格有效至
`2026-08-27T13:19:05.298209+00:00`。V-002 对 current exact identity PASS；Readiness 的下一阻断是从证据写回后的 clean
producer 生成全新 formal product freeze 并执行公开 Web。该资格不授权 hidden canary、SLICE-002 或 Production Activation。

## Slice, dependency and risk closure

本轮有两个依次单独授权的纵向 Slice，不能拆成 Planner、工具、Web、评测等内部组件完成项：

- `SLICE-001`：最小多候选/多方法调查、Source-off、Draft/Review/Citation 和正式 Web；产品代码冻结后执行一份全新早期 canary，
  至少含 1 条无符号多方法 answerable 与 2 条互补 boundary，并先密封成熟源码 Agent 同题结果；产品 Gate、early absence、
  `V-DIAG-001`、early Agent 对照与
  `V-REFLECT-001` 未 PASS，或复盘决定不是 `CONTINUE`，均不得授权下一段；
- `SLICE-002`：分页、三层完整性、cycle/progress、预算与安全加固；再从同一正式 Web 执行两个最终隐藏工程、成熟源码 Agent 对照
  和现场题。

公开 LoginService 仅作回归，不得用于证明泛化。早期 canary 与最终工程不得复用；它们必须在各自 Slice 产品代码冻结前保持
不可见并位于已冻结 Java 语义闭包内。披露后任何产品修改都会烧毁对应项目、问题、baseline 与 target，失败 Result 必须保留。

## Verification readiness

已经冻结：

- 两个小型未见 Java 工程、4 条 answerable、2 条 boundary 的持有与披露协议；
- 至少 2 条多方法题、3 条无符号名题和每工程至少 1 条无符号题；
- 成熟源码 Agent 的 exact 版本、工具权限、revision、预算、运行顺序和密封结果格式；逐 Need/Claim rubric、重大错误定义、
  独立裁决人与争议/同分/失败规则；early 对照必须冻结零重大错误、逐 Need/Claim 不退步和最大时延/成本阈值；
- World Model 建模、单题问答、多题摊销与源码 Agent 调查四类成本的独立统计口径；
- 正式 Web 的 2 条现场题，其中至少 1 条无符号名并执行 `V-XD-002` 的跨域组合；
- 重大错误 0、逐题不退步、Source/Update/Direct fallback 全部为 0；
- 登录/下单回归和所有旧 accepted capability 回归；
- Production Activation `NOT_EXECUTED`。

## Architecture reflection gate readiness

Proposal A1—A8 的 exact section digest `sha256:1248eae8…171c` 已同时写入 Manifest 与本 Readiness metadata，`V-PRE-007`
已执行。A1—A6 的最小可行性证据在
SLICE-001 到期，A7/A8 只保留早期阻断反证并在 SLICE-002 下最终 Verdict；A6 的正向价值指标、单位、比较方向、数值阈值、
复用周期、计算/重放协议、独立裁决 Owner 与 Agent 缓存政策必须在编码前由用户收据冻结，成熟源码 Agent protocol/rubric 也必须是 exact digest，
且能在 SLICE-001 取得早期实测；Result 必须保存可重放 exact JSON 报告、输入 digest 和独立裁决收据，不能自填 actual；early canary 会用互补 boundary 验证 absence/Limitation，并先密封成熟源码
Agent 同题结果；
`V-DIAG-001` 能定位 Source/Snapshot/Query/Trace/Draft-Review/Web 的首次偏差；每个 Slice 恰好一个 Reflection Case；Result 会逐假设
记录 exact Evidence、问题分类、分层诊断、Agent 对照、Finding 去向、下一风险和明确决定。中间段只有产品 Case 全部 PASS、
`V-REFLECT-001 PASS`、`reflection_decision: CONTINUE` 与用户另行授权四项同时成立，SLICE-002 才能成为活动编码输入。

## Authorization decision

**ACCEPTED / ITER-008-SLICE-001 AUTHORIZED。** 用户消息 `codex-user-message:sha256:eb381cfd…7221` 明确要求“开发ITER-008”，
据此接受上述 exact Readiness，并仅授权 `ITER-008-SLICE-001`。授权允许修改该 Slice 列明的 System 实现、`src/`、产品测试和
validation，但不授权新的外部模型分派、早期 canary 披露、SLICE-002、Production Activation、推送或把固定三调用资格当作新
bounded Strategy 资格。SLICE-001 产品代码冻结后，必须先取得绑定 exact freeze 的新披露/Provider 授权。
