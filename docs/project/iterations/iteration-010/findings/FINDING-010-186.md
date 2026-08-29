---
id: FINDING-010-186
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [FINDING-010-175, FINDING-010-176, FINDING-010-185, ITER-010-PDR-012]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: close-inherited-container-qualifiers-through-claim-inventory-and-review
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-186：Claim inventory 与 Reviewer 漏掉标题继承的物质分类

## Observation

`run-075-mvp-experience` 的订单创建后续 Turn 询问：库存校验不通过时，哪些数据库写入一定未发生，哪些副作用无法确认。Primary draft
`model_call_3e223489dea8441ebafea9806b1e4e1f` 在标题“以下数据库写入一定尚未发生”之下，把
`sendDelayMessageCancelOrder → cancelOrderSender.sendMessage` 列入结论。源码只支持这个调用位于 `hasStock` 之后、失败时尚未执行；它是
消息副作用，不是数据库写入。draft claim 7 只枚举“调用位于 hasStock 之后且未执行”，没有带上标题赋予它的“数据库写入”分类。

fresh Reviewer `model_call_1e108616bda94880be565c4be6e0117d` 对 10 个窄 Claim 全部返回 `SUPPORTED` 并 `APPROVED`，没有把正文的标题、表头
和列表项组合为完整 assertion，也没有发现 material container qualifier 未进入 Claim inventory。因此 Turn 虽形成
`SUCCEEDED / ACCEPTED`，仍不满足 `V-CHAT-QUALITY-001` 的重大错误与 Reviewer 漏判均为 0。

## Evidence and first divergence

- Primary action/draft/Reviewer output digest 分别为
  `sha256:be7a783715c908c78313663789e56453598f557b2e516612f401807b6aee9f33`、
  `sha256:24dc07c3ec48588855f8590131730a7995545c1bf646d173854b493c09be858f` 与
  `sha256:bfb268cfc563f3cb6769b819bb3de3422a7eb678bf3ecd3e18554fd764ff401c`。
- 表格自身使用“数据库写入/副作用”联合列，尚可把消息调用识别为副作用；但最终结论明确放在“以下数据库写入一定尚未发生”标题下，且
  bullet 没有局部改写分类。普通文本语义中，标题/lead-in 是所含列表项 assertion 的组成部分，不能只审核 bullet 内的动作与顺序。
- 已有 Prompt 要求正文、summary、table、diagram、code comment 的 material affirmative conclusion 进入 claims，但没有明确要求 Claim
  statement 复制容器继承的 category/scope/condition/certainty/negation。Reviewer 因而只比较窄 Claim 与 Evidence，漏审完整 content assertion。
- Ark 在本 run 全部可信可用，DeepSeek 0；这不是 Provider、路由、Source coverage 或 Citation identity 问题。first divergence 位于
  Primary 的 content-to-claim enumeration，Reviewer 是第二个本应阻断却未阻断的 guard failure。

## Classification and disposition

这是 `system-contract / systemic` Finding；修复所有自然语言、Markdown、表格、列表和代码注释，不按订单、数据库、消息或中文标题特判。

1. heading、table column、list lead-in、label 与 surrounding sentence 所赋予的 category、scope、condition、certainty 和 negation 都是
   contained assertion 的组成部分；`draft.claims[].statement` 必须重述每个物质继承 qualifier。仅记录 action/outcome 不算枚举完整。
2. Primary sealed `draft_reference_policy` 明确投影 container-context rule 与 exact qualifier categories，使它与 role prompt 同时进入每次
   exact request identity；Application 不尝试以关键词规则改写自然语言语义。
3. Reviewer 必须先用容器语境重建完整 content assertion。Claim inventory 漏掉 material inherited qualifier 时返回
   `claim_index=null` 的 global completeness Finding；qualifier 本身错误、无据或误分类时返回 concrete defect。窄 Claim 获支持不能批准其
   容器扩张。
4. Reviewer sealed `review_reference_policy` 显式投影上述义务；现有 decoder 继续允许并重算 global `claim_index=null` Finding、完整 Claim
   assessment 与 decision 一致性。无 AF_UNIX 依赖的受影响组合 `127/127` PASS，外部 dispatch 0。fresh Browser successor 必须以新的异质问题验证 Reviewer
   能阻断或 Primary 能避免同类继承分类错误；run-075 的 approved Review 不追认为质量 PASS。
