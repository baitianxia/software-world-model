# Iteration 001 Foundational Software Semantics Rule Pack

| 元数据 | 值 |
|---|---|
| Artifact ID | `SWM-ITER-001-FOUNDATIONAL-SOFTWARE-SEMANTICS-RULE-PACK` |
| Pack ID | `ITER-001-FOUNDATIONAL-SOFTWARE-SEMANTICS` |
| Version | `0.1.0` |
| Status | `Withdrawn Draft — Not a Current Validation Dependency` |
| Predecessor | `NONE` |
| Pack Digest | `sha256:612faf30f33511942d5251ab99c9f42abae5aecf8cca57647c33b0c7ddb9e8f8` |
| Digest Algorithm | SHA-256 |
| Contract Canonicalization | `SWM-FOUNDATIONAL-SEMANTICS-RULE-PACK-MARKDOWN-LF@1` |
| Implementation Plan | [SWM-IMP-ITER-001](../Implementation_Plan_Iteration_001.md) |
| Governing Design | [Schema Core](../../../detailed-design/topics/DD-KNW-SCHEMA-CORE.md)、[Fact](../../../detailed-design/topics/DD-KNW-FACT.md)、[Inference / Conflict](../../../detailed-design/topics/DD-KNW-INFERENCE-CONFLICT.md) |

> 本 Pack 是 Knowledge Schema 可以按 exact Reference 使用的不可变基础软件语义规则集合。它不创建正式知识、不读取来源、不分配身份，也不授权准入或发布。具体项目、题目、类、方法和答案不得成为 Rule ID 或隐藏分支。

> 撤回说明：本草案尝试一次性形式化多语言、标准库、框架和Query语义，后续复核发现其Local Rule I/O与多项语义路径仍未闭合。当前JWT验证切片改用窄化的validation-only Formal Contract；任何现行基线不得引用本Pack。上表Digest只标识当前保留的草案Payload，不表示Conformance或冻结。

`Pack Digest` 只覆盖下方两个标记之间的内容。规范输入使用 UTF-8、LF、Unicode NFC，无 BOM、CRLF 或行尾空格；输入从 BEGIN 标记后的首字节开始，到 END 标记前一行的 LF 为止。

<!-- BEGIN FOUNDATIONAL SOFTWARE SEMANTICS RULE PACK PAYLOAD -->

## 1. Pack 身份、边界与引用

| 项 | 定义 |
|---|---|
| Pack ID / Version | `ITER-001-FOUNDATIONAL-SOFTWARE-SEMANTICS / 0.1.0` |
| Predecessor | `NONE` |
| Pack Rule Families | `BUILD | JAVA_LANGUAGE | JAVA_LIBRARY | SPRING_TRANSACTION | QUERY_MAPPING | EXTERNAL_API` |
| Output Authority | Pack输出只支持使用方Schema注册的typed Inference Argument / Verification；Direct Fact必须由Schema的Evidence/Support Contract建立，不能由Rule Output替代。任何输出都不是Entity、Fact、Inference、Admission Decision或应用答案 |
| Runtime Boundary | 只解释仓库中被正式 Evidence 固定的声明语义；不声称某部署、数据库或请求实际发生 |

`ExactRuleRef` 是唯一 closed union：

- `PACK_RULE_REF=TUPLE(ENUM(PACK_RULE_REF),PackId,PackVersion,PackDigest,RuleId)`；RuleId 必须逐字存在于该 exact Pack 的 Rule Catalog。
- `CONSUMER_LOCAL_RULE_REF=TUPLE(ENUM(CONSUMER_LOCAL_RULE_REF),ExactConsumerDefinitionRef,RuleId,RuleVersion,RuleDefinitionDigest)`；`ExactConsumerDefinitionRef=TUPLE(ENUM(CONSUMER_DEFINITION_REF),ENUM(KNOWLEDGE_SCHEMA),ID(definitionId),ID(definitionVersion),DIGEST(definitionDigest))`。目标冻结 Consumer Definition 必须直接依赖本 exact Pack，且必须包含可按其声明的 record canonicalization 重算的完整 Local Rule Definition Record。Record 必须闭合声明 Rule ID/version、`FORMAL_KNOWLEDGE_ONLY` Applicability、typed input/output Contract、Execution Class、Unknown Boundary、公开 Step Contract 与 `NO_EXTENSION`；`RuleDefinitionDigest`只覆盖该完整 Record。

`PROJECT_CONSUMER_DEFINITION_REF(ExactConsumerSchemaRef)`是唯一机械投影：从完整Schema Ref读取definition ID、version与digest，并按上述`CONSUMER_DEFINITION_REF/KNOWLEDGE_SCHEMA` tag重编码；不得复制调用方提交的第二份身份。Local Rule Ref中的`ExactConsumerDefinitionRef`必须逐字等于该投影。

Pack不反向导入任一Consumer Schema codec。跨边界对象统一使用：`ExactConsumerTypedObjectCore=TUPLE(ENUM(CONSUMER_TYPED_OBJECT_CORE),ExactConsumerDefinitionRef,ID(consumerCodecId),consumerTypedObject)`；`ExactConsumerTypedObjectDigest=DIGEST(ExactConsumerTypedObjectCore)`；`ExactConsumerTypedObject=TUPLE(ENUM(CONSUMER_TYPED_OBJECT),ExactConsumerTypedObjectCore,ExactConsumerTypedObjectDigest)`。`consumerTypedObject`不是opaque bytes或map，必须由该exact Consumer Definition中的`consumerCodecId`完整解码、拒绝unknown field并重算Core/Digest。本文用它携带Execution Boundary、Scope、Knowledge Context、Rule Execution Sequence、Observation/Formal Knowledge/Requested Basis/Configuration及closed field path，而无需使Pack依赖某个具体Schema。

两种 variant 之外的引用均非法。规则使用方必须保存并解析完整 Reference；不得使用 Pack/Schema 名称、Family、动态当前版本、版本范围、裸 Rule ID 或模型记忆替代。Consumer-local Rule 只扩展对已发布 typed formal knowledge 的分析，不得解析新来源、定义语言/API语义或绕过本 Pack 的 Input、Execution Proof、Rule Verification、Canonical Output协议；其 Consumer Definition Digest同时固定该Definition对本Pack的exact依赖，因此不形成Pack对Consumer的反向依赖。

本 Pack 的六个 Pack Rule Family 只提供可复用的软件语义；Consumer-local Rule只提供在一个exact Consumer Definition内注册的可复用形式知识分析。任何 Rule 都不得包含仓库路径、提交 ID、业务名词、题目编号、预期答案或特定示例常量。

### 1.1 Exact Interpretation Profile Catalog

本 Catalog 是 Pack Payload 的组成部分，不是动态外部 Registry。`Exact Profile Reference = Pack ID + Pack Version + Pack Digest + Profile ID + Profile Version + Profile Definition Digest`；六个字段缺一不可。`Profile Definition Digest` 按 `SWM-INTERPRETATION-PROFILE-RECORD-LF@1` 计算：对表中 `Canonical Definition Record` 反引号内的 ASCII 字节追加一个 LF，执行 SHA-256。Pack Digest 进一步覆盖完整 Catalog、适用语义与 Rule，因此 Profile Definition 与 Rule 的闭包可以从本文独立重建；不得按名称、版本范围或本机安装推断 Profile。

| Profile ID / Version | Family | Canonical Definition Record | Profile Definition Digest |
|---|---|---|---|
| `swm.profile.build.maven-pom-model@1 / 1.0.0` | `BUILD` | `PROFILE|swm.profile.build.maven-pom-model@1|1.0.0|BUILD|MAVEN_POM_4_0_0|PROJECT_PARENT_MODULES_COORDINATES_DEPENDENCY_MANAGEMENT_DEPENDENCIES_PROPERTIES_PROFILES|NO_PLUGIN_EXECUTION_NO_ENVIRONMENT_ACTIVATION_NO_EFFECTIVE_MODEL_WITHOUT_COMPLETE_PARENTS_PROPERTIES_PROFILES` | `sha256:ce0280467e2e7ba5f162fa26df2e1a9447faa2ce32e971bc962d5cdb781d607c` |
| `swm.profile.java.source-17@1 / 1.0.0` | `JAVA_LANGUAGE` | `PROFILE|swm.profile.java.source-17@1|1.0.0|JAVA_LANGUAGE|JAVA_LANGUAGE_LEVEL_17|DECLARATION_EXPRESSION_CONTROL_CALL_DATA_STATE_EXCEPTION_ANNOTATION|NO_GENERATED_SOURCE_NO_REFLECTION_NO_RUNTIME_DISPATCH_WITHOUT_FORMAL_INPUT` | `sha256:8181313b6057e5c8737411cb057067eab9c930c690421c245dadfe1ac6e3a7ec` |
| `swm.profile.jdk.api-17@1 / 1.0.0` | `JAVA_LIBRARY` | `PROFILE|swm.profile.jdk.api-17@1|1.0.0|JAVA_LIBRARY|JDK_17|STRING_SEQUENCE_NUMERIC_BIGDECIMAL_DATE_TIME_COLLECTION_STREAM_ORDERED_MAP_BOUNDED_RANDOM|ONLY_EXACT_REGISTERED_SIGNATURES_NO_IMPLEMENTATION_SPECIFIC_BEHAVIOR` | `sha256:9944c6bc36c414e115ab4243e3737f2b4c4f4498f9b72e109868d829f1abbde2` |
| `swm.profile.spring-boot.source-3.2.2@1 / 1.0.0` | `SPRING_TRANSACTION` | `PROFILE|swm.profile.spring-boot.source-3.2.2@1|1.0.0|SPRING_TRANSACTION|SPRING_BOOT_3_2_2|EXPLICIT_SOURCE_ANNOTATION_CONFIGURATION_EXCEPTION_HANDLER_DECLARATIONS|NO_RUNTIME_AUTO_CONFIGURATION_NO_PROXY_ACTIVATION_NO_MANAGER_SELECTION_WITHOUT_FORMAL_CONFIG` | `sha256:16b75f507a49ff62490e20bafee7caee8980a5932fa4348c7f63ad78d44e8a6c` |
| `swm.profile.spring-boot.source-3.5@1 / 1.0.0` | `SPRING_TRANSACTION` | `PROFILE|swm.profile.spring-boot.source-3.5@1|1.0.0|SPRING_TRANSACTION|SPRING_BOOT_3_5|EXPLICIT_SOURCE_ANNOTATION_CONFIGURATION_EXCEPTION_HANDLER_DECLARATIONS|NO_RUNTIME_AUTO_CONFIGURATION_NO_PROXY_ACTIVATION_NO_MANAGER_SELECTION_WITHOUT_FORMAL_CONFIG` | `sha256:6c375f7d79ae47f296039844e0f5f2d9f18208aefdfa40de79fc6347cd0c5faf` |
| `swm.profile.spring-transaction.declarative@1 / 1.0.0` | `SPRING_TRANSACTION` | `PROFILE|swm.profile.spring-transaction.declarative@1|1.0.0|SPRING_TRANSACTION|SPRING_TRANSACTION_DECLARATIVE_SOURCE_SUBSET_1|TRANSACTIONAL_PROPAGATION_ROLLBACK_RULES_BOUNDARY_GUARANTEE_DIMENSIONS|NO_RUNTIME_PROXY_DB_ISOLATION_LOCK_OR_CONSTRAINT_STATE` | `sha256:f5e8fbef59f162be9c3efa39d7ed0a8f9ed303b5614ff9aeef751dd26596e4ce` |
| `swm.profile.mybatis.mapper-xml-3@1 / 1.0.0` | `QUERY_MAPPING` | `PROFILE|swm.profile.mybatis.mapper-xml-3@1|1.0.0|QUERY_MAPPING|MYBATIS_MAPPER_XML_3|NAMESPACE_STATEMENT_PARAMETER_RESULT_BINDING_STATIC_DYNAMIC_BRANCH_STRUCTURE|NO_DYNAMIC_PROVIDER_NO_RUNTIME_CONFIGURATION_NO_UNRESOLVED_INCLUDE` | `sha256:9c2f5ef0222a8d3d275194999426d8693b85695cf57256eb2207b4cc14fe86fa` |
| `swm.profile.sql.repository-core@1 / 1.0.0` | `QUERY_MAPPING` | `PROFILE|swm.profile.sql.repository-core@1|1.0.0|QUERY_MAPPING|SQL_REPOSITORY_CORE_SUBSET_1|SELECT_INSERT_UPDATE_DELETE_CREATE_TABLE_SCAN_FILTER_JOIN_PROJECT_GROUP_AGGREGATE_SORT_LIMIT_PREDICATE_NULL_THREE_VALUED_CONSTRAINT_DECLARATION|NO_VENDOR_DIALECT_TRIGGER_PROCEDURE_COLLATION_TIMEZONE_OR_IMPLICIT_CAST_WITHOUT_FORMAL_CONFIG` | `sha256:885e1674f50e5f1d6d74de6712680fc479ca0a3c5d8d248e92a7a11e48b2093f` |
| `swm.profile.external-api.model-reviewed@1 / 1.0.0` | `EXTERNAL_API` | `PROFILE|swm.profile.external-api.model-reviewed@1|1.0.0|EXTERNAL_API|VERSIONED_COMPONENT_CALL_CONTRACT|EXACT_COMPONENT_VERSION_OR_EXACT_FRAMEWORK_PROFILE_WITH_PARENT_VERSION_CALL_BINDING_FORMAL_FACT_PREMISES_TYPED_SEMANTIC_CONCLUSION|NO_MODEL_MEMORY_AS_FORMAL_PREMISE_NO_DEFAULT_LIBRARY_BEHAVIOR_UNKNOWN_ON_MISSING_BINDING_VERSION_OR_REVIEW_DISAGREEMENT` | `sha256:bdf1bc1f6cf72667b31c6cf54a403207f1983ad16a160e52369520c2b35aa0e6` |
| `swm.profile.external-api.spring-framework-public-6@1 / 1.0.0` | `EXTERNAL_API` | `PROFILE|swm.profile.external-api.spring-framework-public-6@1|1.0.0|EXTERNAL_API|SPRING_FRAMEWORK_PUBLIC_API_6|BOOT_PARENT=org.springframework.boot:spring-boot-starter-parent@3.2.2,3.5.14_EXACT_SOURCE_TYPE_SIGNATURE_MODEL_REVIEWED_TYPED_SEMANTICS|REQUIRE_OVERRIDE_PROPERTY_DEPENDENCY_CONFIGURATION_CLOSURE_NO_TRANSITIVE_COMPONENT_VERSION_ASSERTION_NO_INSTANCE_CONFIG_NO_RUNTIME_BEHAVIOR` | `sha256:ad526b19d308dc4340392b634cf433838de6a5a2560c5e1eb6b0c2a1c8af08c9` |

