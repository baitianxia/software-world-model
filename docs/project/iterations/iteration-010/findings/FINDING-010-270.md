---
id: FINDING-010-270
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [knowledge, application, quality]
depends_on: [ITER-010-PDR-014, FINDING-010-261, FINDING-010-263, FINDING-010-264, FINDING-010-269, SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/knowledge_engine/capability_cognition.py, src/software_world_model/application_services/java_capability_cognition.py, src/software_world_model/ai_infrastructure/lightweight_engineering_model.py]
tests: [tests/test_capability_cognition.py, tests/test_lightweight_engineering_agent.py, tests/test_lightweight_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: make-source-bound-declaration-implementation-cognition-closure-explicit
target: SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS
---

# FINDING-010-270：查询时签名伴随不能替代 Source-bound 声明—实现认知闭包

## Observation

Phase B 首版 cognition artifact 已有 type inheritance、method body 和 annotation Source 内容，但 method 查询只在索引构造时按文本签名从
implementation 单向拼接 ancestor method；没有发布可遍历的 method implementation → interface/parent declaration 关系。entity summary
省略声明属性和注解，detail relation 也不返回双方 endpoint provenance；snapshot 自身的 Conflict/Unknown 没有出现在每个查询页。结果是知识
内容“存在”却不能在固定结果预算内稳定形成实现、声明、关系来源和认识论边界的完整闭包。

真实 mall 查询还暴露了另一个 cognition-retrieval 缺口：只保留 CamelCase 拆分词元会丢掉复合 owner identifier 的辨识力。常见词元形成大量
行为命中，真实 implementation/declaration 虽已建成，仍可能被挤出有界首屏。这不是题面或回答 Prompt 问题。

## Evidence

- 基线 artifact `sha256:3d31273…` 在 mall-admin 153/153 Java files 上形成 877 entities、3549 relations 和 2198 behaviors；
  `UmsAdminServiceImpl#updateRole` detail 没有显式 method contract relation，查询 summary 也没有 annotations/attributes。
- 当前 exact Source `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`、tree
  `047d79d8588b76013c260f3f1a9565707301a60a` 的七个 `src/main/java` roots 构建 artifact
  `sha256:d552b3d8df62271ac24c85d82fcf046eb67852397eb923212f7f1eb21ba7a243`：519/519 files parsed、15465 entities、
  33866 relations、29435 behaviors、0 Conflict、4 个明确 snapshot Unknown。它包含 142 条 type-scope `IMPLEMENTS` 和 296 条
  method-contract `IMPLEMENTS`；296 个具备内部声明的 implementation methods 全部形成关系，其中 294 `COMPLETE`，2 因多个 wildcard
  import candidate 如实为 `PARTIAL` + Unknown。
- 原问题 `UmsAdminServiceImpl updateRole` 与异质方法问题 `PmsProductServiceImpl create` 的有界 search 都把 implementation/interface
  declaration 放在前两位；method traverse/detail 同时返回双方 Java 文件、类型 `implements` clause、`@Override` 和 11/19 条 direct invoke
  relations。异质类型问题 `PmsProductResult` 可遍历到内部 `PmsProductParam → PmsProduct`，并把外部 `Serializable` 标为
  `EXTERNAL / PARTIAL / type implementation is outside selected Source coverage`。
- 通用复合标识符保留后，full artifact 上 `PmsProductServiceImpl create` 从目标不在前 24 项变为 implementation/declaration 占前两位；
  fixture 中另放入只含拆分词元的 behavior noise，仍由真实声明闭包占前两位。
- 开发侧 capability/Agent/model 定向测试合计 20/20 PASS；其中 visibility fixture 证明跨 package 的 package-private 父类方法不形成
  method contract，同 package package-private、跨 package public/protected 与 interface implicit-public 均保留。独立监督重放另一份跨包
  fixture 得到同一结论；泛型 fixture `I<T> / C implements I<String>` 不伪造 method relation，并在 snapshot 和 search page 披露
  `generic type-variable substitution or unresolved signature namespaces` Unknown。监督在 dirty candidate 上重建同一 digest，并用预先
  密封、未参与实现的五个
  异质任务复用同一 snapshot 得到 5/5 PASS。监督证据位于 supervision lane 的
  `var/supervision/held/dirty-f9ef8d06-cognition.json` 与 `var/supervision/held/dirty-run-006-report.json`，report digest
  `sha256:4c37f98fadd34fd51a0c0fe217307b22d58118d1ba4b8037273cb52b51124f7f`；该报告明确
  `candidate_clean=false / advance_eligible=false`，所以它不是 Phase `ADVANCE`。

## Affected scope and classification

受影响对象为 `ITER-010-SLICE-001`、`V-WORLD-MODEL-COGNITION-001`、
`SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS`，以及 Application 对已注册 relation enum 的机械传播。分类为
**system-contract / systemic**：relation kind/scope、Source provenance 和查询页认识论状态是 knowledge 的可观察契约，不能只留在代码或
测试；Engineering Conversation 已用通用的 registered relation kind 约束模型参数，不需要新的 Prompt 或 Application 语义。

## Disposition

Java projection 在 artifact construction 时发布显式的 type `INHERITS/IMPLEMENTS` 和 method-contract `IMPLEMENTS`。方法匹配只使用通用 Java
声明语义：内部 ancestor graph、method name/arity、erased parameter candidates、显式/同包/implicit `java.lang`/wildcard import；private、
static、constructor 和没有 implementation body 的方法不冒充实现。interface 方法保留 implicit-public 语义；class public/protected 声明可跨
package 继承，package-private 声明只有在整个 inheritance path 与声明类型同 package 时才能形成关系。歧义不猜测，关系降为 `PARTIAL` 并写
Unknown。若内部 ancestor 的同名同 arity candidate 实际引用 type parameter，当前投影不扩张成 generic solver：保留已独立证明的正向
关系，对无法完成的 substitution 不建边，并加入 snapshot/page-level Unknown。关系携带 scope、contract kind、inheritance path 和实际
clause provenance，query detail 同时返回 implementation/declaration endpoint provenance。

索引只依据 artifact 中已发布的 method relation 双向展开 companion，并同时索引完整 repository-native compound identifier 与通用 CamelCase
词元；不增加工程、题目、类名、方法名或路径特判。所有 cognition page 返回 snapshot-level Coverage/Conflict/Unknown。对应 Java 与 Engineering
Conversation 的既有 registered-relation 规则一致，唯一规范写回位于 Java Owner Contract；没有修改回答 Prompt、回答结构协议、Reviewer、
Provider recovery 或 Phase C/D 行为。

本 Finding 的处置只闭合实现与契约，不产生阶段结论。只有监督方在 clean exact product commit 上重新构建 artifact、运行其独立密封五题并
写出 `ADVANCE`，Phase B 才能退出。

