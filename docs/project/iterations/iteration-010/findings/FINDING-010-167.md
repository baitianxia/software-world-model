---
id: FINDING-010-167
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [FINDING-010-159, FINDING-010-160, FINDING-010-166, ITER-010-PDR-012]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: append-a-trusted-shape-only-output-preflight-after-the-sealed-role-input
target: src/software_world_model/ai_infrastructure/conversational_engineering_model.py
---

# FINDING-010-167：同形 action template 已生效，但 malformed output 仍可锚定一次 repair

## Observation

fresh `run-055-mvp-experience` 在 exact product
`e14ef02255a5991b3a6fc30092c1b3b5990bf70f / 04832250a49b2f4194d80f8201e30db65f88376a` 与 mall Source
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7 / 047d79d8588b76013c260f3f1a9565707301a60a` 上，已经完成首个同一
Conversation 的三轮浏览器链：原问题与追问分别 `SUCCEEDED / ACCEPTED`，用户纠正为
`SUCCEEDED / REVIEWED_LIMITATION`，Conversation 保持 `ACTIVE`。这证明 `FINDING-010-166` 的完整 action template 与证据用途分区能通过
真实 Ark 主链，并已经按 PDR-012 立即交付非 MVP 开发候选。

随后在新 Conversation 的首个异质问题“删除商品分类时的关联数据与事务边界”上，Turn 以
`AGENT_MODEL_CALL_REJECTED / STRUCTURED_OUTPUT_INVALID` 失败关闭。初始 call
`model_call_4cba2eacf77848809b327f0494ff9bd1` 与 fresh same-profile repair call
`model_call_8e564de9c84b49fc869d8d79e4ccc6cc` 的 raw output 逐字相同：两者都生成合法的
`SOURCE_SEARCH` 参数与 evidence need，却都只返回 `action.arguments/action.evidence_need`，遗漏 `action.operation`。

repair 的 sealed input 已同时包含：

- trusted local diagnostic：`$.action ... missing=[operation]`；
- 含 explicit `operation=SOURCE_SEARCH` 的完整 `action_template`；
- “复制完整 template、即使单一 operation 也不得遗漏”的 Prompt 规则。

因此本次最早偏差不再是模型可见 action 与输出异形，而是一次 malformed prior output 在同一模型的 deterministic repair 中仍被原样复现。
这是可观察的模型/Prompt 交互，不应被解释为 Source、World Model、Ark availability、fallback 或用户授权失败。

## Evidence

- 三轮开发链的浏览器终态依次为 Ark dispatch `8 / 3 / 4`；第四个异质 Turn dispatch `2` 后失败，总 Ark dispatch `17`，DeepSeek
  authorization/TLS/credential/HTTP dispatch 均为 `0`。
- 两个失败 call 均为 Ark `glm-5.2` completed response、termination=`stop`，各自只因 closed output schema 拒绝；repair 没有重发旧
  request bytes，也没有触发 fallback。
- repair Manifest 的模型可见 `tool_catalog` 保留 `WORLD_MODEL_QUERY` 与 `SOURCE_SEARCH` 两个完整 template，trusted diagnostic 精确指向
  `$.action.operation`；Application 没有按参数形状猜测 operation，也没有补写或接受 malformed output。

## Classification and disposition

这是 `local-implementation`；系统 Owner 与失败语义不变。每次已授权角色调用现在在 sealed role input 之后追加一个独立、受信但
`shape_only` 的 final-output preflight：

- 从 exact registered output schema 机械投影完整 top-level required fields；Primary 另重复当前 effective tool catalog 的完整 action
  templates 与 `operation/arguments/evidence_need` required fields；repair 时只重复 trusted validator code/message，不复制 prior output
  为事实；
- preflight 明确 `semantic_or_tool_authority=false`，不新增 operation、Evidence、Review 或 Delivery 权限；Gateway 从 exact sealed role
  payload 与 registered schema 重新计算其内容和 digest，任何漂移在 Provider dispatch 前失败关闭；
- 模型仍必须显式选择并返回 operation；Application 不补字段、不重标 Evidence，closed validator 仍拒绝 malformed output，一次 fresh
  same-profile repair 后再次失败仍只关闭当前 Turn，fallback 保持 0。

Provider adapter、adapter version、Conformance identity、Source/World Model 权限、预算和产品路线均未改变。定向测试覆盖 initial/repair
preflight 的消息顺序、shape-only 标记、完整 effective templates、exact diagnostic 与逐叶 disclosure accounting；受影响组合
`74/74` PASS，文档 `573` 项检查 PASS。fresh Browser successor 必须使用新 product identity 与新 run authority，不能复用或改写
`run-055` 历史。
