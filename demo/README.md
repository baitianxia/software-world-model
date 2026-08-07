# Software World Model 验证 Demo

这个目录是用于证伪或验证一般架构的轻量纵向切片，不是生产实现，也不预先决定平台最终使用 Python 或 SQLite。

当前实现了验证基线中的五个主干切片、针对首轮产品留出失败补充的 V0.6 纠偏切片，以及由 V0.7 真实模型诊断触发的最小契约修正：

```text
CLI / Scheduler ───────────────→ Application Services
                                      ↓
Connector Provider → Connector Tool → Source / Derived Artifact
                                      ↓
                               Knowledge Engine
                                      ↓
              Evidence → Entity → Fact → Inference → Snapshot
                                      ↓
                Structure / Behavior / Business / History

Web Chat → Agent Orchestrator → Task Execution Agent
                                      ↓
                              Application Services
                                      ↓
                  Answer Candidate → Answer Review Agent
```

实现刻意保留以下边界：

- Connector Provider 负责配置和能力发现，Connector Tool 执行有界读取并输出 Artifact。
- Java Source Artifact 由 Tree-sitter 处理为带 Lineage 的 AST Derived Artifact。
- Knowledge Engine 从 Artifact 构建 Evidence、Entity 和 Fact。
- Knowledge Verifier 独立复核引用、上下文、内容哈希、关系和 Inference 支持范围。
- Application Services 协调 Source Integration 和 Knowledge Engine，二者不直接依赖。
- 四种 Semantic View 只读取当前 Snapshot 中的正式知识，不读取源文件。
- Agent 可组合四类通用正式知识能力：固定 Snapshot 上下文、搜索 Entity / Inference、读取单跳 Fact 邻域、批量解释 Fact / Inference；固定 View 不再是正式知识的唯一读取方式。
- Task Execution Agent 通过模型规划、平台约束的有界 Tool Loop 组合上述能力；Scope、Snapshot Token、阶段上下文和步数预算由平台控制。
- Knowledge Gap 可派生冻结的 Build Intent，在隔离 Investigation 中读取任意 Git Revision、提出 Candidate，并在准入后以 replacement 或同 Revision enrichment 发布完整 Snapshot。
- 模型 Candidate 只提供受限语义字段与 Evidence locator；平台重建 quote/hash、revision、稳定 ID、Scope 和 model-call provenance。
- Candidate 契约错误可在同一 Investigation 中进行最多三次总提议尝试（首提一次、纠错重提最多两次）；耗尽后返回受控失败且不发布。
- Candidate-only 验证模式会使既有 Builder fail-fast：Direct Fact 与基于正式前提的 Inference 必须通过两次独立 Publication 形成，同 Bundle Fact、错误 target 和跨方法混合 premise 均被拒绝。
- Knowledge Use 拒绝不兼容的 Snapshot Knowledge Schema，enrichment 不能跨不兼容 Schema 继承 Base。
- 通用读取结果显式声明知识覆盖状态；覆盖未声明、查询为空或结果被截断时，不得据此推断对象不存在或结果唯一。
- Web Chat 经过动态 Agent 编排和独立 Answer Review；CLI 与 Scheduler 直接调用固定用例。
- SQLite 只是共享物理存储；Artifact 和正式知识仍通过不同模块方法维护逻辑所有权。

## 运行

从仓库根目录执行：

```bash
DEMO_DB=/tmp/swm-demo.sqlite3
PYTHONPATH=demo python3 -m swm_demo --db "$DEMO_DB" configure \
  --scope system:mall \
  --name mall \
  --source validation-projects/mall \
  --expected-revision 0504e86b1f1b6f1b8aa6a734d37a90fb67346be7

PYTHONPATH=demo python3 -m swm_demo --db "$DEMO_DB" update \
  --scope system:mall \
  --profile full-validation

PYTHONPATH=demo python3 -m swm_demo --db "$DEMO_DB" structure \
  --scope system:mall

PYTHONPATH=demo python3 -m swm_demo --db "$DEMO_DB" endpoint \
  --scope system:mall \
  --name "POST /order/generateOrder"

PYTHONPATH=demo python3 -m swm_demo --db "$DEMO_DB" view \
  --scope system:mall \
  --name behavior
```

