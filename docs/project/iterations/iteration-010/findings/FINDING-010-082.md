---
id: FINDING-010-082
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, quality, architecture]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-081, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py, scripts/docs.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py, tests/test_engineering_question_cognition.py, tests/test_engineering_qa_source.py, tests/test_engineering_qa_live.py, tests/test_engineering_qa_preview_cli.py, tests/test_engineering_qa_alpha_cli.py, tests/test_engineering_qa_browser.py, tests/test_docs_gate.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: require-original-question-fulfillment-scan-and-operational-input-output-handoffs
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-082：Challenge 必须独立复核原问题履约而非只审核已有组件 Claim

## Observation and evidence

run-030 的 Q2 已有完整 original question、包含登录响应和 JWT filter 的 Package、Answer 与两次独立 Review；现有 exact checklist/
observation coverage 和 evidence-boundary lead 都闭合，仍把“组件参与”误当“新开发者可按步骤完成调用”。这不是 mall、登录、JWT 或中文题的
个例：任何 startup、call、usage、integration 或 diagnosis 问题都可能同时具备局部正确 Claim，却缺少用户动作顺序、前一步输出到下一步
输入的交接，或已知值与授权边界 unknown 的明确分离。

## Decision and disposition

- Question Understanding 对 startup/call/use/integrate/diagnose 类问题必须形成 operational checklist：按适用范围分别覆盖 prerequisite 或
  build/start 动作、首个请求及输入、返回值、跨步骤输入/输出交接、结果/失败，以及仍为 unknown 的运行参数。依赖、类、filter、handler
  清单不能替代动作或 handoff。
- Application 为每个具有默认正文与引用 Package evidence 的 Draft 再投影一个稳定
  `ORIGINAL_QUESTION_FULFILLMENT_SCAN`。它绑定全部 default Claim、实际引用 entry，并要求独立检查
  `DIRECT_USER_GOAL / ORDERED_USER_ACTIONS / INPUT_OUTPUT_HANDOFFS / KNOWN_UNKNOWN_BOUNDARY / MATERIAL_OUTCOMES`；不按工程、问题、
  语言、关键词、符号、类、方法、fixture 或 Oracle 路由。
- Review disposition 增加 `DRAFT_OMITS_MATERIAL_REQUIREMENT`。若 Package observation 已足够而 Draft 只缺组织或交接，走
  `REWRITE_WITH_EXISTING_EVIDENCE`；若 cited full Package content 已证明所需事实但 Application observation 缺失，同时记录 exact
  Application omission 并走 successor gap delta。Application 还机械拒绝把 material-effect 或 original-fulfillment 专用 disposition
  错用于其他 challenge kind。
- Answer 对上述问题必须把 supported observations 组织为可执行用户序列，显式连接每个 material output 到下一动作输入，并分开具体已知值与
  configuration-backed unknown；组件罗列不能取得 actionability。
- Strategy/Prompt/Review output identity 升级为
  `engineering-qa-adaptive-investigation-local-contract@23` /
  `engineering-qa-adaptive-investigation-prompt@33` / `engineering-qa-review@8`。新增确定性恢复链证明 comprehensive provisional
  approval 之后，fulfillment challenge 能以 `DRAFT_OMITS_MATERIAL_REQUIREMENT` 阻断组件清单，并在同 Package rewrite 成可执行步骤后
  才由双 Review 授权；专用 disposition 与错误 challenge kind 的组合失败关闭。
- 三个核心模块当前 80/80 PASS，Engineering QA 九模块 117/117 PASS；扩展 docs/oracle/full deterministic Gate 由后续
  `FINDING-010-083` 记录。系统真值已同步到 `SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING`。
