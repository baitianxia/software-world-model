---
id: FINDING-010-264
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [knowledge, application, quality]
depends_on: [ITER-010-PDR-014, FINDING-010-263, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/knowledge_engine/capability_cognition.py]
tests: [tests/test_capability_cognition.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: replace-unweighted-cognition-ranking
target: src/software_world_model/knowledge_engine/capability_cognition.py
---

# FINDING-010-264：有界 cognition search 必须保留查询相关声明闭包，不能由任一公共词把全库排入候选

## Observation

Phase B artifact 正确构建了接口注解，Phase C Agent 却看不到它。根因是 `CapabilityCognitionIndex._score` 对任一 token overlap 固定加分，
把完整 `source_path`、公共 package/module 词和行为词等价处理，也没有 discriminative-token 或 strongest-score 尾部。查询中的 `mall` 可令
1,666/1,666 entity 全部入选；`role/relation` 又让大量相邻方法排在真正的接口 contract 之前。

## Evidence

- frozen failure query `UmsAdminServiceImpl register transaction rollback role relation` 的旧结果为 `total=1330`，首屏没有
  `UmsAdminService#updateRole`；同 artifact 的替换结果为 `total=22`，实现方法第 1、带 `@Transactional` 的接口方法第 2；
- Elasticsearch 查询从 `total=1666` 收敛到 `7`，Controller、Service interface 和 implementation 的 `importAll` 均保留；购物车查询仍在
  首屏返回 Controller、implementation `add` 和 `getCartItem`；
- 替换沿用 current Engineering Conversation Contract 已有 relevance 规则：英语 function token 与超过候选一半的公共 token 不作为锚点，
  exact/prefix 权重为 `4/1`，只保留 strongest score 的 75% 尾部，`source_path` 只使用 basename；
- 对 exact `INHERITS` type chain 上相同 method signature 的声明，只在声明为当前 query 新增 token/prefix 信息时紧邻实现返回；没有新增关系、
  Source authority 或负向推断；
- unchanged artifact 的独立五任务报告 `sha256:92ae16e8babde6946285f7f0ea1b1b5426926fb7d1b17b7df5d2e51e967d8e29`
  仍为 5/5 PASS；cognition、Agent、model、Session、Provider 和 Browser 的 35 项受影响测试通过。

## Disposition

以通用 ranking 与 exact declaration closure 替换固定 overlap score。该变化是 cognition query 的本地实现修复，落实既有 System Contract，
不改变跨模块权威、Prompt、Schema、artifact identity 或 Source/Citation 规则。真实原题和两个异质问题仍须在 successor Browser run 复验。