模型主导调查使用同一组 Application Service 的 CLI 调试入口。先固定当前 Snapshot：

```bash
PYTHONPATH=demo python3 -m swm_demo --db "$DEMO_DB" knowledge-open \
  --scope system:mall
```

随后把返回的 `snapshot_token` 传给搜索、单跳遍历和批量解释；Search 与 Neighborhood 在 `has_more=true` 时使用 `next_cursor` 继续读取：

```bash
PYTHONPATH=demo python3 -m swm_demo --db "$DEMO_DB" knowledge-search \
  --scope system:mall \
  --context SNAPSHOT_TOKEN \
  --kind ENTITY \
  --query 'OmsPortalOrderServiceImpl'

PYTHONPATH=demo python3 -m swm_demo --db "$DEMO_DB" knowledge-neighborhood \
  --scope system:mall \
  --context SNAPSHOT_TOKEN \
  --entity ENTITY_ID \
  --direction BOTH

PYTHONPATH=demo python3 -m swm_demo --db "$DEMO_DB" knowledge-explain \
  --scope system:mall \
  --context SNAPSHOT_TOKEN \
  --kind FACT \
  --id FACT_ID
```

Structure 输出中的每条关系都包含 `fact_id`。可以继续追溯：

```bash
PYTHONPATH=demo python3 -m swm_demo --db "$DEMO_DB" explain \
  --scope system:mall \
  --fact FACT_ID

PYTHONPATH=demo python3 -m swm_demo --db "$DEMO_DB" explain-inference \
  --scope system:mall \
  --inference INFERENCE_ID
```

## 测试

```bash
PYTHONPATH=demo python3 -m unittest discover -s demo/tests -v
```

JWT Revision 002 的 validation-only 机械 Conformance 可单独运行：

```bash
PYTHONPATH=demo python3 -m unittest demo.tests.test_formal_validation -v
```

OpenAI Responses no-tools Adapter 的离线机械反例可单独运行：

```bash
PYTHONPATH=demo python3 -m unittest demo.tests.test_openai_no_tools_adapter -v
```

这组测试覆盖 CC-NT-01～12 的 Envelope、无会话、无附件、空 Tool、请求摘要、响应隔离、失败分类、模型身份、Outcome Unknown、Secret Hygiene 与 Sink Denial 机制。CC-NT-11 使用录制响应 Fixture，只验证 Adapter 解析路径；没有真实 Provider、exact Model / Project Configuration 和原始 Capture 时，`CC-MODEL-NO-TOOLS-001` 仍为 `NOT_EXECUTED`。

这 13 个 Case 使用真实 `mall` Git Object 验证 BuildTarget、Criterion Obligation、Manifest→Request、一致性覆盖、Entity→Fact→Inference 分阶段发布、逐项 Sufficiency、来源关闭 Answer 和 validation Store 隔离。第 13 项的 Candidate、Review 与 Answer 是确定性 Fixture，只是机制可行性见证；它不是完整 JWT Capability Run，也不能替代真实 no-tools 模型或 Direct Claim Oracle。

测试直接使用固定 Revision 的真实 `mall` 仓库，验证 Artifact Lineage、方法级 Structure、Behavior/Business/History Inference、Evidence 追溯、Snapshot 隔离、扩展 SPI、Agent 通用 Tool Loop、任意 Revision 调查、模型 Candidate 准入与 contract correction、同 Revision enrichment、阶段上下文隔离和答案审核。Candidate-only 见证另在运行时生成随机双文件 Git 工程，验证 Fact / Inference 两阶段发布、正式前提、来源关闭恢复及失败反例；它不测试真实模型质量。JWT Revision 002 保持 13 项机械 Conformance；新增 no-tools Adapter 离线机械测试后，当前测试总数为 121。实际耗时和结果应以当次命令输出为准。

## 真实模型诊断（非产品门禁）

本轮还以真实 Codex CLI Model Provider 对内置 Agent 做了纵向诊断。它没有重新执行冻结的五题留出集，不产生新产品分数。

