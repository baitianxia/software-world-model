---
id: ITER-010-FINDINGS
kind: iteration-findings-index
status: open
authority: development-evidence
owners: [engineering, architecture, quality]
depends_on: [PROJECT-GOVERNANCE-IMPLEMENTATION-FEEDBACK, ITER-010-PROPOSAL, FINDING-010-141, FINDING-010-153, FINDING-010-154, FINDING-010-155, FINDING-010-156, FINDING-010-157, FINDING-010-158, FINDING-010-159, FINDING-010-160, FINDING-010-161, FINDING-010-162, FINDING-010-163, FINDING-010-164, FINDING-010-165, FINDING-010-166, FINDING-010-167, FINDING-010-168, FINDING-010-177, FINDING-010-178, FINDING-010-179, FINDING-010-180, FINDING-010-181, FINDING-010-182, FINDING-010-183, FINDING-010-184, FINDING-010-185, FINDING-010-186, FINDING-010-187, FINDING-010-188, FINDING-010-189, FINDING-010-190, FINDING-010-191, FINDING-010-192, FINDING-010-193, FINDING-010-194, FINDING-010-195, FINDING-010-196, FINDING-010-197, FINDING-010-198, FINDING-010-199, FINDING-010-200, FINDING-010-201, FINDING-010-202, FINDING-010-203, FINDING-010-204, FINDING-010-205, FINDING-010-206, FINDING-010-207, FINDING-010-208, FINDING-010-209, FINDING-010-210, FINDING-010-211, FINDING-010-212, FINDING-010-213, FINDING-010-214, FINDING-010-215, FINDING-010-216, FINDING-010-217, FINDING-010-218, FINDING-010-219, FINDING-010-220, FINDING-010-221, FINDING-010-222, FINDING-010-223, FINDING-010-224, FINDING-010-225, FINDING-010-226, FINDING-010-227, FINDING-010-228, FINDING-010-229, FINDING-010-230, FINDING-010-231, FINDING-010-232, FINDING-010-233, FINDING-010-234, FINDING-010-235, FINDING-010-236, FINDING-010-237, FINDING-010-238, FINDING-010-239, FINDING-010-240, FINDING-010-241, FINDING-010-242, FINDING-010-243, FINDING-010-244, FINDING-010-245, ITER-010-PDR-010, ITER-010-PDR-011, ITER-010-PDR-012]
code: []
tests: []
iteration: ITER-010
---

# ITER-010 Findings

- [FINDING-010-245](FINDING-010-245.md)：run-112 以 low-effort 连续完成四个 Ark calls 并推进到两次 Source read；第五个 pre-dispatch
  TLS failure 依法激活 fallback，DeepSeek 明确 HTTP 402。unknown/retry 0；保留 `@12` repair，并在 bounded delay 后执行 fresh run-113。
- [FINDING-010-244](FINDING-010-244.md)：run-111 前两次 Ark SSE calls completed；第二次 output 精确触及 `8192`、finish `length`，
  JSON string 中途截断，第三次 repair 仍被笼统归为 response invalid。transport unknown/retry 0、DeepSeek 0，故不是网络不可用。
  current `@12 / 1.12.0` 固定 `reasoning_effort=low` 并保留 incomplete terminal 的 Usage/structured-output 分类；fresh Conformance 已
  13/13 PASS，下一步执行 run-112 长产品复验。
- [FINDING-010-243](FINDING-010-243.md)：run-110 首个 SSE call 在约 `80.333s` completed，第二个约 `102.925s` 后被本地 parser 以
  `PROVIDER_RESPONSE_INVALID` 拒绝；Ark transport `2/2/2`、unknown 0，故不是网络不可用。raw frame 未保存，所以 comment 仍是待验证
  假设；current `@11 / 1.11.0` 修复确定存在的 SSE comment-ignore 缺口，fresh Conformance 已 13/13 PASS，下一步执行 run-111。
- [FINDING-010-242](FINDING-010-242.md)：fresh Ark 短 canary 2/2 成功后，run-109 的异质长问题仍在约 `55.996s` 后
  `REMOTE_DISCONNECTED`；与 run-108 的 `56.075s` 高度一致，证明短网络探针会假阳性。current `@10 / Conformance 1.10.0` 保持 Gateway
  单终态语义，把 Provider wire 改为官方 SSE 并在 Adapter 内严格重组；clean live Conformance 已 2/2 PASS，run-110 是下一产品验证。
- [FINDING-010-241](FINDING-010-241.md)：run-108 Q5 已越过旧 Ark HTTP 400，但在 HTTP dispatch 后
  `REMOTE_DISCONNECTED / PROVIDER_OUTCOME_UNKNOWN`；按 no-retry 与“仅可信 unavailable 才 fallback”边界保持 DeepSeek 0。Q4 fresh
  Conversation 继续 zero-dispatch Clarification，通过隔离但不构成五问质量 verdict。
- [FINDING-010-240](FINDING-010-240.md)：safe Conformance evidence 证明 `glm-5.3` response 精确触及旧 96-token canary cap 并
  `INCOMPLETE_TERMINATION`；CLI 默认升到现有预算内的 512，wire/product bound 不变，fresh qualification 必须重做。
- [FINDING-010-239](FINDING-010-239.md)：fresh `glm-5.3/@9` Conformance 的 completed response 被 closed-output validator 拒绝后，
  artifact 丢失其安全 identity/usage。current 汇总保留这些安全字段与枚举失败分类，仍拒绝资格且不持久化 raw output。
- [FINDING-010-238](FINDING-010-238.md)：用户以 exact UTF-8 authority delta 批准 Ark preferred actual `glm-5.3`；current Adapter `@9`
  删除不兼容的 `thinking` field，并以 Conformance `1.9.0` 要求新 identity/request bytes 在 run-108 前重新资格化。
- [FINDING-010-237](FINDING-010-237.md)：fresh no-source Conformance differential 定位 current Ark 400 来自 `thinking` field，并证明
  冻结 alias 当前返回 actual `glm-5.3` 而非获准/资格化的 `glm-5.2`；临时 variants 已恢复，等待 Provider restore 或 exact human model delta。
- [FINDING-010-236](FINDING-010-236.md)：run-107 的 Q3/Q5 重复收到 Ark HTTP 400 `InvalidParameter / BadRequest`；现有安全 evidence
  丢弃可选 `error.param`，故以向后兼容 `@2` schema 增加严格清洗 parameter-name，保持错误正文丢弃、400 non-eligible 与 route 不变。
- [FINDING-010-235](FINDING-010-235.md)：用户报告流量恢复后的 run-106 中，Ark 前 6 个 call 全部 completed；第 6 个 Primary output 缺少
  顶层 JSON 最后一个 closure，被准确分类为 `STRUCTURED_OUTPUT_INVALID / JSON_SYNTAX_ERROR`。第 7 个 fresh same-profile format
  repair 在 HTTP dispatch 后 `REMOTE_DISCONNECTED / PROVIDER_OUTCOME_UNKNOWN`，按 contract 无 retry、无 DeepSeek fallback；Q4
  zero-dispatch Clarification 继续通过。现有 validator/repair/route 无本地偏差，下一 clean run-107 继续异质冻结题。
- [FINDING-010-234](FINDING-010-234.md)：用户触发的 run-105 Ark-first recheck 在 current committed candidate 上发出 1 个 Ark request，
  仍得到 sealed `429 / AccountQuotaExceeded`；DeepSeek 因周一 16:02 CST peak window 在 credential/TLS/HTTP 前拒绝。Q4
  zero-dispatch Clarification 通过，Q2/Q3/Q5 按同签名停止边界未发送；本次只更新 availability/route 证据，不产生 `@30/@20/@24`
  质量 verdict或代码变化。
- [FINDING-010-233](FINDING-010-233.md)：run-104 的 Q1 以 `15` dispatch fail-closed；4 次全部为 comprehensive Review，阶段性
  Boundary redaction 把真实 Package/Draft 的 `3/1` 个 Boundary presence 也变成 `0/0`，Reviewer 因而在 missing binding/Claim 与恢复
  uncertainty 之间振荡。Q2 首次 DeepSeek fallback 返回 sealed HTTP 402，Q3/Q5 按同外部签名停止，Q4 zero-dispatch Clarification 通过。
  current `@30 / REVIEW_INPUT@20` 保留可信 presence counts 而不转移 focused ownership；模型协议 `37/37`、相邻定向测试 `137/137` PASS。
- [FINDING-010-232](FINDING-010-232.md)：run-103 在 current off-peak standing scope 内完成 Ark 4 个 sealed 429 与 DeepSeek
  39/39 completed，shared Turn budget 把五题都保持在 15 内；Q2 ACCEPTED、Q4 zero-dispatch Clarification，整体仍 FAIL。Q1 证明 focused
  repair 会擦除 Reviewer 已识别的 concrete DEFECT/Finding；Q3 证明 follow-up 仍沿用上一 goal并混淆 abrupt-failure local reachability 与
  rollback/effect unknown。current `@29/@19/@24` 以 Application-restored semantic anchor 阻止 defect erase，并把当前 requirement 与 failure
  条件语义投影到 Primary/Reviewer；定向 `137/137` PASS，fresh committed successor 待验证。
- [FINDING-010-231](FINDING-010-231.md)：run-102 实际发生在周一 09:44 CST / UTC 01:44 高峰：Ark 1 个 sealed 429 后，DeepSeek
  以 `DENIED_PEAK_WINDOW` 在 credential/TLS/HTTP 前保持 0 dispatch；Q4 新 Conversation 零调用澄清通过。shared budget digest 已同时
  绑定两个 runtime，但 `@28/@18/@23` 没有取得模型质量证据；下一 fresh run 使用 PDR-007 闲时，当前峰时调用则属于 exact scope delta。
- [FINDING-010-230](FINDING-010-230.md)：run-101 Q3 实际为 Ark 1 + DeepSeek 15 = 16 dispatch，证明两个 Provider 各自的 15-call
  authorizer 会把同一 logical Turn allowance 叠加。current fixed Artifact Session 为两条 route 注入同一个 pre-dispatch logical budget，
  route seal 再重算 combined sum；第 16 次在 Provider boundary 前 `BUDGET_EXHAUSTED`，fresh run-102 待验证。
- [FINDING-010-229](FINDING-010-229.md)：run-101 的 comprehensive Reviewer 对已明确标为 unconfirmed 的 transaction/cache/refresh
  类别仍要求肯定分类，并围绕同一 Boundary 反复要求删除/增加引用，耗尽 Review。current `@28/@18/@23` 把 uncertainty 的诚实回答视为
  requirement coverage，并令 comprehensive/focused 分别独占一般语义与 exact Boundary challenge；fresh run-102 待验证。
- [FINDING-010-228](FINDING-010-228.md)：run-100 Q5 的正文可用但 Browser 投影 70 个 Citation；旧 Claim 只绑定 SUPPORT Observation，
  导致 broad Search 的完整合法 hit inventory 被整批带入答案。current Claim 新增最小 exact `support_citation_refs`，每个 citation-bearing
  Observation 至少选择一个、全部 refs 必须属于 selected evidence；Answer/Primary output identity 升级到 `@2/@3`，fresh run-101 待验证。
- [FINDING-010-227](FINDING-010-227.md)：run-100 Q3 在 full Source Read 后仍重复 Q2 普通下单答案，comprehensive/focused Reviewer 均批准；
  旧 typed body 只能证明 Claim support，不能证明 Draft 回答 exact current User Message。current 每个 Review 必须返回 exact
  `requirement_coverage_assessment`，未 fully addressed 必须绑定 global Finding且不能交付；current protocol 为 `@27/@17/@22`。
- [FINDING-010-226](FINDING-010-226.md)：run-099 证明 identifier ranking 已在 56-file observation 内检查目标 implementation，但真实源码是
  `generateOrder` 而非 `createOrder`，所以完整 literal 仍为零命中。current Worker/Tool/model boundary 只把最多 16 个已检查 related path
  标为 `IDENTIFIER_PATH_NAVIGATION_CANDIDATE` Boundary opaque READ options；Search 不产生 SUPPORT，fresh full READ 后才可支撑 Claim。
  current `@26/@16/@21`、六模块 `157/157` PASS，fresh run-100 待验证。
