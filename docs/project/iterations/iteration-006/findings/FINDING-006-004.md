---
id: FINDING-006-004
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-006-SLICE-001, SYS-OPS-LOCAL-BROWSER]
code: [src/software_world_model/interface/world_model_browser_ui.py]
tests: [tests/test_maven_workspace.py]
iteration: ITER-006
classification: local-implementation
disposition: switch-profile-copy-and-result-state-together
target: src/software_world_model/interface/world_model_browser_ui.py
---

# FINDING-006-004：切换 Profile 后页面保留上一 Read Set 的结果

## Observation

正式页面先在 Java Read Set 展示 supported/Gap Result，再选择 Maven Read Set 时，Coverage 和示例按钮已切换为 Maven，但右侧仍
显示上一条带 `JAVA_R1_R2` badge 的 Java Result。Result 自身 identity 没有被改写，但选择态与结果态并置会制造当前结果归属
歧义。此前为兼容旧静态 copy 测试而常驻的 Maven-only screen-reader 文本，也会在 Java 选择下暴露错误 Profile 文案。

## Evidence

- 本机浏览器 DOM 在 Java → Maven 切换后同时出现 Maven Coverage 和旧 Java answer；
- 修正后相同流程回到“等待一个真实问题”，只显示 Maven Coverage 和 Maven 示例；切回 Java 后 supported 与 Gap 页面正常；
- Coverage paragraph 使用 `aria-live=polite`，不再常驻另一 Profile 的隐藏说明；
- 最终浏览器 screenshot 布局无覆盖，console warning/error 为空，Maven copy 聚焦回归和 819 项完整套件 PASS。

## Impact and classification

Read Set、Result seal 和服务端 authority 均未漂移；问题只属于 browser client 的视图状态和可访问文案，分类为
`local-implementation`。

## Decision and disposition

选择不同 dataset 时原子更新 selected Profile、清空 `state.last` 并切回 empty Result；选择当前 dataset 保持无操作。Coverage
和 example visibility 始终由所选 dataset 的 `profile_refs` 驱动。代码、copy regression 和真实浏览器复核已经处置本 Finding。
