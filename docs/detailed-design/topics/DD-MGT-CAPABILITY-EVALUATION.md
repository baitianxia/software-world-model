# Capability Evaluation 与 Strategy Activation 详细设计

| 元数据 | 值 |
|---|---|
| Document ID | DD-MGT-CAPABILITY-EVALUATION |
| Version | 0.1.0 |
| Status | Accepted |
| Document Steward | Application Services / Management |
| Architecture Baseline | SWM-ARCH@1.2 |
| Depends On | DD-X-CAPABILITY-EXECUTION@0.1.0、DD-AI-MODEL-GATEWAY@0.1.0 |
| Owns Contracts | MGT-CAPABILITY-EVALUATION-01、MGT-EVALUATION-RUN-01、MGT-EVALUATION-VALIDITY-01、MGT-STRATEGY-ACTIVATION-01、MGT-STRATEGY-RESOLUTION-01 |
| Supersedes | `Software_World_Model_MVP_Detailed_Design.md` 中 DD-00B 的评测与激活部分 |
| Rationale ADR | AD-087、AD-088、AD-100、AD-110、AD-115、AD-116、AD-117、AD-131 |
| Design Validation | None |
| Conformance Cases | None |
| Capability Evaluation | None |

> 概要架构约束直接生效；本文新增的评测、有效期、激活和回退语义在状态进入 `Accepted` 前均为拟议设计。

## 1. 目的与范围

本文定义如何证明一个 Strategy 可以实现某个 Capability Contract，并由 Management 受控激活、失效和回退。它使模型、Prompt、Tool 或确定性实现可以演进，而生产路径不随 Provider 或模型变化静默漂移。

本文不生成测试题、不训练模型、不修改正式知识，也不建设独立 Evaluation & Learning Engine。未来出现系统化问题生成、失败归因和自动晋升需求时，可以把评测执行迁入该条件能力，但激活权威和本契约保持不变。

## 2. 所有权

| 对象或决定 | Owner |
|---|---|
| Capability Evaluation Contract、领域指标与 Oracle | 提供 Capability 的业务模块 |
| Evaluation Definition、Run 协调和不可变 Result | Application Services / Management |
| Strategy Activation、失效和回退记录 | Application Services / Management |
| Model Call 与实际指纹 | Model Gateway |
| 固定样例、直接调查参考与评测 Harness | 验证资产；不成为生产业务路径 |

模型或 Strategy 不能评测并激活自己。评测执行可以调用相同基础模型，但 Oracle、输入、结果和决定链必须独立。

## 3. MGT-CAPABILITY-EVALUATION-01

### 3.1 Evaluation Definition

一个版本化 Definition 至少固定：

- Evaluation ID、版本和目标 Capability Contract Version。
- 候选 Strategy Version 及所有实质配置。
- Case ID/Version、Fixture、数据源 Revision、Schema 和环境。
- Model Reference、预期/实际指纹政策、Prompt、Tool、Adapter 和参数版本。
- 独立 Oracle 或人工复核依据。
- 正确性、完整性、可追溯性、受控失败、成本和延迟指标。
- 必须比较的参考能力、通过门槛、样本分层和停止条件。
- 结果有效期和使结果失效的依赖集合。

Definition 通过结构与依赖校验后才能用于创建 Evaluation Run。创建 Run 时签发符合 X-CAPABILITY 元契约、绑定该 Run 的 `EVALUATION_ONLY Qualification Proof`：只授权 exact candidate Strategy、Case / Fixture、Model / Tool、资源、数据边界和该 Run 的隔离 Evaluation Sink 沿正常 Capability Runtime / Model Gateway 执行评测。它不要求候选 Strategy 已具有生产 Activation；所有输出不得进入正式知识、生产答案或生产 Catalog。PASS 后仍必须另行形成 Activation Decision。X-CAPABILITY 只机械验证 opaque Proof / Digest 和冻结政策，不读取本主题的 Definition / Validity Repository。

模型主导的软件调查或知识构建能力必须与直接来源调查参考能力比较；存在有效确定性参考时同时比较确定性 Strategy。直接调查参考只用于评测，不得成为生产回答旁路。

