---
id: FINDING-010-212
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [FINDING-010-211, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_routing.py, tests/test_conversational_engineering_tools.py, tests/test_engineering_chat_browser.py, tests/test_engineering_chat_candidate.py, tests/test_engineering_chat_alpha_cli.py, tests/test_engineering_chat_provider_launcher.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_qa_browser.py, tests/test_iteration_010_mvp_value_gate.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: require-changed-review-rewrite-and-response-kind-aware-contract-repair
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-212：run-089 暴露无效输出原样修复、重复 Source action 与 Limitation 审核摆动

## Observation and execution evidence

`FINDING-010-211` candidate 已提交为 product commit/tree
`baace68dfe699d7e9a55bd35e086cac2fbaff5a0 / fa1f044258eec7c4d1d8b979b8ce536251c1a980`。DeepSeek 官方 pricing 页面在
`2026-08-30T15:13:11.416Z` 由 in-app Browser fresh 可见检查；capture 文件 SHA-256 为
`8a7c9ddf903d4b055f69269f8eb200ea3a6aae9e6271f11f21fb86a0d74b1577`，可见文本 digest 为
`sha256:9c9dd4d22764599ade403c0ba6cd95abcb947810d5230ee95cb96a56a62d7668`，周六全天闲时成立。

唯一 validated launcher 完成 `run-089-mvp-experience` 的 4 个 Conversation、5 个冻结 Turn；terminal 状态为
`STOPPED_AFTER_DISPATCH`，receipt digest 为
`sha256:22bb569db7b694feef5927e7903510b48ed3ad486a5d5871d76f89e07b6adef0`。Ark 创建 4 个 call，全部完成 TLS、credential 与 HTTP，均得到
sealed `429 / AccountQuotaExceeded` 并形成 trusted unavailable。DeepSeek 在 first real preflight 取得周末
`ALLOWED_OFF_PEAK` active receipt `sha256:d0d16f8c9c30b69e585bc07caff6d1be3854d03b8047ca979b73c5b2df50303b`，创建 28 个
call：27 个完成，1 个在 request bytes 已发出后发生 `REMOTE_DISCONNECTED / PROVIDER_OUTCOME_UNKNOWN`。总 dispatch 为 32，Provider
retry、人工重复审批和 Production Activation 均为 0。

turn-scope/session/pricing-capture/launch/terminal/Ark DB/DeepSeek DB 文件 SHA-256 分别为：

- `49441e26f4e6f04d88e79ad633d04f83a99b0dcba1904168ffad8bf2b10ce953`
- `c7279816edd1003f71c0d1aeee0ead3ad5b5434cf94758115da208a7bed62a5f`
- `8a7c9ddf903d4b055f69269f8eb200ea3a6aae9e6271f11f21fb86a0d74b1577`
- `d819dfb71be1a6864a2885d7c3bb350773c0185b4dd8070e03acc210654599f5`
- `3863d96a050499a105d328e83b9024095c14a4c0ebef2896f994ad92d2be1b71`
- `879009f92433231792b30731b1d114907c4fec38b8d7edb9520cafb4f3be6aab`
- `bb683128c77438bf2e491f457bad1b4ba8820e96692c695ddca52c14b9d85adf`

逐题 dispatch 为 `11/2/5/0/14`。Q1 以 `REVIEWER_MODEL_CALL_REJECTED / PROVIDER_OUTPUT_INVALID`、Q2 以
`AGENT_MODEL_OUTCOME_UNKNOWN`、Q3 以 `AGENT_MODEL_CALL_REJECTED / PROVIDER_OUTPUT_INVALID`、Q5 以
`AGENT_REVIEW_LIMIT_REACHED / MODEL_REVIEW_REJECTED` 失败；Q4 fresh Conversation 继续以
`APPLICATION_INPUT_CLARIFICATION`、零 dispatch 正确隔离。整体仍为质量 FAIL，不能称 MVP。

## Exact first divergences

1. Q1 的 Draft 已把 HTTP 入口、旧关系删除、新关系写入与 cache invalidation 的 source-visible local order 分开，并把 transaction/consumer
   timing 留在 Boundary。focused Reviewer 对四个 caller challenge 全部返回 `WITHIN_CALLER_EVIDENCE`，却同时把 Claim 1 标为 DEFECT 并返回
   “exceeds caller evidence” Finding。`@16` decoder 正确以 exact closure 拒绝；same-profile repair 收到
   `focused Reviewer DEFECT Claim indices must equal ...` 后仍逐字返回同一 4730-char contradictory object。旧 diagnostic 没有投影实际
   DEFECT/EXCEEDS 集合或两个闭合分支，原样返回也没有明确成为 repair 禁止项。
2. Q3 先取得 World Model `BOUNDARY`，再执行 `SOURCE_SEARCH(insertBatch)`；Search 56 个文件、0 match，并以
   `SOURCE_SEARCH_FILE_LIMIT_REACHED / PARTIAL / truncated=true` 形成第二个 reportable Boundary。此时 completion policy 已允许
   `CLARIFICATION/LIMITATION`、Tool action 非必需且仍有 6 个 action slot；下一 Primary 仍复制已列入 `forbidden_exact_values` 的
   `insertBatch`，same-profile repair 收到 “repeated a forbidden current-Turn Source query” 后又复制同一 action。正确收敛不是按该词特判，而是
   对任何 forbidden exact action：有新的 sealed source-native literal 才换合法 action，否则用现有 Boundary 返回纯 Limitation。
3. Q5 的 4 次 comprehensive Review 依次要求 exact-revision、修改接口方法清单、重新解释 Search/Profile diagnostic、再为 Limitation 添加
   Claim；其中还错误声称 Draft 未绑定实际已存在的三个 Boundary IDs，并把 Search hit/interface declaration 当成已关闭实现与 remote
   semantics 的证据。Primary 第一次与最后一次 rewrite 分别原样返回 exact rejected Draft，中间两次只在相邻接口 inventory 与 acquisition
   diagnostic 间替换，未收敛到纯 material Boundary。旧 prompt 虽写有 `LIMITATION claims=[]` 与删除 diagnostic 的规则，但 Application 没有
   机械拒绝 exact unchanged replacement，Reviewer 末端检查也未把 response-kind 分支置于足够明确的闭合位置。
4. Q2 的 first DeepSeek call 发生真实 post-dispatch unknown，Application 没有 retry、没有误回退或交付，行为符合既有契约；它不是本 Finding
   的代码变更目标。

## Decision and disposition

这是 `system-contract / systemic` Finding，不按 mall、问题、Provider、语言、类名、方法名、query literal、revision 或 Finding 文本特判。

1. active same-Package rewrite 的 replacement Draft 必须至少改变一个真实 Draft 字段并解决 Finding。若 response kind、content、ordered
   Claims/bindings 与 Boundary IDs 全部等于 exact rejected Draft，decoder 以 `STRUCTURED_OUTPUT_INVALID` 失败关闭；只改 Work State 不能冒充
   rewrite。Application 不据 Finding 文本静默改写答案。
2. `format_repair_policy` 必须明确 `prior_output_exact_repeat_forbidden`，并为 closed-contract failure 投影不授予事实/Tool authority 的 typed
   convergence directive。重复 Source query 的 directive 只能选择新 sealed legal action 或当前允许的 pure-boundary Draft；focused closure
   directive 必须重读 exact Claim/challenge 并一起重建 verdict、disposition、finding code 与 Finding。validator diagnostic 还投影 actual
   DEFECT/EXCEEDS index set，不能回显 untrusted Finding message 作为 trusted instruction。
3. LIMITATION 的 Claim inventory 始终为空。Reviewer 不得要求向 LIMITATION 添加 Claim、exact-answer detail、interface/search inventory；pure、
   relevant、正确绑定的 Limitation 不因用户原本要求 Answer/full chain/exact Source refs而产生虚构 completeness Finding。若正文含无支持或无关的
   affirmative acquisition diagnostic，修复是删除/收窄到纯 material unresolved boundary，不是换一份清单。Opaque Boundary ID 已在 exact
   array 中时不得声称缺失；Search/interface evidence 不等于 implementation、remote effect 或 consumer-visible evidence。
4. 协议升级为 `conversational-engineering-agent@17 / conversational-engineering-agent-no-tools-prompt@17 /
   ENGINEERING_AGENT_PRIMARY_INPUT@17 / ENGINEERING_AGENT_REVIEW_INPUT@10 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@12`；output schemas 保持
   `engineering-agent-work-state-proposal@2 / engineering-agent-independent-review-proposal@6`。route、15-call Turn authority、4-Review 上限、
   Tool/Source fuse、repair 上限、retry、fallback eligibility、接收方和 Production 边界均不变。直接与相邻
   Chat/route/launcher/Browser 共 147 项定向测试 PASS、外调 0；fresh run-090 仍须验证真实 Answer/Review，run-089 不追认为质量或 MVP PASS。

该变化细化既有 Application/Primary/Reviewer owner，不改变组件职责，故不需要新 ADR。本 Finding 与同步后的
`SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 是 current system write-back。
