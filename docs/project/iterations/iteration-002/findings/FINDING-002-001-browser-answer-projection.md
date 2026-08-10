---
id: FINDING-002-001
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering]
depends_on: [ITER-002-SLICE-001]
code: [src/software_world_model/interface/http_api.py, src/software_world_model/interface/browser_ui.py]
tests: [tests/test_browser_chat_interface.py]
iteration: ITER-002
classification: iteration-design
disposition: incorporated-into-slice-acceptance
target: ITER-002-SLICE-001
---

# FINDING-002-001：浏览器输出暴露内部诊断并扩张问题

## Observation

体验回答把英文的内部 Gap 模板直接呈现给中文用户，并在用户询问工程入口时追加了不构成入口答案的部署信息。旧浏览器请求还按题型词和约定文件注入额外调查范围。

## Evidence / reproduction

用户提供的实际输出包含 `Requested question`、`Verified answer` 和 `Evidence gap`，随后附带与入口问题不等价的部署步骤。`http_api.py` 的旧实现存在题型词、README 和构建文件的专用引导及扁平 Claim 投影。

## Impact

这是系统性的问题保持和展示缺陷，不是某个工程的答案文案问题。它会让正式 Gap 与旁支事实混排，并使不同工程获得不一致的调查策略。

## Classification rationale

变化调整本轮端到端请求形成和浏览器投影，但不改变 Source 或 Knowledge Owner，因此归类为 iteration-design。

## Decision and disposition

移除工程、文件和题型专用的引导；原始请求只保留对当前问题和语言的一般约束；浏览器按 Need 分组正式事实与限制，并在切换项目时创建新会话。上述行为已写入本 Slice 的 Acceptance Scenarios。

## Verification after disposition

由 `tests/test_browser_chat_interface.py` 验证问题不扩张、中文 Gap、按 Need 投影和会话重置；真实体验由 V-007 复核。
