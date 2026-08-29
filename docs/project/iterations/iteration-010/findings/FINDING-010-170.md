---
id: FINDING-010-170
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [FINDING-010-160, FINDING-010-168, FINDING-010-169, ITER-010-PDR-012]
code: [src/software_world_model/application_services/conversational_engineering_tools.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_tools.py, tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: project-current-turn-novel-world-model-items-and-identify-non-json-prefix
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-170：重复 Cognition 投影把同一 Turn 推入超长上下文并放大 JSON 外叙述

## Observation

`run-059-mvp-experience` 以 exact product
`4f6c73b551af8f7d83887e8db974e060bff494a8 / ae5e045dc5c59441548a2db728205c053e3b7f67` 启动
`FINDING-010-169` 的 fresh Browser successor；第二次 Ark dispatch 在已跨 HTTP boundary 后返回
`PROVIDER_OUTCOME_UNKNOWN`。该 run 按合同不重试并以 `STOPPED_AFTER_DISPATCH` 保存，不能据此修改产品逻辑。新隔离的
`run-060-mvp-experience` 使用同一 product 与 mall exact Source，在第一个冻结登录问题上连续完成 11 次 Ark HTTP dispatch，却最终以
`AGENT_MODEL_CALL_REJECTED / STRUCTURED_OUTPUT_INVALID` 失败关闭。

run-060 的第 3、6、8、10 次 Primary 输出都先写自然语言 analysis/narration，再给出 JSON；第 4、7、9 次 fresh same-profile repair 成功
返回唯一 JSON object，但第 11 次 repair 再次先写 analysis，因首字符不是 `{` 被本地 closed validator 正确拒绝。Ark adapter 已发送
`response_format=json_object` 且关闭 thinking；11 个 Provider call 都是 completed response，request retry、fallback 和 DeepSeek dispatch
均为 0。因此不能把该失败归因于 Provider availability，也不能用 substring extraction 追认后部 JSON。

同一 trace 还暴露了更早的系统性放大器。对应 malformed 初始调用的实际 input token 从 `44,102`、`49,203` 增长到 `81,735` 和
`113,884`，最后 repair 为 `115,784`。第 10 次 sealed Primary input 有 `308,313` 个字符；其中三个 World Model SUPPORT content 分别有
`67,625 / 69,537 / 68,812` 个字符，每个都重新投影 35 个 Cognition dimension，但按 exact item digest 计算只有 `35 / 13 / 2` 个首次出现。
也就是说，后两次 World Model Observation 把前面已经进入同一 current-Turn Evidence domain 的 55 个 dimension 再次全文披露。新的
semantic query 虽可能增加少量认知，却不应让 append-only Observation 重复携带已经可引用的完整 statement。

## Evidence and first divergence

- `run-060` terminal receipt 密封 Conversation/Turn `1/1`、Ark dispatch `11`、credential/TLS/HTTP `11/11/11`、request retry `0`、人工重复
  审批 `0`、DeepSeek dispatch `0` 和 Production `NOT_EXECUTED`；当前失败不是 route switch、credential、network 或 Source 操作故障。
- Gateway SQLite 的 11 个 call root 都是 `COMPLETED`。第 10/11 次 output 的 first-non-whitespace class 都是
  `NON_JSON_OBJECT_PREFIX`，而旧 repair diagnostic 只报告 generic line 1 / column 1 / character 0 syntax failure，未把“JSON object 前存在
  外部叙述”作为有界类别投影给 repair。
- 第 10 次输入的三个 World Model support Observation 共投影 105 个 dimension，exact unique digest 只有 50 个。最早可修复的数据膨胀点在
  trusted World Model evidence-tool adapter：它把每次 query-relevant Cognition Context 的完整 item 集合作为新的 SUPPORT，而不是只追加本
  Turn 尚未观察的 item。Agent input 只是忠实重复这些不可变 Observation，不是最早 Owner。
- 对该密封 input 逐 item digest 应用新 delta 规则的只读机械模拟，把三个 World Model SUPPORT 从
  `67,625 / 69,537 / 68,812` 字符变为 `67,773 / 29,523 / 9,050`，整个 sealed Primary input 从 `308,313` 降为 `196,753` 字符（约减少
  36%）。这是对旧 trace 的确定性投影估算，不是 fresh Provider 成功证据。

## Classification and disposition

这是 `system-contract`，因为它收紧 World Model Tool Observation 的跨调用语义，同时保留既有 authority、Evidence 和 Citation 身份：

1. 同一 Turn 内每次 World Model query 仍绑定完整 current Cognition Context、exact revision、coverage、receipt 和 context digest，但新的
   SUPPORT payload 只携带该 Turn 先前 SUPPORT 尚未投影的 exact Cognition item digest，并记录 current/novel/already-observed counts。重复 item
   的原 Observation、Ledger 和 authority receipt 不被删除或改写；需要该事实的 Claim 继续引用首次携带它的 SUPPORT Observation。
2. 当前 query 没有任何 novel supported item 时，不再制造重复 SUPPORT；它形成明确 no-new boundary/no-progress。新 query 含少量 novel item
   时只签发这些 item 的 Citation refs，因此 append-only Evidence 仍完整而 model-facing bytes 不随重叠快照成倍增长。
3. Primary/Reviewer Prompt 把唯一 JSON object envelope 提升到首要约束；trusted diagnostic 区分
   `NON_JSON_OBJECT_PREFIX / JSON_SYNTAX_ERROR / CLOSED_SCHEMA_SHAPE`，`ENGINEERING_AGENT_OUTPUT_PREFLIGHT@3` 机械重复首尾字符、禁止 object
   外 analysis/narration 和 exact failure category。Application 仍不抽取、不转义、不规范化模型输出，也不增加第二次 repair 或 route switch。

确定性测试覆盖两次 World Model query 的 shared+novel item：首次 SUPPORT 为 2 items，第二次只为 1 novel item，shared statement 不重复且最终
Citation identity 完整；另覆盖 analysis prefix 的有界 diagnostic、repair preflight、Primary/Reviewer 与既有 quote/closed-field 修复。该修复
不改变 Provider adapter bytes、Source 权限、预算或问题路由。直接 Model/Tool 责任组合 `32/32` PASS，Agent、routing、launcher、runtime、
artifact 与 CLI 受影响组合 `99/99` PASS，文档 `576` 项检查 PASS；全部是本地验证，外部 dispatch 为 0。它们不追认 run-059/060。必须用新
exact product identity 和 fresh run authority 重新执行冻结三轮 Browser chain；冻结问题 4/5 仍未参与修复并保持 unseen。
