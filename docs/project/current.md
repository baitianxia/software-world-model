---
id: PROJECT-CURRENT
kind: project-current
status: current
authority: current-development
owners: [project]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, PROJECT-GOVERNANCE-DEVELOPMENT-DESIGN, PROJECT-GOVERNANCE-PLAN-EXECUTION, ROADMAP-M-002, ITER-001-INDEX, ITER-002-INDEX, ITER-002-RESULT-ACCEPTANCE, ITER-003-INDEX, ITER-003-RESULT-ACCEPTANCE, ITER-004-INDEX, ITER-004-RESULT-ACCEPTANCE, ITER-005-INDEX, ITER-005-RESULT-ACCEPTANCE, ITER-006-INDEX, ITER-006-RESULT-ACCEPTANCE, ITER-007-INDEX, ITER-007-RESULT-SLICE-001-STOP-DECISION, ITER-008-INDEX, ITER-008-RESULT-SLICE-001-STOP-REDIRECT, ITER-009-INDEX, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, ITER-010-INDEX, ITER-010-SLICE-001, ITER-010-RESULT-V-WEB-000-LIVE-RUN-009, ITER-010-RESULT-V-WEB-001-PUBLIC-DIRECTION-QUESTIONS, ITER-010-RESULT-V-ALPHA-ACCESS-001, ITER-010-RESULT-V-LAYER-ATTRIBUTION-001, ITER-010-RESULT-V-COGNITION-ELIGIBILITY-001, ITER-010-RESULT-V-DEEPSEEK-IDLE-001, ITER-010-RESULT-V-PLAN-RECOVERY-001, ITER-010-RESULT-SLICE-001-STOP-REDIRECT, FINDING-010-027, FINDING-010-028, FINDING-010-091, FINDING-010-092, FINDING-010-093, FINDING-010-094, FINDING-010-095, FINDING-010-096, FINDING-010-097, FINDING-010-098, FINDING-010-099, FINDING-010-100, FINDING-010-101, FINDING-010-102, FINDING-010-103, FINDING-010-104, FINDING-010-105, FINDING-010-106, FINDING-010-107, FINDING-010-108, FINDING-010-109, FINDING-010-110, FINDING-010-111, FINDING-010-112, FINDING-010-113, FINDING-010-114, FINDING-010-115, FINDING-010-116, FINDING-010-117, FINDING-010-118, FINDING-010-119, FINDING-010-120, FINDING-010-121, FINDING-010-122, FINDING-010-123, FINDING-010-124, FINDING-010-125, FINDING-010-126, FINDING-010-127, FINDING-010-128, FINDING-010-129, FINDING-010-130, FINDING-010-131, FINDING-010-132, FINDING-010-133, FINDING-010-134, FINDING-010-135, FINDING-010-136, FINDING-010-137, FINDING-010-138, FINDING-010-139, FINDING-010-140, FINDING-010-141, FINDING-010-153, FINDING-010-154, FINDING-010-155, FINDING-010-156, FINDING-010-157, FINDING-010-158, FINDING-010-159, FINDING-010-160, FINDING-010-161, FINDING-010-162, ITER-010-PDR-001, ITER-010-PDR-002, ITER-010-PDR-003, ITER-010-PDR-004, ITER-010-PDR-005, ITER-010-PDR-006, ITER-010-PDR-007, ITER-010-PDR-008, ITER-010-PDR-009, ITER-010-PDR-010, SYS-ADR-017, SYS-ADR-018, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, ITER-011-INDEX]
code: []
tests: []
as_of: 2026-08-28
active_iteration: ITER-010-INDEX
active_slice: ITER-010-SLICE-001
worktree_status: iteration-010-slice-001-product-stop-condition-met-result-verifier-gap
strategy_relation: dual-core-world-model-cognition-and-conversational-lead-engineering-agent
live_model_path: product-repair-stopped-forward-governance-revision-required-before-failure-handoff
plan_revision_ref: ITER-010-PDR-010
next_action: ITER-010-ACTION-USER-PLAN-RECOVERY-001
next_action_case_id: V-MVP-EXPERIENCE-001
---

# 当前工作上下文

