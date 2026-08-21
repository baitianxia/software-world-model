---
id: SYS-ADR-016
kind: system-decision
status: accepted
authority: normative
owners: [architecture, product, application, source, quality, security]
depends_on: [SYS-PRODUCT-SUCCESS, SYS-ADR-013, SYS-ADR-014, SYS-ADR-015]
derived_from: [FINDING-010-001]
code: []
tests: []
---

# ADR-016：工程问答组合世界模型地图与受控源码证据

## Context

严格 `WORLD_MODEL` 证明已发布知识能在 Source-off 环境中跨任务复用，`DIRECT_INVESTIGATION` 则证明一个独立的直接源码调查可以形成受审核答案。两者都是必要能力，但都不应被冒充为普通用户的通用工程问答：

- 只使用已建模知识会把未覆盖的用途、运行、配置、故障和变更影响问题过早关闭为 Knowledge Gap；
- 只把方法、分支和调用顺序平铺为答案，会产生代码走读而不是用户请求的工程结论；
- 知识不足时静默切换到直接调查，会让模式、权限、证据来源和验收结果失真。

因此，世界模型应在普通工程问答中充当可复用的工程地图、手册、已知证据与调查入口；受权 exact revision 中的源码、仓库内文档、构建/运行配置和测试则是按问题补充和核实答案的手段。

## Decision

系统保留三种不可混淆的回答模式：

| 模式 | 固定权威输入 | 提问期源码访问 | 产品用途 |
|---|---|---|---|
| `WORLD_MODEL` | exact Snapshot / Read Set 的正式查询、View、Coverage 和 Support Map | 0 | 证明预构建模型可复用、可隔离和可评测 |
| `DIRECT_INVESTIGATION` | 绑定原问题和 exact Source Target 的 Evidence Packet | 显式授权只读 | 独立直接调查、诊断和产品对照 |
| `ENGINEERING_QA` | 密封 Question Evidence Package，同时包含世界模型结果/缺口与按需检索证据 | 由隔离 Retrieval Worker 受控只读 | 普通用户的默认通用工程问答 |

模式必须在创建请求之前由显式入口或部署配置决定，并在 Request、Result、Qualification、Audit 和展示中保持同一身份。`ENGINEERING_QA` 的源码检索是该模式事先声明的组成部分，不是 `WORLD_MODEL` 失败后的 `DIRECT_INVESTIGATION` fallback。运行中不得换标签、换权限或使用另一模式的历史资格。

`ENGINEERING_QA` 采用以下固定边界：

