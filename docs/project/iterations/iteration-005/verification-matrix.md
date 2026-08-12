---
id: ITER-005-VERIFICATION
kind: iteration-verification
status: slice-002-run-007-live-pass-awaiting-user-acceptance
authority: planned-verification
owners: [quality]
depends_on: [ITER-005-PROPOSAL, ITER-004-RESULT-ACCEPTANCE]
code: [validation/structure_world_model_iteration_005/g0.py, validation/structure_world_model_iteration_005/slice1.py, validation/structure_world_model_iteration_005/coverage_copy.py, validation/structure_world_model_iteration_005/slice2_freeze.py, validation/structure_world_model_iteration_005/slice2_product_probe.py, validation/structure_world_model_iteration_005/slice2_comparison.py, validation/structure_world_model_iteration_005/slice2_evaluator.py]
tests: [tests/test_iteration_005_g0.py, tests/test_maven_workspace.py, tests/test_world_model_http.py, tests/test_world_model_evaluation_grant.py, tests/test_world_model_gateway_authorization.py, tests/test_world_model_product.py, tests/test_iteration_005_slice2_comparison.py, tests/test_iteration_005_slice2_evaluator.py, tests]
iteration: ITER-005
---

# Iteration 005 Verification Matrix

| Case | Claim | Level | Frozen input / oracle | Expected | Human-visible evidence | Status / blocking meaning |
|---|---|---|---|---|---|---|
| V-001 | 当前 Maven Profile 对新仓库具备最低泛化能力 | pre-coding product / contract | TTL3 `01639f2…` + Gson `310ac34…`；Maven Wrapper `e10ec82…→62c6a95…`；独立 Oracle `sha256:3989a536…` | supported 均 COMPLETE 且图/absence 与 Oracle 一致；序列先发布 valid CURRENT，再准确拒绝 unsupported 且 CURRENT 不动 | `var/iteration-005/g0/a91dc7c-r2/report.{json,md}` / `sha256:bcd7a269…`；全部 public CLI 原始 JSON | **PASS** / 允许授权 SLICE-001 |
| V-002 | 用户可见 Coverage 与正式 Schema 一致 | contract / interface | `MAVEN_REACTOR_STRUCTURE@1` 与所有 browser/dataset copy | 只声称 reactor child membership、POM-local direct internal dependency、exact diff；plugin/property/parent overclaim 为 0 | `run-005/v002-coverage-copy.jpg` / `sha256:6ed4f9b2…`；`v002-copy-audit.json` / `sha256:8fc1de51…` | **PASS / user accepted** |
| V-003 | 工作区可在零问题状态构建 R1、更新 R2 | integration / product | randomized supported repo R1 `7f3ad26…` → R2 `047792c…`；stdlib Oracle | Question/Task/Session=0；Snapshot/Bundle 发布；Root 稳定、State/删除/CURRENT/历史正确；明确 FULL_REBUILD | `run-005/report.{json,md}`、`graphs.md`、raw Workspace/diff；report `sha256:7047522d…` | **PASS** / G2 已执行 |
| V-004 | 跨 Owner 失败和恢复不伪造原子性 | fault / recovery | Bundle failure、实际 I/O 中断、stale CAS、重复幂等键、digest tamper、pointer/receipt crash | Step outcome 保留；新版本 unavailable；旧 queryable 版本可用；原 Attempt 可恢复且不重复副作用；receipt revision 连续 | `run-005/report.md` 故障表、raw Attempt；Workspace fault tests 8/8 PASS；`FINDING-005-001` | **PASS / user accepted** |
| V-005 | `SWM-READ-SET-CATALOG@1` 是可重建 no-payload manifest 且 Source-off 跨重启可用 | architecture / product | R1/R2/ordered Bundles；独立 Catalog root + Bundle root；Source/authority DB unavailable；7 类 tamper | 读取进程无需权威 DB 即验证 canonical digest、内嵌 Receipt/file manifest 并完成 candidates/inventory/path/diff；Catalog 无 Entity/Fact/Evidence payload；篡改拒绝 | Catalog/current、`catalog-audit.json`、mount manifest、raw Source-off Views 与 `tamper-*.json` | **PASS / SLICE-001 accepted** |
| V-006 | 提问与更新严格解耦 | contract / fault | 动态 exact Read Set；supported/Gap/failure questions | 每题前后 Update Attempt、CURRENT、Bundle Receipt、Source Operation 不变；无临时 Bundle/Direct fallback | before/after counter 报告与 Authority page | `run-006` 9 个 comparison + 2 个 browser terminal；`run-007` deterministic probe、9 个 World terminal 与 2 个 browser terminal 均 Source-off/无更新 | **PASS** |
| V-007 | 正式产品 Web 入口在新仓库上完成隔离 Source-off 世界模型问答 | interface / security / human | `software_world_model.interface.world_model_http`；新仓库 single/ordered Read Sets；exact launcher/role package/worker/profile digests；actual repo/`.git`/DB/Store deny targets；qualified product inputs | 不运行 `validation.*` 即可启动；supported、negative、ambiguity、Gap、Citation 和 fail-closed 正确；每问最多 1 call/0 retry；沙箱外目标可达、Answer 内 exact targets 被 OS 拒绝；Broker 只在 seal 后窄读；页面身份完整 | `run-007` startup `sha256:4ab55e41…` / preflight `sha256:3f2527b6…`；browser requests `wm-02208ddb…` / `wm-344a7ffe…`；pages `sha256:7bd6d5d8…` / `sha256:1b591fa7…`；Citation、长 identity 选择与空 console 核对 | **PASS / real browser** |
| V-008 | 实现没有项目、dataset、问题或拓扑硬编码 | contract / metamorphic | 运行时随机 system key、module names/paths/topology；独立 generator/evaluator | 动态数据集和结果随输入正确变化；产品不读取 Oracle 或 baseline | 变形输入、输出、代码扫描与 evaluator report | `run-007` randomized probe `sha256:bb75e610…`；World Model 9/9；comparison `sha256:e7d16fa4…` PASS | **PASS** |
| V-009 | 新仓库产品质量相对源码调查逐题不退步 | CC / CE / product comparison | `SWM-WORLD-MODEL-HELD-OUT-SUITE@2` 在任何 World Model Result 前密封 exact POM closures、controlled Direct/Codex protocols、baseline-first 顺序与 independent comparator；controlled Direct 密封 4096 output token、严格 JSON-only answer contract；全部 9 题先以 formal proposal stub 通过；三条路径分别授权；exact package/provider | 有效 CC/CE；每 surface 每题一次 external task、controller retry=0；World/Direct 成功 terminal Provider call=1，Mature Provider call=`null`（不可观测）；全部失败保留；逐题重大错误 0、完整性不低于两条 eligible baseline 中较强者 | `run-006` FAIL 保留；`run-007` authorization `sha256:a33d6537…`、baseline seal `sha256:cd193c00…`；Direct/Mature/World 各 9/9；comparison `sha256:e7d16fa4…` PASS、无 blocker/filter/interpolation | **PASS / run-007** |
| V-010 | 兼容、回归、正式启动手册与文档闭合 | regression / documentation | focused tests、exact staged Answer tests、full suite、current System docs、`SYS-OPS-LOCAL-BROWSER` | 全部通过；产品命令可重复启动；ITER-003/004 与 Direct 行为不变；所有 Finding 已处置 | SLICE-001 45/45 + 771/771；SLICE-002 `run-007` 51/51 focused、13/13 staged Answer、801/801 full、docs check PASS；正式产品命令启动/停止与真实浏览器 PASS | **PASS** |
| V-011 | Scheduler、真 Delta、多源、非 Maven、Production Activation | boundary | 明确非目标 | NOT EXECUTED；不得由其他 PASS 推导 | SLICE-001 Result 限制清单 | **NOT EXECUTED** / non-blocking boundary |

测试、CC、CE、Product Validation 与 Activation 不得互相替代。V-001 在产品代码前执行；V-002—V-005 已产生
[SLICE-001 Result](results/slice-001-workspace-catalog.md)，且用户已接受并授权 SLICE-002 编码。SLICE-002 的
[Run-006 Live Result](results/slice-002-run-006-live.md) 保留 V-009 `FAIL` 与 V-007 浏览器 PASS；
[Candidate Freeze](results/slice-002-candidate-freeze.md) 闭合新 `run-007` 的确定性输入、资格、未授权短路和回归；
[Run-007 Live Result](results/slice-002-run-007-live.md) 在 exact 用户授权下闭合三条 population、V-009 independent
comparison 与正式 Web 人工验收。V-006—V-010 现为 PASS，但用户尚未接受 SLICE-002 / ITER-005，因此不能标记
accepted/completed。
