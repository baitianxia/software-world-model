---
id: ITER-010-INDEX
kind: iteration-index
status: authorized
authority: current-development
owners: [product, project, architecture, engineering, quality]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ROADMAP-M-002, ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, ITER-010-PROPOSAL, ITER-010-READINESS, ITER-010-VERIFICATION, ITER-010-SLICE-001, ITER-010-SLICE-002, ITER-010-SLICE-003]
code: []
tests: []
iteration: ITER-010
coding_input: true
---

# ITER-010：工程问题答案优先的混合证据问答

## Status and authorization

`AUTHORIZED / SLICE-001 CURRENT DEVELOPMENT / SLICE-002 AND SLICE-003 NOT AUTHORIZED`。

用户消息 `codex-user-message:sha256:1b3270242962b8d099ac9166304dc6188be22054cfc2a685b2ade5616d4cc2f4`
先要求把环境准备到 `ITER-010` 可开发；随后消息
`codex-user-message:sha256:5cdb7000ba36328f5caa27727c6b689ad4e98e7ad13eca72837fa020d0c270c9` 于
`2026-08-21T07:10:28Z` 接受此前解释的 `ENGINEERING_QA` 混合证据架构。两条消息共同构成 Readiness 与
`SLICE-001` 开发授权链；Manifest 以较晚收据作为终结引用，并单独保存前一 preparation request。

初始授权只覆盖代码、System 文档和本地确定性测试；不覆盖 credential 读取、Provider/model 调用、正式 live Web/browser 运行、
隐藏输入披露、`SLICE-002/003` 或 Production Activation。任何 live 动作仍须绑定 exact candidate、资格、freeze 和独立授权。

本轮产品基线固定为 commit `1fb997bab6444523f82ebf1a514a1abbf79656c7`、tree
`1369ce932c778c57a118123e8257ede476229d73`。ITER-009 的体验代码保留为技术资产，但其代码走读式产品方向已由
`ITER-009-RESULT-SLICE-001-STOP-REDIRECT` 否决，不能被写成 Acceptance。

## Required inputs

- [Proposal](proposal.md)
- [Manifest](manifest.yaml)
- [Verification Matrix](verification-matrix.md)
- [Readiness Review](readiness-review.md)
- [Development Design](development-design/README.md)
- [Findings](findings/README.md)
- [Results](results/README.md)

执行顺序固定为：先在 `SLICE-001` 形成 Finding，并更新 ADR/System Contract/治理门禁，再实现最小 `ENGINEERING_QA` 混合证据链并供
真实 Web 方向体验；用户 `CONTINUE` 后才进入跨工程夯实；再次 `CONTINUE` 后才进入正式验收。`REDIRECT/REJECT` 会终止后续 Slice。
