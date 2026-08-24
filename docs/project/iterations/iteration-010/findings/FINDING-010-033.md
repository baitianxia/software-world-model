---
id: FINDING-010-033
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, quality, engineering]
depends_on: [ITER-010-SLICE-001, FINDING-010-027, FINDING-010-028, SYS-ADR-016, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: require-evidence-grounded-atomic-observation-closure
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-033：宽泛 Checklist 可以被代表性事实伪闭合

## Observation

持续 Alpha 首次以 candidate `b6e13eb…` 回归现场题“登录流程是怎样的？”时，完整
`UmsAdminServiceImpl` 已进入 Question Evidence Package 和 Reviewer 输入，源码明确包含成功认证后写入登录审计记录的
`insertLoginLog(username)` 及其时间/IP 持久化效果；最终正文仍只说明凭据校验、JWT 返回和失败日志，遗漏成功路径副作用，Reviewer 却返回
`APPROVED`。

## Evidence and root cause

- 该题形成 Result `engineering_result_3ddb554b462182ef91fa1a4d0239c60b`，8 次 role dispatch，retry/switch 均为 0；
- raw Gateway audit 表明 Question Understanding 已提出“成功后的状态变化”，完整 Service source 也已读取；
- 首个语义偏差出现在 Investigation `FINISH`：一个宽泛 disposition 只用“生成 token”代表成功效果；Answer 继承该摘要，Reviewer 的独立
  checklist 仍只重复同一宽泛结论；
- 因此根因不是 Browser 投影或 Source 缺失，而是 `@2` 结构只机械保证 checklist ID coverage，不要求完整证据中的不同阶段、结果、状态变化和
  副作用分别形成可追踪 obligation；同一盲点可以跨 FINISH、Answer 和 Review 传播。

## Decision and disposition

Engineering QA 升级为 `ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3`。每个 FINISH disposition 必须从完整引用内容产生有界、原子的
`PROCESS_STAGE / OUTCOME / STATE_CHANGE / SIDE_EFFECT / LIMITATION` material observations，并逐条绑定 admissible evidence references；
Application 生成稳定 observation identity。Answer Claim 必须显式链接其文本实际表达的 observation，覆盖全部 observation、把它们放入默认
用户正文，并引用每条 observation 所需的全部 Package entries。Reviewer 从完整 Package evidence 独立重建带证据 observation，并分别列出
Package observation 与 Draft observation omission；任何 omission 阻断 `APPROVED`。

该机制不包含 mall、登录、方法名、符号、问题文本或 Oracle 分支，适用于流程、生命周期、运行、故障和影响问题。

## Verification

确定性回归构造同一 checklist 下的主流程与副作用两条 observation；只链接主流程的 Draft 被 Application 以
`CONTROL_STATE_DENIED` 拒绝，Reviewer 独立标出副作用正文遗漏时也不能批准。closed FINISH/Answer/Review schema、identity、证据分区与 Prompt
contract 测试同步升级。真实 Provider 与三题持续体验仍须基于新 clean freeze 重新执行，旧错误 Result 永久保留。
