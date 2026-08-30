---
id: FINDING-010-195
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, knowledge, quality]
depends_on: [FINDING-010-181, FINDING-010-192, FINDING-010-194, ITER-010-PDR-012]
code: [src/software_world_model/application_services/engineering_question_cognition.py]
tests: [tests/test_engineering_question_cognition.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: remove-structural-common-and-weak-tail-noise-from-cognition-relevance
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-195：Cognition relevance 被结构值、公共路径词和弱尾部命中污染

## Observation

继续审计 run-076 第一个角色重分配问题的 exact World Model SUPPORT 后发现，32 个 affirmative item 中混入
`PmsProductServiceImpl.create/update → relateAndInsertList` 商品服务事实。原 relevance tokenizer 遍历 statement 的全部 JSON value，
因此 `kind=STRUCTURE_RELATION` 自身贡献 `structure/relation`，`mall-admin/...` 的公共模块路径让几乎所有 Java item 贡献
`mall/admin`，英语连接词 `and` 又能前缀命中 `relateAndInsertList`。排序器随后接受任何正分或前缀分，直到 32-item 上限；去除第一层
污染后，较弱的 `controller/new/relation` 组合仍会把营销 Controller 和通用 Role Controller 填入尾部。

这不是 mall、角色题、类名或业务词特判，而是 query relevance 把 representation metadata、cohort-common context 和弱 lexical tail
误当成问题证据。

## Evidence and first divergence

- run-076 exact Primary evidence need 为角色重分配 HTTP 入口、旧关系清理、新关系写入、权限刷新和时序保证；污染 item 只因公共
  `mall`、结构 discriminator `relation`、连接词 `and` 与 `insertion`→`insert` 前缀取得正分。
- 正式 Snapshot、Capability Manifest、Eligibility Assessment 和 SUPPORT/BOUNDARY 分区均未改变 item 内容或 authority；最早偏差位于
  Application-owned multi-Profile query projection 的 relevance ranking，在 Agent 读取 SUPPORT 之前。
- 修复后对 run-076 原 Session artifact 和原 evidence need 做零外调 exact replay：affirmative candidate 从 32 收敛到 14；
  `PmsProductServiceImpl`、`SmsHomeNewProductController`、`SmsFlashPromotionProductRelationController`、`UmsRoleController` 均为 0；
  `updateRole` identity 2、`UmsAdminServiceImpl` 1、`UmsAdminController` 3，并保留角色关系 insertion 与 cache 相关 item。
- 当前 Structure Profile 对 `updateRole` implementation 仍声明 incomplete，replay 没有把旧关系删除伪装为完整 cognition；该细节仍须由
  Source Broker/Worker 的 exact-revision READ 补证。

## Classification and disposition

这是 `system-contract / systemic` Finding。current query projection 采用以下通用规则：

1. JSON field name 从不参与匹配；schema/discriminator、entity/modality/disposition/completeness/resolution/revision 等表示层 value 也不参与。
2. `source_path` 只贡献 basename，不让 module/package path 的公共前缀给整个候选 cohort 增权；正式 locator、Citation 和 Source target
   identity 不变。
3. 英语 function token 不作 anchor；在超过候选 cohort 一半 item 中出现的 exact query token 不作 discriminative anchor。若没有任何
   discriminative token，确定性回退到原 query token，避免无条件空投影。
4. exact match 权重继续为 4、bounded prefix match 权重为 1；存在至少两个 exact anchor 时不接纳 prefix-only item，并只保留达到本次
   strongest score 75% 的相关尾部，再执行既有 deterministic digest tie-break 与 item 上限。
5. 这些规则只改变问题相关 projection，不改变 Snapshot、Read Authority、Coverage/Unknown、Support reference、Source 权限或 fuse。

认知单元测试 `10/10` PASS；含 Tool、Model、Agent、Conversation、Browser、Candidate、Session 的相邻组合 `102/102` PASS；run-076
exact artifact replay 如上，外部 dispatch 0。fresh Browser Delivery/Review 与异质质量比较仍待验证。
