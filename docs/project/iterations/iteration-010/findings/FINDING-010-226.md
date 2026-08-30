---
id: FINDING-010-226
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [source, application, ai, quality]
depends_on: [FINDING-010-223, FINDING-010-225, ITER-010-PDR-012, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/interface/engineering_qa_source.py, src/software_world_model/application_services/conversational_engineering_tools.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_engineering_qa_source.py, tests/test_conversational_engineering_tools.py, tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: issue-boundary-only-opaque-read-options-for-identifier-path-navigation-after-zero-literal-hits
target: SYS-CONTRACT-SOURCE-ARTIFACT
---

# FINDING-010-226：run-099 证明 identifier path ranking 已命中目标文件，但完整 method literal 在该文件中不存在

## Observation and execution evidence

唯一 validated Engineering Chat launcher 在 product commit/tree
`ddf18a11f5c3eb0e0c907ace53c5ab6dc7db5472 / b0b6876da29a3b6da04aa3225d8908747e2b6cda`
上完成 `run-099-mvp-experience` 的 4 个隔离 Conversation、5 个冻结 Turn，并以 `STOPPED_AFTER_DISPATCH` 正常密封。terminal receipt digest
为 `sha256:28c86cd2970d4eafb1e8fbe7f4d127ab5a3b66262468ef15ef1e94630190393e`。

逐题 dispatch 为 `11 / 9 / 12 / 0 / 11`。Q1、Q5 均为 `SUCCEEDED / ACCEPTED` 且各有 2 个 exact Citation；Q4 继续以零 dispatch
形成 `APPLICATION_INPUT_CLARIFICATION`。Q2 为
`FAILED / REVIEWER_MODEL_CALL_REJECTED / PROVIDER_OUTPUT_INVALID / STRUCTURED_OUTPUT_INVALID`：Primary 在找不到目标实现后起草了无关的
`UmsMemberCouponController` 结果，focused Reviewer 已正确拒绝，因而没有重现 run-098 的 false acceptance。Q3 为
`SUCCEEDED / REVIEWED_LIMITATION`，但未取得 Citation，仍未满足 follow-up 质量。run-099 因而保持 Quality FAIL，不是 MVP。

Ark 4 个 dispatch 全部完成 verified TLS、credential resolution 与 HTTP dispatch，然后以 sealed
`429 / AccountQuotaExceeded / PROVIDER_HTTP_ERROR` 形成 trusted unavailable；每个 verdict 才激活对应 Turn 的 DeepSeek fallback。
DeepSeek 39/39 completed，使用 2 次 TLS session 与 37 次 connection reuse；post-dispatch unknown、retry、人工审批与 Production 均为 0。
各 Turn 的 Ark/DeepSeek dispatch 为 `1/10、1/8、1/11、0/0、1/10`，均保持 current per-Turn/per-Provider authority。

turn-scope、pricing capture、session、launch、terminal、Ark DB、DeepSeek DB 文件 SHA-256 分别为：

- `17b23e63ce0752e66be547d83da967461aedaae73dad9349e13b9acbe390dfe7`
- `e6dfa777ea37ebe26448c668ddbbb081048cf1219b23e495cdadb58ea05cfcd0`
- `461c32cf520a8361aba9282a55c05c0de487a2f00ee5e7208232d3b2ce7d1fdc`
- `5b478b1b95cf7a925491ca7ffa7d0031b17cd4a3c27a8a8eae9cc0e8b3608d2a`
- `e26adb25ad2b022c0c6cf0e7e2cdc599f0ecf408606b29f8b9cad034405b192b`
- `0594e979dfba8794e3c9b11b9fa20b5ba9d1f376aed6b3d93ee0d9f4e829510e`
- `876cc65ef5d2190de721eb0516da83447df15a4ddb5786bafb74a5f380f082a6`

preparation、public Source session authority、session runtime 与 standing authority digest 分别为
`sha256:818908a3d037219f983691153d5d4d24046ef8e6428422e463218bbee3320f07`、
`sha256:575eb4c43dcfb7894b3203dff92d07add20ced6d0a3d7f51ae5667f5d5af3752`、
`sha256:4bd0043126dfa4b3b5d6a657d4f53766c4be8fce28f52185bc262d753af113ce` 与
`sha256:cd4d6f42d1bd2a64f57f3bc9ab386fd45a34449125b5e99c8efe5da0ee61c663`。official DeepSeek pricing 在
`2026-08-30T22:47:19.234Z` fresh 检查，visible-text digest 为
`sha256:9c9dd4d22764599ade403c0ba6cd95abcb947810d5230ee95cb96a56a62d7668`。

## Exact first divergence

`FINDING-010-223` 的 regression fixture 让目标 `OmsPortalOrderServiceImpl.java` 正文包含 `createOrder`，因此证明 identifier-component
ranking 可以在 56-file fuse 内取得 literal hit；真实 mall exact revision 却没有该方法。目标实现的方法名是 `generateOrder`，库存调用为
`lockStock`，后续订单项调用是 `orderItemDao.insertList`，不是 Q3 猜测的 `insertBatch`。

run-099 的 `SOURCE_SEARCH(createOrder)` 已按 `order` component 把 `OmsPortalOrderServiceImpl.java` 放入首批 15 个 path candidates，随后检查
41 个 fallback，共 56 个文件；它仍按契约正确返回 0 个完整、大小写敏感 literal hit。旧 Result 只能表达“无 hit + Partial”，不能把已经读取且
与 identifier path material 相关的目标文件签发为可继续 full READ 的候选。Primary 因而转向无关 `coupon` 搜索，Q2 被 Reviewer 拒绝；Q2 未交付
full-source Citation 后，Q3 也没有 prior exact-source revalidation option，只能从不存在的 `insertBatch` 再次零命中并交付过度保守的 Limitation。

把 component/path 直接改成 SUPPORT 会重现 run-098 的错误 Citation；提高 fuse 或把 `createOrder` 当成近似正文命中同样不正确。最早偏差是 Result
缺少“已授权、已读取、仅供导航、必须再 READ”的独立类型和 Application copy domain。

## Decision and disposition

这是 `system-contract / systemic` Finding，不按 mall、问题、方法名、类名或文件位置特判。

1. Worker 仍只把完整、大小写敏感 query literal 的逐字正文命中作为 `LITERAL_TEXT_SEARCH_HIT`。仅当当前 bounded Search observation 的 literal
   hit 为 0 时，才可从已检查的 rank-2 identifier-component path cohort 签发最多 16 个 typed navigation candidate；候选 modality 固定为
   `IDENTIFIER_PATH_NAVIGATION_CANDIDATE`，并在 `RetrievalResult.navigation_candidate_item_ids` 中按 item 顺序完整绑定。
2. navigation candidate 必须保持 exact revision、Request、Profile、evidence class、allowlist、operation、实际 path/line/content digest 与所有既有
   file/byte/result fuse；它只生成 opaque locator 和 coverage/audit，不是近似 match、SUPPORT、Claim evidence 或正文不存在证明。
3. Tool Adapter 把这些 item 只投影为 `ENGINEERING_AGENT_SOURCE_BOUNDARY@2 / SOURCE_IDENTIFIER_NAVIGATION_CANDIDATES`，Citation refs 仅用于
   current-Turn opaque READ copy domain，不产生 Search SUPPORT。Primary 只可从
   `CURRENT_TURN_IDENTIFIER_PATH_NAVIGATION` option 选择 materially matching resource 并执行 `SOURCE_READ`；只有 fresh full-resource READ
   的 `EXACT_STATIC_SOURCE_TEXT` SUPPORT 才能支撑 Claim。payload、Citation 或 resource identity 不一致时失败关闭。
4. model strategy/prompt/Primary input 升级为 `@26/@26/@26`，final preflight 升级为 `@21`；Review input `@16`、wire output schemas、Source
   56/64 fuse、15-call Provider authority、route、fallback admission、retry 与 Production 边界不变。
5. regression 把真实 lexical mismatch 写入第 76 个 implementation filename，验证 56-file scan 只签发 navigation modality；Conversation 测试验证
   Search 仅形成 Boundary、opaque READ 后才形成唯一 SUPPORT/Citation；model-boundary 测试验证 typed option 与伪造 payload 失败关闭。六模块
   定向测试 `157/157` PASS。fresh run-100 是下一真实质量证据；run-099 保持真实质量 FAIL。

该变化细化既有 Source Worker、Application Tool Adapter 与 model-boundary owner，不改变组件职责，故不需要新 ADR。本 Finding 与同步后的
`SYS-CONTRACT-SOURCE-ARTIFACT`、`SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 是 current system write-back。
