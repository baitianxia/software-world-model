---
id: PROJECT-CURRENT
kind: project-current
status: current
authority: current-development
owners: [project]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, PROJECT-GOVERNANCE-DEVELOPMENT-DESIGN, PROJECT-GOVERNANCE-PLAN-EXECUTION, ROADMAP-M-002, ITER-010-INDEX, ITER-010-SLICE-001, ITER-010-PDR-012, ITER-010-PDR-014, FINDING-010-256, FINDING-010-257, FINDING-010-260, FINDING-010-261, FINDING-010-262, FINDING-010-263, FINDING-010-264, FINDING-010-265, FINDING-010-266, FINDING-010-269, FINDING-010-270, FINDING-010-273, FINDING-010-274, FINDING-010-275, FINDING-010-276, FINDING-010-277, FINDING-010-278, FINDING-010-279, FINDING-010-280, FINDING-010-281, FINDING-010-282, FINDING-010-283, SYS-ADR-018]
code: []
tests: []
as_of: 2026-09-15
active_iteration: ITER-010-INDEX
active_slice: ITER-010-SLICE-001
worktree_status: single-development-and-independent-supervision-lanes
strategy_relation: dual-core-world-model-cognition-and-conversational-lead-engineering-agent
live_model_path: preferred-execution-profile-first-fallback-only-on-trusted-unavailability
plan_revision_ref: ITER-010-PDR-012
execution_decision_ref: ITER-010-PDR-014
execution_plan_ref: ITER-010-EXECUTION-PLAN-CURRENT
next_action: ITER-010-ACTION-USER-DIRECTION-DECISION-001
next_action_case_id: V-BROWSER-CHAT-MVP-BUILD-001
---

# 当前工作上下文

## 当前结论

ITER-010 的产品目标和总体架构不变，但 PDR-013 的执行计划已经被 PDR-014 完全替换。Git 投入审计证明过去 186 个提交主要增长了回答、审核
和输出协议，知识引擎没有提交；因此不得继续把旧模型边界、正文证明协议或逐题修复当作产品主线。

当前唯一开发主线是分别建立并验证：

1. 一个小型、Provider 透明、能观察后重规划的主工程 Agent；
2. 一份在提问前构建、可跨问题复用、包含结构/关系/行为/边界的真正软件世界模型认知；
3. Agent 通过通用搜索、遍历、详情工具使用世界模型，并按 Gap 受控读取源码；
4. 同一浏览器 Chat 中的自然答案、真实 Citation、fresh 独立技术审核和多轮上下文；
5. same-Agent source-only、same-Agent World Model + source 与 actual current Codex 的独立比较。

Phase A 的 source-only Browser 诊断基线保留为已完成的诊断证据。Phase B 的首版认知证据曾因声明/继承闭包不足进入 `REWORK`；该缺口已由
`FINDING-010-270` 的 clean product commit `b3c19ff31fcc8e498bcbaf9c36f2434e86570e75` 修复。独立监督在
`codex/supervision@7615bffccaf3df3b299304a52b1218f8b4680585` 对同一 exact Source 重建 artifact，并以 report
`sha256:8d7e4a1a5c205d28ae54a43f5c88e2f361ea82d55dabb4edf80a02e4e71b7b66` 给出 `ADVANCE → C`。Phase C 现已激活，
Phase D 继续锁定。Reviewer 只按 Phase C 的 fresh review 最小职责接入；Provider recovery 和其他归档内容仍须在对应阶段重新取证后才能
选择性引入，不能直接恢复到产品线。

PDR-012 继续拥有可信 standing authority 和 Manifest 兼容 action；PDR-014 只在其范围内替换执行路线。Manifest 中的
`ITER-010-ACTION-USER-DIRECTION-DECISION-001 / V-BROWSER-CHAT-MVP-BUILD-001` 因此仍保留身份，但不再代表旧协议循环。

本轮讨论进一步明确运行分工：软件世界模型是指定版本工程的结构、关系、行为、边界、覆盖范围、来源和检索入口组成的系统认知，不是文字手册或
答案库；Agent 负责理解问题、自适应选择认知和源码证据、组织答案及处理追问；模型负责推理与表达；源码是最终事实依据。World Model + source
优于 source-only 是必须用同一 Agent 的成对实验验证的产品假设，不能预先宣称成立。认知覆盖不足时必须降级到通用源码检索，不能用错误导航候选
或固定动作替代事实。

## 唯一开发入口与下一动作

当前执行顺序唯一见 `ITER-010-EXECUTION-PLAN-CURRENT`。该执行卡把 C0 恢复绑定、C1 Agent 证据规划、C2 多轮浏览器、C3 Alpha 交付和 C4
方向通过后的夯实分开；旧 Proposal/Readiness 中的 Phase B REWORK 文字只保留历史记录，不得作为开发任务输入。

