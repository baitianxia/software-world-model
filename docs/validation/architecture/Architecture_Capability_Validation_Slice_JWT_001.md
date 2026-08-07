# Software World Model 架构能力验证切片：JWT Commit 影响分析 001

| 元数据 | 值 |
|---|---|
| Document ID | `SWM-ACV-SLICE-JWT-001` |
| Status | `Ready for Demo Harness Implementation` |
| Validation Type | Architecture Feasibility / Formal Knowledge Single Path |
| Target Repository | `https://github.com/macrozheng/mall.git` |
| Target Commit | `dacce5f28dfc1734f2db09668d928d7fac2a3a7a` |
| Exact Parent | `00bd03591cfd91f82ebe48787315eed613754277` |
| Target Tree | `1a39a7d550ce802f46b68ca56a59362b09b5bdbe` |
| Runtime State | `NOT_RUN` |
| Formal Contract | [SWM-ITER-001-JWT-VALIDATION-FORMAL-CONTRACT@0.1.0](../../implementation/iteration-001/contracts/ITER-001-JWT-Validation-Formal-Contract.md) |

> 本切片只回答一个问题：现行架构能否使用真实模型，通过受控来源调查构建并发布足以回答 JWT 迁移影响的正式知识，并在关闭来源上下文后达到直接读取同一代码的 Agent 所能证明的正确性与完整性。本切片不验证全部详细设计、33 项能力、跨项目泛化或生产就绪。

## 1. 范围原则

本切片按一条纵向能力链划分范围，不按现有模块数量扩大验证面。只有直接参与下列链路的类型和契约属于开工前闭合范围：

`Requirement → canonical BuildTarget → bounded Source Tool Loop → Artifact → Evidence → Entity / Fact / Inference Candidate → Verification / Admission → Snapshot → per-Need Sufficiency → Answer Candidate → independent Answer Review → Delivery`

以下内容明确排除：

- H-01、H-02、H-03、H-05 及其专用语义表达。
- DB、Log、Trace、部署、跨 Scope、Schema Evolution、性能和企业安全能力。
- 为 Java、JDK、Spring、MyBatis 或 SQL 建立完整解释器、标准库语义库或项目专用 Builder。
- 生产实现、生产数据迁移和完整 Iteration 001 解禁。

若运行暴露当前通用类型无法承载某项必需语义，只修订该通用契约；不得借机补齐未被本切片触达的框架或语言语义。

## 2. 冻结问题与 Need

冻结问题为：

> 比较提交 `dacce5f28dfc1734f2db09668d928d7fac2a3a7a` 与其父提交，说明它在依赖、令牌生成、解析/验签、过期判断、校验和刷新上的全部语义影响。把源码可证明的结论与依赖库默认行为造成的未知项分开。

Requirement Revision 必须在任何调查前一次性冻结为以下六个 Need；运行中不得删除、合并、弱化或原地改写：

| Need ID | 必须回答的实质问题 | 最低正式覆盖 |
|---|---|---|
| `JWT-N01` | 比较对象和完整变更范围是什么 | exact Commit、exact Parent、完整 changed-file set及其闭合性 |
| `JWT-N02` | JWT 依赖声明发生了什么变化 | before/after POM 声明、移除关系及适用模块 |
| `JWT-N03` | 令牌生成与 `exp` 表达发生了什么变化 | before/after调用、Secret字节转换、payload与过期值构造 |
| `JWT-N04` | 解析、验签、过期判断、校验和异常行为如何变化 | before/after控制、数据和异常结果，包含空值与失败分支 |
| `JWT-N05` | 刷新行为如何变化 | `created`类型分支、30分钟边界、返回原Token或重新签发 |
| `JWT-N06` | 哪些结论不能仅由当前来源证明 | 新默认签名算法等明确的Unknown Boundary及其缺失前提 |

`SATISFIED` 必须逐 Need 绑定同一 exact Snapshot 中可解析的 Fact / Inference。相关、同类型或同主题知识不能替代语义蕴含；任一 Need 为 `GAP | UNKNOWN | CONFLICT | INSUFFICIENT` 时，整体不得判为完全满足，答案必须原样保留该状态。

## 3. 被测路径与角色边界

### 3.1 唯一被测路径

Software World Model 只允许一条回答路径。调查阶段的模型可以提出 Source Tool Proposal 和知识 Candidate；平台负责授权、执行、Artifact / Evidence 固化、身份补全、结构校验、Verification、Admission 和 Publication。发布后必须销毁或关闭调查消息、Tool 结果、Artifact Payload访问和模型会话。

答案阶段重新建立无来源权限的 Knowledge Use Session，只允许读取被冻结 Snapshot 中的正式 Entity、Fact、Inference、Context、Coverage和限制。答案缺失时只能返回 Gap，不得重新读取来源或调用直接调查 Agent。

### 3.2 模型角色

- `Investigation Model`：根据已冻结目标和上一步观察提出下一步Source Tool Proposal，并从授权Artifact形成知识Candidate。
- `Knowledge Reviewer`：使用独立模型调用审核Candidate的证据支持、目标绑定、Context、Modality和越界推断。
- `Answer Model`：只读取正式Snapshot和Requirement，形成逐Need Answer Candidate。
- `Answer Reviewer`：使用独立模型调用审核Answer Claim与正式Support Proof是否一致。