- [FINDING-010-225](FINDING-010-225.md)：run-098 Q5 的 focused Review body 已全闭合且 Findings 为空，却把 decision 写成 FINDINGS；
  generic repair 随后制造无绑定 global Finding。current closed-contract directive 只允许保留 assessments/empty Findings 并把 decision 改为
  APPROVED；Application 不自行批准。与 `FINDING-010-224` 共用 current `@25/@16/@20`，fresh run-099 待验证。
- [FINDING-010-224](FINDING-010-224.md)：run-098 Q3 已读 exact order implementation，但 same-Package rewrite 持续保留“订单写入调用”
  这类 authored effect label，邻接 caveat 未消除矛盾并最终耗尽 Review。current `@25/@16/@20` 要求只保留 exact call expression/local
  order，删除 surrounding effect label，且 caveat 不构成修复；fresh run-099 待验证。
- [FINDING-010-223](FINDING-010-223.md)：run-098 的 Ark 3 个 trusted-unavailable verdict 正确激活 DeepSeek，32/32 fallback completed；
  Q2 的 `createOrder` 因完整 query 不在第 76 个 `OmsPortalOrderServiceImpl` filename 中而越过 64-file fuse。current Worker 在授权 tree
  metadata 上以长度至少 4 的 Java identifier components 排序 path candidates，正文仍只按完整 literal 匹配，56/64 fuse不变；fresh
  run-099 待验证。
- [FINDING-010-222](FINDING-010-222.md)：run-097 恢复 Ark 主路线并完成 40 个 dispatch；Q1/Q5 ACCEPTED、Q4
  零调用 Clarification，Q2 为单一 post-dispatch unknown。Q3 的 13 个 caller challenge 全部 correctly WITHIN，随后 bound + empty
  Boundary 被 Reviewer 和 repair 错标为 `NOT_DISCLOSED_IN_DRAFT`。current `@24/@16/@19` 逐 challenge 投影 reference/fragment-state
  closed disposition 表与 exact repair facts；targeted `34/34`、相邻 16 模块 `261/261` PASS，fresh run-098 待验证。
- [FINDING-010-221](FINDING-010-221.md)：run-096 已证明 DeepSeek stale/idle rotation 生效且 37/37 call completed；
  Q1/Q5 ACCEPTED、Q4 零调用 Clarification。Q2 的 focused Reviewer 却把 exact caller-only Claim 重解释成 database effect，
  Primary 随后两次 exact-repeat。current `@23/@15/@18` 直接投影 exact challenged Claim 并要求 stricter different
  caller-effect rewrite；targeted `34/34`、相邻 16 模块 `261/261` PASS，fresh run-097 待验证。
- [FINDING-010-220](FINDING-010-220.md)：run-095 的 Q3 focused Reviewer 把两个 disclosed Boundary 都判为 material/null code，
  却又返回额外 Finding；generic repair 原样重复矛盾对象。current `@22/@14/@17` 用专用二选一 directive 要求 retained Finding 绑定
  exact challenge，或删除 unbound Findings 并 APPROVE；相邻十七模块 `255/255` 定向测试 PASS，fresh run-096 待验证。
- [FINDING-010-219](FINDING-010-219.md)：run-095 的 DeepSeek fallback 完成 27/28 call；Q2 在 Q1 后闲置约 141 秒时复用已失效
  keep-alive，于 HTTP 后密封 unknown。current Engineering Chat runtime ref `@3` 在 qualified transport call 前轮转可读/异常或 idle ≥60 秒
  的 session，仍保留最多 3 acquisition、每 session 20 dispatch 和零 retry；base Adapter/Conformance exact identity不变，loader与相邻
  十七模块 `255/255` 定向测试 PASS，run-096 待验证。
- [FINDING-010-218](FINDING-010-218.md)：run-094 的 Q1 ACCEPTED/Q4 零调用 Clarification 通过；Q2 unknown、Q3 limitation、Q5
  protocol violation 使整体仍 FAIL。Q5 的 valid SOURCE Search 证明 initial question-scope helper 把同 module POM/TEST prefixes 混入
  SOURCE-only operation；current fix 只从 current evidence-class allowlist 选择 prefix，六模块 `154/154`、相邻十五模块 `229/229` tests PASS，
  fresh run-095 待验证。
- [FINDING-010-217](FINDING-010-217.md)：run-093 的 Q2/Q5 证明显式 module scope 只约束 cognition、未约束 Source Search，且多个普通
  Search 都从 canonical fallback index 0 重扫。current `COMPILED_SOURCE_OPERATION@3` 由 Broker 重算 original-question prefix scope，
  只轮转 rank-3 fallback cohort并按 validated actual count推进；`56/64` fuse和最后一个 READ 槽位不变，六模块 `154/154`、相邻十五模块 `229/229` PASS，fresh
  run-094 待验证。
- [FINDING-010-216](FINDING-010-216.md)：run-093 在 Ark 3 个 sealed 429 后自动由 DeepSeek 完成 28 个 call，证明备用路线与 standing
  authority 正常。Q1 focused Review 的两个 fragment 只省略 Draft inline-code backticks，却被 byte matcher 误拒。current
  `@21/@13/@16` 只对 U+0060 presentation delimiter 作双侧 normalization，仍拒绝语义改写、虚构和 normalized duplicate；fresh run-094
  待验证。
- [FINDING-010-215](FINDING-010-215.md)：run-092 的 Ark 53 个 call 全部完成，无 trusted unavailable，故 DeepSeek 0 正确；Q3/Q4
  成功，Q1/Q2/Q5 因未绑定且未披露的 resolved Search diagnostic 被反复制造 audit-only 空操作 Finding 而耗尽 authority。current
  `@20/@12/@15` 新增 exact `draft_disclosed_fragments[]`，机械闭合 reference/fragment/disposition 并拒绝 no-op audit-only；Agent/Tool/Model
  73 tests PASS，fresh run-093 待验证。
- [FINDING-010-214](FINDING-010-214.md)：run-091 的 Ark 37 个 call 完成、1 个 post-dispatch unknown；无可信 pre-dispatch unavailable，故
  DeepSeek dispatch/credential/TLS/HTTP 均为 0。Q1 错误交付零 Citation 的混合事实/边界 Limitation，Q2 补证后丢失完整 Findings，Q3
  cognition-literal repair 原样重复非法 query，Q4 零 dispatch Clarification，Q5 no-retry unknown。current `@19/@11/@14` 保留补证后
  correction baseline、限制 Limitation 为零 SUPPORT、给出 material literal replan 并冗余 resolved-candidate audit-only 边界；58 项模型/Agent
  测试与相邻十二模块 148 项测试均 PASS，fresh run-092 待验证。
- [FINDING-010-213](FINDING-010-213.md)：run-090 的 Ark 31 个 call 完成，另有 1 个 pre-dispatch TLS failure 与 1 个 post-dispatch
  unknown；DeepSeek fallback 因 pricing evidence 超过 900 秒在 credential/TLS/HTTP 前关闭。Q4 零 dispatch Clarification 保持。Q1 的
  coherent repair 回退到 non-JSON prefix 后旧 gate未使用第二 slot；Q2 audit-only assessment 缺 Finding code且 repair 原样返回。current
  `@18/@11/@13` 改为 distinct-category final repair 与单义 audit-only closure；模型边界 34 tests PASS，相邻集与 run-091 待验证。
- [FINDING-010-212](FINDING-010-212.md)：run-089 的 Ark 4 个 sealed 429 合法启动 DeepSeek 周末 fallback；DeepSeek 27 个 call 完成、1 个
  post-dispatch unknown。Q4 零 dispatch Clarification 保持，其余工程 Turn 未交付。first divergence 是 invalid Review/Source action repair
  原样复制、same-Package rewrite 原样复制 rejected Draft，以及 Limitation Reviewer 要求 Claim、误报已有 Boundary binding并把 Search/interface
  当实现证据。current `@17/@10/@12` 密封 changed-replacement guard、typed convergence directive、focused actual index diagnostic 和
  pure-boundary Limitation review；147 tests PASS，fresh run-090 待验证。
- [FINDING-010-211](FINDING-010-211.md)：run-088 的 Ark 4 个 sealed 429 合法启动 DeepSeek 周末 fallback；DeepSeek 52 个 call 完成、1 个
  post-dispatch unknown。Q4 零 dispatch Clarification 保持，其余工程 Turn 未交付。first divergence 是逐缺陷 Review、重复 local Finding
  identity、focused body/decision/Finding 自相矛盾与 Primary 未一次解决全部 Findings。current `@16/@9/@11` 密封 full-audit、focused exact
  closure、Reviewer-authored decision repair、未引用 duplicate-code disambiguation 和 all-Findings rewrite；146 tests PASS，fresh run-089 待验证。
- [FINDING-010-210](FINDING-010-210.md)：run-087 的 Ark 4 个 sealed 429 后合法切换 DeepSeek，Q4 零 dispatch Clarification 保持，其余
  工程 Turn 未交付。exact rejected-Draft edit base 生效；新偏差是 semantic Claim 被按 phrase 拆分、Limitation rewrite branch 冲突和 opaque
  Boundary binding 被误作正文披露。current `@15/@8/@10` 通用闭合；144 tests PASS，后继 run-088 见 `FINDING-010-211`。
- [FINDING-010-209](FINDING-010-209.md)：run-086 的 Ark 49 次 HTTP dispatch 中 47 次完成、2 次 post-dispatch outcome unknown，故
  DeepSeek 0 正确。Q2 final preflight 未重复 exact SUPPORT/BOUNDARY ID domains；Q3 Review successor 丢失 exact rejected Draft，Claims
  从 `5 → 10 → 7 → 13` 扩张。current `@14/@7/@9` 密封 exact edit base、targeted rewrite 与 redundant reference domains；144 tests PASS，
  fresh run-087 待验证。
- [FINDING-010-208](FINDING-010-208.md)：run-085 的 Ark 52 次 HTTP dispatch 中 51 次完成、1 次 post-dispatch outcome unknown，故
  DeepSeek 0 正确；Q4 零 dispatch Clarification 保持。Q1/Q3/Q5 暴露 nested field、trusted action/draft branch 与 Boundary
  binding/disclosure 缺口。current `@13/@7/@8` 递归投影 closed shape 和有效 branch，要求 Limitation 保留 material Boundary binding，
  并统一 untrusted typed-output error；15 次 authority 不变，144 项定向 PASS，fresh run-086 待验证。
- [FINDING-010-207](FINDING-010-207.md)：run-084 的 Ark typed TLS unavailable 首次出现时，周六窗口、run authority 与 900 秒 pricing
  freshness 仍有效，但旧 DeepSeek 600 秒 receipt 已从 listener preparation 提前过期，故 credential/TLS/HTTP 为 0。current policy
  `ITER-010-PDR-007@3` 只在 first real DeepSeek preflight 从同一 plan 激活 active receipt 并重验全部条件；preparation decision 不授权外调或
  消耗 active duration，11/16 分钟边界测试与相邻 144 项定向 PASS。
- [FINDING-010-206](FINDING-010-206.md)：run-084 四个工程 Turn 均失败、隔离 Clarification 继续零 dispatch。最早产品偏差是 Search/Read
  matcher 错把真实 `LITERAL_TEXT_SEARCH_HIT` 当成 `EXACT_STATIC_SOURCE_TEXT`，导致同资源 resolved diagnostic 被误分类；Review input 还缺
  kind-specific closed disposition domain，Prompt/preflight 未显式禁止 authored string 尾随换行。current `@12/@6/@7` 按真实 modality、
  authorized Citation 与 exact canonical path 重算，投影 `allowed_exact_dispositions` 和无首尾 whitespace contract；144 项定向 PASS，fresh
  run-085 待验证。
- [FINDING-010-205](FINDING-010-205.md)：run-083 的 Ark 43 次 TLS/credential/HTTP 全成功，DeepSeek 0 正确；Q1/Q3/Q5 accepted、Q4
  零 dispatch Clarification，Q5 已关闭旧 diagnostic/effect 缺陷。Q2 暴露 syntax→closed-contract 分层修复缺口；Q1 暴露不同 opaque locator 的
  same-resource Search/Read 漏配与普通 Boundary materiality 漏审。current `@11/@5` 只允许严格后继 validator stage 的第二次 repair，按 exact
  canonical resource identity 关联 Source item，并挑战每个 Package Boundary；15 次 authority 不变，144 项定向 PASS，fresh run-084 待验证。
