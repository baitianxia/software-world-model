---
id: FINDING-010-217
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, source, quality]
depends_on: [FINDING-010-216, FINDING-010-200, FINDING-010-202, ITER-010-PDR-012, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/application_services/engineering_question_cognition.py, src/software_world_model/application_services/conversational_engineering_tools.py, src/software_world_model/interface/engineering_qa_source.py]
tests: [tests/test_engineering_qa_source.py, tests/test_engineering_question_answering.py, tests/test_engineering_question_cognition.py, tests/test_conversational_engineering_tools.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: bind-search-to-explicit-question-scope-and-rotate-bounded-fallback-cohort
target: SYS-CONTRACT-SOURCE-ARTIFACT
---

# FINDING-010-217：run-093 暴露普通 Source Search 重扫全局 canonical 前缀并耗尽读取预算

## Observation and execution evidence

本 Finding 使用 `FINDING-010-216` 已密封的同一 `run-093-mvp-experience` identity、Provider route、artifact digests 与 terminal evidence。
Ark 的 3 个 sealed 429 已合法触发 DeepSeek；Q2 失败和 Q5 不完整答案均发生在可用 Provider 已返回合法 tool proposal 后，因此最早偏差位于
Source acquisition，不是 Ark/DeepSeek 路由或重复人工授权。

## Exact first divergence

1. Q2 明确询问 `mall-portal`。首个 `SOURCE_SEARCH(mall-portal)` 被 Broker 以
   `SOURCE_SEARCH_QUERY_EQUALS_PATH_SEGMENT` 零读取正确拒绝；后续 `createOrder` Search 从全 SOURCE class 的 canonical 开头扫描 56 个文件
   未命中。`lockStock` Search 只剩 7 个搜索槽位，却再次从同一 canonical 开头扫描，未到达
   `mall-portal/.../OmsPortalOrderServiceImpl.java`；最后 1 个 `coupon` Search 命中异域 `mall-admin` Controller。正确 service 文件在
   `mall-portal` 84 个 Java 文件的 canonical index 63，而在全 SOURCE class 约 519 个文件中约为 index 488。旧 Worker 每次 SEARCH 都从
   fallback index 0 开始，故多次合法 query 并未增加 bounded coverage。
2. Q5 明确询问 `mall-search`。`ElasticsearchRepository` Search 扫描 56 个全局文件未命中，`ProductController` Search 又扫描开头 7 个并只
   取得 Controller locator，随后 1 次 read 将 Source file fuse 精确用到 `64/64`。答案因此只说明 HTTP endpoints，并明确没有读取 service
   implementation；本地 exact revision 中 Controller/Repository/ServiceImpl 都位于只有约 11 个 Java 文件的 `mall-search` scope。
3. `FINDING-010-197` 已让 original-question exact top-level scope 约束 World Model Profile selection，却没有把同一个 sealed scope 下传给
   Source Search。Source Worker 又只记录单次 coverage，没有 Turn-level fallback cursor。这两个缺口叠加，使正确 source-native literal 仍可能在
   允许预算内重复扫描同一批无关文件。

## Decision and disposition

这是 `system-contract / systemic` Finding，不按 mall、模块名、题号、query、文件名、排序位置或测试 fixture 特判。

1. Application 从 immutable original question 与 sealed `source_allowlist` 重用 exact top-level scope recognition；当 SOURCE Search 没有更强的
   cognition exact-path scope 时，把匹配 scope 对应的完整 allowlist prefixes 作为 trusted Search-only restriction 交给 Broker。Broker 从
   original question 独立重算并要求 exact match，再重验 canonical/unique/bounded、Request allowlist、Source Profile/class 与 operation。
   scope 不是模型 argument、locator 或 READ authority；cognition exact-path scope 优先。
2. `COMPILED_SOURCE_OPERATION@3` 新增 `search_path_prefix_scope` 和 non-negative `search_fallback_offset`。Worker 始终先检查当前 query 的
   stem/name/path candidate cohort，只对 rank-3 canonical fallback cohort按 offset 做确定性环形轮转；Result 密封 requested/applied offset、
   scoped entry count 与实际 fallback file count。Application 仅以 validated current-Turn Result 的 actual fallback count推进 cursor，不能从模型
   文本、命中数或隐藏缓存推进。
3. per-search `56`、whole-Turn `64`、最后一个 exact READ 槽位、byte/action/result fuses、case-sensitive content match、Partial/Boundary、
   exact revision、allowlist 与 locator issuance 全部不变。轮转不复用旧 source bytes，不把未扫描部分称为 complete，也不提高任何预算。
4. deterministic regression 证明：显式 module scope 排除另一 module；第一次错误 literal 扫描 scoped fallback 56 个文件；第二个不同 literal 从
   offset 56 开始，在余下 7 个 Search 文件内取得 index-63 target；最后 1 个槽位完成 opaque-locator full read，累计仍为 `64/64`。Broker、
   Worker、Cognition、Tool、Agent/Model 六模块 `154/154` 与相邻十五模块 `229/229` 定向测试 PASS。

Q2 旧 trace 中 Source acquisition 之后还出现过 response-kind completion-policy 分支冲突；本次不越过最早偏差做症状补丁。fresh run-094 将验证
Source 闭合后该下游分支是否仍可达；若仍发生，将以新的 exact evidence 单独处置。run-093 保持 Quality FAIL，不能称 MVP。

该变化细化既有 Source Broker/Worker 与 Application owner，不改变组件职责，故不需要新 ADR。本 Finding 与同步后的
`SYS-CONTRACT-SOURCE-ARTIFACT`、`SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 是 current system write-back。
