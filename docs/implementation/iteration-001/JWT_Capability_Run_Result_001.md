# Iteration 001 JWT Capability Run Result 001

| 元数据 | 值 |
|---|---|
| Record ID | `SWM-IMP-JWT-CAPABILITY-RUN-RESULT-001` |
| Date | 2026-08-06 |
| Status | `JWT CE PASS / VALID AT REGISTRATION / ACTIVATION NOT RUN` |
| Scenario | `H-04 JWT Commit Impact` |
| Answer Generator | `VOLCENGINE_ARK / glm-5.2`（Direct与World） |
| Independent Evaluator | `OPENAI_CODEX / NOT_EXPOSED_BY_CLIENT` |
| Production Authorization | `NONE` |

## 1. 结论

当前Coding Plan @7 Adapter CC、Direct Oracle源码复核、隔离Run Configuration、七角色World Model运行、跨模型逐Obligation比较和CE Authority登记均已真实完成。最终World结果为`PASS / DELIVERED`；独立比较为`PASS`；CE Registration为`PASS / VALID`并签发`CAPABILITY_EVALUATION`资格。

Direct答案和World答案都由火山`glm-5.2`生成，因此比较阶段不再调用火山自评。Codex从冻结Git对象重读源码，以`obligation_id`对齐两侧内容并出具本地Review Attestation。比较记录明确保存双方生成来源、Evaluator来源和独立性判断；Oracle与World正文没有在此阶段发送给火山。

本记录仍不是产品验收或生产激活。产品Holdout尚未执行，真实Strategy Activation保持`NOT_RUN`。CE Validity有时间窗，过期或实现、配置、CC依赖变化后必须重验，不能把历史PASS当作永久资格。

## 2. 最终不可变证据

| 阶段 | 不可变身份 | 摘要 / 结果 |
|---|---|---|
| Ark CC | `ccrun_25bcd3f2fbf040ff957dabe02bf7ea63` | `sha256:91ccfbb2d084ee41888833d7519d1867cd96c91b22d5bed279032e76d5a0a5ac`；12 / 12 PASS；2 requests；Input 327 / Output 77 |
| Direct Oracle | `oracle_249409ecf7d84da7b1a6cc85f21b89b8` | `sha256:dc72745c3a1a8ce84754a3cefbae180f5e44796ef6406c6f0f7f3b2358693b56`；6 grouped Claims；21 / 21 Obligations |
| Final Run Configuration | `jwtrun_11fa390ceb7545f4b7d951973729dd85` | `sha256:8e9a547c3869d7429ce0ad0b8524c551a9fb54da3051ad532a7a6ce2c69d8a86`；Oracle正文不可供Runtime读取 |
| Final World Result | `jwtrun_715915f2629b4656aee9c31b6127bef0` | `sha256:86ce8ebec0c93cb011015a23e3e893a64a603aa94874053ae6dd047d134b7fd4`；`PASS / DELIVERED` |
| Delivery Body | Final World Result内 | `sha256:4e2a5c0f3f8ed833411438e13465b17d3bbe0c3c064dd5d715a2d5cc06b91b48` |
| Codex Review | Final Comparison绑定 | `sha256:a73edb552cdb3bde43d790e070a2a3f41c3ad4741c2fbcae591668b5009bcd44`；21 / 21 Findings |
| Comparison | `jwtcmp_3218ad611ea24c98b1930b92d0cd5f0a` | `sha256:1a895a24a3e66caa1e908a629211cd01194e31e940c9c08b14dd54d22f8bcfca`；PASS；Direct 9 / World 10 |
| CE Registration | `evaluation_run_094afa178f7e4a17916d6ecdaf0d2e72` | `sha256:1d91be12a8be5ab73ecc07662b442aaceaffbf4b380afd3aaa0d93884280351a`；PASS；`CAPABILITY_EVALUATION` |
| CE Result | `evaluation_result_6e8ce0ffbd3740d191061010b345e033` | `sha256:192681578b63a751ee6262ffaa5d100318ee16467cda521a100cf8cdb984bffb`；有效至`2026-08-07 00:00:33.396562 +08:00` |

产物分别位于`var/conformance/`、`var/jwt/oracle/`、`var/jwt/run-config/`、`var/jwt/world-runtime/results/`、`var/jwt/review/`、`var/jwt/comparison/`和`var/jwt/evaluation/`。这些是本地受控运行证据，不应提交到公开仓库。

## 3. 最终World运行事实

- 角色调用次数：Planner 4、Fact Proposer 5、Knowledge Reviewer 6、Inference Proposer 1、Sufficiency Reviewer 3、Answer Generator 4、Answer Reviewer 4。
- 模型调用预算计数31次，其中27次被接受、4次Provider结果已知但被closed Schema或语义复验拒绝并用新物理调用恢复。
- Source Tool：3步；读取1个精确文件窗口；Source Bytes 11985。
- Usage：Input 210874 / Output 34286 tokens，完整；未配置价格，因此不推测成本。
- 时间：518484毫秒。
- Answer：21条Claim，21 / 21 Obligation均`SATISFIED`，Answer Review为`APPROVED`。

