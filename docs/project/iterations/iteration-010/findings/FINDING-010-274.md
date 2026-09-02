---
id: FINDING-010-274
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, source, knowledge, quality]
depends_on: [FINDING-010-273, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, SYS-CONTRACT-SOURCE-ARTIFACT]
code: [src/software_world_model/application_services/conversational_engineering_tools.py, src/software_world_model/application_services/lightweight_engineering_agent.py]
tests: [tests/test_lightweight_engineering_agent.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: classify-cognition-provenance-before-source-navigation
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-274：认知详情中的非源码 provenance 不能阻断 Source 接线

## Observation

真实 `CapabilityCognitionIndex` 的 Java 详情页同时返回 Java entity 和 Maven module entity。后者的 provenance 指向
`MAVEN_MODULE_DESCRIPTOR`，而当前 Chat Source Profile 将对应路径注册为 `BUILD_CONFIGURATION`。bridge 若把详情页的所有
provenance 都直接交给 `SourceBroker.issue_required_path_locators` 并强制要求 `SOURCE`，会在合法的 cognition 查询之后错误产生
`AUTHORITY_RECORD_INCONSISTENT`，使主 Agent 尚未有机会读取真正的 Java Gap。

## Evidence

- run-141 的第二个合法 `RETRIEVE_COGNITION_DETAIL` dispatch 后，detail page 新增 19 个 candidate；其中
  `mall-portal/pom.xml` 的 `evidence_kind` 为 `MAVEN_MODULE_DESCRIPTOR`，Source Profile 分类为 `BUILD_CONFIGURATION`。
- 绑定 SourceBroker 的本地重现显示 Java provenance 可以签发 SOURCE locator，而 POM 只有在错误地按 SOURCE 请求时才触发上述失败。
- `tests.test_lightweight_engineering_agent.LightweightEngineeringAgentTest.test_cognition_provenance_becomes_brokered_source_read_in_unrelated_repo`
  现在使用同一 fixture 的 Java `SOURCE` 与 `app/pom.xml` `BUILD_CONFIGURATION`，验证混合输入只产生 Java navigation carrier，
  未绑定 path 仍 hard-fail。
- executor-level fixture 验证 `BUILD_CONFIGURATION` provenance 留在 cognition candidate/Observation 输入，`read_candidates` 不含该路径，
  且内部 trajectory 仅记录受控 skip 元数据（count、canonical paths、evidence kinds 与 provenance digests）。

## Disposition

在既有 `cognition_source_read_options` 接线中，adapter 先调用绑定 Request 的
`SourceBroker.evidence_class_for_path`。只有解析为 `SOURCE` 的 provenance 才申请既有 required path locator 并铸造 navigation
carrier；明确绑定为其他 retrieval class 的 provenance 不申请 locator，继续由完整 cognition Observation 承载。executor 对尚未有
full-source candidate 的 provenance 逐项调用既有 bridge，空返回仅表示该受控 non-SOURCE skip，并写入内部 trace；未绑定、越权、
多类匹配、revision/tree 漂移和 identity 错误仍保留 fail-closed。没有新增 Agent protocol、版本化 option、Prompt、Provider 或题面规则。

该边界已回写 `SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION`；后续 fresh loopback 运行必须证明混合 cognition 页面不会阻断
`cognition → Broker READ → Worker SOURCE Citation`。
