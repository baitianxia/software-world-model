---
id: FINDING-010-077
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, quality, security]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-075, FINDING-010-076, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py, tests/test_engineering_qa_live.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: require-exact-per-challenge-scope-assessment-before-answer-authorization
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-077：fresh challenge 仍可跳过已投影 lead，最终授权必须验证逐项 scope assessment

## Observation and evidence

`FINDING-010-075/076` 的处置形成 clean product commit
`f832ceb7f8dfcdfdb0d8fabb6e5b5a6214e3f5bf` / tree
`50fb93e2ce2ad22cf33ec0415da8f5d68512fe82`。run-028 对 exact mall
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` 执行 fresh DeepSeek Conformance 2/2 PASS；Result digest 为
`sha256:52b6f2b6739b489bfacc131324ff2124d67c2d40e6015b58dad6b09dc9ba3689`。同一持续 Browser 会话三题分别使用
9/9/8 次 dispatch，共 26 次；retry 0、Provider switch 0，每题各一次 TLS handshake，后续分别复用 8/8/7 次连接。66,000-byte
输入在 Provider 前拒绝且 Gateway 调用数保持 26；服务继续 READY，Browser warning/error 为 0，全页 screenshot 为 177,734 bytes。
Session、launch、Gateway DB、terminal 文件均为 `0600`，clean stop 后无 WAL/SHM；terminal receipt document digest 为
`sha256:b199e6c9346c032490c16633643d068ae6fe0a06ae17c797afb121bcd92afc76`，Production Activation 为 `NOT_EXECUTED`。

Q1 `engineering_result_347a96a5e52b2146fad2ebcc973fe861` 的登录主链，以及 Q3
`engineering_result_4b0ff46ab1f0a9800569b993ff20e9ca` 对 token extraction/validation、SecurityContext、dynamic authorization
三个检查面的区分均可由授权 full-content Source 核对；Q3 还明确保留未挂载 entry-point/denied-handler 输出与最终 HTTP status mapping
为未知，独立复核为 PASS。

Q2 `engineering_result_15123f1a66227fdc795ce1380df5fd2f` 虽正确保留 `${jwt.tokenHeader}` / `${jwt.tokenHead}` 的具体运行值、
JWT secret、端口与数据库连接为未知，却仍把 Controller 中只可见的 `umsAdminLoginParam.getUsername()` /
`getPassword()` caller use 写成“`UmsAdminLoginParam`（包含 username 和 password）”。未挂载 DTO implementation，因此该证据只能证明
Controller 接收该参数类型并调用两个 getter，不能证明 DTO 存储同名 field、接受同名 wire property 或声明相应 validation。

raw challenge input 已精确包含 `MENTIONED_APPLICATION_TYPE_WITHOUT_MOUNTED_IMPLEMENTATION` lead、受影响 Claim、qualified type、
importing entry 与“caller only proves relationship”规则；fresh challenge Reviewer 仍把同一句断言复制进
`independent_material_observations`，五项全 PASS、Findings 为空。由此可排除 lead 投影、focus 顺序、fresh context 或 Gateway terminal
transition 缺失：根因是 closed Review output 只要求综合 observation/Findings，没有要求 Reviewer 对每个投影 lead 留下可机械核对的逐项裁决；
finding-free 不能证明所有 challenge 都被实际比较。

## Decision and disposition

- `evidence_boundary_challenges` 成为 Application-owned typed value；每项由 kind、相关 Claim、Package entries、受控 rule 与稳定
  `challenge_id` 密封。Strategy 只投影该同一 Domain value，Application 在 Review accept 与 Authorization 时重新计算，避免模型或
  Adapter 自报 challenge 集合取得权威。
- Provider Review closed output 新增必填 `evidence_boundary_assessments`。`COMPREHENSIVE` 必须为空；
  `EVIDENCE_BOUNDARY_CHALLENGE` 必须对 required challenge ID 恰好逐项返回 `evidence_boundary`、`draft_scope`、
  `WITHIN_EVIDENCE_BOUNDARY / DRAFT_EXCEEDS_EVIDENCE_BOUNDARY` 与 nullable/bound `finding_code`。漏项、重复、未知 ID、首审提前处置均在
  Application 授权前失败关闭。
- `DRAFT_EXCEEDS_EVIDENCE_BOUNDARY` 必须绑定同一输出中作用于该 challenge 相关 Claim 的真实 Finding；缺失或错绑失败关闭。
  最终 Authorization 除既有五项质量、omission 与 empty Finding Gate 外，还必须验证 exact challenge-ID 集合完整且所有 disposition
  都是 `WITHIN_EVIDENCE_BOUNDARY`。
- Prompt 明确要求分别写出证据最大范围和 Draft 实际断言范围，禁止把 Draft 原句复制为“独立观察”代替比较；caller getter 只证明
  method invocation/use，不证明未挂载 type 的 field、wire property 或 validation。该规则对工程、问题、语言、类名和 getter 名均无特判。
- Strategy/Prompt/Review output identity 升级为 `engineering-qa-adaptive-investigation-local-contract@21` /
  `engineering-qa-adaptive-investigation-prompt@31` / `engineering-qa-review@6`。focused 三模块 78/78、Engineering QA 九模块
  115/115 PASS；扩展 docs/oracle/full deterministic Gate 与新 clean/fresh live 由后续 verification Finding 记录。
- run-028 永久保持 Q1/Q3 PASS、Q2 FAIL；页面 `APPROVED` 不被追认。Production Activation 继续不执行。
