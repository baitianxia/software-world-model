# Software World Model 架构能力 Formal Mapping 静态审计 002

| 元数据 | 值 |
|---|---|
| Document ID | `SWM-ARCH-CAPABILITY-FORMAL-MAPPING-AUDIT-002` |
| Related Case | `DVR-FORMAL-PATH-CAPABILITY-001` |
| Audit Date | 2026-08-05 |
| Status | `Invalidated — Contract Inputs Changed; 33/33 Conclusion Withdrawn` |
| Full ACV Run Status | `Not Executed` |
| Direct Claim Source | `PV-HOLDOUT-001 / H-01…H-05 + E-001…E-003` |
| Target Schema | `swm.local-git.software-knowledge / iter-001.initial.2` |
| Evidence Nature | Non-normative validation evidence |

> 本文保留为一次历史审计记录。审计后Rule Pack、Provider和Schema候选继续修改，当前文件摘要和传递依赖已不再等于§1.1冻结输入；后续严格复核还发现Local Rule I/O、Source Observation身份和多项语言/框架语义路径未闭合。因此本文的`33 / 33 SUPPORTED`结论已经撤回，不得用于开工、能力证明或新审计的继承输入。

当前只执行 [JWT Commit 架构能力验证切片 001](Architecture_Capability_Validation_Slice_JWT_001.md)。新的契约摘要形成后，仅对该切片六个Need从零复核；本文其余逐项表格不在原地改写，避免把历史审计伪装成当前结果。

## 1. 审计输入、勘误应用与结论

### 1.1 冻结输入

| 输入 | exact Reference / Digest |
|---|---|
| [PV-HOLDOUT-001](../product-value/Product_Value_Holdout_Baseline.md) | 文件 SHA-256 `d5ebc4921fcddbfdf942f7bf2a63fb4a396237a242af858530285c56a33a0587` |
| [PV-HOLDOUT-001 Errata](../product-value/Product_Value_Holdout_Baseline_Errata.md) | 文件 SHA-256 `4e68e70cf9b96fc832416612c0e5cc645fadb1e32d828cc189df16b4bc506984` |
| [Local Git Provider Profile Revision 002](../../implementation/iteration-001/contracts/ITER-001-Local-Git-Provider-Profile-Revision-002.md) | `ITER-001-LOCAL-GIT-PROVIDER / 0.2.0 / sha256:59732d3aa4dc66813864b49012227a4785c758188791ededaf126e16cee69b0d` |
| [Foundational Software Semantics Rule Pack](../../implementation/iteration-001/contracts/ITER-001-Foundational-Software-Semantics-Rule-Pack.md) | `ITER-001-FOUNDATIONAL-SOFTWARE-SEMANTICS / 0.1.0 / sha256:5b44266758bf9a0df92d2df2ace80404e4556c728cd631f17b31ca1d9611fc88` |
| [INITIAL Knowledge Schema Revision 002](../../implementation/iteration-001/contracts/ITER-001-Initial-Knowledge-Schema-Revision-002.md) | `swm.local-git.software-knowledge / iter-001.initial.2 / sha256:ef675f22d0e3eed76004c6a10a821377a99f87921298386cda25c97f9219af04` |

上表记录的是本次历史审计当时使用的输入，不是当前契约身份。当前Rule Pack Payload与header摘要不一致，Provider和Schema仍绑定旧Pack摘要；因此以下33项表格只能解释当时判断，不能代表当前状态。

### 1.2 勘误应用规则

本次审计不改变 H-01～H-05 的题目、六/七项评分点身份、评分权重或总数，只按冻结勘误修正对应评分点的语义：

| Errata | 归属评分点 | 本审计使用的 exact 语义 |
|---|---|---|
| `E-001` | `H03-03` | `promotionType=1` 输出价格为 SKU 原价；单件减免为 SKU 原价减 SKU 促销价 |
| `E-002` | `H03-06 / H03-07` | 无优惠 helper 在 SKU 存在时设置 `realStock=stock-lockStock`；SKU 缺失时继续输出但不设置 `realStock` |
| `E-003` | `H03-05` | 以 `subtract(...).intValue()` comparator 稳定排序，再取排序后首个满足项；没有正式 amount-domain 证明时不得声称严格数值降序或数值最高档 |

### 1.3 历史静态结果（已撤回）

| 结果 | 数量 | 含义 |
|---|---:|---|
| `SUPPORTED` | 33 | exact Entity / Fact / Inference / Context / Modality / Coverage / Rule / Admission 承载闭包存在 |
| `PARTIAL` | 0 | 无 |
| `UNSUPPORTED` | 0 | 无 |
| **总计** | **33** | 静态 Claim Preservation 候选为 `100%` |

