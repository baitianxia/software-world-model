# JWT Commit 架构能力验证切片 Formal Mapping 审计 001

| 元数据 | 值 |
|---|---|
| Document ID | `SWM-ACV-SLICE-JWT-FORMAL-AUDIT-001` |
| Related Slice | `SWM-ACV-SLICE-JWT-001` |
| Status | `Completed — 6/6 Static Mapping Supported; Runtime Not Run` |
| Audit Date | 2026-08-05 |
| Evidence Nature | Validation evidence; non-production |

> 本审计只判断H-04六个Need是否具有可实现、可审核且无来源回答旁路的正式承载路径。它不复用历史Audit 002的33项结论，也不判断真实模型会稳定生成正确Candidate。

## 1. exact 输入

| 输入 | exact身份 |
|---|---|
| [JWT验证切片](Architecture_Capability_Validation_Slice_JWT_001.md) | `SWM-ACV-SLICE-JWT-001`；Runtime=`NOT_RUN` |
| [JWT Validation Formal Contract](../../implementation/iteration-001/contracts/ITER-001-JWT-Validation-Formal-Contract.md) | `0.1.0 / sha256:468db1c92419faad5e66597496c2103c92d83331ab28a9a01e90e108072f36b9` |
| Base Knowledge Schema | `iter-001.initial.1 / sha256:1ba1a4090032464b4970bbc13a2a29685bb5b7f5d00fbf35b5da914e266c64fa` |
| Local Git Provider | `0.1.0 / sha256:d1eacb1e2c61c160c239b840cc84d660fef9fe282acd465358ae41f07bf76d1f` |
| no-tools Adapter Profile | `0.1.0 / file-sha256:f222ea0b86db6994db2f09baa2f9ad44cd4dd8b7746b88ef09573410db8add60` |
| Repository | `https://github.com/macrozheng/mall.git` |
| Comparison | `00bd03591cfd91f82ebe48787315eed613754277 → dacce5f28dfc1734f2db09668d928d7fac2a3a7a` |

Provider实查确认target只有该显式parent，完整changeset恰有三个`MODIFIED`成员：根`pom.xml`、`mall-security/pom.xml`和`JwtTokenUtil.java`。这只是验证输入核对，不是运行时预置知识；Demo仍须通过公开Source Tool Loop取得并正式化这些内容。

## 2. 判定方法

`SUPPORTED`要求同时存在：

1. 来源可由当前Provider的通用Tool取得。
2. 直接观察有Fact Proposition和单Artifact Evidence承载。
3. 开放语义有原子、typed、MODEL_REVIEWED Inference承载。
4. Conclusion保留Revision、affected entity、aspect、条件、限制和Unknown Boundary。
5. 逐Need Binding能引用同一Snapshot中的确切Conclusion member。
6. Answer阶段不需要Artifact、Evidence内容或调查上下文。

本审计不要求为JDK或第三方库建立完整机械语义库。源码直接呈现的调用、值绑定、条件、返回和异常先形成原子Fact；跨Fact变化由模型提出typed Inference并经独立模型和Knowledge Verifier审核。依赖库默认行为缺少正式前提时只能形成bounded Unknown。

## 3. 六个 Need 的静态映射

| Need | 正式承载路径 | 完整性与失败边界 | 结果 |
|---|---|---|---|
| `JWT-N01` 比较对象与完整范围 | Base `revision-parent` + validation `closed-revision-change-set`；`CompleteChangeSetEvidence`绑定单个terminal compare Artifact | target / parent / repository逐字等于BuildTarget；member、count和ordering双向重算，漏项或额外项失败 | `SUPPORTED` |
| `JWT-N02` 依赖变化 | BEFORE / AFTER `atomic-source-proposition(DECLARES_DEPENDENCY)`；对`io.jsonwebtoken`和相关version token形成`closed-source-literal-selection`；`atomic-semantic-change(DEPENDENCY,REMOVES)`逐项表达 | 零匹配只在完整单文件literal selection内成立；不能外推到仓库或runtime；根POM management与模块direct dependency是不同Conclusion | `SUPPORTED` |
| `JWT-N03` 生成与`exp` | 原子`DECLARES_INVOCATION / DECLARES_VALUE_BINDING` Fact保存Jwts / JWTUtil调用、Secret UTF-8 bytes、`exp` long构造；`API_CALL / DATA_FLOW / VALUE_SEMANTICS`原子变化分别发布 | 一个Conclusion只有一个entity / aspect / relation；API默认不进入Fact；每个值和调用由连续Evidence直接支持 | `SUPPORTED` |
| `JWT-N04` 解析、验签、过期、校验和异常 | `DECLARES_INVOCATION / CONDITION / RETURN / EXCEPTION_HANDLING` Fact；`VALIDATES_BEFORE / RETURNS_WHEN / TREATS_AS` Semantic Relation表达verify→parse、null、missing / invalid `exp`和异常结果 | 条件、返回和异常各自形成原子结论；相关调用不能冒充行为；错误Revision、Context或缺前提时Review拒绝 | `SUPPORTED` |
| `JWT-N05` 刷新 | `DECLARES_TYPE_BRANCH / CONDITION / RETURN / VALUE_BINDING / ORDERING` Fact；`REFRESH_BEHAVIOR`变化表达Long / Date、30分钟边界、原Token与重新签发 | DURATION、CONDITION和OUTPUT是Relation必需Role；缺任一成员不能由答案补写 | `SUPPORTED` |
| `JWT-N06` 未知边界 | 代码调用与旧注释分别保持`CODE_DECLARES / CODE_COMMENT_DECLARES`；`bounded-unknown(LIBRARY_DEFAULT)`列出建立默认算法所缺的正式premise | Unknown只表示当前授权Boundary未建立，不表示算法不存在；注释、模型常识和库名不能补成具体默认算法 | `SUPPORTED` |

汇总：`SUPPORTED=6 / PARTIAL=0 / UNSUPPORTED=0`。该计数只证明当前切片的Contract capacity，不表示任何Runtime Gate PASS。

## 4. 结构与摘要复核

| 检查 | 结果 |
|---|---|
| Contract Payload SHA-256与header一致 | `PASS` |
| Base Schema、Provider Payload和Adapter文件摘要与依赖一致 | `PASS` |
| UTF-8、NFC、LF、无BOM / CRLF /行尾空格 | `PASS` |
| 新增正式知识没有自由文本Proposition / Conclusion | `PASS`；自然语言只存在Requirement、审计rationale和Answer Claim |
| Evidence一条只绑定一个Artifact | `PASS` |
| Model Authorized Input按Role闭集；Answer无Source输入 | `PASS` |
| 模型响应→domain payload具有唯一Output Contract投影 | `PASS` |
| Fact先发布、Inference后引用exact Snapshot | `PASS` |
| Core→Digest→Envelope与后置Decision拓扑 | `PASS`；未发现反向引用或动态CURRENT |
| validation与production状态隔离 | `PASS` |

## 5. 仍待运行的内容

以下项目不是静态审计结果：

- no-tools Adapter真实Conformance与Model Eligibility。
- 第12节12个Contract Conformance Case的实现和运行。
- 真实模型能否在预算内完成Source Tool Loop、Fact / Inference Proposal及独立Review。
- Knowledge Admission、Snapshot Publication、来源关闭、逐Need Assessment和Answer Review的完整公共路径。
- 与Direct Agent的同题评分结果。

因此当前只具备`Ready for Demo Harness Implementation`资格。完整JWT Capability Run和Iteration 001生产编码仍为`NOT_RUN / PAUSED`。