四类调用都必须经过真实 `NO_EXTERNAL_ACCESS` Adapter；不得使用拥有shell、文件、Web、MCP、Connector、Agent Tool、历史会话、附件或隐藏工作区能力的运行时。确定性Fixture只可验证门禁代码，不能作为本切片能力通过证据。

### 3.3 Direct Agent 对照

直接读取代码的 Agent 只在被测运行之外建立同题能力下限。它可以读取同一冻结Repository和Revision，但其回答不得进入Artifact、Evidence、Candidate、Snapshot、Sufficiency或答案输入。对照采用独立语义评分，不采用正文复制或字符串匹配。

这不是运行时双路径：被测系统从始至终只走Formal Knowledge Single Path。

## 4. Source Tool Loop 边界

首轮只允许通用 Local Git 工具：

- `resolve exact revision / parent`
- `compare revisions`
- `list changed files or directory members`
- `search exact revision`
- `read file or bounded range at exact revision`

模型只提出下一步 Tool Proposal，平台执行并记录。预算在运行前冻结，至少包含最大步骤、文件数、读取字符数、模型调用数和成本；达到任一上限、重复无新信息、权限失败或目标满足时停止。Tool结果只能进入Artifact / Evidence / Candidate链，不能直接进入Answer。

BuildTarget必须机械绑定目标Commit、Parent、Comparison Context、六个Need和最小覆盖目标。短SHA、同名方法、错误Revision或擅自扩大到全仓库都必须失败关闭；模型不能把六个Need降级为一条宽泛的`HISTORY_IMPACT`。

## 5. AI Native 与形式化边界

本切片不通过硬编码完整JDK或第三方库解释器来模拟模型。职责边界固定为：

- 平台形式化控制身份、授权输入、Source Locator、Artifact / Evidence Lineage、Context、typed Candidate envelope、Support、Verification、Admission、Snapshot、Need覆盖和摘要。
- 模型负责开放式源码理解、调查规划、语义Candidate和答案表达。
- Schema只需提供本切片必需的通用命题形状，例如声明变化、调用变化、数据值变化、控制/异常结果、语义变化和有界Unknown；项目名、类名、Commit、黄金答案和具体JDK方法不得成为类型或规则。
- Reviewer必须以冻结Artifact / Evidence或正式Snapshot为输入重新判断，不接受生成模型的隐藏推理、自报confidence或模型常识作为支持。

如果语义只能通过自由文本保存、无法逐成员绑定Evidence与Context，本切片失败；如果只是缺少某个预编码JDK operation但模型能够形成可审核的typed通用结论，不因此要求扩建机械语义库。

## 6. 通过条件

本切片只有同时满足以下条件才能记为`PASS`：

1. `BuildTarget`唯一解析到冻结Commit、Parent、Comparison Context和六个Need。
2. 真实no-tools模型通过有界Source Tool Loop取得所需材料；每一步可回放且未越权。
3. 全部答案所需语义经过Artifact、Evidence、Candidate、独立Knowledge Review、Admission和Snapshot Publication，没有Builder、Fixture或私有写入旁路。
4. 调查上下文关闭后，Answer Model只依赖新Snapshot完成回答，来源操作数为零。
5. 六个Need逐项具有同Snapshot正式Support Proof；未知默认算法保持Unknown，不由模型常识补齐。
6. 独立Answer Reviewer拒绝缺Need、错Commit、相关但不蕴含、Evidence越界、Context错配和Snapshot外补写。
7. 按H-04冻结10分量表独立评分，Software World Model回答不低于同条件Direct Agent，并且没有任何实质错误由总分抵消。
8. 完整运行记录包含model/provider/adapter/prompt revision、Authorized Input Manifest、实际模型标识、Tool轨迹、Artifact/Evidence/Candidate/Decision/Snapshot/Assessment/Answer摘要和Token/时长/成本。

一次`PASS`只证明本冻结问题上的架构可行性，不证明模型可靠性、跨项目泛化或产品优势。一次`FAIL`必须按最早失败位置归因到来源可达性、模型调查、正式表达、Verification、Publication、Sufficiency或Answer Review，不得通过扩大范围掩盖。

## 7. 开工门禁

实现本切片前只要求以下规范闭合：

1. 上述链路实际使用的每个type、closed union、reference、canonicalization和digest preimage可机械构造且无环。
2. Pack、Provider、Schema及no-tools Adapter的exact依赖摘要一致。
3. Authorized Input Manifest与实际Provider Request双向无missing/extra，隔离在dispatch前成立。
4. 本切片所需Candidate与六个Need的Support Projection有正例和失败关闭反例。

不要求H-01、H-02、H-03、H-05达到形式化映射完备。满足本节只能授权Demo Harness实现，不能解除Iteration 001生产编码暂停。

## 8. 当前状态与下一步

问题、Need、角色、单路径和通过条件已经限定。当前切片不再依赖已撤回的Provider Revision 002、Foundational Rule Pack和Schema Revision 002；它复用已冻结Provider 0.1、Base Schema `iter-001.initial.1`和no-tools Adapter，并只通过上表Formal Contract增加本切片必需的validation-only类型。

四项静态开工门禁和六Need Formal Mapping已经通过。下一步只允许实现Formal Contract第12节的Conformance Case；这些Case全部运行通过后，才可执行真实JWT Capability Run。本文状态不授权Iteration 001生产编码。
