---
id: ITER-004-PROPOSAL
kind: iteration-proposal
status: completed
authority: historical-project
owners: [product, engineering]
depends_on: [ITER-003-RESULT-ACCEPTANCE, SYS-ARCH-DEPLOYMENT, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-OPS-LOCAL-BROWSER, SYS-QUALITY-ACCEPTANCE, SYS-QUALITY-SECURITY]
code: [src/software_world_model/interface, validation/structure_world_model_iteration_004]
tests: [tests/test_world_model_browser.py, tests/test_iteration_004_interactive_browser.py]
iteration: ITER-004
coding_input: false
---

# ITER-004 Proposal：可自由提问的 World Model 本机体验

## Trigger and evidence

ITER-003 已证明隔离的 Snapshot-first World Model 在冻结与随机化 Maven Structure 问题上通过，但其 G4
浏览器工件只回放预先完成的 terminal。正式 `/v1/browser/chat` 仍只装配 ITER-002 Evidence-first
`DIRECT_INVESTIGATION`，用户不能从服务页面输入新问题并走 ITER-003 链路。用户实际体验暴露了这一系统性
产品入口缺口。

## Outcome and users

本机用户可以在永久标记为 `EVALUATION_ONLY / WORLD_MODEL` 的独立页面中选择一个已密封的 Maven Structure
Read Set，自由输入问题；每次请求必须实际执行 accepted ITER-003 Answer worker、exact Model Egress Gateway 和
独立 Citation Projector，并显示答案、Snapshot/Read Set/Bundle、View/Coverage/Gap、引用和完整权威链。

## Scope / non-goals

范围只包含已接受 ITER-003 工件中的 `ORDERED_A_B`、`EXACT_B` 与 `EXACT_FIXTURE_VALID` Read Set，单轮自由问题，
本机回环 HTTP，以及一问一次、无隐藏重试的外部模型调用。问题超出 Maven reactor Structure Coverage 时必须返回
Knowledge Gap。

非目标包括任意仓库自动建模、在提问时读取 Source、Evidence-first 回退、对话记忆、自动更新、认证、网络部署、
Production Activation 和改变 ITER-003 的历史裁决。

## Adopted system IDs

- `SYS-ADR-014`
- `SYS-ARCH-DEPLOYMENT`
- `SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING`
- `SYS-CONTRACT-APPLICATION-STRUCTURE-VIEW`
- `SYS-CONTRACT-AI-MODEL-GATEWAY`
- `SYS-OPS-LOCAL-BROWSER`
- `SYS-QUALITY-ACCEPTANCE`
- `SYS-QUALITY-SECURITY`

## Development slices and dependencies

本轮只有 `ITER-004-SLICE-001`。入口必须复用 ITER-003 exact product package、no-payload Bundles、Gateway 资格与
角色隔离，不把 validation Oracle、baseline、Source 或 Evidence payload 装入 Answer worker。浏览器桥接层是 trusted
evaluation launcher，只负责请求排队、选择已密封 Read Set、启动隔离角色、验证 Result 并投影给页面。

## Risks and unknowns

- accepted `var/` 工件缺失、digest 漂移、资格失效或 OS sandbox 不可用时必须拒绝启动；
- 自由问题不等于全问题支持，解释器不能识别或正式知识不覆盖时必须显示 Gap；
- 当前服务无认证且一次只处理一个问题，只能绑定回环地址；
- 浏览器不得把 `DIRECT_INVESTIGATION` 结果静默标成 `WORLD_MODEL`；
- 新入口不能降低 ITER-003 对 Answer/Gateway/Projector 的文件与网络隔离。

## Verification and acceptance

机械测试验证 route、dataset allowlist、输入边界、Result digest、Citation 分离读取、无 Direct fallback 与失败关闭；
真实本机浏览器验证自由输入、长期水印和页面内容。至少执行一个此前未作为 exact 产品问题出现的支持问题和一个明确
超出 Coverage 的问题，均通过相同隔离链路；全部 Provider 调用与失败永久保留。完整回归与文档门禁必须通过。

## Authorization decision

用户于 2026-08-11 明确要求“调整下，否则如何让体验最新的开发结果呢”，并在前一消息明确同意自由问答所需的
外部模型调用与披露。该授权只覆盖本轮本机 `EVALUATION_ONLY` 体验和用户主动提交的问题，不包含 Production
Activation。
