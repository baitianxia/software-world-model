---
id: FINDING-010-265
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, knowledge, quality]
depends_on: [ITER-010-PDR-014, FINDING-010-264, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/lightweight_engineering_model.py]
tests: [tests/test_lightweight_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: clarify-source-native-cognition-query-contract
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-265：轻量 Agent 必须按 cognition 的 lexical 能力提交源码原生查询，不能把用户语言转述当成语义检索

## Observation

ranking successor `pdr014-browser-alpha-run-005` 的 Ark transport 已恢复并连续完成五次 HTTP/model call，但事务 Turn 仍在 review 前被
Application Control 拒绝。最早偏差不再是固定英文诊断查询的排序，而是实际 Agent 把中文用户表述直接提交为 cognition query：
`mall-admin 用户注册 角色分配 事务 回滚`。该查询只命中带中文 `@Operation` summary 的 Controller `register`，Agent 随后只读
`UmsAdminServiceImpl`，再次错误声称 `updateRole` 没有事务声明。

## Evidence

- run-005 terminal `sha256:c8f753aaa0bdd979e1c09798bb6181db9c547072b73e0770d664979c1fef0f1a` 密封 1 Conversation / 1 Turn /
  5 Ark dispatch，TLS/HTTP `5/5`、output `5/5`、retry 0、DeepSeek dispatch 0、human approval request 0、Production `NOT_EXECUTED`；
- trajectory 依次执行 `SEARCH_COGNITION → RETRIEVE_COGNITION_DETAIL → SEARCH_SOURCE(UmsAdminServiceImpl) → READ_SOURCE → FINISH`；
  FINISH 选择了未交付的 Citation，因而以 `CONTROL_STATE_DENIED` 在 review 前关闭。浏览器没有显示错误答案，但该机械拒绝不证明语义审核
  识别了事务错误；
- unchanged cognition artifact 对实际中文 query 返回 `total=1`，唯一结果是
  `UmsAdminController#register(UmsAdminParam)`；对 source-native `mall-admin register role transaction rollback` 返回 `total=31`，首屏前二
  是 implementation `updateRole` 和带 `@Transactional` 的 interface `UmsAdminService#updateRole`；
- 该差异来自工具能力误用，不证明需要按中文、mall、role 或事务题添加索引别名。按工程、问题、关键词或语言注入检索规则会违反 current
  generality boundary。

## Disposition

在 capability-oriented Agent 的唯一 Owner Contract 中明确：cognition search 是 source-derived identifier/statement 的 bounded lexical
query，不是翻译或通用 semantic search；Agent 使用 repository-native identifier/technical token，不能只用 module name；物质 contract 可能位于
interface/supertype 时须先检查声明，不能从一个 implementation body 的缺失作负向结论。同一通用约束进入轻量 Agent 指令与 disclosure 测试，
不新增答案格式、正文校验、工程/题面分支、语言别名、Source authority 或 Provider retry。successor Browser 仍须用原事务题和两个异质问题复验。
