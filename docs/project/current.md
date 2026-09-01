---
id: PROJECT-CURRENT
kind: project-current
status: current
authority: current-development
owners: [project]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, PROJECT-GOVERNANCE-DEVELOPMENT-DESIGN, PROJECT-GOVERNANCE-PLAN-EXECUTION, ROADMAP-M-002, ITER-010-INDEX, ITER-010-SLICE-001, ITER-010-PDR-012, ITER-010-PDR-014, FINDING-010-256, FINDING-010-257, FINDING-010-260, FINDING-010-261, FINDING-010-262, FINDING-010-263, FINDING-010-264, FINDING-010-265, SYS-ADR-018]
code: []
tests: []
as_of: 2026-09-01
active_iteration: ITER-010-INDEX
active_slice: ITER-010-SLICE-001
worktree_status: iteration-010-slice-001-capability-separated-recovery
strategy_relation: dual-core-world-model-cognition-and-conversational-lead-engineering-agent
live_model_path: preferred-execution-profile-first-fallback-only-on-trusted-unavailability
plan_revision_ref: ITER-010-PDR-012
execution_decision_ref: ITER-010-PDR-014
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

Phase A 的 source-only Browser 诊断基线已用两个异质问题和一个追问通过；Phase B 的 exact-source 认知纵切已在同一 artifact 上用五个独立
任务 5/5 通过。Phase C 首个真实 Browser run 已完成三个异质问题和一个追问，但事务追问漏掉接口 `@Transactional` 并被 Reviewer 错误
批准，因此状态保持 REWORK。通用 ranking 已让 frozen source-native 查询同时返回实现和接口；真实 run-005 进一步证明 Agent 把中文转述
误当 lexical cognition query，随后仍只读实现。Application Control 已拒绝该错误答案；current 修复只澄清 source-native 查询和声明检查的
通用工具契约，真实 successor 与 same-Agent 消融仍未完成。

PDR-012 继续拥有可信 standing authority 和 Manifest 兼容 action；PDR-014 只在其范围内替换执行路线。Manifest 中的
`ITER-010-ACTION-USER-DIRECTION-DECISION-001 / V-BROWSER-CHAT-MVP-BUILD-001` 因此仍保留身份，但不再代表旧协议循环。

## 唯一下一动作

严格按 PDR-014 继续执行尚未完成的 C→D：

- C：复跑已修正 cognition ranking 与 source-native query 使用的浏览器 Alpha，并冻结 same-Agent source-only / World Model + source 消融；
- D：用五个异质问题、多轮 Chat、same-Agent 消融和 current Codex 完成质量判断。

时间上限只触发自动简化或换实现，不触发暂停、失败 Result、重复授权或质量降低。第一个可操作候选立即交付；full regression、hidden、
跨工程、性能和工程化只在用户确认方向后开始。

## 开发纪律

- 旧 `conversational_engineering_model.py` 及其测试在 MVP 前只可缩减或薄适配，净行数不得增长；不得新增协议版本或正文词法语义校验。
- Prompt/Schema 变化必须先有分层 trajectory 和替换实验，证明最早偏差确在模型交互层；否则不进入候选。
- 知识、Agent、集成和最终答案分别出证据。只增加 Docs/Test/Prompt/Schema 时状态为 `NO_PRODUCT_PROGRESS`，开发自动回到最早缺失能力。
- 每次通用修复同时复验原失败和两个异质未参与问题；只改善原题时必须换责任层或实现策略。
- 普通答案、测试、Provider 或网络失败不停止开发。首选执行配置成功时不运行备用；只有可信不可用结论才透明回退。

## 授权与边界

现有公开 mall exact revision、只读 Source、既有执行配置、披露、预算和 loopback evaluation 继续位于 standing authority 内。同范围的新
Conversation、Turn、问题、候选、定向测试和外调不重复申请授权；每次外调仍自动生成 exact runtime record。只有私有/新 Source、新接收方
或账户、扩大披露/预算、外部写入、非 loopback、Production 或破坏性操作才属于 scope delta。

当前状态：`AUTHORIZED / REWORK / PDR-014 CAPABILITY-SEPARATED RECOVERY / NON-PRODUCTION`。