该结果没有经受后续exact type与真实源码映射复核，现已撤回。当前状态不是`33 / 33 SUPPORTED`，ACV-G02也没有重新执行资格。

## 2. 独立判定方法

### 2.1 状态

| 状态 | 判定规则 |
|---|---|
| `SUPPORTED` | 评分点的全部实质语义、目标身份、Context、Modality、完整性/边界语义均有 exact 注册路径，并存在失败关闭的 Rule、Argument 与 Admission Obligation |
| `PARTIAL` | 只能保存相关来源观察，或公式、外部 API 语义、枚举闭合、Context、Unknown/反例边界中至少一项只能由答案文本补齐 |
| `UNSUPPORTED` | 核心命题没有注册的正式类型、规则或可信支持路径 |

Evidence Quote、Entity metadata、Coverage metadata、Argument 审核说明、模型记忆与答案文字不计入支持。`SUPPORTED` 判断的是 Contract capacity：真实 Candidate 仍可能因来源不完整、模型/审核分歧、Rule 不适用或 Admission 失败而保持 Gap / Unknown。

### 2.2 `MECHANICAL` 与 `MODEL_REVIEWED`

| 路径 | 本审计如何计入支持 |
|---|---|
| `MECHANICAL` | Build Role/解析、Query AST/Binding、图算法、集合差分和最终 typed counterexample evaluation 只有在 exact 输入与公开步骤可重算时计入；相同 exact 输入须产生相同 canonical output |
| `MODEL_REVIEWED` | Java/JDK/Spring/Query semantic、External API、Behavior、Guarantee 与 Semantic Change 只有在 typed Conclusion、正式前提、公开 Argument、独立生成/审核 Attempt 和失败边界全部注册时计入；模型实际正确率不在静态审计中假定 |

`Execution Class` 只规定生成与 Argument Assurance，不决定知识类别或权威性。无论哪种执行方式，都必须再经过独立 Knowledge Verification 与普通 Admission。

### 2.3 Fact / Inference 边界

- Provider 只固定 source-declared 语法、声明、call token、直接创建/赋值、Query AST 与闭合 region，不解释 API、框架、callee/query effect 或业务行为。
- Direct Fact 只保存上述来源直接呈现内容和机械允许的规范化；`program-state-effect` 只允许 `SOURCE_CREATE | SOURCE_WRITE`，不得把方法调用直接写成外部状态效果。
- API、框架、跨节点 data/state effect、行为、保证、变化、反例与第三方语义必须形成 Inference。用户可见公式、顺序、结果、限制与 Unknown 必须在正式 Proposition / Conclusion 中，不能藏在 Evidence、Coverage 或 Argument 文本里。
- Inference direct premise 只能来自构建开始时固定 Snapshot；中间 Inference 必须经过多轮 `UNCHANGED` 正式发布，不能引用同批 Candidate。

### 2.4 Exact Profile Tag Registry

最终 Rule Pack 为每个 Interpretation Profile 内置恰好一个 `NO_EXTENSION` Tag Registry。Source Node、Type、Expression operator、rounding、overflow、query operator、constraint、framework/external operation和typed limitation使用完整 `Exact Profile Tag Reference`：Profile Reference、Registry ID/version/digest、tag kind、member、零基 ordinal与member digest缺一不可。Verifier必须从Pack Payload重算Profile↔Registry唯一绑定、Registry Record、ordinal及member inclusion；未知、自造、插件或近似tag均失败关闭。

本次逐项检查确认33项所需tag均在封闭Catalog内：Maven descriptor/parent/module/dependency/property，Java declaration/control/call/data/write/exception及基础operator，JDK string/numeric/BigDecimal/date/collection/sort/random，Spring transaction/handler，MyBatis/SQL AST/binding/predicate/constraint，以及external API的copy/transform/parse/validate/nondeterministic-result与typed limitation。该结果只证明tag承载空间存在；没有可Conform的Provider/Rule实现时仍不能产出知识。

Build声明在Provider Observation、`BUILD-DECLARATION-ROLE@1`和`swm.fact.build-declaration@1`三处使用同一九成员闭集：`AGGREGATES_MODULE | IDENTIFIES_COMPONENT | MANAGES_DEPENDENCY | DECLARES_DEPENDENCY | DECLARES_PARENT | DECLARES_PROPERTY | DECLARES_PROFILE | DECLARES_ACTIVATION | DECLARES_CONFIGURATION`。role→target kind固定为`MODULE`、`COMPONENT`、`PROPERTY`、`PROFILE`、`ACTIVATION`或`CONFIGURATION`的唯一映射；dependency/parent target只能先锚定`dependency-component`，不能直接伪装成`software-module`绕过`BUILD-COMPONENT-MODULE-BINDING@1`。Provider只观察source-declared typed form，不做插值、profile激活、继承或effective resolution。H-01只消费聚合、component identity、management和dependency子集，effective dependency与Framework closure则消费完整九类闭包。