Catalog 的规范适用面固定如下：

| Profile | APPLICABLE 的最小充分输入 | 保持 UNKNOWN 的边界 |
|---|---|---|
| Maven POM Model | 完整 `modelVersion=4.0.0` descriptor region；parent、properties、profiles和activation输入均在正式输入闭包内 | plugin执行、环境/文件激活、未读parent/property/profile或工具运行结果 |
| Java Source 17 | parser明确选择language level 17；目标node完整且node kind属于 Provider Observation 或 JAVA_LANGUAGE Rule 显式允许集合 | preview/unsupported/generated syntax、reflection、未解析overload/generic/dynamic dispatch |
| JDK API 17 | callee同时具有exact declaring type、method descriptor和JDK 17 profile；操作属于 `String/primitive-wrapper/BigDecimal/Date-Time/Collection-Stream/ordered-map/bounded-random` Rule 明示语义面 | 未注册第三方类型、JDK实现细节、缺少descriptor/类型/nullability/rounding/order/time输入 |
| Spring Boot Source 3.2.2 / 3.5 | source或repository配置明确且唯一匹配对应 exact Profile；只解释显式annotation/configuration/exception-handler declaration | 两个版本之间不回退；运行时auto-configuration、proxy激活、bean/advice顺序、transaction manager或部署配置 |
| Spring Transaction Declarative | `Transactional` 声明及其显式属性、调用边界、异常类型和正式配置均完整；只解释本 Pack SPRING_TRANSACTION Rule 的声明子集 | runtime proxy、self invocation、DB isolation/lock/constraint状态或任何未显式默认 |
| MyBatis Mapper XML 3 | 完整mapper namespace与`select|insert|update|delete` statement；使用的`include|if|choose|when|otherwise|foreach|where|set|trim`分支均闭合 | dynamic provider、未解析include、运行时configuration、插件或生成mapping |
| SQL Repository Core | 完整repository declaration；operation限`SELECT|INSERT|UPDATE|DELETE|CREATE_TABLE`且AST仅使用Catalog record列出的operator | vendor dialect、trigger/procedure、collation/timezone、隐式cast、运行schema与数据 |
| External API Model-reviewed | 已发布`BUILD-EFFECTIVE-DEPENDENCY-RESOLUTION@1`结果及正式`RESOLVES_EFFECTIVE_DEPENDENCY`知识唯一固定source owner module、exact component/version；或Catalog exact Framework Profile由owner module的完整effective descriptor chain、链尾exact supported parent及链上所有override/property/dependency/profile/activation/config closed-set closure共同支撑；program-call Fact与正式type/data前提可唯一重建resolved Call Binding；所有输入/输出Term命中使用方Schema closed type | 版本范围、`BUILD-EFFECTIVE-VALUE@1`或source declaration冒充effective dependency、Framework Profile缺owner/descriptor-chain/parent Formal Basis或链上任一closure、source token无法唯一解析signature、动态dispatch多义、非正式前提、开放文本结论或生成/审核分歧 |
| Spring Framework Public API 6 | exact source declaring type属于Spring Framework public API 6；source call owner module的published descriptor chain从child逐项闭合到root，链尾`DECLARES_PARENT` Fact逐字匹配`org.springframework.boot:spring-boot-starter-parent@3.2.2|3.5.14`；链上每个descriptor的override/property/dependency/profile/activation/config selector均由published closed-set Fact闭合且所有成员已解释；method/arguments/source types足以唯一审核descriptor；必须披露transitive component version未独立解析 | 非public/internal API、其他parent coordinate/version、owner module或child→root链断裂、链上任一selector/Coverage/成员解释不完整、source type/signature多义、实例配置/bean state/proxy/runtime behavior、企图断言未解析的transitive component version |

每次 Pack Rule Application至少有一个Primary Profile且其Family必须与Rule Family相等；只有Rule表显式声明跨Family basis时才可增加Supporting Profile。跨Family列表按`Profile ID`字节升序，且每个Profile都必须来自本Catalog。当前只有`EXTERNAL-API-SEMANTIC-INTERPRETATION@1`允许把Catalog中的Framework Profile作为component basis；它仍必须同时包含External API Primary Profile。输入无法逐项命中上述适用面时结果必须为`UNKNOWN`，不得选择“最接近”Profile。`CONSUMER_LOCAL_RULE_REF`只接受Definition Record声明的`PROFILE_MODE=FORMAL_KNOWLEDGE_ONLY`，Profile List必须为`EMPTY`；原始软件语义必须已经存在于有exact Rule/Profile Provenance的已发布Formal Premise中。Local Rule若需要解释任何Source Observation、语言、库、框架或查询语义，必须改用相应Pack Rule，不能自行添加Profile或用空Profile绕过Catalog。

Spring Transaction Profile 与 Boot Profile 是正交且必须同时闭合的语义维度：`swm.profile.spring-transaction.declarative@1` 定义声明式事务规则子集，不隐含任何 Boot 版本；在 Boot 3.2.2 或 3.5 来源上应用 SPRING_TRANSACTION Rule 时，Profile List 必须分别包含匹配的 exact Boot Profile 与该 exact Transaction Profile。两者不允许互相替代；缺少任一项或 Boot 版本不匹配时 Applicability=`UNKNOWN`。

### 1.2 Exact Profile Tag Registry Catalog

Profile Definition不允许挂接运行时自造tag。每个§1.1 Profile在本Pack中恰好绑定一个下表core Registry。`Registry Definition Digest`按`SWM-PROFILE-TAG-REGISTRY-RECORD-LF@1`计算：对`Canonical Registry Definition Record`反引号内ASCII字节追加一个LF后执行SHA-256。

| Exact Profile | Registry ID / Version | Canonical Registry Definition Record | Registry Definition Digest |
|---|---|---|---|
| `swm.profile.build.maven-pom-model@1 / 1.0.0` | `swm.tagreg.build.maven-pom-model@1 / 1.0.0` | `TAGREG|swm.tagreg.build.maven-pom-model@1|1.0.0|swm.profile.build.maven-pom-model@1|1.0.0|NODE=DESCRIPTOR,PARENT_DECLARATION,MODULE_DECLARATION,COMPONENT_DECLARATION,DEPENDENCY_MANAGEMENT_DECLARATION,DEPENDENCY_DECLARATION,PROPERTY_DECLARATION,PROFILE_DECLARATION,ACTIVATION_DECLARATION,CONFIGURATION_DECLARATION;OPERATOR=LITERAL,PROPERTY_REFERENCE,ACTIVATION_PREDICATE;TYPE=COORDINATE,VERSION_STRING,SCOPE_TOKEN|NO_EXTENSION` | `sha256:0ef43e6b6126a958242ebf01d210a4fbbec5c7f7cc19f7a07cddc2251b114cd6` |
| `swm.profile.java.source-17@1 / 1.0.0` | `swm.tagreg.java.source-17-core@1 / 1.0.0` | `TAGREG|swm.tagreg.java.source-17-core@1|1.0.0|swm.profile.java.source-17@1|1.0.0|NODE=TYPE_DECLARATION,METHOD_DECLARATION,CONSTRUCTOR_DECLARATION,FIELD_DECLARATION,PARAMETER_DECLARATION,LOCAL_DECLARATION,IF,SWITCH,LOOP,TRY,CATCH,FINALLY,RETURN,THROW,INVOCATION,CONSTRUCTION,ASSIGNMENT,LAMBDA,MEMBER_ACCESS,INDEX,LITERAL,ANNOTATION;OPERATOR=PLUS,MINUS,MULTIPLY,DIVIDE,REMAINDER,EQUAL,NOT_EQUAL,LT,LE,GT,GE,LOGICAL_AND,LOGICAL_OR,NOT,NEGATE,CAST,INSTANCE_OF,CONDITIONAL,ASSIGN;TYPE=BOOLEAN,BYTE,SHORT,INT,LONG,FLOAT,DOUBLE,CHAR,VOID,REFERENCE;ROUNDING=UP,DOWN,CEILING,FLOOR,HALF_UP,HALF_DOWN,HALF_EVEN,UNNECESSARY;OVERFLOW=JAVA_NARROWING,JAVA_WRAP,THROW,EXACT|NO_EXTENSION` | `sha256:de38b7b5b7ed242e5e7daf2552e2b8ac6978d77dbf7686e81e69faf92945ddb9` |
| `swm.profile.jdk.api-17@1 / 1.0.0` | `swm.tagreg.jdk.api-17-core@1 / 1.0.0` | `TAGREG|swm.tagreg.jdk.api-17-core@1|1.0.0|swm.profile.jdk.api-17@1|1.0.0|OPERATOR=STRING_SEQUENCE,NUMERIC_CONVERSION,DECIMAL_ARITHMETIC,DATE_TIME_COMPARISON,DATE_TIME_OFFSET,COLLECTION_FILTER,COLLECTION_MAP,COLLECTION_GROUP,COLLECTION_REDUCE,COLLECTION_SORT,ORDERED_MAP,RANDOM_BOUND;TYPE=JDK_REFERENCE,JDK_VALUE;ROUNDING=UP,DOWN,CEILING,FLOOR,HALF_UP,HALF_DOWN,HALF_EVEN,UNNECESSARY;OVERFLOW=JAVA_NARROWING,JAVA_WRAP,THROW,EXACT|NO_EXTENSION` | `sha256:0d01f97c4e669c1b8ed5dea103cd4420178d6d906bfb812c522777cabfca1748` |
| `swm.profile.spring-boot.source-3.2.2@1 / 1.0.0` | `swm.tagreg.spring-boot.source-3.2.2@1 / 1.0.0` | `TAGREG|swm.tagreg.spring-boot.source-3.2.2@1|1.0.0|swm.profile.spring-boot.source-3.2.2@1|1.0.0|NODE=ANNOTATION_DECLARATION,CONFIGURATION_DECLARATION,EXCEPTION_HANDLER_DECLARATION;OPERATOR=ANNOTATION_APPLICATION,CONFIGURATION_BINDING,HANDLER_MAPPING;TYPE=FRAMEWORK_TYPE|NO_EXTENSION` | `sha256:ae5b964d2bdd04917af71a0cf4d31bf3281fad3cb8a57cf3a9fdd277f2d2c756` |
| `swm.profile.spring-boot.source-3.5@1 / 1.0.0` | `swm.tagreg.spring-boot.source-3.5@1 / 1.0.0` | `TAGREG|swm.tagreg.spring-boot.source-3.5@1|1.0.0|swm.profile.spring-boot.source-3.5@1|1.0.0|NODE=ANNOTATION_DECLARATION,CONFIGURATION_DECLARATION,EXCEPTION_HANDLER_DECLARATION;OPERATOR=ANNOTATION_APPLICATION,CONFIGURATION_BINDING,HANDLER_MAPPING;TYPE=FRAMEWORK_TYPE|NO_EXTENSION` | `sha256:6049ff53bdbac403b6690ad1f7560e46159186ea84c4cb618d898be1206941e4` |
| `swm.profile.spring-transaction.declarative@1 / 1.0.0` | `swm.tagreg.spring-transaction.declarative@1 / 1.0.0` | `TAGREG|swm.tagreg.spring-transaction.declarative@1|1.0.0|swm.profile.spring-transaction.declarative@1|1.0.0|OPERATOR=TRANSACTION_APPLICATION,ROLLBACK_ASSESSMENT,GUARANTEE_ASSESSMENT;TYPE=PROPAGATION,ROLLBACK_RULE,TRANSACTION_BOUNDARY;GUARANTEE=ATOMICITY,ISOLATION,RACE_EXCLUSION,UNIQUENESS|NO_EXTENSION` | `sha256:a48199bca1dcffe1904708f7961d21987bf91eb1d8c7bc85b20184804b2a00ef` |
| `swm.profile.mybatis.mapper-xml-3@1 / 1.0.0` | `swm.tagreg.mybatis.mapper-xml-3@1 / 1.0.0` | `TAGREG|swm.tagreg.mybatis.mapper-xml-3@1|1.0.0|swm.profile.mybatis.mapper-xml-3@1|1.0.0|NODE=MAPPER,SELECT,INSERT,UPDATE,DELETE,INCLUDE,IF,CHOOSE,WHEN,OTHERWISE,FOREACH,WHERE,SET,TRIM,PARAMETER_MAPPING,RESULT_MAPPING;OPERATOR=MAPPER_BINDING,PARAMETER_BINDING,RESULT_BINDING;TYPE=MAPPER_TYPE|NO_EXTENSION` | `sha256:5721ab6beb63e910e7e1432943c72e72f7add38142fcd264dda4a2e494486ca2` |
| `swm.profile.sql.repository-core@1 / 1.0.0` | `swm.tagreg.sql.repository-core@1 / 1.0.0` | `TAGREG|swm.tagreg.sql.repository-core@1|1.0.0|swm.profile.sql.repository-core@1|1.0.0|NODE=SCAN,FILTER,JOIN,PROJECT,GROUP,AGGREGATE,SORT,LIMIT,SET_OP,PREDICATE,INSERT,UPDATE,DELETE,CREATE_TABLE,FIELD_DECLARATION,CONSTRAINT_DECLARATION;OPERATOR=EQUAL,NOT_EQUAL,LT,LE,GT,GE,AND,OR,NOT,IS_NULL,IS_NOT_NULL,ADD,SUBTRACT,MULTIPLY,DIVIDE;JOIN=INNER,LEFT,RIGHT,FULL,CROSS;SET_OPERATOR=UNION,UNION_ALL,INTERSECT,EXCEPT;CONSTRAINT=PRIMARY_KEY,UNIQUE,NOT_NULL,CHECK,FOREIGN_KEY;TYPE=SQL_VALUE,SQL_RELATION|NO_EXTENSION` | `sha256:7ff057ee3ed339acfd0602f6cc11ba884a3172a43829a07b607a741ab5e7a96a` |
| `swm.profile.external-api.model-reviewed@1 / 1.0.0` | `swm.tagreg.external-api.model-reviewed-core@1 / 1.0.0` | `TAGREG|swm.tagreg.external-api.model-reviewed-core@1|1.0.0|swm.profile.external-api.model-reviewed@1|1.0.0|OPERATOR=RETURN_VALUE,COPY_VALUE,TRANSFORM_VALUE,MUTATE_RECEIVER,WRITE_ARGUMENT_TARGET,READ_EXTERNAL_STATE,WRITE_EXTERNAL_STATE,VALIDATE,PARSE,ENCODE,DECODE,COMPARE,CONSTRUCT,THROW,NONDETERMINISTIC_RESULT;TYPE=EXTERNAL_COMPONENT_TYPE;LIMITATION=RUNTIME_STATE_UNOBSERVED,DYNAMIC_BINDING_UNRESOLVED,CONFIGURATION_UNRESOLVED,SEMANTICS_UNKNOWN|NO_EXTENSION` | `sha256:232912adf22bd6948e7ef9fff17a3c3fe62cce18d3e7c129d25e6e967981cd2e` |
| `swm.profile.external-api.spring-framework-public-6@1 / 1.0.0` | `swm.tagreg.external-api.spring-framework-public-6@1 / 1.0.0` | `TAGREG|swm.tagreg.external-api.spring-framework-public-6@1|1.0.0|swm.profile.external-api.spring-framework-public-6@1|1.0.0|OPERATOR=RETURN_VALUE,COPY_VALUE,TRANSFORM_VALUE,MUTATE_RECEIVER,VALIDATE,CONSTRUCT,THROW;TYPE=SPRING_PUBLIC_API_TYPE;LIMITATION=TRANSITIVE_COMPONENT_VERSION_UNRESOLVED,INSTANCE_CONFIGURATION_UNRESOLVED,RUNTIME_STATE_UNOBSERVED|NO_EXTENSION` | `sha256:93963e0dd0ac25d117c9c93f9678073de29eed92d2c997f0db2af7076791e67b` |

