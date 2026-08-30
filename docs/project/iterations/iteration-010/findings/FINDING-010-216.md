---
id: FINDING-010-216
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [FINDING-010-215, ITER-010-PDR-007, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: normalize-only-inline-code-presentation-for-verbatim-draft-fragments
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-216：run-093 暴露 exact Draft fragment 被 Markdown inline-code 展示差异误拒

## Observation and execution evidence

`FINDING-010-215` candidate 已提交为 product commit/tree
`f0087e5d95930f22ecd9e2b2dc16037120941d7c / f480d1e61b6fbb9a8de976b72c4014ecec1c396a`。唯一 validated launcher
完成 `run-093-mvp-experience` 的 4 个隔离 Conversation、5 个冻结 Turn，terminal 状态为 `STOPPED_AFTER_DISPATCH`，terminal/runtime/
public-source authority digest 分别为
`sha256:36d14202da3e0476e41357c1a3d0e8643cfaecbb2956268657d53c3060caddcc`、
`sha256:453d68086d7f160b830ffe64652d95356a440dee2953260468bd90531a28d9df`、
`sha256:b7cc48049887e9e2c7fdf08a399f9a1647c3a3598735c118b9e259e51f2fa7c2`。

Ark 19 个 HTTP dispatch 中 16 个完成，3 个 sealed `429 / AccountQuotaExceeded` 在
`18:16:54 / 18:18:24 / 18:20:04Z` 形成 trusted unavailable evidence；第一次 429 后 DeepSeek 于
`18:16:56Z` 按 `ALLOWED_OFF_PEAK` 自动激活，28 个 dispatch 全部完成。总 dispatch `47`，retry、人工审批和 Production Activation 均为 0。
这证明 fallback 已按 standing authority 工作；Q1/Q2 的失败不是因为 DeepSeek 未获授权。Q3 为
`SUCCEEDED / REVIEWED_LIMITATION`，Q4 为零 dispatch Clarification，Q5 为 `SUCCEEDED / ACCEPTED`，但整体答案质量仍 FAIL。

turn-scope/pricing-capture/session/launch/terminal/Ark DB/DeepSeek DB 文件 SHA-256 分别为：

- `5e88f91c81ccbb8011f9d70521ed8438385dd4579af7dffc497f17e8526328b6`
- `59e5fa0b64e9a759bbcccbe3166118e47f44614674800655651405399137b579`
- `ff1124d6fca8303d1beef397cf7f09d6cfd92b41cd81a9c25a99b8b396636b48`
- `5659953d1e813e5527f63da2e2258714e26466d8565a1fab7133dae6c2d0a6e7`
- `1482643d67360dd32e514435704d0b95c20ba06974201db94a76df8b7debf933`
- `c5fe24b92e602795135ae25be66e96f9a44bd73171c8c366e92c6fe8389764fd`
- `2599fa225a554da56ea21d6b5ba27db73c9e7760e961907dec32c7b357e12592`

## Exact first divergence

Q1 call 10 的 focused Reviewer 语义上返回 `APPROVED`，并给出 5 个 `draft_disclosed_fragments`。前 3 个是 Draft 的 byte-exact
substring；后 2 个只省略了 Draft 围绕 Java identifier 的 Markdown inline backticks：一项包含
`getResourceList / loadUserByUsername / UserDetails`，另一项包含 `delResourceList / UmsAdminCacheService`。其余文字、顺序和标点均一致。

Application 的旧 matcher 直接执行 `fragment in draft.content`，因此把无语义变化的展示差异判为
`STRUCTURED_OUTPUT_INVALID / REVIEWER_MODEL_CALL_REJECTED`。这不是 Reviewer Finding、证据不足、Provider unavailable 或 authority
耗尽，而是 exact disclosure contract 把 Markdown presentation delimiter 错当成语义正文。若改为模糊匹配或普遍删除 Markdown 标记，又会放行
paraphrase、虚构内容和有意义的标点变化。

## Decision and disposition

这是 `system-contract / systemic` Finding，不按题号、模型、语言、identifier 或 fragment 文本特判。

1. `draft_disclosed_fragments` 继续要求 verbatim Draft substring；唯一允许的 presentation normalization 是在 fragment 与 Draft 两侧删除
   U+0060 backtick delimiter bytes。其他字符、文字、标点和顺序必须完全一致，任何 paraphrase 或虚构内容仍失败关闭。
2. Application 在 Assessment construction、model decode、Review seal 与 Delivery closure 使用同一 normalization；normalized-empty fragment
   非法，normalized duplicate 非法，因此 `` `name` `` 与 `name` 不能作为两个独立 disclosure surface。
3. 协议升级为 `conversational-engineering-agent@21 / conversational-engineering-agent-no-tools-prompt@21 /
   ENGINEERING_AGENT_PRIMARY_INPUT@21 / ENGINEERING_AGENT_REVIEW_INPUT@13 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@16 /
   engineering-agent-independent-review-proposal@8`；Assessment/Review identity 升为 `@4/@3`。两次 repair、15-call Turn authority、4-Review、
   Tool/Source fuse、route、fallback、freshness、retry、接收方和 Production 边界均不变。
4. regression 覆盖 backtick-only 差异通过、改变一个语义词仍拒绝、以及 normalized duplicate 拒绝。与 Source 修复共同执行的六模块
   `154/154` 定向测试与相邻十五模块 `229/229` PASS；fresh run-094 才能验证真实模型链，run-093 不追认为质量或 MVP PASS。

该变化细化既有 Reviewer/Application owner，不改变组件职责，故不需要新 ADR。本 Finding 与同步后的
`SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 是 current system write-back。
