---
id: FINDING-010-173
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai-infrastructure, application, quality]
depends_on: [FINDING-010-168, FINDING-010-170, FINDING-010-172, ITER-010-PDR-012]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: exact-output-allowlist-repair-and-direct-evidence-inference
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-173：闭域 repair 不知道应删除哪个输入字段，Reviewer 又放行间接类型推断

## Observation

fresh `run-063-mvp-experience` 绑定 exact product
`4dd20755833482fd1356dac761c0357f693f9e4d / cfcba8bd02c7a5ceb024716656a5d0111643ced9` 与 mall exact Source
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7 / 047d79d8588b76013c260f3f1a9565707301a60a`，用于复验
`FINDING-010-172` 的固定三轮 Browser 链。

Turn 1 以 6 次 Ark dispatch 形成 `SUCCEEDED / ACCEPTED`，页面交付自然答案、2 个 full-resource Source Citation、fresh Review 和
Delivery Authorization。Turn 2 以 10 次 Ark dispatch 形成 `SUCCEEDED / ACCEPTED`；其中
`UmsAdminServiceImpl.java` 在 Turn 1/2 的 Citation content digest 都是
`sha256:98b14479b35c90f9134f2343a180bdd437d19d1cb8130c242371baded3be8e94`，但 current-Turn locator 分别是
`source_locator_d222b8c61dca4e0d8dd6fa9ca892c298` 与 `source_locator_7dc979a3b9d7f6e73c51085c7db96c39`。Browser 可展开第二轮新
Citation 的 exact revision、modality、content/citation digest。这真实证明上一轮 full-source identity 只作为 locator candidate，本轮实际 READ
后重新形成 current SUPPORT/Citation；旧 Answer/Observation 没有被当作事实复用。

但 Turn 2 答案又声称：因为 `Asserts.java` 的 package/import，`ApiException` 就不是 `AuthenticationException` 的子类且不会被 catch；同一
答案同时承认本 Turn 没有读取 `ApiException` 的完整继承关系。该推断没有被其三个 Citation 直接支持，fresh Reviewer 却把 7 个 Claim 全部
标为 `SUPPORTED`。`Asserts.fail` 位于 `insertLoginLog` 前，故“密码错误不会持久化 UmsAdminLoginLog”的核心结果不依赖这个未知继承关系；
正确行为应收窄结论，而不是扩写无据的 catch coverage。

Turn 3 接受用户对“登录日志 = UmsAdminLoginLog 持久化”的明确纠正。sealed Primary input 已含三个
`PRIOR_TURN_EXACT_SOURCE_REVALIDATION` option，包括目标 Service full source。初始输出与唯一 same-profile repair 输出都多写一个
input-only `work_state_ref` 顶层字段；本地 validator 正确给出 `CLOSED_SCHEMA_SHAPE`，但旧 bounded diagnostic 只有
`missing=[none]; unexpected_count=1`。为了不回显 untrusted key，它没有告诉模型哪个字段不能保留；repair 虽从 `SOURCE_SEARCH` 改为复制正确
Service revalidation locator 的 `SOURCE_READ`，仍重复 `work_state_ref`，最终在任何 Tool 执行、Evidence Package、Answer 或 Review 前以
`AGENT_MODEL_CALL_REJECTED` 失败关闭。问题不是 Source locator、route、network 或 Browser display。

## Evidence and first divergence

- Turn 1 的 Evidence Package/Answer/Review 分别为
  `agent_evidence_package_3a207952f2b34234b465c99b8411a710`、`agent_answer_2eb82708bb26467c8b81536d3b713963`、
  `agent_review_12f3b172a1f64c608ef3745eb42a7e71`；Turn 2 对应
  `agent_evidence_package_1f91ce3eadec439ab53c2f23c17856b2`、`agent_answer_e7c722013887480db68ccc3dc9989672`、
  `agent_review_6539708c2b994032a475f501af432156`。
- Turn 3 的 initial/repair Gateway call 为 `model_call_782b2191596f4946967143a173db4cc9` 与
  `model_call_ce740cb490994ad78cf23f1486efbf1f`；两份 parseable JSON 的唯一多余顶层字段均为 `work_state_ref`。repair input 绑定原 call receipt、
  untrusted prior output 与 exact diagnostic，没有 request retry 或 route switch。
- 对 Turn 2 material catch-coverage Claim，first divergence 是 Answer synthesis 的无据扩写；应阻断未阻断点是 independent Reviewer。对 Turn 3，
  first failed boundary 是 AI model closed-output shape；Application decoder 和 Browser failure projection 都正确失败关闭。旧 repair diagnostic 未提供
  trusted schema 的完整 allowlist，是同一失败在唯一 repair 中重现的最早可修复 Owner 缺口。
- terminal receipt digest
  `sha256:0eeba657acf5142f557337abed47ec5fa628d51af014d78e26010b476ead3c10` 密封 Conversation/Turn `1/3`、Ark dispatch `18`、
  DeepSeek dispatch `0`、request retry `0`、human approval request `0` 和 Production `NOT_EXECUTED`。run-063 保持失败历史，不能补写第三轮
  Answer 或继续异质问题。

## Classification and disposition

这是 `system-contract`：修复 closed output repair 与证据推断标准，不按工程、题目、类、方法、异常名或关键词增加例外。

1. `CLOSED_SCHEMA_SHAPE` diagnostic 在 mismatch path 投影 trusted output schema 的完整 `allowed_exact` field set、missing names、unexpected
   count 与 `additional_fields_forbidden=true`；untrusted unexpected key name 仍不回显。repair 必须从该 allowlist 重建 object，而不是猜测应
   保留 prior output 的哪些 input metadata。
2. Primary/Reviewer prompt 把 final preflight 的 `required_top_level_fields` 明确为 exhaustive allowlist。sealed input field 只有同名属于 output
   schema 才可输出；对 parseable closed-shape failure，Application 递归比较 prior/repair 中所有已存在的 allowlisted field，值或顺序漂移即
   失败关闭，只允许补 missing field、删 unexpected field。Application 仍不规范化或追认 invalid output，唯一 repair 耗尽后仍失败关闭。
3. Primary 与 Reviewer 都不得只凭 path/package/import/symbol/caller syntax 推断类型关系/catch boundary、数据库约束、运行时配置值或外部
   副作用。必须有 current Evidence 直接声明/执行该关系，或把结论收窄为不依赖未知关系的结果；Reviewer 对 material violation 返回 Finding。
4. 修复沿用 current `conversational-engineering-agent@8 / conversational-engineering-agent-no-tools-prompt@8 /
   ENGINEERING_AGENT_PRIMARY_INPUT@8 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@3` shape family；closed output schema、Tool domain、权限、预算、
   Provider adapter 和 route 不变，每次 call 仍由新的 exact prompt/input/request digest 区分字节。

新增确定性 Case 覆盖一个 input-owned identity 混入 root output：diagnostic 只显示 trusted exact allowlist，不泄漏 unexpected name；fresh
same-profile repair 按白名单返回合法 Proposal；另一 Case 让 repair 改写既有 goal，机械语义守恒检查在 Proposal 前拒绝。Model suite
`23/23` PASS，相关 Agent/Tool/Model/routing/Browser/candidate/launcher/runtime/artifact/CLI/Gateway 组合 `114/114` PASS；全部是本地证据，
外部 dispatch 为 0。这些测试不追认 run-063。fresh Browser successor 必须使用
新的 clean product/run identity 重跑固定三轮；问题 4/5 继续保持 unseen。
