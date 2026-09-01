---
id: FINDING-010-259
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, source, ai, quality]
depends_on: [ITER-010-PDR-014, FINDING-010-258, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/lightweight_engineering_agent.py, src/software_world_model/ai_infrastructure/lightweight_engineering_model.py]
tests: [tests/test_lightweight_engineering_agent.py, tests/test_lightweight_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: adopt-literal-query-contract-and-stop-review-churn
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-259：首轮真实基线暴露字面检索与关闭工具后的评审回流缺口

## Observation

Phase A `run-001` 在 candidate `ae8fb9dabd35708ef26addcde0655f8ffc0863fd`、mall source
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` 上经真实 Browser 和 Ark 执行。Agent 先后提交
`UmsAdminController register`、`UmsAdminServiceImpl register` 这类空格连接的多词 query；Source search 的实际能力是连续字面查找，因而没有找到
service implementation。两次无进展使只读工具熔断关闭。Agent 随后诚实返回 Limitation，fresh Reviewer 正确要求更多 implementation Evidence，
但循环仍重复 `FINISH → MORE_EVIDENCE`，最终以 `BUDGET_EXHAUSTED` 失败。

Browser 折叠 trajectory 共记录 22 个 ordered events。terminal receipt 保存 Ark `14/14` completed dispatch、DeepSeek 0、retry 0、human
approval 0、Production `NOT_EXECUTED`，并为每次外发保留 `LIGHTWEIGHT_EXACT_DISPATCH_AUTHORIZATION`。因此最早偏差在 Agent-facing
Source query 契约以及 Application 的 review successor 条件，不在网络、Provider、Citation 或回答格式。

## Evidence

- 首轮失败证据原样保存在 `var/iteration-010/pdr014-source-only/run-001/`，不重用其 session、数据库或输出路径；
- 模型 prompt 现在把 `SEARCH_SOURCE` 明确定义为一个连续 identifier 或 exact phrase，禁止把多个检索词拼成 semantic query；
- ordered trajectory 保存每次 decision 的实际 `query` 或 Application-owned `read_index`，后续可以从最早 action 检查偏差；
- 当 fresh Review 返回 `MORE_EVIDENCE` 且工具预算或无进展熔断已经关闭时，Application 立即失败当前 Turn；定向测试证明该路径只有两次
  Agent decision、一次 Source action、一次 Review 和三次 Provider receipt，不再重复 Review 消耗预算；
- 修复没有加入 mall 标识、问题文本、文件名或答案正文规则，也没有扩张旧 Claim/Boundary/content-unit 协议。

## Disposition

Engineering Conversation 当前 profile 明确 Source search 的连续字面契约，并把“工具仍可用”设为 `MORE_EVIDENCE` 返回同一 Agent 的必要条件。
`run-001` 继续记为失败而不被覆盖。修复后的 exact candidate 必须用 fresh artifact 重跑原问题，并至少验证两个异构未见问题和一个语义追问；
在这些真实 Browser 证据完成前不宣称 Phase A 基线通过。
