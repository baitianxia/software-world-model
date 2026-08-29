---
id: FINDING-010-178
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [operations, quality]
depends_on: [FINDING-010-157, FINDING-010-158, FINDING-010-177, ITER-010-PDR-012]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: individual
disposition: provider-environment-hold-with-partial-investigation-proof
target: ITER-010-VERIFICATION
---

# FINDING-010-178：修复后调查首步已真实生效，但当前 Provider 路径连续不可执行

## Observation

clean exact product `b03dc622e0e5b3d3a30df11c9cf0eeb5e8f13fa8 / 4bff0e1f3a3988dabc91be4449b729c0b8f08dc2`
在 fresh `run-068/069/070-mvp-experience` 上继续固定三轮 Browser 链。run-068 的前两次 Ark call 均完成：Primary 第一步从
`WORLD_MODEL_QUERY` 开始，第二步才提交精确 `SOURCE_SEARCH(SOURCE, UmsAdminController)`。这真实证明
`FINDING-010-177` 的 World Model-first 和 cognition-derived source-native target 已进入 live model path，没有复现 run-067 的 broad
`UmsAdminLogin` 首搜；但它不证明剩余 Tool budget 收敛、Draft、Review、Citation、Delivery 或完整三轮。

run-068 第三次 Ark call 返回 raw `PROVIDER_HTTP_ERROR`；fresh run-069 的第一次 Ark call 又返回同类 raw
`PROVIDER_HTTP_ERROR`。两者都没有受信 `PREFERRED_EXECUTION_PROFILE_UNAVAILABLE` verdict，因此 route 正确保持 fallback dispatch 0，
没有把原始 HTTP outcome 擅自改写为 availability。短暂间隔后的 fresh run-070 第一次 Ark call 在 HTTP 前发生一次 TLS failure，由现有
availability Owner 密封为 `PROVIDER_UNAVAILABLE`；route 因而合法选择 fallback，但当前 DeepSeek admission 在本地
`2026-08-29T14:50:43+08:00` 为 `DENIED_PRICING_CHECK`，在 credential/TLS/HTTP 前拒绝。页面如实显示
`AGENT_PRE_DISPATCH_REJECTED`。

本 Finding 当时把根因暂归为外部 `configuration/environment`，并且正确拒绝了修改 Prompt、提高 budget、把 HTTP error 强行提升为
unavailable、绕过 admission、重试同一 request 或切换到未授权 Provider。后续 `FINDING-010-179` 取得了新的官方 schedule 证据，纠正了
“没有 implementation defect / 只能等待”的部分结论；本 Finding 的原始 run、路由和 transport 计数仍保持有效。

## Evidence

- run-068 Conversation `conversation_b015eb842e034d25904879fd1a5eb8b9`：
  `model_call_723d8eae61ed4447b3fa570a6326c532` 完成 World Model action；
  `model_call_ce2e9654c2774eb5921855210bc5bab8` 完成精确 Controller search action；
  `model_call_7c4d5d28802041f5b18856445fe3b337` 以 `PROVIDER_HTTP_ERROR` 关闭。terminal digest
  `sha256:4bbfb27ab219a8bae899b6eea7b26d67272f13b37f6fa737ec2234d59f770d9c` 密封 Ark 3 / DeepSeek 0。
- run-069 Conversation `conversation_3ae134a6ec32423db364af5a0560c3d7`：首个
  `model_call_403a59efeec74afc96a0611ca5b60c3d` 以 `PROVIDER_HTTP_ERROR` 关闭。terminal digest
  `sha256:adf6edfe942f9c9c920720d56cdbaa17391188bcd3c678a3b2e5ae063f65477e` 密封 Ark 1 / DeepSeek 0。
- run-070 Conversation `conversation_f34089b16d23430681d32eb125cc9f43`：首个
  `model_call_2772a4d0a27a415883e142fbd7be6614` 记录一次 pre-HTTP `TLS_FAILURE / PROVIDER_UNAVAILABLE`。Ark transport audit 为
  TLS attempt 1 / success 0、credential 0、HTTP 0；DeepSeek admission 为 `DENIED_PRICING_CHECK`，其 credential/TLS/HTTP 均为 0。
  terminal digest `sha256:36e2e3c046771c95f905fe1011d6bf3d13795387dc6da6c85d93193bd4a2e289` 密封 Ark dispatch 1 / DeepSeek
  dispatch 0。
- 三个 run 合计 Ark dispatch 5，其中前两次完成、随后两个 raw HTTP failure 和一个 pre-HTTP unavailable；DeepSeek dispatch 0、request
  retry 0、human approval request 0、Production `NOT_EXECUTED`。每个失败 run 均已停止并使用独立 identity，没有重提交失败 Turn。

## Classification and disposition

这是 `verification` Finding，处置到 `ITER-010-VERIFICATION`：

1. 保留 run-068 对 World Model-first 与精确 Source target 的 partial live proof，但 current
   `BOUNDED_INVESTIGATION_BUDGET_AND_TARGET_RELEVANCE_LOCAL_CANDIDATE` 仍不是 Browser/质量 PASS。
2. run-068/069/070 只作为失败与路由边界证据；不得形成 Answer/Citation/Review/Delivery，也不产生失败 Result、PDR、重复人工授权或计划游标
   变化。active standing authority 与同一开发动作仍有效。
3. 下一次 live 验证必须使用新的 clean exact product/run identity。`FINDING-010-179` 已证明 run-070 的 pricing check 过期，并把 current
   policy 修订为工作日三个时段、周末全天；fresh successor 可在 900 秒内 pricing check 与正常 route 条件成立时继续，不再等待周末窗口。
   仍不得伪造 Ark availability 或绕过 fallback admission。
4. 本 Finding 当时没有支持新的答案链 product change；本地 `115/115` 受影响测试、583-document check 与 plan snapshot/diff PASS 继续属于
   `FINDING-010-177` 候选证据，不追认上述 live run。
