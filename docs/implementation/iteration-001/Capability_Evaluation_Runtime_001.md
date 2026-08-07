# Iteration 001 Capability Evaluation Runtime 001

| 元数据 | 值 |
|---|---|
| Record ID | `SWM-IMP-CE-RUNTIME-001` |
| Date | 2026-08-06 |
| Status | `GENERIC RUNNER AND SIX-ROLE DEFINITION IMPLEMENTED / JWT CE PASS / ACTIVATION NOT RUN` |
| Contract | `MGT-CAPABILITY-EVALUATION-01`、`MGT-EVALUATION-RUN-01`、`MGT-EVALUATION-VALIDITY-01` |
| Next Gate | `Product holdout, then explicit scoped activation decision` |

## 1. 已实现闭环

生产模块现已实现以下通用机制：

- 版本化`EvaluationDefinition`固定Capability / Strategy、实现摘要、Live CC Result、配置指纹、Model / Adapter、Prompt、Output Schema、Tool Policy、数据源Revision、环境、参考Strategy、资源政策、指标、Threshold、Case Fixture和独立Oracle。
- `EvaluationRun`使用`PREPARED → RUNNING → COMPLETED | FAILED | OUTCOME_PENDING`状态；每个物理Case Attempt使用稳定Attempt Key与Request Digest。
- `OUTCOME_UNKNOWN`不会被写成失败、零Usage或PASS；只有原Attempt解析后才恢复Run。
- Case只保存隔离Evaluation Sink中的Output / Manifest Reference与Digest，不写正式知识、Candidate、Answer或生产缓存。
- 只有全部必需Case都有可裁决结果时才能在同一SQLite事务封存不可变Result、初始`VALID`Validity和Run的`COMPLETED`状态。
- Result结论为`PASS | FAIL | INCONCLUSIVE`；只有PASS创建`CAPABILITY_EVALUATION` Qualification Proof。
- Validity只允许`VALID → STALE | REVOKED`和`STALE → REVOKED`，不能恢复为VALID；过期或最新Revision不匹配时资格失败关闭。
- 模型方案仍默认禁止启用。即使显式打开真实集成开关，也必须由当前能力评估存储验证通过证明，并核对评估时的实现指纹、接口符合性结果、配置指纹、实际模型和适配器版本；确定性测试证明、旧有效性版本、同名旧实现或手写引用均不能代替。
- 通用评估执行器按冻结用例生成稳定执行身份；成功结果可恢复，语义不通过会封存为不通过，确定性契约错误会停止，外部结果未知则保持待解析且绝不暗中重发。

## 2. 代码命名含义

| 名称 | 含义 |
|---|---|
| `CE` | Capability Evaluation，判断exact Strategy是否达到某个Capability门槛。 |
| `EvaluationDefinition` | 评测前冻结的完整配置；不是某次执行结果。 |
| `EvaluationRun` | 一次可恢复的评测运行及其状态。 |
| `CaseAttempt` | 一个Case的一次物理分派；重试必须用新Attempt，Outcome未知只能解析原Attempt。 |
| `EvaluationResult` | Run闭合后不可变的语义结论与证据摘要。 |
| `Validity` | Result当前能否用于新激活；它可以单调失效，但不改写旧Result。 |
| `QualificationProof` | 把PASS Result、最新Validity、Capability和Strategy绑定起来的资格证明。 |
| `EVALUATION_ONLY` | 只允许输出进入Run专属隔离Sink，不允许生产交付。 |
| `CAPABILITY_EVALUATION` | PASS后用于Strategy Activation重验的证明类型。 |
| `OUTCOME_PENDING` | 至少一个已分派外部调用结果尚无法证明，不能封存结论。 |
| `Oracle` | 在被测World运行之前独立冻结的Direct答案与命题集合；World Runtime不能读取正文。它不是自动正确的真理，仍由不同模型来源的Evaluator结合源码复核。 |
| `Review Attestation` | 不同模型来源Evaluator形成的闭合逐Obligation评审声明；本地比较器复验字段、Digest绑定和生成器/Evaluator来源不同。 |

## 3. 已验证行为

离线自动化测试覆盖：

