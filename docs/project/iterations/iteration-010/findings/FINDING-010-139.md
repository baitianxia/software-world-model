---
id: FINDING-010-139
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [project, engineering, quality, ai, operations]
depends_on: [ITER-010-PDR-003, ITER-010-PDR-005, ITER-010-PDR-006, SYS-ADR-017, SYS-OPS-CONFIGURATION]
code: [src/software_world_model/application_services/deepseek_dispatch_admission.py, src/software_world_model/interface/engineering_chat_provider_runtime.py, src/software_world_model/interface/engineering_chat_session_artifact.py, src/software_world_model/interface/engineering_chat_alpha_cli.py, scripts/docs.py]
tests: [tests/test_deepseek_dispatch_admission.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_chat_alpha_cli.py, tests/test_docs_gate.py]
iteration: ITER-010
classification: iteration-design
scope: systemic
disposition: replace-deepseek-scheduling-preference-with-hard-pre-dispatch-admission
target: ITER-010-PDR-007
---

# FINDING-010-139：DeepSeek 闲时偏好没有形成执行门禁

> Current authority amendment：`ITER-010-PDR-008 / SYS-ADR-019` 已将当前公开来源评测改为 standing human authority。
> 下文形成时所称“新的 external/exact grant”现应解释为从该 standing authority 自动派生的 exact machine receipt；只有真正
> scope delta 或 DeepSeek 峰时 override 才需要新的人工授权。历史 run-043 的授权与调度失败事实不变。

## Observation

`run-043-pdr005-direction-canary` 在北京时间 `2026-08-27 11:19–11:27` 执行，处于当前计划冻结的
`09:00–12:00` 高峰窗口。其 terminal receipt 记录 DeepSeek `18` 次 HTTP dispatch，其中 `16` 次有完整 usage，合计
`608,785` input tokens 和 `10,679` output tokens，另有 `2` 次 `PROVIDER_OUTCOME_UNKNOWN`。同一 run 的输入、Session、launch 和
terminal 对象均没有本批官方价格检查、北京时间窗口判定或峰时 override 收据。

用户再次指出 DeepSeek 没有遵守闲时策略；该消息的本地 UTF-8 摘要为
`sha256:ba8b85ba94ed69c876bf7cf15fa060ee494afb0c3dff383042c7197bdacacc7a`。这条消息是执行治理纠正，不是峰时调用授权。

## Evidence

- `var/iteration-010/slice-001/run-043-pdr005-direction-canary/session.json` 把 exact product
  `a4bfd6acabc6d9ae8a8201f6f03cfa24b43765b8`、五个 provider-eligible Turn、Ark→DeepSeek route 和
  `2026-08-27T03:18:23Z` 的执行授权绑定到同一 planned direction run；这不是无法预见的生产突发流量；
- `deepseek-gateway.sqlite3` 中 `18` 个 terminal model call 的审计时间为 `2026-08-27T03:19:34.232484Z`，即北京时间
  `11:19:34`；`terminal.json` 与 Gateway audit 对账为 DeepSeek HTTP `18`、retry `0`、outcome unknown `2`；
- `PDR-003`、`PDR-005`、Manifest 与通用治理把 DeepSeek 调度写成“默认/优先/偏好”，没有规定窗口外必须在 Provider socket/
  connected descriptor、TLS、credential、HTTP 前 fail closed，也没有独立阻断 Case；
- 当前 Session artifact schema 和 runtime route 没有 schedule policy、trusted clock、window verdict、fresh official check 或 peak
  override 字段；Ark 进入允许的 fallback 分类后会立即启动 DeepSeek；
- `scripts/docs.py` 只验证 Manifest 中静态字符串、日期格式和窗口列表，不能证明某次 run 的真实 dispatch 时间或 override；
- DeepSeek 官方定价页在 `2026-08-27` 仍定义北京时间 `09:00–12:00`、`14:00–18:00` 为高峰，但峰谷价格生效时间待正式通知。
  用户指定的闲时调度是项目运营约束，不依赖折扣是否已经生效。

历史审计还显示 PDR-003 生效后，run-035、run-036、run-037、run-038 及三次 DeepSeek Conformance 也曾在冻结窗口外启动。
因此本次问题是系统性的计划可执行性缺口，不是 run-043 的单次操作失误。

## Decision and disposition

该发现处置到 `ITER-010-PDR-007`：

- 所有计划性开发、Conformance、Capability、canary、比较、回归和多问题体验中的 DeepSeek dispatch 都受同一硬门禁；“batch”名称不再
  决定是否受约束；
- 当前允许窗口使用 `Asia/Shanghai` 半开区间 `[00:00,09:00)`、`[12:00,14:00)`、`[18:00,24:00)`。是否已经正式执行峰谷价格
  不影响该项目门禁；
- 下一次 DeepSeek dispatch 前必须先形成可审计 admission receipt，并在每个新 request 前重验窗口/override。窗口外没有 exact user peak
  override 时，必须在 Provider socket/connected descriptor provisioning、TLS acquisition、credential resolution 和 HTTP dispatch 前关闭，
  相应计数均为 `0`；
- 峰时不得停止整个开发：Ark-only、本地归因、修复、mock、targeted tests、candidate freeze 和其他独立安全工作继续。需要峰时例外时按
  PDR-006 直接申请 exact delta，不能从普通 canary、Provider 或 fallback grant 推导；
- planned canary 必须在开始前保证其完整最坏质量链可在允许窗口结束前完成；不能先在峰时开题，再以“问题已经开始”为由触发
  DeepSeek；
- run-043 永久保留为真实调用、成本和失败证据，但标记为 `DEEPSEEK_SCHEDULING_POLICY_FAIL / NOT_DIRECTION_ACCEPTANCE_EVIDENCE`；
  不得为了修正调度记录立即重跑。先从该 run 做本地归因，只有产生通用候选并进入允许窗口后，才可按 PDR-008 自动派生的 exact
  machine receipt 执行一次后继 canary；
- 自动运行时门禁、逐 dispatch receipt 和注入时钟验证是当前 Slice 的开发输入；在本发现形成与计划修订时尚未修改产品/System 代码，
  后续实现证据单列如下，不能追溯改写 run-043。

## Implementation evidence

后续产品修改已由 `03520eb2b01e16116b3419dd5f1aa562e96cd21c` / tree
`9a73b04641e681ab6d9a9e3499b36d6f831c1a3c` 实现，`ITER-010-RESULT-V-DEEPSEEK-IDLE-001` 以外部调用、credential、TLS 和 HTTP
均为 0 的本地确定性证据把 Case 更新为 `PASS / local-dispatch-admission-only`。实现包括：

- typed plan、official pricing check、exact peak override、run receipt、逐 execution-envelope authorization 与注入时钟；
- `SWM-ENGINEERING-CHAT-ARTIFACT-SESSION-CONFIG@3` 的 closed admission input，以及旧 `@1/@2` 只读兼容、current preparation fail closed；
- Model Gateway preflight 与实际 invoke 前的双重 current-window/override/identity/budget 检查；
- fixed CLI 在 listener 前拒绝 denied admission，terminal 对账同一 receipt、Gateway envelope 与 transport dispatch。

该实现关闭“门禁不存在”的本地缺口；PDR-008 standing authority 的自动 machine-receipt 派生、允许窗口、fresh 官方检查和真实
launch/terminal receipt 仍须由后继 run 独立证明。只有 scope delta 才需要新的 human grant。
