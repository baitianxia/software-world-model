---
id: ITER-011-INDEX
kind: iteration-index
status: proposed
authority: project
owners: [product, project, architecture, engineering, quality]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ROADMAP-M-002, ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST, ITER-010-RESULT-SLICE-001-STOP-REDIRECT, ITER-011-PROPOSAL, ITER-011-READINESS, ITER-011-VERIFICATION, ITER-011-SLICE-001, ITER-011-SLICE-002, ITER-011-SLICE-003, ITER-011-SLICE-004]
code: []
tests: []
iteration: ITER-011
coding_input: false
---

# ITER-011：答案优先的工程问答快速验证与分阶段夯实

## 本轮目标

保留 ITER-010 已真实验证的世界模型认知、自适应调查、只读来源代理、证据包、引用、独立审核和 Web 资产，修正“证据正确但正文仍像
代码走读”的系统性答案方向问题。新主线让问题理解、答案结构、应用层验收、独立审核和页面共同使用可验证的答案层次：先回答用户目标，
原问题需要时再说明可见流程、影响或实现证据；存在证据缺口或边界时才表达限制和未知。

## 四段开发顺序

| Slice | 用户可验证出口 | 后续条件 |
|---|---|---|
| [SLICE-001](development-design/SLICE-001-answer-first-direction-probe.md) | 同一产品 Web 的 1 条代表题 + 1 条用户现场题 | 独立 Result、复盘和用户 `CONTINUE` 后才可申请 Slice2 授权 |
| [SLICE-002](development-design/SLICE-002-cross-dimension-alpha.md) | 系统性最小迭代后，3—5 条跨维度题 + 至少 1 条现场题的可用 Alpha | 独立 Result、复盘和用户 `CONTINUE` 后才可申请 Slice3 授权 |
| [SLICE-003](development-design/SLICE-003-engineering-hardening.md) | 跨工程、完整 early canary、复杂补证/恢复、安全性能、三臂消融与完整回归结果 | 独立 Result、复盘和用户 `CONTINUE` 后才可申请 Slice4 授权 |
| [SLICE-004](development-design/SLICE-004-formal-product-acceptance.md) | 最终两个 held-out 工程 10+2、现场题和正式 Web 验收 | 全部 Gate 与复盘通过后，用户另行 `ACCEPT` |

前两段不是正式验收，但 exact revision、只读、来源不可信、最小授权、Secret 隔离、逐结论 Citation、独立审核、失败真实性和 loopback
边界不能延后。持久恢复、复杂 conflict/dedup、多轮补证、完整性能安全、full regression、hidden 和三臂消融明确留到 Slice3。
每次早期体验先由独立评测方裁决技术质量，再由用户决定产品方向；用户不承担代码事实审核。

## Status and authorization

`PROPOSED / ALL SLICES NOT AUTHORIZED / NO CODING INPUT`。

用户规划反馈
`codex-user-message:sha256:7711b359a33d13ac1dd4577dd316fd4bf49d04a05aef263cfc88ad9b3ad49af4` 要求“尽快提供可验证内容，
再夯实代码”。该收据只授权制定本计划，不是产品开发授权，也不是对 ITER-010 或本轮产品方向的 `CONTINUE / REDIRECT / ACCEPT` 裁决。

ITER-010 的真实技术证据和失败记录永久保留；它的 Provider、credential、源码披露、问题、运行和 Web grant 均已消费或绑定旧产品
identity，不得在本轮复用。任何 Slice 必须在前序 exact Result 和新用户授权后单独切换为 current development；任何 live 执行还须取得
绑定当时 exact freeze、Provider、角色、输入和源码披露的一次性授权。

## Required inputs

- [Proposal](proposal.md)
- [Manifest](manifest.yaml)
- [Readiness Review](readiness-review.md)
- [Verification Matrix](verification-matrix.md)
- [Development Design](development-design/README.md)
- [Findings](findings/README.md)
- [Results](results/README.md)
