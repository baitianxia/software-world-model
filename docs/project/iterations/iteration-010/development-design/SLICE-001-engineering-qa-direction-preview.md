---
id: ITER-010-SLICE-001
kind: development-slice
status: authorized
authority: current-development
owners: [engineering, architecture, quality, product]
depends_on: [ITER-010-PROPOSAL, ITER-010-READINESS, ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST, ITER-006-RESULT-ACCEPTANCE, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, FINDING-010-001, FINDING-010-002, SYS-ADR-013, SYS-ADR-014, SYS-ADR-015, SYS-ADR-016, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-QUALITY-SECURITY]
code: [src/software_world_model/application_services, src/software_world_model/ai_infrastructure, src/software_world_model/interface]
tests: [tests]
iteration: ITER-010
coding_input: true
product_goal_gate: V-000
product_goal_accepted_capability_refs: [ITER-006-RESULT-ACCEPTANCE]
product_goal_cross_domain_case_ids: [V-XD-001]
product_goal_web_checkpoint_id: V-WEB-000
direction_preview_web_checkpoint_id: V-WEB-001
product_goal_direction_preview_checkpoint_id: V-PREVIEW-001
product_goal_reflection_gate_case_id: V-REFLECT-001
product_goal_slice_gate_case_ids: [V-BASELINE-001, V-ARCH-001, V-COGNITION-001, V-QINTENT-001, V-INVESTIGATE-001, V-BROKER-001, V-LEDGER-001, V-ISOLATION-001, V-ANSWER-001, V-REVIEW-001, V-LIMIT-001, V-SEC-001, V-XD-001, V-WEB-000, V-WEB-001, V-PREVIEW-001, V-REFLECT-001]
---

# SLICE-001：最小自适应调查纵切与真实方向体验

## Status and dependencies

`AUTHORIZED / CURRENT DEVELOPMENT / CODING INPUT`。用户以
`codex-user-message:sha256:585f02c4edcf25502b40f880c17a7bdf7f1af71044cd8d1bbe97b055a735ee9e`（`2026-08-21T09:18:34Z`）
接受 Readiness 并只授权本 Slice。`SLICE-002/003` 不随之授权；此前绑定修正前一次性检索/先封包设计的收据不构成本 Slice 的权限来源。

开发 baseline 仍候选绑定 commit `1fb997bab6444523f82ebf1a514a1abbf79656c7` / tree
`1369ce932c778c57a118123e8257ede476229d73`；冻结的 planning commit/tree 为
`01dcfe2233625dfaa021495850fb18ae1323063b` / `8e364ae854bfaa48580ab080a3e0d9c9c43c3d6f`。本开发授权不允许
credential、Provider/model call、live Web/browser、源码片段外发、hidden disclosure 或 Production；live 必须在产品 freeze 后另取 exact grant。

## Product-goal contribution and cumulative integration

- Product delta：把“固定调查后代码走读”推进为“世界模型认知引导、模型自适应读源码、答案优先”的真实纵切。
- Existing capability：复用 ITER-006 exact Snapshot、declaration/`CALLS`、Citation、只读来源和 loopback Web，不复制 validation-only 入口。
- New chain：World Model Cognition Context → Investigation LLM → Source Broker → Retrieval Worker → append-only Ledger → 双分区 Package →
  Answer → Reviewer；审核给出具体 gap 后，新的 Verification Investigation 在新上下文中自适应补证，再形成后继 Package、重答、重审。
- Earliest Web micro-checkpoint：最小链一旦完成，立即用一条需要 World Model 认知与 query-time Source 共同支持的代表问题跑真实 Web；
  exact revision、只读、不可信来源、support/citation 分区、Citation 和独立 Review 在该检查点不可延后。