## PDR-010 当前唯一动作

ITER-010 已进入“完整体验版开发”。可以直接修改 Manifest 当前动作允许的产品、Agent、Evidence/Review、Provider 组合与 loopback Web；不需要
Activation、Freeze、分钟收据、阶段 Result 或新的 standing-scope 人工确认。

机器动作 ID `ITER-010-ACTION-USER-PLAN-RECOVERY-001` 仅为可信父提交连续性保留；其当前含义由 `ITER-010-PDR-010` 重定义为
`V-MVP-EXPERIENCE-001`，不是计划恢复动作。

| 当前顺序 | 完成定义 | 交付点 |
|---|---|---|
| 首次可操作浏览器交付（`V-CHAT-EXPERIENCE-001`） | 版本化软件世界模型认知、主工程 Agent、按 Gap 受控只读源码、逐 Turn Evidence/Citation、fresh 独立审核、语义多轮 Chat 与新 Conversation 隔离在同一真实链上成立 | 第一条主链可操作后立即把启动命令、URL、exact candidate、质量状态和限制交给用户；`requires_result=false`、不移动游标、不等待比较或全量回归 |
| 最终体验方向 handoff（`V-MVP-EXPERIENCE-001`） | 在同一候选上运行至少 3 条异质问题，至少 2 条未参与修复；再以 actual current Codex 独立作答作强基线 | 完成比较并如实报告逐题和总体结论；或证明一次通用修复后同类重大失败仍存在；此时才 `requires_result=true`，密封一次 Result 并移动到 `V-PREVIEW-002` |
| 用户判向 | 用户实际追问、纠正、深入或总结，并查看问题结果、Citation、审核和限制 | 用户决定 `CONTINUE / REWORK / REDIRECT / REJECT`；receipt 只记录方向且 action 自环。`CONTINUE` 后仍须新 PDR、明确用户授权与可信父 cutover 才能解锁 hardening、full regression、第二工程、hidden 与完整四路因果消融 |

## 执行纪律

- 普通失败、定向测试失败、内部候选变化以及首次浏览器即时交付都留在同一长动作中，不生成阶段 Result，也不暂停开发或移动游标。
- 答案失败先沿“世界模型构建/投影 → Agent 调查/综合 → Evidence/Review → Chat/Web”找最早偏差；只做一次最小通用修复，并复验原失败与两个异质案例。不得按题面、工程、关键词、符号、类或方法加特判。
- 首次体验前只运行改动相关测试、启动 smoke、安全与失败真实性检查；full regression 不得延迟第一次完整浏览器体验。
- 当前公开 mall exact revision 和既有披露/预算/路线属于 standing scope。每个真实 dispatch 仍由 runtime 自动派生 one-use exact receipt；只有来源、revision policy、账户、披露、预算或路线准入出现真实 scope delta 才申请新授权。
- `FINDING-010-154` 的 Artifact Session `@4` 已在 run-045 实际派生 standing→exact Session→Turn attempt→28 个 one-use call receipt；
  terminal 对账为 human approval request 0、retry 0、Production 0，`V-PUBLIC-OSS-AUTHORITY-001` 已有 live PASS 证据。Manifest 的 NOT-RUN
  字段是可信父冻结的 planning scalar，不允许候选用自述改写。
- run-045 主 Conversation 的 Turn 2/3 质量失败，不能作为首次可操作完整主链交付；`FINDING-010-155` 已将 first divergence 归因到
  Source 最后文件槽位，并用不增加预算的 model-catalog + Broker 双层通用修复处置。run-048 已证明 denied fallback admission 不阻塞
  preferred-only listener，但第一 Turn 的第三个 Ark call 在 HTTP 前发生一次 TLS failure。run-049 随后立即在相同 denied admission 下执行，
  7 次 Ark TLS/HTTP 全部成功、DeepSeek 0；第一 Turn 因单一 `WORLD_MODEL_QUERY` action 在初始/repair 输出中连续遗漏 `operation` 失败。
  run-050 又在 listener/network 前发现首个诊断候选错误改变了 Provider adapter identity；`FINDING-010-160` 已恢复 exact qualified adapter
  bytes，并把诊断移回 Agent/Application boundary。仍未形成完整主链；不封存 Result、不移动游标。
