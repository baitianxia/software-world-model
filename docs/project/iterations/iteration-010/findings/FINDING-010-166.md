---
id: FINDING-010-166
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [FINDING-010-159, FINDING-010-160, FINDING-010-161, ITER-010-PDR-012]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: make-model-facing-action-and-evidence-projections-isomorphic-to-closed-output-roles
target: src/software_world_model/ai_infrastructure/conversational_engineering_model.py
---

# FINDING-010-166：模型可见工具签名与输出 action 不同形，证据用途也未就地分区

## Observation

对 `run-052/053` 的原始 Gateway SQLite、sealed Primary input 和 exact output 逐项重建后，最早偏差位于主 Agent 的模型可见投影，而不是
Source、World Model、Provider availability、route 或本地 validator：

- `tool_catalog` 只给出 `operation` 和参数名序列，closed output 却要求模型另行构造
  `action.operation + arguments[{name,value}] + evidence_need`。历史 malformed output 正好覆盖这两个转换点：既出现
  `arguments[{locator_reference:...}]`，也在原问题和异质问题中连续遗漏 `operation`；后者即使收到
  `$.action ... missing=[operation]` 的 trusted repair diagnostic 仍原样重复。
- `current_turn_observations` 把 SUPPORT 与 BOUNDARY 内容混排，合法 ID 只在远离内容的 policy 数组中分区。run-053 的 Answer 已把
  draft-wide boundary IDs 正确列出，却又把同一 BOUNDARY observation 放入 affirmative Claim 的
  `support_observation_ids`；原始 repair 只收到无路径的通用语义错误，第二次输出重复非法引用。

模型不应靠长上下文中的二次形状转换来满足安全边界。Application 同样不得从参数形状或单一 effective operation 猜测、补写
`operation`，也不得把 BOUNDARY 静默改标为 SUPPORT。

## Evidence

- `run-052` calls `model_call_9a252241044f46b088014de6a906e2e8 / model_call_0ded87bd80314a6d93095d9c1ae12f6e`
  的 exact action 都只有 `arguments/evidence_need`；catalog 同时存在 WORLD_MODEL_QUERY 与 SOURCE_SEARCH。
- `run-053` calls `model_call_49354a32c5bf4ccc9184858d7ca5c736 /
  model_call_fee18f9efaf0426a9db04a20a1bc8321` 在只剩 WORLD_MODEL_QUERY 时仍连续缺 `operation`；calls
  `model_call_7828b77e8c96444880d2a71a4d2fb4a2 / model_call_566cc0f2197e48e0a8090b90e6b9166f` 连续把
  BOUNDARY ID 放入 Claim support。
- 新定向 fixture 覆盖“缺 operation → fresh same-profile repair”与“BOUNDARY 进入 Claim → 带 exact path 的 fresh repair”；Agent、
  routing、launcher、runtime、artifact 与 CLI 组合 `74/74` PASS。外部 Provider/network dispatch 0，full regression 0。

## Classification and disposition

这是 `local-implementation`：系统 Owner、不变量和安全语义不变，仍由主 Agent 显式选择 action，由 Application 严格验证；SUPPORT 只支持
affirmative Claim，BOUNDARY 只绑定 limitation。修复只让模型输入与既有输出角色同形：

- 每个 effective tool entry 直接携带完整 `action_template`；模型复制完整对象并只填空值，不再把参数名签名转换成另一种对象形状；
- current-Turn evidence 内容在模型输入中按 SUPPORT/BOUNDARY 分区，draft policy 明确 Answer 中的 boundary 只能进入 content 与
  `boundary_observation_ids`，不能伪装为 Claim；
- output schema 就地描述 explicit operation 与引用 copy domain；语义拒绝给出 bounded JSON path 和合法 policy 字段，但仍不回显未知键或
  静默修补输出。

Provider adapter、execution-profile identity、fallback eligibility、Source/World Model 权限、预算和产品路线均未改变。fresh Browser
successor 仍须证明真实模型是否接受该通用投影；失败时继续留在同一产品开发动作并重新定位，不以本地测试追认体验或质量。
