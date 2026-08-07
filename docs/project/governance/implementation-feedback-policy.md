---
id: PROJECT-GOVERNANCE-IMPLEMENTATION-FEEDBACK
kind: project-governance
status: current
authority: project-governance
owners: [engineering, architecture]
depends_on: [PROJECT-GOVERNANCE-DEVELOPMENT-DESIGN, PROJECT-GOVERNANCE-BOUNDARY]
code: []
tests: []
---

# 实现发现与文档回写

代码和测试不仅验证设计，也会发现新的事实。每条可能影响 System、当前 Slice、验收或后续方向的事实，都在活动 Iteration 的 `findings/FINDING-*.md` 登记；纯编辑备注不进入 Finding。

若发现发生时没有活动 Iteration，不得追写进已完成的历史 Iteration，也不得借 Finding 绕过开发授权。先保留可重复证据并停止受影响变化，待用户明确授权最小 Iteration 后再登记、分类和继续；纯粹修正本文档体系自身且已被用户直接授权的变更，可以在该授权范围内闭合。

## Finding 最小字段

- Observation：发现了什么，不先写结论；
- Evidence：代码、测试、日志或可重复步骤；
- Affected slice/system IDs；
- Classification 与影响范围；
- Decision/Disposition、目标文档和责任人；
- Status：`open`、`dispositioned`、`rejected` 或 `superseded`。

## 分类与去向

| 分类 | 判断 | 必须去向 |
|---|---|---|
| local-implementation | 不改变调用方和系统语义 | 代码/测试；Finding 说明为什么无需文档 |
| iteration-design | 改变本轮路径但不改变 System | 修订 Development Slice，必要时新增 PDR |
| system-contract | 改变 Owner、接口语义、不变量、安全或一致性 | 暂停 Slice；更新 System Contract/Architecture，必要时 ADR |
| verification | 暴露新的长期质量下限或本轮 Case | System Quality 或本轮 Verification Matrix |
| roadmap | 有价值但不在本轮授权范围 | planning-only Candidate，写明进入条件 |
| invalid | 证据不足、重复或假设错误 | rejected，并保留理由 |

`disposition` 和 `target` 都是单一主处置，不是列表。`target` 使用可解析的精确目标：`local-implementation` 指向 Finding front matter 的 `code` / `tests` 中已有的仓库路径；`iteration-design` 指向同轮 Slice 或 PDR ID；`system-contract` 指向 `docs/system/` 中的规范文档 ID；`verification` 指向 System Quality ID 或同轮 Verification Matrix ID；`roadmap` 指向 Roadmap Candidate ID。`invalid` 被拒绝时写 `target: none`。`superseded` 必须用 `superseded_by` 指向同一 Iteration 中另一条真实存在的 Finding，不能自指。

## 回写规则

1. System 影响必须与代码修改在同一可审查变更中闭合；不能只在 Result 记录“实际行为”。
2. Roadmap 不接收普通编码细节；只有独立 Outcome、价值和进入条件的后续工作才能成为 Candidate。
3. Result 记录发生了什么和证据，不拥有新规范。
4. 一个 Finding 可以引用多个证据，但最终只能有一个主要 disposition；连锁变化通过链接表达。
5. Iteration Acceptance 前不得有 `open` Finding。自动文档检查会阻止把仍有未处置发现的迭代标记为 accepted/completed。

## 反馈闭环

```text
Development Slice → code/test evidence → Finding
Finding → classify → PDR/System/Roadmap/code
destination updated → verification rerun → Finding dispositioned
```
