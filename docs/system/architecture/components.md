---
id: SYS-ARCH-COMPONENTS
kind: system-architecture
status: current
authority: normative
semantic_owner: SYS-ARCH-BASELINE
authority_scope: controlled-architecture-appendix
owners: [architecture]
depends_on: [SYS-ARCH-BASELINE, SYS-ARCH-INVARIANTS]
code: [src/software_world_model]
tests: [tests/test_foundation.py, tests/test_interface_runtime.py, tests/test_structure_read_bundle.py, tests/test_structure_view.py, tests/test_citation_projector.py, tests/test_iteration_003_g2_isolation.py]
---

# 组件与依赖边界

> 本文件是架构基线的组件附录。它只细化 Owner、Port 和依赖边界，不得改变 [Software World Model 架构基线](architecture-baseline.md) 的顶层关系。

| 组件 | 拥有的权威 | 允许依赖 | 禁止事项 |
|---|---|---|---|
| Interface | 协议解析与展示 | Conversational Task Control、Application Use-case Services、Response Control 的交付端口 | 直接访问 Repository 或决定业务状态 |
| Application Use-case Services | Management、Direct Evidence Answering、World Model Query、Engineering Conversation、Knowledge Update / Use、Knowledge Maintenance Task、Capability Strategy 的资格与受控激活记录；World Model Cognition Context、当前 Turn Evidence 与临时 Evidence Package | 领域公共 Port、Model Gateway、Response Control、只读 View | 复制领域权威、让任务证据包冒充正式知识、让严格世界模型查询回源、把世界模型降格为 locator 缓存，或建立跨 Owner 大事务 |
| Conversational Task Control | Conversation、Turn、Agent Work State Revision、Grant、Agent Invocation、Action Authorization 与 Application Dispatch | Agent Proposal、Application Services、Response Control 的不可变 Result / Assertion | 把 Provider hidden state 或先前答案当权威，实现 Source/Knowledge 领域用例，修改 Response Control 私有状态或绕过授权分派 |
| Response Control | Answer Candidate、固定 Evidence Packet、Question Evidence Package 或 exact Snapshot Query/View 上的 Revision、Review Decision、Final Authorization、Dispatch 与 Logical Delivery | Reviewer Proposal、Task / Application 只读 Assertion、固定权威输入、Delivery Adapter | 修改 Task、Ledger、Package、来源证据或领域 Result，直接读取 Repository/Source Tool，让 Reviewer 自行执行补证、放行或发送正文 |
| Primary Engineering Agent | 无权威业务状态；产生 Goal、Hypothesis、Plan、Tool、Work-State 与 Answer Proposal，根据受信 Observation 重规划 | 经授权的 Application Services、Model Gateway、密封 Conversation/Work State、World Model Cognition 与 Ledger prefix | 直接访问 Core、Repository、Source Tool、Broker dispatch、shell、网络或 credential，把隐藏状态/先前答案当证据，或自行授权、准入、发布、审核、放行 |
| Independent Reviewer | 无权威业务状态；只审核当前 Turn/Package/Draft，并产生 Assessment 与具体 Finding | Response Control、角色限定的密封 Conversation Context 和 Question Evidence Package；经 Source Broker 的有界只读核验读取（V1.4） | 重新解决原问题、生成替代答案、继承主 Agent 会话、直接使用工具、扩大来源范围、把核验观察放入答案 Package、自行补证或放行 |
| Source Integration | Data Source、Binding、Source Operation、Artifact；Source Broker 的 policy decision 与 Retrieval Worker execution receipt | Provider/Tool Adapter；Broker 只编译受权注册操作，Worker 只执行 exact-revision allowlisted read-only operation；V1.4 起工具目录须满足基线 7.7 节工具对等，可在隔离沙箱中以注册只读命令实现 | 形成正式知识或问题结论，接受模型 Proposal 为授权，执行仓库内指令、模型自由拼接的任意 shell、新网络或写入来源 |
| Knowledge Engine | Scope、Schema、Context、正式知识、Admission、Snapshot | 自有 Repository Port | 访问外部来源、读取模型会话、交付答案 |
| Semantic View | 无新权威；只形成 exact Snapshot 的可重建只读认知、组织结果及 Coverage/View Limitation/Support Map/手册投影，以及 Cognition Retrieval Projection（V1.4） | Knowledge Engine 公共只读 Port | 创造知识、把投影冒充完整世界模型、直接访问 Repository/Source、按名称补关系、形成 Knowledge Gap 或决定 Sufficiency |
| Citation Projection | 无领域权威；只形成与密封 Result 精确绑定的 disposable observation Store 和浏览器展示 Projection | Broker 使用实际密封 Result 与窄 Knowledge Evidence Port；Projector 只使用 Result seal 与 exact Store | 让 Projector 直接访问权威数据库/完整 Evidence Store，扩大 Result allowlist，把正文回传答案链 |
| Model Gateway | 模型调用记录、适配和隔离收据 | Provider Adapter | 拥有领域 Strategy、执行领域 Tool、接受结果为真 |
| Infrastructure | 各 Owner 的持久化实现 | Owner-defined persistence Port | 改变领域语义或绕过 Port |
| Cross-cutting | 标识、Digest、错误投影、Telemetry | 权威结果的只读投影 | 成为第二业务权威或放行门禁 |

核心实现保持模块化单体；Application Layer 是逻辑分区，不是单一状态 Owner，其中的 Use-case Services、Task Control 和 Response Control
只交换不可变 Reference、Result 和只读 Assertion。`WORLD_MODEL` 的答案 worker 与 Citation Projector 继续采用文件与网络能力隔离。
Engineering Conversation 要求主 Agent、Source Broker/Worker 与独立 Reviewer 分离：主 Agent 只消费密封 Conversation/Work State、
World Model Cognition 和获准 Ledger Observation，通过 Proposal 使用工具；Broker/Worker 独占 exact-revision allowlist 上的只读执行；
Reviewer 只挂载当前用户 Turn、受信对话上下文、双分区 Package 与 Draft，并可经 Broker 做有界只读核验读取（V1.4）。Broker、Worker、Ledger、Conversation Store、进程拆分和出口
网关都不新增正式知识 Owner；Knowledge Maintenance Task 只是 Application 到 Knowledge Update 的异步维护入口，不是第二知识库或新的正式知识 Owner；
任何逻辑 Owner 和事务边界也不能因其余组件同进程而被合并。
