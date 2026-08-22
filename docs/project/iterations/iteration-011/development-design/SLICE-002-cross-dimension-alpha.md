---
id: ITER-011-SLICE-002
kind: development-slice
status: proposed
authority: proposed-development
owners: [engineering, product, architecture, quality]
depends_on: [ITER-011-PROPOSAL, ITER-011-READINESS, ITER-006-RESULT-ACCEPTANCE, ITER-011-SLICE-001]
code: [src/software_world_model/application_services, src/software_world_model/ai_infrastructure, src/software_world_model/interface]
tests: [tests]
iteration: ITER-011
coding_input: false
product_goal_gate: V-000
product_goal_accepted_capability_refs: [ITER-006-RESULT-ACCEPTANCE]
product_goal_cross_domain_case_ids: [V-XD-002]
product_goal_web_checkpoint_id: V-WEB-002
product_goal_direction_preview_checkpoint_id: V-PREVIEW-002
product_goal_live_ad_hoc_checkpoint_id: V-ADHOC-002
product_goal_reflection_gate_case_id: V-REFLECT-002
product_goal_slice_gate_case_ids: [V-ALPHA-002, V-SEC-002, V-XD-002, V-WEB-002, V-ADHOC-002, V-PREVIEW-002, V-REFLECT-002]
---

# SLICE-002：跨维度可用 Alpha 判向

## Status and dependencies

`PROPOSED / NOT AUTHORIZED / NOT CODING INPUT`。必须先有 Slice1 exact Result、`V-REFLECT-001 PASS`、用户 decision=`CONTINUE`，再以该
同一决定收据取得 Slice2 新授权并补入 `depends_on`/Manifest。Slice1 的开发或 live 授权不能复用。

## Product-goal contribution and cumulative integration

- Product gap shortened：确认方向探针不是单题偶然成功，用一轮系统性最小迭代覆盖同一真实工程的多个问题维度。
- User-visible delta：从同一产品 Web 立即展示 3—5 条预冻结跨维度问题和至少 1 条用户现场题。
- Cross-dimension minimum：在同一真实工程至少覆盖用途/架构/运行/业务流程/配置/故障/影响/实现中的三个维度，至少两题不是实现走读题。
- Stop signal：只对 Slice1 题有效、出现题型/工程路由、正文重新被实现清单主导、重大遗漏被批准、Citation/安全失败。
- Critical assumptions：累积到 A1/A2；A3/A4 只记录 early signal。
- Reflection：`V-REFLECT-002`；**没有用户新 `CONTINUE`，Slice3 不得启动。**

## Direction preview checkpoint

本 Slice 允许基于 Slice1 证据做一轮最小且系统性的通用修正，然后立刻 freeze 和展示 Alpha；不允许在展示前把 persistence、复杂多轮补证、
conflict/dedup、完整 security/performance、full regression、hidden canary 或三臂 comparison 塞入范围。

Alpha 是“可用方向确认”，不是正式验收。准备题 3—5 条全部从同一 product-owned Web 运行，随后用户至少现场提出 1 题；页面保留
非验收/非生产标识和已知限制。独立评测方先裁决技术质量；用户再基于已复核的原始答案、限制和失败，独立作出
`CONTINUE / REDIRECT / REJECT`。

## Current vs expected behavior

进入本段时 Slice1 只证明两个实际问题的方向。预期是在不扩建完整工程基础设施的前提下，使同一 hierarchy contract 与各自独立重建的
checklist 对不同抽象层级、
受众、来源组合和工程结构仍能形成直接答案、必要解释、限制和 Citation；发现共性缺口时只做可解释的协议/表示修正，不做题目补丁。

## System contracts and invariants

- Slice1 的 hierarchy/Application acceptance/Reviewer contract 不静默改义；若真实证据要求边界变化，先写 Finding 并同步 owning docs。
- 同一问题/工程/关键词/符号/类/方法/fixture/Oracle 特判为硬停止条件。
- exact revision、Broker/Worker 只读、Source untrusted、Package/Citation、role/Secret 隔离、独立 Review、no retry 和 loopback 均从 Slice1 保持。
- Alpha 的同工程问题是可见方向输入，不得冒充 Slice3 第二工程 hidden canary 或最终 held-out 泛化证据。

## Interfaces and affected code

只允许修正 Slice1 暴露的系统性 hierarchy、Application acceptance、Reviewer checklist、Answer composition 和同一 Web 呈现，并补 focused
cross-dimension tests。禁止 persistence store、复杂恢复框架、专用项目 adapter、hidden harness、三臂 runner 和全面性能优化。

## Compatibility, data and security boundaries

每题/工程必须冻结 exact revision、Source Profile、World Model identity、Provider role/input disclosure 和运行授权。旧题失败不重试，旧
grant 不复用。最小安全 Gate 只允许证明 Alpha 可安全体验，不替代 Slice3 完整矩阵。

## Open questions and implementation risks

- 3—5 题仍是小样本；本 Slice 只裁决产品方向和最小通用性，不宣称泛化完成。
- Slice3 的第二工程与问题集必须在 Alpha 完成后独立冻结并由用户持有，严格执行 burn rule，不能预先暴露给 Slice2 实现。
- 若 Alpha 需要大规模重构才能可见，应先交付当前最小差异并判向，不把夯实工作隐藏在本段。

## Acceptance scenarios

1. `V-ALPHA-002`：同一真实工程的 3—5 条问题覆盖至少三个维度并达到预冻结的直接性、层级、完整性和重大错误门；至少两条非实现维度。
2. `V-SEC-002`：Alpha exact revision、Source/role/Secret/disclosure、loopback、no-retry 和失败真实性成立。
3. `V-XD-002`：至少一题在同一答案中组合 accepted World Model 能力与 query-time 多来源 Evidence。
4. `V-WEB-002`：全部准备题从同一产品 Web 交付答案/Limitation 与可打开 Citation，console clean，无平行演示入口。
5. `V-ADHOC-002`：freeze 后用户至少现场提 1 题并获得同质量链结果。
6. `V-PREVIEW-002`：用户查看 Alpha 后给出独立 `CONTINUE / REDIRECT / REJECT`。
7. `V-REFLECT-002`：A1/A2 exact Verdict、A3/A4 early signal、全部 Finding 与用户决定完整。

## Architecture reflection checkpoint

Result 必须区分 Probe 偶然性、通用表示缺口、模型波动、Source/World Model 缺口和 Web 表达问题。`V-REFLECT-002 PASS` 只说明复盘完整；
只有 user-owned exact decision=`CONTINUE` 才可申请 Slice3。没有该收据时，任何 persistence、hidden、comparison 或 hardening 编码都越权。

## Findings

写入本轮 [Findings](../findings/README.md)，并按[实现发现回写规则](../../../governance/implementation-feedback-policy.md)处置。
