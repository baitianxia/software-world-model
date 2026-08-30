---
id: FINDING-010-202
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [source, application, quality]
depends_on: [FINDING-010-182, FINDING-010-200, FINDING-010-201, ITER-010-PDR-012, SYS-CONTRACT-SOURCE-ARTIFACT]
code: [src/software_world_model/interface/engineering_qa_source.py]
tests: [tests/test_engineering_qa_source.py, tests/test_conversational_engineering_tools.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: stop-navigation-search-after-verified-filename-cohort-with-partial-coverage
target: SYS-CONTRACT-SOURCE-ARTIFACT
---

# FINDING-010-202：无 Cognition path scope 的精确类型定位仍为一个 locator 扫完整个 56-file Search 配额

## Observation

run-079 第五题询问 `mall-search` 商品导入 Elasticsearch、按 ID 写入/删除、数据库读取和文档转换。该 scope 不在现有
`mall-admin` Java Profile 内，因此 World Model 正确只给出 Maven module 与 Coverage Boundary，没有 Java Source target path。Primary
先后搜索并读取 `EsProductController` 与 `EsProductServiceImpl`；两组 exact type query 都把最相关文件排在第一位并成功签发 locator，
但 Worker 为声明全 Evidence Class content coverage 仍继续读取低相关文件，最终 Source receipt 正好达到 `64/64`。

Turn 仍以 Ark 9 次、3 Citation、fresh Review 交付 `SUCCEEDED / ACCEPTED`，答案诚实说明 `EsProduct` domain 和 repository interface 未读，
没有伪造远端刷新/一致性语义；但相对 run-078 的 9-Citation 同题答案出现物质证据覆盖退步。根因不是 Agent 在 Source 仍可用时偷停，而是
locator navigation 与 exhaustive content search 共享同一个 56-file scan 成本。

## Evidence and first divergence

- `EsProductController` Search 的 query 与 canonical Java stem 精确相等，排序器首先读取
  `mall-search/src/main/java/com/macro/mall/search/controller/EsProductController.java` 并取得 2 个 case-sensitive hits；旧 Worker 随后继续至
  56 files，才以 `SOURCE_SEARCH_FILE_LIMIT_REACHED` 返回 Partial。
- Service Search/Read 使用剩余 8 个文件槽位并达到 `64/64`；model-facing Source Search/Read 随即正确关闭，只剩 3 个 Agent action slot 和
  World Model。Primary 不能合法继续读取 `EsProduct.java`、`EsProductRepository.java` 或 DAO mapping，故较窄边界不是假 Limitation。
- first systemic divergence 位于 bounded Worker：它已有 exact-revision、allowlisted tree metadata 和 filename-relevance ordering，也已在最相关
  filename cohort 得到正文 literal hit，却仍为当前导航目标读取全部低相关 canonical fallback。
- 修复后对 run-079 exact mall revision 做零 Provider replay：allowed SOURCE entries 519，`EsProductController` Search 读取 1 个文件、命中 2
  行、签发同一 canonical resource locator，并以
  `PARTIAL / SOURCE_SEARCH_FILENAME_MATCH_EARLY_STOP / filename_early_stop=true` 明确保留未检查其余 corpus；没有把局部导航命中冒充
  exhaustive search complete。
- 多资源回归以 `LoginService / LoginServiceAudit / LoginServiceToken` 证明：存在 exact stem anchor 时必须先检查所有 basename 含该 query 的
  authorized filename candidate，不能在第一个文件后停止而丢 locator；无 exact stem anchor 的普通 member query 继续原 bounded scan。

## Classification and disposition

这是 `system-contract / systemic` Finding；不按 Elasticsearch、类名、Java package、工程、问题或 Provider 特判。

1. Worker 继续只使用已授权 exact-revision tree path metadata 排序。只有至少一个 candidate stem 与 case-insensitive query 精确相等，且每个
   basename 等于或包含该 query 的 filename cohort 都已安全检查、至少一个文件含 case-sensitive content hit、cohort 内无 unsafe/binary/UTF-8
   gap 时，才可在进入 path-only/canonical fallback 前停止。
2. 该停止必须返回 `PARTIAL / SOURCE_SEARCH_FILENAME_MATCH_EARLY_STOP`，`truncated=true`，并记录 exact-stem/filename candidate count、
   content match count、ordering 与 early-stop flag。未检查完整 allowlist 时不得宣称不存在、完整或全局唯一；后续 full READ 才支持资源正文
   结论。
3. 若没有 exact stem anchor、filename cohort 无正文 hit、cohort 自身触发 file/byte/result fuse，或存在 unsafe/binary/non-UTF8 entry，则继续
   原 bounded scan或保留更早的 typed failure；trusted cognition path scope 的完整语义不变。
4. 实际读取的每个文件仍计入 whole-Turn usage；新规则不提高 56/64 fuses、不扩大 allowlist/Profile/revision/modality、不授予 path/READ
   authority，也不改变 Agent/Reviewer/Provider route。Source `13/13`、Conversation Tool `15/15` 与 Question Broker `53/53` PASS，外调 0；
   fresh exact Browser successor 仍须验证 Q5 是否利用保留预算闭合 material document-mapping evidence，run-079 不取得质量或 MVP PASS。