### 2.5 Effective Dependency、Framework Closure 与 Unknown

通用 `external-api-semantic` 路径不是“模型知道库就算支持”。普通组件唯一肯定basis是已发布且由 `BUILD-EFFECTIVE-DEPENDENCY-RESOLUTION@1` 唯一生产的 `derived-relation(RESOLVES_EFFECTIVE_DEPENDENCY)`。`BUILD-EFFECTIVE-VALUE@1`只规范化一个已闭合声明表达式的scalar value，不能收集dependency candidate、执行冲突mediation或生产effective dependency；source dependency/property/parent声明及其任意拼接也不能替代正式resolution。

有效依赖生产者要求exact target module、从owner descriptor到repository root的完整child→root ordered descriptor chain、每层九类build声明及对应COMPLETE closed-set Coverage、direct/managed candidate全集、profile/activation/config输入、冲突与mediation全集。输出必须唯一给出exact component/version；chain断裂、selector未闭合、环境激活未知、candidate或decision同步遗漏、范围版本或多解一律保持Unknown。Schema只允许该Rule的完整typed output、COMPLETE analysis/enumeration Coverage、独立 `MODEL_REVIEWED` 审核以及 `EFFECTIVE_DEPENDENCY_RESOLUTION_CLOSED@1` 共同支持正式relation。

Catalog支持的Spring Framework fallback与普通effective dependency路径不同。它只接受source-call owner module的完整child→root→exact supported parent descriptor chain；链尾必须逐字命中 `org.springframework.boot:spring-boot-starter-parent@3.2.2 | 3.5.14`，且链上每个descriptor的override/property/dependency/profile/activation/config selector均COMPLETE、所有成员均已解释。单个parent Fact、单个descriptor closure或“工程使用Spring”的判断均不充分；fallback还必须披露 `COMPONENT_VERSION_NOT_INDEPENDENTLY_RESOLVED`，不能断言未独立解析的传递组件版本。

本审计同时核对了PV输入的静态可达性，而不是只核对抽象类型：固定Revision `0504e86…` 的`mall-portal → root` source chain、root Boot parent `3.5.14`、root Hutool direct/managed declaration与`${hutool.version}=5.8.40`均存在；H-04的BEFORE/AFTER `mall-security → root` source chain、Boot parent `3.2.2`、root Hutool direct/managed declaration与`${hutool.version}=5.8.16`均存在。因此完整source输入可以经Provider九类声明进入新resolution producer，BeanUtils也具有3.5.14 Framework fallback的完整chain候选。这里的“可达”不假定真实Provider、模型Reviewer或Admission已运行通过。

在任一路径中，系统随后必须从正式 source type/import/call token 重建exact descriptor，并对每个typed Conclusion member形成独立MemberAssurance；任何effective resolution、framework closure、binding、配置、动态dispatch或审核缺口均保持 `UNKNOWN | FAILED`。

第三方默认行为、运行配置、代理激活、数据库运行状态和未封闭来源不能被模型补写。`UNKNOWN_WITHIN_BOUNDARY` 只有在边界与“不足以建立结论”本身有完整 Argument 时才能准入；它不等价于否定 Fact。

### 2.6 RequestedBasis、Projection、StructuredArgument 与 12 项 Admission

