---
id: FINDING-010-261
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [knowledge, source, application, quality]
depends_on: [ITER-010-PDR-014, FINDING-010-257, SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS, ITER-010-VERIFICATION]
code: [src/software_world_model/knowledge_engine/capability_cognition.py, src/software_world_model/application_services/java_capability_cognition.py, src/software_world_model/infrastructure/file_capability_cognition.py, src/software_world_model/interface/java_capability_cognition_cli.py]
tests: [tests/test_capability_cognition.py, tests/test_source_operations.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: adopt-exact-source-capability-cognition-query-projection
target: SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS
---

# FINDING-010-261：同一 exact Source 可形成跨问题复用的最小认知纵切

## Observation

Phase B 从 mall exact revision `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`、tree
`047d79d8588b76013c260f3f1a9565707301a60a` 在任何问题出现前一次构建认知。冻结 tree-sitter Java frontend 解析 276 个 Java 文件，形成
1,666 个 module/package/file/type/method 实体、7,341 个 contain/import/inherit/invoke 关系和 4,849 个 condition/exception/state/call/
return 行为；artifact 保留逐项 provenance、Coverage、Conflict/Unknown 和 exact Source binding。

实现证据同时表明，这一 Alpha 读模型若取得自己的 CURRENT 或正式 publication 语义，会与现有 Formal/Structure/Java Source Semantics
形成平行真相。因此它被限定为复用冻结 frontend 和 exact Source contract 的 immutable query projection：没有 CURRENT、跨版本连续性或
闭世界负向权威，只能通过三个有界通用操作进入 Agent Session。

## Evidence

- canonical private artifact `var/iteration-010/pdr014-cognition/build-002/cognition.json` digest 为
  `sha256:eda4d8a162287b905f565e7b199526d15ee2ca03f6f653518d2eecddddeb4acc`，构建文件 276/276、partial 0、conflict 0；
- 五个独立任务覆盖 portal 入口层级、入口到 service invoke、admin implementation inheritance、购物车条件/协作者/return 和搜索 repository
  外部 Unknown，`build-002/report.json` 为 5/5 PASS；report digest 为
  `sha256:828b27a553379599bc1faca55134fcf9561011fe4a79da2b8a51b5791818f701`；
- 五题的 search page 均返回同一 snapshot digest；外部 `saveAll` 保持 `PARTIAL + Unknown`，没有伪造内部实体；
- 26 项 cognition/source 定向测试验证构建、source order、search/traverse/detail 分页复用、external Unknown、canonical digest、0600
  write-once artifact 和 exact revision/tree 绑定。

## Disposition

Java Source Semantics Contract 接受上述 Alpha capability-cognition query projection 及其与正式 Snapshot 的隔离边界。
`V-WORLD-MODEL-COGNITION-001` 记为 PASS；Phase C 只能把这三个工具接入 Phase A 的同一个 Agent，并继续用 Source Citation 补证，不能把
本 Finding 扩张为正式 Profile acceptance 或产品质量结论。
