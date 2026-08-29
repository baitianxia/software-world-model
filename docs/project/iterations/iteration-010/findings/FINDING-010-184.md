---
id: FINDING-010-184
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [FINDING-010-175, FINDING-010-183, ITER-010-PDR-012]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: rebuild-zero-copy-invalid-subtrees-and-restore-existing-values
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-184：closed-shape repair 把无可复制值的 invalid array 长度误当成守恒义务

## Observation

fresh Browser `run-074-mvp-experience` 绑定 exact product
`ba91713568c522b0d92ec3c730856db3b3685b0a / fd5c6ea9554bd9b5ff0ddafd64cca7fc3e37dc98` 与 mall exact Source
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7 / 047d79d8588b76013c260f3f1a9565707301a60a`。同一登录 Conversation 的
Turn 1/2/3 分别以 Ark dispatch `14/9/4` 形成 `SUCCEEDED / ACCEPTED`，真实覆盖初问、沿用上一轮的失败分支追问和用户纠正口径后的定向
修订；页面为每 Turn 显示 current Evidence/Citation、fresh Review 和 Delivery Authorization。该三轮链已按 PDR-012 立即作为“开发体验候选”
交付，明确不是 MVP 或质量 PASS。独立新 Conversation 的商品分类删除问题又以 Ark `7` 次成功交付。

第五个 Maven/启动链问题在 5 次 Ark dispatch 后以 `FAILED / AGENT_MODEL_CALL_REJECTED` 关闭。第四个 Primary call
`model_call_448732051b0b40fcac51aaeb327ef75d` 返回 parseable JSON，但把 `SOURCE_SEARCH.arguments` 写成长度为 1 的 array，唯一 item 为
`{"evidence_class":"BUILD_CONFIGURATION","query":"docker-maven-plugin"}`。trusted diagnostic 正确定位
`$.action.arguments[0] allowed_exact=[name,value] / missing=[name,value] / unexpected_count=2`。唯一 same-profile repair
`model_call_494fd11668934ad9bd78b65f0aae32ee` 正确复制 sealed action template，重建成两个 `name/value` item；但它还把
`open_items[0]` 的 Unicode `—` 改成 ASCII `-`。

现行 `ENGINEERING_AGENT_OUTPUT_PREFLIGHT@4` 把 prior array 的长度/顺序无条件投影为 exact-copy obligation。这个 prior item 没有任何一个
allowlisted field/value，合法的两参数 action 却必须把 array 从 1 个 malformed item 重建为 2 个 sealed-template item，因此长度守恒与
closed action contract 不可能同时满足。标点漂移又证明即使其他字段已经合法，让模型重发完整数千字 Work State 也会产生与 shape repair
无关的字节变化。Application 拒绝 raw drift 是正确的；系统缺口是 projection 没有区分“已有合法值必须守恒”与“完全没有合法值、只能从
trusted template 重建”的子树，也没有在不授予新语义的前提下机械恢复 prior exact value。

## Evidence and first divergence

- 首个登录 Conversation 为 `conversation_8b24339efd5c4867843d4246e7b499f8`；Turn 1/2/3 的 Provider dispatch 为 `14/9/4`，Citation
  分别为 `38/38/1`，三轮均有 fresh approved Review 与 Delivery Authorization。分类删除 Conversation
  `conversation_025fefb6ff674f68a09c814e888f315d` 以 7 次 Ark 和 39 Citation 成功。Maven/启动链 Conversation
  `conversation_847433b823b340dc9e74b838a7d0afd2` 保持 ACTIVE，但失败 Turn 不含 Answer/Review/Delivery。
- invalid/repair output digest 分别为
  `sha256:2389c6f37acef72bc48d6afb186a8156f9b2969eb4d4a4f27a53c006f52277d2` 与
  `sha256:2f85c4090e9bbd0abec194e2dc1ecbadca4439cab3d0f60dfd6a0fe45b74b857`。除 `action.arguments` 必要重建外，两个 JSON 的既存
  allowlisted primitive 只在 `$.open_items[0]` 有一处 `—`/`-` 差异。
- repair sealed role input 明确保留 `tool_action_budget used=3 / remaining=5`、含 `SOURCE_SEARCH` 的 effective catalog、
  `BUILD_CONFIGURATION` class 和未使用 query domain；失败不是 tool/source budget、completion policy 或 route 拒绝。
- terminal receipt payload digest 为 `sha256:92ca409adf1ebd597ef64158a38d58886b17cd5297ba7a2b2756b45aca51bee7`，terminal 文件
  SHA-256 为 `4d6eb0635bff8ab908863dd0793f0961a07f1240867bd0c2a6962913556d51d8`。它密封 3 Conversation、5 Turn、Ark
  dispatch/TLS/credential/HTTP `39/39/39/39`、retry 0、post-dispatch unknown 0、human approval request 0。DeepSeek admission 为周末
  `ALLOWED_OFF_PEAK`，但 Ark 全部可信可用，故 DeepSeek dispatch/TLS/credential/HTTP 全 0；Production `NOT_EXECUTED`。
- first model defect 是 initial Primary 的 malformed action item；first systemic repair divergence 是 `@4` 把没有任何 existing
  allowlisted item value 的 invalid array 容器长度仍当作守恒义务。Application 不应放宽 Tool/Context contract，也不应让 raw 标点漂移进入
  Work State。

## Classification and disposition

这是 `system-contract / systemic` Finding；修复任何工程、语言、问题、字段或 Unicode 内容，不按 mall、Maven、参数名或破折号特判。

1. `ENGINEERING_AGENT_OUTPUT_PREFLIGHT@5` 递归投影 copy obligation。若 schema-invalid array 的全部 item 都没有任何 existing
   allowlisted value，整个 array 子树从 projection 缺席，repair 可且只能从 current sealed schema/domain/template 重建；只要仍有一个合法
   item value，原 array 长度/顺序和所有可对齐 sibling 继续逐值守恒。
2. 对 projection 中的既存值，Application 在 Proposal decode 前执行
   `RESTORE_SCHEMA_MATCHING_ALLOWLISTED_VALUES_BEFORE_DECODE@1`：只把 repair 的对应值恢复为 prior exact value，再运行原机械相等检查。
   raw `—`→`-` 等漂移不被授权，也不会进入 Work State。
3. restoration 不生成 missing field、不保留或解释 unexpected key、不构造 invalid subtree、不改变有 copy obligation 的 array 对齐，也不
   授予事实、Tool、Review 或 Delivery authority。无 copy obligation 的 rebuilt subtree 仍须通过 output schema、effective tool catalog、
   argument/domain、Context/Evidence、completion policy 和后续 Review；任一不成立仍失败关闭。
4. Provider raw output、prior output 与最终 sealed Work State 保持可重算；不抽取 JSON substring、不增加第二次 repair、不改变 Provider
   adapter/qualification、不触发 fallback。受影响 Model/Agent/Tool/Route/Browser/Session/CLI/Gateway 组合 `141/141` PASS，外部 dispatch 0。
   fresh Browser successor 必须使用新 clean product/run identity复验第五题与未参与修复的异质题；run-074 的历史失败 Turn 不追认。