- 每项来源观察绑定 exact Repository / Git Commit；语义变化分别使用 `BEFORE | AFTER`，不把两个 Revision 合成共同成立的 Context。
- Interpretation Context 完整保存 Rule Pack/Profile ID、version、Pack/Profile Definition Digest、Applicability Input Digest 和正式版本/config basis。
- `closed-observation`、`analysis-domain`和`enumeration-proof`分别有唯一closed tuple；Artifact/Evidence/Observation/Formal Reference必须完整可解析，成员、count、ordering、cursor/truncation与digest可重算。动态CURRENT、Candidate Reference、Payload/Quote、任意map/text、自引用和未知variant非法。
- 每个 `enumeration-proof.requested` 必须来自冻结 `RequestedBasis`，而不是Candidate、答案或黄金结果。闭合来源只有：`COVERAGE(CLOSED_OBSERVATION|ANALYSIS_DOMAIN)`、`BUILD_TARGET(ExactFrozenBuildTargetRef)`、`REQUIREMENT_CRITERION(ExactRequirementCriterionRef)`。六条Requested Projection分别只读取closed member、analysis nodes、analysis edges、analysis paths、frozen target required terms或requirement criterion required terms；analysis rule还必须与`enumerationKind/domainKind`匹配且只读一个字段。Candidate同步删除requested/produced成员、换Projection或混入其他analysis字段均不能通过。
- 每个produced term必须与一个`ProducedMemberBinding`一一对应。Verifier通过closed field path从已发布Fact/Inference或当前受审Inference Conclusion提取raw member，再用唯一`swm.projection.produced-member-wrap@1`无强制转换地包装成`ENTITY|EDGE|OUTCOME|GUARANTEE|VALUATION|ASPECT|DELTA|…` CoverageTerm并重算digest；整条Conclusion digest、raw digest或错误外层tag都不能冒充produced term。
- 当前Candidate使用不含Coverage、Argument、Binding、Self Token或Decision的`CandidatePrebindingCore`构造`SelfCandidateToken`，因此没有摘要构造环。Token只能用于当前enumeration binding，不能进入Premise、`InitialAvailableTerm`、Rule input或其他Coverage。Publication在提交前必须从would-be formal State沿同一路径重验kind/type/raw/projected digest并封存Self→Formal映射，任一变化中止事务。
- 枚举、absence与“全部”只来自 `closed-set-observation` 和 COMPLETE Coverage；Fact member allowlist递归禁止Fact/Inference Reference，不能用待证结论自造闭合域。分析Coverage可以引用正式前提，但必须固定Snapshot与递归Fact leaf闭包。
- `CanonicalTermDictionary`只提供内容寻址，不赋予输入authority。Argument从`InitialAvailableTerm`的正式Premise/Context/RequestedBasis建立`S0`，普通Step只能消费`S(n-1)`并通过exact Rule/Application Result产生有名输出；Request term只能控制目标、边界与枚举，不能充当软件语义前提。匿名MAP、Dictionary注入、Candidate binding入S、前向/悬空引用和未消费输出均失败关闭。
- Counterexample/path/cycle输入先进入独立Witness Pool，只有被`EVALUATE/CHECK_COUNTEREXAMPLE`机械消费后，其验证结果才可支持Conclusion。`StructuredArgument.ENUMERATE`必须逐字重复enumeration kind、RequestedBasis、Requested Projection及requested/produced/binding digest；`MODEL_REVIEWED`生成与审核Attempt/Strategy必须独立，MemberAssurance只是Review Proposal，不能写权威Decision。
- Analysis-domain limitation矩阵参与COMPLETE判定。尤其H03-05的 `COMPARATOR_ORDER_NOT_EQUIVALENT` 只在冻结requested明确要求“exact comparator行为”而非“数值全序/最高数值档”时兼容COMPLETE；若requested要求较强结论则必须PARTIAL。
- 本轮Mapping依赖全部12项新增义务：`CLOSED_OBSERVATION_COMPLETE@1`、`PROGRAM_SEMANTICS_PATH_CLOSED@1`、`INTERPRETATION_RULE_APPLICABLE@1`、`ENUMERATION_BIDIRECTIONAL@1`、`COUNTEREXAMPLE_REPLAYABLE@1`、`SEMANTIC_CHANGE_ASPECT_CLOSED@1`、`CONCLUSION_TERM_CLOSED@1`、`COVERAGE_TERM_CLOSED@1`、`ARGUMENT_TERM_CLOSED@1`、`EFFECTIVE_DEPENDENCY_RESOLUTION_CLOSED@1`、`MODEL_REVIEW_ARGUMENT_INDEPENDENT@1`、`EXTERNAL_API_SEMANTIC_REVIEWED@1`。任一适用义务不是PASS时，普通肯定结论不得准入。

本轮关键枚举成员的exact闭包如下：

| 语义面 | Requested authority | Produced member与绑定 |
|---|---|---|
| source member / changeset | COMPLETE closed-observation + member Projection，或冻结Criterion | published closed-set Fact字段 → exact wrapper |
| graph node / direct edge / path | COMPLETE analysis-domain + nodes/edges/paths单字段Projection | graph-analysis closed node/edge/result成员 → `ENTITY|EDGE|PATH` |
| terminal outcome | FrozenBuildTarget / RequirementCriterion | behavior `terminalOutcomes[i]` → `OUTCOME` |
| change aspect | FrozenBuildTarget / RequirementCriterion | semantic-change `semanticDelta.aspect|delta` → `ASPECT|DELTA` |
| guarantee dimension | FrozenBuildTarget / RequirementCriterion | guarantee-assessment `guaranteeClaim` → `GUARANTEE` |
| counterexample | FrozenBuildTarget / RequirementCriterion | counterexample `inputValuation|semanticBoundary` → `VALUATION|BOUNDARY`，另由replay obligation验证 |