Member Catalog字段按分号分组、每组按`TAG_KIND=member1,member2...`编码；分组与成员顺序是规范顺序。`Exact Profile Tag Reference`固定为：

`TUPLE(ENUM(PROFILE_TAG_REF),ExactInterpretationProfileRef,ID(registryId),ID(registryVersion),DIGEST(registryDefinitionDigest),ENUM(tagKind),ID(memberId),UINT64(memberOrdinal),DIGEST(memberDefinitionDigest))`

`memberOrdinal`是按Record中的分组顺序再按组内成员顺序展平的零基序号。`Member Definition Record = TAG|registryId|registryVersion|tagKind|memberId`，其Digest按ASCII Record加LF执行SHA-256。Verifier必须重算Registry Record Digest、Profile↔Registry唯一绑定、ordinal、member string和Member Digest；任一不一致或Catalog不存在该成员时失败关闭。

本版本所有Registry均为`NO_EXTENSION`，不存在外部运行时Registry依赖。未来增加tag只能发布新Pack版本并在其Payload Catalog中以新exact Registry Record声明；不得在本Pack上挂接插件、自造ID、近似名称或“当前最新版”。这使当前依赖闭合，同时不要求在本次迭代列举整门语言或所有第三方API。

## 2. 共通 Rule Contract

### 2.1 输入封装

每次规则应用只接受下列closed输入封装；Pack本身只认识§1定义的Consumer typed wrapper，不使用未导入的Schema-local短类型名。

- `ExactConsumerRuleInputContractRef=TUPLE(ENUM(CONSUMER_RULE_INPUT_CONTRACT_REF),ExactConsumerDefinitionRef,consumerInferenceTypeId,contractId,contractVersion,DIGEST(contractDefinitionRecord))`。Record必须存在于该exact Consumer Definition，且在Request之前闭合声明每个Pack semantic slot或Local Rule input slot的closed consumer type、cardinality、允许Authority variant、唯一value projection、Context Role，以及唯一named canonical output member/type/cardinality；它禁止Request、Manifest、Proposal、Rule Output、Candidate、Admission、Publication及其digest。Consumer Contract只能窄化Pack Rule的Applicability/Input/Output，不能增加或改写Rule语义；Local Rule必须把其完整I/O与Step slot contract内联在Local Rule Record中，本Ref只选择相同consumer codec而不创建第二份权威定义。
- Pack通用`RuleInputSemanticSlot`闭集为`PRIMARY_SUBJECT|FORMAL_BASIS|CONTEXT_BASIS|REQUESTED_BASIS|PRIOR_RULE_RESULT|SCHEMA_CONFIGURATION`。§2.5为每条Pack Rule固定required/optional slot；`CONSUMER_LOCAL_RULE_REF`则使用其Record内联slot。任何动态role ID或Catalog外slot非法。
- `ExactPriorRuleOutputRef=TUPLE(ENUM(PRIOR_RULE_OUTPUT_REF),ExactConsumerTypedObject ruleExecutionSequenceRef,UINT64(priorExecutionOrdinal),ExactRuleRef,resultId,RuleApplicationInputManifestDigest,RuleOutputDigest)`；它必须解析同一Sequence内完整Canonical Rule Output。`PriorRuleOutcomeTerm=TUPLE(ENUM(PRIOR_RULE_OUTCOME_TERM),ExactPriorRuleOutputRef,ENUM(APPLICABLE_UNKNOWN|NOT_APPLICABLE_UNKNOWN|UNKNOWN_UNKNOWN),ENUM(INTERPRETATION_UNKNOWN|NOT_APPLICABLE|APPLICABILITY_UNKNOWN))`，只能从所解析Output的无语义UNKNOWN branch机械投影，FAILED或INTERPRETED均不能构造该Term。
- `RuleInputAuthorityRef`是closed union：`SOURCE_OBSERVATION(ExactConsumerTypedObject observationEnvelope) | FORMAL_KNOWLEDGE(ExactConsumerTypedObject formalKnowledgeState) | FROZEN_CONTEXT(ExactConsumerTypedObject contextObject) | REQUESTED_BASIS(ExactConsumerTypedObject authorizedRequestedBasis) | PRIOR_RULE_OUTPUT(ExactPriorRuleOutputRef) | PRIOR_RULE_OUTCOME(ExactPriorRuleOutputRef) | SCHEMA_CONFIGURATION(ExactConsumerTypedObject configurationObject)`。每个Consumer object的Definition必须等于Request target Definition、完整前像可解码且Digest可重算；Observation wrapper必须内联Provider完整Source Interpretation Observation Envelope/Digest和唯一Source identity，不能只携同值output digest。Formal/Requested/Context/Configuration wrapper同样必须内联其Schema exact closed object，而非短Ref或裸digest。
- `AuthorityValueProjection`是closed union：`CONSUMER_WHOLE_OBJECT | CONSUMER_REGISTERED_FIELD_PATH(ExactConsumerTypedObject closedFieldPath) | PRIOR_OUTPUT_MEMBER(UINT64(outputMemberOrdinal)) | PRIOR_OUTCOME_STATUS`。`PROJECT_AUTHORIZED_TYPED_INPUT(Authority,Projection)`固定：WHOLE返回Consumer wrapper内的完整typed object；FIELD_PATH按同Definition注册path从其Authority object唯一抽取；OUTPUT_MEMBER从已解析`APPLICABLE_INTERPRETED` Output的有名member抽取；OUTCOME_STATUS只返回上述`PriorRuleOutcomeTerm`。Projection variant必须与Authority variant兼容，路径owner/type必须匹配，结果canonical bytes必须与下述input逐字相等；因此不能将Authority A与同类型值B拼接。
- `RuleApplicationTypedInput=TUPLE(UINT64(inputOrdinal),RuleInputSemanticSlot,UINT64(slotMemberOrdinal),ENUM(SOURCE_INTERPRETATION_OBSERVATION|RESOLVED_FORMAL_KNOWLEDGE|TYPED_VALUE|SCHEMA_CONFIGURATION),RuleInputAuthorityRef,AuthorityValueProjection,ContextRole,canonicalTypedInput,TypedInputDigest)`；`TypedInputDigest=DIGEST(canonicalTypedInput完整closed bytes)`。inputOrdinal全局从0连续；slotMemberOrdinal在每个slot内从0连续。Exact Consumer Input Contract与Pack §2.5或Local Rule Record必须对slot、closed type、cardinality、Authority/Projection和Context Role同时PASS。
- input kind与Authority variant的合法矩阵只有：`SOURCE_INTERPRETATION_OBSERVATION→SOURCE_OBSERVATION`、`RESOLVED_FORMAL_KNOWLEDGE→FORMAL_KNOWLEDGE`、`TYPED_VALUE→FROZEN_CONTEXT|REQUESTED_BASIS|PRIOR_RULE_OUTPUT|PRIOR_RULE_OUTCOME`、`SCHEMA_CONFIGURATION→SCHEMA_CONFIGURATION`。Consumer-local `FORMAL_KNOWLEDGE_ONLY` Rule只接受`RESOLVED_FORMAL_KNOWLEDGE`与`TYPED_VALUE`两行，并要求至少一个可递归解析到published Fact leaf的Formal Knowledge输入；`PRIOR_RULE_OUTCOME`只允许Local Rule Record显式声明的epistemic slot。
- `RuleProfileBinding`是closed union：`PACK_PROFILE_REQUIRED(ExactInterpretationProfileRef primary,ORDERED_LIST(ExactInterpretationProfileRef supporting),ORDERED_LIST(ExactProfileTagRef)) | CONSUMER_LOCAL_PROFILE_FREEZE(EMPTY_PROFILE_LIST,EMPTY_PROFILE_TAG_LIST)`。primary与supporting的完整Profile Ref按Profile ID唯一，supporting升序；Tag Ref按完整canonical digest唯一升序，每个Tag内的Profile Ref必须逐字属于primary∪supporting，且输入实际使用的Profile Tag与列表双向无missing/extra。前者只适用于`PACK_RULE_REF`，后者只适用于`FORMAL_KNOWLEDGE_ONLY` Local Rule。
- `FiniteRuleExecutionEnvelope=TUPLE(UINT64(maxRuleSteps),UINT64(maxInputMembers),UINT64(maxCanonicalBytes),UINT64(maxModelCalls),UINT64(maxDurationMillis))`；除`maxModelCalls`外各上限必须大于0；MECHANICAL要求`maxModelCalls=0`，MODEL_REVIEWED要求`maxModelCalls>=2`，且实际执行不得超过任一上限。
- `RuleApplicationRequestCore=TUPLE(ENUM(RULE_APPLICATION_REQUEST_CORE),ExactRuleRef,ExactConsumerDefinitionRef targetDefinition,ExactConsumerRuleInputContractRef,ExactConsumerTypedObject ruleExecutionSequenceRef,UINT64(ruleExecutionOrdinal),ExactConsumerTypedObject executionBoundary,ExactConsumerTypedObject knowledgeScope,ExactConsumerTypedObject frozenKnowledgeContext,RuleProfileBinding,ORDERED_LIST(RuleApplicationTypedInput),FiniteRuleExecutionEnvelope)`；Sequence/Boundary/Scope/Context wrapper的codec必须逐字命中Consumer Input Contract，且四者Definition均等于target Definition。`RuleApplicationRequestDigest=DIGEST(RuleApplicationRequestCore)`；`RuleApplicationRequest=TUPLE(ENUM(RULE_APPLICATION_REQUEST),RuleApplicationRequestCore,RuleApplicationRequestDigest)`。
- `ApplicabilityInputCore=TUPLE(ENUM(APPLICABILITY_INPUT_CORE),ExactRuleRef,ExactConsumerDefinitionRef,ExactConsumerRuleInputContractRef,ExactConsumerTypedObject ruleExecutionSequenceRef,UINT64(ruleExecutionOrdinal),ExactConsumerTypedObject executionBoundary,ExactConsumerTypedObject knowledgeScope,ExactConsumerTypedObject frozenKnowledgeContext,RuleProfileBinding,ORDERED_LIST(TUPLE(UINT64(inputOrdinal),RuleInputSemanticSlot,UINT64(slotMemberOrdinal),ENUM(SOURCE_INTERPRETATION_OBSERVATION|RESOLVED_FORMAL_KNOWLEDGE|TYPED_VALUE|SCHEMA_CONFIGURATION),RuleInputAuthorityRef,AuthorityValueProjection,ContextRole,TypedInputDigest)))`；其列表与同一Request全部Input双向无missing/extra，所有非value字段逐字相等；`ApplicabilityInputDigest=DIGEST(ApplicabilityInputCore)`。
- `RuleApplicationInputManifestCore=TUPLE(ENUM(RULE_APPLICATION_INPUT_MANIFEST_CORE),RuleApplicationRequest,ApplicabilityInputCore,ApplicabilityInputDigest,TUPLE(ENUM(RULE_APPLICATION_IDEMPOTENCY_KEY),RuleApplicationRequestDigest))`；`RuleApplicationInputManifestDigest=DIGEST(RuleApplicationInputManifestCore)`；`RuleApplicationInputManifest=TUPLE(ENUM(RULE_APPLICATION_INPUT_MANIFEST),RuleApplicationInputManifestCore,RuleApplicationInputManifestDigest)`。