### 3.2 MGT-EVALUATION-RUN-01

每次执行使用一个可恢复的 Evaluation Run，固定 Run ID、Owner Idempotency Key、Definition / Design Baseline / 实现提交、Evaluation-only Qualification Proof、隔离 Sink、根 Allocation 和 Request Digest。状态为：

`PREPARED → RUNNING → COMPLETED | FAILED | CANCELED | OUTCOME_PENDING`

`OUTCOME_PENDING → RUNNING | COMPLETED | FAILED | CANCELED`

每个 Case 的每次物理执行形成独立 Case Attempt：

`PREPARED → DISPATCHED → SUCCEEDED | FAILED | OUTCOME_UNKNOWN`

`PREPARED → CANCELED_BEFORE_DISPATCH`

`OUTCOME_UNKNOWN → SUCCEEDED | FAILED`

- Case Attempt 固定 Case / Fixture、Strategy、实际 Model Call / Tool、输入 Manifest、隔离 Sink Partition、Dispatch Attempt Key 和 child Allocation。相同 Attempt Key 与 Request Digest 只恢复同一物理尝试；不同 Digest 复用 Key 失败关闭。
- Candidate 输出先写入该 Run 专属的隔离 Staging / Sink。生产 Repository、Artifact、Evidence、Candidate、Assessment、Application Result、Answer 和生产缓存不接受 Evaluation-only Reference；共享执行路径不表示共享输出位置。
- 已经 dispatch 且结果未知的 Attempt 保留 `OUTCOME_UNKNOWN`，Run 进入 `OUTCOME_PENDING`；恢复只能按原 Provider / Tool Request ID 解析原 Attempt，不能用同一 Attempt ID 再次执行。Provider 后续证明原调用真实结果时，以 Expected Case Attempt Revision CAS 追加不可变 Resolution Revision，把同一 Attempt 收敛为 `SUCCEEDED | FAILED`，并固定原 Request ID、Provider Outcome / Usage Reference 和 Resolution Digest；它不是一次新执行。需要新的物理尝试时创建新 Attempt 和 child Allocation。
- 取消请求以不可变 Cancel Revision / Reason 封存，只阻止尚未 dispatch 的 Attempt。已 dispatch Attempt 必须先解析为已知终态或明确 `OUTCOME_UNKNOWN`，不能把取消写成“未执行”。取消期间存在未知外部结果时 Run 保持 `OUTCOME_PENDING`；原 Attempt 全部解析后，若取消仍生效且尚未封存 Result，Run 收敛到 `CANCELED`，保留全部真实 Case Outcome / Usage，但不形成 Evaluation Result 或 Activation 依据。
- 只有全部必需 Case 已有可裁决结果，或者 Definition 明确允许把已知缺失归为 `INCONCLUSIVE` 时，Run 才能封存 Evaluation Result。尚有无法裁决的外部 Outcome 时保持 `OUTCOME_PENDING`，不签发 PASS。
- 相同 Owner Idempotency Key 与等价 Run Request 返回同一 Run；不同 Request Digest 返回 `IDEMPOTENCY_MISMATCH`。Run、Case Attempt 和 Sink Manifest 追加记录，不因重试覆盖。

隔离 Sink 的提交只在 Management 本地权威事务中把已经封存的 Case Output Reference 纳入 Run Manifest；它不把内容搬入任何生产 Sink。Run 失败或取消后，隔离内容按评测保留政策退出，不产生生产副作用。

### 3.3 Evaluation Result

Result 不可变，并记录 Run、Definition、Design Baseline、实现提交、每个 Case Attempt / Sink Manifest、指标、失败、成本、模型实际指纹和证据位置。

结论使用：

- `PASS`：全部必需门禁通过。
- `FAIL`：至少一个必需门禁不通过。
- `INCONCLUSIVE`：Oracle、样本、环境或执行不足，无法作出门禁结论。