这里假定exact BuildTarget / Requirement Criterion已由上游冻结，只判断其内容能否被正式保留并机械消费；本文不把“新问题上自动形成完整Need/criterion”的能力一并视为已证明。

## 3. H-01：Maven 内部模块依赖图

| ID | 实质评分点 | exact Formal Support Closure | 执行边界 | 状态 |
|---|---|---|---|---|
| H01-01 | 列全根 POM 聚合的 7 个模块 | `software-module` + `build-declaration(AGGREGATES_MODULE)`；完整 descriptor region 的 `closed-set-observation` 保存同 Support Closure 锚定的 module Entity 集合；closed-observation RequestedBasis按exact member projection生成requested并双向枚举 | Build / set closure `MECHANICAL` | `SUPPORTED` |
| H01-02 | 区分聚合、dependencyManagement 和实际 dependency | 九成员build Role闭集中的 `AGGREGATES_MODULE \| MANAGES_DEPENDENCY \| DECLARES_DEPENDENCY` 为互不等价的exact子集；`IDENTIFIES_COMPONENT`固定identity，其余parent/property/profile/activation/config role不得被归并；descriptor closure固定完整role partition | Role解析 `MECHANICAL`；Provider只观察source声明，不做effective interpretation | `SUPPORTED` |
| H01-03 | 列全 8 条内部直接依赖边 | `DECLARES_DEPENDENCY` Fact + component/module identity；`BUILD-COMPONENT-MODULE-BINDING@1 → derived-relation(DECLARES_DIRECT_DEPENDENCY)`；全部 descriptor closure构成analysis-domain RequestedBasis，按exact domain projection对edge双向枚举 | component identity多义、profile/condition未知或source domain不完整时失败关闭 | `SUPPORTED` |
| H01-04 | 给出正确拓扑分层 | 闭合 module/edge domain + `graph-analysis(TOPOLOGICAL_LAYERS)`；`graph-result`正式保存层和 enumeration-proof | 图算法 `MECHANICAL` | `SUPPORTED` |
| H01-05 | 给出全部传递可达关系 | 同一闭合图 + `graph-analysis(TRANSITIVE_REACHABILITY)`；每个pair有ordered witness path，requested/produced双向相等 | 图算法 `MECHANICAL` | `SUPPORTED` |
| H01-06 | 确认图中无环并绑定完整 POM 证据 | 同一闭合节点/边集 + `graph-analysis(ACYCLICITY)`；正式 `ACYCLIC(certificate) \| CYCLIC(witness)`、POM Evidence与analysis Coverage共同准入 | 开放或partial图不得产生无环结论 | `SUPPORTED` |

H-01 汇总：`SUPPORTED=6 / PARTIAL=0 / UNSUPPORTED=0`。

## 4. H-02：会员领取优惠券的控制流与一致性边界

| ID | 实质评分点 | exact Formal Support Closure | 执行边界 | 状态 |
|---|---|---|---|---|
| H02-01 | 入口与当前会员 | `interface-mapping`、source-declared `program-call / data-flow` Fact；已发布 callee behavior可进入 `declared-program-behavior`，保持 exact Git / Java Profile Context | Java/Behavior 为 `MODEL_REVIEWED`；动态callee保持Unknown | `SUPPORTED` |
| H02-02 | 四个拒绝条件及顺序 | control/exception Fact保存source nodes、guard与lexical order；expression/behavior Inference保存typed guard、behavior graph与terminal outcome；冻结Requirement Criterion列出四个拒绝断言，projection与全路径枚举防止Candidate少报分支 | Fact不直接宣称运行结果；Behavior独立审核 | `SUPPORTED` |
| H02-03 | 成功时写入 Coupon History 字段 | source assignment/create由data/state Fact保存；Mapper invocation只形成call Fact，mapper/query Fact固定binding/AST，后续 Query semantic + behavior Inference形成 INSERT/UPDATE semantic-operation与字段/value binding | invocation不得伪装Direct Fact effect；Query meaning `MODEL_REVIEWED` | `SUPPORTED` |
| H02-04 | 16 位领取码的完整计算规则 | data/call Fact固定source expression；Java/JDK expression Inference解释 `System.currentTimeMillis`、`String.substring/format`、`Random.nextInt(10)`和concat，正式表达毫秒后8位、4位随机域、会员ID补齐/截取及最终长度 | JDK规则 `MODEL_REVIEWED`；exact signature、numeric/string policy或bound缺失时Unknown | `SUPPORTED` |
| H02-05 | stock、receiveCount 的精确更新规则 | control/data/source-write Fact固定guard、lvalue/rvalue；expression/behavior Inference表达 `stock-1`、`null→1`、`else +1`及两个分支 | Java semantic `MODEL_REVIEWED` | `SUPPORTED` |
| H02-06 | 所有响应结果 | return/throw/call/control/exception Fact + behavior Conclusion；Spring handler只在exact Boot parent/Profile basis及annotation/type/config前提适用时形成typed outcome；Requirement Criterion projection固定正常/拒绝结果的requested集合并与produced双向闭合 | advice激活/顺序/response转换不能证明时显式条件或Unknown；Argument/Coverage closed obligations适用 | `SUPPORTED` |
| H02-07 | 区分事务原子性与并发隔离 / 竞争保证 | annotation、program、query/schema及closed-set Fact；exact Boot parent/context basis + Spring Rule与 `guarantee-assessment` 分别表达条件化事务/回滚、原子性、隔离、race与uniqueness的 established / not-established / unknown边界；冻结Criterion投影四个guarantee dimension | `MODEL_REVIEWED`；事务存在不得推出并发安全，运行配置未见不得补写 | `SUPPORTED` |

