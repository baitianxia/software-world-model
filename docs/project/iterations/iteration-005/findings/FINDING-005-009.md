---
id: FINDING-005-009
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-005-SLICE-002, ITER-005-VERIFICATION]
code: [src/software_world_model/interface/world_model_browser_ui.py]
tests: [tests/test_world_model_browser.py]
iteration: ITER-005
classification: local-implementation
disposition: constrain-dynamic-read-set-grid-tracks-and-wrap-identities
target: src/software_world_model/interface/world_model_browser_ui.py
---

# FINDING-005-009：长 Read Set identity 会让选择卡溢出并被结果面板遮挡

## Observation

`run-005` 的真实浏览器验收中，第一个 Read Set 可以完成 Supported 问答，但第二、第三个 Read Set 的卡片不能改变选中状态。
语义 click、DOM click、键盘激活和坐标 click 均复现；页面 console 没有错误，刷新后仍然存在。

## Evidence

浏览器在 1280 px viewport 报告三张 `.dataset` 卡的宽度均约为 333 px，而 composer panel 只有约 494 px。第二、第三张卡
实际溢出到右侧 result panel 下方，后者截获指针；截图同时显示长 `read_set_*` 和 workspace identity 没有换行。根因是
`.dataset-grid` 使用 `repeat(3,1fr)`，Grid track 的自动最小尺寸被不可断行的 identity 撑开。

同一 run 的首个 Read Set 已真实返回 `SUPPORTED`，覆盖边界问题也返回
`CHANGE_INTENT_OUTSIDE_STRUCTURE_COVERAGE`，两次均为 Provider/Network/Retry=`1/1/0`；因此问题局限在浏览器选择控件布局，
不改变 World Model、Read Set 或 Gateway contract。

## Impact and classification

该缺陷使动态 Catalog 中除首项外的 Read Set 在双栏 viewport 下不可操作，阻断正式浏览器验收。它不改变调用方、接口语义或系统
不变量，分类为 `local-implementation`。

## Decision and disposition

- Grid track 改为 `repeat(3,minmax(0,1fr))`，禁止 min-content 扩大列宽；
- `.dataset` 显式使用 `min-width:0`，长 Read Set/workspace identity 使用 `overflow-wrap:anywhere`；
- 新增静态资产回归测试，锁定三条必要的收缩/换行约束；
- `run-005` 的浏览器失败与 comparison `FAIL` 保持不变，不覆写、不重试；修改后的 launcher 必须重新密封为新候选并重新执行浏览器验收。

处置仅落在代码和测试，因为这是现有“可选择动态 Read Set”行为的局部布局实现缺陷，不新增系统契约或长期质量规则。
`run-006` 真实浏览器复核中三张卡均约 139.5 px 且位于约 436.5 px 的 parent 内，第三张卡通过普通语义 click 成功选中；
supported/Gap 后续操作与 console 检查均通过。
