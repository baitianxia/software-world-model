---
id: FINDING-010-049
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-039, FINDING-010-048]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_model_source.py, tests/test_engineering_question_strategy.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: align-required-path-closure-with-the-investigation-fuse-and-preserve-provider-outcome-identity
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-049：必读路径集合与调查熔断不可达，Outcome Unknown 被误报为 binding drift

## Observation and evidence

`FINDING-010-048` 的处置形成 clean candidate
`00afecd5c80ab842876f5c40e859634411bab6d0` / tree
`d555c37ec532e8448afbbad131738fc3874239a6`。fresh DeepSeek Conformance run-016 以 2/2 request PASS，Result
`sha256:df22a7eb3e289a5edaf6b11ab61df35bfffc63e34780614e4a2e74e821020df4`，actual model
`deepseek-v4-pro`、retry 0。随后在固定 mall revision
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` 的同一持续 Alpha 中依次提交三题：

- 原现场题“登录流程是怎样的？”的 Question Understanding 正确新增了独立的持久化/审计/缓存/通知/外部交互副作用 checklist，并声明
  6 个 mandatory-read paths。调查完整读取 Controller、Service、README、JWT utility/filter 等证据，且下一项 unknown 明确指向登录日志
  持久化；第 12 次总 dispatch 在 Provider dispatch 后进入 `PROVIDER_OUTCOME_UNKNOWN`。Gateway 原始状态正确为
  `OUTCOME_UNKNOWN`，retry 0，但页面错误显示“Result is outside the exact authorized Provider binding”；
- 本地构建/安全接入/resources unknown 混合题声明 8 个 mandatory-read paths。1 次 Understanding 后，12 次 Investigation 全部被
  search/read 消耗，尚未读取全部 required paths 或形成 FINISH，Application 以预密封调查上限失败关闭；
- 401/403 排障题声明 6 个 mandatory-read paths。搜索一个 required symbol 后，角色还读取同一搜索结果中的非必读相关文件；1 次
  Understanding 加 12 次 Investigation 后只搜索到最后一个必读测试文件，仍未读取或 FINISH，同样因安全上限失败关闭。

terminal receipt
`sha256:b3c94c2d30194a42a9a0b286a190ef16b345b662b657acff6b0c7700c283c67b` 记录 3 个 accepted question、
38 次 dispatch（12/13/13）、retry 0、Provider switch 0、Production Activation `NOT_EXECUTED`；第一题 transport audit 精确记录
1 个 post-dispatch outcome unknown。session、launch、Gateway SQLite 和 terminal receipt 均为 `0600`。同一 listener 上的 22,000 字符
输入在本地预检失败关闭，Gateway call root 在提交前后均为 38，证明没有外发；服务随后优雅停止。

## Root cause

- closed schema 与 Domain 允许 1—8 个 mandatory-read paths，但当前 frozen initial-investigation fuse 只有 12 次角色调用。最坏情况下每个
  路径各需要一次 SEARCH 和一次 READ/PARSE，另需一次 FINISH；8 个路径在执行前已经数学不可达；
- `eligible_locator_references` 只排除已完整消费路径，没有在未读 required path 存在时优先收窄到 required locators。一次搜索返回多个相关
  文件后，模型可把稀缺步骤花在非必读 caller、interface 或 wiring 上；
- Prompt 提到“remaining fuse”，但 Initial Investigation 输入只暴露 limits digest，没有提供本 attempt 的精确总步数和剩余步数；
- exact Provider terminal propagation 只把 `FAILED` 和 rejected completed output 识别为已验证 binding，漏掉同样具有 exact manifest、request、
  isolation receipt 和 eligibility identity 的 `OUTCOME_UNKNOWN`，因而落入通用 qualification/binding-drift 分支。

## Decision and disposition

- Question Understanding 的 mandatory-read path 上限从 8 收紧为 4。对当前 12-call initial-investigation fuse，最坏 4 次 SEARCH + 4 次
  READ/PARSE + 1 次 FINISH 后仍保留 3 次自适应余量；这不减少 material checklist 或 required evidence class，只要求选择最小决定性文件集，
  可选佐证不得占用 mandatory capacity；
- 当仍有 unread required paths 时，Application 只向角色暴露已签发且属于这些路径的 locator；若没有，则角色只能为 unread required path
  继续 SEARCH 或尝试会被既有 required-path closure 拒绝的 FINISH。所有 required paths 消费后才恢复其他未消费 locator；
- Initial Investigation 输入新增 exact maximum 与“含当前动作”的 remaining call count，Prompt 要求在证据闭合后保留一个 FINISH 动作，
  不得把最后一步用于可选探索；
- exact `OUTCOME_UNKNOWN` 只在 manifest、Provider request digest、Provider/configuration、isolation receipt、qualification 与 eligibility
  全部重验通过时传播为 `LIVE_INTEGRATION_HELD`，消息明确 Provider outcome unknown、当前问题关闭且 zero retry；真实 binding drift 仍保持
  `QUALIFICATION_INVALID`；
- Strategy/Prompt/Question Understanding schema identity 分别升级为 `@10/@20/@4`，Question Understanding Domain identity 升级为
  `@5`。current System Contract、Slice/Manifest/Verification 与确定性测试在同一变更中同步；新 clean candidate 与 fresh 三题 live
  仍须重新执行，旧三题全部只作为失败诊断证据。