H-02 汇总：`SUPPORTED=7 / PARTIAL=0 / UNSUPPORTED=0`。

## 5. H-03：购物车促销计算规则（应用 E-001～E-003）

| ID | 实质评分点 | exact Formal Support Closure | 执行边界 | 状态 |
|---|---|---|---|---|
| H03-01 | 入口、当前会员购物车和 `cartIds` 条件筛选 | interface/control/call/data Fact；`BUILD-EFFECTIVE-DEPENDENCY-RESOLUTION@1`以`mall-portal`完整descriptor chain、Hutool direct/managed candidate与mediation closure生产exact 5.8.40 relation，CollUtil source call再进入 `external-api-semantic`；collection expression/behavior表达非空guard、filter membership和前后数据流 | scalar effective value或raw property/dependency声明不足；resolution、binding或逐member review缺失则Unknown | `SUPPORTED` |
| H03-02 | TreeMap 分组与 DAO 促销资料装配 | call/data/mapper/query Fact；JDK collection/ordered-map与query semantics表达productId分组、批量参数/结果binding、TreeMap key order和装配data flow | Query AST/binding `MECHANICAL`；行为语义 `MODEL_REVIEWED` | `SUPPORTED` |
| H03-03 | promotionType=1 完整规则（E-001） | branch/source-write/data/call Fact；BeanUtils优先使用published effective dependency；fallback则绑定source owner `mall-portal`的完整`mall-portal → root → Boot 3.5.14` chain及链上override/property/dependency/profile/activation/config closed closure，并对copyProperties逐member审核；expression/behavior表达“输出价格=SKU原价”及“减免=原价-促销价” | fallback披露component version未独立解析；单parent/单descriptor或任一selector/成员缺口保持Unknown；不得沿用错误的“促销价覆盖” | `SUPPORTED` |
| H03-04 | promotionType=3 完整规则 | aggregate/sort/control/data Fact；expression/behavior表达跨SKU总数量、源码count comparator与首个满足项、`原价×(1-discount)`、字段写入；BeanUtils价格继承仅经published effective dependency或同一完整owner descriptor chain Framework fallback + copy member assurance成立；tier/path的frozen requested与produced双向闭合 | comparator保留exact typed expression；copy basis/closure不全或更强排序缺适用域时Unknown/limitation | `SUPPORTED` |
| H03-05 | promotionType=4 完整规则（E-003） | BigDecimal/JDK expression + behavior表达SPU总额、`subtract(...).intValue()` comparator、`SORTED_BY_COMPARATOR(expression,STABLE)`、排序后首个满足项、`原价/总额×reducePrice`与`HALF_EVEN`；Requirement Criterion只投影exact comparator行为，BeanUtils输出字段经有效external basis逐member保证 | 无amount-domain证明时必须携带 `COMPARATOR_ORDER_NOT_EQUIVALENT`；它对该较弱requested可兼容COMPLETE，但对“严格数值降序/数值最高档”requested必须PARTIAL；typed counterexample可重放截断边界 | `SUPPORTED` |
| H03-06 | 默认分支与公共字段（E-002） | control/data/source-write Fact + expression/behavior表达 `reduceAmount=0`、积分/成长值及SKU存在时 `realStock=stock-lockStock`；BeanUtils复制只在effective dependency或完整Framework fallback与逐member审核通过后进入Inference | 不得把callee/copy效果写成Direct Fact；closure不足与SKU缺失分支分别保留 | `SUPPORTED` |
| H03-07 | 输出顺序与 Product / SKU 缺失行为（E-002） | ordered-map/collection semantics表达SPU升序与组内encounter order；nullability/dereference Inference表达Product/SKU需要分支的NPE；默认helper行为表达SKU缺失仍输出且不设置realStock；terminal path Coverage防漏 | 缺资料结果是源码条件化行为，不外推为真实运行事件 | `SUPPORTED` |