Verifier必须完整重算Request、全部Consumer wrapper、Authority→value projection、typed input、Applicability投影与Manifest Digest。每个Prior Ref的Sequence必须逐字等于当前Request Sequence且`priorExecutionOrdinal < ruleExecutionOrdinal`；相等、跨Sequence或环均失败。Consumer-local Rule Ref的Definition、Request target Definition、Input Contract Definition及Proposal Contract Definition必须相同；Pack Rule仍必须使用同一target Definition的Input/Proposal Contract。Artifact、Evidence Quote、模型摘要、动态CURRENT、未发布Candidate、类名相似和自然语言常识不能成为隐藏输入。内容寻址Dictionary不授予authority；Rule新term必须由有名Step/output member产生。

### 2.2 Applicability 与结果

| 对象 | 状态 | 语义 |
|---|---|---|
| Applicability | `APPLICABLE` | Profile、版本、调用形态、类型、配置和必需输入全部满足 Rule Contract |
| Applicability | `NOT_APPLICABLE` | 输入明确属于其他语义或违反允许形态 |
| Applicability | `UNKNOWN` | 版本、类型、动态绑定、配置、隐式默认或必要来源语义不能证明 |
| Rule Result | `INTERPRETED` | 两种Execution Class都携带同一完整`InterpretedSemanticResult`；MECHANICAL另携完整可重放Manifest，MODEL_REVIEWED另携Generation/Review与Eligibility或Fixture执行闭包 |
| Rule Result | `UNKNOWN` | 正常完成但结论不能在当前边界内建立 |
| Rule Result | `FAILED` | 输入、Digest、资源、解析或执行完整性失败；没有语义结果 |

Applicability与Rule Result不是两个可自由组合的enum。唯一合法矩阵为：`APPLICABLE_INTERPRETED(APPLICABLE,INTERPRETED)`、`APPLICABLE_UNKNOWN(APPLICABLE,UNKNOWN)`、`APPLICABLE_FAILED(APPLICABLE,FAILED)`、`NOT_APPLICABLE_UNKNOWN(NOT_APPLICABLE,UNKNOWN)`、`UNKNOWN_UNKNOWN(UNKNOWN,UNKNOWN)`、`UNKNOWN_FAILED(UNKNOWN,FAILED)`；其余组合均为codec failure。`NOT_APPLICABLE`只属于Applicability，不是Rule Result。

只有 `APPLICABLE_INTERPRETED` 携带语义payload并可以支持普通肯定结论。三个UNKNOWN分支只携带有名`NO_SEMANTIC_RESULT`：分别表示规则适用但解释未建立、规则不适用、适用性不能建立；它们不能携带typed output或公开Argument，也不能被改写为软件否定事实。使用方若要形成`NOT_ESTABLISHED_WITHIN_BOUNDARY`，必须由另一个显式epistemic Rule以该UNKNOWN状态、正式前提和封闭边界为输入重新建立。两个FAILED分支只携带`FAILED_NO_SEMANTIC_RESULT`，不得形成任何语义Candidate。

### 2.3 Canonical Rule Output

每个已经取得有效Exact Rule Reference与可完整解码Rule Application Input Manifest的Rule Application都形成一个closed `CanonicalRuleOutput` Envelope；Reference、Manifest或Profile Definition本身尚不能通过codec/digest校验时，Application Owner只形成§10前置失败记录，不伪造Canonical Rule Output。公共字段固定为Rule Reference、Execution Class、完整Rule Application Input Manifest / Digest和一个§2.2合法`RuleApplicationOutcome`。只有`APPLICABLE_INTERPRETED`分支包含typed output、公开Argument、假设、限制、已检查反例、Context Construction和执行Provenance；UNKNOWN/FAILED分支明确没有这些语义字段。公开Argument不保存或依赖模型隐藏 Chain-of-Thought。Rule Application Input Manifest是§2.1的软件语义输入闭包；它不等于、也不能替代Model Gateway的`AI-AUTHORIZED-INPUT-MANIFEST-01`，后者只证明某一次模型调用获准看到的精确输入。

公开Argument的唯一前置语义对象为：

- `ExactConsumerPublicArgumentContractRef=TUPLE(ENUM(CONSUMER_PUBLIC_ARGUMENT_CONTRACT_REF),ExactConsumerSchemaRef,consumerInferenceTypeId,argumentContractId,argumentContractVersion,DIGEST(argumentContractDefinition))`。该Reference必须解析到目标Schema冻结Payload中对该Inference Type注册的closed tagged codec；Definition Digest必须从该Payload的完整Definition Record重算，不能引用动态CURRENT、开放map/text或本机类型。
- `ProposalPublicArgumentCore=TUPLE(ENUM(PROPOSAL_PUBLIC_ARGUMENT_CORE),ExactRuleRef,RuleApplicationInputManifestDigest,ExactConsumerPublicArgumentContractRef,DIGEST(canonicalTypedOutput),consumerTypedPublicArgumentBody)`；`ProposalPublicArgumentDigest=DIGEST(ProposalPublicArgumentCore)`；`ProposalPublicArgument=TUPLE(ENUM(PROPOSAL_PUBLIC_ARGUMENT),ProposalPublicArgumentCore,ProposalPublicArgumentDigest)`。`consumerTypedPublicArgumentBody`必须以内联完整字段逐项命中上述consumer codec，且其Premise、Context、Rule、typed term、step、member assurance、Coverage basis和limitation只能引用形成Proposal前已冻结、可解析的对象；不能使用opaque bytes、只存digest、任意map/text或由Candidate补写的字段。
- `ProposalPublicArgumentCore`及其递归body明确禁止包含或摘要 `ModelExecutionEligibilityInputCore`、`ExactModelResultEligibilityRef`、`EligibleModelProposalBinding`、`ModelReviewedExecutionClosure`、Capability Provenance、`CanonicalRuleOutputCore`、`RuleOutputDigest`、`ExactRuleApplicationResultRef`、Candidate/`SelfCandidateToken`、Admission、Publication、目标/输出Snapshot、动态CURRENT或任何依赖这些后置对象的Reference/Digest。构成Rule Input的既有冻结Snapshot Formal Premise仍可按§2.1进入body，但不得换成动态CURRENT。Consumer Schema需要保存执行Provenance、Candidate binding或发布重放字段时，必须在`RuleOutputDigest`形成后用独立后置wrapper组合；该wrapper只能内联并重放本Core/Digest，不能反向进入本Core。

本文所有带自身校验摘要的新增对象统一遵循`XCore → XDigest=DIGEST(XCore) → XEnvelope=TUPLE(ENUM(X),XCore,XDigest)`；`XCore`不得包含`XDigest`、`XEnvelope`或其后置对象。`DIGEST(Y)`只有在`Y`是此前已定义、完整可解析且拓扑更早的closed preimage时才表示普通字段摘要，不得用未定义的`DIGEST(core|candidate|manifest|output)`暗示自摘要。

所有Execution Class只有在完整typed output与consumer-typed公开Argument都可构造时才形成下列`InterpretedSemanticResult`；否则直接进入Canonical Rule Output的UNKNOWN/FAILED无语义分支，不得伪造空typed output或空Argument。`MODEL_REVIEWED`在此基础上先形成不具有Rule Result权威的Generation与Review暂存Proposal。相关closed preimage为：

- `ReviewFinding=TUPLE(ENUM(PREMISE_UNRESOLVED|RULE_NOT_APPLICABLE|STEP_NOT_REPLAYABLE|COVERAGE_INCOMPLETE|CONTEXT_MISMATCH|CONCLUSION_UNSUPPORTED),PROPOSAL_WIDE|STEP(UINT64(proposalStepOrdinal))|MEMBER(DIGEST(canonicalConclusionMember)))`；MEMBER Digest必须从同一`ProposalPublicArgument`内可解析的完整typed Conclusion member重算。`ReviewProposalAssessment=TUPLE(ENUM(REVIEW_PROPOSAL_ASSESSMENT),ENUM(REVIEW_ASSERTS_PASS|REVIEW_ASSERTS_UNKNOWN|REVIEW_ASSERTS_DISAGREE),ORDERED_LIST(ReviewFinding))`；`REVIEW_ASSERTS_PASS`要求finding列表为空，`REVIEW_ASSERTS_UNKNOWN|REVIEW_ASSERTS_DISAGREE`要求非空且按完整Finding canonical digest唯一升序。该codec没有任意map/text、隐藏状态、置信度、Rule Verification/Obligation/Admission Decision或可扩展字段。
- `InterpretedSemanticResultCore=TUPLE(ENUM(INTERPRETED_SEMANTIC_RESULT_CORE),canonicalTypedOutput,ProposalPublicArgument)`；`InterpretedSemanticResultDigest=DIGEST(InterpretedSemanticResultCore)`；`InterpretedSemanticResult=TUPLE(ENUM(INTERPRETED_SEMANTIC_RESULT),InterpretedSemanticResultCore,InterpretedSemanticResultDigest)`。Proposal Envelope内的output digest必须从同一Core内完整`canonicalTypedOutput`重算；Proposal内的Rule/Input随后必须分别与Generation或Mechanical Manifest、Rule Verification Decision及Canonical Rule Output外层逐字匹配。assumption、limitation、checked counterexample与context construction没有平行开放字段，只能按`ExactConsumerPublicArgumentContractRef`注册的closed codec存在于`consumerTypedPublicArgumentBody`并由完整Proposal Envelope覆盖；使用方不得在Semantic Result或后置对象中另行补写。
- `ModelProposalSemanticOutputCore=TUPLE(ENUM(MODEL_PROPOSAL_SEMANTIC_OUTPUT_CORE),ENUM(GENERATION|REVIEW),ExactRuleRef,RuleApplicationInputManifestDigest,ExactCapabilityAttemptRef,ExactCapabilityRef,ExactStrategyRef,ENUM(PRODUCTION|CAPABILITY_EVALUATION|CAPABILITY_VALIDATION),GENERATION(APPLICABLE,INTERPRETED,InterpretedSemanticResult)|REVIEW(ModelProposalSemanticOutputDigest targetGenerationDigest,InterpretedSemanticResult reviewedSemanticResult,ReviewProposalAssessment))`；`ModelProposalSemanticOutputDigest=DIGEST(ModelProposalSemanticOutputCore)`；`ModelProposalSemanticOutput=TUPLE(ENUM(MODEL_PROPOSAL_SEMANTIC_OUTPUT),ModelProposalSemanticOutputCore,ModelProposalSemanticOutputDigest)`。GENERATION中的Semantic Result Envelope必须与同一Core的Rule/Input逐字匹配；REVIEW必须取得目标Generation的完整Envelope，重算`targetGenerationDigest`，并内联逐字相同的Generation `InterpretedSemanticResult`后才可审核。三个`REVIEW_ASSERTS_*`都只是非权威Review Proposal字段：无论来自MODEL还是Fixture，都不能充当Rule Verifier、Knowledge Obligation或Admission Decision。该Core明确排除Eligibility、Capability Provenance、最终Rule Result、Rule Verification Decision、`RuleOutputDigest`和任何Admission/Publication对象，因而不能形成摘要环。Review执行失败不编码为审核断言，而进入下述`FAILED_NO_SEMANTIC_RESULT`。
- `ModelExecutionEligibilityInputCore=TUPLE(ENUM(MODEL_EXECUTION_ELIGIBILITY_INPUT_CORE),ENUM(GENERATION|REVIEW),ExactCapabilityAttemptRef,ExactCapabilityRef,ExactStrategyRef,ENUM(PRODUCTION|CAPABILITY_EVALUATION),ExactModelCallRef,DIGEST(modelCallRecord),requestedModelRef,actualModelFingerprint,PINNED|OBSERVED_MUTABLE|UNRESOLVED_MUTABLE,exactProviderRef,exactProviderConfigurationRef,exactAdapterRef,exactAdapterConfigurationRef,promptContractId,promptRevision,DIGEST(promptContract),DIGEST(renderedMessageSequence),ExactAuthorizedInputManifestRef,DIGEST(authorizedInputManifest),DIGEST(canonicalProviderRequest),ENUM(NO_EXTERNAL_ACCESS),ExactIsolationReceiptRef,DIGEST(isolationReceipt),ExactCapabilityCatalogSnapshotRef,DIGEST(capabilityCatalogSnapshot),ExactModelQualificationProofRef,DIGEST(modelQualificationProof),DIGEST(modelResponse),ModelProposalSemanticOutputDigest)`。Catalog Reference必须解析到冻结的Model/Adapter Identity Policy及同一Qualification Proof；Isolation Receipt必须在dispatch前签发，逐字绑定同一Manifest、Request、Provider/Adapter/configuration及仍有效的Adapter Conformance，并机械证明shell、文件系统、Web、MCP、Connector、Agent/Provider Tool、托管检索、附件、历史会话和隐藏应用上下文均不可用。
- `ExactModelResultEligibilityRef=TUPLE(ENUM(MODEL_RESULT_ELIGIBILITY_REF),ID(X-MODEL-RESULT-ELIGIBILITY-01),eligibilityResultId,DIGEST(ModelExecutionEligibilityInputCore),PASS,DIGEST(eligibilityResult))`；`EligibleModelProposalBindingCore=TUPLE(ENUM(ELIGIBLE_MODEL_PROPOSAL_BINDING_CORE),ModelProposalSemanticOutput,ModelExecutionEligibilityInputCore,ExactModelResultEligibilityRef,DIGEST(eligibilityResult))`；`EligibleModelProposalBindingDigest=DIGEST(EligibleModelProposalBindingCore)`；`EligibleModelProposalBinding=TUPLE(ENUM(ELIGIBLE_MODEL_PROPOSAL_BINDING),EligibleModelProposalBindingCore,EligibleModelProposalBindingDigest)`。Binding内Proposal Envelope与Eligibility Input的role、Attempt、Capability、Strategy、Execution Purpose和Proposal Digest必须逐字相等。Capability Owner必须从权威Model Call、Gateway、Catalog和Qualification记录独立重建全部字段；模型、Fixture或Candidate提交的inline副本没有资格。Model Response到Proposal的受控解析必须重算同一`ModelProposalSemanticOutputDigest`，不能借用一个合格Call证明另一份Proposal。
- `FixtureProposalBinding=TUPLE(ENUM(FIXTURE_PROPOSAL_BINDING),ModelProposalSemanticOutput,DRIVER(exactDriverRef,DIGEST(driverBinary))|REVIEW_FIXTURE(exactFixtureRef,DIGEST(fixtureBinary)),ENUM(MODEL_ELIGIBILITY_NOT_APPLICABLE))`。它只适用于`CAPABILITY_VALIDATION`；Generation使用DRIVER、Review使用独立REVIEW_FIXTURE，且Review Core仍绑定目标Generation Digest。Fixture不能构造、携带或冒充`ExactModelResultEligibilityRef`。
- `ModelReviewedExecutionClosure`是closed union：`ELIGIBLE_MODEL_EXECUTION(EligibleModelProposalBinding generation,EligibleModelProposalBinding review) | CAPABILITY_VALIDATION_FIXTURE(FixtureProposalBinding generation,FixtureProposalBinding review)`。前者要求两个Binding分别为GENERATION/REVIEW、Attempt/Strategy不同、Rule/Input/Purpose一致且Review绑定Generation；后者要求Purpose均为CAPABILITY_VALIDATION并保持Fixture角色分离。

