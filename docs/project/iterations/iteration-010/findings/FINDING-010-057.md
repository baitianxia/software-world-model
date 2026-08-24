---
id: FINDING-010-057
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, source, ai-infrastructure, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-055, FINDING-010-056]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_model_source.py, tests/test_engineering_question_strategy.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: issue-request-attempt-profile-bound-direct-locators-for-validated-mandatory-paths
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-057：已知 exact mandatory path 仍被迫以内容搜索重新发现

## Observation and evidence

`FINDING-010-055/056` 的处置形成 clean candidate
`274e5ea23423072574bf1797ec5254def4be3903` / tree `c7875bef05b6538c0d240fa28e462d5f763d0a1c`；clean clone 的 Engineering QA
99/99 与 docs 450/450 PASS。fresh DeepSeek Conformance run-020 以 2/2 request PASS，Result
`sha256:8bf5f3b763e2e987ec796e8c1e58e890f156847dcedc07ca303c290bbec394dc`，actual model `deepseek-v4-pro`、retry 0。
同一持续 Alpha 中，原登录题以 10 次 dispatch 形成 `APPROVED` Result
`engineering_result_04d7615ff9fb358542a66a26565953ab`，默认正文覆盖入口、凭据/启用校验、JWT、SecurityContext、失败返回和登录日志。

第二题在 1 次 Question Understanding + 4 次 Initial Investigation 后以 `NO_PROGRESS_FUSE_EXHAUSTED` 失败关闭，Result
`engineering_result_ffd9cf21ff22607b82e8c211b37ba268`。Understanding 已正确选出 4 个 allowlisted exact mandatory paths；但每一轮
`eligible_locator_references` 都为空。模型先把 `mall-admin/pom.xml` 当成 `BUILD_CONFIGURATION` 文件内容搜索词，再把
`SecurityConfig.java` 当成 `SOURCE` 文件内容搜索词，两个合法 search 都返回零 item；之后再次搜索同一 POM path，两次 Proposal 被 Broker
以 `DUPLICATE_ACTION_INTENT` 拒绝并触发 no-progress fuse。审计中的 4 个 raw Investigation output、2 个 Retrieval Result、4 个 Broker
Decision 与零 unread-path 消费完整证明该失败不是余额、网络、Source 越权或总调用上限。

## Root cause

Question Understanding 选择的 mandatory path 已被 Application 验证为 immutable Request allowlist 成员，并由 Source Profile 唯一解析到一个
registered evidence class；但旧协议只允许 READ/PARSE 使用此前搜索结果签发的 opaque locator。literal search 查的是文件内容，不查文件名或
路径，因此要求模型通过内容搜索重新发现一个已经确知的 exact path 不增加任何安全权威，反而让 `pom.xml` 等内容未包含自身路径的合法文件依赖
模型猜测 artifact/symbol token。`required_evidence_paths` 与 `eligible_locator_references` 由此形成了系统性断点。

## Decision and disposition

- Source Broker 在 mandatory path 已通过 Request allowlist、Binding-scoped Source Profile 和唯一 class 校验后，为每个 path 签发
  `ENGINEERING_QA_REQUIRED_EVIDENCE_PATH_LOCATOR@1`。locator identity 绑定 exact Request digest、Investigation attempt、Source Profile
  digest、evidence class 与 path；模型只能复制当前输入中的 opaque reference，不能提供或扩大可执行 path authority；
- Initial/Verification role input 新增 `eligible_required_path_locators` 描述符并把其 reference 合并进唯一
  `eligible_locator_references`。unread mandatory path 存在时优先直接 READ/PARSE；读完后 locator 从可用集合消失。Broker 编译时重建并重验
  locator identity、proposal attempt、Request/Profile/class/path、global/class allowlist；既有 search-issued locator 与重复动作熔断保持不变；
- Broker policy 升为 `ENGINEERING_QA_SOURCE_BROKER@2`。该修复不读取新来源、不把 path 选择权交给模型，也不按工程、问题、关键词、类、方法、
  fixture 或 Oracle 特判。三模块定向测试与完整 Engineering QA 100/100 PASS；新 clean/fresh live 尚未执行，run-020 第二题永久保留为失败证据。