- [FINDING-010-204](FINDING-010-204.md)：run-081 因 stale pricing evidence 在外调前停止，不是 Ark unavailable；刷新官方证据后的
  run-082 获周末 fallback admission，但 Ark 41 次 TLS/credential/HTTP 全成功，DeepSeek 0 正确。Q2 暴露 Application-owned Observation ID
  冗余抄写漂移，Q3 暴露三次 Review 容量不足；Q5 的未声明 resolved diagnostic 绕过旧 relevance 交集投影，Reviewer 又把 external-effect
  scope 自相矛盾地判成 caller evidence 内。current `@10/@4` 由 Application 绑定 exact Observation prefix、挑战全部 resolved candidate、
  密封 closed semantic scope，并以 `11+4=15` 保持 dispatch authority；132 项定向 PASS；该 candidate 的 run-083 后继结果见
  `FINDING-010-205`。
- [FINDING-010-203](FINDING-010-203.md)：run-080 四个工程答案均 `ACCEPTED`、隔离 Clarification 零 dispatch，Ark 32 次
  TLS/credential/HTTP 全成功且 DeepSeek 0 正确；fresh Reviewer 却继续放行已由 full READ 闭合的 Search 诊断，以及只凭 caller
  expression 断言 callee/database/Elasticsearch effect。current Application 投影 exact caller/callee 与 resolved-acquisition relevance
  challenge，focused Review 逐项 disposition，Response Control 重算闭合；协议 `@9/@3`，预算/route/authority 不变；后继 run-081/082
  由 `FINDING-010-204` 记录。
- [FINDING-010-202](FINDING-010-202.md)：run-079 的精确 Java type Search 在最相关 filename 正文命中后仍扫描低排名 corpus，最终耗尽
  Source `64/64`。current Worker 先完整检查安全 basename cohort，再以 typed Partial early-stop 保留预算；无 anchor/hit 或安全/编码/fuse gap
  时继续原 bounded scan。Source/Tool/Question `81/81` PASS，fresh successor 待验证。
- [FINDING-010-201](FINDING-010-201.md)：run-079 的 typed relation 已含 `UmsAdminServiceImpl` endpoint，直接 Entity state 却被 75%
  relevance cutoff 截掉，导致首次 Source target 闭域缺失。current ranking 在既有 bound 内保留 selected relation 的 same-Snapshot direct
  subject/object Entity；不递归、不恢复弱尾部、不授予 Source authority。Cognition `12/12` PASS，fresh successor 待验证。
- [FINDING-010-200](FINDING-010-200.md)：run-078 首次真实贯通 Ark typed pre-HTTP unavailable → DeepSeek 周末 fallback；Q2 却把
  `mall-portal` 目录段当作正文 literal，空扫 56 文件后过早 Limitation。current Broker 在 Worker 前零读取 typed reject，Primary 必须根据
  sealed decision 改用不同正文 literal；`82/82` 定向 PASS，fresh five-turn successor 待验证。
- [FINDING-010-199](FINDING-010-199.md)：首版 HTTP evidence 修复误触两家 conformance-bound Gateway core。current decorator 原样委托
  exact Adapter，只在 inner terminal 后持久化/enrich；core 与 Ark/DeepSeek aggregate 恢复既有 PASS exact identity，loader 没有降级。
- [FINDING-010-198](FINDING-010-198.md)：Ark Adapter 的安全 HTTP status/details 在 Gateway 持久化边界丢失，使 trusted availability
  owner 无法形成 unavailable verdict，DeepSeek fallback 不可达。current candidate 密封并贯穿 status + evidence digest；503/402 fallback
  与 auth/config/client/unsealed fail-closed 定向通过，fresh live 仍待验证。
- [FINDING-010-197](FINDING-010-197.md)：冻结 `mall-search` / `mall-portal` 题仍会收到 `mall-admin` Java item 或 Profile-wide gap。
  current projection 用 original question + sealed allowlist 的 exact top-level scope 约束 formal Coverage root；真实 artifact 零外调复演只保留
  对应 Maven module item，异域 affirmative/gap 为 0；认知 `11/11` PASS，fresh live 仍待验证。
- [FINDING-010-196](FINDING-010-196.md)：run-076 Draft 仅凭 import/field/caller syntax 推断 Mapper 生成 provenance，且普通邻接细节没有
  反事实 materiality 判据。current Primary/Reviewer 对每个 detail/Boundary 执行 omission test、禁止为 Draft 自引入细节扩大调查，并要求
  generation/tool provenance 有 direct SUPPORT；Model `28/28` PASS，fresh live 仍待验证。
- [FINDING-010-195](FINDING-010-195.md)：run-076 的 32-item SUPPORT 被结构 value、公共 path、function token 和弱正分尾部污染。
  current cohort-aware relevance replay 收敛到 14 个 item，商品/营销/通用 Role Controller 噪声为 0；相邻八模块 `102/102` PASS，
  fresh live 仍待验证。
- [FINDING-010-194](FINDING-010-194.md)：run-076 SUPPORT `dimensions` 仍夹带 typed `COVERAGE/UNKNOWN` capability/eligibility metadata。
  current `ENGINEERING_AGENT_WORLD_MODEL_SUPPORT@4` 只允许五类 affirmative dimension，metadata-only Context 只形成 Boundary；
  相邻七模块 `92/92` PASS，fresh live 仍待验证。
- [FINDING-010-193](FINDING-010-193.md)：run-076 Draft 在后续 full READ 已闭合相同 need 后仍向用户披露早期 Search 截断，并加入与具体
  requested conclusion 无关的 559/866 全局清单数字。current Primary/Reviewer 分开 audit retention 与 user-visible material Boundary；
  无关或已解决诊断只留 audit，fresh live 仍待验证。
- [FINDING-010-192](FINDING-010-192.md)：run-076 的 World Model SUPPORT 顶层夹带已在 BOUNDARY 中的 global Coverage/Gap，使合法
  SUPPORT ID 可承载边界语义。current adapter 只在 SUPPORT 保留 novel affirmative item 与 per-item coverage，global
  coverage/conflict/unknown 只进入 BOUNDARY；相邻七模块 `91/91` PASS，fresh live 仍待验证。
- [FINDING-010-191](FINDING-010-191.md)：run-076 的 pre-delivery Draft 把 Cognition coverage gap 误称为授权边界，并在只读角色更新的
  producer 实现时推断 request/session 何时看到新权限。Primary/Reviewer 现须区分 authority、coverage、tool、runtime state，以及
  producer invocation、callee effect 与 consumer-visible lifecycle；模型边界直接 `28/28`、相邻组合 `77/77` PASS，fresh live 仍待验证。
- [FINDING-010-190](FINDING-010-190.md)：run-077 的首个 Ark call 再次 raw `PROVIDER_HTTP_ERROR`，页面已真实分层显示 execution 与 Provider
  evidence；新 EMPTY CONTEXT 的“这些失败也会回滚吗？”则以零 dispatch Clarification 成功。相同外调 signature 随即停止；DeepSeek 虽获
  周末闲时 admission，但无 trusted unavailable verdict，故 0 dispatch 正确。工程答案质量仍未验证。
- [FINDING-010-189](FINDING-010-189.md)：run-076 的 Turn/route projection 已保留 raw `PROVIDER_HTTP_ERROR`，Browser 主消息与 notice 却只显示
  `AGENT_MODEL_CALL_REJECTED`。现把 execution-stage code 与 raw Provider classification/code 分层展示；UI 不取得 availability/fallback
  权威，也不暴露错误正文、凭据或未密封输出。
- [FINDING-010-188](FINDING-010-188.md)：新 Conversation 的“这些失败也会回滚吗？”没有命中旧 zh-CN marker 集，错误进入 Ark attempt。
  current Binding-owned policy 已通用覆盖单数、复数和类别性指示表达，仍仅在真正 EMPTY CONTEXT 下以零 dispatch Clarification 关闭。
- [FINDING-010-187](FINDING-010-187.md)：run-076 的角色重分配题已完成 9 次 Ark call、真实 Source Read 和 Answer Draft，越过旧 dangling
  locator 矛盾；repair 与后四题随后连续收到 raw `PROVIDER_HTTP_ERROR`。没有受信 unavailable verdict，故已获周末闲时 admission 的
  DeepSeek 保持 0 dispatch 正确。五题均未交付，质量仍未验证。
- [FINDING-010-186](FINDING-010-186.md)：run-075 的库存失败追问把消息发送列入“数据库写入一定未发生”，而 Claim 只记录调用顺序，fresh
  Reviewer 对 10 个窄 Claim 全部 `SUPPORTED` 并漏掉标题继承的错误分类。现要求 Claim 和 Reviewer 都把 heading/table/list 容器的
  category/scope/condition/certainty/negation 纳入完整 assertion；漏枚举用 global Finding，错误分类用 concrete defect。
- [FINDING-010-185](FINDING-010-185.md)：run-075 的角色重分配题在 Source `64/64` 时，effective catalog 已正确撤销 Source operation，
  `source_read_options` 却仍暴露 controller locator，same-profile repair 复制 dangling READ 后被拒。现投影 exact Source file budget，并让
  read options 与 catalog 在 exhausted 状态共同关闭；`63/64` 预留 READ 与真实 terminal denial 语义保持不变。
- [FINDING-010-184](FINDING-010-184.md)：run-074 首次交付真实三轮 Chat，分类删除异质题也成功；Maven/启动链题随后因
  `SOURCE_SEARCH.arguments` 的单个 malformed item 必须重建为两个 sealed-template item，却被 `@4` 无条件 array-length copy obligation
  拒绝，并伴随 `—`→`-` 的既存文本漂移。现以 `ENGINEERING_AGENT_OUTPUT_PREFLIGHT@5` 只允许完全没有既存 allowlisted item value 的 invalid
  array 子树重建，并在 decode 前恢复其余 prior exact value；受影响组合 `141/141` PASS，fresh successor 待验证。
- [FINDING-010-183](FINDING-010-183.md)：run-073 的 same-Package targeted rewrite 已获第二次 fresh Reviewer `APPROVED`，却因 Response
  Control 要求 successor Work State 等于 Package 首次封装状态而失败。现明确 immutable Package origin 语义，并重验 Package identity 与
  current Work State→Draft→Review exact chain；真实 sealed-control 正负向回归 PASS，fresh Browser successor 待验证。
- [FINDING-010-182](FINDING-010-182.md)：run-073 的 cognition scoped Search 只检查 1 个文件，但普通 `JwtTokenUtil` Search 达到单次
  56-file scan 上限时误报整轮 `SOURCE_FILE_FUSE_EXHAUSTED`，Agent 在实际 `59/64` 且 Source catalog 仍可用时提前作答。现分离
  Search operation-local file/byte limit code 与 Broker whole-Turn rejection；相关八模块 `225 tests / 3 skipped / 0 failure`。
- [FINDING-010-181](FINDING-010-181.md)：run-072 的 first Source query 已精确选择 `UmsAdminServiceImpl`，但两个 exact Search 为全类路径
  覆盖仍分别读取 56/6 个文件，与两个 full READ 合计耗尽 `64/64`，后续 `AdminUserDetails` repair 因 Source catalog 撤销而失败。现把
  cognition canonical paths 密封为 Broker-validated Search-only scope，不授予模型 path/READ authority；受影响四模块 `102/102` PASS，
  fresh Browser successor 待验证。
- [FINDING-010-180](FINDING-010-180.md)：run-071 的 World Model 已给出 exact declaring type/source path，Primary 却仍以宽泛 `login`
  首搜并耗尽 Source file fuse；第 14 个 Ark dispatch post-dispatch outcome unknown 后正确停止且 DeepSeek 0。current @8 local candidate 把
  第一次 Source search 约束到 cognition-derived exact declaring type；其执行范围缺口已由 `FINDING-010-181` 继续处置。
- [FINDING-010-179](FINDING-010-179.md)：fresh 官方价格页与用户纠正确认 DeepSeek 高峰只发生在周一至周五，周末全天闲时；run-070 的
  `DENIED_PRICING_CHECK` 则直接来自超过 900 秒的旧 check。现以 policy `ITER-010-PDR-007@2` 补齐 weekday/weekend 与连续闲时，且
  stale/changed check 仍失败关闭；下一 fresh run 不再错误等待周末窗口。