诊断入口保留在 `demo/real_model_diagnostic.py`，但当前默认返回 `CODEX_AGENT_RUNTIME_NOT_ISOLATED`。Codex CLI 是完整 Agent Runtime；临时空目录、只读参数和事后工具事件拒绝不能机械证明执行前无工具。脚本只有在显式确认该验证风险时才允许启动，这个 opt-in 也不把它升级为 no-tools Provider。新的内部 Source Artifact 不应继续交给该入口，正式重跑须先更换为真正无工具的模型接口或外部强隔离执行环境。这里的 no-tools 是防止验证时绕过世界模型正式路径，不是提前建设企业级安全能力。

| 诊断 | 结果 | 边界 |
|---|---|---|
| Behavior 单例 | 8 次 Model Call、`83.093s`；Final Response 为 `ANSWERED`，Answer Review 为 `PASS` | 只证明一个已有正式知识足够的单例走通，不证明 Behavior 泛化。 |
| H-04，错误 SHA | 诊断参数使用了错误 Commit | 该运行不能支持任何架构或产品结论。 |
| H-04，正确 SHA | 轨迹中提出 17 条 Fact Candidate、5 条 Inference Candidate；至少一条 Fact 的 `object` 引用了未声明 Entity，Candidate 被严格校验拒绝 | 已到达复杂候选形成阶段，但尚未完成准入、发布、重评和回答。 |
| Candidate 修正实现（尚未真实重跑） | 已实现最多 3 次总提议尝试（首提 1 次、contract correction / re-proposal 最多 2 次） | 当前 Codex Agent 不是真正的 no-tools Provider，真实重跑因安全边界暂停，不能宣称问题闭环。 |

诊断暴露的问题已形成以下契约修正：空 `include_globs` 不再隐式选择全仓库文件；Provider 兼容的 Structured Output 形状 Schema 与平台能力校验明确分层，其中严格 owner 校验已覆盖 Candidate、Build Intent 和 Formal Tool 等本轮关键路径，尚未覆盖全部注册 Capability；Candidate 可以携带结构化错误进行最多 3 次总提议尝试（首提 1 次、纠错重提最多 2 次）；Answer Review 的权威命题从绑定 Snapshot 重建，并强制拒绝 `PASS` 与 unsupported Claim 同时出现的结果。

继续真实验证仍需关闭四项阻塞：`KnowledgeBuildTarget` canonical binding、逐 Need 的语义充分性、有界 Source Tool Loop，以及执行前机械禁用工具的真正 no-tools Provider。产品结果保持 `33.75 / 50`，即直接 Git Agent 的 `67.5%`；本诊断不是产品 P0 门禁。

## 验证边界

- 这是架构验证 Harness，不冻结生产接口、技术栈或存储 Schema。
- Candidate-only 测试只证明 Application / Knowledge Engine 的手工两阶段 seam；公开 `execute()` 尚未自动执行两轮更新，第二阶段 premise 仍由 Fixture 选择，不能据此宣称公开 Agent 已达到直接源码调查能力。
- 自动回归中的 Agent 流程主要使用可回放的确定性或脚本化 Model Provider test double，只验证 Gateway、Tool Loop、Knowledge Update、Snapshot 绑定和审核门禁。真实模型诊断目前只有一个 Behavior 单例通过；正确 H-04 在复杂 Candidate 本地引用错误处停止，不能代表真实模型质量已经达标。
- `KnowledgeRequirement` 与逐项 `KnowledgeSufficiencyAssessment` 的最小不可变契约已经接入内置 Agent；真实模型的 Requirement 完整性、工具规划、复杂 Candidate 和充分性判断仍未通过新的未见产品门禁。
- H-04 纠偏回放中的复杂 History Candidate 仍由确定性 Builder 生成；最新真实模型运行虽提出 17 条 Fact Candidate 和 5 条 Inference Candidate，却因未声明 Entity 引用而未准入。这两段证据不能合并成“复杂模型语义已经通过”的结论。
- Behavior 与 Business 的首批 Inference 使用确定性候选生产器和独立规则审核；真实模型生成准确率、误拒绝率和跨项目泛化仍需单独评测。
- 未接入 DB、Log、Trace、部署平台与多系统 Scope；这些属于后续扩展验证。
- Demo 为回放保存完整 Artifact Payload，测得的存储放大不能直接作为生产保留策略。

验证结论与未关闭风险见[架构验证记录](../docs/validation/architecture/Architecture_Validation_Log.md)。