最终答案保留了此前容易丢失的边界：完整三文件集合、verify与parse两个异常位置、旧代码显式`SignatureAlgorithm.HS512`与注释证据的区别，以及`Map<String,Object>`声明类型和未知运行时载荷类型/序列化的区别。

## 4. 独立比较结论

比较以21个冻结`obligation_id`为主键，不要求Direct与World拥有相同`semantic_key`或Claim分组。Direct的6条组合Claim和World的21条拆分Claim分别被展开到相同义务集合；最终证据为：

- missing Direct = 0，missing World = 0；
- extra Direct = 0，extra World = 0；
- duplicate Direct = 0，duplicate World = 0；
- target / need结构错配 = 0；
- 20项`EQUIVALENT`，1项`WORLD_BETTER`，没有`DIRECT_BETTER`或事实错误；
- Direct 9分，World 10分。

`JWT-N06-O03`判为`WORLD_BETTER`：两侧都承认Hutool具体运行时载荷类型与序列化未知，但World进一步准确区分了源码可见的`Map<String,Object>`声明和未知的具体运行时值。

独立性边界是“Evaluator模型来源不同于两个Answer Generator”。记录中Direct与World生成来源均为`VOLCENGINE_ARK`，Evaluator来源为`OPENAI_CODEX`。当前Evaluator复用了Oracle源码复核者，产物通过`oracle_reviewer_reused=true`如实披露；这是模型来源独立，不是两个Codex人员会话之间的人员独立。Review Attestation属于受控操作员声明，系统可验证其闭合字段、依赖Digest和来源不相同，但不能从本地文件密码学证明远端模型身份。

若未来Direct由Codex生成，则同一规则要求Evaluator不能是Codex；可由火山或其他不同来源模型出具相同Schema的Review Attestation，再由本地比较器封存。比较器本身不固定为Codex，也不需要把候选答案发送给其生成模型自评。

## 5. 失败证据与迭代

失败没有被覆盖或改写：

| 轮次 | Comparison | 结论 | 主要发现 |
|---|---|---|---|
| 1 | `jwtcmp_15fc1a1918924b8c8c4f98ee2b4ad5ff` / `sha256:9e93866787b38926be2b4d03eb0044a9b229a75d44d4deca5839b7894bb183ce` | FAIL；Direct 9 / World 8 | parse异常表述不精确；丢失HMACSHA512注释模态 |
| 2 | `jwtcmp_c5d2402741424a2d90320cbb7082ff41` / `sha256:8764b5680b027c1cf770115e9f553a151176f82aa2f2a0942b4d00793c199d37` | FAIL；Direct 9 / World 7 | 完整三文件未落在对应义务；异常错误依赖verify=true；旧HS512代码被降为注释；载荷未知边界偏移 |
| 3 | `jwtcmp_3218ad611ea24c98b1930b92d0cd5f0a` / `sha256:1a895a24a3e66caa1e908a629211cd01194e31e940c9c08b14dd54d22f8bcfca` | PASS；Direct 9 / World 10 | 21项完整且无事实错误；20项等价、1项World更好 |

前两轮各自登记为CE FAIL且不签发Qualification。第三轮使用新的Run Configuration、World Result、Review、Comparison和CE Result；动态Strategy / Evaluation版本按实现与配置Digest隔离，避免用新代码重解释旧运行。

## 6. 命名解释

| 名称 | 含义 |
|---|---|
| `ccrun_*` | Contract Conformance真实运行ID。 |
| `oracle_*` | 独立复核并密封的Direct Oracle ID。 |
| `jwtrun_*` | JWT Run Configuration或World执行ID；必须结合对象类型和Digest判断。 |
| `jwtcmp_*` | 一次不可变跨模型逐Obligation比较ID。 |
| `evaluation_run_*` | CE Authority中的一次评测运行ID。 |
| `evaluation_result_*` | CE运行封存后的不可变语义结论ID。 |
| `semantic_key` | 单侧答案内部的Claim语义身份；跨侧比较不要求相同。 |
| `obligation_id` | 跨Direct与World对齐的冻结验收义务身份。 |
| `Review Attestation` | 独立Evaluator对21项义务形成的闭合、Digest绑定的本地评审声明。 |
| `CAPABILITY_EVALUATION` | CE PASS后签发、供显式Strategy Activation重验的资格类型。 |
| `VALID` | 当前CE Result仍在有效窗且未被标记STALE/REVOKED；不是永久状态。 |
| `NOT_RUN` | 没有执行；当前特指产品Holdout和真实Activation。 |

## 7. 剩余门禁

下一阶段是产品Holdout与激活决策，不是再次让火山比较自己的两个答案：

1. 另行冻结未参与本次调试的工程和任务并执行G-12；历史`PV-HOLDOUT-001`已失败且H-01至H-05只能做回归，不能冒充新未见集；
2. 对比正确性、任务完成率、关键证据覆盖、诚实缺口、延迟和成本；
3. 若Holdout通过且CE仍`VALID`，再由用户显式决定是否创建限定Scope的Activation；
4. 若CE已过期、实现或配置变化，先重跑受影响的CC / World / Comparison / CE；
5. 在上述条件满足前保持`production_activation=NOT_RUN`，不得宣称Iteration 001产品验收完成。