H-03 汇总：`SUPPORTED=7 / PARTIAL=0 / UNSUPPORTED=0`。

H03-05 的 `SUPPORTED` 指能够保存并回答勘误后的较弱、准确语义。只有另有正式 amount-domain 前提并证明 comparator 符号与严格数值顺序等价时，系统才可以发布“数值最高档”推断；否则发布该更强结论应被 Verification / Admission 拒绝。

## 6. H-04：JWT 迁移提交的语义影响

| ID | 实质评分点 | exact Formal Support Closure | 执行边界 | 状态 |
|---|---|---|---|---|
| H04-01 | 父提交与恰好三个修改文件 | `revision-parent / revision-change` + Provider `REVISION_CHANGE_SET`；closed-set Fact正式保存 exact member set/cardinality，closed-observation projection从冻结changeset重建requested；BEFORE/AFTER Context与双向enumeration防止只列相关文件 | changeset必须单Artifact COMPLETE | `SUPPORTED` |
| H04-02 | JJWT 版本、management 和直接依赖移除 | BEFORE/AFTER build Fact的不同Role及descriptor closure；`semantic-change(DEPENDENCY)`保存removed delta；冻结Requirement Criterion/BuildTarget投影DEPENDENCY requested aspect，不能由Candidate自行缩成任一同类History Fact | Build解析 `MECHANICAL`；Semantic Change `MODEL_REVIEWED` | `SUPPORTED` |
| H04-03 | JWT 生成、Secret bytes 和 exp 变化 | `BUILD-EFFECTIVE-DEPENDENCY-RESOLUTION@1`以BEFORE/AFTER各自`mall-security → root`完整chain和candidate/mediation closure分别固定BEFORE JJWT 0.9.1及适用Revision的Hutool 5.8.16；source call/data Fact + generic external-api/JDK Inference表达Jwts/HS512与JWTUtil、key bytes、payload/exp数据流；Criterion投影独立API_CALL / DATA_FLOW / VALUE delta | `BUILD-EFFECTIVE-VALUE@1`、raw property或dependency声明不能单独作basis；每个component/call/member独立审核 | `SUPPORTED` |
| H04-04 | 解析/验签、过期、校验与异常变化 | 同一新producer发布的BEFORE JJWT与Hutool effective relations + BEFORE/AFTER call/control/data/exception Fact；JJWT及JWTUtil/StrUtil external-api Inference与behavior表达旧parse、verify→parse、Map读取、null guard和typed outcomes；Criterion projection固定API_CALL / CONTROL_FLOW / EXCEPTION_FLOW等requested aspect并逐项闭合 | effective version/signature/binding/MemberAssurance或Argument/Coverage closed obligation失败时保持Unknown | `SUPPORTED` |
| H04-05 | Long / Date 刷新和 30 分钟规则 | control/data/call Fact；同一published Hutool resolution支撑DateUtil external-api，JDK/expression/change Inference表达类型分支、offsetSecond/time arithmetic、原Token return与重新签发及typed delta；frozen aspect projection防漏 | DateUtil必须有effective dependency、exact call descriptor及逐member PASS | `SUPPORTED` |
| H04-06 | 默认算法等证据边界 | 新调用与旧注释分别形成CODE Fact / `source-statement`且Modality不混同；即使component/version已effective-resolved，缺JWTUtil默认算法所需正式配置/语义前提时也只能返回有界Unknown/limitation | Profile、模型记忆、常见默认值或版本basis本身都不能补配置依赖成员；Unknown不是否定Fact | `SUPPORTED` |

H-04 汇总：`SUPPORTED=6 / PARTIAL=0 / UNSUPPORTED=0`。

H04-06 的 `SUPPORTED` 不是“知道默认算法”，而是系统有能力保留可证明观察并正式暴露知识边界。若实际运行输出未经正式前提和独立审核的具体默认算法，则该评分点与本 Mapping 均失败。

## 7. H-05：`listCart` 优惠券可用性与边界反例

