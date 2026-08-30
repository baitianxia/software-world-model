---
id: FINDING-010-206
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [FINDING-010-205, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_routing.py, tests/test_conversational_engineering_tools.py, tests/test_engineering_chat_browser.py, tests/test_engineering_chat_candidate.py, tests/test_engineering_chat_alpha_cli.py, tests/test_engineering_chat_provider_launcher.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_qa_browser.py, tests/test_iteration_010_mvp_value_gate.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: match-real-search-read-modalities-and-close-review-output-domains
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-206：run-084 暴露真实 Search modality 漏配与 Reviewer closed-output 缺口

## Observation and execution evidence

`FINDING-010-205` candidate 已提交为 product commit/tree
`88ac7da2796be3d2bed5f67c60c6e2cbfcfb1328 / 4348e24843ac1da07fbeb3a9f4f5cd5006fe08cd`。DeepSeek 官方 pricing 页面在
`2026-08-30T10:43:39.130Z` 由 in-app Browser fresh 可见检查；capture 文件 SHA-256 为
`b912d59e6c0f10fc7de5c40cd369a5788eb995c844f26818222909ac16e4ef15`，可见文本 digest 为
`sha256:9c9dd4d22764599ade403c0ba6cd95abcb947810d5230ee95cb96a56a62d7668`，仍明确周末全天闲时。

唯一 validated launcher 完成 `run-084-mvp-experience` 的 4 个 Conversation、5 个冻结 Turn；terminal 状态为
`STOPPED_AFTER_DISPATCH`，receipt digest 为
`sha256:e1ff2882aa8af33bdc4a3838e41c6a42440190815f3fdf7e21a5718fd72a085c`。Ark 共创建 44 个 model call，其中 43 个取得完整
HTTP output，另 1 个在 HTTP 前发生 typed TLS unavailable；HTTP bytes 已发送后的 unknown、Provider retry、人工重复审批和 Production
Activation 均为 0。DeepSeek dispatch 为 0；其独立准入生命周期偏差由 `FINDING-010-207` 处置。

turn-scope/session/pricing-capture/launch/terminal/Ark DB/DeepSeek DB 文件 SHA-256 分别为：

- `921cef44fe6591c4ad998adab555a87d6572f029e0d8bd56a894bb12a4fff05a`
- `e2b5d4c08c4c5e7422f1bfb76c2c2ecb380198cf111086e5c80ae9b4d810e56f`
- `b912d59e6c0f10fc7de5c40cd369a5788eb995c844f26818222909ac16e4ef15`
- `c2de6460b09112af34b49a1d0aaa9031c70058d572dd3dd9fdec623ffd3b49d5`
- `13519d402495210e5c320753e47deccfc4dde19ccd37289bc8c1fc1ed1524db2`
- `5c984a957aefd731aa0eabeb12877f7fb3cf18205eee4b750ffc1c4eeb1b141a`
- `0f539b3df4c6127e4b2a90005b287ed8e49b3701f314994f6d1ce8e79dd6672c`

逐题结果仍为质量 FAIL：Q1 角色重分配、Q2 普通订单、Q3 同 Conversation 追问和 Q5 `mall-search` 均失败；Q4 fresh Conversation
继续以 `APPLICATION_INPUT_CLARIFICATION`、Provider dispatch 0 正确隔离。Q1/Q5 的 focused Reviewer 实际识别了 resolved Search，但其
disposition 被 Application 的错误 trusted kind 拒绝；Q2 的 repair 则重复输出尾随换行，触发 `draft content must be non-empty text`。

## Exact first divergences

1. 真实 Source Search retrieval item 的 modality 是 `LITERAL_TEXT_SEARCH_HIT`；只有后续 full Source Read item 才是
   `EXACT_STATIC_SOURCE_TEXT / coverage_complete=true`。`FINDING-010-205` 首版 resource matcher 错误要求 Search/Read 两侧都为
   `EXACT_STATIC_SOURCE_TEXT`，因此真实同资源永远不能得到 `RESOLVED_ACQUISITION`。原测试 fixture 也使用了不真实的 Search modality，形成
   false PASS。Q1/Q5 被错误投影成 `BOUNDARY_MATERIALITY`，Reviewer 合理返回的 `RESOLVED_AUDIT_ONLY` 随后被 closed decoder 拒绝。
2. Review input 只给 `kind` 和通用 prose，没有直接投影由 trusted kind 与 Draft reference flag 决定的 closed disposition domain；repair
   需要从长 Boundary 文本反推 Application-owned分类。旧 decoder 的通用错误也没有给出 exact assessment index、challenge ID 和允许值。
3. Primary/Reviewer schema 已机械禁止 string 首尾 whitespace，但 Prompt/final preflight 没有显式呈现。Q2 Primary repair 保留
   `draft.content` 末尾换行，再次触发同一 `CLOSED_OUTPUT_CONTRACT`；Application 正确没有 trim，但模型缺少同形 closed 提示。
4. Q1 仍把 global `559/866` inventory metric 与 material gap 一起披露。focused input 需要明确 materiality 按每个 disclosed fragment
   计算，material gap 不授权相邻 global metric；这仍是通用 relevance contract，不按数字或题面删除。

## Decision and disposition

这是 `system-contract / systemic` Finding，不按工程、问题、语言、数字、Source path、Provider/model、fixture 或具体输出特判。

1. resolved-acquisition matcher 分开验证两种真实 operation/modality：Search 必须是 `SOURCE_SEARCH + LITERAL_TEXT_SEARCH_HIT`，Read 必须是
   later `SOURCE_READ + EXACT_STATIC_SOURCE_TEXT + coverage_complete=true`；两侧均须绑定各自 authorized Citation。opaque reference exact
   equality 也只接受 Search retrieval item 实际签发的 reference；canonical path 仍只删除规范 `:Lstart[-end]`，不做 basename/fuzzy 匹配。
2. 每个 relevance challenge 直接投影 `allowed_exact_dispositions`：Draft 已绑定时为 material + kind-specific audit-only，未绑定时为
   not-disclosed + kind-specific audit-only。Reviewer 只能复制其中一项；decoder 返回 exact index/challenge/domain 并从 trusted challenge
   重算，不从 Provider prose接受 kind 改写。
3. Primary/Reviewer Prompt 与 `ENGINEERING_AGENT_OUTPUT_PREFLIGHT@7` 显式要求所有 authored string non-empty 且首尾无 whitespace，尤其
   `draft.content` 最后字符不能是空格或换行。Application 保持原值验证，不 trim、不生成或静默修复内容。
4. materiality challenge 显式要求逐 disclosed fragment 判断；混合 material/non-material disclosure 必须得到 audit-only Finding，material
   gap 不能带入 adjacent global metric。
5. 协议升级为 `conversational-engineering-agent@12 / conversational-engineering-agent-no-tools-prompt@12 /
   ENGINEERING_AGENT_PRIMARY_INPUT@12 / ENGINEERING_AGENT_REVIEW_INPUT@6 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@7 /
   engineering-agent-work-state-proposal@2 / engineering-agent-independent-review-proposal@6`。route、15-call Turn authority、repair 上限、Tool/Source
   fuse、retry、接收方和 Production 边界均不变；直接、相邻、route、launcher 和 Browser 边界共 144 项定向测试 PASS、外调 0。fresh run-085
   仍须验证真实 Answer/Review，run-084 不追认为质量或 MVP PASS。

该变化只细化现有 Application/Reviewer owner，不改变组件职责，故不需要新 ADR。本 Finding 与同步后的
`SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 是 current system write-back。