- 模型配置对产品流程透明；产品代码只能读取 `preferred/fallback` route role、execution-profile ref/digest 和独立可用性结论，禁止按具体
  Provider/model 身份形成动作、分支或质量标准。具体身份只存在于 execution profile 配置与运行收据。
- 备用路线只在 Provider availability boundary 密封 `PREFERRED_EXECUTION_PROFILE_UNAVAILABLE` 后可用。结构化输出无效和 Reviewer
  拒绝都证明首选路线已经返回结果，不得触发回退；需要修复时在同一 execution profile 上发起有界的新 call（新 request/receipt），不能冒充
  transport request retry，仍失败则如实关闭当前 Turn。
- `FINDING-010-156` 的通用 profile/availability-only route 和 `V-MODEL-TRANSPARENT-ROUTING-001` 已 PASS；`FINDING-010-157` 又移除了
  fallback admission 对 listener 的错误门禁。run-048 随后暴露真实 launcher 未组合 availability Owner；`FINDING-010-158` 已仅把 Gateway
  密封的 canonical pre-HTTP unavailable 提升为 exact verdict，HTTP/outcome、输出合同无效和审核拒绝仍不回退。
- `FINDING-010-159/160` 已把 trusted closed-schema path/missing-field diagnostic 绑定到一次 fresh same-profile format repair，明确 action
  必须完整含 `operation/arguments/evidence_need`，并把 owner 保留在 Agent/Application 以复用 exact unchanged Provider Conformance；Application
  不静默补字段。run-051 证明格式诊断可以修复 JSON 外叙述，且只有随后真实 Ark pre-HTTP TLS unavailable 才使 fallback eligible；DeepSeek
  admission 在自身 credential/TLS/HTTP 前拒绝。run-052 原问题初始/repair 连续缺 `operation`；run-053 的两个异质案例又分别连续提交非法
  Evidence support binding 和缺 `operation`，17 个 Ark TLS/HTTP 全成功、DeepSeek 0。`FINDING-010-161` 因而触发 PDR-010 的产品停止条件。
- `FINDING-010-162` 证明冻结 `ITER010_MVP_LIGHT@2` 无法表达当前答案前失败：它仍无条件要求三份已交付系统答案、Citation、Review、Codex
  比较和单一 Session，同时只接受 machine PASS。当前动作禁止修改 frozen runner/PDR，不能伪造 handoff 或让候选自授权。Manifest 游标保持
  `V-MVP-EXPERIENCE-001`；唯一下一步是用户明确授权最小 forward governance revision，先修订失败 handoff contract/runner 并形成新的 trusted
  parent，后续提交才能密封唯一 Result、进入 `V-PREVIEW-002`。
- 用户消息 digest 只是内容证据引用，不具备平台认证身份、签名或自行授权能力。

## 当前边界与权威入口

- 当前开发权威：[PDR-010](iterations/iteration-010/decisions/PDR-010-complete-mvp-vertical-slice.md)、[Manifest](iterations/iteration-010/manifest.yaml)、[Slice1](iterations/iteration-010/development-design/SLICE-001-engineering-qa-direction-preview.md) 和 [Verification Matrix](iterations/iteration-010/verification-matrix.md)。
- PDR-009 的 Freeze-first、多动作路径和分钟 timebox 已被 PDR-010 取代；历史决定和执行证据仍可从 [ITER-010 index](iterations/iteration-010/README.md)、[decisions](iterations/iteration-010/decisions/README.md)、[findings](iterations/iteration-010/findings/README.md) 与 [results](iterations/iteration-010/results/README.md) 查阅，不是当前开发指令。
- Product architecture 未改变：软件世界模型提供版本化、可验证的软件认知；主工程 Agent 以该认知为基础，必要时受控读取源码并形成可审答案。

当前状态：`AUTHORIZED / PRODUCT-REPAIR-STOPPED / RESULT-NOT-SEALED / FORWARD-GOVERNANCE-REVISION-REQUIRED / NON-PRODUCTION`。
