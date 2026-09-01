---
id: FINDING-010-273
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, knowledge, quality]
depends_on: [ITER-010-PDR-014, FINDING-010-270, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS]
code: [src/software_world_model/application_services/conversational_engineering_tools.py, src/software_world_model/application_services/lightweight_engineering_agent.py]
tests: [tests/test_lightweight_engineering_agent.py, tests/test_conversational_engineering_tools.py, tests/test_iteration_010_direction_check.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: bridge-trusted-cognition-provenance-through-existing-source-read-authority
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-273：认知 provenance 必须经既有 Source authority 转换为可执行读取

## Observation

`run-130-phase-c-review-boundary-qualified` 的 cognition detail 已返回目标 implementation 的 exact revision/tree、Java path、line range 与 content
digest，但 Agent 的 `read_candidates` 只有此前 Source search 取得的 Controller。模型不能把受信 cognition provenance 转换为既有
`SOURCE_READ` 的 opaque locator，只能重新做 literal Source search；搜索未命中实现后，模型的 `FINISH` 同时选择了没有 Citation 的
cognition Observation 1/2 和 Controller Source Observation 6。Application 在 Agent `_resolve_citations`、Reviewer 调用前以
`CONTROL_STATE_DENIED` 失败关闭。最早偏差层是 Application 的 cognition retrieval → Source read 集成，不是 knowledge construction、
Provider、Prompt、Reviewer 或题面语义。

首版修复曾新增一个版本化 cognition Source read option。ITER-010 direction check 把它正确识别为新增 legacy protocol；该类型、Schema 和
公共导出已全部删除，不能以新增回答/Agent 协议修复集成缺口。

## Disposition

Application 现在只使用既有 Source read authority：它从受信 `CapabilityCognitionIndex` 解析并重验完整 provenance，确认 exact
snapshot revision/tree 与 current Turn Binding 一致，再把 canonical path 交给 `SourceBroker.issue_required_path_locators`。Broker 继续按 current
Request、attempt、Source Profile、allowlist、evidence class 和 revision 重新签发 opaque locator。工具仅用既有 `EngineeringAgentCitation`
对象把该 opaque ref 与 provenance locator/digest 携带到 Agent 的数字 `read_candidates`；该对象是 navigation carrier，不进入 cognition
Observation citations、最终 `_resolve_citations`、delivered Citation 或跨 Turn Citation domain。模型选择数字 `read_index` 后仍执行既有
`SOURCE_READ`，只有 Worker 的实际读取 Observation 才能形成可交付 Source Citation。

provenance 只保存在 adapter 的内部非版本化 current-Turn map。Proposal Ledger 记录 source tree、由完整 provenance 重算的 digest，以及
`cognition_provenance_grants_source_evidence=false`。片段 content digest 不与后续整文件 Worker digest 混比。若同 path 已由 prior delivered
full Source 在 current Turn 重新签发，则复用该更强能力并跳过 cognition duplicate；cognition-derived path catalog 每 Turn 累计最多 64 项，第
65 项失败关闭。整个路径没有 raw filesystem 读取、模型 path authority、工程/题目/类/方法特判，也没有修改 Provider、Prompt、Reviewer 或答案
Schema。

## Verification

- 异质临时 Git 工程从 `CheckoutServiceImpl` cognition provenance 直接完成 Broker locator → Worker READ → real `SOURCE` Citation；trajectory
  为 `SEARCH_COGNITION → TRAVERSE_RELATIONS → READ_SOURCE → FINISH`，没有 `SEARCH_SOURCE`，最终正文只陈述实际所读的 interface
  implementation 与 return behavior。
- 同一 Conversation 追问同 implementation 时只保留一个同 path candidate，adapter 对相同 provenance 返回空的新增集合；另一个 fresh Turn
  分两批签发 32 + 32 项后，第 65 项以 `BUDGET_EXHAUSTED` 失败关闭。
- `tests.test_lightweight_engineering_agent` 与 `tests.test_conversational_engineering_tools` 合计 21/21 PASS。
- 绑定 Phase A/B/C 已封存能力、trajectory 与 replacement evidence 的 `direction_check` 为 `PASS`，`violations=[]`；新增协议违规已经消失。

该 Finding 只闭合 cognition → Source 的既有能力接线，不宣告 Phase C 或方向质量完成。fresh clean product commit 仍须重跑真实 loopback Web
原问题与异质任务，并由独立监督继续给出结论。
