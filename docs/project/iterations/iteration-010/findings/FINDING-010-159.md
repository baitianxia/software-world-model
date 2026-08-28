---
id: FINDING-010-159
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [FINDING-010-155, FINDING-010-156, FINDING-010-158, ITER-010-PDR-010]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py, src/software_world_model/ai_infrastructure/openai_responses_adapter.py]
tests: [tests/test_openai_responses_adapter.py, tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_routing.py, tests/test_engineering_chat_provider_launcher.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_chat_alpha_cli.py, tests/test_volcengine_ark_chat_adapter.py, tests/test_deepseek_chat_adapter.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: bind-trusted-closed-schema-diagnostics-into-one-same-profile-format-repair
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-159：格式修复缺少可信字段级诊断，单一工具 action 连续遗漏 operation

## Observation

availability Owner 修复后的 fresh `run-049` 没有等待 DeepSeek：listener 在 fallback admission=`DENIED_PRICING_CHECK` 时正常启动，第一 Turn
只执行 Ark。7 个 Ark call 的 TLS、credential resolution 和 HTTP dispatch 全部成功，actual model fingerprint 均为 `glm-5.2`；Turn 最终仍以
`AGENT_MODEL_CALL_REJECTED / STRUCTURED_OUTPUT_INVALID` 失败，DeepSeek authorization/TLS/credential/HTTP 全部为 0。

原始闭合输出显示 4 个 invalid call：第一次遗漏 `action.operation` 后，fresh repair 正确补上 `SOURCE_SEARCH`；第四次把
`arguments` 错写成 locator-key object 后，fresh repair 正确恢复 `name/value` 数组；第六次在 effective tool catalog 只剩无 argument 的
`WORLD_MODEL_QUERY` 时再次遗漏 `action.operation`，第七次 fresh repair 原样遗漏同一字段，耗尽一次格式修复并关闭 Turn。

最后两个输出的 `evidence_need` 和 plan 都明确写着要执行 `WORLD_MODEL_QUERY`，所以首次偏差不是理解、Source、Ark availability 或 route；是
closed shape repair 没有得到足以定位字段的受信诊断。修改前 nullable `action.anyOf` 校验会丢弃各分支错误，只返回
`$.action matches no allowed schema variant`；format-repair input 又只绑定 untrusted prior output，不包含该 trusted local validator failure。

## Evidence

- exact candidate `d961be71b80bbc3c06d1e19074bcecb009834bed` / tree
  `52243b232bad32cc9da7b1e744c957f4866e171c`，Source commit/tree 仍为
  `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7 / 047d79d8588b76013c260f3f1a9565707301a60a`。
- `run-049-mvp-experience` terminal receipt：Conversation/Turn=`1/1`、Ark dispatch=`7`、DeepSeek dispatch=`0`、retry=`0`、human approval
  request=`0`、Production Activation=`NOT_EXECUTED`；Ark TLS attempt/success、credential resolution/success 和 HTTP dispatch 均为 `7/7`，
  pre/post-dispatch failure 均为 0。terminal internal digest 为
  `sha256:6b85b4993ed5a5c3671faaef44dbaf1e6f03fe1331c34cd76ddd0369eac968bd`。
- call 6/7 的 exact tool catalog 都只有 `{"operation":"WORLD_MODEL_QUERY","arguments":[]}`；两个 raw output 的 action 都只有
  `arguments/evidence_need`。这证明同一 shape violation 在既有一次 repair 后复现，不能靠重跑或 fallback 碰答案。

## Disposition

当前 `SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 要求：

- closed-schema validator 对 `anyOf` 保留每个分支的 bounded failure；closed object mismatch 明确列出 missing/unexpected field names，不记录
  output value。
- 一次 fresh same-profile format repair 同时绑定原 failed call receipt、untrusted prior output、trusted validator error code/message；diagnostic
  只定位 shape，不授予事实、工具或审核权。
- prompt 明确每个非空 action 恰好包含 `operation/arguments/evidence_need`；即使 catalog 只有一项也必须复制 operation。Application 不猜测、
  补写或静默规范化字段，第二次仍失败就关闭 Turn，fallback 仍为 0。
- 该诊断性 bugfix 沿用 current `conversational-engineering-agent@8 / conversational-engineering-agent-no-tools-prompt@8 /
  ENGINEERING_AGENT_PRIMARY_INPUT@8 / ENGINEERING_AGENT_REVIEW_INPUT@2` 协议族，并由修复后的 exact prompt/input/request digest 区分具体字节；
  这与可信提交 `92d1024` 在同一 current identity 下引入 `format_repair_policy` 的既有版本语义一致。不得复用历史 v7 的 unaccepted
  Review input `@3`，也不得制造 docs gate 未授权的 `@9/@4`。

定向测试新增 nullable closed-object missing-field diagnostic，以及与 run-049 同形的“缺 operation → fresh repair 显式
`WORLD_MODEL_QUERY`”链；受影响 Adapter/Agent/routing/launcher/runtime/artifact/CLI 组合 124 tests PASS。一次 operator 命令曾引用不存在的
`tests.test_engineering_chat_session_runtime`，在 test discovery 阶段失败且没有产品 Case 运行；更正后的 exact 有效集合为 124/124 PASS。
外部 Provider/network dispatch 0，full regression 0。fresh Browser successor 待执行。
