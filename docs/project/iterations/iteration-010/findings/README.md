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

后续 Finding 按实现反馈规则逐一落位，不能只写在 Result 中。
