---
id: ITER-005-READINESS
kind: iteration-readiness
status: accepted
authority: project-authorization
owners: [project, architecture, quality]
depends_on: [ITER-005-PROPOSAL, ITER-005-VERIFICATION, ITER-004-RESULT-ACCEPTANCE]
code: []
tests: []
iteration: ITER-005
authorized_by: user
authorized_at: 2026-08-11T18:10:12+08:00
---

# Iteration 005 Readiness Review

## SLICE-002 live authorization and result update

用户于 `2026-08-11T22:08:23Z` 单独授权 held-out suite `sha256:04f50cae…` 的 9 个问题与 exact Maven POM 源码闭包
发送至火山引擎 Ark 和 OpenAI Codex，仅用于 `EVALUATION_ONLY`，并明确禁止 Production Activation。authorization
document `sha256:a33d6537…` 精确绑定三条 disclosure scope；product grant `sha256:bfeecc85…` 绑定同一 suite、candidate
commit/tree、qualification、Provider 与 launcher。

`run-007` 随后按 baseline-first 密封顺序完成：controlled Direct、Mature Source Agent、World Model 均 9/9；independent
comparison `sha256:e7d16fa4…` 为 PASS；正式产品 Web 入口的 supported、Gap、Citation、动态 Read Set 选择、长 identity
布局与空 console 也全部通过，listener 已停止。详见 [Run-007 Live Result](results/slice-002-run-007-live.md)。这使
SLICE-002 当时达到等待用户验收状态；用户随后于 `2026-08-12T08:44:55+08:00` 通过独立消息接受 SLICE-002 与 ITER-005。
该 Acceptance 不是由 Readiness 文档自动产生，Production Activation `NOT_EXECUTED`。

## SLICE-002 post-implementation freeze update

`run-006` 已在 exact 用户授权下完成三条 live population 与真实浏览器验收：浏览器 PASS、comparison FAIL；全部失败由
[Run-006 Live Result](results/slice-002-run-006-live.md) 保留。`FINDING-005-009/010` 后的 `run-007` 重新密封
product-owned launcher/runtime、candidate Answer/Gateway wrapper、role/profile、held-out suite `sha256:04f50cae…`、independent
evaluator `sha256:020287ba…` 与 comparison runner `sha256:e3da9685…`，并通过 51 focused、13 staged Answer、801 full
regression、docs check、未授权 comparison pre-dispatch 和 product pre-listen gate。旧授权绑定 `run-006` suite，不能用于
`run-007`。详见 [SLICE-002 Candidate Freeze](results/slice-002-candidate-freeze.md)。

## SLICE-002 authorization addendum

用户于 `2026-08-11T19:32:39+08:00` 回复“继续开发”，接受 SLICE-001 Result 并授权 SLICE-002 编码。已接受的
ITER-003 Answer/Prompt/Strategy、Gateway、Broker、Projector package 保持逐字节不变，绑定 commit/tree
`b9b329a…` / `43accc4…`、stage manifest `sha256:b5556501…`、有效 Conformance
`sha256:c86aad99…` 与 Qualification `sha256:005b1bf4…`。Provider subject 仍是 Ark /
`openai-chat-completions-no-tools@8` / `glm-5-2-260617` 与 exact HTTPS endpoint。

`FINDING-005-002` 处置了“在新增 launcher 尚未实现前要求其 file digest”的循环前置条件：编码前冻结 public contract、
继承 package 和资格；实现后、监听前再密封 launcher/runner/profile exact provenance 并重验。每个 exact suite 的 World
Model、controlled Direct 与 Mature Source Agent 披露仍需用户单独授权。该规则已分别用于 `run-006` 与 `run-007`，两个
授权只覆盖各自 suite；Production Activation 继续不授权。

## Reviewed exact inputs

代码基线为 clean commit `a91dc7c8446f3815bf7b4f9a1123b6242620a97e` / tree
`73b8cf52e0ab5202137dd833445ced237ef698cd`。已核对 ITER-003/004 接受结果、当前 Maven Update/Bundle CLI、
Structure View、World Model browser adapter，以及 ITER-004 launcher 的固定 product/dataset 绑定。