- [FINDING-010-178](FINDING-010-178.md)：run-068 真实证明修复后的 World Model-first 与精确 `UmsAdminController` Source target 已生效，
  但随后 run-068/069 的 raw Ark HTTP error 和 run-070 的 Ark pre-HTTP unavailable + stale DeepSeek pricing check 使三轮链停止。三个
  run 均独立停止、retry/fallback HTTP/Production 为 0；其“只能等待”的当前结论已由 `FINDING-010-179` 纠正。
- [FINDING-010-177](FINDING-010-177.md)：run-067 在 fresh Turn 跳过 World Model，先用 broad/已读 caller-expression search 和辅助
  Mapper read 消耗 Source slot，随后又对同一 service implementation gap 换句式重复查询，最终在第九个 Primary call 提出第九项 Tool
  action 并被 8-action 上限失败关闭。现精确投影 remaining budget、机械要求 fresh World Model-first/zero-budget convergence，并明确
  semantic-gap no-requery 与 unresolved-target Source relevance；24 项 Model tests PASS，fresh Browser successor 待验证。
- [FINDING-010-168](FINDING-010-168.md)：run-056 前两轮登录链成功，但用户纠正 Turn 的初始/repair Draft 都把原文双引号未转义地写入 JSON
  string，导致词法解析失败；现以受信且不回显内容的行/列/字符诊断和全角色 `@2` 序列化预检闭合本地修复，75 项受影响测试 PASS。
  run-056 已密封为 Ark 17 / DeepSeek 0 / Production 未执行，fresh successor 仍需独立 run-057 外发授权。
- [FINDING-010-167](FINDING-010-167.md)：run-055 首个同一 Conversation 三轮链已真实成功并交付，但新 Conversation 的异质问题在初始/
  repair 中逐字重复遗漏 `action.operation`，尽管 sealed input 已含同形 template 与 exact diagnostic。现于 sealed role input 后追加受信但
  shape-only 的 final-output preflight，重复有效 templates/required fields/repair diagnostic；Application 仍不补字段，fresh successor 待验证。
- [FINDING-010-166](FINDING-010-166.md)：run-052/053 原始输入证明模型可见 tool signature 与 closed action 不同形，SUPPORT/BOUNDARY
  内容也未就地分区，分别对应参数错形/遗漏 operation 与跨 disposition Claim 引用。现改为完整 action copy template、用途分区 evidence
  和带 exact path 的语义诊断；Application 仍不补字段、不改标证据，74 项受影响测试 PASS，fresh Browser successor 待验证。
- [FINDING-010-165](FINDING-010-165.md)：通用 plan gate 曾把 PDR-011 sealing action 的“禁止新外调”与 Result 对 PDR-010 历史 19 次 Ark
  调用的“运行对账”混为一谈。现只对 exact @3 failure packet 允许历史 external counters，其他 non-external action、错误 schema 与非零
  full regression 继续失败关闭；该治理修正必须先成为 trusted parent，Result 后置重建。
- [FINDING-010-164](FINDING-010-164.md)：@3 首次真实 run-052/053 回放发现 Gateway `output_digest` 使用
  canonical JSON string codec，而 synthetic verifier fixture 错用 raw-text SHA-256。现保留原始输出 raw digest，另用产品同源
  canonical digest 对账 Gateway；真实形状 dry replay 已闭合 19 个 Ark / 0 个 DeepSeek dispatch。
- [FINDING-010-163](FINDING-010-163.md)：普通 plan revision 要求 base governance action + PASS Result，而当前非治理动作只能先生成被
  @2 expressiveness gap 阻止的 Result，形成机械自锁。用户已明确授权 exact 最小 trust-root recovery；PDR-011 只先冻结 @3 runner，
  产品/Provider/Result 均不进入该恢复提交。
- [FINDING-010-162](FINDING-010-162.md)：PDR-010 的失败出口允许答案前停止，但冻结 `ITER010_MVP_LIGHT@2` 仍要求三份完整系统答案、
  Citation、Review、Codex 比较和单一 Session，且只接受 PASS；当前动作又禁止修改 runner/PDR。为避免伪造 handoff，Result/游标保持未变，
  PDR-011 已按用户授权采用 runner-first、Result-second 的 forward recovery。
- [FINDING-010-161](FINDING-010-161.md)：owner 纠正后的 run-051/052/053 已完成原失败与两个异质复验。结构化输出无效始终留在 Ark
  same-profile repair，DeepSeek 0；只有 run-051 的真实 Ark pre-HTTP TLS unavailable 曾使 fallback eligible，随后仍由 DeepSeek 硬门禁在
  network 前拒绝。run-053 的 17 个 Ark TLS/HTTP 全成功，但一个异质案例连续误用 BOUNDARY support，另一个初始/repair 再次缺
  `operation`，PDR-010 产品停止条件成立。
- [FINDING-010-160](FINDING-010-160.md)：run-050 在 listener/network 前正确拒绝了首个诊断候选，因为修改通用 adapter 使双 Provider
  Conformance implementation digest 失效。现已恢复 adapter exact qualified bytes，把字段诊断放回 Agent/Application boundary；双资格
  aggregate digest 对账与 123 项定向测试 PASS，无需等待或重跑 DeepSeek Conformance。
- [FINDING-010-159](FINDING-010-159.md)：run-049 的 7 次 Ark TLS/HTTP 全部成功且 DeepSeek 0；第一 Turn 只因单一
  `WORLD_MODEL_QUERY` action 在初始/repair 输出中连续缺少 `operation` 而失败。nullable validator 原先丢弃字段级分支诊断，repair input 又不
  携带 trusted failure；首个通用诊断候选 124 项定向测试 PASS，但 owner/资格边界随后由 `FINDING-010-160` 纠正，fresh Browser successor
  待执行。
- [FINDING-010-158](FINDING-010-158.md)：run-048 的 Ark 前两次 HTTP 已成功，第三次 call 只在 HTTP 前发生一次 TLS failure；真实缺口是
  launcher 未组合受信 availability Owner。现仅把 Gateway 密封的 canonical pre-HTTP unavailable 提升为 exact verdict，HTTP/outcome、
  输出合同无效与审核拒绝仍不回退；36 项定向测试 PASS，fresh Browser successor 待执行。
- [FINDING-010-157](FINDING-010-157.md)：备用执行配置的 dispatch admission 曾被错误提升为整个 Browser Session 的启动门禁，导致
  峰时 Ark-only 也等待 DeepSeek。现已允许 denied fallback receipt 下启动 preferred-only listener；fallback 若被合法选择，仍在
  credential/TLS/HTTP 前由逐请求门禁失败关闭。
- [FINDING-010-156](FINDING-010-156.md)：run-045 的 Ark 7 次 TLS/credential/HTTP 均成功，2 次完整响应仅因输出合同无效被拒，却触发了
  备用路线；现已把 availability-only fallback、同 profile 新调用和模型透明路由写入系统契约并完成产品重构，定向机械 Case 已 PASS；
  真实 Session 无 current exact availability verdict 时 fallback dispatch 保持 0。
- [FINDING-010-155](FINDING-010-155.md)：run-045 在 `63/64` 且已有未读 locator 时仍向模型暴露 SEARCH，第三次搜索吞掉最后槽位并使
  exact READ 失败。Resource receipt、动态 tool catalog 与 Broker backstop 现共同保留最后 READ；`56 + 7 + 1 = 64` 定向回归 PASS，
  run-045 质量失败保持不变，fresh Browser successor 待复验。
- [FINDING-010-154](FINDING-010-154.md)：Artifact Session `@3` 仍把 exact machine receipt 绑定为逐 run user-message grant，未实现
  `SYS-ADR-019` 的 standing parent；`@4` 现重验公开 upstream/clean exact commit-tree/license object，并派生 exact Session、Turn attempt
  与 one-use call authority chain。正负向本地测试及 run-045 的 28 个真实 dispatch/terminal 对账均 PASS，人工重复审批请求为 0；
  产品答案质量仍 FAIL。
- [FINDING-010-153](FINDING-010-153.md)：PDR-009 动作图没有 fresh 用户方向的可达治理出口，导致用户明确调整计划后既不能继续旧动作也不能合法修订；
  一次性 recovery Result 只恢复了采纳 PDR-010 的治理能力，PDR-010 已用可跨提交的完整体验开发动作和显式用户方向分支完成处置，不再设置
  rotating slot、分钟收据或整份 Manifest 摘要门禁。
- [FINDING-010-141](FINDING-010-141.md)：现有计划以组件/阶段完整度而不是最早产品价值假设组织，且 Slice 内没有机器可读的唯一动作；
  曾处置为 PDR-009 四路价值 Gate 前移；PDR-010 保留基线差分和唯一动作约束，但已把完整 MVP 体验前移并解锁产品与 standing-scope 外部执行。

- [FINDING-010-001](FINDING-010-001.md)：ITER-009 体验与用户架构裁决证明严格 Source-off `WORLD_MODEL` 不能独自承担默认通用工程
  问答；已处置到 `SYS-ADR-016` 和同变更 owning System Contract/治理边界。
- [FINDING-010-002](FINDING-010-002.md)：世界模型仍是持久、版本化的软件外部认知；修正提问期流程为模型主导自适应调查、
  Broker/Worker 受控读取、调查后密封和 Reviewer 独立补证。已处置到同一 ADR/Engineering QA Contract 与重制后的 ITER-010 计划。
- [FINDING-010-003](FINDING-010-003.md)：首轮实现封闭了五类角色输入，却没有统一机械化结构化输出边界；已在本地实现中处置为
  五个 closed output schema、exact input/schema receipt binding、可信坐标补入和失败关闭解码，并以完整补证状态机验证。
- [FINDING-010-004](FINDING-010-004.md)：补证编排曾把旧调查的全部 raw Result 与 current Package 一并传给新角色；已收紧为
  current gap 后 Ledger `SOURCE_RESULT` 与 `new_typed_retrieval_results` 的精确有序闭包，旧内容只能经密封 Package 进入补证上下文。
- [FINDING-010-005](FINDING-010-005.md)：全局 source allowlist 无法证明模型声明的 evidence class 对该路径成立；已用 Binding-scoped、
  versioned Source Profile 把 class-specific path capability 贯穿 Request、Broker operation、Worker/Application validation 和 Package，
  同时固定 class + operation 的 Result modality，禁止来源类型或静态观察模态重标。
- [FINDING-010-006](FINDING-010-006.md)：完整 Result digest 会因每次 operation identity 改变，不能判断是否获得新观察；已新增与
  operation identity 解耦的 semantic progress digest，使重复相同调查按 deterministic no-progress fuse 失败关闭。
- [FINDING-010-007](FINDING-010-007.md)：successor Ledger 原先只绑定 parent Ledger seal，未直接绑定 Reviewer gap 所属的 prior
  Package；现已把 Ledger/gap/current Package/successor Package 的 predecessor identity 贯穿并在角色调用前重验。
- [FINDING-010-008](FINDING-010-008.md)：wall-time 原先主要在外部调用前检查，角色可在 deadline 返回 `FINISH/APPROVED` 后仍被接受；
  现已在 Understanding、Cognition、Investigation、Worker、Answer、Review 返回后、状态转换前重验，达到上限即失败关闭。
- [FINDING-010-009](FINDING-010-009.md)：WSGI ingress 原先会静默接受重复 JSON key 和短于 `CONTENT_LENGTH` 的 body；现于产品路由前
  要求 unique-key JSON 与 exact byte count，否则返回 `INVALID_JSON`。
- [FINDING-010-010](FINDING-010-010.md)：首轮只有 Cognition Projector port/fixture，没有把持久化 Structure Read Bundle 装载到新用例的
  产品 Adapter；现已实现 exact Binding/revision/authority 校验、typed projection、确定性 byte bound 和显式截断 Unknown。
- [FINDING-010-011](FINDING-010-011.md)：closed role output receipt 不能授权 Cognition/Ledger/Package 外发；现已形成 exact user run grant
  → 每个动态完整输入的一次性 disclosure grant → Gateway 双重校验 → no-retry audit，并提供 current DeepSeek 与 exact prepared Web 组合。
- [FINDING-010-012](FINDING-010-012.md)：可组合 WSGI 对象不等于可执行产品入口；现已新增通用 trusted launcher，在 listener 前验证
  clean exact product origin、Source revision、published Bundle/Profile/Request/run grant，并密封 0600 launch/terminal audit receipts。
