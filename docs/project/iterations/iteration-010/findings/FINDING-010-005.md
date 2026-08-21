---
id: FINDING-010-005
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, source, architecture, security, quality]
depends_on: [ITER-010-SLICE-001, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-QUALITY-SECURITY]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/interface/engineering_qa_source.py, src/software_world_model/interface/engineering_qa_browser.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_qa_source.py, tests/test_engineering_qa_browser.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: bind-evidence-classification-to-an-exact-versioned-source-profile
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-005：模型或 Worker 声明不能决定来源证据类型

## Observation

Local Git Worker 首轮实现把 Proposal 的 `evidence_class` 传到 Broker operation 和 Retrieval Item，但只用 Request 的全局 path
allowlist 过滤实际文件。因而模型可以把 `README.md` 声明为 `BUILD_CONFIGURATION` 后 search/read/parse；只要路径位于全局
allowlist，Worker 就会按模型声明生成配置类 Result。内容和 revision 仍是真实的，但 evidence class、对应 byte fuse、modality 和后续
admissibility 可能错误。继续检查还发现 Worker 的 Result modality 没有由 Broker/Profile 预先固定；一个错误或恶意 Worker 可在 class/path
正确时把静态文本标成更强的执行观察。

## Evidence and root cause

- Request 原本只绑定全局 source allowlist，没有绑定 Source Profile identity；
- Broker 会拒绝非 retrieval class，却没有从受信配置验证该 class 对哪些路径成立；
- Worker 在 exact Git tree 中只取全局 allowlist 的交集，并直接把 operation 的 class 写入 Result；
- Compiled operation 原先没有 expected result modality，Application 因而只能验证 Worker 自报 modality 的格式，不能验证它是否与
  Source/Profile capability 和 operation 相符；
- 因此“README 路径 + BUILD_CONFIGURATION class”能越过 Worker 的来源类型边界。确定性复现证明这不是 Source injection、Git
  revision 或路径逃逸问题，而是受信分类 authority 缺失；
- 既有契约要求来源差异由显式、版本化 Source/Profile capability 拥有，但没有机械规定 Profile identity 必须贯穿 Request、Broker
  operation、Worker Result validation 和 Package。

根因是全局读取权限和证据类型权限被合并：前者回答“可否读取这个路径”，后者回答“这个路径可否作为哪种 evidence class”。让模型
提供后者会使不可信语义 Proposal 取得分类权威。该缺口影响所有来源类型和后续证据判断，分类为 `system-contract / systemic`。

## Decision and disposition

- Request 在任何调查前绑定 Binding-scoped、versioned Source Profile ref/digest；Profile 由受信配置把 evidence class 映射到规范化路径
  capability，并把每个 class + operation 映射到 exact Result modality；模型、问题文本、仓库内容和 Worker 都不能修改。Local Git
  Profile `@1` 使用非空且跨 class 不重叠的保守路径映射；未来 Profile 若需多模态路径，必须以新的显式、可资格版本定义确定性歧义规则；
- Source Broker 同时验证 Request 的全局 allowlist 和 exact Source Profile，为每个操作编译不可伪造的 class-specific allowlist。
  read/parse locator 必须既由当前 Ledger 签发，又属于 Proposal class 的 Profile capability；
- Compiled Source Operation 绑定 Profile ref/digest、class allowlist 和 expected Result modality。Retrieval Worker 重验 Binding、Profile
  identity、完整 class allowlist、path membership 与 modality，并只读取全局 allowlist 和 class allowlist 的交集；
- Application 不信任 Worker 自报，重新验证每个 Result item 的 operation identity、declared class、全局路径、class-specific 路径，
  expected modality，且 read/parse 只能返回编译的 exact path；
- Question Evidence Package 绑定 Source Profile ref/digest，使 Answer、Review、Citation 与 successor Package 的证据分类可追溯到同一
  受信配置；浏览器固定 Request factory 同样必须提供 exact Profile identity。

主处置写入 `SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING`，并同步 ADR-016、安全边界、Slice 设计和本机浏览器运维说明。
本变化不按约定文件名推断类型，也不授权 Provider、外发、listener/browser session、live validation 或 Production Activation。

## Verification

确定性测试覆盖跨 evidence class 重叠 Profile 拒绝、Worker 拒绝把文档重标为配置、Local Git 文档读取使用 exact document modality、
恶意 Worker 返回另一 class 路径或把静态文本升级为执行观察时 Application 失败关闭，以及完整 Broker → Local Git Worker → Ledger →
Package 链。既有五角色状态机同时验证 Source Profile identity 进入 exact role input Manifest；完整回归仍需与最终文档和实现一起执行。
