---
id: FINDING-010-079
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, quality, security]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-077, FINDING-010-078, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py, scripts/docs.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py, tests/test_engineering_qa_live.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: require-per-entry-material-effect-scan-exact-rewrite-observation-coverage-and-exact-challenged-claim-binding
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-079：run-029 暴露副作用漏审、rewrite observation 丢失与 Finding Claim 错绑

## Observation and evidence

`FINDING-010-077/078` 的处置形成 clean product commit
`e0ad3c88bab16b44cdb01646440e5444213a56ad` / tree
`23c13f3599f98cd35ea243b0605639fbca233a32`。从该 candidate 与 exact mall
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` 启动的 run-029 先执行 fresh DeepSeek Conformance 2/2 PASS；Result digest 为
`sha256:e4050a5e46d5f7e6a0e1ea1870a13d8920f9ebcfc8e2a056b23ca30e51b66883`。持续 Alpha 的 Session Authority digest 为
`sha256:c220e4212e2139b28884b0476e2c1d0671d3415278e49e762241231bd33ddbd2`，三题分别使用 9/11/8 次 dispatch，共 28 次；每题一次
TLS handshake，后续分别复用 8/10/7 次连接，retry 0、Provider switch 0、outcome unknown 0。

三个 Result 均不能取得答案质量 PASS：

- Q1 `engineering_result_890ecfc5030bafe3364cfe63f710063f` 被页面错误标为 `APPROVED`。完整
  `UmsAdminServiceImpl.java` 已进入 Package，但 Answer 与两个 Review 都遗漏 `login()` 调用 `insertLoginLog(username)`，以及 helper
  内部 `loginLogMapper.insert(loginLog)` 的管理员登录审计持久化副作用。既有 Prompt 要求 comprehensive Review 扫描副作用，仍不足以
  证明模型逐 entry 实际执行了扫描。
- Q2 安全失败关闭。初稿把 Controller 中 `getUsername()/getPassword()` 的 caller use 扩张为未挂载
  `UmsAdminLoginParam` 的字段结构；challenge 正确返回越界 Finding，rewrite 也删除了该断言，却同时丢掉 Package 中另一个安全的
  caller-getter material observation。Application 的 exact observation coverage Gate 以
  `answer claims must cover every Package material observation` 拒绝。根因是 rewrite 输入没有在靠前位置提供逐 observation 的 exact
  statement/evidence checklist，模型把“收窄一个 Claim”误作可删除该 Claim 所承载的其他安全事实。
- Q3 安全失败关闭。challenge 正确识别 Draft 把局部 authentication/authorization 决定扩张为 401/403，但多个 assessment 复用了
  Finding code，所指 Finding 的 `claim_id` 并不属于每一个对应 challenge 的 `default_claim_ids`。Application 以
  `exceeded evidence-boundary assessment must bind a Finding on one challenged Claim` 拒绝。Finding code 存在不等于 exact
  challenged-Claim binding 成立。

66,000-byte 输入通过 Browser 真实提交后在 Provider 前被本地 preview limit 拒绝，Gateway 总调用数保持 28；Browser warning/error 为
0。Gateway DB、Session、launch 与 terminal 文件均为 `0600`，clean stop 后无 WAL/SHM，terminal receipt document digest 为
`sha256:f1db9702e011b87b21434ccc3c9203479c498b695071126fe6ffa41f23b7e2ef`。Production Activation 为
`NOT_EXECUTED`。run-029 永久保持 0/3 PASS；安全失败关闭不等于答案通过，错误页面 approval 也不被追认。

## Decision and disposition

- Application 为每个被默认正文 Claim 引用的 full-content Java support entry 投影独立
  `FULL_CONTENT_MATERIAL_EFFECT_SCAN` challenge，显式要求逐 entry 检查 persistence write、audit write、cache mutation、notification
  与 external interaction。该 lead 不预判存在副作用，也不按工程、问题、类或方法特判。
- Review assessment 增加 `DRAFT_OMITS_MATERIAL_EFFECT`。所有非 `WITHIN_EVIDENCE_BOUNDARY` assessment 都必须绑定同一输出中的
  Finding，且该 Finding 的单一 `claim_id` 必须属于该 exact challenge 的 `default_claim_ids`；只有同一 Claim 同时属于每个被绑定
  challenge 时才能复用 Finding code。
- full entry 已证明、Package atomic observation 也已存在而 Draft 漏写时，Reviewer 使用
  `REWRITE_WITH_EXISTING_EVIDENCE`。full entry 已证明但 sealed Package 的 atomic observation 缺失时，Reviewer 同时记录
  Application observation omission，并以 `INVESTIGATE_MISSING_EVIDENCE` 派生 successor gap delta；Verification 可复用 predecessor
  support，不需要伪造新 Source 权限或重复读取，后继 Package 必须重新 Answer 与双 Review。
- Answer role input 在原问题和大对象之前投影 exact `material_observation_coverage_contract`：列出每个 required observation ID、原子
  statement、kind、checklist 与全部 required Package evidence entry。初答和 rewrite 都必须在默认正文恰好覆盖每项；收窄一个不安全
  推断不得删除另一个有支持的 observation。
- Strategy/Prompt/Review output identity 升级为
  `engineering-qa-adaptive-investigation-local-contract@22` /
  `engineering-qa-adaptive-investigation-prompt@32` / `engineering-qa-review@7`。新增确定性恢复链证明 material-effect omission 可形成
  successor Package 并进入最终答案；错绑到同一 Draft 中其他合法 Claim 仍失败关闭。focused 三模块 79/79、Engineering QA 九模块
  116/116 PASS；扩展 docs/oracle/full deterministic Gate 与新 clean/fresh live 由后续 verification Finding 记录。
- ITER-010 保持 `REWORK`，`V-ANSWER-REWORK-001` 继续 blocking；run-028 与 run-029 都不追认，Slice2/3、hidden、Acceptance 和
  Production Activation 状态不变。
