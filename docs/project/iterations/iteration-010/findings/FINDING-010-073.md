---
id: FINDING-010-073
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, quality, security]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-070, FINDING-010-071, FINDING-010-072, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-QUALITY-SECURITY]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: bind-verification-limitations-to-current-gap-and-terminal-review-boundary
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-073：Verification limitation 不能借用无关 predecessor boundary，已穷尽 gap 不得被重复请求

## Observation and evidence

clean product commit `32a00a3a4056948719153f23c365e0aff0431343` / tree
`89436febd4b2207b99003db3cc47e03b6ea1fa84` 的 run-026 使用 exact mall
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`。fresh DeepSeek Conformance 2/2 PASS，result digest
`sha256:d365db93bc0db9653c118176607e86d97c45f63d45417be76f78b6aa42e85b93`；同一 Browser listener 的三题分别发生
8/12/14 次 dispatch，总计 34，retry/switch 均为 0。66,000-byte UTF-8 输入在 Provider 前拒绝，调用数保持 34；Browser
warning/error 为空，SQLite/launch/session/WAL/SHM/terminal 文件均为 `0600`，Production Activation 为 `NOT_EXECUTED`。terminal
receipt document digest 为 `sha256:cfa932040fdfe9a91a68ce4861b39b01357f94fadccf6302d2549b623632c0ea`。

Q1 `engineering_result_32b52798be46f22da3b1f85ae37b36e5` 为 `APPROVED`，答案的登录入口、密码校验、启用状态、当前请求
SecurityContext、JWT 与登录日志均可由三个显示 Citation 的完整源码核对。Q2 首轮 Review 形成两个外部响应映射 gap；单 gap
Verification 对 `check-2` 诚实返回 `UNKNOWN`，但其三个 limitation observations 错把 predecessor Package 中本来描述数据库、JWT
密钥和端口的 `cognition-unknown-1/2/3` 当作 CommonResult 缺证边界。新 Answer 反而引用了当前 Verification Request 形成的 gap
boundary，Application 的逐 observation/evidence closure 因此以
`answer claim does not cite every Package entry supporting its material observation` 正确失败关闭。SQLite raw role output、successor
Package input和独立 SQL join 精确证明缺失项是三个 unrelated predecessor boundary entry，不是 Provider 余额、网络、retry 或 trusted
merge 丢失。

Q3 `engineering_result_86db2ff5614f6a49d0b2dc81b1ffeaa5` 已把两个未授权 handler implementation 诚实降为 limitation，但第二次
Review 仍对同一已受控调查并穷尽的 `check-4` gap 再次请求完全相同的实现，最终触发
`VERIFICATION_INVESTIGATION_FUSE_EXHAUSTED`。这说明“单 gap delta + stable merge”仍缺两条通用闭包：Verification 非支持观察的
boundary 必须绑定本次 gap；经 bounded Verification 形成的真实 UNKNOWN 本身可以完成 material checklist 的 evidence-boundary 回答，
Reviewer 不得把“缺证仍然缺证”当作再次调查理由。另一个 unsupported detail 若只是 Draft 自行扩张，必须基于当前 Package 删除或收窄，
不能借 accepted checklist 的宽泛措辞扩大调查。

## Decision and disposition

- Verification 输入的 `admissible_boundary_references` 现在从完整 eligibility 中机械移除 predecessor Package 的全部 boundary source
  references，只保留当前 Verification Request 及本 attempt 新产生的 search/partial/rejection/gap/receipt boundaries；肯定 support 仍可
  复用 predecessor Package 已密封的 admissible support。
- 角色输入显式投影唯一 `verification_gap_boundary_reference`。每个 `UNKNOWN / CONFLICT / FAILED` child observation 都必须逐条保留
  该 exact reference；Application 在 Provider 后独立重验，不能以另一个 cognition unknown、旧 search candidate 或旧 gap 冒充当前缺口。
- Package 将普通 Investigation `GAP` 与 `VERIFICATION_REQUEST` 产生的 typed `VERIFICATION_GAP` 分开密封。Review 输入从当前
  Package 可信投影 `verified_gap_outcomes`：只有 non-supported disposition 真正保留 `VERIFICATION_GAP` 时才进入。Draft
  诚实陈述该 limitation 且不暗示缺失的肯定结果时，material completeness 可以 PASS，Reviewer 不得再次请求同一缺证；其他 supported
  本地机制和不同 checklist gap 仍须完整审核。
- Reviewer 规则进一步明确 deletion test：外部 status/body/error/handler output 只有在 original question 或 accepted checklist 字面要求
  时才可补证；Draft 自行增加的非必要下游结果使用 current-Package rewrite 删除或收窄。

Strategy/Prompt identity 分别升级为 `engineering-qa-adaptive-investigation-local-contract@19` 和
`engineering-qa-adaptive-investigation-prompt@29`；Provider output schema 未改变。三模块新增回归后 76/76 PASS。扩展 Engineering QA、docs、
oracle、full suite 与下一 clean/fresh live 由后续 verification Finding 单独记录；run-026 永久保持 Q1 PASS、Q2/Q3 FAIL，不追认三题 Gate。