最终codec先定义机械执行的完整可重放前像：`MechanicalRuleExecutionManifestCore=TUPLE(ENUM(MECHANICAL_RULE_EXECUTION_MANIFEST_CORE),ExactRuleRef,RuleApplicationInputManifest,RuleApplicationInputManifestDigest,ExactCapabilityAttemptRef executorAttempt,ExactCapabilityRef executorCapability,ExactStrategyRef executorStrategy,InterpretedSemanticResult)`；`MechanicalRuleExecutionManifestDigest=DIGEST(MechanicalRuleExecutionManifestCore)`；`MechanicalRuleExecutionManifest=TUPLE(ENUM(MECHANICAL_RULE_EXECUTION_MANIFEST),MechanicalRuleExecutionManifestCore,MechanicalRuleExecutionManifestDigest)`。Manifest完整内联Input与Semantic Result，不能只保存任一摘要。`ProposalPublicArgument`的consumer Contract必须为MECHANICAL执行声明其body内按0连续ordinal排列的完整Rule Step closed codec与唯一重放顺序；Verifier从Semantic Result中的Proposal Envelope解析全部typed Step Input/Output并逐步重算完整Semantic Result，不能依赖Pack中不存在的本机Step Catalog、opaque bytes、任意map/text或隐藏执行状态。Revision 002 consumer的该前像就是其完整`ORDERED_LIST(ProposalArgumentStep)`，不得另造摘要替代。

`RuleExecutionProof`是closed union：`MECHANICAL_RULE_EXECUTION(MechanicalRuleExecutionManifest) | MODEL_REVIEWED_RULE_EXECUTION(ModelReviewedExecutionClosure)`。`RuleVerificationDecisionCore=TUPLE(ENUM(RULE_VERIFICATION_DECISION_CORE),ExactCapabilityAttemptRef verifierAttempt,ExactCapabilityRef ruleVerifierCapability,ExactStrategyRef ruleVerifierStrategy,ExactRuleRef,RuleApplicationInputManifestDigest,InterpretedSemanticResult,RuleExecutionProof,ENUM(RULE_VERIFICATION_PASS))`；`RuleVerificationDecisionDigest=DIGEST(RuleVerificationDecisionCore)`；`RuleVerificationDecision=TUPLE(ENUM(RULE_VERIFICATION_DECISION),RuleVerificationDecisionCore,RuleVerificationDecisionDigest)`。该Decision只能由平台Rule Verifier Owner在取得完整Input、完整Semantic Result、Proposal/Review Envelope与Execution Proof后独立重放形成；verifier Attempt、Capability和Strategy必须从Application Authority冻结Catalog解析到同一`RULE_VERIFIER`职责，且Catalog必须将该Capability/Strategy标为`NON_MODEL_MECHANICAL`并提供可回读exact record/digest。本版本不允许MODEL、Agent、Fixture或无机械资格Strategy担任Rule Verifier。三项身份分别不得等于或别名到Generation、Review、Driver、Fixture以及`MechanicalRuleExecutionManifestCore`中executor的Attempt、Capability或Strategy。MODEL_REVIEWED正例要求Review Proposal为`REVIEW_ASSERTS_PASS`，但该断言只有被Decision独立验证后才可形成权威`RULE_VERIFICATION_PASS`；Fixture、MODEL、Driver、Rule Executor和Candidate均不得签发或提交Decision。

`CanonicalInterpretedPayload=TUPLE(ENUM(CANONICAL_INTERPRETED_PAYLOAD),InterpretedSemanticResult,RuleVerificationDecision)`；`NoSemanticResult=TUPLE(ENUM(NO_SEMANTIC_RESULT),ENUM(INTERPRETATION_UNKNOWN|NOT_APPLICABLE|APPLICABILITY_UNKNOWN))`；`FailedNoSemanticResult=TUPLE(ENUM(FAILED_NO_SEMANTIC_RESULT),ENUM(RULE_STEP_INCOMPLETE|RULE_VERIFICATION_FAILED|MODEL_CAPABILITY_NOT_AUTHORIZED|MODEL_EXECUTION_NOT_ELIGIBLE|MODEL_PROPOSAL_BINDING_MISMATCH|MODEL_REVIEW_TARGET_MISMATCH|PROPOSAL_PUBLIC_ARGUMENT_INVALID|VALIDATION_AUTHORITY_FENCE_VIOLATION|RESOURCE_LIMIT))`。`RuleApplicationOutcome`是唯一closed union：`APPLICABLE_INTERPRETED(APPLICABLE,INTERPRETED,CanonicalInterpretedPayload) | APPLICABLE_UNKNOWN(APPLICABLE,UNKNOWN,NoSemanticResult(INTERPRETATION_UNKNOWN)) | APPLICABLE_FAILED(APPLICABLE,FAILED,FailedNoSemanticResult) | NOT_APPLICABLE_UNKNOWN(NOT_APPLICABLE,UNKNOWN,NoSemanticResult(NOT_APPLICABLE)) | UNKNOWN_UNKNOWN(UNKNOWN,UNKNOWN,NoSemanticResult(APPLICABILITY_UNKNOWN)) | UNKNOWN_FAILED(UNKNOWN,FAILED,FailedNoSemanticResult)`。任何UNKNOWN/FAILED分支出现Interpreted Semantic Result、typed output、Proposal Public Argument、assumption、limitation、counterexample、contextConstruction、Rule Verification Decision或语义Execution Proof均为codec failure；诊断说明由Application/Knowledge Use的独立失败记录管理，不进入本Pack语义结果。

`CanonicalRuleOutputCore=TUPLE(ENUM(CANONICAL_RULE_OUTPUT_CORE),ExactRuleRef,ENUM(MECHANICAL|MODEL_REVIEWED),RuleApplicationInputManifest,RuleApplicationInputManifestDigest,RuleApplicationOutcome)`；`RuleOutputDigest=DIGEST(CanonicalRuleOutputCore)`；`CanonicalRuleOutput=TUPLE(ENUM(CANONICAL_RULE_OUTPUT),CanonicalRuleOutputCore,RuleOutputDigest)`。`APPLICABLE_INTERPRETED`中的`RuleVerificationDecisionCore`不是可移植断言：其Exact Rule、Input Manifest Digest、完整`InterpretedSemanticResult`和`RuleExecutionProof`必须分别与外层`CanonicalRuleOutputCore`、`CanonicalInterpretedPayload`及其执行闭包逐字相等，Execution Proof variant必须与外层Execution Class一致。MECHANICAL分支还必须从完整`MechanicalRuleExecutionManifest`重放每个Step，并要求其Rule、Input和Semantic Result Envelope与外层逐字相等；MODEL_REVIEWED分支中Generation与Review Envelope必须绑定同一外层Rule/Input/完整Semantic Result Envelope，Review必须内联并审核同一Semantic Result且为`REVIEW_ASSERTS_PASS`。独立Rule Verifier据此形成`RULE_VERIFICATION_PASS` Decision。任何来自另一Rule、Input、Semantic Result、Attempt或Execution Proof的合法Decision均不能移植到当前Output。因此`RuleOutputDigest`覆盖完整Mechanical Manifest，或两份Model Proposal Envelope、Review→Generation绑定、两份Eligibility Binding及其Call/隔离/资格闭包，并覆盖独立Rule Verification Decision。Consumer的后置Capability Provenance、完整Argument wrapper、Candidate或Publication对象只能在本Envelope之后形成并引用它，不得反向进入Proposal或Canonical Rule Output。摘要拓扑固定为`RuleApplicationRequestCore/Digest/Envelope → ApplicabilityInputCore/Digest → RuleApplicationInputManifestCore/Digest/Envelope → ProposalPublicArgumentCore → ProposalPublicArgumentDigest → ProposalPublicArgument → InterpretedSemanticResultCore/Digest/Envelope → [MODEL_REVIEWED: ModelProposalSemanticOutputCore/Digest/Envelope → Eligibility Input/Result → Eligible Binding | MECHANICAL: MechanicalRuleExecutionManifestCore/Digest/Envelope] → RuleVerificationDecisionCore/Digest/Envelope → CanonicalRuleOutputCore → RuleOutputDigest → CanonicalRuleOutput → Consumer Capability Provenance/Argument/Candidate`。

### 2.4 Execution Class

| Execution Class | Contract |
|---|---|
| `MECHANICAL` | 规则的规范变换、分支和输出可由确定性实现逐步重放；相同 exact 输入必须产生相同 canonical output。Parser / Verifier 的具体算法属于 Conformance 实现，但公开 Rule Step 必须足以机械重算结果 |
| `MODEL_REVIEWED` | Pack 固定输入闭包、typed Conclusion Contract、Context、必须公开的结构化 Argument、失败边界和独立 Verifier Profile；不冻结也不伪装模型的完整推理算法。生成与审核使用不同 Capability Attempt/Strategy和各自的`EligibleModelProposalBinding`，审核方只读正式前提、Contract和公开 Argument重建判断，不能读取生成会话或隐藏思维链；两次模型调用都必须在执行前机械建立`NO_EXTERNAL_ACCESS`隔离并在输出进入Rule Application前通过`X-MODEL-RESULT-ELIGIBILITY-01` |

Execution Class 只约束 Strategy / Argument Assurance，不是 Conclusion Modality、语义权威等级或 Admission Decision。`MODEL_REVIEWED` 不会把 `POSSIBLE` 提升为 `ASSERTED`；`MECHANICAL` 也不会自动产生 Fact。Fact / Inference边界和Modality只由使用方 Schema Contract决定。

只有`EXECUTION_PURPOSE=CAPABILITY_VALIDATION`允许MODEL_REVIEWED的Generation Proposal与Review Proposal分别由两个独立deterministic Fixture经公共Proposal Port提交，以验证完整门禁而隔离模型质量；Fixture只能形成`FixtureProposalBinding`，Eligibility必须显式为`MODEL_ELIGIBILITY_NOT_APPLICABLE`。Review Fixture可以在非权威Review Proposal中提交`REVIEW_ASSERTS_PASS`，但任何Fixture都不能签发`RULE_VERIFICATION_PASS`、Knowledge Obligation PASS、Admission Decision、Snapshot或CURRENT；权威Decision仍由真实Verifier/Gate按本Pack机械形成。CAPABILITY_VALIDATION Rule Output及其下游Candidate/Admission/Publication若为验证完整公共路径而继续，只能进入由Application Authority预先冻结并机械校验的`VALIDATION_ONLY` sink与Snapshot namespace；该namespace不得等于、别名到或切换任何production CURRENT，不得被production Reader当作正式答案来源，且其中Formal State永远不能成为`EXECUTION_PURPOSE=PRODUCTION`的Premise、Rule Input、Coverage Basis、Candidate continuation或Root/State复用来源。Consumer Schema必须把execution purpose和validation authority fence带入Admission、Snapshot/Reader及Premise解析并失败关闭；Pack不创建Snapshot，但不满足该fence的Fixture Rule Output不得离开暂存Proposal。`PRODUCTION|CAPABILITY_EVALUATION`必须由两个独立MODEL Attempt/Strategy形成Generation与Review `EligibleModelProposalBinding`；DRIVER、REVIEW_FIXTURE、缺失或非PASS Eligibility Result、非`NO_EXTERNAL_ACCESS` Receipt、隐藏上下文/Tool能力、Catalog/Qualification失效或任何绑定字段错配均失败关闭。PRODUCTION只接受PRODUCTION Catalog资格；CAPABILITY_EVALUATION只接受exact EVALUATION_ONLY Qualification且结果只能进入隔离Evaluation Sink，不能进入生产Candidate、Admission、Snapshot或缓存。

每个 Rule 的默认 Execution Class 固定如下：

