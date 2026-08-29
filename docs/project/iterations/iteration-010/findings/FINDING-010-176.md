---
id: FINDING-010-176
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai-infrastructure, application, quality]
depends_on: [FINDING-010-173, FINDING-010-175, ITER-010-PDR-012]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: call-expression-evidence-and-review-remediation-separation
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-176：Reviewer 把可同包收窄的调用点结论误标为强制补证

## Observation

fresh `run-066-mvp-experience` 绑定 exact product
`3c4b49154666e479a292e8116fa8ebb71fea3e89 / e4115c6b65d023a1853aeae480755467e7de401b` 与 mall exact Source
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7 / 047d79d8588b76013c260f3f1a9565707301a60a`，用于复验
`FINDING-010-175` 的 exact repair copy 与 Draft claim closure。

Turn 1 取得 Controller 与 `UmsAdminServiceImpl` 的 current full-source observations。Primary 在 Reviewer rewrite 后把 Controller 行为加入
Claim inventory，并把 `new UsernamePasswordAuthenticationToken(userDetails, null, userDetails.getAuthorities())` 收窄为源码中直接可见的
构造器调用；同一 Claim 和正文都明确声明没有读取 `AdminUserDetails.getAuthorities()` 的实现，因而不肯定其运行时返回值或行为。

fresh Reviewer 仍把“源码中调用 `userDetails.getAuthorities()`”误读为对该方法运行时行为的肯定，返回 global
`COMPLETENESS_GLOBAL` Finding，并把 `requires_evidence` 设为 true；Finding 自己却同时给出“narrow the conclusion”作为合法修复。这违反
现有约定：current Package 已足以支持调用表达式与源码可见局部顺序，且同包删除/收窄即可纠正对 callee semantics 的任何扩写，不能同时声明
必须取得新 Evidence。Application 正确把这个 boolean 机械投影为 `tool_action_required=true`、`allowed_response_kinds=[]`。

后续 Primary 没有提交强制 Tool action，而是返回已收窄 Draft；第一次返回又在 diagram JSON string 中含未转义换行，形成
`JSON_SYNTAX_ERROR`。唯一 same-profile format repair 产生合法 JSON 并保持收窄语义，但本地 completion-policy validator 正确因 action 为
null 而拒绝。Turn 最终以 `FAILED / AGENT_MODEL_CALL_REJECTED` 关闭，没有 Delivery Authorization。问题不是 Source、route、网络、format
repair allowlist 或 Application completion enforcement；最早偏差是 Reviewer 混淆“caller 直接执行该调用表达式”与“callee 的实现/动态语义”，
随后错误选择 evidence-gap remediation。

## Evidence and first divergence

- Conversation 为 `conversation_21f6725c1dc945da8bd1cfd558bb9f1d`。失败页保留 Evidence Package
  `agent_evidence_package_498619894f9049279bca0278a937aada`、Answer
  `agent_answer_c8565d416a5c48478d70f41e84891757` 与 fresh Review
  `agent_review_e9a2f0eade45459db58b2a24089091cf` identity，但 Citation 为 0、Delivery Authorization 为 `NOT PRESENT`，不能追认为答案交付。
- `model_call_6475b13ac5014705a7750b9415aedcba` 形成首份 evidence-bound Draft；
  `model_call_f9242f4ea0b74d519956674d7e0c9118` 的 Review 触发同包 rewrite；
  `model_call_e30cb2fce66342d590c3f78858a29507` 加入 Controller Claim 并改写正文。第二次 Review
  `model_call_d068a16d3c214346b590c4050c450d30` 的 assessment/Finding binding 不一致，唯一 contract repair
  `model_call_3ed0c49f5d1d495889043ff25bb7b82e` 保留了 global `requires_evidence=true` Finding；这就是 first divergence。
- `model_call_9969239e8ee34c24a2b2cfe5792ff4b6` 在 `tool_action_required=true` 时仍返回 Draft，并因 character 9377 的未转义
  control character 首先被分类为 `JSON_SYNTAX_ERROR`；`model_call_6df0621a63dc40eca2e042de5d179bbc` 修复 JSON 后仍为 action null，故
  Application 以 closed completion policy 失败关闭。不能增加第二次 repair 或绕过强制 action 来追认该 Draft。
- terminal receipt digest
  `sha256:b576e34ff14629aa8b1d6e2600e7d924dfc15f2bb2e1b5864706bee7a29afb90` 密封 Conversation/Turn `1/1`、Ark
  dispatch `12`、DeepSeek dispatch `0`、request retry `0`、human approval request `0` 与 Production `NOT_EXECUTED`。

## Classification and disposition

这是 `system-contract`：修复任何语言、框架、工程、方法或调用表达式的 evidence/review 边界，不按 mall、登录、Spring Security、
`getAuthorities` 或具体 Finding code 特判。

1. Primary 与 Reviewer 都必须区分 caller expression 和 callee semantics。直接包含 call expression 的 current Source 行只直接支持“caller
   调用了该表达式”以及源码可见的局部顺序；它不支持 callee 实现、动态目标、返回语义、类型继承或外部副作用。Draft 只陈述前者并把后者
   明确留在 evidence boundary 时，Reviewer 不得因已声明未知的后者拒绝它。
2. Reviewer 对每个 Finding 独立选择 remediation：只有 current Package 缺少当前 User Message 真正要求的 material fact，且删除或收窄会让
   该要求仍未回答时，才可设 `requires_evidence=true`。若用 current Package 删除、收窄、限定或重组 offending statement 即可保留全部已支持
   的 requested conclusions，则必须为 false。Finding 自己给出这种 existing-Package correction 时不得同时要求新 Evidence。
3. Application 对 `requires_evidence=true` 的机械行为不变：standard successor 仍必须 tool action、Draft domain 仍为空；Primary 忽略它、JSON
   syntax repair 后暴露其他 contract defect、唯一 repair 耗尽时仍失败关闭。本修复不让 Application 解析 Finding 文本、自动降级 boolean、
   追认失败 Draft、增加 repair、改换 route 或扩大 Source authority。
4. 修复沿用 current `conversational-engineering-agent@8 / conversational-engineering-agent-no-tools-prompt@8 /
   ENGINEERING_AGENT_PRIMARY_INPUT@8 / ENGINEERING_AGENT_REVIEW_INPUT@2` 协议族；每个具体 dispatch 继续由修复后的 exact prompt/input digest
   区分。closed schemas、Tool catalog、预算、Provider adapter 与 qualification identity 不变。

确定性 Model suite `23/23` PASS：Prompt contract Case 同时固定 caller-call/callee-semantics 区分、existing-Package rewrite 与真正 evidence gap
的互斥选择；既有 `requires_evidence=true` 强制 Tool action 和 `requires_evidence=false` 同包 rewrite 行为不放宽。该本地证据外部 dispatch 为
0，不追认 run-066。fresh Browser successor 必须使用新的 clean exact product/run identity 重新开始固定三轮链，问题 4/5 继续 unseen。
