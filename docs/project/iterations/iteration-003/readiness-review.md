---
id: ITER-003-READINESS
kind: iteration-readiness
status: proposed
authority: project-authorization
owners: [project, architecture, quality]
depends_on: [ITER-003-PROPOSAL, ITER-003-VERIFICATION]
code: []
tests: []
iteration: ITER-003
authorized_by: pending
authorized_at: pending
---

# Iteration 003 Readiness Review

## Reviewed exact inputs

准备工作起点固定为 ITER-002 关闭提交 `40c65840eaf146360c58ca888b97fc5bd9a0f2e2`，且新轮禁止脏工作区基线。`mall` A/B revision、递归 child module（明确排除 root project）和直接内部依赖 Oracle 已逐项核对；Structure Model、Structure View、World Model Answering、Snapshot-first 模式、Root/State 和 Publication Mode 已进入 current System Contract。正式授权时，Manifest 的开发基线必须更新为无产品代码变化的准备提交 P，不能仍指向关闭提交；授权 checkpoint 是随后单独的治理提交 Q，不要求 Q 的 HEAD 等于 P。

## Outcome, scope and non-goals

Outcome 是一个可独立构建、更新、持久化并在 Source-off 状态查询的 Maven Structure World Model 纵向闭环。范围与非目标已冻结，不把 Scheduler、多源、Schema Evolution 或其他 Semantic View 偷带入本轮。

## System contracts and unresolved decisions

ADR-014 明确 `WORLD_MODEL` 与 `DIRECT_INVESTIGATION` 的边界；本轮不再存在“知识不足时是否可以透明回源”的开放选择，答案是不可以。新 Structure Schema 只在新 Scope 做 INITIAL adoption。

Maven 正/负 fixture 已在产品代码前版本化，覆盖名称/GAV、同 GA 异版本、Profile、属性、range、external parent、重复声明、symlink/路径逃逸和 classifier，并通过正向 Maven offline reactor validate；digest 为 `sha256:418c223c…d1`。Schema、Evaluation Context、Canonicalization、mall Oracle、相互隔离的 Product input/evaluator suite、独立 closed CE suite、同模型 Direct Source protocol、成熟 Codex Source Agent protocol 与运行时随机图 generator 的 exact ref/digest 已冻结。全局 Readiness 当前只等待：

1. 本准备包形成 clean commit，并把 Manifest 的开发基线更新到该 exact commit；
2. 用户明确授权 ITER-003 / SLICE-001，Proposal、Readiness、Manifest、Index、Slice 与 `project/current.md` 在同一治理变更中转为 authorized/current。

G0 的旧 Snapshot 兼容 fixture 已由未修改产品源码的 ITER-002 baseline 生成两次，数据库 digest 均为 `sha256:081cc8e3…aaff`，报告固定旧 ID、digest 和 locator。仍待后续阶段闭合的子门不阻止授权后执行确定性 G1/G2/G3a：首次 CE 或其他外部模型分派前必须冻结 exact Provider/Adapter/Model、Provider scheme/host/port/path、默认拒绝的 Model Egress Gateway policy、有效 Conformance、credential reference 并获得本轮披露确认；G3a exact 实现形成后才能运行 closed World Model Capability Evaluation。PASS/VALID 后先按 G0 已冻结协议完成并密封同模型 Direct Source 与成熟 Codex Source Agent 两条 baseline，之后才可进入 G3b。任一子门未闭合只阻止对应后续 Gate，不能被文档描述为已经满足。

## Slice, dependency and risk closure

唯一 Slice 内的 G0→G1→G2→G3a→G3b→G4 是阻断顺序。G1 的 typed relation、稳定身份、确定性 `ENRICH`/`REPLACE_COVERAGE`、悬空/歧义/重叠拒绝不过，禁止写 Structure View/UI；G2 必须生成可验证且不含 Evidence payload 的 Snapshot Read Bundle，并在目标仓库、原工作树、权威/旧数据库和 Evidence Store 均未挂载的回答进程重启，Citation Projector 使用独立进程和存储；G2 不过，禁止模型回答。G3a 只完成无外部分派的权威链与故障反例；其 exact checkpoint 依次通过 CC、closed CE 并预先密封两条源码 Agent baseline 后，G3b 才允许隔离评测页面真实模型调用。G3b 不过，禁止产品结论。

调用预算在实现前冻结：世界模型一次回答包含规划、综合、独立审核和可选同 Read Set 重写，连同格式修正总 Provider 调用不得超过 5；超限失败关闭。同模型 Direct Source 与成熟 Codex Source Agent 的 Prompt/Tool/资源/隔离协议在 G0 冻结，不能看过 G3b 后削弱；运行前重新绑定 exact binary/model/config，并先密封全部基线结果。请求时延从 HTTP request received 到 terminal result persisted；冷启动另从 process start 计量。相对同 exact Provider/Adapter/Model 的 controlled Direct baseline，首问请求 P95 不得超过 1.5 倍，重复已建模问题请求 P95 不得超过 0.5 倍；成熟 Agent 只作为质量对照，不做跨模型时延比。世界模型逐题完整性不得低于两条基线中更强者；任一实质配置漂移必须重跑相应对照。

## Verification readiness

Verification Matrix 已冻结 contract、root project 语义、反例、A→B→A、真正隔离的 Source-off、浏览器五题、措辞/运行时标识变形、Knowledge Gap、五次重复、直接基线、旧数据库兼容和完整回归的独立阻断含义。每门产物必须可人工打开，不以测试计数替代内容核对。

## Authorization decision

**HOLD / proposed。** 当前可以提交开发前准备，不能修改产品代码。准备包提交 P 完成并得到用户编码授权后，以单独治理提交 Q 原子更新 Iteration、Slice、Manifest baseline 和 `project/current.md`；Q 后只能执行 V-001/G0 的资产机械检查与人工核对。只有绑定 Q 的 `ITER-003-RESULT-G0` 已提交为 PASS，且 `P..Q`、`Q..G0 Result` 均确认没有产品代码差异，才可修改产品代码并开始 G1。live Provider 与两条 Agent baseline 结果继续按 G3 子门控制，不阻止先完成确定性世界模型内核。