| Rule | Execution Class |
|---|---|
| `BUILD-DECLARATION-ROLE@1`、`BUILD-COMPONENT-MODULE-BINDING@1`、`BUILD-DECLARATION-SET-CLOSURE@1`、`BUILD-EFFECTIVE-VALUE@1` | `MECHANICAL` |
| `BUILD-EFFECTIVE-DEPENDENCY-RESOLUTION@1` | `MODEL_REVIEWED` |
| `JAVA-TYPED-EXPRESSION@1`、`JAVA-CONTROL-FLOW@1`、`JAVA-CALL-BINDING@1`、`JAVA-DATA-FLOW@1`、`JAVA-STATE-EFFECT@1`、`JAVA-EXCEPTION-FLOW@1`、`JAVA-NULL-DEREFERENCE@1`、`JAVA-SEMANTIC-COMPARISON@1` | `MODEL_REVIEWED` |
| `JLIB-STRING-SEQUENCE@1`、`JLIB-NUMERIC-CONVERSION@1`、`JLIB-BIGDECIMAL@1`、`JLIB-DATE-TIME@1`、`JLIB-COLLECTION-PIPELINE@1`、`JLIB-ORDERED-MAP@1`、`JLIB-BOUNDED-RANDOM@1` | `MODEL_REVIEWED` |
| `SPRING-TRANSACTION-APPLICATION@1`、`SPRING-ROLLBACK-DEFAULT@1`、`SPRING-TRANSACTION-GUARANTEE@1`、`SPRING-EXCEPTION-HANDLER@1` | `MODEL_REVIEWED` |
| `QUERY-TYPED-AST@1`、`QUERY-MAPPER-BINDING@1`、`QUERY-DECLARATION-SET-CLOSURE@1` | `MECHANICAL` |
| `QUERY-PREDICATE-SEMANTICS@1`、`QUERY-UPDATE-SEMANTICS@1`、`QUERY-CONSTRAINT-SEMANTICS@1` | `MODEL_REVIEWED` |
| `EXTERNAL-API-SEMANTIC-INTERPRETATION@1` | `MODEL_REVIEWED` |
| 任一 `CONSUMER_LOCAL_RULE_REF` | 逐字等于其已验证 Local Rule Definition Record 的 `MECHANICAL|MODEL_REVIEWED`；运行时或调用方不得覆盖 |

本版本禁止把表中`MODEL_REVIEWED` Rule降级为`MECHANICAL`，也不注册`MECHANICAL_EQUIVALENCE_CONFORMANCE`。Request、Manifest、Execution Proof、Decision和Canonical Output的Execution Class必须逐字等于上表或Consumer-local Rule Record的class；存在parser、库或调用方声称等价都不能改变它。未来若启用退化，必须先以新Pack版本定义exact Conformance Ref/Record/Digest并把Rule/Profile/input domain/strategy绑定进Request→Proof→Decision全链。

`MODEL_REVIEWED` 的Generation和Review都只产生非权威暂存Proposal Envelope。只有两份Proposal分别取得合格Binding、Review提交`REVIEW_ASSERTS_PASS`、Review目标Digest匹配Generation，且平台Rule Verifier机械证明最终完整`InterpretedSemanticResult` Envelope、Decision字段与Execution Proof全部匹配后，才可构造`APPLICABLE_INTERPRETED`。Generation无法形成完整语义Proposal，或Review为`REVIEW_ASSERTS_UNKNOWN|REVIEW_ASSERTS_DISAGREE`时，最终只形成相应`NO_SEMANTIC_RESULT`；Eligibility、隔离、Catalog/Qualification、Call/Response/Proposal/Argument Digest、Envelope、Binding或Rule Verification失败时只形成`FAILED_NO_SEMANTIC_RESULT`，暂存输出不得进入语义Candidate、Assessment、Answer或任何生产状态。不得由多数投票、模型置信度、事后Tool事件检查或重试覆盖；新采样必须形成新Attempt、Model Call和完整Binding。CAPABILITY_VALIDATION Fixture按前款只验证方案门禁，不产生模型资格结论，也不得越过`VALIDATION_ONLY` fence。

本 Pack 只定义语义及审核义务，不证明任何真实模型具备相应能力。模型正确率、跨项目泛化、版本敏感性和生成/审核独立性由 Capability Evaluation 验证；Pack Conformance 不能替代该评测。

所有集合明确 `ORDERED | UNORDERED`；无序集合按成员 canonical digest 排序。有单位、精度、scale、rounding、时区或字符编码的值必须显式保存。未声明默认值不得补入输出。

### 2.5 Pack Rule I/O Semantic Slot Catalog

Pack Rule的具体Applicability/Input表仍定义软件语义，但所有实例输入必须先机械落入下表固定slot。符号`P/F/C/R/B/G`分别表示`PRIMARY_SUBJECT/FORMAL_BASIS/CONTEXT_BASIS/PRIOR_RULE_RESULT/REQUESTED_BASIS/SCHEMA_CONFIGURATION`；`+`表示该slot至少一个member，`?`表示零个或多个。每条Rule输出恰有一个`CANONICAL_TYPED_OUTPUT` Envelope；其closed consumer type和有名member投影由`ExactConsumerRuleInputContractRef`绑定，不能产生表外第二输出。

| Pack Rule | Required slots | Optional slots |
|---|---|---|
| `BUILD-DECLARATION-ROLE@1` | `P+` | `F? C? G? B?` |
| `BUILD-COMPONENT-MODULE-BINDING@1` | `P+ F+` | `C? B? R?` |
| `BUILD-DECLARATION-SET-CLOSURE@1` | `P+ F+` | `C? B?` |
| `BUILD-EFFECTIVE-VALUE@1` | `P+ F+ C+` | `G? B? R?` |
| `BUILD-EFFECTIVE-DEPENDENCY-RESOLUTION@1` | `P+ F+ C+` | `G? B? R?` |
| `JAVA-TYPED-EXPRESSION@1` | `P+` | `F? C? G? R?` |
| `JAVA-CONTROL-FLOW@1` | `P+` | `F? C? G? R?` |
| `JAVA-CALL-BINDING@1` | `P+ F+` | `C? G? R?` |
| `JAVA-DATA-FLOW@1` | `P+` | `F? C? G? R?` |
| `JAVA-STATE-EFFECT@1` | `P+` | `F? C? G? R?` |
| `JAVA-EXCEPTION-FLOW@1` | `P+` | `F? C? G? R?` |
| `JAVA-NULL-DEREFERENCE@1` | `P+ F+` | `C? R?` |
| `JAVA-SEMANTIC-COMPARISON@1` | `P+ F+ C+` | `B? R?` |
| `JLIB-STRING-SEQUENCE@1`、`JLIB-NUMERIC-CONVERSION@1`、`JLIB-BIGDECIMAL@1`、`JLIB-DATE-TIME@1`、`JLIB-COLLECTION-PIPELINE@1`、`JLIB-ORDERED-MAP@1`、`JLIB-BOUNDED-RANDOM@1` | `P+ F+` | `C? G? R?` |
| `SPRING-TRANSACTION-APPLICATION@1`、`SPRING-ROLLBACK-DEFAULT@1`、`SPRING-TRANSACTION-GUARANTEE@1`、`SPRING-EXCEPTION-HANDLER@1` | `P+ F+ C+` | `G? B? R?` |
| `QUERY-TYPED-AST@1` | `P+` | `F? C? G? R?` |
| `QUERY-MAPPER-BINDING@1` | `P+ F+` | `C? G? R?` |
| `QUERY-PREDICATE-SEMANTICS@1`、`QUERY-UPDATE-SEMANTICS@1`、`QUERY-CONSTRAINT-SEMANTICS@1` | `P+ F+` | `C? G? R?` |
| `QUERY-DECLARATION-SET-CLOSURE@1` | `P+ F+` | `C? B?` |
| `EXTERNAL-API-SEMANTIC-INTERPRETATION@1` | `P+ F+ C+` | `G? B? R?` |

对每行，Rule自身Applicability/Input中列出的每一必需语义输入必须在required slot或其有名member中出现；slot表不是省略正式前提的许可。Consumer Input Contract必须逐slot给出closed type、cardinality、Authority→value projection和Context Role，并证明其映射覆盖该Rule Input表全部必需项且没有扩大类型/来源。Pack Rule Verifier先验证slot closure，再按该Rule表验证语义Applicability；缺任一项只能UNKNOWN/FAILED，不能靠Proposal文本补齐。

## 3. BUILD Rule Family

| Rule ID | Applicability / Input | Canonical Output | Unknown Boundary |
|---|---|---|---|
| `BUILD-DECLARATION-ROLE@1` | 一个完整且语法 Profile 受支持的 build declaration node | `owner, role=AGGREGATES_MODULE|IDENTIFIES_COMPONENT|MANAGES_DEPENDENCY|DECLARES_DEPENDENCY|DECLARES_PARENT|DECLARES_PROPERTY|DECLARES_PROFILE|DECLARES_ACTIVATION|DECLARES_CONFIGURATION, targetNativeKey, ordinal, versionExpressionOrLiteral?, scope?, condition?`；parent保存exact component token/version expression，property/profile/activation/configuration只保存source-declared typed key/value/predicate | profile、继承、插值、激活条件或 target identity 不能完整解释 |
| `BUILD-COMPONENT-MODULE-BINDING@1` | 已发布的 module component identity 与 dependency declaration，二者 Context 可组合 | `dependentModule, dependencyModule, bindingKeys, relation=DECLARES_DIRECT_DEPENDENCY` | component coordinate 未解析、多个 module 匹配、profile 条件未知 |
| `BUILD-DECLARATION-SET-CLOSURE@1` | 一个完整 descriptor region 或已关闭的 descriptor 集合 Coverage | exact declaration member set、role partition、cardinality、ordering | 任一 descriptor、profile 分支、分页或 selector 未闭合 |
| `BUILD-EFFECTIVE-VALUE@1` | dependency declaration与`DECLARES_PROPERTY`等literal/property/inheritance/activation正式输入全部在 exact Profile 中有依据 | normalized exact value、substitution steps、applicability conditions | 任一 property、parent、profile、environment input 或 precedence 未证明；版本范围不输出exact value |
| `BUILD-EFFECTIVE-DEPENDENCY-RESOLUTION@1` | 一个exact target module；从该module descriptor沿published parent关系到root的完整ordered effective descriptor chain；每层direct/managed dependency、parent/property/profile/activation声明及对应COMPLETE closed-set Coverage；所有候选component/version、冲突项、mediation输入及适用配置均为冻结正式前提 | `TUPLE(targetModule,ORDERED_LIST(descriptorChainChildToRoot),declaredDependency,ORDERED_LIST(candidateComponentVersions),ORDERED_LIST(conflictAndMediationDecisions),exactComponent,exactVersion,ORDERED_LIST(conditionExpressions),ORDERED_LIST(typedLimitations))`；`ProposalPublicArgumentCore`逐步绑定target、验证chain adjacency与各层closure、解析profile/activation、枚举候选/冲突并审核mediation，独立Verifier重建后才能支持使用方Schema发布`RESOLVES_EFFECTIVE_DEPENDENCY` | chain断裂、任一descriptor或selector未闭合、parent/property/profile/activation/config未知、候选/冲突/mediation集合不全、环境激活输入缺失、版本范围/多解、生成审核分歧均UNKNOWN；不要求或伪装完整Maven solver，不解释plugin执行 |

`BUILD-DECLARATION-ROLE@1`的role-target kind固定为：`AGGREGATES_MODULE→MODULE`，`IDENTIFIES_COMPONENT|MANAGES_DEPENDENCY|DECLARES_DEPENDENCY|DECLARES_PARENT→COMPONENT`，`DECLARES_PROPERTY→PROPERTY`，`DECLARES_PROFILE→PROFILE`，`DECLARES_ACTIVATION→ACTIVATION`，`DECLARES_CONFIGURATION→CONFIGURATION`；未知或错配kind必须UNKNOWN/FAILED，不能输出MODULE|COMPONENT宽联合。

该Rule全部输出字段使用closed codec：`targetModule=EntityRef(software-module)`；`DescriptorChainMember=TUPLE(UINT64(depthFromTarget),EntityRef(software-module),source-node-ref(descriptor),ABSENT|PRESENT(EntityRef(software-module) parent))`；`DeclaredDependency=TUPLE(EntityRef(software-module) owner,source-node-ref(descriptor),EntityRef(dependency-component),DIRECT|MANAGED,UINT64(sourceOrdinal),TypedLiteral|expression(version),ABSENT|PRESENT(expression condition))`；`DependencyCandidateCore=TUPLE(ENUM(DEPENDENCY_CANDIDATE_CORE),EntityRef(dependency-component),TypedLiteral(exactVersion),source-node-ref(descriptor),DIRECT|MANAGED,UINT64(depthFromTarget),UINT64(sourceOrdinal),ABSENT|PRESENT(expression condition))`；`DependencyCandidateDigest=DIGEST(DependencyCandidateCore)`；`DependencyCandidate=TUPLE(ENUM(DEPENDENCY_CANDIDATE),DependencyCandidateCore,DependencyCandidateDigest)`；`MediationInputsCore=TUPLE(ENUM(MEDIATION_INPUTS_CORE),EntityRef(dependency-component),ORDERED_LIST(DependencyCandidate),ruleApplicationInputManifest)`；`MediationInputsDigest=DIGEST(MediationInputsCore)`；`MediationInputs=TUPLE(ENUM(MEDIATION_INPUTS),MediationInputsCore,MediationInputsDigest)`；`MediationDecision=TUPLE(EntityRef(dependency-component),ORDERED_LIST(DependencyCandidateDigest),DependencyCandidateDigest selectedCandidate,DIRECT_DECLARATION|MANAGED_OVERRIDE|NEAREST_CHAIN_MEMBER|PROFILE_ACTIVATED,MediationInputs)`；`exactComponent=EntityRef(dependency-component)`；`exactVersion=TypedLiteral(non-empty exact version string,not range)`；`conditionExpressions=ORDERED_LIST(expression)`；`typedLimitations=ORDERED_LIST(TypedLimitation)`。MediationInputs中的Manifest必须逐字等于外层Canonical Rule Output的完整Rule Application Input Manifest，且Candidate Envelope列表必须与该component的完整candidate projection逐字相等；condition、configuration、profile和activation输入只能从该Manifest的有名typed input解析。Coverage/Formal refs留在consumer的公开Argument Core。chain按depth从0连续；candidate按Core中的component、depth、source ordinal规范排序；每个decision的候选Digest集合必须与MediationInputs及该component的完整`DependencyCandidate` projection双向相等，selected必须恰好等于集合中一个已重算的`DependencyCandidateDigest`。Core不含自身Digest或MediationDecision，Envelope不得新增字段。任何未知variant、map/text、字段类型宽化、Digest/preimage不一致或同步删除candidate/decision均失败关闭。

