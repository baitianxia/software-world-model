---
id: FINDING-010-174
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai-infrastructure, application, quality]
depends_on: [FINDING-010-173, ITER-010-PDR-012]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: bounded-complete-closed-shape-diagnostic
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-174：父对象 shape mismatch 提前返回，隐藏同次输出的嵌套缺失字段

## Observation

fresh `run-064-mvp-experience` 绑定 exact product
`d2230bd777e2fd71ed8dd743025296990a53012d / f4348ddcff7d4ea5457b15f4e60bff2c54e635f9` 与 mall exact Source
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7 / 047d79d8588b76013c260f3f1a9565707301a60a`，用于验证
`FINDING-010-173` 的 exact allowlist repair 和机械语义守恒。

Turn 1 的 initial Primary 输出是 parseable JSON，但同时存在三处 closed-shape 违例：root 多出 input-owned
`work_state_digest`；`action` 多出 `evidence_need_for_boundary`；`action.operation` 缺失。旧 diagnostic 在 root field set mismatch
处立即返回，只投影 root 的 `allowed_exact`、`missing=[none]` 和 `unexpected_count=1`，没有继续遍历仍可由 trusted schema
机械定位的 `action` mismatch。

唯一 same-profile repair 删除了 root 和 `action` 的两个 unexpected field，且没有改写任何原先已存在的 allowlisted field value；因此
`FINDING-010-173` 的语义守恒 guard 没有误杀。但 repair 输入从未获知 `action.operation` 也缺失，repair 输出继续漏掉该字段，最终在任何
Tool、Evidence Package、Answer 或 Review 前以 `AGENT_MODEL_CALL_REJECTED` 失败关闭。问题不是 Provider route、Source、Browser 或
repair 次数不足，而是 Application-owned diagnostic 没有在唯一 repair 前一次性投影同份 parseable output 中已知的嵌套 shape failure。

## Evidence and first divergence

- initial/repair Gateway call 分别为 `model_call_4cee674917ec4533b1f7a159d92f2730` 与
  `model_call_3a5847a0f09f41fda27a26200893553e`；两份原始输出都保存在 run-064 Ark Gateway repository。
- repair sealed input 的 trusted diagnostic 只有
  `$ object fields do not match the closed schema (... missing=[none]; unexpected_count=1; ...)`。initial output 的
  `action` 没有 `operation`；repair output 仍没有 `operation`，但其余既有合法字段和值保持不变。
- first failed boundary 是 AI model closed output；最早可修复 divergence 是
  `_structured_output_diagnostic` 的 parent-first early return。closed decoder 和 Browser failure projection 继续正确失败关闭；不能补写
  run-064 Answer，也不能把它追认为 `FINDING-010-173` 的 live PASS。
- terminal receipt digest
  `sha256:7cd6079b026e3cc9c5396045d2fe52e5b7dab765bff93ba9228e4bdc5ffe1cdd` 密封 Conversation/Turn `1/1`、Ark
  dispatch `2`、DeepSeek dispatch `0`、request retry `0`、human approval request `0` 与 Production `NOT_EXECUTED`。

## Classification and disposition

这是 `system-contract`：修复任意 closed output 的结构诊断，不按工程、问题、字段名、工具或模型输出增加例外。

1. 对 parseable closed output，Application 以 deterministic trusted-schema traversal 收集同一输出中可机械定位的 parent 与 nested object
   field-set mismatch；root mismatch 不得短路对仍存在的 allowlisted child value 的遍历。
2. 单次 diagnostic 最多投影 32 处 mismatch；每处只包含 path、完整 trusted `allowed_exact`、missing field names、unexpected count 与
   additional-fields-forbidden 状态，不回显 untrusted unexpected names。nullable union 只遍历与 runtime value 类型相符的 schema branch；
   local `$ref` 仍在本地解析。
3. repair 次数仍为 1，route、Provider adapter、Tool authority、预算和 closed output schema 不变；`FINDING-010-173` 的递归语义守恒继续要求
   所有既有 allowlisted value/顺序不变，只允许补 missing field 和删 unexpected field。

新增确定性 Case 复现 root unexpected、nested unexpected 与 nested missing 同时出现：唯一 repair input 同时收到 `$` 与 `$.action`
diagnostic，不泄漏两个 unexpected name，fresh repair 补齐 `operation` 后形成合法 Proposal。Model suite `23/23` PASS；相关
Agent/Tool/Model/routing/Browser/candidate/launcher/runtime/artifact/CLI/Gateway 组合 `114/114` PASS；文档检查 `580` 份 current
documents PASS。外部 dispatch 为 0；该本地证据不追认 run-064。fresh Browser successor 必须使用新的 clean exact product/run identity
重新开始固定三轮链，问题 4/5 继续 unseen。
