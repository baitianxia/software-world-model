---
id: ITER-010-RESULT-V-COGNITION-ELIGIBILITY-001
kind: iteration-result
status: passed-local-cognition
authority: execution-evidence
owners: [application, knowledge, source, quality, interface, project]
depends_on: [ITER-010-PDR-005, ITER-010-VERIFICATION, ITER-010-RESULT-V-LAYER-ATTRIBUTION-001, FINDING-010-132, FINDING-010-134, FINDING-010-135, FINDING-010-136]
code: [src/software_world_model/application_services/engineering_question_cognition.py, src/software_world_model/application_services/conversational_engineering_tools.py, src/software_world_model/application_services/java_source_semantics.py, src/software_world_model/interface/engineering_chat_session_artifact.py]
tests: [tests/test_engineering_question_cognition.py, tests/test_conversational_engineering_tools.py, tests/test_engineering_chat_session_artifact.py, tests/test_java_source_semantics.py]
iteration: ITER-010
case_id: V-COGNITION-ELIGIBILITY-001
case_verdict: PASS
external_model_calls: 0
source_reads_during_projection: 0
acceptance: NOT_ACCEPTANCE
production_activation: NOT_EXECUTED
---

# ITER-010 V-COGNITION-ELIGIBILITY-001 本地工程认知资格 Result

## Verdict

`V-COGNITION-ELIGIBILITY-001: PASS / local-cognition-only`。同一 exact
`mall@0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` 上已形成固定顺序的 Maven 结构 Profile 与 Java 实现/行为 Profile；Application 用
`ENGINEERING_COGNITION_CAPABILITY_MANIFEST@1` 分别保留两个 Snapshot、Read Session、Read Set、Read Authority、Coverage、Gap 和
query capability，未创建 mixed-profile Snapshot 或 Read Set。问题资格同时匹配 material cognition dimension 与 versioned query
capability；Maven-only 行为题明确不合格。

结构、行为/调用流程、职责/失败边界三类冻结问题得到不同的正式 Context。Java Profile 提供可追溯的非 locator 正向调用关系，同时继续
公开 559 个 method implementation incomplete、866 个 representable unit unsupported，以及缺少 `STATE/CONSTRAINT` 的边界；没有从
空边、未命中或 Gap 推导不存在。artifact Session Configuration `@2` 已能把 ordered multi-Profile cognition 组合进既有 Session/Web
runtime；旧 `@1` 单 Profile配置仍可加载，但不能取得 multi-Profile 资格。

本 Result 没有执行 Provider/model、credential、listener、browser 或 live Source，也不通过
`V-CHAT-EXPERIENCE-001/V-CHAT-001/V-CHAT-QUALITY-001/V-CHAT-XD-001`、Comparison、Preview、Acceptance 或 Production。PDR-005
本 Result 密封时下一外部 Gate 尚未授权；后续
`local-user-message-utf8:sha256:15a8f8100f8cb6ac333edf85166cf572bb67a5e69d5a731a75c574d36fa5a4e4` 已授权一次
受限 direction canary，但不追溯改变本 Result 的零外部调用边界。

## Exact capability binding

Application authority 固定为 repository `repository_0504e86b1f1b6f1b8aa6a734d37a90fb`、Binding
`binding_4ef0d3446b3e44c79ed3c0ffc855d5c9` 和上述唯一 revision。组合 Manifest digest 为
`sha256:bf8a416f6866bce7015946aac6ee2e19073d897ca33a76ffc76316f4eb643792`。

| Profile | Exact authority | Positive capability | Coverage / Gap |
|---|---|---|---|
| `MAVEN_REACTOR_STRUCTURE@1` | Snapshot `structure_snapshot_5033a7fc944141d08ecd5ad3879ce1ba`；Snapshot Bundle `sha256:aba230958a990ed7e7a2f8069a34de50e23bd35b6e4dcf274189c3cb1b9b6b6a`；ordered Bundle `sha256:4843f67eeae273a87d0aacb22598442ef77ea7fc8019dbc425f1460f4b633fb4`；Read Authority `sha256:9cd68a23017fcd3ca6d91d5f63cd49021038e29f0a327c710c9a4bd2cda01c16`；capability digest `sha256:8274b8d068e591d4ace31ddcd249440abc00aaf82f39b06baf4072d248d63e01` | `ENTITY/RELATION` 与 `direct_dependency@1`；8 Entity、15 Relation | 只覆盖 Maven module、containment 与 direct dependency，不取得 Behavior、State 或 Constraint |
| `JAVA_SOURCE_SEMANTICS@1` | source Binding `binding_141b6af98149457f9ffe394c071e3175`；Snapshot `structure_snapshot_30c29cee2db34077b5f2123c82fa7323`；Snapshot Bundle `sha256:dd3d7e97d64fe158fe0596bf9784ae73abfdf6f65194b5ac83643bd59ca14744`；ordered Bundle `sha256:1d16dd3b288a8fae20b3b92e0d69859f58f5134e012d013171f7946e6c4de132`；Read Authority `sha256:1e8e9452a1818e796a63167b626ba4dff04c3bab24ca40797fcbce1a43c3265a`；capability digest `sha256:63e6b3fd82738af1f37015ffa521afb3107b772483de7824b2288d1ed4e308d9` | `ENTITY/RELATION/BEHAVIOR` 与 `method_implementations@1`；914 Entity、681 Relation、0 Literal | 153 file、154 named type、559 member method 均有 disposition；48 个 implementation atom；559 implementation incomplete、866 representable unit unsupported；`STATE/CONSTRAINT` unavailable |

