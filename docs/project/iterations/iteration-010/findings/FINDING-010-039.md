---
id: FINDING-010-039
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai-infrastructure, application, operations, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-038]
code: [src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_model_source.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: preserve-exact-provider-failure-through-policy-and-terminal-audit
target: src/software_world_model/ai_infrastructure/engineering_question_model_source.py
---

# FINDING-010-039：Provider HTTP 失败不能被重标为授权绑定漂移或结果未知

## Observation

clean candidate `c7e32b51e5ffbc6e3b3e706d3a156185262c699b` 与 current DeepSeek Conformance
`sha256:8802280e16bc3effe6d76ce5c0dc925431758138c20e5c0c3945a42b53a5496c` 的持续 Alpha 会话先以 7 次 role
dispatch 回答原现场题。Result `engineering_result_c33bb762f3fdf9b689fefea340d49998` 与独立 Review 均为 `APPROVED`；调查实际读取
固定 mall revision 的 `UmsAdminController` 和 `UmsAdminServiceImpl`，Package、Answer 和 Reviewer 都覆盖了凭据提交、用户/密码/禁用状态
校验、`SecurityContext`、JWT、失败返回及 `loginLogMapper.insert` 登录审计副作用。Gateway 主文件、live WAL/SHM 均为 `0600`。

同一会话随后提交两道不同问题。二者的首个 `QUESTION_UNDERSTANDING` dispatch 都在 Gateway SQLite 中精确终止为
`FAILED / PROVIDER_HTTP_ERROR`，没有 Provider response identity；每题只调用一次，retry/switch 均为 0，listener 继续接受下一题。但是页面把
两次失败显示为 `Engineering QA model Result is outside the exact authorized Provider binding`，terminal receipt 又把它们写成
`OUTCOME_UNKNOWN / QUALIFICATION_INVALID` 且丢失 `model_call_id`。实际 SQLite 调用根与展示/terminal audit 因而矛盾。

会话还通过真实页面提交了 22,000 个汉字的超限 JSON：本地 ingress 在 Provider 前返回
`request body is empty or exceeds the local preview limit`，按钮恢复、health 仍为 `READY`，调用根保持 9 个不变。最终 terminal receipt
`sha256:c58ebfadf26ed4732567284ac83adabf9740c62aaeef8d9056eaafb8ade3939f` 为 3 个 accepted questions、9 次 dispatch、retry 0、
switch 0、Production Activation `NOT_EXECUTED`。该会话证明原题修复与受控失败隔离成立，但两道后续题没有形成答案，不能取得持续三题
或答案质量 PASS。

## Root cause

- `_require_eligible_result` 把所有非 `COMPLETED` Result 与真正的 Manifest/Provider/qualification identity drift 放在同一个布尔拒绝分支，
  因而丢失 Gateway 已持久化的 terminal failure code；
- production policy wrapper 在返回 Result 给 model source 前执行相同检查并直接抛出 `DomainError`。外层 dispatch audit 因拿不到已密封的
  `ModelGatewayResult`，只能把已知失败错误降格记录为 outcome unknown；
- 这不是 DeepSeek、mall、具体问题、关键词或 fixture 特例，而是所有 exact Provider terminal failure 的系统性错误分类与审计保真缺口。

## Decision and disposition

- 只有在 failed Result 的 Manifest、Provider/model/configuration、Isolation Receipt、qualification reference、eligibility digest、call identity
  和空 response 形状全部与当前调用精确一致时，才把已知 `ErrorCode` 原样传播；未知 terminal failure code 仍映射为
  `LIVE_INTEGRATION_HELD`。任一 identity 不一致继续返回 `QUALIFICATION_INVALID`；
- policy wrapper 继续先拒绝失败 Result，但用内部 rejection envelope 把已密封 Result 交给唯一外层 model source 做审计。model source 记录
  exact call ID/state 后重新抛出原 `DomainError`，不会把失败 output 交给角色或用户；
- 现有 Engineering QA Contract 已要求真实失败、单题关闭、no retry 和 terminal audit，因此本 Finding 以代码与测试处置，不重定义 System
  语义。旧 candidate/session 永久保持部分成功/后续失败；新 clean candidate、current Conformance 和持续三题 run 仍须重做。
