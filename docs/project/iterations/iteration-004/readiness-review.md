---
id: ITER-004-READINESS
kind: iteration-readiness
status: accepted
authority: project-authorization
owners: [project, architecture, quality]
depends_on: [ITER-004-PROPOSAL, ITER-004-VERIFICATION, ITER-003-RESULT-ACCEPTANCE]
code: []
tests: []
iteration: ITER-004
authorized_by: user
authorized_at: 2026-08-11T15:55:42+08:00
---

# Iteration 004 Readiness Review

## Reviewed exact inputs

Baseline 为 clean commit `0d046767f42a0a64fb0f965a3095beac58eb835a`。复用对象严格绑定 ITER-003
accepted product commit `b9b329a…`、prepared registry `sha256:ace18c7c…`、batch `sha256:bf8ca1fe…`、
evaluation `sha256:7952bd9b…` 及其中三个非 Oracle selector。外部 Provider/Adapter/model/endpoint 与 accepted
G3b 一致；Secret 仍只使用 `env:ARK_API_KEY` reference。

## Outcome, scope and non-goals

Outcome 是用户从服务页面自由输入问题并实际走 Snapshot-first WORLD_MODEL 链路。范围只覆盖已密封 Maven
Structure Read Set 和本机 `EVALUATION_ONLY`；不支持任意仓库即时建模、不读 Source/Evidence payload、不回退到
Direct Investigation、不启用生产。

## System contracts and unresolved decisions

现有 World Model Answering、Deployment、Local Browser、Model Gateway 与安全契约足以约束本切片。关键设计已闭合：
使用独立 evaluation launcher，而不是把隔离角色塞回现有单进程 `http_api`；浏览器只拿 Answer Result 与 Citation
Projection；所有缺失、漂移、超时和资格错误失败关闭。没有必须由用户再选择的跨模块语义。

## Slice, dependency and risk closure

唯一 Slice 在 accepted G3b stage 与 prepared input 上增加 trusted loopback 调度和交互投影。启动时重新验签、检查
OS capability 并只暴露 allowlisted selector。请求单线程串行，request ID、问题长度和输出引用均受限；每问只允许一次
Provider dispatch，没有自动 retry。

## Verification readiness

Verification Matrix 已区分单元/契约、隔离运行、真实 Provider、浏览器产品体验和 Production Activation。测试使用 fake
runner 不替代 live smoke；live smoke 不替代完整回归；Production Activation 保持 `NOT_EXECUTED`。

## Authorization decision

用户明确要求修复该体验缺口，并已同意自由提问所需的外部调用与披露。Readiness 为 **ACCEPTED**，授权
`ITER-004-SLICE-001` 编码和本机 evaluation-only 验证；不授权 Production Activation。
