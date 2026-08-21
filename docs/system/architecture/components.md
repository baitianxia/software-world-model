---
id: SYS-ARCH-COMPONENTS
kind: system-architecture
status: current
authority: normative
owners: [architecture]
depends_on: [SYS-ARCH-OVERVIEW, SYS-ARCH-INVARIANTS]
code: [src/software_world_model]
tests: [tests/test_foundation.py, tests/test_interface_runtime.py, tests/test_structure_read_bundle.py, tests/test_structure_view.py, tests/test_citation_projector.py, tests/test_iteration_003_g2_isolation.py]
---

# 组件与依赖边界

| 组件 | 拥有的权威 | 允许依赖 | 禁止事项 |
|---|---|---|---|
| Interface | 协议解析与展示 | Conversational Task Control、Application Use-case Services、Response Control 的交付端口 | 直接访问 Repository 或决定业务状态 |
| Application Use-case Services | Management、Direct Evidence Answering、World Model Query、Engineering Question Answering、Knowledge Update / Use、Evaluation 的 Attempt 与不可变 Result；Question Checklist、Evidence Packet 与 Question Evidence Package | 领域公共 Port、Model Gateway、Response Control、只读 View | 复制领域权威、让任务证据包冒充正式知识、让严格世界模型查询回源、让 Snapshot hint 成为 Engineering QA 的 Source 召回门禁，或建立跨 Owner 大事务 |
| Conversational Task Control | Task、Revision、Grant、Agent Invocation、Action Authorization 与 Application Dispatch | Agent Proposal、Application Services、Response Control 的不可变 Result / Assertion | 实现领域用例、修改 Response Control 私有状态或绕过授权分派 |
| Response Control | Answer Candidate、固定 Evidence Packet、Question Evidence Package 或 exact Snapshot Query/View 上的 Revision、Review Decision、Final Authorization、Dispatch 与 Logical Delivery | Reviewer Proposal、Task / Application 只读 Assertion、固定权威输入、Delivery Adapter | 修改 Task、来源证据或领域 Result，直接读取 Repository/Source Tool，让 Reviewer 自行放行或发送正文 |
| Agent Roles | 无权威业务状态；只产生 Proposal / Assessment | 经授权的 Application Services、Model Gateway | 直接访问 Core、Repository、Source Tool，或自行授权、准入、发布、放行 |
| Source Integration | Data Source、Binding、Source Operation、Artifact | Provider/Tool Adapter；Engineering QA 的隔离只读 Retrieval Worker 只经受权 Port 调用 | 形成正式知识或问题结论，替模型扩权，执行仓库内指令或写入来源 |
| Knowledge Engine | Scope、Schema、Context、正式知识、Admission、Snapshot | 自有 Repository Port | 访问外部来源、读取模型会话、交付答案 |
| Semantic View | 无新权威；只形成 exact Snapshot 的可重建只读组织结果及 Coverage/View Limitation/Support Map 投影 | Knowledge Engine 公共只读 Port | 创造知识、直接访问 Repository/Source、按名称补关系、形成 Knowledge Gap 或决定 Sufficiency |
| Citation Projection | 无领域权威；只形成与密封 Result 精确绑定的 disposable observation Store 和浏览器展示 Projection | Broker 使用实际密封 Result 与窄 Knowledge Evidence Port；Projector 只使用 Result seal 与 exact Store | 让 Projector 直接访问权威数据库/完整 Evidence Store，扩大 Result allowlist，把正文回传答案链 |
| Model Gateway | 模型调用记录、适配和隔离收据 | Provider Adapter | 拥有领域 Strategy、执行领域 Tool、接受结果为真 |
| Infrastructure | 各 Owner 的持久化实现 | SQLite/外部技术 | 改变领域语义或绕过 Port |
| Cross-cutting | 标识、Digest、错误投影、Telemetry | 权威结果的只读投影 | 成为第二业务权威或放行门禁 |

核心实现保持模块化单体；Application Layer 是逻辑分区，不是单一状态 Owner，其中的 Use-case Services、Task Control 和 Response Control 只交换不可变 Reference、Result 和只读 Assertion。`WORLD_MODEL` 增加一个必要的部署安全例外：答案 worker 与 Citation Projector 必须是文件与网络能力隔离的独立进程，前者的应用输入只有 no-payload Snapshot Read Bundle，并只能通过 exact Model Egress Gateway 访问固定 Provider endpoint；后者只在结果密封后读取 Result seal 与 result-scoped disposable Citation Store、禁止出网且没有答案回传端口。`ENGINEERING_QA` 另要求 Retrieval Worker 与 Answer/Reviewer 分离：只有前者获得 exact-revision allowlist 上的只读能力，后两者只挂载密封 Question Evidence Package。Broker、Worker、进程拆分、Store 和出口网关都不新增领域 Owner；任何逻辑 Owner 和事务边界也不能因其余组件同进程而被合并。