Result 的语义结论创建后不变。只有已闭合的 Run 可以封存 Result；Run 的未知外部 Outcome 不能被缺省为失败、零用量或 PASS。Run 转为 `COMPLETED`、封存 Result 和创建 `Validity Revision = 1, VALID` 必须在同一 Management 本地事务完成，并固定当时全部依赖 Revision；因此不存在“Run 已宣称完成但没有 Result / Validity”的中间状态。运行基础设施本身失败且无法形成可裁决结果时，Run 为 `FAILED` 且不产生 Result；已知 Oracle、样本或环境不足时可以封存 `INCONCLUSIVE` Result。只有 `PASS` 且当前 Validity 为 VALID 的 Result 可以支持 Activation。评测发现正式知识错误时，修正仍进入正常 Knowledge Update，不能由评测结果直接写库。

### 3.4 MGT-EVALUATION-VALIDITY-01

Result 后续是否仍可用于新 Activation，由独立不可变 `Evaluation Validity Decision` 表达：

- `VALID`：Result 的依赖、有效期和适用边界仍满足。
- `STALE`：Contract、Strategy、模型、Adapter、Schema、Fixture、Oracle 或数据分布已实质变化。
- `REVOKED`：管理或安全决定明确禁止继续使用。

Decision 固定 Result Reference、检查的 Dependency Revision Set、Validity Revision、Reason、Authority 和 Decision Digest。初始 `VALID` 与 Result 同事务创建；其后只允许以 Expected Validity Revision CAS 追加 `VALID → STALE | REVOKED`，以及 `STALE → REVOKED`。迟到检查、依赖恢复或人工操作都不能把 STALE / REVOKED 写回 VALID；需要重新取得有效资格时必须形成新的 Evaluation Result。解析时读取该 Result 的最新 Revision，并在 Activation CAS 边界重验。

## 4. MGT-STRATEGY-ACTIVATION-01

`Strategy Activation Record` 在本契约中具体表现为以下不可变 Activation Decision Record；既有下游 `Activation Record Reference` 必须解析到某个 exact Decision / Revision，不能指向可变别名。Activation Control Key 由 `Capability Contract Version + normalized Activation Scope` 构成。每个 Key 维护单调递增的 Activation Revision；状态不通过修改 Strategy 或 Evaluation Result 表达，而由不可变 Activation Decision 派生：

- `ACTIVATE`：在当前没有可用主项时激活一个 Strategy。
- `REPLACE`：以新 Strategy 原子替换当前主项，旧 Decision 只保留历史可追溯性。
- `DEACTIVATE`：使该 Activation Scope 后续解析为无主项；不撤销同一 Evaluation Result 在其他 Scope 的资格。

每个 Decision 至少固定：

- Decision ID / Digest、Owner Idempotency Key、Expected / New Activation Revision。
- Capability Contract Version、规范化 Activation Scope 和 Decision Type。
- `ACTIVATE / REPLACE` 的 Strategy Version，以及支持它的 `PASS` Evaluation Result 与命令提交边界重验的 latest `VALID` Validity Decision。
- 生效顺序/时间、资源与数据政策。
- 可选的已批准 Fallback Activation Decision Reference；该 Decision 必须属于同一 Capability Contract 与 Activation Scope，引用自己的 `PASS + latest VALID` 依据，并由当前 Decision 显式授权为回退项。
- 决定者、理由、Request Digest 和前一 Decision Reference。

Activation Scope 只能使用 Capability Contract 声明的稳定维度，例如数据源类型、Knowledge Schema、任务风险级别或环境；不能把具体题目答案、文件路径或未声明模型特征编码为路由规则。

Decision 通过 Management 本地事务以 Expected Activation Revision CAS 追加，并同时更新该 Control Key 的 current pointer。相同 Owner Idempotency Key 与 Request Digest 返回同一 Decision；不同 Digest 复用 Key 返回 `IDEMPOTENCY_MISMATCH`。调用方在提交响应丢失后只能按原 Key 查询，不得创建一个“等价替代”Decision。`DEACTIVATE` 后没有隐式默认 Strategy；重新启用必须追加新的 `ACTIVATE`。

