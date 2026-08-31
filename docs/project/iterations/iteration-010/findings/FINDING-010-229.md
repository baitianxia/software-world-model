---
id: FINDING-010-229
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai, quality]
depends_on: [FINDING-010-227, FINDING-010-228, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: separate-comprehensive-semantic-review-from-focused-boundary-review-and-treat-explicit-unknown-as-requirement-coverage
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-229：run-101 的 Reviewer 在 uncertainty 与 Boundary ownership 上反复制造相反修复

## Observation and execution evidence

validated Engineering Chat launcher 在 product commit/tree
`eb0e96666107e3934cf198e7f0b7e4e8e5d59a68 / 5af2e900a14ce5f8cdb9ffc00785650b1186e113` 上完成
`run-101-mvp-experience` 的 4 个隔离 Conversation、5 个冻结 Turn，并正常停止。terminal receipt digest 为
`sha256:f80286b0ef77e93027e673f01f47a3cea88a8c5226f12bf138df120827e5e28e`；逐题 dispatch 为
`14 / 12 / 16 / 0 / 10`。Ark 4 个 dispatch 全部形成 sealed `429 / AccountQuotaExceeded` trusted-unavailable verdict，DeepSeek
48/48 completed；post-dispatch unknown、retry、人工审批与 Production 均为 0。因此这不是 Ark、DeepSeek、fallback admission 或 standing
authority 不可用。

Q1 Draft 已精确陈述当前源码可见的 local call order，并把 transaction boundary、cache consumer effect 与 permission timing 明确列为未确认。
comprehensive Reviewer 却同时要求把这些项目肯定分类为 transactional database change / dynamic refresh，又承认 Evidence 未建立这些事实；
Primary repair 因而重复或在两种相反要求间摆动，最终 structured-output-invalid。Q2 的 comprehensive Reviews 围绕同两个 Boundary ID 依次
要求删除、增加、删除，直到第 4 次才批准，耗尽全部 Review slot，focused Review 无合法剩余调用而以 review limit 失败。Q5 的 global Finding
同样一面要求按 ID update，另一面否认当前 Evidence 可建立该效果，repair 无一致目标。

run-101 的 session、turn-scope、pricing capture、launch、terminal、Ark DB 与 DeepSeek DB SHA-256 分别为：

- `8b4e9bac1bde548b84ce608e39a023b8b16c54e3665b7cb33421149225d640d4`
- `d6437d1d56482e0e163f5f212fa1300b98afc80533253fcf470425a24278072d`
- `589438e8df175e82d072de8395bb067e2705412f6620f848f184824aedd9fe8b`
- `1172eabe9310d825742a239b75d36c7ec161a0bae553c9fcc8d50886807b24ba`
- `074f92cba4ceb72791823e003ad824aa7777503ac01158e7c1ca30bc94e80d2c`
- `1a54b898d7e299a5a10a6e26178277a319746a76addaa536403fb3bfc794509b`
- `be7892a9c347267b9e4d2370a44cf48c8a6b4ce59ee9924d1c2ed5247787c095`

## Exact first divergence

旧 Review input 同时把完整 Boundary inventory 投影给 comprehensive 和 focused focus，却没有定义哪一阶段拥有 Boundary materiality/reference
Finding。两个独立 Review 因而可以对同一 reference 产生相反修复。requirement-coverage Prompt 也只要求覆盖题面类别，没有明确“用户提到某个
类别”不是该事实存在的 Evidence，也没有规定诚实的 unconfirmed treatment 已经回答 uncertainty request。自由文本 Reviewer 于是可以要求
Provider 从同一 sealed Package 同时产生肯定事实与未知声明。

这是通用 Review focus ownership 与 uncertainty coverage contract 缺口，不是 mall 角色、订单、搜索模块、中文措辞或 DeepSeek 特例。

## Decision and disposition

1. comprehensive Review 拥有 current requirement coverage、普通 Claim support 与一般完整性/相关性缺陷；caller/callee scope、Boundary
   materiality、resolved-acquisition 与 Boundary reference 增删只由 focused Review 的 exact challenge 拥有。
2. comprehensive input 将 `evidence_package.boundary_observations` 与 `draft.boundary_observation_ids` 阶段性投影为空，并显式标记此空值
   不是 absence evidence；该 focus 不得创建唯一修复为增加、删除或披露 Boundary reference 的 Finding。
3. 用户问题中的名词/候选分类不是事实 Evidence。Draft 以 SUPPORT 陈述可见局部行为、并诚实说明 transaction/database/cache/remote/timing
   等未被建立时，已经回答对应 uncertainty；Reviewer 不得要求把未知提升为肯定事实。
4. global requirement Finding 必须指名 exact missing/contradicted/misclassified delta，并给出一个 sealed Package 内可完成的修复；相互矛盾、
   只复述题面或要求超出 Evidence 的 Finding 非法。
5. protocol family 升级到 `conversational-engineering-agent@28 / prompt@28 / ENGINEERING_AGENT_PRIMARY_INPUT@28 /
   ENGINEERING_AGENT_REVIEW_INPUT@18 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@23`。Review output、Draft/Answer 与 Tool/Source schema 不变。

这项变化写回 `SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 与 active Slice，不改变组件职责，故不需要新 ADR。run-101 永久保持
Quality FAIL；fresh run-102 必须验证原失败题与异质题是否收敛。