- Fast checkpoint：一个真实工程 4 条不同维度自然问题，加至少一条现场题；至少 3 supported、至少 2 个非实现维度。
- Deferred hardening：持久恢复、复杂冲突、跨轮去重、完整异常矩阵、第二工程、全面性能、完整回归、hidden 和三臂对照留到方向
  `CONTINUE` 后。Slice1 仍须保留实际发生的 Conflict/Gap/Failure/Partial/Unknown，不得静默消解。
- Stop：世界模型被手册化；调查一次性固定；模型直接 Source；任何特判；Ledger/Package/Review 身份错配；答案仍是代码走读；错误、安全
  或审核降级；用户 REDIRECT/REJECT。

## Direction preview checkpoint

在 4 题方向体验之前先执行 `V-WEB-000`：同一 product-owned 页面、一个真实工程、一条代表问题、完整最小后端链。它只回答“真实用户能否
尽早摸到正确方向”，不要求先完成持久恢复、复杂冲突处理、跨轮去重或完整异常矩阵。微检查点失败立即修正主链，不以扩大 fixture 数量
掩盖；通过也不代表方向或 Slice 验收。

方向体验必须使用同一个 product-owned loopback Web，只监听 `127.0.0.1`，普通用户无需认证，持续显示“方向体验 / 非验收 / 非生产”。
默认只展示问题、直接答案或 Limitation 和可打开 Citation；World Model Cognition、Ledger、Broker 操作、Package、调用数、Review Finding
和授权诊断折叠到开发者详情。

4 条代表问题从系统用途、整体架构、基本使用/启动、业务流程、故障定位、配置影响、变更影响、测试意图、实现机制和证据边界中选择不同
维度。这些只是验证覆盖，不是题型 enum 或路由。用户判断答案是否像工程问答、是否直接有用、代码细节是否按需、Citation 与未知是否
可信，并决定 `CONTINUE / REDIRECT / REJECT`。

## Current vs expected behavior

当前产品能在 World Model 上做有界调查并给出代码行为，但默认正文常机械展开方法、分支和调用顺序。初版 ITER-010 的一次性 upfront
retrieval 又会在模型充分调查前封包。

预期行为是：World Model 先提供 exact 系统认知；Investigation LLM 保留原问题全部约束，根据每一步 Ledger Result 自适应决定下一项
抽象读操作或结束；Broker/Worker 控制 actual read。调查结束后才密封 Package，Answer 在新上下文中只读包、先回答目标；Reviewer 在
独立新上下文中检查并可指出具体证据缺口，但不能自己读源码或执行工具。

## System contracts and invariants

### Phase 0：复核正式边界

开发前必须确认 `FINDING-010-002`、`SYS-ADR-016`、Engineering Question Answering Contract、Product Success、runtime/Agentic/Evidence/
World Model/Response/Source/Security/Browser 文档和治理门禁共同表达 `ENGINEERING_QA_ADAPTIVE_INVESTIGATION@1`。严格 `WORLD_MODEL`
Source-off 和显式 `DIRECT_INVESTIGATION` 继续保留，不得静默 fallback。任一 current Owner 或 Manifest digest 不一致即停止。

### Phase 1：最小真实协议

- Request 固定 immutable original question、exact repository/revision、World Model Context/Scope/Schema/Snapshot、source allowlist、Provider
  disclosure policy 和资源上限；问题或运行状态不能改变这些身份。
- World Model Cognition Context 提供实体、关系、行为、约束、状态、证据、coverage 和 unknown boundary。手册/地图只是投影；Snapshot
  为零或不足不能阻断授权 Source 调查。
- Investigation LLM 是独立角色，只能读取原问题、认知上下文和当前 append-only Ledger；每次只能提出注册的抽象 search/read/parse/
  finish 意图。下一步必须引用 prior Result/progress，不能一次性预写固定列表，也不能按题目/工程/关键词/符号路由。
- Source Broker 验证并编译提议的操作、版本、路径、allowlist、bytes、disclosure 和安全上限。Retrieval Worker 只执行 Broker 批准的
  exact-revision、read-only 操作。两者都不生成答案；模型没有直接 FS/Shell/network/credential/write/source authority。