`BUILD-EFFECTIVE-VALUE@1`只规范化一个已闭合声明表达式的scalar value；它不执行dependency candidate collection、conflict mediation或effective model resolution，不能单独或与source literal拼接后支持`RESOLVES_EFFECTIVE_DEPENDENCY`。该正式关系只能由`BUILD-EFFECTIVE-DEPENDENCY-RESOLUTION@1`的完整typed output与独立审核支持。

该 Family 不实现或假装完整Maven、Gradle solver。Syntax Profile可以注册具体build language；`MODEL_REVIEWED` resolution在冻结输入闭包内做通用有界调查并失败关闭，正式Knowledge Type仍使用通用build declaration role。

## 4. JAVA_LANGUAGE Rule Family

| Rule ID | Applicability / Input | Canonical Output | Unknown Boundary |
|---|---|---|---|
| `JAVA-TYPED-EXPRESSION@1` | 完整 Java expression node、语言级别和可解析类型输入 | typed expression tree、operator、ordered operands、result type、conversion steps | overload、generic inference、constant、dynamic type 或 language level 未解析 |
| `JAVA-CONTROL-FLOW@1` | 完整 executable declaration body | entry/exit、typed control edges、guards、lexical order、reachable node domain | body 不完整、unsupported syntax、dynamic generated code 或 finally semantics 未闭合 |
| `JAVA-CALL-BINDING@1` | 完整 invocation/new node、receiver/type/import/overload 输入 | invocation kind、exact or bounded callee signature、receiver、ordered arguments、result type | dynamic dispatch 目标需要运行时信息；overload 或 symbol 多义 |
| `JAVA-DATA-FLOW@1` | 完整 assignment、argument、return、lambda 或 collection transform node | source expression、target location、flow kind、guard、program point | alias、reflection、capture 或 interprocedural input 未正式提供 |
| `JAVA-STATE-EFFECT@1` | 完整 write/create/update-like source node | effect kind、target location/operation、value bindings、guard | 隐含 framework side effect、callee effect 或 target identity 未证明 |
| `JAVA-EXCEPTION-FLOW@1` | throw/catch/declaration/call node 和已知 API exception contract | explicit/implicit exception event、type、handler/propagation target、guard | unchecked library behavior、reflection、framework interception或 catch domain 未闭合 |
| `JAVA-NULL-DEREFERENCE@1` | nullable receiver/value、dereference node 和 path guard | exceptional outcome `NullPointerException` 及成立条件 | nullability 或 guard relation 不可证明 |
| `JAVA-SEMANTIC-COMPARISON@1` | BEFORE/AFTER 的 typed source observations与 exact change Context | symbol/node mapping、aspect、change kind、typed before/after delta | node correspondence、多义 rename、generated source 或任一侧 Coverage 不完整 |

Java Rule 只解释源码声明的程序语义，不把静态可达路径表达为一次真实执行，也不把任意调用名称当作副作用。

## 5. JAVA_LIBRARY Rule Family

| Rule ID | Applicability / Input | Canonical Output | Unknown Boundary |
|---|---|---|---|
| `JLIB-STRING-SEQUENCE@1` | exact JDK API signature、receiver/argument type 与字符序列操作 | slice、length、padding、concat 等规范表达式和边界异常 | charset、code-point/code-unit、index 或 API 版本不明 |
| `JLIB-NUMERIC-CONVERSION@1` | Java primitive/wrapper/BigDecimal conversion API 与 exact type | truncation、overflow/precision、null unboxing 与 result type | source type、scale、overflow policy 或 overload 未知 |
| `JLIB-BIGDECIMAL@1` | exact BigDecimal operation、operands、scale 与显式/规则定义 rounding | decimal expression、scale、rounding、exception precondition | MathContext、scale、rounding 或 operand provenance 未知 |
| `JLIB-DATE-TIME@1` | exact Date/Instant API signature、typed operands 和时区/epoch前提 | strict comparison、epoch conversion、duration arithmetic | timezone、clock、unit、nullability 或 API profile 未知 |
| `JLIB-COLLECTION-PIPELINE@1` | exact collection/stream operation chain、lambda 和 encounter order输入 | filter/map/group/reduce/sort pipeline、membership 与 order preservation | source order、parallelism、comparator、equality/hash semantics 未知 |
| `JLIB-ORDERED-MAP@1` | exact ordered-map type、comparator/profile 和 insertion/input facts | key ordering、iteration ordering、value group behavior | comparator、null-key policy 或具体 implementation 未证明 |
| `JLIB-BOUNDED-RANDOM@1` | exact bounded-random API call 与 bound expression | result domain和digit/interval property；不产生具体随机值 | PRNG/API、bound、distribution 或 call signature 未知 |

Library Rule 必须绑定 exact API signature 和版本化 Profile。没有注册的第三方库默认行为保持 `UNKNOWN`；旧注释、方法名或常见用法不能补足。

## 6. SPRING_TRANSACTION Rule Family

| Rule ID | Applicability / Input | Canonical Output | Unknown Boundary |
|---|---|---|---|
| `SPRING-TRANSACTION-APPLICATION@1` | annotation application、method visibility/call boundary、proxy/configuration正式输入 | transaction boundary、propagation、applicability conditions | self invocation、proxy mode、activation、manager selection 或配置未知 |
| `SPRING-ROLLBACK-DEFAULT@1` | applicable transaction boundary、exception type/propagation facts 与 exact framework profile | rollback/commit condition和限制 | exception 被捕获、转换、rollbackFor/noRollbackFor 或 profile 未闭合 |
| `SPRING-TRANSACTION-GUARANTEE@1` | transaction boundary、ordered state effects、query/update语义与 schema constraints | atomicity、isolation/race-exclusion/uniqueness 各维度独立 assessment | database isolation、lock、conditional update、constraint 或 deployment config 未证明 |
| `SPRING-EXCEPTION-HANDLER@1` | exact handler annotations、exception type hierarchy、method mapping事实 | handler selection、response outcome与 precedence条件 | advice activation、order、inheritance 或 response conversion 未证明 |

`SPRING-TRANSACTION-GUARANTEE@1` 禁止由“存在事务”推出并发安全。原子提交、隔离、丢失更新防护、超卖防护和唯一性必须分别判断。

## 7. QUERY_MAPPING Rule Family

| Rule ID | Applicability / Input | Canonical Output | Unknown Boundary |
|---|---|---|---|
| `QUERY-TYPED-AST@1` | 完整且 dialect/profile 受支持的 query statement | scan/filter/join/project/group/aggregate/sort/limit/set-op typed tree | dynamic SQL 分支、dialect、placeholder type 或 statement region 未闭合 |
| `QUERY-MAPPER-BINDING@1` | mapper declaration、query operation、parameter/result mapping完整输入 | mapper operation↔query operation、parameter slots、result shape | namespace、overload、dynamic provider、result map 或 generated mapping 多义 |
| `QUERY-PREDICATE-SEMANTICS@1` | typed query AST、parameter binding、null/dialect profile | normalized predicate、three-valued/null semantics与 result range | collation、timezone、implicit cast 或 dialect behavior 未证明 |
| `QUERY-UPDATE-SEMANTICS@1` | UPDATE/INSERT/DELETE AST、predicate和bindings | affected relation/field、value expression、atomic statement boundary、guard | trigger、stored procedure、isolation、affected-row condition 或 runtime schema 未知 |
| `QUERY-CONSTRAINT-SEMANTICS@1` | repository-declared DDL/schema/annotation constraint node | relation、constraint type、field set、predicate、declaration scope | runtime DB drift、migration order、environment selection 或 incomplete schema source set |
| `QUERY-DECLARATION-SET-CLOSURE@1` | exact selector 下所有受支持 schema/query declaration region 及 COMPLETE Coverage | exact member set、cardinality、kind partition | selector、file family、dynamic SQL、pagination 或 parser Coverage 未闭合 |

Repository query/schema Rule 只表达 Git 中声明的查询与结构。它不观察实际数据库对象、数据行、锁、隔离级别或触发器状态。

## 8. 跨 Family 组合与确定性边界

### 8.1 External API Semantic Interpretation

| Rule ID | Execution Class | 必需正式输入 | Canonical typed output | Unknown Boundary |
|---|---|---|---|---|
| `EXTERNAL-API-SEMANTIC-INTERPRETATION@1` | `MODEL_REVIEWED` | component basis二选一：已发布由`BUILD-EFFECTIVE-DEPENDENCY-RESOLUTION@1`支持的`RESOLVES_EFFECTIVE_DEPENDENCY`唯一给出source owner module与exact component/version；或Catalog已支持Framework exact Profile + owner module完整effective descriptor chain(child→root→exact supported parent) + 链上全部override/property/dependency/profile/activation/config closed-set closure；`BUILD-EFFECTIVE-VALUE@1`、source declaration/property/parent Fact单独均不充分。另需已发布program-call Fact中的exact source type/import/call token及相关正式type/data/control Fact、目标Inference Type Contract | `componentBasis, resolvedCallBinding, semanticOperationSet, dataFlowSet, stateEffectSet, exceptionalOutcomeSet, preconditionSet, limitationSet`；Call Binding含exact component/type/descriptor；Framework替代路径必须带component-version未独立解析的typed limitation；每个语义成员必须是使用方Schema的closed tagged term，并在`ProposalPublicArgumentCore`中有独立Member Assurance，保存supporting Formal Reference set、公开Argument step set、Context Role和typed limitation set | effective resolution缺失/版本范围、Framework owner/descriptor chain/parent predicate或链上任一build/config closure不完整、resolved Call Binding无法从正式前提唯一重建、signature/dispatch多义、实例配置/运行状态缺失、typed output无法表达、生成/审核分歧、任一审核义务未通过 |

该 Rule 不注册任何第三方组件的默认配置、运行状态或动态binding，也不允许 Pack、Prompt或模型记忆充当正式前提。它允许模型在 exact、已发布的软件事实边界内提出开放式语义解释；公开Argument第一步必须解析resolvedCallBinding，独立Review先从正式component/version和source type/import/call token重建该binding，再按每个Conclusion member逐项核对typed语义、Argument、Context、反例和限制，并提交`REVIEW_ASSERTS_PASS|REVIEW_ASSERTS_UNKNOWN|REVIEW_ASSERTS_DISAGREE`；Review执行失败进入FAILED无语义分支。只有binding与所有成员均获`REVIEW_ASSERTS_PASS`，且独立Rule Verifier重放完整Semantic Result/Execution Proof并签发`RULE_VERIFICATION_PASS`，才可以继续进入使用方Inference Admission；其余结果保持Unknown或删除整个replacement Proposal，不能保留部分肯定语义。该规则不能支持Direct Fact或Evidence。

Generation、Review与Rule Verifier的Attempt/Strategy必须相互分离：Generation与Review分别形成§2.3的完整`ModelProposalSemanticOutput` Envelope，Review绑定目标Generation Digest及逐字相同的`InterpretedSemanticResult`与其中的`ProposalPublicArgument` Envelope；Rule Verifier随后按冻结Catalog职责独立重放。PRODUCTION与CAPABILITY_EVALUATION的Generation/Review必须分别取得不同Attempt/Strategy/Model Call的`EligibleModelProposalBinding`，actual model、Provider/Adapter/configuration、Prompt、Authorized Input Manifest、Request、`NO_EXTERNAL_ACCESS` Receipt、Catalog/Qualification与Response/Proposal Digest均由Eligibility权威记录闭合；CAPABILITY_VALIDATION只能保存各自exact Fixture ref/digest并标记`MODEL_ELIGIBILITY_NOT_APPLICABLE`。三者不得复用同一职责身份，Generation/Review另不得复用同一会话、Fixture、隐藏上下文、缓存判断、Eligibility证明或自审结果。Proposal Argument Core只保存正式前提到typed Conclusion的有名语义步骤、适用规则、反例检查和限制，不保存私有思维链或任何后置执行/准入/发布Provenance。

### 8.2 组合规则

1. Family 输出只能通过使用方 Schema 注册的 Fact Direct Observation、Inference Type Rule 或 Verification Profile 消费；不能按字段相似自动连接。
2. BUILD 可以为语言/API Profile 提供正式版本输入；JAVA_LANGUAGE 可以为 JAVA_LIBRARY 调用提供 typed call；QUERY_MAPPING 可以为 JAVA state-effect/behavior 提供 query operation语义；SPRING_TRANSACTION 可以消费已发布 annotation、exception、state-effect和query知识。
3. 任一跨 Family 组合都必须公开每个输入、Rule Reference、Context Role、步骤和输出限制。需要正式软件语义的输入必须进入 Inference direct premise closure。
4. Pack 内 Rule dependency graph 必须有界无环；`UNKNOWN` 不参与普通肯定结论的继续推导。
5. 确定性图算法、集合差分、typed counterexample evaluation及其他只消费已发布Formal Knowledge的分析，可以由使用方以`CONSUMER_LOCAL_RULE_REF`注册；必须具备完整Local Rule Definition Record、exact Definition/Rule Digest和本Pack全部执行/验证闭包，且不得扩张本 Pack 未解释的语言/API语义。
6. `MODEL_REVIEWED` 规则允许模型主导开放式推理，但不能把模型输出、Confidence或Capability Evaluation结果当作正式前提；正式前提、typed Conclusion、Context、独立审核、Admission和Publication边界保持不变。

## 9. Canonicalization 与 Digest

`SWM-FOUNDATIONAL-SEMANTICS-CANONICALIZATION@1` 固定：

