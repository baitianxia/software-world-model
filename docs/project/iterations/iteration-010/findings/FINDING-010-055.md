---
id: FINDING-010-055
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-053, FINDING-010-054]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_model_source.py, tests/test_engineering_question_strategy.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: add-closed-cross-claim-and-observation-consistency-review-gate
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-055：Reviewer 批准了同一答案内互相冲突的失败语义

## Observation and evidence

`FINDING-010-053/054` 的处置形成 clean candidate
`c65617ee36280b5473b142e840fe6a50a1331623` / tree `df98dd0749eb6b8a7d91186674fcae454c02b49a`。clean clone 的
Engineering QA 99/99 与 docs 448/448 PASS；fresh DeepSeek Conformance run-019 以 2/2 request PASS，Result
`sha256:8cde961ffd9a4f285204c8aff0a2ed5f838bfc3ddcf18a23388710d749bf89fe`，actual model `deepseek-v4-pro`、retry 0。
同一持续 Alpha 的三个模型 Review 都返回 `APPROVED`：

- 原现场登录题以 12 次 dispatch 形成 Result `engineering_result_88e15e73e80db0b871ae9261fa295d40`，覆盖登录入口、用户/密码/启用
  校验、JWT、SecurityContext、失败返回、登录日志与 3 个源码 Citation；
- 构建/安全/resources unknown 题以 15 次 dispatch 形成 Result `engineering_result_6852bb516c2cdd488c4bd403aeadee4a`，覆盖 POM
  依赖/插件、登录与受保护接口接入，并明确把未授权 resources 内的数据库连接、JWT 密钥和端口保留为未知；
- 401/403 题以 12 次 dispatch 形成 Result `engineering_result_8381e52c0def4f5cf51a87d28f09ffe2`；本次修复目标成立，独立
  `IMPLEMENTATION_EVIDENCE` 核对依据已出现在默认正文，并引用 `JwtAuthenticationTokenFilter`、`JwtTokenUtil`、
  `DynamicSecurityMetadataSource` 与 `DynamicAuthorizationManager`。

但独立技术复核不能接受第三题的模型 `APPROVED`。同一默认正文先声称“未认证或权限不足时返回 `AuthorizationDecision(false)`，导致
403”，紧接着又声称“令牌失败、未建立认证时表现为 401；已认证但权限不足时表现为 403”。前者把两个条件压成同一结果，后者又把它们
区分为两个互斥结果。Gateway raw Answer、Package observations 和 raw Review 都完整保留这组冲突；Reviewer 的独立 observations 也逐字
复述两者，却仍把既有四项 quality 全部标为 `PASS` 且 Findings 为空。这是同一答案内部可直接证明的矛盾，不依赖读取被排除的 handler
实现，也不能因其余结论正确而忽略。

22,000 字符输入在本地以 `request body is empty or exceeds the local preview limit` 失败关闭，Gateway call root 在提交前后均为 39；服务
随后优雅停止。terminal receipt `sha256:cfed19a1dd5da2bc6a9970c855d0bac4f8b773b87018c2e8409e2d35c5dafde8` 记录 3 个
accepted question、39 次 dispatch（12/15/12）、retry 0、Provider switch 0、全部 transport verified、post-dispatch outcome unknown 0、
Production Activation `NOT_EXECUTED`；session、Gateway SQLite、launch 与 terminal receipt 均为 `0600`。

## Root cause

Reviewer 已有 direct answer、abstraction fit、material completeness 和 implementation-detail budget 四项 closed Gate，也会重新枚举 Package
observations；但没有一个必须显式比较 direct answer、默认 Claims、Package observations 和独立 observations 的 consistency verdict。
因此“所有 observations 都被覆盖”可以与“其中两条 observations 互相冲突”同时成立，Application 只能机械验证四项全 PASS，无法阻断这类
假批准。该缺陷与 mall、JWT、401/403、类名或具体状态码无关，适用于任何同一 subject/condition 被赋予互斥 outcome、state、ordering 或
side effect 的答案。

## Decision and disposition

- Review closed quality assessment 新增必填 `claim_consistency: PASS | FAIL`。Reviewer 必须成对比较 direct answer、每个默认可见 Claim、
  Package observations 和自己独立形成的 observations；同一 subject/condition 的互斥 outcome、error category、state、ordering 或 side
  effect，以及把已区分子集错误压成一个宽泛结果，都必须 `FAIL` 并形成绑定 Claim/checklist 的 actionable rewrite Finding；
- `APPROVED` 现在要求五项 quality 全 PASS。Application 保持 fail-closed，Review output schema 升为 `@4`，Quality identity 升为 `@2`，
  Prompt/Strategy 升为 `@22/@13`；不加入项目、问题、关键词、符号、类、方法、fixture 或 Oracle 特判；
- current System Contract、ADR、Slice/Manifest/Verification 与确定性测试在同一变更中同步。三模块定向 62/62 PASS；Engineering QA、docs、
  full、new clean/fresh Conformance 和三题 live 仍须重新闭合。run-019 的 3 个模型 `APPROVED` 永久保留为 2 个独立可接受答案加 1 个
  independent-quality FAIL，不能追认为 `V-ANSWER-REWORK` PASS。