- 每次认知查询、提议、Broker decision、操作、Result、locator、digest、bytes、truncation 和 progress 只追加到本题 Evidence Ledger。
  只有合法 `FINISH` 或失败关闭 stop 后才能 seal；不得覆盖历史或在调查完成前密封。
- Question Evidence Package 保持一个 seal/identity，但内部严格分区：`support/citation` 只收经 modality、Context、Coverage 和 Support
  校验通过的可采信条目，只有它们能支持肯定 Claim 与 Citation；`boundary/audit` 必须保留 Gap、Failure、Partial、Conflict、Unknown、
  拒绝决定和资源收据，只能约束结论或形成标记清楚的边界说明，不能支持肯定 Claim。seal 不把任何条目或模型推断变成真。
- Answer 在全新上下文中只读当前 sealed Package。每个实质结论绑定包内证据；代码只在问题要求或支持结论确有必要时展开。
- Reviewer 在另一个新上下文中读取原问题、理解记录、当前 Package 和 Draft，无 repo/Source/World Model tool、FS、Shell、network 或
  credential。表达缺陷可请求同包针对性重写；证据缺口只能输出绑定 Checklist/Claim/evidence class/need 的 versioned Verification
  Request，不能提出可执行 path/command/operation。
- 合法 Request 启动独立 `Verification Investigation LLM`。它使用全新上下文，只读具体 gap、当前 Package 与 Ledger prefix，根据每步新
  Result 自适应提出 search/read/parse/finish；每一步仍由 Application/Broker 校验编译、Worker 执行。它不回初始 Investigation LLM，
  不继承 Reviewer 会话，也无直接来源权限。完成后追加新 Ledger Revision、密封新 Package、完整生成新 Answer 并独立 Review；旧 Review
  不得批准新包。
- 为尽快验证方向，Slice1 每个问题最多冻结一次 Verification Investigation；这是 preview 的临时安全边界，不是永久协议。Slice2/3
  禁止固定一轮上限，改为在各自 exact freeze 前预密封 Package Revision、model call、Broker operation、source bytes、wall time 与
  no-progress 高安全熔断。answerable 因任一熔断耗尽而未回答必须计 `FAIL`，不能用 Limitation 取得 supported 分数。
- 调用、步骤、文件、bytes 和 wall time 是高安全上限。达到上限失败关闭；只有预先分类的真实 boundary 才能交付独立审核认可的准确
  Limitation，answerable 因上限耗尽未回答必须计 FAIL。不能删减调查、checklist、Evidence、Citation 或 Review。
- 交付后的高质量证据/结论可异步提议 Knowledge Update，不能阻塞或追认本题答案。

## Interfaces and affected code

本 Slice 授权允许修改 Application orchestration、Investigation/Verification Investigation role、Source Broker port/policy、Retrieval Worker adapter、Evidence Ledger/Package、
Response Control、Answer/Review Strategy、role-specific Gateway input、product-owned HTTP/Web 及对应 tests。优先复用现有 World Model Query、
Evidence Answering、Citation 和 Web 组件，不复制 ITER-009 pipeline。

源码路径不能直接传给模型后依赖 prompt 自律；模型只能提出 Broker 能验证的抽象意图。所有自然问题进入同一协议，UI 不按问题维度切换
后端。禁止工程、题目、关键词、符号、类、方法、fixture 或 Oracle 特判。

## Compatibility, data and security boundaries

严格 `WORLD_MODEL` no-payload/Source-off、Citation 和历史 accepted 测试继续成立；新协议使用独立 identity。源码、README、注释、配置、
测试均视为不可信输入；拒绝 symlink escape、submodule/remote 自动获取、binary、oversize、path traversal、写、执行和网络。

每个 original question、Cognition Context、Ledger Revision、Package、Draft、Review、补证请求和独立 Verification Investigation 保存稳定
ID/digest。Slice1 的 request-scoped Ledger 必须只追加且能形成完整 Result；跨进程持久恢复与复杂幂等 replay 明确后移到 Slice2。live
前另行冻结 exact
Provider/model/role、fragment allowlist、redaction、configuration、secret reference 和 audit；计划与开发授权都不允许自动外发。