1. Pack Rule、Family、Profile、Operator、Role 和 Enum ID 使用本文 ASCII 字面值，区分大小写；Profile Definition Record 按 §1.1 的单行加 LF 规则独立重算。Consumer-local Rule使用其冻结Definition声明的ASCII Record与canonicalization，且必须从完整Record重算Rule Definition Digest。
2. Typed input/output 使用有名 Role；不得以 JSON map 顺序或自然语言段落替代。
3. Source node/path保留 source-native bytes 与 exact Context；显示行号不参与身份。
4. Expression、Query AST 和 Rule Step 保留有序子节点；无序集合按成员 digest排序。
5. Literal 固定类型、值、单位、精度、scale、rounding 与 encoding（适用时）。
6. `ProposalPublicArgumentDigest`只覆盖其完整Core，Core逐项内联consumer-typed body且不含Eligibility、Capability Provenance、Rule Output、Candidate/Admission/Publication或其Digest；Review与Canonical Rule Output必须分别取得完整Envelope、重算Digest并逐字绑定同一Argument。`RuleOutputDigest`严格按§2.3的`CanonicalRuleOutputCore`重算；`MODEL_REVIEWED`的`APPLICABLE_INTERPRETED`另完整覆盖Generation/Review Model Proposal Envelope、Review→Generation目标绑定、各自Attempt/Capability/Strategy/Purpose，以及MODEL路径的Call、actual fingerprint、Provider/Adapter/configuration、Prompt revision/digest、Authorized Input Manifest、Provider Request、`NO_EXTERNAL_ACCESS` Isolation Receipt、Catalog/Qualification、Response/Proposal Digest和`X-MODEL-RESULT-ELIGIBILITY-01` Result/Ref/Digest，或CAPABILITY_VALIDATION路径的Fixture ref/digest与`MODEL_ELIGIBILITY_NOT_APPLICABLE`。不得只复制opaque Output、Argument、Proposal、Eligibility或Binding Digest而不提供其closed preimage。
7. 带自身校验摘要的对象严格使用§2.3的`XCore → XDigest → XEnvelope`，Digest只覆盖Core且不包含自身或Envelope。`DependencyCandidateDigest`只覆盖`DependencyCandidateCore`；MediationDecision必须取得完整`MediationInputs`及全部Candidate Envelope、重算每个Digest并与外层Rule Application Input Manifest逐字对齐后才能引用或选择。
8. Pack Digest 只按本文标记和元数据声明的 canonicalization 计算；`PACK_RULE_REF`不允许省略 Pack Digest，`CONSUMER_LOCAL_RULE_REF`不允许省略 Consumer Definition Digest、Rule Version或Rule Definition Digest。

## 10. 失败语义与 Conformance

| 失败 | 处理 |
|---|---|
| `RULE_REFERENCE_INVALID` | Canonical Rule Application形成前的Application Owner Failure；Pack Rule不存在于exact Pack，或Consumer-local Rule的Definition依赖、Record、version/digest、Profile Mode任一不可解析即失败；不得按Family或名称选择近似Rule，也不得伪造含`ExactRuleRef`的Canonical Rule Output |
| `INPUT_TYPE_UNSUPPORTED` | NOT_APPLICABLE；输入保留为未解释观察 |
| `APPLICABILITY_UNKNOWN` | UNKNOWN；不得使用默认值或模型常识 |
| `INPUT_DIGEST_MISMATCH` | Canonical Rule Application形成前的Application Owner Failure并隔离输入；不得把不匹配Manifest伪装成Canonical Rule Output |
| `RULE_STEP_INCOMPLETE` | FAILED；不交付部分语义结果 |
| `RULE_VERIFICATION_FAILED` | FAILED；Rule Verification Decision缺失、Verifier职责/独立性不成立、Decision与外层Rule/Input/完整Interpreted Semantic Result/Execution Proof不一致，或机械重放不能得到同一结果时，不交付语义结果 |
| `MODEL_REVIEW_DISAGREEMENT` | UNKNOWN；不得保留生成方肯定结论 |
| `MODEL_CAPABILITY_NOT_AUTHORIZED` | FAILED；输出不得进入Candidate |
| `MODEL_EXECUTION_NOT_ELIGIBLE` | FAILED；Model Call、actual identity、Provider/Adapter/configuration、Prompt、Manifest、Request、`NO_EXTERNAL_ACCESS` Receipt、Catalog/Qualification或Eligibility任一缺失、过期、失配或不可解析时，暂存输出不得进入任何领域Proposal/状态 |
| `MODEL_PROPOSAL_BINDING_MISMATCH` | FAILED；Model Response、Proposal Core/Digest、Attempt/Strategy/Purpose或Eligibility Binding不能互换、借用或事后补写 |
| `MODEL_REVIEW_TARGET_MISMATCH` | FAILED；Review未绑定exact Generation Proposal Digest，或最终typed output/Argument与Generation不一致 |
| `PROPOSAL_PUBLIC_ARGUMENT_INVALID` | FAILED；consumer Contract/Definition不可解析、Argument Core/Digest错配、Review/Rule Output未绑定同一Core，或body包含Eligibility、Capability Provenance、Rule Output、Candidate/Admission/Publication及其后置Digest |
| `VALIDATION_AUTHORITY_FENCE_VIOLATION` | FAILED；CAPABILITY_VALIDATION Fixture输出离开`VALIDATION_ONLY` sink/namespace、切换或别名production CURRENT，或成为PRODUCTION premise/input/basis/continuation/root-state复用来源 |
| `PROFILE_VERSION_UNRESOLVED` | UNKNOWN；不能选择“常见版本” |
| `PROFILE_DEFINITION_DIGEST_MISMATCH` | Canonical Rule Application形成前的Application Owner Failure；不能使用同名本机Profile或其他Catalog项，也不得构造Canonical Rule Output |
| `RESOURCE_LIMIT` | FAILED；不截断后宣称完整 |
| `TOPIC_SPECIFIC_RULE_DETECTED` | Pack Conformance FAIL |

Conformance 至少覆盖：每个 `MECHANICAL` Rule 的一个正例、一个 NOT_APPLICABLE、一个 UNKNOWN、完整`MechanicalRuleExecutionManifest Core/Digest/Envelope`与Proposal Step逐步重放、顺序/无序规范化、边界异常和跨 Family 隐藏输入反例；只给Manifest Digest、Input或Semantic Result前像缺失、Proposal Step ordinal断裂或typed codec错配必须失败。逐一验证§2.2六个合法Outcome，并拒绝其余Applicability/Result组合、UNKNOWN/FAILED携带semantic payload以及Core/Digest/Envelope缺失或错配。`MODEL_REVIEWED` Rule还覆盖typed codec、正式前提闭包、独立Attempt/Strategy/Model Call、Review→Generation Digest绑定、两阶段Digest重放、审核分歧和Unknown失败关闭。每个`CONSUMER_LOCAL_RULE_REF`还必须解析exact Consumer Definition、确认其直接依赖本Pack、重算完整Local Rule Definition Record Digest、校验`FORMAL_KNOWLEDGE_ONLY + EMPTY Profile List`、Execution Class、typed input/output与Step Contract；裸ID、Record缺字段、Definition/Rule digest错配、Source Observation输入或本地扩张语言/API语义均失败关闭。每个consumer Argument Contract必须重算Definition Digest并逐字段解码完整`ProposalPublicArgument`，验证Generation、Review、Canonical Rule Output中的Envelope逐字相等及拓扑单向；向body注入Eligibility、Capability Provenance、ModelReviewedExecutionClosure、RuleOutputDigest、ExactRuleApplicationResultRef、Candidate/SelfToken、Admission/Publication或这些对象的Digest必须失败。MODEL路径必须逐项验证actual model、Provider/Adapter/configuration、Prompt revision/digest、Authorized Input Manifest、Provider Request digest、dispatch前`NO_EXTERNAL_ACCESS` Isolation Receipt及其有效Conformance、Catalog/Qualification、Model Response/Proposal Digest和`X-MODEL-RESULT-ELIGIBILITY-01` Ref/Result/Digest；缺字段、旧Receipt/资格、隐藏上下文或任一Tool能力、Generation/Review Call互换、Eligibility互换、Proposal/Argument Digest互换、Review指向另一Generation、合格Call绑定替换Proposal及final Rule Output篡改均必须失败关闭。所有`APPLICABLE_INTERPRETED`正例还必须重算`InterpretedSemanticResult`与`RuleVerificationDecision`各Core/Digest/Envelope，逐字核对Generation、Review、Mechanical Manifest、Decision与外层中的完整Semantic Result Envelope，以及Rule、Input和Execution Proof；移植或篡改任一Semantic Result/Attempt/Proof/Decision、在Proposal之外补写assumption/limitation/counterexample/context，或Verifier与Generation、Review、Driver、Fixture或MECHANICAL executor的任一Attempt/Capability/Strategy相等或别名，均必须失败。CAPABILITY_VALIDATION另验证独立Generation/Review Fixture只经公共Proposal Port、Eligibility固定`MODEL_ELIGIBILITY_NOT_APPLICABLE`；Review Fixture可以提交`REVIEW_ASSERTS_PASS`，但Fixture不能携带或伪造MODEL Eligibility，也不能签发`RULE_VERIFICATION_PASS`、Knowledge Obligation PASS或Admission Decision；还必须证明validation namespace与production CURRENT不可相等/别名/切换，validation Formal State不能被PRODUCTION Premise/Input/Basis/Continuation或Root/State resolution消费。Fixture数据可以固定验证输入；Driver、Rule、Selector、Verifier和实现分支不得按scenario ID、claim、问题、repository/class/path专名、commit或黄金值改变语义，也不得包含Catalog之外的题目专用组件分支或业务答案。

所有Rule另须先逐字段重算`RuleApplicationRequest Core/Digest/Envelope → ApplicabilityInput Core/Digest → RuleApplicationInputManifest Core/Digest/Envelope`：Input ordinal连续，Role/kind/Authority/Context/typed bytes/digest双向一致，Profile variant与Rule Ref variant相容，Boundary/Scope/Schema/Context不被换写，Applicability投影无missing/extra，Idempotency Key只绑定同一Request Digest。只给Manifest Digest、Core/Envelope错配、Authority前像不可解析、Context或typed input digest借用、Profile variant互换、投影同步删项或在Proposal/Execution Proof/Decision/Canonical Output间替换Manifest均失败关闭。

`BUILD-EFFECTIVE-DEPENDENCY-RESOLUTION@1`还必须覆盖child→root descriptor chain、direct/managed candidate、property/profile/activation、冲突/mediation closure的正例，并逐项重算`DependencyCandidateCore → DependencyCandidateDigest → DependencyCandidate Envelope → MediationInputsCore/Digest/Envelope → MediationDecision`；MediationInputs中的完整Rule Application Input Manifest与外层不一致、Core内放入自身Digest、Envelope/Core字段错配、selected Digest无对应Envelope、chain中间层缺失、同步删除candidate与conflict记录、环境激活未知、版本范围和用`BUILD-EFFECTIVE-VALUE@1`冒充resolution均失败关闭。Conformance不得以嵌入完整Maven solver作为本Rule成立前提。

BUILD Conformance另须逐项覆盖九种declaration role-target kind映射，任一MODULE/COMPONENT宽联合或PROPERTY/PROFILE/ACTIVATION/CONFIGURATION错配均失败关闭。

架构能力Demo可以用deterministic Contract Driver与独立Review Fixture经各自公共Proposal Port提交冻结Proposal以排除模型概率；两者都必须形成§2.3的Fixture Binding并明确`MODEL_ELIGIBILITY_NOT_APPLICABLE`，不得伪造一次MODEL Call或Eligibility。Demo必须在同一Run先经公共Source/Observation → Artifact/Evidence → Fact Verification/Admission/Publication，关闭来源调查上下文并从新Snapshot正式重读后，再经公共Rule Application / Candidate Proposal → Review Proposal → Rule Verification → Knowledge Verification/Admission/Publication；Fixture参与的整个后半链只能落入Application Authority预签的`VALIDATION_ONLY` sink/Snapshot namespace，使用独立validation Current或可见性指针且永不读取、覆盖、别名或切换production CURRENT。Review Fixture可以提交非权威`REVIEW_ASSERTS_PASS`；Driver/Fixture不能调用私有Rule实现缝隙、直接写Artifact/Evidence/Fact/Candidate、签发`RULE_VERIFICATION_PASS`、Knowledge Obligation PASS或Admission Decision、写Snapshot/CURRENT、伪造Verifier结果或把Source payload带入Answer。真实Gate也不得把validation State暴露给production Reader或用作PRODUCTION premise、input、basis、continuation及Root/State复用来源。私有seam测试最多证明局部机制，不能作为本Pack或整体方案能力通过证据；只有完整公开端口Demo运行才能验证该边界内的方案能力，且其结果不证明产品完成或真实模型可靠性。

## 11. 明确排除项

- 不包含题目、业务对象、具体仓库、提交、方法或黄金答案专用 Rule。
- 不注册默认第三方库行为；缺少 exact Profile 时保持 Unknown。
- 不包含Prompt正文、特定模型、Confidence阈值、答案模板或黄金值；只定义MODEL_REVIEWED的通用Assurance义务。
- 不产生 Runtime Fact，不声称数据库、事务代理或请求已真实运行。
- 不允许 Artifact / Evidence 直接成为正式 Inference 前提。
- 不允许自由文本 output 补写 typed output 未表达的语义。
- 不改变 Architecture、Accepted DD、Provider授权、Knowledge Admission 或 Snapshot发布边界。

<!-- END FOUNDATIONAL SOFTWARE SEMANTICS RULE PACK PAYLOAD -->

## 12. 验证状态

本文只形成 Proposed Rule Pack。Pack Digest、静态闭包和 Conformance Fixture 完成不等于任何 Knowledge Schema 的 33 项能力映射已经通过独立复核。静态 33/33 最多证明设计容量候选；只有完整 Architecture Capability Validation 才能证明方案具备该能力，真实模型可靠性另由 Capability Evaluation 判定。
