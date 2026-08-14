---
id: FINDING-008-003
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, quality]
depends_on: [ITER-008-SLICE-001, SYS-ADR-015, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING]
code: [src/software_world_model/application_services/structure_read_bundle.py, src/software_world_model/application_services/bounded_world_model_investigation.py, src/software_world_model/infrastructure/file_structure_read_bundle.py, src/software_world_model/interface/world_model_product.py]
tests: [tests/test_structure_read_bundle.py, tests/test_bounded_world_model_investigation.py, tests/test_java_source_semantics.py]
iteration: ITER-008
classification: local-implementation
disposition: seal-pre-question-recall-result-in-versioned-read-authority
target: src/software_world_model/application_services/structure_read_bundle.py
---

# FINDING-008-003：正式 Answer worker 缺少可用的业务发现召回证明

## Observation

有界调查服务可以根据独立 Business discovery recall Oracle 判定第三层完整性，但原实现只能由进程内调用方直接注入 Oracle。
正式 Web 的 Answer worker 按 Source-off 隔离规则只挂载 exact ordered/Snapshot Read Bundle，并明确不能读取 product Oracle 文件；
因此同一正式产品链即使前两层 COMPLETE，也永远只能把零候选返回为 `BUSINESS_DISCOVERY_RECALL_UNPROVEN` Limitation，无法执行
SLICE-001 冻结的最小 bounded-absence Case。

## Evidence

- Formal answer workload 构造 `WorldModelProductAnswerService` 时只有已验证的 `StructureViewService`、Snapshot Bundles 和模型
  Gateway，不读取 evaluator/product Oracle；
- 未携带召回权威的原 `STRUCTURE_ORDERED_READ_BUNDLE@1` 在零候选测试中保持 Limitation；
- 增加的 `STRUCTURE_ORDERED_READ_BUNDLE@2` 只密封 pre-question Oracle ref/result digest、exact Profile/discovery Contract、Snapshot/
  Bundle digest、冻结的三类反例 verdict 和 binding digest，不含问题、源码、Evaluator payload 或答案；
- 平台内部 Trace 保留该 binding 以重放完整性结论，但 Draft/Review 的模型输入只投影 typed steps、trace digest 和三层 verdict，删除
  `discovery_oracle`、`oracle_ref` 与 result identity；真实 Gateway 的 forbidden-input policy 因此不会接收 Oracle 字段；
- Formal workload 从同一个已登记 Read Set 自动取得该 binding 后能给出 `BOUNDED_ABSENCE`，同时
  `product_oracle_read_count=0`；binding 字段、result digest、Snapshot/Bundle 或 Profile 漂移均失败关闭；旧 `@1` bytes/digest 与行为
  保持不变。

## Impact and classification

System Contract 已要求 Oracle 独立、提问前冻结、绑定 exact authority，且 Answer 进程不得挂载评测 Oracle；发现的是该既有语义在
Read Bundle DTO/file adapter 中没有权威承载位置。`implementation-query.md` 已明确 DTO 与状态由代码和测试定义，因此本变更不改变
Owner、安全边界、Oracle 语义或验收 Case，分类为 `local-implementation`。

## Decision and disposition

召回证明只允许作为有版本的 ordered Read Authority binding 进入 Answer：绑定必须引用 exact Snapshot Bundle、Profile、活动
`JAVA_IMPLEMENTATION_FEATURE_INDEX@1` discovery Contract 和独立 result digest。Application 不信任任意运行时注入；显式 Oracle 也必须
与已密封 binding 完全相等。无 binding、UNKNOWN verdict、旧 `@1` envelope 或任何漂移仍返回具体 Limitation，不能从分页结束或
Coverage COMPLETE 推导第三层。完整 binding 只由平台 authority chain 使用；模型只获得受控 completeness projection，不获得 Oracle
身份或结果字段。

主处置进入 `structure_read_bundle.py` 及 strict file adapter/调查测试；无需修订 System 文档，因为当前规范已经拥有上述语义和边界。

## Verification after disposition

- `@1` ordered envelope 的 canonical bytes/digest 与历史回归不变；
- `@2` binding round-trip、tamper、Snapshot/Bundle/Profile fence 由 strict parser 和 View 验证；
- bounded session 分别覆盖无 binding 的 Limitation 与三层独立 COMPLETE 的 bounded absence；
- Formal Web asset test 证明同一 Answer workload 使用 Read Authority binding，且不读取 product Oracle 文件。
- Formal bounded-absence test 同时证明所有 Investigation/Draft/Review sealed model inputs 均不含 Oracle ref/result 字段。
