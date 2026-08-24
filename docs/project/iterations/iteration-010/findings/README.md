---
id: ITER-010-FINDINGS
kind: iteration-findings-index
status: open
authority: development-evidence
owners: [engineering, architecture, quality]
depends_on: [PROJECT-GOVERNANCE-IMPLEMENTATION-FEEDBACK, ITER-010-PROPOSAL]
code: []
tests: []
iteration: ITER-010
---

# ITER-010 Findings

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
  Snapshot 可继续最早 Web，但不能替代 `V-XD-001` 要求的 declaration/`CALLS`，该 Gate 保持 blocking。
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

后续 Finding 按实现反馈规则逐一落位，不能只写在 Result 中。