- Definition与已注册Model Strategy / Implementation Digest逐字绑定；
- Live Adapter Conformance在Definition注册、Run准备和Result封存三个边界重验；
- PASS签发资格并允许显式激活；FAIL和INCONCLUSIVE不签发；
- 未知Outcome阻止Result，原Attempt解析后恢复；
- Validity失效后历史Proof立即拒绝；
- 定义、Result、Validity和Evaluation-only Proof摘要重算；
- 当前通用方案的六类职责必须全部包含必测用例，缺少任何一类都不能形成整体评估定义；
- 每项用例结果必须绑定预先封存的参考答案、完整模型用量和不同来源的独立评审，篡改或同源自评不能进入评估结果；
- 启动时实现、接口符合性结果、配置、模型或适配器任一变化，历史资格立即拒绝。

## 4. 当前真实JWT CE证据

当前已在任何SWM Source Operation前冻结：

1. 同题Direct Agent独立结果和逐Claim双向Oracle；
2. JWT六Need、全部Criterion Obligation、Joint Constraint和七角色Authorized Input Matrix；
3. exact Prompt / Schema / Tool / Budget、方舟CC PASS Result和完整Run Manifest；
4. 与Oracle物理、逻辑隔离的SWM执行与Review路径；最终World结果已`PASS / DELIVERED`。

Direct与World答案均由`VOLCENGINE_ARK / glm-5.2`生成；Codex以`OPENAI_CODEX`来源独立重读冻结源码并对21项`obligation_id`出具Review Attestation。本地比较器不调用外部模型，最终Comparison `jwtcmp_3218ad611ea24c98b1930b92d0cd5f0a`为PASS：20项等价、1项World更好，Direct 9 / World 10，missing / extra / duplicate / structural mismatch均为0。

CE Authority已登记`evaluation_run_094afa178f7e4a17916d6ecdaf0d2e72`，结论PASS并签发`CAPABILITY_EVALUATION`。登记时Validity为`VALID`，有效至`2026-08-07 00:00:33.396562 +08:00`。前两轮比较和CE FAIL继续保留，不签发Qualification。

仍未执行的是面向当前生产实现的新产品Holdout和真实Activation。历史`PV-HOLDOUT-001`已于2026-08-02执行并以33.75 / 50失败；H-01至H-05已用于诊断，不再是未见集，只能做回归。新的G-12必须另行冻结未参与当前调试的工程和任务。CE过期、实现/配置Digest变化或CC失效后必须重验，不能用历史PASS绕过。

## 5. JWT评测桥接

验证层现已把私有Direct Oracle、Sanitized Run Configuration、七角色World Model Result和Post-delivery跨模型Obligation Comparison接入本通用CE状态机。比较PASS时登记一个`CE-JWT-CLAIM-CONSERVATION-001` Case；Provider Request、完整Usage、Oracle / Sink / Output摘要进入Evidence。Review本身不是Provider调用，因此Reviewer Token Usage不适用，也不伪造为零。CE有效期严格短于其Ark CC资格有效期。

PASS Registration可以由独立命令加载为`CAPABILITY_EVALUATION` Proof；激活时还会从SQLite重读Evaluation Definition，并核对当前Harness Implementation Digest与Run Configuration Digest。开发、World Run、Comparison和CE登记均不会自动激活。当前`production_activation=NOT_RUN`。完整顺序和命名见[JWT Capability Run Harness 001](JWT_Capability_Run_Harness_001.md)。

## 6. 当前通用方案评估准备

生产代码已经具备用于当前通用方案的评估定义工厂、六类职责覆盖检查、可恢复评估执行器和独立评审证据转换。六类职责分别是：需求保真、来源调查、事实依据、证据充分性、答案来源闭合、答案语义复核。需求与事实中的生成和复核仍使用分开的模型调用，因此六类职责合计绑定八套提示词和八套封闭输出结构。

这表示评估机制已经可以接收真实、已封存的用例结果，但不表示真实评估已经运行。下一步必须先冻结用例材料和参考答案，再执行模型调用并由不同来源逐项复核；只有六类必测用例全部通过，才能签发当前通用方案的能力资格。随后还必须执行新的未见项目产品对照。产品对照逐任务要求：直接回答与本系统回答使用同一实际模型，评审来源不同于两侧生成路径，且任何一个任务的正确性或完成度都不能低于直接回答，不能用其他任务的高分抵消。
