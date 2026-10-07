---
id: ITER-010-PDR-012
kind: project-decision
status: accepted
authority: project-decision
owners: [product, project, architecture, engineering, quality, ai]
depends_on: [ITER-010-PDR-011, ITER-010-RESULT-V-USER-DIRECTION-DECISION-001, FINDING-010-161, FINDING-010-163, FINDING-010-165, PROJECT-GOVERNANCE-PLAN-EXECUTION]
code: []
tests: []
iteration: ITER-010
decision: REWORK
rework_strategy: PRODUCT_FIRST_CONTINUOUS_BROWSER_CHAT_BUILD
decision_ref: local-user-message-utf8:sha256:2755c56a091dc1928d5952dc64a238e04922891451c6471787ecd4d9bbe68e62
effective_scope: ITER-010-SLICE-001
coding_input: true
---

# PDR-012：恢复以产品目标为中心的持续浏览器 Chat 开发

## 问题

PDR-010 已经规定先形成完整体验再验证方向，但 PDR-011 的失败 handoff 把工作计划误作授权来源：一次答案前失败后，产品、Web 和范围内
模型调用全部停止；随后又要求 Result、PDR、fresh 授权和可信切换。实际新增主要是治理工件，用户仍没有可验证产品。这不是质量保护，而
是计划自锁。

历史 run-052/053、failure Result 和 PDR-011 保留为真实证据；它们不能证明现有产品可用，也不能撤销仍有效的公开工程 standing
authority。用户已明确要求停止把主要精力投入阻塞开发的门禁，并把重点放回完成产品目标且不偏离目标。

## 决定

1. 不新建 Iteration 或 Slice。恢复 ITER-010 / SLICE-001 的一个持续产品开发动作。为兼容可信父切换，current_action 的技术 ID 暂保留旧值；其 kind、Case、路径、权限和本 PDR 明确定义为产品 BUILD，不再代表等待用户判向。Manifest 中非 current 的 governance compatibility contract 也只用于可信父格式兼容，不是当前任务、停止点或再次授权要求。范围内编码、本地启动、定向测试和已授权执行配置直接
   继续，不再逐问题、运行、失败或计划调整申请授权。
2. 当前唯一纵切是一个可往返的用户闭环：真实世界模型认知和精确版本只读源码作为 Agent 可选择的两类证据路径；Agent 根据问题和当前
   证据状态调查、综合并生成带 Evidence/Citation 的自然答案，fresh Review 可把缺口反馈给同一个 Agent，最后由无认证语义多轮 Web Chat
   承载本轮结果。组件单独完成、POM/Maven-only 回答、静态回放或一次性脚本都不是进度出口。这里不规定世界模型与源码的固定先后。
3. 第一条非 POM/Maven 的真实三轮 Conversation 可操作即在固定 loopback 页面作为“开发体验候选”交给用户，requires_result=false；它只证明
   产品链可操作，不得称为 MVP、质量 PASS、方向 PASS 或完成，也不等待全量回归、hidden、跨工程、完整比较基础设施或工程夯实。
4. 普通答案、格式、测试和 Reviewer 失败留在同一开发动作。必须先定位最早偏差层，提出可证伪根因，做通用修复并用不同类型、未参与修复
   的问题复验；不得针对题面、关键词、工程名、符号、类、方法或 fixture 碰答案。
5. 开发体验候选交付后不得暂停或等待新的用户决定，必须立即在同一候选上使用异质问题与 actual current Codex 强基线完成 MVP 质量资格
   判断。Codex 不是事实来源、Oracle 或裁判；独立 exact-source 证据与技术复核判断双方正确性、完整性、引用与未知边界。只有系统自身重大
   错误为零、逐题无物质退步、总体严格更优，且至少一项重要价值来自非 locator 世界模型认知时，才能称为 MVP 并交给用户判向；否则继续
   REWORK。候选代码变化后，旧体验和比较证据不得为新候选授予 MVP 资格。
6. 工作计划与 standing authority 分离。计划可在既有范围内依据证据直接调整，不能创建、扩大、撤销、消费或暂停权限。只有真实 scope
   delta、用户明确停止/改向或不可绕过的安全禁止才停止相关工作。
7. 本 PDR 的切换只允许删除旧校验器中“未知后续 PDR 一律失败”和“只有旧停工状态合法”的两个自锁条件；切换完成后到首次体验交付前，
   不再修改治理脚本、验证器或建设新门禁，只运行当前纵切相关的 targeted、startup、安全和失败真实性测试。

## 唯一下一动作

从现有 trace 和代码建立最小分层证据，确认最早产品偏差后直接修复该通用 Owner，并打通一条三轮浏览器 Conversation。世界模型必须提供
行为/职责/失败边界中的可观察认知贡献；Agent 只在认知 Gap 上读源码；页面必须得到 Answer、可打开 Citation 和本轮 fresh Review。

首条完整链完成后立即把启动命令、固定 URL、exact product/source revision、已知限制和可操作页面作为开发体验候选交给用户，不生成阶段
Result，也不停止后续同范围开发。随后直接完成同一候选的绝对质量检查和 current Codex 同题比较；质量资格通过才完成本动作的 MVP 目标。

## 不变边界

Source exact revision 且只读；Secret 不进入仓库、Prompt、日志或结果；外部执行不越过既有 route/disclosure/budget；只允许 loopback
evaluation；Production、外部写入、私有/未知 Source 和破坏性操作仍禁止。模型身份只属于运行配置和日志，产品计划只使用首选/备用角色；
输出格式或审核失败不是首选路线不可用，不能借此切备用碰答案。