## 5. MGT-STRATEGY-RESOLUTION-01

Application Services 在调用 Core Capability 前：

1. 固定 Capability Contract 和 Activation Scope。
2. 以 exact Activation Revision 读取唯一 current Decision；`DEACTIVATE` 或没有 Decision 时返回 `NO_ACTIVE_STRATEGY`。
3. 对 `ACTIVATE / REPLACE` 排除 Result 为 FAIL / INCONCLUSIVE，或 latest Validity 为 STALE / REVOKED / 已过期的 Strategy。
4. 主项失效时，只有 current Decision 显式引用的 exact Fallback Activation Decision 才可作为回退，并重验其同 Scope、独立 `PASS + latest VALID` 依据；不能使用裸 Strategy Version 或任意历史激活记录。
5. 根据 exact current / fallback Decision、PASS Result 和 latest VALID Decision 签发 `PRODUCTION Qualification Proof`，冻结允许的 actual Model / Adapter Identity Policy，并将其与 Capability Catalog Snapshot、Strategy Reference 和 Execution Envelope 一起固定。
6. 将它们作为显式输入传给能力所有者。

Core Capability 和 Model Gateway 不读取 Activation Repository。运行中产生的新 Activation 不影响已冻结 Catalog。

## 6. 模型升级、滚动别名与退化

以下变化要求写入新的 `STALE` Validity Decision，并重新评测产生新 Result：

- Capability Contract、Strategy 执行图或确定性校验变化。
- 模型、Prompt、Tool、Adapter、上下文裁剪、重试、修正或重要参数变化。
- Knowledge Schema、Fixture、Oracle、门槛或数据分布发生实质变化。
- 线上 Conformance/Canary 发现隔离、质量、成本或延迟越界。

对模型引用：

- `PINNED` Model Fingerprint 可以按 Definition 的依赖和有效期复用 Evaluation。
- `OBSERVED_MUTABLE` 指纹变化后，旧 Result 的 Validity 立即进入 `STALE`；新指纹在评测通过前不能按旧 Activation 接受。
- `UNRESOLVED_MUTABLE` 只可用于 Capability Contract 明确允许的非精确回放 Strategy，并必须具有短有效期、持续 Canary 和独立领域审核；超过有效期或 Canary 失败即停止解析。要求精确可回放的 Capability 禁止此类 Strategy。

业务 Capability Owner 在 post-call 门禁返回 `MODEL_FINGERPRINT_NOT_EVALUATED` 时，Application Services 必须把信号中的 exact Qualification Proof / actual fingerprint / Catalog / Adapter Revisions 交给本主题；本主题由 Proof 解析其 Activation / Evaluation 依据，并以 Expected Validity Revision 将相关 Evaluation 从 VALID 单调推进为 STALE。该追加可以晚于被拒绝的调用，但被拒绝调用本身已经不能封存领域结果；因此失效事件延迟不会形成生产污染窗口。

模型能力增强后，只有新 Strategy 通过相同或更严格门禁，才能减少确定性语义规则或扩大模型工作。模型退化时只回退到同一 Contract 下已经通过门禁的 Strategy，且不改变 Artifact、Candidate、Verifier、Snapshot 或 Answer Review 路径。

## 7. 回退流程

1. 监测、Conformance 或业务审核使当前 Evaluation 失效。
2. Management 按影响范围追加 Evaluation Validity 失效，或对单个 Activation Scope 追加 `REPLACE / DEACTIVATE`；不修改旧 Result 或旧 Decision。
3. 新运行只解析 current Decision 显式批准的 Fallback Activation Decision，并再次确认其独立 `PASS + latest VALID`；已开始运行仍按其 Failure Contract 受控结束或取消。
4. 回退执行产生新的 Attempt、Catalog、用量和审计记录，不伪装成原 Strategy 成功。
5. 没有有效回退时返回 `NO_ACTIVE_STRATEGY`，不能临时使用未评测模型或直接来源旁路。

## 8. 失败与并发