- [FINDING-010-013](FINDING-010-013.md)：冻结前 focused 58/58、docs 389/389 PASS；允许 AF_UNIX 的 full 1108 中 1103 PASS，唯一
  4 FAIL + 1 ERROR 精确属于 `FINDING-008-020`。raw suite 保持 FAIL，只以 exact preserved historical hold gate 继续候选冻结。
- [FINDING-010-014](FINDING-010-014.md)：`mall` 的现代 Java 源码超出已接受 `JAVA_STATIC_CALL_GRAPH@1` 语法子集；exact Maven
  Snapshot 曾继续最早链路验证，但 run-035—042 已反证它足以用于行为问答的旧项目判断；当前由 FINDING-010-132 取代。
- [FINDING-010-015](FINDING-010-015.md)：首次真实 Web 暴露 live role-progress policy 把合法小写 `search/read/parse` 与错误大写常量
  比较，系统性拒绝所有非 FINISH 调查；已改为 authoritative enum values 并补 initial/verification 回归，旧 candidate/run 保持 FAIL。
- [FINDING-010-016](FINDING-010-016.md)：第二次真实 Web 的 FINISH 为三个 UNKNOWN 项返回空引用；investigation Schema/Prompt 与共享
  array validator 原先未表达并重验领域层非空唯一 evidence/boundary reference invariant，现已升级契约并补机械回归，旧 qualification
  因 implementation digest 变化须重新取得。
- [FINDING-010-017](FINDING-010-017.md)：第二次代表题的目录级 SOURCE capability 含 167 个 entry，首个搜索即耗尽规范的 64 文件
  question fuse；下一次只登记登录/JWT 相关 exact 文件，不提高上限、不纳入 `src/main/resources`。
- [FINDING-010-018](FINDING-010-018.md)：第三次真实 Web 证明精确文件 Profile 已不触发 fuse，但模型用自然语言语义描述做 literal search，
  又把 allowlisted path 当成 opaque locator reference；Prompt `@3` 现明确短 literal token、exact typed-result ID 与 path 禁止语义。
- [FINDING-010-019](FINDING-010-019.md)：第四次真实 Web 已正确使用 literal query 与 opaque locator，却重复读取已返回完整内容的同一路径；
  no-progress fuse 正确失败关闭，Prompt `@4` 现要求 query/locator single-use、禁止重复 full-content path 并比较 progress digest。
- [FINDING-010-020](FINDING-010-020.md)：第五次真实 Web 证明 Prompt-only 仍不能可靠约束 latest Ledger basis 与 full-content locator
  单次使用；现把 required basis、eligible locator 和 consumed path 提升为动态角色控制，并由 Application 机械拒绝集合外 locator。
- [FINDING-010-021](FINDING-010-021.md)：Preview Request 的 24-call 默认熔断未与更小的 exact run dispatch grant 对齐；现由同一
  `maximum_dispatches` 绑定 Request、Provider configuration 与 run grant，使 Application 在真实上限内预留 Answer/Review。
- [FINDING-010-022](FINDING-010-022.md)：第六次 Web run 证明 latest-basis/eligible-locator 与审核预留均按设计工作，但 7-call grant 只够
  Understanding + 4 次 Investigation，代表题尚未 FINISH，累计 26/28 后保持 `V-WEB-000 FAIL / blocking`。
- [FINDING-010-023](FINDING-010-023.md)：Browser 曾把 Answer/Review 前的预算关闭也标成 `REVIEWED RESULT`；现按 Result status 区分
  `REVIEWED RESULT`/`FAIL CLOSED`，显示用户可理解的预算 limitation，并在开发者详情保留 exact terminal reason 与阶段到达状态。
- [FINDING-010-024](FINDING-010-024.md)：第七次 Web run 的 FINISH 沿用了前一个 action 的 SOURCE evidence class，既有领域 invariant
  正确失败关闭；Prompt `@6` 现逐操作冻结 evidence class/query/locator/disposition 的合法字段组合，不放宽或静默归一化领域契约。
- [FINDING-010-025](FINDING-010-025.md)：第八次 Web run 的合法 FINISH 把 latest Ledger Result 当成 Package support/boundary reference；
  现从 authoritative Package 分类投影 exact support/boundary eligibility，并在模型前后机械拒绝集合外 disposition 引用，Prompt 升级为 `@7`。
- [FINDING-010-026](FINDING-010-026.md)：首条公开方向题重复执行同一 SOURCE query 并触发 no-progress；根因是 Prompt 要求避免重复，
  角色输入却没有投影先前 query/locator intent。现将 attempt-scoped action intent 追加到 Ledger 并投影给角色，Broker 在 Worker 前机械拒绝
  重复 intent，Prompt 升级为 `@8`；旧题永久失败且不重试。
- [FINDING-010-027](FINDING-010-027.md)：用户现场登录题的主链、3 个 Citation 和独立 Review 均成立，但正文仍主要按 Controller/Service/
  Filter 方法调用顺序展开，并省略 `insertLoginLog` 副作用。原运行不重试、不追认；PDR-001 将旧 `REDIRECT` 推断修订为同轮 `REWORK`。
- [FINDING-010-028](FINDING-010-028.md)：Prompt 要求答案优先，但 Question Understanding 只提供自由文本层级，Answer 只有扁平 Claim，
  Application 机械拼接正文，Reviewer 没有可执行的方向质量 invariant；返工现以受控 detail/content role、逐 Claim checklist links、
  默认正文投影、Reviewer 独立 checklist 与四项 PASS/FAIL Gate 形成通用机械约束，确定性测试通过，真实三题回归仍待新 freeze/live 授权。
- [FINDING-010-029](FINDING-010-029.md)：既有 live launcher 只允许一个 prepared Request/run，与同会话自由提问冲突；现以会话级
  exact authority、用户提交 receipt、System Owner 编译逐题 Request/run 和既有逐角色 one-use disclosure 形成闭合授权链，浏览器不再
  要求普通用户构造 request ID 或 grant。已写回 ADR-016、Engineering QA Contract、Security 与 Local Browser Operations。
- [FINDING-010-030](FINDING-010-030.md)：惰性 Manifest 解析只物化 `rework_result_refs`，会漏掉 file-backed
  `prior_authorization_refs` 并误判合法的同 Slice 返工授权；现以 closed 字段 allowlist 解析两类历史序列，并由文档门禁测试覆盖。
- [FINDING-010-031](FINDING-010-031.md)：loopback Host 不能证明问题由当前页面主动提交；跨站 simple request 仍可能伪造确认并消费调用。
  现于 receipt/transport 前强制 exact same-origin、`application/json` 和可选 `Sec-Fetch-Site: same-origin`，跨站请求失败关闭。
- [FINDING-010-032](FINDING-010-032.md)：返工后完整 1141 项中 1136 PASS，raw 仍为既有 4 FAIL + 1 ERROR；未通过项精确属于冻结的
  V-009 Adapter Conformance 与 Codex binary drift。保持 raw FAIL，只以 zero-new-failure historical hold 继续准备 candidate。
- [FINDING-010-033](FINDING-010-033.md)：首次持续 Alpha 回归再次遗漏完整源码中已存在的成功路径副作用且 Reviewer 错误批准；根因是宽泛
  checklist 可被一个代表性事实伪闭合。协议 `@3` 现要求 FINISH 原子 evidence observations、Answer observation/evidence closure，以及
  Reviewer 从完整 Package evidence 独立比较 Package/Draft observation omission。
- [FINDING-010-034](FINDING-010-034.md)：首次持续 Alpha 的 Gateway SQLite 主文件实际为 `0644`，WAL/SHM 同样没有 private-mode
  创建保证。两个 launcher 现以 exclusive `0600` 创建主文件并在 `0077` mask 下运行 SQLite，测试核对 live sidecars 从创建起均为
  `0600`。
- [FINDING-010-035](FINDING-010-035.md)：协议 `@3` 与 private SQLite 回归后的完整 1144 项中 1139 PASS，raw 只保留既有
  4 FAIL + 1 ERROR；本机 AF_UNIX 重跑消除沙箱额外错误。保持 exact historical hold，不追认冻结 runtime。
- [FINDING-010-036](FINDING-010-036.md)：clean `fc827ce…` 原题已经覆盖登录审计副作用，但 coverage-only Limitation 被非空
  observation-link 规则强迫错绑 supported observations 而失败关闭；收窄为仅末尾 coverage limitation 可用空 link，其他事实 Claim 继续
  强制 observation/evidence closure。
- [FINDING-010-037](FINDING-010-037.md)：coverage-only Limitation 修复后的完整 1147 项中 1142 PASS，raw 仍精确为既有 4 FAIL + 1
  ERROR historical hold；定向错误形状回归与治理 Gate 通过，没有新增 ITER-010 失败。
- [FINDING-010-038](FINDING-010-038.md)：clean `e15ec50…` 原题已采用空-link coverage Limitation，但 Investigation 在只读 README 后过早
  FINISH，Answer 又把 limitation 错标为 process/impact role。保留 Domain fail-closed，并显式下发合法 kind/role mapping 与跨 evidence-class
  未知消减规则。
- [FINDING-010-039](FINDING-010-039.md)：clean `c7e32b5…` 已使原题、登录审计副作用和独立 Review 通过，受控超限请求也保持 listener 与
  零新增 dispatch；但两道后续题的真实 `PROVIDER_HTTP_ERROR` 被 UI/terminal audit 重标为 binding drift/outcome unknown。现仅在完整 exact
  binding 成立时传播真实 terminal failure，并让 policy rejection 携带密封 Result 供外层准确审计；旧会话不追认为三题 PASS。
- [FINDING-010-040](FINDING-010-040.md)：失败分类/审计修复后的完整 1148 项中 1143 PASS，raw 仍精确为冻结 V-009/Codex digest 的既有
  4 FAIL + 1 ERROR；沙箱 AF_UNIX 噪声已在允许本机 socket 的同命令重跑中消除，保持 historical hold 且不追认 live 质量。
- [FINDING-010-041](FINDING-010-041.md)：clean `31a9ccd…` 的新 DeepSeek Conformance 只调用一次即收到官方定义为余额不足的 HTTP 402；
  TLS/credential 成功、retry/switch 0。旧 adapter qualification 仍在有效期且 implementation/config digest 相同，但不能冒充当前账户可用
  或新三题答案；live 保持环境 hold，等待账户持有人恢复余额后以 fresh session 继续。
- [FINDING-010-042](FINDING-010-042.md)：余额恢复后的 fresh Conformance 2/2 PASS；异质构建题的合法 FINISH 返回 9 条原子事实，撞上
  每项 8 条旧上限，且 completed-output rejection 被错误重标为 qualification drift。现以每项 16/全局 64 闭合原子事实，并仅在完整 exact
  binding 成立时传播真实 structured-output failure。
- [FINDING-010-043](FINDING-010-043.md)：旧候选第三题虽被 Reviewer 批准，却用 dynamic manager 接线代替内部权限判定证据，并在默认正文
  重复同一批 observation。现明确 setup/wiring 不证明被委托行为，Reviewer 必须请求决定性证据；Application 机械要求每个 observation 在
  默认用户可见 Claim 中恰好出现一次。
- [FINDING-010-044](FINDING-010-044.md)：clean `34f0496…` 原题的直答已完整自然，但模型追加的过程 Claim 完全重复同 7 个 observation，
  硬拒绝整题没有必要。Application 现按顺序保留首次覆盖、把全冗余后续 Claim 投影到开发者详情；部分交叠仍失败关闭且默认正文仍须覆盖
  精确 observation 全集。
- [FINDING-010-045](FINDING-010-045.md)：clean `47a96b6…` 原题已返回短直答和无重复的逐事实 Claim，但短直答为避免重复使用空 observation
  link，被旧 value rule 与 coverage Limitation 一并拒绝。现允许有 support 的 affirmative DIRECT_ANSWER 作为受控空-link 摘要；它不取得
  observation coverage、只能链接 supported checklist，Reviewer 必须核对其未扩张后续事实。
