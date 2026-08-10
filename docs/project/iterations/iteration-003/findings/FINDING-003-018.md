---
id: FINDING-003-018
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-003-SLICE-001, FINDING-003-017, ITER-003-VERIFICATION]
code: [validation/structure_world_model_iteration_003/questions/mature-agent-baseline-protocol-1.0.2.json, validation/structure_world_model_iteration_003/v009]
tests: [tests/test_iteration_003_validation_assets.py, tests/test_iteration_003_v009.py]
iteration: ITER-003
classification: iteration-design
disposition: replace-legacy-read-only-sandbox-with-root-deny-permission-profile-and-requalify-v009
target: ITER-003-SLICE-001
---

# FINDING-003-018：Mature baseline 的 legacy read-only 不能证明精确源码隔离

## Observation

第四轮 V-009 在 checkpoint `c2ab31b14a6d052eb42fc70941608b903b061347` 上取得 exact
Conformance PASS，再取得 closed CE 7 PASS、0 FAIL、0 UNKNOWN 与 PASS/VALID qualification。
在任何 baseline 模型请求发出前，运行前兼容性审计发现：冻结的 Mature Agent 命令带
`--sandbox read-only`，而当前 Codex CLI 明确把 `--sandbox` 解释为 legacy sandbox 设置。该设置只禁止
写入，并不等价于协议要求的“只允许 exact isolated checkout，其他文件打开全部失败”。

Codex 当前官方 Permissions 文档也明确说明：只要命令传 `--sandbox`，就使用旧 sandbox settings 而不是
`default_permissions` / `[permissions]`。因此不能一边保留该 flag，一边用新的 filesystem allowlist 证明
原仓库、checkout parent、用户目录与临时目录不可读。

## Evidence

- qualified input freeze：`ITER-003-V009-EXACT-INPUTS@1.0.3` /
  `sha256:10620f4eb47b41b8ec4216d04d7a501e9766987163e2888585e412ece492ff17`；
- Conformance binding：`sha256:6aac75eee21f2a2e75fc0bad2acdac8af6e73123cff4d980693fe6f98003595c`；
- closed Result：`evaluation_result_4c4453b448fd4e6b9cbb923ec0e2398f` /
  `sha256:7df13becf23f2499089c49517fbe38fe55a5703c3ad44072457b05830c2a48b3`；
- qualification：`capability-evaluation:evaluation_result_4c4453b448fd4e6b9cbb923ec0e2398f` /
  `sha256:af4527a5f87daa5bba217d0166beef6d67a18dcf410d27a41ac90dbce8114782`；
- 原始证据目录：`var/iteration-003/v009/c2ab31b14a6d052eb42fc70941608b903b061347/`；
- 本机 `/Applications/ChatGPT.app/Contents/Resources/codex exec --help` 把 `--sandbox` 描述为 legacy
  `read-only | workspace-write | danger-full-access` 策略；二进制还报告 permission profile 与 legacy
  sandbox mode 不能组合；
- 无模型 Seatbelt 探针使用 root deny、minimal runtime read、exact workspace read、temp deny、network deny
  的自定义 profile：读取 isolated workspace 成功，读取原仓库 `docs/project/current.md` 以
  `Operation not permitted` 失败；
- 官方当前文档：`https://learn.chatgpt.com/docs/permissions`；
- 审计阶段没有发起 controlled Direct 或 mature Agent baseline 请求，没有可被挑选的 baseline
  success/failure。

## Impact and classification

该冲突使原 Mature baseline 无法满足自身冻结的 OS 文件访问边界，因而阻断 V-009。它不改变 System
Contract、产品实现或产品 Oracle，只修正验证协议与 exact gate inputs，故分类为
`iteration-design`。第四轮 7/7 PASS 是真实且不可变的历史证据，但不能授权改变后的 baseline。

## Decision and disposition

保留 `@1.0.1` 作为历史协议，新增
`ITER-003-MATURE-SOURCE-AGENT-BASELINE@1.0.2`：删除 `--sandbox`，改用明确的
`default_permissions=mature_source`；其 filesystem 先 `:root=deny`，只重新开放 `:minimal=read` 与
`:workspace_roots/.=read`，并显式拒绝 `$TMPDIR`、`/tmp` 与 sandboxed command network。命令继续
`--ignore-user-config` / `--ignore-rules`，增加 strict config，禁用 Web Search、Apps 与 multi-agent；
Codex model/effort 明确固定为 `gpt-5.6-sol` / `low`，并绑定 prepared binary 与 bundled model catalog
digest。

首次模型请求前必须以同一 permission profile 保存 allowed workspace read 以及 denied original
workspace、checkout parent、home、temp 与 network probes。每个 case/run 继续使用只含授权 POM 与 answer
schema 的独立 workspace，保存 exact argv、事件流、stdout/stderr、退出状态和模型提出的全部文件操作。

新 `ITER-003-V009-EXACT-INPUTS@1.0.4` 绑定第四轮 PASS、本 Finding 和 Mature protocol `1.0.2`。
由于 baseline protocol/model/config 属于 V-009 exact inputs，`@1.0.3` qualification 不可复用；必须从
新的 clean checkpoint 完整重跑 Conformance 和全部七个 CE Case，再运行两条 baseline。

## Verification after disposition

资产测试必须机械验证 Mature exact argv 不含 `--sandbox`、权限 profile 包含 root deny / minimal runtime /
workspace read / temp+network deny、模型与 effort 明确固定、Web/Search/Apps/multi-agent 禁用，并以真实 CLI
完成 strict parse smoke。V-009 runtime verifier 重新绑定新 protocol raw digest、binary、answer schema、
model catalog 与 profile identity；文档检查、聚焦测试和全量测试通过后形成新 clean checkpoint。