本次诊断实际运行 `tests.test_maven_structure_cli` 与 `tests.test_iteration_003_g1_integration`，5/5 PASS。随后冻结独立
G0 Oracle `sha256:3989a536…` 并只通过 public CLI 运行：TTL3 `01639f2…` 的 8 modules/5 direct edges、Gson
`310ac34…` 的 7 modules/6 direct edges 与 Entity/Relation/absence Oracle 全部一致；Maven Wrapper
`e10ec82… → 62c6a95…` 先发布 COMPLETE，再因 reactor 内 `type=pom` 依赖明确拒绝，CURRENT 保持
`structure_snapshot_53eaf6…`。完整报告为 `var/iteration-005/g0/a91dc7c-r2/report.json` /
`sha256:bcd7a269…`。

## Outcome, scope and non-goals

Outcome 是用户指定的、符合当前 Profile 的本机 Maven 仓库可以独立构建、更新、跨重启复用，并最终通过产品代码拥有的
正式本机 Web 入口进行 Source-off 问答。范围保持 Maven Structure 与 `EVALUATION_ONLY`；Scheduler、多源、其他语言、
真 Delta、认证、网络部署和 Production Activation 均不属于本轮。

## System contracts and unresolved decisions

现有 Knowledge Update、Structure Model、Snapshot/Bundle、Structure View、World Model Answering、部署与安全契约足以
约束主方向；current Management、Knowledge Use 与 Persistence 已补充 Workspace Owner、跨 Owner 恢复以及
`SWM-READ-SET-CATALOG@1` 的生成、Receipt/file manifest 验证、CAS、重建和 Source-off 挂载语义。

SLICE-001 的输入和 Contract 已闭合；以下是 SLICE-002 编码前识别的三个 implementation-time 输入及当前处置：

1. SLICE-002 exact product-owned launcher/Answer/Gateway/Projector/worker/profile subject，以及由此决定的 CC/CE/Product
   Validation 输入与旧资格可继承性裁决；`run-007` 已密封并确定性 requalify；
2. World Model、controlled Direct、成熟 Source Agent 三条真实外部分派的实际披露内容和用户授权；它们不阻断编码，
   但严格阻断真实调用和最终接受；`run-006` 与 `run-007` 均取得各自 exact 授权并完成，授权不能跨 suite 复用；
3. 新增 launcher/runner/profile 的实现后 exact provenance；`run-007` 已密封，任何后续 bytes 漂移都要求新 freeze。

## Slice, dependency and risk closure

SLICE-001 先做无模型的 G0、工作区更新、Bundle 与动态 Catalog；它必须先产出人可读结果。SLICE-002 只有在前一结果
被人工接受、产品输入重新冻结并再次检查 Readiness 后才可授权，但它是 Iteration Acceptance 必需项。问题请求永远不能
拥有更新权限，管理入口优先使用 CLI，不把本机仓库路径暴露给无认证问答 HTTP。一次性 validation launcher、静态回放页
或只有 API 测试都不能替代正式 Web 人工提问。

## Verification readiness

Verification Matrix 已区分代码现状审计、确定性契约/故障、Source-off 产品、真实模型产品对照与 Production Activation。
V-001 与 SLICE-001 已 PASS 并被用户接受。`run-006` 的 V-007 真实浏览器部分 PASS、V-009 FAIL 原样保留；`run-007` 已使
V-006—V-010 全部 PASS；用户随后接受 SLICE-002 / ITER-005 Result。

## Authorization decision

用户明确要求开发 ITER-005；G0、System write-back 与 SLICE-001 输入均已闭合。Readiness 为 **ACCEPTED**，用户随后
通过独立消息接受 SLICE-001、授权 `ITER-005-SLICE-002` 编码，并分别对 `run-006` 与 `run-007` 作 exact live disclosure
授权。`run-007` live gate 已 PASS；用户后来另行确认最终 Acceptance。Production Activation 保持 `NOT EXECUTED`。