- [FINDING-010-046](FINDING-010-046.md)：clean `8565fa5…` 的现场题再次只读 README 后把所有结论过早标成全局 Unknown，错误 limitation
  仍被 Reviewer 批准。现由 Source Profile 投影 registered/investigated/untried evidence classes；含 non-supported disposition 的 FINISH
  在 untried 非空时由 Application 追加 required-class GAP 并继续调查，答案抽象层级不再排除 Source behavior evidence；遍历全部
  registered class 的处置已被 `FINDING-010-047` 收窄。
- [FINDING-010-047](FINDING-010-047.md)：clean `8575517…` 已让原登录题读取源码并通过，但两道异质题暴露 registered registry 被误作
  逐题语义最小集，以及 FINISH schema 未联动 outcome/observation kind。现由 Understanding 声明 required classes，Application 只闭合
  untried required，并以条件化 schema 在 Provider 输出边界拒绝 supported/limitation 混类；新 clean candidate/fresh live 仍待执行。
- [FINDING-010-048](FINDING-010-048.md)：clean `5ce5ab0…` 的 run-015 三题证明 class 闭包仍会漏读被委托实现、扁平 Answer Schema 仍允许
  两个直接回答，且 Reviewer 再次漏审持久化审计副作用。现由 Understanding 声明 exact mandatory-read paths，Application 在任何 FINISH 前
  闭合完整读取，并把 Answer 改为唯一 `direct_answer` + 禁止直答的 follow-up claims；新 clean/fresh live 仍待执行。
- [FINDING-010-049](FINDING-010-049.md)：clean `00afecd…` 的 run-016 三题证明 1—8 个 mandatory-read paths 与 12-call 调查熔断
  数学不可达，且非必读 search hit 会继续消耗步骤；第一题的真实 `PROVIDER_OUTCOME_UNKNOWN` 又被误报为 binding drift。现把必读路径上限
  收紧为 4、未闭合时只暴露 required locator、投影 exact remaining fuse，并准确传播已重验 binding 的 outcome unknown。
- [FINDING-010-050](FINDING-010-050.md)：上述修复后 Engineering QA 97/97、docs 444/444、compile/diff PASS；允许 AF_UNIX 的 full
  1163 项中 1158 PASS，raw 唯一 4 FAIL + 1 ERROR 仍精确为冻结 V-009/Codex historical hold，没有 ITER-010 新失败。
- [FINDING-010-051](FINDING-010-051.md)：clean `d12223f…` / run-017 已证明 4-path/fuse 修复可达，三题中构建/resources 题获
  `APPROVED`，但登录与 401/403 题都因合法 follow-up role 被 Provider 以后补 process 的顺序返回而在 Answer Domain 前失败。Gateway
  raw output 保留；可信 adapter 现只按受控 role 稳定归一化展示顺序，不改写任何 Claim 语义、链接或同 role 原顺序。
- [FINDING-010-052](FINDING-010-052.md)：上述修复后 Engineering QA 98/98、docs 446/446、compile/diff PASS；允许 AF_UNIX 的 full
  1164 项中 1159 PASS，raw 唯一 4 FAIL + 1 ERROR 仍精确为冻结 V-009/Codex historical hold，没有 ITER-010 新失败。
- [FINDING-010-053](FINDING-010-053.md)：clean `88e33bd…` / run-018 的登录与构建/resources 题均获 `APPROVED`，401/403 题却因用户
  明确要求的源码核对依据被正确分类为 `IMPLEMENTATION_EVIDENCE` 后无条件移出默认正文而失败。现只隐藏 observation 已由其他可见 Claim
  完整覆盖的实现证据；uniquely material 的简洁核对依据保持可见，部分交叠仍失败关闭。
- [FINDING-010-054](FINDING-010-054.md)：上述修复后 Engineering QA 99/99、docs 448/448、compile/diff PASS；允许 AF_UNIX 的 full
  1165 项中 1160 PASS，raw 唯一 4 FAIL + 1 ERROR 仍精确为冻结 V-009/Codex historical hold，没有 ITER-010 新失败。
- [FINDING-010-055](FINDING-010-055.md)：clean `c65617e…` / run-019 的三题均获模型 `APPROVED`，但独立复核发现 401/403 正文先把
  未认证与权限不足都归为 403，随后又正确分流为 401/403；Reviewer 逐字复述冲突却仍全 PASS。现新增 closed `claim_consistency` Gate，
  成对审核 direct/default Claims、Package 与独立 observations；五项全 PASS 才能批准。
- [FINDING-010-056](FINDING-010-056.md)：上述修复后 Engineering QA 99/99、docs 450/450、compile/diff PASS；允许 AF_UNIX 的 full
  1165 项中 1160 PASS，raw 唯一 4 FAIL + 1 ERROR 仍精确为冻结 V-009/Codex historical hold，没有 ITER-010 新失败。
- [FINDING-010-057](FINDING-010-057.md)：clean `274e5ea…` / run-020 的 Q2 已声明 4 个 exact mandatory paths，却因角色拿不到 direct
  locator 而把 path/filename 当内容搜索词，零命中与重复动作在 5 次 dispatch 后触发 no-progress fuse。现由 Application/Broker 为每个已验证
  required path 签发 Request + attempt + Profile + class + path 绑定的 opaque direct locator；模型仍无 path authority。
- [FINDING-010-058](FINDING-010-058.md)：run-020 的 Q3 已完整读取四个决定性实现，却在一个 `SUPPORTED` FINISH item 中再次混入
  `LIMITATION` 与 search-only boundary reference，被本地 validator 正确关闭。Provider-facing FINISH 现拆为结构互斥的
  supported/non-supported 数组；Prompt 同时禁止因“可核对依据”擅自引入无关 TEST/log/config need。
- [FINDING-010-059](FINDING-010-059.md)：上述修复后 Engineering QA 101/101、docs 453/453、compile/diff PASS；允许 AF_UNIX 的
  full 1167 项中 1162 PASS，raw 唯一 4 FAIL + 1 ERROR 仍精确为冻结 V-009/Codex historical hold，没有 ITER-010 新失败。
- [FINDING-010-060](FINDING-010-060.md)：clean `dfba244…` / run-021 的 Q1/Q3 各以 8 次 dispatch 获得独立可接受的
  `APPROVED`，Q2 已用 direct locator 完整读取 4 个 mandatory paths，却把 3 个 UNKNOWN 同时放入 supported 与 non-supported arrays 而
  正确失败关闭，且尚余 8 个含当前动作的调查 call。现要求 FINISH partition disjoint + exact-once，并明确 mandatory minimum 不是调查上限。
- [FINDING-010-061](FINDING-010-061.md)：上述修复后 Engineering QA 101/101、docs 455/455、compile/diff PASS；允许 AF_UNIX 的
  full 1167 项中 1162 PASS，raw 唯一 4 FAIL + 1 ERROR 仍精确为冻结 V-009/Codex historical hold，没有 ITER-010 新失败。
- [FINDING-010-062](FINDING-010-062.md)：clean `be15a0a…` / run-022 的首个 Investigation 已选合法 direct locator 与 current basis，却
  返回空 `checklist_item_ids`；Domain 正确关闭，而 Provider Schema 原来允许空/重复数组。现把 checklist/basis 两个绑定数组与 Domain 对齐为
  non-empty + unique，并保留 Application exact binding 重验。
- [FINDING-010-063](FINDING-010-063.md)：上述修复后三模块 65/65、Engineering QA 102/102、docs/compile/diff PASS；允许 AF_UNIX 的
  full 1168 项中 1163 PASS，raw 唯一 4 FAIL + 1 ERROR 仍精确为冻结 V-009/Codex historical hold，没有 ITER-010 新失败。
- [FINDING-010-064](FINDING-010-064.md)：clean `656b549…` / run-023 的 Q1/Q2 独立可接受，Q3 却从上游 empty-context/deny 无据推导
  最终 401/403，并把同一局部条件分配到互斥外部结果，Reviewer 仍误判 consistency PASS。现要求外部 status/error/body 回到下游
  response/exception mapper full-content owner evidence，handler wiring 只证明选择，并把 transport status 与 response-body code 分开。
- [FINDING-010-065](FINDING-010-065.md)：上述修复后三模块 65/65、Engineering QA 102/102、docs/compile/diff PASS；允许 AF_UNIX 的
  full 1168 项中 1163 PASS，raw 唯一 4 FAIL + 1 ERROR 仍精确为冻结 V-009/Codex historical hold，没有 ITER-010 新失败。
- [FINDING-010-066](FINDING-010-066.md)：clean `740c74a…` / run-024 的 Q1 因 parent 漏抄一个 child reference、Q3 因把 UNKNOWN
  重复分装进两个数组而失败；两者都是 Provider 重复维护 JSON Schema 无法表达的跨字段等式。现已改为单一 tagged disposition 数组，并由
  trusted Adapter 从 child observations 稳定派生 parent reference closure。
- [FINDING-010-067](FINDING-010-067.md)：run-024 Q2 的 Reviewer 两次明确指出当前 Package 缺少 dynamic authorization 实现，却两次
  独立声明 `REWRITE_REQUIRED + null request`，最终触发同 Package rewrite fuse。现让每条 Finding 使用受控 remediation variant，由
  Adapter/Application 派生 review action 与 Verification Request，并限制补证服务于原问题 material scope。
- [FINDING-010-068](FINDING-010-068.md)：旧 ITER-007 readiness 单测把历史冻结 Contract 摘要用今天的 current System 文档重算，随合法
  Contract 演进产生伪回归。现直接核对当时冻结的 schema/digest，不修改历史 Manifest，也不削弱活动 Iteration 的 current fileset Gate。
- [FINDING-010-069](FINDING-010-069.md)：上述处置后 Engineering QA 106/106、current docs 463/463、含 docs Gate 139/139、compile/diff PASS；允许 AF_UNIX 的
  full 1172 项中 1167 PASS，raw 唯一 4 FAIL + 1 ERROR 仍精确为冻结 V-009/Codex historical hold，没有 ITER-010 新失败。
- [FINDING-010-070](FINDING-010-070.md)：clean `7fb7e7c…` / run-025 的 Q2 已由 Reviewer/Application 正确派生只绑定 `check-3` 的
  Verification Request，补证 FINISH 也正确只返回该项，却被共享的“完整 Checklist exact-once”规则拒绝。现区分 Initial 全量 scope 与
  Verification 单 gap scope，并由可信 Application 保序替换 predecessor Package 唯一目标、原样保留非目标 disposition。
- [FINDING-010-071](FINDING-010-071.md)：run-025 的补证输入未把 predecessor Package 已有 full-content source 当作 consumed，且最新
  Broker duplicate rejection 只埋在长 Ledger 中，造成重复读与重复动作。现投影 Package + 新 Result consumed-path 并集和当前 attempt
  最近 Broker rejection；不重新披露旧 raw Result，不扩大 path/operation authority，也不削弱 duplicate/no-progress fuse。
- [FINDING-010-072](FINDING-010-072.md)：上述处置后 Engineering QA 109/109、docs 组合 142/142、历史 oracle 组合 74/74、current docs
  466/466、compile/diff PASS；允许 AF_UNIX 的 full 1175 项中 1170 PASS，raw 唯一 4 FAIL + 1 ERROR 仍精确为冻结 historical hold，
  没有 ITER-010 新失败。
- [FINDING-010-073](FINDING-010-073.md)：clean `32a00a3…` / run-026 的 Q2 Verification limitation 错借 predecessor Package 中与当前
  gap 无关的 cognition unknown，Q3 Reviewer 又重复请求已经受控穷尽并诚实披露的同一 gap。现排除 predecessor boundary、强制每个
  非支持 observation 保留当前 gap boundary，并向 Reviewer 投影 terminal verified gap；非必要 Draft 扩张只能同包删除或收窄。
- [FINDING-010-074](FINDING-010-074.md)：上述处置及 typed `VERIFICATION_GAP` 独立审计后，focused 76/76、Engineering QA
  113/113、docs 组合 146/146、历史 oracle 组合 78/78、current docs 468/468、compile/diff PASS；允许 AF_UNIX 的
  full 1179 项中 1174 PASS，raw 唯一 4 FAIL + 1 ERROR 仍精确为冻结 historical hold，没有 ITER-010 新失败。
- [FINDING-010-075](FINDING-010-075.md)：clean `b709fad…` / run-027 的 Q1 独立复核 PASS，但 Q2/Q3 被单一 Reviewer 错误
  `APPROVED`；placeholder、unmounted type 和 downstream status 的证据所有权均被扩张。现把 comprehensive Review 降为
  provisional，再由 fresh evidence-boundary challenge 独立授权；focused 78/78、Engineering QA 115/115 PASS，扩展 Gate 与新 live 待闭合。
