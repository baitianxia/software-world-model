---
id: SYS-ARCH-COMPONENTS
kind: system-architecture
status: current
authority: normative
owners: [architecture]
depends_on: [SYS-ARCH-OVERVIEW, SYS-ARCH-INVARIANTS]
code: [src/software_world_model]
tests: [tests/test_foundation.py, tests/test_interface_runtime.py]
---

# 组件与依赖边界

| 组件 | 拥有的权威 | 允许依赖 | 禁止事项 |
|---|---|---|---|
| Interface | 协议解析与展示 | Conversational Task Control、Application Use-case Services、Response Control 的交付端口 | 直接访问 Repository 或决定业务状态 |
| Application Use-case Services | Management、Knowledge Update / Use、Evaluation 的 Attempt 与不可变 Result | 领域公共 Port、Model Gateway | 复制领域权威或建立跨 Owner 大事务 |
| Conversational Task Control | Task、Revision、Grant、Agent Invocation、Action Authorization 与 Application Dispatch | Agent Proposal、Application Services、Response Control 的不可变 Result / Assertion | 实现领域用例、修改 Response Control 私有状态或绕过授权分派 |
| Response Control | Answer Candidate、Review Decision、Final Authorization、Dispatch 与 Logical Delivery | Reviewer Proposal、Task / Application 只读 Assertion、Delivery Adapter | 修改 Task 或领域 Result、让 Reviewer 自行放行或发送正文 |
| Agent Roles | 无权威业务状态；只产生 Proposal / Assessment | 经授权的 Application Services、Model Gateway | 直接访问 Core、Repository、Source Tool，或自行授权、准入、发布、放行 |
| Source Integration | Data Source、Binding、Source Operation、Artifact | Provider/Tool Adapter | 形成正式知识或替模型扩权 |
| Knowledge Engine | Scope、Schema、Context、正式知识、Admission、Snapshot | 自有 Repository Port | 访问外部来源、读取模型会话、交付答案 |
| Model Gateway | 模型调用记录、适配和隔离收据 | Provider Adapter | 拥有领域 Strategy、执行领域 Tool、接受结果为真 |
| Infrastructure | 各 Owner 的持久化实现 | SQLite/外部技术 | 改变领域语义或绕过 Port |
| Cross-cutting | 标识、Digest、错误投影、Telemetry | 权威结果的只读投影 | 成为第二业务权威或放行门禁 |

生产实现保持模块化单体，以进程内调用实现这些逻辑边界。Application Layer 是逻辑分区，不是单一状态 Owner；其中的 Use-case Services、Task Control 和 Response Control 只交换不可变 Reference、Result 和只读 Assertion。任何逻辑 Owner 和事务边界都不能因部署在同一进程而被合并。
