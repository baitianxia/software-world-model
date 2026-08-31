---
id: FINDING-010-252
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai, quality, operations]
depends_on: [FINDING-010-251, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: exact-inline-code-anchor-reference-coverage
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-252：run-123 将正文技术锚点绑定到不蕴含该语义的 Claim

## Observation and execution evidence

clean product commit/tree
`71033a504c7096011fb491443f9cfe50264a0fff / 53577296c7c002df93895c183724039fbb852570` 上，fresh Ark qualification
`ccrun_897b4a77935f454d9665e613bcda3151` 以 actual `glm-5.3`、13/13 cases、TLS/credential/HTTP `2/2/2`、retry/unknown 0
通过；result digest 为 `sha256:7d37ff511cf3bc62645cde231702d0b781556f1ef76e551c10fb8bde813d2038`。

run-123 的第一次本地 preparation 在 listener bind 前被 sandbox 以 `Operation not permitted` 拒绝；当时两个 Gateway 的 root/revision/output/
failure/isolation rows 均为 0，零 dispatch launch evidence 已移入该 run 的 `sandbox-preparation-failed/` 保留，未删除或重放请求。随后同一 sealed
Session 在获准的 sandbox 外启动。页面 Q4 形成 `SUCCEEDED / ACCEPTED`、6 Citations、fresh comprehensive/focused Review 与 Delivery；Ark
10 个 calls 全部 `COMPLETED`，TLS/credential/HTTP `10/10/10`，DeepSeek dispatch、request retry、pre-dispatch failure 与 post-dispatch
unknown 均为 0，Production 未执行。terminal digest 为
`sha256:00be33c5e07aecddc5cee2f79ebaff2bd21c284c95aa79dc1ac0a8d1c20c9b90`。

`FINDING-010-251` 的新协议在本次运行中确实投影并审核了 final Draft 的 26/26 exact content units；第一次 comprehensive Review 还通过
`F_UNIT15/F_UNIT20` 找到并驱动删除了两个未绑定/过宽正文语义。这证明完整 unit 集合已经进入 Review，而不是继续绕过结构审核。

独立审核仍判定 Quality FAIL。final content unit 19 声称
``EsProductDao.getAllEsProductList` 的 SQL 与结果映射实现位于 `src/main/resources`（被排除路径）``，却绑定 Claim 3 与一个 WORLD_MODEL
Boundary：Claim 3 明确只说 Dao API 声明“不证明 SQL 或映射实现的位置与内容”，Boundary 只报告 mall-search 超出一个 Profile root 和行为维度
覆盖缺口，两者都不建立该实现位于这个路径。Reviewer 仍把 affirmative location 与后半句 uncertainty 合并判为 `COVERED`。同一 final
Review 还把正文的 ``CommonResult.failed()``、``EsProductDao.getAllEsProductList`` 与 ``EsProductRepository`` 技术锚点分别绑定到没有逐字
包含这些 exact anchors 的较窄 Claim。于是“每项有 assessment”仍不等于“assessment 引用的 Claim/Boundary 实际包含正文的技术对象”。

## Exact first divergence

`content_coverage_assessments` 只密封 content-unit index 与 Claim/Boundary IDs。Application 能验证引用域、顺序和 disposition shape，却没有一个
可机械验证的必要条件来证明正文中的 exact technical anchor 至少存在于所映射 reference。Reviewer 因相关 identifier、同主题 uncertainty 或
邻近 Claim 而给出错误 mapping 后，Application 无法区分 exact entailment 与关键词重叠。

这是通用 presentation-to-reference anchor 缺口，不是 mall、Dao、Elasticsearch 或 resources 特判。任何答案都可能在 Markdown inline code
中加入一个路径、symbol、method、declaration、route 或 literal，再把该 unit 绑定到只包含相邻概念的 reference。

## Decision and disposition

1. 每个 `COVERED` content unit 的 Markdown inline-code span 是 exact technical anchor。Application 必须按出现顺序去重，并要求每个 anchor
   逐字存在于至少一个 mapped Claim statement 或 mapped exact Boundary observation content；一个都不命中即失败关闭。
2. 该检查是 semantic coverage 的必要条件而非充分条件。Reviewer 仍必须判断 category、scope、condition、certainty、negation 与 local order；
   identifier 命中不能证明语义蕴含。尤其，声称位置/效果/类别/确定性 unknown 的 reference 不能覆盖 affirmative assertion；excluded/unread
   scope 只建立未读边界，不建立实现存在于该路径。
3. comprehensive Review 对看不到 exact Boundary ID 的 unit，只能以 Claim exact-anchor coverage、合法 defer 或 Finding 闭合；focused Review
   必须在 exact Claim/Boundary domain 上闭合。decode、sealed Review 与 Delivery 分别重算，不能依赖 Reviewer 自报。
4. 违反该条件的 Reviewer output 进入 bounded fresh format-repair，只能补上真正包含 exact anchor 的 reference 或把 unit 标为 `DEFECT` 并绑定
   Finding；repair 不能修改 Draft、伪造 Claim/Boundary 或扩大 Evidence。Primary 收到 Finding 后删除 unsupported anchor、收窄正文或用合法
   current SUPPORT 增加对应 Claim。
5. 协议族升级为 `conversational-engineering-agent@37 / prompt@37 / ENGINEERING_AGENT_PRIMARY_INPUT@34 /
   ENGINEERING_AGENT_REVIEW_INPUT@26 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@31`。Review output `@10` 与 sealed Review `@5` shape 不变；route、
   Provider adapter、资格、数据披露、Source/Tool/dispatch budget、no-retry 与非 Production 边界均不改变。

## Verification

run-123-like negative fixture 让正文断言 ``Dao.load` 位于 `src/main/resources```，mapped Claim 只说实现位置未获证明、mapped Boundary 只说行为
维度不可用；decode 必须以 unmatched exact inline-code anchor 失败。domain helper 同时验证缺失 anchor 被返回、逐字存在的 anchor 通过；Review
input/preflight 密封 exact-anchor、uncertain-vs-affirmative 与 excluded-scope policy。Agent/Model/Tool 定向集合 `84/84` PASS，相邻 Slice1 集合
`184/184` PASS，658 份 current documents check PASS；计划门禁、clean commit、fresh Ark qualification 和 run-124 同题 live successor 仍须
依次完成。run-123 证明 content-unit enumeration 生效，
但因 reference entailment 仍有漏判，不取得 Quality 或 MVP PASS。