| ID | 实质评分点 | exact Formal Support Closure | 执行边界 | 状态 |
|---|---|---|---|---|
| H05-01 | 当前会员且 `use_status=0` 的数据范围 | query/mapper/call/data Fact把Mapper方法绑定到typed query AST；query predicate/behavior Inference表达会员参数和`use_status=0` filter，保持Git/MyBatis/SQL Context | Query AST/binding `MECHANICAL`；predicate semantics `MODEL_REVIEWED` | `SUPPORTED` |
| H05-02 | 金额公式与三种 useType 范围 | source expression/control/data/query Fact；Java/JDK/query Inference表达 `(price-reduceAmount)×quantity`、useType 0/1/2的filter/aggregate范围及分支枚举 | 公式语义必须位于typed Inference，不由Fact文本补写 | `SUPPORTED` |
| H05-03 | 三个分支的精确谓词 | source calls/guards Fact；numeric conversion、BigDecimal与Date expression Inference表达total来源、`intValue`、strict `before`与阈值；behavior保存三个branch条件 | JDK semantic `MODEL_REVIEWED`；numeric policy显式保存 | `SUPPORTED` |
| H05-04 | 至少两个有效边界反例 | 已发布expression/behavior作为前提；`counterexample`保存typed valuation、连续evaluation steps、precision/scale、actual result和violated boundary；冻结Requirement Criterion投影至少两个边界反例requested，counterexample enumeration双向闭合 | 最终求值 `MECHANICAL`；任何上游MODEL_REVIEWED规则仍保留独立审核记录 | `SUPPORTED` |
| H05-05 | endTime 严格边界及未检查 startTime | Date semantic正式表达严格 `<` 和相等时false；完整method region的closed selector/member set支持“该方法边界内无startTime读取” | absence不外推到类、模块、仓库或运行时 | `SUPPORTED` |
| H05-06 | 未识别 useType、请求 type 和 null 分区 | control/data Fact与behavior graph闭合识别/未识别useType、`type==1`/其他非空值；nullability + null-dereference Inference表达null NPE条件；terminal outcome枚举 | Java/Behavior `MODEL_REVIEWED` | `SUPPORTED` |
| H05-07 | 注释与代码证据边界 | `source-statement(CODE_COMMENT_DECLARES)`只证明注释声明；query/program Fact与behavior表达实现语义，两种Modality不可替代；Reader不得从注释、Evidence或Argument补行为结论 | 注释与代码冲突不自动选择赢家 | `SUPPORTED` |

H-05 汇总：`SUPPORTED=7 / PARTIAL=0 / UNSUPPORTED=0`。

## 8. 总体汇总与静态判定

| 题目 | SUPPORTED | PARTIAL | UNSUPPORTED | 合计 |
|---|---:|---:|---:|---:|
| H-01 | 6 | 0 | 0 | 6 |
| H-02 | 7 | 0 | 0 | 7 |
| H-03 | 7 | 0 | 0 | 7 |
| H-04 | 6 | 0 | 0 | 6 |
| H-05 | 7 | 0 | 0 | 7 |
| **总计** | **33** | **0** | **0** | **33** |

静态 Claim Preservation 候选为：

`33 / 33 = 100%`

本轮没有发现新的 `ARCH`、`DD` 或剩余 `IS` 静态承载缺口。新增 Contract 保持通用：业务对象、特定 Commit、题目和黄金答案没有成为 Type、Rule、Selector 或隐藏分支；Build、Java、JDK、Spring、MyBatis、SQL 与 External API 只作为版本化 Profile / 通用 Rule / typed Inference边界出现。

## 9. 本审计没有证明的内容与下一门禁

本审计明确没有证明：

1. Provider 0.2、Rule Pack 0.1 和 Schema `iter-001.initial.2` 已实现或通过 Conformance。
2. 真实模型能够为任一 `MODEL_REVIEWED` Rule 生成正确 Proposal，独立 Reviewer 能稳定发现错误，或两者满足 Capability Evaluation。
3. H-01～H-05 已经通过公共 Source Tool / Observation Port、Candidate Proposal Port、Knowledge Verification、Admission、Publication与Reader实际构建和恢复。
4. no-tools Provider、canonical BuildTarget、逐 Need Sufficiency、有界 Source Tool Loop、Context、防篡改、复用与独立 Answer Review 已端到端通过。
5. 新未见工程上的正确率、泛化、时延、成本或产品价值已经达到直接调查 Agent 下限。

下一步必须先治理三份 Proposed Contract并完成Provider / Rule Pack / Schema Conformance，再按 [Architecture Capability Validation Baseline](Architecture_Capability_Validation_Baseline.md) 通过公共端口运行完整 ACV-G00～G10。只有完整 Run 的真实轨迹和独立审核才能形成“方案具备该能力”的结论；真实模型能力仍由 Capability Evaluation，新未见产品表现仍由 Product Holdout 判定。
