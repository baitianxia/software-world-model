---
id: FINDING-010-029
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [architecture, application, security, interface, operations]
depends_on: [ITER-010-SLICE-001, ITER-010-PDR-001, SYS-ADR-016, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-OPS-LOCAL-BROWSER, SYS-QUALITY-SECURITY]
code: [pyproject.toml, src/software_world_model/ai_infrastructure/engineering_question_model_source.py, src/software_world_model/interface/engineering_qa_browser.py, src/software_world_model/interface/engineering_qa_live.py, src/software_world_model/interface/engineering_qa_alpha_cli.py]
tests: [tests/test_engineering_question_model_source.py, tests/test_engineering_qa_browser.py, tests/test_engineering_qa_live.py, tests/test_engineering_qa_alpha_cli.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: define-session-authority-and-system-compiled-per-question-grants
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-029：逐题 prepared grant 与持续自由提问产品契约冲突

## Observation

PDR-001 要求同一个 loopback Web Alpha 在固定工程与 exact revision 的一次启动中连续接受自由问题，普通体验者不拼装逐题 freeze、grant、
request ID 或内部参数。当前 Engineering QA System Contract、Security 和 Browser Operations 却要求 launcher 在 listener 前装载一个 exact
prepared Request/run grant，并禁止浏览器提交不同问题。现有实现因此能证明单题披露安全，却不能形成 `V-EXPERIENCE-001` 所要求的持续
产品体验。

## Evidence and root cause

- `ExactAuthorizedEngineeringQuestionRequestFactory` 只接受一个预先密封的 request ID 与 question；第二个自然问题必然
  `CONTROL_STATE_DENIED`；
- `EngineeringQuestionWebRuntimeStatus` 和 trusted preview launcher 的 identity、launch/terminal receipt 都只绑定单个 Request/run；
- 逐角色输入授权已经能在动态 Ledger/Package 形成后由 trusted boundary 收窄为 exact one-use digest，因此缺口不在角色级披露，而在其
  上游缺少“固定会话边界 + 用户提交 exact question + System Owner 编译 per-question Request/run”的权威层；
- 若简单允许任意 POST 复用旧 run grant，会使新问题、动态来源片段和调用预算获得未授权外发；若要求普通用户手工生成每题 grant，则仍
  不是持续产品。

## Decision and disposition

引入 `ENGINEERING_QA_SESSION_AUTHORITY@1`。listener 前由 operator/user 授权并密封 exact product candidate、loopback origin、工程/
Binding/revision、World Model Read Authority、Source Profile/allowlist、Provider/model/configuration/qualification/secret reference、角色
Prompt/schema、redaction、每题与整会话安全熔断、有效期和非生产状态。它只授权这个闭合边界，不授权任何尚未提交的问题或直接 dispatch。

页面必须在提交控件旁持续显示 Provider、工程/revision、可外发来源类别、排除项和非生产限制。用户点击提交时，服务规范化并密封 exact
question bytes/digest、session authority digest、唯一 server-issued request/run identity、提交时刻和披露确认，形成不可伪造的
`Question Submission Receipt`。Application/System Owner 只能从该 receipt 与固定会话模板编译一个 exact Request 和一次性 per-question
run authorization；浏览器不提供 request ID、grant 或 Provider 参数。随后仍按既有规则为每个动态角色输入形成 full-input digest 的
one-use disclosure authorization，零重试、dispatch 后不切 Provider。

每题拥有独立 Request、Ledger、Package、Answer、Review、Citation 和审计；重复提交 receipt、身份漂移、会话/题目预算耗尽或授权过期只
失败关闭当前新请求，不得把旧 Result 当作新题结果。已开始的单题按其 exact 授权到终态；一个问题的调查或审核失败不得停止 listener，
但会话总熔断或资格过期必须拒绝后续新题。Source/Provider/工程边界变化必须停止并重新冻结会话，不能由问题文本扩张。

`SYS-ADR-016`、Engineering QA Contract、Security 和 Local Browser Operations 在同一变更中写回。旧 exact prepared launcher 只保留为
历史运行/回归兼容面，并改用 `swm-engineering-qa-preview` 命令名；`swm-engineering-qa` 只指向持续 Alpha。页面和文档只能把持续入口标为当前产品。该处置不授权真实 Provider dispatch，
产品 freeze 后仍须取得 exact session/live 授权。