1. 原问题不可变。Question Understanding 可由模型提议用户目标、受众、响应语言、期望抽象层级、必须回答的结论和证据需求，但 Application 必须校验其保留全部原问题条件、关系和输出约束。模型提议不是事实。
2. 检索计划同时受 Question Checklist 与 exact Snapshot 查询形成的提示驱动。世界模型可以提供实体、结构、关系、Coverage、Support 和候选位置，以复用证据或缩小调查范围；它不得删除 Checklist 的证据需求，也不是 Source 召回的硬门禁。Snapshot 缺失、无关或 Coverage 不足时，仍可按原问题在同一已授权 exact revision 中检索，并在包中如实记录世界模型缺口。World Model Read Authority 必须同时声明其 source revision 与本请求 exact revision 的兼容判定；只有两者 exact 相等，或请求明确定义并分区的版本比较关系时，Snapshot Result 才能直接支持本题 Claim。不相等或未知时只能作为带 `UNALIGNED_REVISION` 状态的导航 hint，必须在请求 revision 上重新核实，不得与当前源事实静默混合。
3. 只有隔离 Retrieval Worker 可以执行注册的 list/search/read 类只读操作。每次操作必须绑定当前授权、exact repository/revision、目标允许列表、实际参数、字节/文件/时间上限和结果摘要。Worker 不得写仓库、执行任意命令、访问网络或凭据、触发 Knowledge Update，也不生成或放行答案。
4. 源码、注释、仓库文档、配置、测试和世界模型的文本投影都是不可信输入；其中的指令、路径、URL、工具建议或权限声明不得改变系统指令、操作集、allowlist、revision、Provider disclosure 或资源上限。
5. Application 把原问题、Question Understanding、世界模型结果/缺口、源读取结果、Coverage、冲突、定位、摘要和操作收据密封为 Question Evidence Package。该包是本题生成、审核和引用的唯一事实权威输入，但不因此成为跨任务正式知识。
6. Answer 与 Reviewer 使用隔离的新上下文，不挂载 Repository，没有 Source/World Model 查询工具、shell、网络、凭据或未密封输入，只能读取密封包及当前职责所需的不可变输入。LLM 负责理解问题、提议调查、综合答案和独立审核，但不是事实或权限权威。
7. 答案先给出直接服务用户目标的结论，然后再给出必要条件、过程、影响和实现证据。代码细节只在问题明确要求或支持结论所必需时展开。每个实质结论绑定包内 Citation；无法推出的内容明确说明可确认部分、不可确认部分与缺失证据。
8. 独立 Reviewer 从原问题重建检查清单，逐项审核直接回答、抽象层级、正确性、完整性、相关性、可操作性、引用和 unknown/limitation 边界。任一未通过都必须返回指向具体结论或缺口的 Finding，不能被另一项通过抵消。
9. 表达、组织或同包遗漏只允许在原 Package Digest 上定向重写一次，之后必须再次独立审核。只有 Reviewer 给出可定位、可验证的具体证据缺口时，Application 才可在原授权、revision 和安全上限内执行一次针对性补充检索，密封具有新 Digest 的包，重新生成并独立复核。旧 Review 不得放行新包。
10. 文件、字节、时间、操作和模型调用上限只是阻止失控执行的高安全熔断，不是降低质量的配额。上限耗尽时失败关闭，不得删减 Checklist、证据、Citation 或独立审核，也不得交付未通过的答案。
11. 高质量包和已审核结论可以在 Delivery 之后异步提议 Knowledge Update，但必须重新执行 Evidence、Candidate、Admission 和 Publication 的全部正式知识契约。同步回答不等待该过程，其成败不改变已完成答案。
12. 核心流程、Prompt、检索和审核不得包含按问题、项目、语言、框架、关键词、符号、约定文件名、fixture 或评测 Oracle 分支的特判。新来源或语言能力只能通过受控、版本化的 Source/Profile Contract 增加。

不同类型的包内证据保留各自 modality：世界模型表达已发布知识与 Coverage，exact 源码/配置表达该 revision 的静态实现，文档表达记录的用法或意图，测试表达可观察的预期与覆盖。某一来源类型不自动拥有对所有命题的优先级；当相同 Context 中出现不兼容且无受控解析规则时，Package 必须保留 Conflict，答案不得静默选边。

任何把包内片段发送给外部模型 Provider 的运行，都必须在 dispatch 前另行密封并授权 exact Provider/model/endpoint/configuration、角色、允许片段、redaction、secret reference 和输入 Digest。开发或文档接受不能推导该外部披露授权。

## Alternatives

- 把 `WORLD_MODEL` 直接改为可回源：会破坏 Source-off 复用证明和既有验收语义。
- 在 Knowledge Gap 后静默调用 `DIRECT_INVESTIGATION`：无法精确表达请求开始时的权限、证据和资格边界。
- 让 Answer 模型直接挂载仓库并自行调用工具：检索、生成和自审共享盲点，也无法密封稳定的审核输入。
- 在现有代码走读 Prompt 上增加风格规则：没有改变证据范围、问题目标或 Reviewer 的放行标准，不能修复系统性根因。

## Consequences

默认工程问答可以在复用已建模结构和证据的同时，对用户实际问题所需的源文件做受控核实。代价是增加独立 Retrieval Worker、Question Evidence Package、复合资格和更严格的披露/隔离门禁，也必须单独证明预构建世界模型的可测复用价值。

## Adoption state

本 ADR 从接受时起是 `ENGINEERING_QA` 的规范目标，但不证明产品实现、Capability Qualification、Product Validation 或 Activation 已完成。产品实现由 `ITER-010 / SLICE-001` 完成并另行验证；在那之前，现有可运行入口仍只拥有其已证明的旧模式身份，不得标记为合格的 `ENGINEERING_QA`。