- 唯一开发分支：`codex/development`；唯一监督分支：`codex/supervision`；`main` 只接收已验收成果。
- 其他本地开发分支全部转换为 `archive/branches/*` 标签后删除。旧临时工作树和 dirty candidate 只作恢复来源，不再作为开发或监督目标。
- Phase B 已由监督方在 clean exact commit 上独立 `ADVANCE`；该结论不由开发分支修改或重新解释。
- 当前唯一产品任务是 Phase C：先完成当前候选的根因对账（N0），再按最早责任层闭合 Agent/世界模型证据规划（N1），重新打通多轮浏览器（N2），
 形成完整链后立即交付 Alpha（N3）。当前 clean HEAD 为 `51640be9c9a7d0ddc2126b889623d2ed1ab1c430`（tree `baac70a5e3c76b8bed6b604592b3c315a0f8be01`）；run-276 已补齐 C1 turn-level evidence，但监督仍未给出新的 `ADVANCE`。run-278/279 的 C2 真实浏览器尝试仍有失败，不能继承旧候选
  的 C2 结论。
- `run-156` 的 q5 已证明固定 8-action fuse 与耗尽后 fail-closed 正常；当前最早偏差是 Application cognition→Source candidate construction
  的同路径重复幂等和同一预算内已有 cognition/Source candidate 的 Primary evidence planning/selection。`FINDING-010-277` 只复用既有
  path capability、内部 sidecar 和通用呈现收敛，不恢复工具、不扩大预算、不重试 Reviewer、不新增 Agent 协议；历史 raw citation receipt
  缺失时只记录机器可读 `NOT_RUN`。
- `run-158` 的 q5 暴露多个 Source Observation 的 Citation ordinal 是局部域；`FINDING-010-278` 的 Application 修复按不可变
  Observation prefix 允许一次同一主 Agent 机械 replan，新增 Observation 才形成新的同范围机会，严格保留 rejected receipt/answer/findings，
  不自动映射、重编号或合成 Citation。fresh successor 仍需证明 q5 补证后进入 Reviewer。
- FINDING-010-279 记录同一主 Agent 的重复动作与无进展恢复：Application 以既有 action fuse 阻止重复 Tool dispatch，向同一 Agent 反馈换用
  不同合法动作，并在 Reviewer MORE_EVIDENCE 后稳定呈现已有未读 Source candidate。该修复保持现有协议、预算和 Source/Citation identity
  不变；fresh successor 仍需验证补证后进入 Reviewer。
- Phase D、完整质量 Gate、Provider recovery 和归档协议扩张仍禁止；Phase C 若失败，按最早 knowledge/integration/Agent/review/Web 层做通用
  修复，不回写题面规则。

Phase C 只启用集成纵切所需的 fresh Reviewer，不继续 Provider recovery、回答 Prompt/Schema 或 Phase D 验收器。普通测试、模型、答案或
网络失败仍不暂停开发、不重复申请授权。

监督每 30 分钟以及每次 HEAD/工作树/运行证据变化时检查一次。监督必须同时写入可观察 heartbeat 和独立 assessment；目标分支、工作树或
baseline 不匹配时只修复监督绑定，不能把开发误判为完成、暂停或重新授权。

时间上限只触发自动简化或换实现，不触发暂停、失败 Result、重复授权或质量降低。第一个可操作候选立即交付；full regression、hidden、
跨工程、性能和工程化只在用户确认方向后开始。

## 开发纪律

- 旧 `conversational_engineering_model.py` 及其测试在 MVP 前只可缩减或薄适配，净行数不得增长；不得新增协议版本或正文词法语义校验。
- Prompt/Schema 变化必须先有分层 trajectory 和替换实验，证明最早偏差确在模型交互层；否则不进入候选。
- 知识、Agent、集成和最终答案分别出证据。只增加 Docs/Test/Prompt/Schema 时状态为 `NO_PRODUCT_PROGRESS`，开发自动回到最早缺失能力。
- 每次通用修复同时复验原失败和两个异质未参与问题；只改善原题时必须换责任层或实现策略。
- 普通答案、测试、Provider 或网络失败不停止开发。首选执行配置成功时不运行备用；只有可信不可用结论才透明回退。
- 受信证据确认 HTTP/model dispatch 为 0 的临时 Provider 失败必须按 5/15/30 分钟 fresh logical-run cadence 自动重试；不等待用户、不重复
  授权、不重放同一请求。post-dispatch outcome unknown 继续禁止 replay。

## 授权与边界

现有公开 mall exact revision、只读 Source、既有执行配置、披露、预算和 loopback evaluation 继续位于 standing authority 内。同范围的新
Conversation、Turn、问题、候选、定向测试和外调不重复申请授权；每次外调仍自动生成 exact runtime record。只有私有/新 Source、新接收方
或账户、扩大披露/预算、外部写入、非 loopback、Production 或破坏性操作才属于 scope delta。

当前状态：`AUTHORIZED / PHASE C ACTIVE / ROOT-CAUSE RECONCILIATION REQUIRED / NON-PRODUCTION`。
