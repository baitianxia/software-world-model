---
id: FINDING-010-201
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, knowledge, ai, quality]
depends_on: [FINDING-010-195, FINDING-010-200, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/engineering_question_cognition.py]
tests: [tests/test_engineering_question_cognition.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: retain-bounded-direct-relation-endpoint-entities-in-query-relevant-cognition
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-201：run-079 的关系事实进入 SUPPORT，直接端点 Entity 却被全局相对分数截掉

## Observation

fresh Browser `run-079-mvp-experience` 绑定 exact product
`cd3fbcb65904e155dd28a7daaf22d6810cefc700 / 4765646bfa791f5b9fd0acb7ab45d5687ff0b3ac` 与 mall exact Source
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7 / 047d79d8588b76013c260f3f1a9565707301a60a`。第一题询问后台用户角色重分配，首个
Ark call 正常完成 World Model query。第二个 call 的 `action` 同时缺少 `operation`，并把 `UmsAdminServiceImpl` 作为首次 Source query；
唯一 same-profile repair 正确补回 `operation=SOURCE_SEARCH` 且机械保留已有字段值，随后 Application 因 query 不在 sealed cognition target
闭集而拒绝，Turn 以 `FAILED / AGENT_MODEL_CALL_REJECTED / STRUCTURED_OUTPUT_INVALID` 关闭。

## Evidence and first divergence

- World Model SUPPORT 已包含 `UmsAdminServiceImpl.updateRole` call site 到 `UmsAdminServiceImpl.getCacheService` 的 typed
  `CALL_SITE_TARGETS` relation；该 relation 是当前问题的直接行为证据，不是模型猜测。
- 同一 exact Snapshot 中存在 `getCacheService` 的 `STRUCTURE_ENTITY_STATE`，带 canonical
  `mall-admin/src/main/java/com/macro/mall/service/impl/UmsAdminServiceImpl.java` 与 exact revision；但 query relevance 的全局 strongest score 为
  13、75% cutoff 为 10，该 endpoint Entity 只得 8 分，因而没有进入 13-item SUPPORT。
- 由 SUPPORT 派生的首次 Source target 闭集只有 `UmsAdminCacheServiceImpl / UmsAdminRoleRelationDao / UmsAdminCacheService /
  UmsAdminController`。raw output 虽从 typed relation 精确复制了 `UmsAdminServiceImpl`，仍不在可执行 copy domain；shape repair 按 current
  合同不得改写这个既存值，也不得增加第二次语义 repair，最终拒绝是正确的下游行为。
- first model defect 是一个输出同时含 missing field 与 closed-domain value violation；first systemic divergence 更早，位于
  Application-owned cognition relevance：它允许 selected relation 脱离其已有证据的 direct endpoint Entity，使合法 relation literal 无法形成
  trusted cognition→Source navigation target。
- 对 run-079 exact artifact、原 User Message 与原 evidence need 做零 Provider replay 后，query-relevant affirmative item 从 13 增至 17；
  target literals 新增 `UmsAdminServiceImpl`，绑定上述 exact path/revision，且不恢复商品、营销或通用 Controller 弱尾部。
- `run-079` terminal 密封 4 Conversation、5 Turn、Ark 21、DeepSeek 0、retry/人工审批/Production 0；Ark 全部 TLS/credential/HTTP 成功，
  DeepSeek 0 是 preferred route 持续可用的正确结果，不是 fallback 不可用。terminal receipt digest 为
  `sha256:4c43104b87ddf7ab0f344e483e6dbdb9bcb6ecb1f92affb27b8eaac0592eb808`，terminal file SHA-256 为
  `cc9f4be275f6804eff237e3b24ad4725145bba82f5c4647f065c73659b6aa2f7`。

## Classification and disposition

这是 `system-contract / systemic` Finding；修复不按 mall、角色、类名、方法名、问题文本、语言或 Provider 特判，也不放宽 closed repair。

1. query relevance 仍先执行 `FINDING-010-195` 的 semantic-value、cohort-common、prefix 与相对分数规则；词法弱尾部不会因此重新取得
   SUPPORT。
2. 对每个已经入选的 typed `STRUCTURE_RELATION`，排序器在剩余 item/byte bound 内立即附加 current Snapshot、same revision 中可直接按
   `subject_entity_root_id / object_entity_root_id` 解析的 Entity state，并按 relation 的 subject→object 顺序与 digest 去重。这是 direct graph
   closure，不递归邻居，不从名称猜 path，也不改变 Snapshot、Read Authority、Coverage、Citation 或 Source 权限。
3. endpoint Entity 仍须已有 Snapshot evidence；缺失、无 evidence 或超出 bound 时保持 Unknown/截断，不补造。它携带的 verified
   declaring type/source path 只参与既有 cognition Source-target projection，仍不授予 READ authority，Broker 继续重验
   Profile/allowlist/revision/fuse。
4. closed-shape repair 的 one-attempt、existing-value restoration、无语义扩张和无第二 repair 合同保持不变。Cognition 单元 `12/12`、相邻
   Source/Tool/Question 组合 `81/81` PASS，外调 0；fresh exact Browser successor 仍须验证第一题真实 Delivery/Review，run-079 不取得质量或
   MVP PASS。