Maven Read Session `structure_read_session_14e79326bedb4db49bf1258fb82dc650` / digest
`sha256:b78fabe0275ef8a79d5d9256584461c2bc02aa3aa78bf71eb807cf60b2b114bf` 与 Read Set digest
`sha256:9be2661641d2e28505eb7574bc7ea0f9bea79fd8aca382f3056098640e493b31` 保持原 authority。Java 使用独立 Read Session
`structure_read_session_fef388d874d74106b85c05fe1651429b` / digest
`sha256:345a0b3a0be7f572656841019ea8a92402cc1f5b0aeb9262b581deee6dd3e26a` 与 Read Set digest
`sha256:c5232cde7fd03a2aa40c59114756fad4b70c453d8e5e8a3a6ccd323e2a993614`。Java ordered/Snapshot files 分别绑定 file digest
`sha256:b3ecdae2d7d0ecbff3cb1bf0d57a88b9bfcea301c89b1ec6ef82b90ac6866204` 与
`sha256:4e943e00809978c75ec309e9b846e02a26ec18ea0c9d2a694e191d7f79070a90`。通用 disposition path 不改变 legacy-complete closure：只有旧
exact closure 发布 `CALLS`；普通 Java 只发布同 declaring type、unqualified/`this`、name+arity 唯一解析的正向 `CALL_SITE_TARGETS`，并使
所有不完整 facet 和 nested executable boundary 显式可见。

## Frozen question eligibility and projection

Need 始终由 original question 生成；Agent 的 semantic query 只重排该 Need 下的相关正式项，不能改写资格。投影只读取上述已验证 Bundle，
不持有 Source handle，也不把后续 Source observation 回填成 World Model contribution。

| Frozen category / question | Required Need | Eligibility and projection | Exact result |
|---|---|---|---|
| 结构：`mall-admin 模块依赖哪些内部模块？` | `ENTITY + RELATION`、`direct_dependency@1` | Maven Profile eligible；Java declaration Profile 不因宽泛 Relation 标签进入结果；无 relevant Gap | Context `sha256:985e8b0059fab70c04e8a508f13777f0af60661c333ac3a9e57ba048c06166f4`；26 项中 23 项为 support；正式非 locator 关系含 `mall-admin DEPENDS_ON mall-mbg` 与 `mall-security` |
| 行为：`管理员登录实现会调用哪些同类方法？` | `ENTITY + BEHAVIOR`、`method_implementations@1` | Java Profile eligible；Maven-only assessment 同时缺 Behavior 与 query capability | Context `sha256:23534d124053e91aef8e9e7cddb47d7da0841447c11cc7d8fa45344c91311144`；35 项中 32 项为 support；保留 incomplete/unsupported Gap |
| 职责/失败边界：`登录失败职责、状态和配置边界是什么？` | `ENTITY + BEHAVIOR + STATE + CONSTRAINT`、`method_implementations@1` | Java 只满足 behavior sub-need；overall assessment 对 `STATE/CONSTRAINT` 明确不合格 | Context `sha256:478a6c93f8f447a64c25c5f743e3ef24a38f5b40dcc8ea01d20253f56bd096f2`；36 项中 32 项为正向 support；责任、状态与配置边界不从 call fact 扩张 |

行为 Context 中的五项问题相关正向事实为：

- `login → loadUserByUsername`；
- `login → insertLoginLog`；
- `insertLoginLog → getAdminByUsername`；
- `loadUserByUsername → getAdminByUsername`；
- `loadUserByUsername → getResourceList`。

每项关系都绑定 exact declaring method、implementation atom、Evidence metadata 与 Java Profile authority，不是 Source locator、文件名命中或
模型生成结论。

## Session/Web binding and compatibility

`SWM-ENGINEERING-CHAT-ARTIFACT-SESSION-CONFIG@2` 逐 Profile 固定 zero-based ordinal、Profile/Schema/Source Binding、selected
Snapshot、ordered Bundle/file digest 及每个 Snapshot Bundle/file digest。loader 在创建 projector 前重新计算全部 file/Bundle digest 和
Profile identity，并把多个独立 projector 组合为 Application-owned cognition authority；任一 drift 失败关闭。Preparation 与 query-time
`WORLD_MODEL_QUERY` 不触发 Source、credential 或 Provider，query-time successor Context 继续绑定同一 Turn Request 与 Manifest，并向
Ledger 追加新的 `COGNITION_CONTEXT` receipt。

兼容路径只让 `@1` 配置归一为单 Profile并继续运行；它不会被标记为多 Profile资格。现有 Web transport、rendering 与失败显示没有修改，
本地 runtime composition test 使用真实 Session 链但 fake Provider boundary；因此这里的“接回 Web”是可执行本地组合证据，不是 live
Browser/Provider 质量证据。

## Verification and scope

- Java semantics、Need/Manifest/projector、query-aware tool ledger 与 artifact Session targeted suites 全部通过；
- exact mall Java workspace/Snapshot/Bundle 构建成功，153 个文件全部 parse clean；projection 期间 Source read 为 0；
- Provider/model call、credential resolve、listener、browser、Production Activation 均为 0 / `NOT_EXECUTED`；
- `V-LAYER-ATTRIBUTION-001` 与本 Case 已 PASS，但 PDR-005 后续真实语义链、两个未参与修复的异质问题、独立质量审核和三臂比较仍为
  `NOT-RUN`；ITER-010 整体保持 `REWORK / NOT_ACCEPTED`。
