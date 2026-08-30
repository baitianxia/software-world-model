---
id: FINDING-010-208
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [FINDING-010-206, FINDING-010-207, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_routing.py, tests/test_conversational_engineering_tools.py, tests/test_engineering_chat_browser.py, tests/test_engineering_chat_candidate.py, tests/test_engineering_chat_alpha_cli.py, tests/test_engineering_chat_provider_launcher.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_qa_browser.py, tests/test_iteration_010_mvp_value_gate.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: close-nested-output-branches-and-separate-boundary-binding-from-text-disclosure
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-208：run-085 暴露 nested closed-output 与 Boundary binding/disclosure 缺口

## Observation and execution evidence

`FINDING-010-206/207` candidate 已提交为 product commit/tree
`87aad746af791f3f65515aae646f8bb9f2e07f05 / 64e1b795a1febd6ca3f419fcc23e1995352a8fba`。DeepSeek 官方 pricing 页面在
`2026-08-30T11:42:32.104Z` 由 in-app Browser fresh 可见检查；capture 文件 SHA-256 为
`2618ea36683cf70559a1324c0068df34c7ea50b40574ad6a182fdbb95a15d102`，可见文本 digest 为
`sha256:9c9dd4d22764599ade403c0ba6cd95abcb947810d5230ee95cb96a56a62d7668`，仍明确周末全天闲时。

唯一 validated launcher 完成 `run-085-mvp-experience` 的 4 个 Conversation、5 个冻结 Turn；terminal 状态为
`STOPPED_AFTER_DISPATCH`，receipt digest 为
`sha256:29acf29927979766a9b088ebd8f4a343341e465df207e9137b32a2f2bb56bdc4`。Ark 共完成 52 次真实 HTTP dispatch：51 次
`COMPLETED`、1 次在 bytes 已发送后发生 `REMOTE_DISCONNECTED / PROVIDER_OUTCOME_UNKNOWN`；另一个 Q5 proposal 在 Provider boundary
前因 15 次 Turn authority 耗尽而正确拒绝。Provider retry、人工重复审批和 Production Activation 均为 0。没有出现可触发 fallback 的 Ark
HTTP 前 trusted unavailable，故 DeepSeek dispatch/TLS/credential/HTTP 保持 `0/0/0/0` 正确；Q2 的 post-dispatch unknown 不能改路重发。

turn-scope/session/pricing-capture/launch/terminal/Ark DB/DeepSeek DB 文件 SHA-256 分别为：

- `a4b8be1fcfd6980c1f6ddf5a91913465f5ec10bb5d08d050e1a33ee7838ad470`
- `3cddf500b3c611ca9f0836cd1da79c26285b0759aa65a549eac7f3760a18c2ea`
- `2618ea36683cf70559a1324c0068df34c7ea50b40574ad6a182fdbb95a15d102`
- `5c30c4e7e1b063a0178b4f96662ccda598aaf78ceed4b2d79fe94b79b67f2bf9`
- `54333919372499de85caa88cdcffb5a1ea0b3ee0366dcfd6fc4a490b443cc29f`
- `61ca51df61cb22d2cdc7ef78010b0a92dba3d830aa7c1963ca837863a82eafe1`
- `0f539b3df4c6127e4b2a90005b287ed8e49b3701f314994f6d1ce8e79dd6672c`

逐题 dispatch 为 `12/12/13/0/15`。Q4 fresh Conversation 继续以
`APPLICATION_INPUT_CLARIFICATION` 零 dispatch 正确隔离；Q1 在 focused Reviewer shape repair 后失败，Q2 在最终 Reviewer request
发出后 outcome unknown，Q3 在 Primary repair 后失败，Q5 在 focused rewrite 前耗尽原有 15 次 authority。整体仍为质量 FAIL，不能称 MVP。

## Exact first divergences

1. final preflight 只枚举顶层字段，没有把 nested closed object 的 exact field names 与当前有效 action/draft branch 直接投影。Q1 Reviewer
   因而使用 `boundary_challenge_id` 而非 schema 要求的 `challenge_id`；repair 又改变了既有合法 decision/finding 值，机械守恒正确拒绝。
2. Q3 focused Reviewer 把结构化 `draft.boundary_observation_ids` binding 当成向用户披露了 Boundary 的全部 raw metadata，要求 Primary 删除所有
   binding。Primary 随后先产生没有 Boundary binding 的 `LIMITATION`，再产生 `phase=RESPONSE_READY` 的 action。实际用户披露只来自
   `draft.content`；结构化 reference 是 evidence binding，不自动披露未写入正文的 inventory、audit 或 provenance 片段。但
   `LIMITATION` 仍必须绑定至少一个与用户请求相关的可报告 Boundary，不能用“未自动披露”取消证据边界。
3. Primary preflight 没有显式给出 action argument item 只能是 exact `{name,value}`，也没有把 completion policy 的
   `tool_action_required` 编译成排他的 ACTION/DRAFT/phase branch。Q5 因而先提交直接 keyed `locator_reference`，后又在需要 action 时提交 Draft，
   消耗了本来可用于真实调查与 rewrite 的既有 slots。
4. 模型产生的 schema-shaped object 进入 typed domain constructor 后，`INVALID_ARGUMENT` 直接泄漏为 Application argument error。该输入仍是
   untrusted Provider output，应统一报告 `STRUCTURED_OUTPUT_INVALID`；Application 自身 authority/invariant 错误不能被该归一化掩盖。

## Decision and disposition

这是 `system-contract / systemic` Finding，不按题面、工程、Provider、类名、具体 ID 或输出字符串特判。

1. `ENGINEERING_AGENT_OUTPUT_PREFLIGHT@8` 必须递归投影 closed nested object/array-item 的 exact required fields，并明确 additional fields
   forbidden。Primary action argument item 固定为 `{name,value}`；Reviewer boundary assessment 固定使用 `challenge_id`。
2. Primary preflight 从 trusted completion policy 编译唯一有效 branch：action 只能处于非终态且 draft 为 null；Draft 只能处于
   `RESPONSE_READY` 且 action 为 null。`ANSWER` 至少有一个 Claim；`CLARIFICATION` 无 Claim/Boundary；`LIMITATION` 无 Claim 且至少绑定一个
   reportable Boundary。模型不能用 output 自己选择 branch。
3. structured Boundary binding 与用户可见文本 disclosure 分离。materiality 逐 `draft.content` 中实际片段判断；未出现在正文的 raw metadata
   不视为已披露。删除 audit-only prose 时，仍须保留或替换支撑物质 Limitation 的 Boundary binding。
4. shape repair 必须先精确恢复 `existing_allowed_field_copy_projection` 中既有合法值，再补 missing field；不得以 shape 修复进行语义协调。
   model-authored typed constructor 的 `INVALID_ARGUMENT` 归一化为 `STRUCTURED_OUTPUT_INVALID`，其他内部 DomainError 原样传播。
5. 协议升级为 `conversational-engineering-agent@13 / conversational-engineering-agent-no-tools-prompt@13 /
   ENGINEERING_AGENT_PRIMARY_INPUT@13 / ENGINEERING_AGENT_REVIEW_INPUT@7 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@8`；output schemas 保持
   `engineering-agent-work-state-proposal@2 / engineering-agent-independent-review-proposal@6`。route、15-call Turn authority、repair 上限、
   Tool/Source fuse、retry、fallback eligibility、接收方和 Production 边界均不变。直接与相邻 Chat/route/launcher/Browser 共 144 项定向测试
   PASS、外调 0；fresh run-086 仍须验证真实 Answer/Review，run-085 不追认为质量或 MVP PASS。

该变化细化既有 Application/Reviewer owner，不改变组件职责，故不需要新 ADR。本 Finding 与同步后的
`SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 是 current system write-back。