- [FINDING-010-076](FINDING-010-076.md)：上述双审处置经 focused 78/78、Engineering QA 115/115、docs 组合 148/148、历史 oracle
  组合 80/80、current docs/compile/diff 与 full 1181/1176 exact historical hold 闭合 deterministic Gate；新 clean/fresh live 是下一 Gate。
- [FINDING-010-077](FINDING-010-077.md)：clean `f832ceb…` / run-028 的 Q1/Q3 独立 PASS，Q2 仍把 caller getter 扩张为未挂载 DTO
  fields/wire property；fresh challenge 已收到精确 type lead 却原样复述并错误 `APPROVED`。现为每个 lead 密封稳定 `challenge_id`，要求
  challenge 逐项返回 evidence/Draft scope 与受控 disposition，Application 重算 exact ID 集合并校验越界 Finding 绑定后才可授权。
- [FINDING-010-078](FINDING-010-078.md)：上述处置后 focused 78/78、Engineering QA 115/115、docs 组合 148/148、历史 oracle
  组合 80/80、current docs/compile/diff 与 full 1181/1176 exact historical hold 闭合 deterministic Gate；新 clean/fresh live 是下一 Gate。
- [FINDING-010-079](FINDING-010-079.md)：run-029 证明 comprehensive approval 仍会漏掉完整 Java entry 中的 material effect，并暴露
  rewrite 丢失安全 observation 与 challenge Finding 错绑；现投影逐 entry effect scan、Answer exact observation table 与 exact Claim binding。
- [FINDING-010-080](FINDING-010-080.md)：上述处置以 focused 79/79、Engineering QA 116/116、docs/oracle/full exact historical hold
  闭合 deterministic Gate；没有 ITER-010 新失败。
- [FINDING-010-081](FINDING-010-081.md)：run-030 的 Q1/Q3 独立 PASS；Q2 页面虽 APPROVED，却遗漏 login token → protected request
  handoff 与 resources-excluded header/prefix unknown，实际仍为 FAIL。
- [FINDING-010-082](FINDING-010-082.md)：startup/call/use/integrate/diagnose 现要求 operational checklist、输入输出 handoff 和通用
  original-question fulfillment scan，缺 material 用户目标必须失败并形成绑定 Finding。
- [FINDING-010-083](FINDING-010-083.md)：上述处置以 focused 80/80、Engineering QA 117/117、docs/oracle/full exact historical hold
  闭合 deterministic Gate；没有 ITER-010 新失败。
- [FINDING-010-084](FINDING-010-084.md)：run-031 的 Q1 发现 cache write，却把缺失 Application observation 错选成第二次同包 rewrite；
  现要求 exact omitted-effect statements 与 `APPLICATION_PACKAGE / DEFAULT_DRAFT` closed layer，不放宽 rewrite fuse。
- [FINDING-010-085](FINDING-010-085.md)：上述 layer、statement membership、entry/class/remediation 重算以 focused 80/80、
  Engineering QA 117/117、docs/oracle/full exact historical hold 闭合 deterministic Gate。
- [FINDING-010-086](FINDING-010-086.md)：run-032 证明 observation 使用 `retrieval_item_*` source reference，而旧 challenge/Application
  错拿 `support_entry_*` 直接比较并形成伪空集；Q1 PASS、Q2 FAIL、Q3 OUTCOME_UNKNOWN、66,000-byte Provider 前拒绝均永久保留。
- [FINDING-010-087](FINDING-010-087.md)：统一 exact entry → source-reference resolver 与 application-missing-first layer precedence 后，
  focused 80/80、Engineering QA 117/117、docs/oracle/full exact historical hold 已闭合；新 clean/fresh live 是下一 Gate。
- [FINDING-010-088](FINDING-010-088.md)：clean `d70a3e6…` / run-033 的 Q1 证明 single-gap replacement 可静默删除 target 中既有
  supported observations；Q2 admissible-reference FAIL、Q3 post-dispatch OUTCOME_UNKNOWN 与 66,000-byte Provider 前拒绝均独立保留。
  现要求 supported target exact/relative-order monotonic preservation，并把 `APPLICATION_PACKAGE` gap 收窄为 caller full content 已可见 effect，
  不追索未挂载 callee 内部。
- [FINDING-010-089](FINDING-010-089.md)：上述 monotonic merge、preservation contract 与 caller-visible effect boundary 已以 focused
  80/80、Engineering QA 117/117、docs/oracle/full exact historical hold 闭合；新 clean/fresh live 是下一 Gate。
- [FINDING-010-090](FINDING-010-090.md)：新 clean `fe6b6b6…` / run-034 的第一条 fresh Conformance request 在 credential/TLS/HTTP
  成功后仍收到 DeepSeek 402；request 1、retry/switch 0，无 Qualification/Alpha/Browser/Production。当前 key 所属账户余额恢复前保持
  configuration-environment hold。
- [FINDING-010-091](FINDING-010-091.md)：用户报告 ITER-010 约 14 小时仍无新体验版本且 DeepSeek token 消耗过多；现把根因处置为
  Access/Quality/hardening 串行化的迭代设计缺陷，并以 PDR-003 的体验优先、硬时限和轻量 live-attempt 规则恢复。
- [FINDING-010-092](FINDING-010-092.md)：当前 Engineering QA 尚未落实对用户透明的 Ark-primary/DeepSeek 独立 fallback attempt；已处置到
  ADR-017/Model Gateway，并要求同一 logical question 不重提、不共享中间态、late result 不覆盖、同 identity 有效 Conformance 复用，且
  DeepSeek 批次价格状态逐次复核、成本不削弱质量。
- [FINDING-010-093](FINDING-010-093.md)：当前多层固定内容流水线保留了安全与证据边界，却没有正式的主工程 Agent 来持续拥有用户目标、
  假设、计划、观察、重规划与完成判断；已处置为“软件世界模型 + 主工程 Agent”双核心和 ADR-018。
- [FINDING-010-094](FINDING-010-094.md)：当前 Session 只共享工程、授权和资源熔断，每题仍是没有历史/指代/纠正的独立 Request；已处置为
  server-owned Conversation/Turn/Context、逐轮证据与 Review、新对话隔离和五轮 Chat canary。
- [FINDING-010-095](FINDING-010-095.md)：新的独立 Chat Access 已以 server-owned Conversation/Turn/Context、消息历史、新对话隔离、
  0-dispatch Provider 失败真相和固定 loopback 命令形成本地确定性候选；真实 listener/browser 尚未执行，故 `V-ALPHA-ACCESS-001`
  继续为 NOT-RUN，旧 QA 入口保持兼容身份。
- [FINDING-010-096](FINDING-010-096.md)：clean `cf2883b…` 上真实 fixed-command listener 和 in-app Browser 证明失败 Turn 隔离、完整历史、
  新 Conversation 消息隔离及零 Provider 调度成立；`V-ALPHA-ACCESS-001` 更新为 `PASS / access-only`，所有 Chat/Quality 后续 Case 仍 NOT-RUN。
- [FINDING-010-097](FINDING-010-097.md)：Application-owned 主 Agent loop、跨 Turn Work State、密封 Observation/Package、fresh Review
  Finding 回路、exact Delivery binding 与失败 Turn 隔离已形成本地确定性候选并通过 48/48；真实 Provider/World Model/Source/Ledger/Citation、
  launcher wiring、五轮 live Chat 和 Production 仍未集成、资格化或执行。
- [FINDING-010-098](FINDING-010-098.md)：现有 World Model projector、Source Broker/Worker 与逐 Turn Ledger/Citation authority receipt 已接成
  trusted evidence-tool adapter；support/boundary 分区与 opaque locator search→read 在临时 Git 上通过，mall/live 未执行。
- [FINDING-010-099](FINDING-010-099.md)：主 Agent/Reviewer 的 closed no-tools 模型输入输出、逐 dispatch Disclosure/Gateway receipt、
  失败计数和非调度 candidate preflight 已形成本地候选；双 Provider fallback、fixed Provider launcher 与五轮 live Chat 仍阻断。
- [FINDING-010-100](FINDING-010-100.md)：Application-owned Ark→DeepSeek route 现以 typed owner classification、两个隔离 full-chain
  attempt、committed Work State repository、logical Turn 分账与 late quarantine 形成本地组合候选；固定组合预检保持全部 I/O 为 0，真实
  Adapter/transport/credential、Access-only 命令切换和五轮 live Chat 仍未资格化或执行。
- [FINDING-010-101](FINDING-010-101.md)：生产 Ark/DeepSeek Adapter、credential-lazy transport、Model Gateway、Session Disclosure 与
  Conversational Agent model boundary 已接入双 route 的 non-starting composition；79/79 本地组合通过，但 current sealed Conformance、
  Source/World Model runtime、fixed command Session 和 live 尚未加载或执行。
- [FINDING-010-102](FINDING-010-102.md)：Provider runtimes、exact evidence authority、per-attempt fresh Tool/Response Control、committed Work
  State、route、Conversation 与 Browser 已形成完整 non-starting Session runtime composition；89/89 通过，artifact config/fixed command/live
  仍未闭合。
- [FINDING-010-103](FINDING-010-103.md)：owner-private closed artifact Session loader 与唯一 `--session-config` fixed-command lifecycle 已
  闭合 product/source identity、published World Model、Source Profile、ordered Ark→DeepSeek qualification identity、private Gateway/receipt
  paths 和固定 5×15/75 bounds；相关聚焦组合 117/117，通过 fake listener 证明 launch-before-listener/terminal-after-shutdown。current actual
  artifact、Ark transport Session audit 与五轮 live Chat 仍未执行或资格化。
- [FINDING-010-104](FINDING-010-104.md)：Ark direct transport 现固定为每 request 一个 verified TLS session、TLS 后取 credential、每 session
  一个 HTTP dispatch、retry 0，并以 strict Session audit 接入 Conformance 与 artifact terminal；HTTP 前不可用又经 Gateway owner-typed
  classification 接入既有独立 fallback。旧 Ark Conformance 明确失效，fresh Conformance、current artifact 与五轮 live Chat 仍阻断。
- [FINDING-010-105](FINDING-010-105.md)：clean `1e99e9b…` 的 fresh Ark Conformance 已以 2/2 request、13/13 Case、TLS/credential
  `2/2`、reuse/retry/unknown 0 PASS；current Ark qualification 可用。artifact Gate 复核同时证明旧 DeepSeek qualification 因共享
  Gateway implementation drift stale，故下一步先取得 fresh DeepSeek Conformance，再生成 current artifact。
- [FINDING-010-106](FINDING-010-106.md)：clean `653eff3…` 的 fresh DeepSeek Conformance 已以 2/2 request、12/12 Case、TLS
  `1/1`、credential `2/2`、connection reuse 1、retry/unknown 0 PASS；结合 fresh Ark Result，双 Provider qualification 当前同时可用。
  Conformance grant 不授权 Source/World Model disclosure、artifact Session 或 Browser，下一 Gate 是 exact five-Turn Session authorization。
- [FINDING-010-107](FINDING-010-107.md)：exact `eb835f5…` / `run-035-chat-alpha` 已执行 owner-private 五轮 Chat 与新对话
  leakage probe；五轮 5/5 失败且没有 Answer/Citation/Review/Delivery。新 Conversation transcript 隔离成立，但省略指代返回通用
  pre-dispatch failure 而非澄清；20 logical dispatch、retry 0、private files、clean stop 与 Production `NOT_EXECUTED` 已密封。
- [FINDING-010-108](FINDING-010-108.md)：首次 live 的最早 Source 偏差是 model-facing semantic-search 许诺与 Worker 大小写敏感 literal
  semantics 不一致；现将 query 收紧为短 literal token，并只用授权 path metadata 在固定 file/byte/result fuses 前确定性排序候选。
- [FINDING-010-109](FINDING-010-109.md)：空新 Conversation 的省略指代不能依赖 Provider 或 Session budget；现由
  `ENGINEERING_CHAT_BINDING@2` 固定 versioned zh-CN input policy，在 World Model/Source/credential/Provider 前返回非事实澄清。该修复与
  FINDING-010-108 均只是 local candidate，必须在新 exact product/session grant 下重验。