| 类别 | 处理 |
|---|---|
| EVALUATION_DEFINITION_INVALID | 不运行；修正 Case、Oracle 或依赖 |
| EVALUATION_RUN_CONFLICT | 同一 Run Idempotency Key 对应不同 Request，或 Run 状态不允许推进；失败关闭 |
| EVALUATION_OUTCOME_PENDING | 至少一个已 dispatch Case Attempt 的 Outcome 无法证明；不封存 PASS，按原 Attempt 解析 |
| ORACLE_UNAVAILABLE | Result 为 INCONCLUSIVE，不按失败样例猜测 |
| STRATEGY_CONTRACT_MISMATCH | Result 为 FAIL，不允许激活 |
| MODEL_FINGERPRINT_MISMATCH | 写入 STALE Validity Decision；不修改既有 Result |
| ACTIVATION_WITHOUT_PASS | 拒绝管理命令并审计 |
| ACTIVATION_CONFLICT | 乐观并发失败；重新读取后显式决策 |
| ACTIVATION_IDEMPOTENCY_MISMATCH | 同一 Owner Key 对应不同 Decision Request；拒绝且不推进 Revision |
| NO_ACTIVE_STRATEGY | 应用调用失败关闭或使用预先批准回退，不临时选择 |

Evaluation Run / Case Attempt、Evaluation Result 和 Activation Decision 使用各自稳定幂等身份。Validity 追加使用 Expected Validity Revision；迟到的 VALID 写入不存在合法命令。并发激活通过 Activation Control Key、Expected Activation Revision 和逻辑唯一约束保证一个 current Decision，不能依赖“最后写入覆盖”。

## 9. 可观测性与数据边界

- 记录 Definition、Case、Run、Design Baseline、实现提交、实际模型指纹、用量、成本和复核者。
- 线上运行只上报中立指标；Telemetry 不能自行修改 Activation。
- Fixture、Prompt、原始模型响应和人工 Oracle 按数据分类保存，不能泄露到普通运行日志。
- CE 结果不是 Artifact、Evidence 或正式知识，也不能直接修改生产 Snapshot。

## 10. 拟议不变量

1. 每个业务模块拥有其 Capability Evaluation Contract；Application Services 拥有 Evaluation Run / Result、Validity 和 Activation Decision。
2. 只有闭合 Evaluation Run 产生、语义结论为 PASS 且最新 Validity 为 VALID 的 Result 可以支持 Strategy 激活和回退；Evaluation-only 输出始终留在隔离 Sink。
3. 模型、Prompt、Tool、Adapter 或实质配置变化不能沿用旧 Strategy/Evaluation 身份。
4. 滚动别名必须暴露可回放性风险；实际指纹变化或有效期届满使依据失效。
5. Application Services 在进入 Core 前解析并冻结 Strategy；Core 和 Gateway 不反向读取激活状态。
6. 评测与直接调查参考不能成为生产知识或回答旁路。
7. 回退不能降低正式知识、权限、准入、发布或审核边界。
8. 未来 Evaluation & Learning Engine 只能承接评测执行与分析，不能绕过 Application 的激活权威。
9. Evaluation-only Grant 只运行 exact candidate / cases，输出不能进入生产；首次评测不依赖生产 Activation。
10. 每个 Result 封存时具有 initial VALID；后续 Validity 单调失效，回退只能引用 current Activation Decision 显式批准并经重验独立合格的 Fallback Activation Decision。
11. 每个 Activation Scope 由单调 Activation Revision 和不可变 Decision 管理；停用一个 Scope 不撤销其他 Scope，共享 Result 也不能代替 Scope 级停用。
12. Evaluation Run、Case Attempt 和 Activation Decision 的未知 Outcome 只按原稳定身份恢复，不能通过新 ID 掩盖或重复执行。

## 11. 验证类型边界

- `CE-*` 判断 Strategy 是否达到 Capability 门禁。
- `CC-*` 判断 Runtime、Adapter 或实现是否符合已经 Accepted 的契约。
- `DVR-*` 只关闭会改变本设计契约的实质不确定性。

三者可以复用 Harness，但不能共用结论或状态。本文当前无需 Design Validation Demo。
