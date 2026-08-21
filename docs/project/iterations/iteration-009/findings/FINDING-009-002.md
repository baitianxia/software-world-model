---
id: FINDING-009-002
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [interface, product, quality]
depends_on: [ITER-009-SLICE-001, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING]
code: [src/software_world_model/interface/world_model_browser_ui.py]
tests: [tests/test_world_model_browser.py]
iteration: ITER-009
classification: local-implementation
disposition: render-limitation-status-before-supported-fallback
target: src/software_world_model/interface/world_model_browser_ui.py
---

# FINDING-009-002：浏览器把无 Gap 的 Limitation 标成 SUPPORTED

## Observation and evidence

浏览器 Claim 状态原先只读取 `claim.gap_code`，为空就显示 `SUPPORTED`。合法的 Application Limitation 可以具有
`gap_code = null` 和非空 `limitation_codes`；因此 run-012 同类 typed Limitation 即使通过 Review，也会在方向体验页被误标为
supported。该事实可由原表达式 `claim.gap_code || "SUPPORTED"` 确定性复现，不依赖模型输出或网络状态。

这是展示层遗漏，没有改变 Application page、Claim schema、Owner 或调用方语义。现有 Answering 系统契约已经区分 supported、
Gap 与 Limitation，故分类为 `local-implementation`，无需修改 System 文档。

## Decision and disposition

页面状态投影现在依次显示 Gap code、`LIMITATION · <exact limitation codes>`、最后才回退到 `SUPPORTED`。浏览器回归测试固定该
优先级，并固定 Slice 要求的可见“方向体验 / 非验收 / 非生产”标记。页面同时把 4–6 调用文案改为
`Investigation 2–4 → Draft → Review`，准确反映既有 dispatch policy；服务协议和调用数量未改变。

## Verification after disposition

`tests.test_world_model_browser` 与同组策略回归均通过；未启动正式 Web，因此这里只证明静态页面资产和本地 HTTP 交付逻辑，不构成
`V-WEB-*`、方向判断或 Acceptance 证据。
