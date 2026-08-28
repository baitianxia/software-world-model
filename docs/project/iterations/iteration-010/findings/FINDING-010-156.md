---
id: FINDING-010-156
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai, architecture, quality]
depends_on: [FINDING-010-154, FINDING-010-155]
code: [src/software_world_model/application_services/conversational_engineering_routing.py, src/software_world_model/application_services/engineering_conversation.py, src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py, src/software_world_model/interface/engineering_chat_provider_launcher.py, src/software_world_model/interface/engineering_chat_session_artifact.py, src/software_world_model/interface/engineering_chat_session_runtime.py]
tests: [tests/test_conversational_engineering_routing.py, tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_model.py, tests/test_engineering_chat_provider_launcher.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: availability-only-fallback-and-model-transparent-route-refactor-is-current-blocking-case
target: SYS-ADR-017
---

# FINDING-010-156：输出合同失败被误当成首选执行配置不可用

## Observation

`run-045-mvp-experience` 的 terminal digest 为
`sha256:00ad46545e8d31699ace4ff1f7fa8b6b8cf662a04e86f480698684f1cbf9914f`。Ark Gateway 数据库记录 7 次调用：7 次
TLS handshake、credential resolution 和 HTTP dispatch 全部成功，实际模型指纹均为 `glm-5.2`，transport 的 pre/post-dispatch failure 与
outcome unknown 均为 0。7 次中有 2 次在已收到完整响应后被 Application 标记为 `STRUCTURED_OUTPUT_INVALID`：

- Primary Agent 返回了 JSON，但 `action.arguments` 使用了错误的封闭结构；
- Independent Reviewer 返回自然语言分析而不是要求的 JSON 对象。

同一运行随后在备用执行配置上产生 21 次调用。这里没有证据证明首选执行配置不可用；证据只证明两个已完成响应不满足 Application 的输出合同。
因此把这些失败作为备用路线条件，会用更换模型掩盖结构化解码、Agent 输出或 Reviewer 输出问题，并使运行行为依赖具体模型表现。

当前产品实现与该错误语义一致：

- `conversational_engineering_routing.py` 的产品协议和构造器固定 `VOLCENGINE_ARK → DEEPSEEK`；
- Router 对任何 `FAILED` 且带 `provider_failure_classification` 的首选 attempt 都直接创建 fallback attempt；
- `EngineeringProviderFailureClassification` 仍包含 HTTP error、outcome unknown、output invalid 和 review rejected，Agent 又把输出解码失败和审核拒绝映射到这些路由分类。

问题属于通用路由架构和实现，不是 Ark、DeepSeek、mall 或本轮题目的特例。配置中可以记录当前 Provider/model 身份，但产品动作、Agent 决策和
fallback branch 不得读取这些身份。

## Disposition

当前权威文档已统一处置到 `SYS-ADR-017`、Model Gateway、Engineering Conversation、架构不变量、运行流和安全边界：

1. 产品路由只消费 `preferred/fallback` role、execution-profile ref/digest 和受信 availability verdict；具体 Provider/model 只存在于配置、资格、
   Adapter/plugin 与 runtime receipt。
2. 只有 execution profile 登记的 availability owner 对 exact profile 与原始收据密封
   `PREFERRED_EXECUTION_PROFILE_UNAVAILABLE`，才允许最多一个 fallback attempt。Raw unavailable、HTTP error/status 或 outcome unknown
   只是裁决输入，不直接授予 fallback。
3. Structured-output invalid 和 Reviewer reject 明确 non-eligible。需要继续时，只能在同一 execution profile 上发起有界的新授权 call，使用新
   request identity、receipt 和预算；它不是旧 transport request 的 retry。耗尽后如实关闭当前 Turn。
4. `V-MODEL-TRANSPARENT-ROUTING-001` 已成为当前长动作的 executable blocking Case：互换虚拟 profile 身份不得改变行为；只有可信 unavailable
   verdict 可产生一次 fallback；output-invalid、review-rejected 和 raw HTTP/outcome-without-verdict 的 fallback dispatch 必须为 0。

本次只纠正权威文档与计划机械门禁，没有修改上述产品代码，也没有运行外部 Provider。当前实现因此被明确标记为不符合新契约；后续开发的第一项
产品任务是完成通用 route/profile/availability boundary 重构及定向测试，在该 Case PASS 前禁止真实 fallback dispatch 和最终方向 handoff。

## Implementation evidence（2026-08-28）

后续同一活动长动作已完成该处置，不改动作、Result 或计划游标：

- Application route spec/authority/attempt/route receipt 只保留 `PREFERRED/FALLBACK`、execution-profile ref/digest、披露/standing authority 与预算；
  具体 Provider/model/endpoint/qualification 已移回配置、Adapter 与 runtime receipt 层。首选 profile 的 registered availability owner 及 verdict 被 route plan、
  logical Turn、exact profile、exact preferred attempt receipt、raw failure 和时间共同绑定；无 verdict、owner 漂移或 malformed verdict 均失败关闭。
- `PROVIDER_OUTPUT_INVALID` 与 `MODEL_REVIEW_REJECTED` 不再授予 fallback。Primary/Reviewer 结构无效时，模型边界最多创建一次同 profile 的 fresh call，
  新 input Manifest/request digest/model receipt 均不同，旧 output 作为 untrusted repair input，transport request retry 仍为 0；第二次失败保留两次准确调用并关闭当前 Turn。
- `tests.test_conversational_engineering_routing` 的 14 个确定性用例覆盖虚拟 profile 身份互换、静态身份分支阻断、raw HTTP/outcome 无 verdict、registered owner、
  exact unavailable verdict、output-invalid、Reviewer reject、fresh fallback chain 与 duplicate-cost risk。`tests.test_conversational_engineering_model` 覆盖 Primary/Reviewer
  fresh format repair 和 repair exhaustion；Agent 既有 Finding rewrite 用例证明同 profile 新 Agent/Reviewer call 与 fresh Review。
- 定向 impact/startup/safety/failure-truthfulness 组合共 95 tests PASS，外部 Provider/network dispatch 0，full regression 0。该证据使
  `V-MODEL-TRANSPARENT-ROUTING-001` PASS；真实 Session 仍使用 fail-closed availability owner，除非未来取得当前 exact availability verdict，否则不会发起实际 fallback。
