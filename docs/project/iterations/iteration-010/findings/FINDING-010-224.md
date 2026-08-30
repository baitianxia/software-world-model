---
id: FINDING-010-224
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai, quality]
depends_on: [FINDING-010-223, FINDING-010-221, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: remove-authored-effect-labels-from-caller-only-review-rewrite
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-224：run-098 暴露 caller-only rewrite 可保留“写入调用”效果标签并耗尽 Review

## Observation and execution evidence

本 Finding 使用 `FINDING-010-223` 密封的同一 `run-098-mvp-experience` identity、Provider route、artifact digests 与 terminal evidence。
Q3 的 Ark 3 + DeepSeek 14 dispatch 分别保持在 current per-Provider 15-call authority 内；其失败不是 route、retry、人工授权或 Production
边界问题。

## Exact first divergence

Q3 已成功读取 exact `OmsPortalOrderServiceImpl.java` full Source，并形成用户要求的局部调用顺序。comprehensive Reviewer 对 3 个 Claim 全部
SUPPORTED；focused Reviewer 随后正确指出，caller source 只能证明 `orderMapper.insert` 与 `orderItemDao.insertList` 的调用及局部顺序，
不能证明 callee implementation 或 database write effect。

Primary 的 successive same-Package rewrites 加入“当前源码未确认数据库写入效果” caveat，却在正文和 Claim 中持续保留“订单写入调用 / 订单项批量
写入调用”这类 model-authored effect label。这个 label 仍把 call expression 分类为 database write；邻接 caveat 不能消除同一 Draft 内的矛盾。
fresh focused Reviewer 因而连续返回相同 caller-effect Findings，最终 `AGENT_REVIEW_LIMIT_REACHED`。`FINDING-010-221` 已要求 invocation/local
order 与 effect 分离，但它没有明确要求删除包围 exact call expression 的 authored effect label，模型便把“加上 call 后缀”误作收窄。

## Decision and disposition

这是 `system-contract / systemic` Finding，不按中文词、mapper/DAO 名、mall 或题号特判。

1. active same-Package review rewrite contract 显式投影：caller-effect repair 必须从 matching content 与 Claim 删除所有 model-authored database、
   persistence、state-update、cleanup、message-side-effect、successful-result 等效果标签；唯一安全重述是 exact call expression 与
   source-visible local order。
2. “效果未确认”的邻接 caveat 不能修复同一 Draft 中仍存在的 effect label；方法名或 call-expression name 本身仍不增加效果语义。若 exact
   call/local order 不足以回答用户，Primary 只能保留 material unknown boundary 或继续合法补证，不能用效果分类包装 caller evidence。
3. model strategy/prompt/Primary input 升级为 `@25/@25/@25`，final preflight 升级为 `@20` 并冗余复制 exact rewrite contract；Review input
   `@16`、wire output schemas、15-call per-Provider authority、route、budget、retry 与 Production 边界不变。
4. regression 机械验证 rewrite contract 同时包含 remove-effect-label=true、adjacent-caveat-cures=false 与 exact-call/local-order-only safe
   restatement；六模块定向测试 `155/155`、相邻 19 模块 `265/265` PASS。fresh run-099 验证真实模型是否越过该分歧；run-098 保持真实质量 FAIL。

该变化细化既有 Application/Primary owner，不改变组件职责，故不需要新 ADR。本 Finding 与同步后的
`SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 是 current system write-back。
