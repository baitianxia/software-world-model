---
id: FINDING-010-223
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, source, quality]
depends_on: [FINDING-010-222, FINDING-010-217, ITER-010-PDR-012, SYS-CONTRACT-SOURCE-ARTIFACT]
code: [src/software_world_model/interface/engineering_qa_source.py]
tests: [tests/test_engineering_qa_source.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: rank-authorized-source-paths-by-java-identifier-components-before-bounded-fallback
target: SYS-CONTRACT-SOURCE-ARTIFACT
---

# FINDING-010-223：run-098 暴露完整方法 literal 无法把第 76 个实现文件带入 64-file fuse

## Observation and execution evidence

唯一 validated Engineering Chat launcher 在 product commit/tree
`658ffbbdf992fb6cf30c05553030fc09c462f394 / 56068343b42bc8b7a4ed1bf42014b3a5a2688f8e`
上完成 `run-098-mvp-experience` 的 4 个隔离 Conversation、5 个冻结 Turn，并以
`STOPPED_AFTER_DISPATCH` 正常密封。terminal 内部 receipt digest 为
`sha256:b8d70d8866ef16881809a32ac474252e812237e0e4197d772ddb978e987c7921`。

逐题 dispatch 为 `13 / 14 / 17 / 0 / 12`。Q1 为 `SUCCEEDED / ACCEPTED`；Q2 为
`SUCCEEDED / ACCEPTED`，但 12 个 Citation 全部来自无关的 `UmsMemberCouponController`，答案明确承认无法确认用户要求的订单创建顺序；
Q3 为 `FAILED / AGENT_REVIEW_LIMIT_REACHED`；Q4 为零 dispatch
`APPLICATION_INPUT_CLARIFICATION`；Q5 为
`FAILED / REVIEWER_MODEL_CALL_REJECTED / PROVIDER_OUTPUT_INVALID / STRUCTURED_OUTPUT_INVALID`。run-098 因而仍为 Quality FAIL，不是 MVP。

Ark 共 24 个 dispatch：21 completed，1 个 pre-dispatch `TLS_FAILURE / PROVIDER_UNAVAILABLE`，2 个 sealed
`429 / AccountQuotaExceeded / PROVIDER_HTTP_ERROR`；transport 为 24 次 TLS attempt、23 次 TLS success、23 次 credential resolution 与
23 次 HTTP dispatch，post-dispatch unknown 为 0。只有这 3 个 trusted-unavailable verdict 才激活 DeepSeek；DeepSeek 随后 32/32
completed，以 3 次 TLS session、29 次 connection reuse、32 次 credential/HTTP dispatch 完成，retry、人工审批与 Production 均为 0。
Q3 虽合计 17 个 dispatch，但按 Provider 分别为 Ark 3、DeepSeek 14，未超过每 Turn、每 Provider 15-call authority。

turn-scope、pricing capture、session、launch、terminal、Ark DB、DeepSeek DB 文件 SHA-256 分别为：

- `426e4fa81b7ca24b94e45187ce084e2753c9f8ef3a30251b67b8c5c16dd60a74`
- `9079a918ccdb7938a45cbb8dd8de0f4a9591f22d6ee8f8a19e2a2ad1c4d230a9`
- `3d068a7b05a27b070c80f4203a121cb9f0a3f71156e78fbbc4d46685264f1edc`
- `3ade9604d2db309f1047d12127c6f5833a59e4353335c756068ea34014fabdf8`
- `c9ab47886c00853a16738c77c8710c283693b8b535b23ab1a70a7c529aabaded`
- `2e5a75dd1060e638902ab9b35cfd803251d0f118183572df4b902be895334010`
- `683f688563c56f3acd76e6b30870b1aaca0ab6b3f1083d4affbfd7d09e0b9c6e`

public Source session authority、session runtime 与 preparation receipt digest 分别为
`sha256:043c623d3c80b436dc9972628871a1a8c2075eb14eb460140122d21681ec080b`、
`sha256:d9c99a4194f903fd4323c793e9784910e45f8739a9a8c80e6f726b3a5967cedb` 与
`sha256:a4026c701cd20887e573a6b49ef4b4b5fd0a4fb6f26a195f3e67df14d5b180b6`。official DeepSeek pricing 在
`2026-08-30T21:53:16.465Z` fresh 检查，visible-text digest 仍为
`sha256:9c9dd4d22764599ade403c0ba6cd95abcb947810d5230ee95cb96a56a62d7668`。

## Exact first divergence

Q2 原消息逐字限定 `mall-portal`，所以 current Broker 正确把 SOURCE Search 限定到该 module 的 84 个 Java 文件。首个合法
`SOURCE_SEARCH(createOrder)` 仍把 84 个文件全部列入 rank-3 fallback，因为旧 `_search_entry_rank` 只比较完整 query 与
stem/name/path；`createOrder` 并不是 `OmsPortalOrderServiceImpl` 的连续子串。第一次 Search 因而检查 canonical 前 56 个文件且零命中，
第二个 `lockStock` 只检查余下 7 个 fallback，最后一个 file slot 被 `coupon` 的 filename cohort 消耗并返回 12 个无关 Controller hits。

exact revision 的 `OmsPortalOrderServiceImpl.java` 在该 scoped canonical tree 中为第 76 个文件；`OmsPortalOrderService.java` 为第 61 个。
因此 `FINDING-010-217` 的旋转 fixture（目标位于第 63 个）只证明两次 Search 能越过 56，却没有覆盖 target 本身位于 whole-Turn 64-file
fuse 之后的情形。提高 `56/64` 不是修复；正确的最早偏差是 authorized path-metadata ranking 没有把 Java method identifier 的稳定名词组件
用于 filename navigation。

## Decision and disposition

这是 `system-contract / systemic` Finding，不按 mall、题号、方法名、类名、文件位置或中文表述特判。

1. Worker 对一个 Java-style content literal 做确定性的 camel/snake identifier component projection；只保留长度至少 4 的 component，并只在
   已授权 exact-revision tree path metadata 上比较 filename stem component。完整 stem/name/path equality 与 substring 仍优先，component
   overlap 只把 candidate 提前到 bounded path cohort。
2. 例如 `createOrder` 机械得到 `create/order`，因 `order` 与 `OmsPortalOrderServiceImpl` 的 stem component 相交而优先检查该文件；Worker
   仍必须在正文中逐字、大小写敏感匹配完整 `createOrder` 才能签发 locator。component、filename 或 path 自身都不是 Evidence、READ
   authority 或 content hit。
3. coverage ordering 升级为
   `QUERY_IDENTIFIER_PATH_RELEVANCE_THEN_ROTATING_CANONICAL_FALLBACK@3` /
   `QUESTION_PREFIX_QUERY_IDENTIFIER_PATH_THEN_ROTATING_CANONICAL_FALLBACK@2`，并密封 component count/digest。prefix、rotation、Partial、
   exact revision、allowlist、Profile、56 per-search、64 whole-Turn、reserved READ、byte/action/result fuse 全部不变。
4. regression 把唯一含 `createOrder` 的 `OmsPortalOrderServiceImpl.java` 放在 84-file scope 的 canonical index 76；56-file Search 仍在原 fuse
   内取得 exact content hit，并记录 2 个 navigation terms、其 digest 与 55 个 fallback reads。六模块定向测试 `155/155`、相邻 19 模块
   `265/265`、documentation check `631`、plan snapshot/diff 与 current hook 均 PASS。

该变化细化既有 Source Worker owner，不改变组件职责，故不需要新 ADR。本 Finding 与同步后的
`SYS-CONTRACT-SOURCE-ARTIFACT` 是 current system write-back。

## run-099 correction

`FINDING-010-226` 保留本 Finding 的 identifier-component ranking 决策，但纠正了 regression 与真实 mall source 的关键差异：真实
`OmsPortalOrderServiceImpl.java` 不含 `createOrder`，而是 `generateOrder`。因此 ranking 只能把目标文件带入 bounded observation，不能生成
literal Search hit；current successor 以独立 navigation-only modality 和 Boundary opaque-read option 表达该事实。本文的 run-098 observation 与
当时 fixture 结果仍是历史执行证据，不再单独定义 current zero-literal-hit 行为。
