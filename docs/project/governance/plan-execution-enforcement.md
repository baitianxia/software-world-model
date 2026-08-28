---
id: PROJECT-GOVERNANCE-PLAN-EXECUTION
kind: project-governance
status: current
authority: project-governance
owners: [project, engineering, quality]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, PROJECT-GOVERNANCE-DEVELOPMENT-DESIGN, PROJECT-GOVERNANCE-VERIFICATION]
code: [.githooks/plan-pre-commit, scripts/docs.py, scripts/plan_gate.py]
tests: [tests/test_docs_gate.py, tests/test_plan_gate.py]
---

# 开发计划执行规则

## 目的

计划执行的首要目标是持续完成用户可验证的产品结果，并尽早发现方向偏差。机械检查只保护真实权限、安全和完成真实性，不能把计划、收据
或验证器变成主要交付物，也不能让普通开发失败自动停止整个开发回合。

## 持续授权与工作计划必须分离

仓库必须区分两个对象：

- **持续授权边界（standing authority）：** 唯一的权限来源，规定允许的代码范围、Source、只读/写入、外部接收方、配置路线、披露、
  预算、loopback/Production 和撤销条件。
- **工作计划（work plan）：** 当前产品目标、任务顺序、最早可验证纵切、已知阻塞和下一开发任务。实现者可依据新证据在既有授权内直接
  调整；它不能创建、扩大、撤销、消费或暂停授权。

Manifest 的 current action 是工作计划与审计定位的兼容镜像，不是新的人工授权来源。coding_allowed、external_execution_allowed、
路径和 lock 字段必须镜像持续授权与真实安全边界，不能因答案错误、测试失败、格式失败、检查点未达成、Result 缺失或计划文字更新而把仍
有效的开发授权改成 false。

只有真实 scope delta 才申请最小增量权限：私有或来源不明数据、新的外部接收方或账户、扩大披露/预算、外部写入、非 loopback、
Production 或破坏性动作。同一公开开源 exact revision、既有路线、预算和只读范围内的新问题、Conversation、Turn、候选、定向测试与本地
启动不重复申请。

## 一个持续的产品开发闭环

活动 Slice 默认只有一个持续产品开发闭环：

    理解目标 → 形成最小纵切 → 定向验证 → 立即交付真实 Web
        ↑             ↓
        └─ 分层归因 ← 普通失败/用户反馈

普通失败留在同一 Slice：保存原输入、输出和证据，定位
Source → 世界模型构建/查询 → Agent → Evidence/Answer → Review → Web
的最早偏差，做通用修复并用不同类型、未参与修复的问题复验。不得为单题、提交、测试、模型调用或失败单独创建动作、PDR、Result、授权
请求或停止点；不得用题面、关键词、工程名、符号或 fixture 特判碰答案。

第一个贯通世界模型认知、主工程 Agent、按 Gap 只读源码、Evidence/Citation、fresh Review 和语义多轮 Chat 的浏览器版本一旦可操作，
必须立即交给用户。首次交付 requires_result=false，不移动计划游标，也不等待全量回归、跨工程、hidden、完整比较基础设施或工程夯实。
用户可以随时 REWORK / REDIRECT / STOP / REJECT；听取这类反馈不要求产品先取得技术 PASS。

方向确认前只运行改动相关的 targeted、startup、安全和失败真实性验证。实际体验后再用异质问题和 current Codex 强基线判断方向；Codex
不是事实来源、Oracle 或裁判。方向成立后才执行全面夯实和完整回归。

## 最小机械边界

机械检查只应拒绝当前具体 diff、外部操作或完成声明中的以下错误：

1. 候选超出可信持续授权的路径、Source、披露、预算、写入、网络、loopback/Production 或破坏性边界；
2. 候选计划试图为自己的同一 diff 创建或扩大权限；
3. 外部副作用缺少既有 standing authority 或必要的自动运行记录，Secret 被写入仓库、Prompt、日志或 Result；
4. 未发生的产品体验、测试、答案、Citation、Review、比较或完成状态被宣称为已发生。

检查失败只阻止该 diff、操作或完成声明；修正后继续原开发闭环。它不得撤销未越界的开发权限、生成失败 Result、移动全局游标，或要求用户
重新批准同一范围。Git commit/tree 已提供版本绑定；运行记录用于审计真实外调，不应复制为整套计划状态机。

## Result 与计划修订

Result 用于最终完成/方向交接或确实需要迁移项目状态时密封已发生事实，不是过程日志。第一次 Web 交付、普通失败、定向测试、内部候选和
同范围 REWORK 都不需要 Result。若已有历史 Result 记录失败，它保留为证据，但不撤销仍有效的 standing authority。

既有范围内，实施者可以直接修订工作计划并继续开发，无需再次取得用户授权。只有 scope delta、用户明确改变产品方向、Production/外部
边界改变或不可绕过的安全禁止才需要新的决定。计划工具表达不了真实状态时，先以当前产品目标继续所有不受影响的工作；不得建设
Activation 时钟、逐失败动作、whole-Manifest digest、冻结验证器恢复状态机或“修复门禁的门禁”。

## 验证

- python3 scripts/docs.py check：检查当前文档引用和一致性；
- python3 scripts/plan_gate.py snapshot 与 diff --base：检查可信范围、候选自扩权和虚假完成；
- 首次体验前仅运行与当前纵切相关的测试；完整回归在方向确认后的夯实阶段和最终验收前运行。

本地 hook 和远端工作流是误操作防护，不证明管理员不可绕过。不得用门禁通过数、文档数、测试数或收据数代替产品可体验性和答案质量。
