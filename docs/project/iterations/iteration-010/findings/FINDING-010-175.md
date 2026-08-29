---
id: FINDING-010-175
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai-infrastructure, application, quality]
depends_on: [FINDING-010-173, FINDING-010-174, ITER-010-PDR-012]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: exact-repair-copy-and-draft-claim-closure
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-175：shape repair 改写既有语义，正文未枚举结论又绕过 Reviewer

## Observation

fresh `run-065-mvp-experience` 绑定 exact product
`9f829266847297346e6c9e93bfde21cd43a971ab / eb3dcede5179611867050741aabb5eb9fd50d46a` 与 mall exact Source
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7 / 047d79d8588b76013c260f3f1a9565707301a60a`，用于验证
`FINDING-010-174` 的 bounded complete shape diagnostic。

Turn 1 以 12 次 Ark dispatch 形成 `SUCCEEDED / ACCEPTED`，页面显示自然答案、37 个 Citation、fresh Review 和 Delivery Authorization；
两个 Source Citation 可展开 exact revision、modality、content/citation digest。但用户要求从 HTTP 入口开始且每个关键结论有
exact-revision 源码证据，Agent 没有读取 `UmsAdminController.login` 方法体。Draft 多处诚实报告该边界，随后又在“完整调用链总结”中肯定
写出 `Controller 调用 UmsAdminServiceImpl.login(username, password)`。该肯定句没有进入 `draft.claims`，因此也没有直接 current SUPPORT
绑定。

第一次 independent Review 实际返回 `CONTROLLER_DELEGATION_EVIDENCE_GAP`，但把它错误绑定到只声明 Controller 方法签名、且 assessment 为
`SUPPORTED` 的 Claim 0；本地 decoder 因 SUPPORTED Claim 不能携带 Finding 而正确拒绝。唯一 `CLOSED_OUTPUT_CONTRACT` repair 保留了另一个
JWT 算法 Finding，却删除 Controller 全局缺口，而没有把它改为 `claim_index=null`。后续重写仍在正文总结断言该 delegation、仍未把它加入
claims；最后 fresh Reviewer 只批准 10 个枚举 Claim，遗漏了正文中的物质肯定结论。

Turn 2 的 initial Primary 输出又把 `SOURCE_READ` argument 写成 `{"locator_reference": ...}`，而 closed schema 要求
`{"name":"locator_reference","value":...}`。`FINDING-010-174` 的新 diagnostic 正确一次定位
`$.action.arguments[0]`、投影 `allowed_exact=[name,value]`、`missing=[name,value]` 与 `unexpected_count=1`；repair 也补对 action shape。
但 repair 同时改写 `audience`、`action.evidence_need` 和多个 `open_items/plan` 文本，机械语义守恒因此正确拒绝，Turn 在 Tool、Package、
Answer 或 Review 前以 `AGENT_MODEL_CALL_REJECTED` 失败关闭。

## Evidence and first divergence

- Turn 1 的 Evidence Package/Answer/Review 分别为
  `agent_evidence_package_89f0e7f347414b4aa6d7c2eacb62a9da`、`agent_answer_9299491359db4b3ab477195b2c93c420`、
  `agent_review_fa8069eeba744c4ea15e332985fe744a`；Delivery Authorization digest 为
  `sha256:570502caa337ae86cf956aa2a55c324a122fb081ba06b6b44fa1440bd9277608`。
- Turn 1 Service/JWT Source locator 分别是 `source_locator_5603c3dce4fec1a52073e96da0d69c2a` 与
  `source_locator_dd34d84826314fda1b541773bde17140`，content digest 分别是
  `sha256:98b14479b35c90f9134f2343a180bdd437d19d1cb8130c242371baded3be8e94` 与
  `sha256:a4ea1ad6f887720a6006cd2512c070d8c397133d540a73467304def47efa262e`。没有 Controller full-source Citation。
- 首次 Reviewer/其 contract repair call 为 `model_call_3cde1be744f349e9b120da9a43e6e1ee` 与
  `model_call_c5289d08c21d4a7db7d1bed73ae8b330`；final Reviewer call 为
  `model_call_1f94f3e2086849ec8cc6310c01c51752`。first divergence 是 Primary 把未绑定的 material affirmative statement 写入正文；首个
  Reviewer 已发现但 contract repair 丢失全局 Finding，final Reviewer 又未做 content-to-claim completeness 检查。
- Turn 2 initial/repair call 为 `model_call_547828fb02754c67804a111b74d5782b` 与
  `model_call_1da7bca47635496596ee9fc563e9a053`。diagnostic 已正确，first divergence 是 repair 没有按字节保持已存在 allowlisted values；
  Application guard 正确失败关闭，不应放宽。
- terminal receipt digest
  `sha256:597f9189cfe745c5acc970385b858dcf57e898ecd2f0e905471485c0f268b106` 密封 Conversation/Turn `1/2`、Ark
  dispatch `14`、DeepSeek dispatch `0`、request retry `0`、human approval request `0` 与 Production `NOT_EXECUTED`。

## Classification and disposition

这是 `system-contract`：修复任意 closed-shape repair 与任意自然语言 Draft/Review，不按工程、问题、字段值、Controller 或登录关键词特判。

1. `ENGINEERING_AGENT_OUTPUT_PREFLIGHT@4` 在 `CLOSED_SCHEMA_SHAPE` repair 中从 untrusted prior output 与 trusted output schema
   递归投影 `existing_allowed_field_copy_projection`：只保留已经存在的 allowlisted fields/values，删除 unexpected field、保持 missing field
   缺席；nullable union、本地 `$ref` 与 array item 使用同一 schema traversal。投影不授予事实、语义或 Tool authority。
2. Primary/Reviewer 必须逐值复制 projection 中的 primitive value 和 array 长度/顺序，禁止改写或释义；唯一允许的 mutation 仍是增加 missing
   allowlisted field 与删除 unexpected field。Application 原机械守恒 guard 不变，repair 次数仍为 1。
3. Primary 的 `draft.claims` 必须覆盖 `draft.content` 中每个 material affirmative conclusion，包括 summary/table/diagram/code comment 中的
   重复陈述；一处 boundary caveat 不能授权另一处继续肯定未知关系。Reviewer 必须先做完整 content-to-claim coverage；未枚举的物质肯定结论
   形成 `claim_index=null` 的 global completeness Finding。`CLOSED_OUTPUT_CONTRACT` repair 不得仅因 claim binding 错误删除真实缺口；对未
   枚举正文结论应保留 Finding 并改用 null binding。

确定性 Model suite `23/23` PASS：Case 证明 parent/nested mismatch 的 exact-copy projection 不含 unexpected names、保留合法值与 array
顺序、允许按模板补 missing fields；既有语义漂移负测仍失败关闭；Reviewer decoder 接受“所有枚举 Claim 均 SUPPORTED + 一个
`claim_index=null` 全局完整性 Finding”。相关 Agent/Tool/Model/routing/Browser/candidate/launcher/runtime/artifact/CLI/Gateway 组合
`114/114` PASS；文档检查 `581` 份 current documents PASS。外部 dispatch 为 0；该本地证据不追认 run-065。fresh Browser successor
必须使用新的 clean exact product/run identity 重新开始固定三轮链，问题 4/5 继续 unseen。
