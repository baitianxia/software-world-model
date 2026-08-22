---
id: FINDING-010-023
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-022]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/interface/engineering_qa_browser.py, src/software_world_model/interface/engineering_qa_browser_ui.py]
tests: [tests/test_engineering_qa_browser.py, tests/test_engineering_question_answering.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: distinguish-approved-results-from-fail-closed-limitations-in-the-browser
target: src/software_world_model/interface/engineering_qa_browser_ui.py
---

# FINDING-010-023：Browser 把未进入 Answer/Review 的失败关闭标成 REVIEWED RESULT

## Observation

第六次 `V-WEB-000` 以 `INDEPENDENT_REVIEW_RESERVE_EXHAUSTED` 关闭，且 `answer_attempts=0`、`review_attempts=0`。产品主视图仍显示固定 eyebrow
`REVIEWED RESULT`；正文只给出“调查或独立审核未形成可授权答案”的通用文案。开发者详情包含 usage 和 `review: null`，却不包含 Result 已密封的
`terminal_reason`，必须结合 Request limit 与状态机代码才能确定是审核预留熔断。

## Evidence and root cause

- Application Result 已持有并摘要绑定 `terminal_reason`，`model_view().limitation.reason` 也正确输出该值；
- `engineering_qa_browser_ui.py` 把所有 HTTP 200 Result 的 eyebrow 硬编码为 `REVIEWED RESULT`，没有根据 `value.status` 区分；
- `developer_details` 投影没有 `terminal_reason`、`answer_reached` 或 `review_reached`；
- Browser presentation 覆盖 limitation 时使用同一通用 message，没有把已知预算关闭解释成用户可理解的限制。

根因属于 `local-implementation / systemic` 的 Result presentation 缺口。它适用于任何在 Answer/Review 前失败关闭的工程问答，不依赖本题或
Provider。

## Decision and disposition

- Application developer details 明确输出 `terminal_reason`、`answer_reached` 和 `review_reached`；
- Browser 对 `INDEPENDENT_REVIEW_RESERVE_EXHAUSTED` 显示“调查在预留独立审核所需调用额度前达到本次上限”，其他安全熔断保持通用、诚实的
  fail-closed limitation；
- UI 仅在 `status == APPROVED` 时显示 `REVIEWED RESULT`，失败结果显示红色 `FAIL CLOSED`；
- 不把 internal terminal code 平铺到普通用户正文，不把失败 Package 中的 support candidate 当成授权答案。

该变化实现现有 Local Browser Contract 的“默认主视图展示用户可理解的 limitation、诊断折叠在开发者详情”，处置到 Browser/Application
代码与回归测试，无需改变 System Contract。

## Verification

直接 Browser/Application 26/26 PASS；新 fixture 机械证明低预算 Result 的 HTTP 状态仍可返回密封审计对象，但主结果为
`FAILED_CLOSED`、limitation 明确审核预留、delivery authorization 为 false，developer details 证明 Answer/Review 都未到达。新的 product
candidate 通过 focused 118/118、docs 399/399、`py_compile` 与 `git diff --check`。更新 current Local Browser 状态时，第一次 full run 正确
暴露 ITER-007 readiness manifest 仍绑定旧 system fileset digest；同步 ITER-007/010 的 exact digest 后，针对性 84/84 PASS，最终允许
AF_UNIX 的 full discovery 共 1114 项，其中 1109 PASS，唯一 4 FAIL + 1 ERROR 的 identity、marker 与 Codex digest 精确保持
`FINDING-008-020` 历史 hold，没有新增失败。本 UI 变化发生在第六次 live run 后，因此该 run 不能追溯证明新页面已生效。