- [FINDING-010-110](FINDING-010-110.md)：组合审计发现大目录 SEARCH 即使先命中目标，仍会消费全部 64 个总文件名额，使签发的 locator
  无法 READ。Broker 现在在不提高总熔断的前提下为后续 exact READ/PARSE 保留 1 个名额；71 文件、同一固定五轮与新对话负测的
  deterministic successor canary 已闭合，真实 Provider/browser 仍须新 exact Session Authority。
- [FINDING-010-111](FINDING-010-111.md)：exact `999616d…` / `run-036-chat-alpha` 第二次真实五轮仍 5/5 失败，24 logical dispatch、retry 0；
  新 Conversation 的“它呢？”首次真实通过 Application clarification、Context 隔离与零 dispatch。证据分离了 Source 多 READ 容量、Draft
  跨 disposition 引用和独立 transport failure，run 永久保持 FAIL。
- [FINDING-010-112](FINDING-010-112.md)：同 signature 复现触发架构职责评审；Source 资源契约现把 per-SEARCH scan fuse 56 与 whole-Turn
  actual file fuse 64 显式分开。73 文件相邻案例在 PARTIAL Coverage 下继续完成 3 个不同 locator READ，累计 59/64，不增加任何总上限。
- [FINDING-010-113](FINDING-010-113.md)：Primary input/strategy/prompt 升级到 v2，由可信 Application 投影 ANSWER SUPPORT 与 LIMITATION
  BOUNDARY 的 closed ID domains；decoder 继续重算并 fail closed，不修补模型输出。旧双 Provider Conformance 因 identity 改变而失效。
- [FINDING-010-114](FINDING-010-114.md)：exact `d429be6…` / `400d579…` 的 fresh DeepSeek 与补充 Ark Conformance 均以固定 2/2
  request、12/12 与 13/13 Case、retry/unknown 0 PASS；Ark 补充 TLS acquisition 使用 4/10，只有 credential/HTTP 均为 0 的失败 run
  被重新启动。两份资格只允许条件式 run-037，不证明答案质量。
- [FINDING-010-115](FINDING-010-115.md)：`run-037-chat-alpha` 固定五轮再次 0/5，终态为 Review limit / No progress /
  Outcome unknown / No progress / Outcome unknown，总 logical dispatch 31、retry 0；新 Conversation 继续以空 Context、零 dispatch
  clarification PASS。最早产品偏差是缺失 Tool proposal copy domain 与 Reviewer 正负判断合同，transport/JSON failure 均按策略关闭。
- [FINDING-010-116](FINDING-010-116.md)：Primary input v3 现在由 Application 密封 current-attempt `prior_actions`、已尝试 query/read 和
  authority-receipt 派生的未使用 `source_read_options`；decoder 拒绝 exact action 重复、参数漂移和未签发 locator，不增加任何资源熔断。
- [FINDING-010-117](FINDING-010-117.md)：Review input/output 升级到 v2，对 exact ordered Claim set 强制完整 `SUPPORTED/DEFECT`
  assessments，并重算 assessment↔Finding↔decision 一致性；role prompt v3 明确禁止 JSON 外叙述，closed adapter 不增加 substring 修复。
  v3 successor 仍需 fresh 双 Provider Conformance 与新 Live Authority。
- [FINDING-010-118](FINDING-010-118.md)：exact `743942d…` / `748902c…` 的 fresh Ark 与 DeepSeek Conformance 分别以固定
  2/2 request、13/13 与 12/12 Case、retry/unknown 0 PASS；资格只允许条件式 run-038，不证明答案质量。
- [FINDING-010-119](FINDING-010-119.md)：`run-038-chat-alpha` 四轮失败，仅 Turn 5 形成 `REVIEWED_LIMITATION`，整体仍为
  1/5 / Quality FAIL；29 logical dispatch、retry 0、private artifact、clean stop 与 Production `NOT_EXECUTED` 已密封，新 Conversation
  clarification/隔离/零 dispatch 继续 PASS。
- [FINDING-010-120](FINDING-010-120.md)：Primary input v4 的 Source Read copy domain 现在按 canonical resource 去重；任意 line
  reference 已读即移除同资源全部 option，terminal Source operation/file/byte fuse 后 Source Search/Read 退出 effective catalog。
- [FINDING-010-121](FINDING-010-121.md)：连续无进展不再继续调查，而是进入无工具的 `EVIDENCE_ONLY_SYNTHESIS`；只允许基于已有
  SUPPORT/BOUNDARY 的 Answer/Limitation，并仍须 fresh Review/Response Control，Reviewer 要求新证据时 fail closed。
- [FINDING-010-122](FINDING-010-122.md)：Artifact preparation 测试的 qualification validity 现绑定 Adapter 实际 UTC clock，消除固定
  测试日期自然过期造成的伪 `QUALIFICATION_INVALID`；产品资格规则没有变化。
- [FINDING-010-123](FINDING-010-123.md)：exact `34d98ae…` / `b9100b1…` 的 fresh Ark 与 DeepSeek Conformance 分别以固定
  2/2 request、13/13 与 12/12 Case、retry/unknown 0 PASS；一次 Ark credential/HTTP 前 TLS failure 按授权 fresh restart，资格只允许
  条件式 run-040，不证明答案质量。
- [FINDING-010-124](FINDING-010-124.md)：`run-040-chat-alpha` 四轮失败，仅 Turn 2 形成 `REVIEWED_LIMITATION`，整体仍为
  1/5 / Quality FAIL；28 logical dispatch、retry 0、private artifact、clean stop 与 Production `NOT_EXECUTED` 已密封，新 Conversation
  clarification/隔离/零 dispatch 继续 PASS。run-039 的 Binding mismatch 在 listener/credential/Source/Provider 前失败，不是 live attempt。
- [FINDING-010-125](FINDING-010-125.md)：Primary input v5 以 `work_state_reference_policy` 只授权 exact current-Turn Observation 和
  correction/superseded prefixes，不再披露 prior-Turn Observation IDs；Reviewer 要求新 Evidence 时 successor 只能提交一个 exact tool
  action。decoder/fuses 不放宽，v5 仍需 fresh 双 Provider Conformance 与新 Live Authority。
- [FINDING-010-126](FINDING-010-126.md)：exact `6e97bc1…` / `fd54821…` 的 fresh Ark 与 DeepSeek Conformance 分别以固定
  2/2 request、13/13 与 12/12 Case、retry/unknown 0 PASS；两个 Ark credential/HTTP 前 TLS failure 按授权 fresh restart，资格只允许
  条件式 run-041，不证明答案质量。
- [FINDING-010-127](FINDING-010-127.md)：`run-041-chat-alpha` 的 Turn 1 Answer 与 Turn 3/4 reviewed Limitation 技术成功，提升到
  3/5，但 Turn 2/5 仍为 model-call rejection，整体 Quality FAIL；28 logical dispatch、retry/unknown 0、private artifact、clean stop 与
  Production `NOT_EXECUTED` 已密封，新 Conversation clarification/隔离/零 dispatch 继续 PASS。
- [FINDING-010-128](FINDING-010-128.md)：Primary input v6 让 `allowed_response_kinds` 只列 current SUPPORT/BOUNDARY 实际支持的
  Answer/Limitation，并把已用 query 与未用 locator 直接投影为对应工具参数的 forbidden/allowed exact values；decoder 继续从原 Evidence 与
  action history 重算。相关 Chat contract 84/84 PASS，v6 仍需 fresh 双 Provider Conformance 与新 Live Authority。
- [FINDING-010-129](FINDING-010-129.md)：exact `3b8d09c…` / `6728a5a…` 的 fresh Ark 与 DeepSeek Conformance 均一次以固定
  2/2 request、13/13 与 12/12 Case、retry/TLS failure/unknown 0 PASS；资格只允许条件式 run-042，不证明答案质量。
- [FINDING-010-130](FINDING-010-130.md)：`run-042-chat-alpha` 的 Turn 2/3/4 为 Package-boundary Limitation，Turn 1/5 失败，仍为
  3/5 / Quality FAIL；43 logical dispatch、retry/unknown 0、private artifact、clean stop 与 Production `NOT_EXECUTED` 已密封，新
  Conversation clarification/隔离/零 dispatch 继续 PASS；源码存在未调查事实，故这些 Limitation 不是产品质量 PASS。
- [FINDING-010-131](FINDING-010-131.md)：v7 的 path-relevance query guidance 与 Review materiality 只有字段投影测试，没有逐层归因、
  真实答案或跨题证据；已作为未接受症状实验由 FINDING-010-133 取代，不再进入 current Contract 或 fresh 双资格重跑。
- [FINDING-010-132](FINDING-010-132.md)：run-035—042 唯一 World Model input 只有 Maven 模块与依赖；该窄 Profile 本身正确，但对行为、
  流程、职责、配置和故障问题无工程认知资格。已处置到 ADR-018 与相关 Knowledge/Application/Product/Quality Owner。
- [FINDING-010-133](FINDING-010-133.md)：run-042 同时存在 Cognition coverage、Agent 调查和 Reviewer 守门故障，v7 不能作为根因修复；
  已处置到长期逐层归因 Gate，并成为 PDR-005 恢复的第一阻断项。
- [FINDING-010-134](FINDING-010-134.md)：run-042 的逐 material-fact、六臂离线替换已密封：行为事实 first divergence 是 Knowledge
  construction/admission；Agent 漏读与 Reviewer 放行/扩域是独立下游故障，Web 无 display first divergence。下一产品修改只进入
  Knowledge/Application 的多 Profile Manifest、Question Eligibility 与问题相关投影。
- [FINDING-010-135](FINDING-010-135.md)：普通 parseable Java 超出窄 legacy closure 时不能整包丢弃正向事实；现以完整
  file/type/member-method disposition manifest 发布同 declaring type、唯一 name+arity 的正向 call-site facts，保持所有不完整 facet、
  nested executable boundary 和禁止负向推断。
- [FINDING-010-136](FINDING-010-136.md)：工程认知资格同时绑定原问题 Need 的 dimension 与 versioned query capability，并保留每个
  Profile 独立 Snapshot/Read Authority；artifact Session `@2` 逐 Profile 固定完整 artifact identity，`@1` 仅保留单 Profile兼容。
- [FINDING-010-137](FINDING-010-137.md)：缺少 external grant 只阻断对应 exact action，不终止仍获授权的开发；到达权限边界必须先冻结
  最小 request 并直接申请，批准后自动续跑。timebox/Gate failure 只阻止晋级、扩域和无新证据外部重跑。
- [FINDING-010-138](FINDING-010-138.md)：PDR-005 canary 证明 Java Snapshot 虽含 exact `UmsAdminServiceImpl.login`，中文 original Turn
  的 lexical projection 却漏掉该 entity；Agent 的 semantic `evidence_need` 没有成为受控 World Model query argument，后续 Source scan
  又被 `loginType` 同词噪声耗尽。clean `3a6089f…` 已把 semantic need 与 exact Turn 交由 Application 编译，并以登录、Maven 结构和 SKU
  行为三类真实 bundle 离线诊断闭合本地修复；live Agent/Source/答案质量仍待新 canary。
- [FINDING-010-139](FINDING-010-139.md)：run-043 在北京时间高峰窗口执行 DeepSeek 18 次，且没有 fresh official check、window verdict
  或 peak override receipt；根因是“闲时优先”没有成为调用前机械 Gate。已处置到 PDR-007，clean `03520eb…` 与
  `V-DEEPSEEK-IDLE-001` 已闭合本地机械 Gate；后继真实 dispatch 仍需新 grant、允许窗口和 `@3` receipt，峰时 Ark-only 与本地开发继续。
- [FINDING-010-140](FINDING-010-140.md)：公开 Apache-2.0 mall 测试工程与当前 Slice 已有持续 human authority；此前把逐 run/Turn/
  dispatch 的机器审计收据误当成逐次人工授权。已处置到 PDR-008：current scope 内自动派生 one-use receipts，Ark 与闲时 DeepSeek 不再
  请求重复批准；runtime 尚待 `V-PUBLIC-OSS-AUTHORITY-001` 验证，峰时、私有/不同来源和其他真正 scope delta 仍须 exact authorization。

后续 Finding 按实现反馈规则逐一落位，不能只写在 Result 中。