## Open questions and implementation risks

- 调查模型可能循环或过早 FINISH；最小版保留基本 progress/no-progress 安全关闭与 Application FINISH 检查，完整循环/异常矩阵后移。
- World Model 和 Source 冲突时必须把两者作为 `boundary/audit` 条目保留，不能默认源码或较新时间自动获胜；复杂冲突裁决留到 Slice2。
- 独立补证可能重复初始调查；Slice1 只证明一轮全新上下文、结果驱动和后继 identity，复杂多轮、dedup/recovery 留到 Slice2。
- 公开 4 题不能证明跨工程泛化；它只判断方向，不能替代 Slice2/3。
- 更多模型调用可能增加成本；首版先证明正确职责和答案质量，随后测量，不因调用数目标删减工作。

## Acceptance scenarios

1. `V-BASELINE-001`：exact baseline/tree 与 ITER-009 rejected 结论一致。
2. `V-ARCH-001`：Finding、ADR/Contract、Manifest、docs gate 一致；严格 WORLD_MODEL/DIRECT 回归边界不变。
3. `V-COGNITION-001`：World Model 以 exact、持久、版本化外部认知供模型使用，不退化为手册/缓存/keyword hints。
4. `V-QINTENT-001`：原问题目标、受众、层级、结论、语言和约束不丢失；无特判路由。
5. `V-INVESTIGATE-001`：至少两步由 prior Result 驱动；partial/zero cognition 不阻断必要 Source；FINISH 有证据与 progress 支持。
6. `V-BROKER-001`：Broker 编译并审计抽象提议，Worker 仅执行 allowlisted read-only exact-revision 操作；模型直接权限为 0。
7. `V-LEDGER-001`：Ledger append-only，调查后 seal；Package 的 support/citation 仅 admissible，boundary/audit 必须保留且不能支持肯定 Claim，
   seal 不等于真值，revision 身份不可混用。
8. `V-ANSWER-001`：4 题至少 3 supported、至少 2 个非实现维度、重大错误 0、直接答案且逐结论 Citation。
9. `V-REVIEW-001`：Reviewer 只给具体 gap；独立 Verification Investigation 在新上下文中多步自适应补证，经 Broker/Worker 形成新
   Ledger/Package/Answer/Review；不回初始 Investigation 且无直接 Source。
10. `V-LIMIT-001`：证据或安全上限不足时准确 Limitation 或失败关闭，不伪造 absence/coverage；answerable 因上限耗尽计 FAIL。
11. `V-XD-001`、`V-WEB-000`：最小纵切一成立，同一真实 Web 立即完成一条 World Model + query-time Source 代表问题。
12. `V-WEB-001`、`V-PREVIEW-001`：微检查点之后在同一真实 Web 完成 4 题+现场题和用户方向决定。
13. `V-SEC-001`：Source injection、path/write/exec/network/secret/disclosure、budget、no retry、loopback 全部符合边界。
14. `V-REFLECT-001`：A1—A3 exact Verdict，A4/A5 early signal，全部 Finding 和用户新决定完整。

## Architecture reflection checkpoint

Slice Result 必须复核世界模型概念、调查自适应性、Broker/Worker 权限、Ledger/Package identity、补证独立性、4 题+现场题体验、安全、
成本/复杂度和全部 Finding。只有 A1—A3 全部 `SUPPORTED`、Case PASS 且用户后续决定 `CONTINUE`，才可申请 Slice2。

## Findings

`FINDING-010-001` 保留默认工程问答需要受控回源的根因；`FINDING-010-002` 修正世界模型定义表达和提问期职责。后续发现按
[Findings](../findings/README.md) 与[实现发现回写规则](../../../governance/implementation-feedback-policy.md)处置。
