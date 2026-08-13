---
id: ITER-006-RESULT-JAVA-CAPABILITY-CANDIDATE-FREEZE
kind: iteration-result
status: candidate-frozen-awaiting-authorization
authority: execution-evidence
owners: [engineering, quality, security]
depends_on: [ITER-006-VERIFICATION, ITER-006-RESULT-LIVE-RUN-003, FINDING-006-008, FINDING-006-009, FINDING-006-010]
code: [src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, src/software_world_model/ai_infrastructure/world_model_capability_evaluation.py, src/software_world_model/ai_infrastructure/java_model_egress_qualification.py, src/software_world_model/ai_infrastructure/java_model_egress_policy.json, validation/structure_world_model_iteration_006/capability]
tests: [tests/test_world_model_answer_strategy.py, tests/test_iteration_006_capability_qualification.py, tests/test_model_egress_gateway.py, tests/test_world_model_evaluation_grant.py, tests]
iteration: ITER-006
---

# ITER-006 Java Capability Candidate Freeze

## Decision

run-003 的 qualification blocker 已实现为一个新的 Java proposal candidate：contract/Strategy `1.1.0`、Prompt `@4`、
vocabulary `@2` 与 exact operation set 独立于 Maven 1.0.2；八个 required case、独立 stdlib evaluator、资格 Result closure
和后续 exact Java Gateway policy 已闭合。最终 full regression 为 **835/835 PASS（86.208 秒）**。

本 Result 只证明候选和 zero-provider preflight 已冻结。没有执行八次 Ark capability call，没有形成 qualification，也没有重跑
三路 Product Comparison；因此 V-008 仍由 run-003 的 FAIL 决定，Slice/Iteration 均未接受。

## Exact candidate

- legacy Maven Strategy 文件保持原始 SHA-256：
  `520580b24f46a94439602e987268b24575746383b5e9e0c8e6845189664f2ebc`；
- Java versioned Strategy 文件 SHA-256：
  `902f5bf4d1d48fe0bf4f959f97782353cd82dfa493f268451556a1a8bf5476f9`；
- Java Strategy implementation digest：
  `sha256:987642e59a27f0674d06e24d3cdf5ddd72345e460ae853d56e5430440320a5ac`；
- Prompt program digest：
  `sha256:7051ca379581386cf677c8f1c74d941e50e533cfab562820a307622fe42cab5f`；
- output contract digest：
  `sha256:2b7e9a5dbae0d9436ee9d7cc87ffa17be33997d4e1f59bbc75e385c8e51bbd9d`；
- metric contract digest：
  `sha256:47dd65fde126f2b2246ac7ecd1e20182e83e9b2ba0d08652ac12d3ecbffa0b6c`；
- exact egress policy file digest：
  `sha256:63729ded35116ea47ee7fbe1c653b6a48e023e6307ffbace5e58c3fa778a7455`。

Candidate identity 只覆盖 baseline commit/tree 加实际改变的 `src/`、`tests/`、`validation/` 与 `pyproject.toml`，不让结果文档
回写反向改变可执行 subject。60 个 candidate path 的 manifest digest 为
`sha256:8d094dea54f08838bea8d91fdeffd2087b7d6a432cb49563f3cc1d92faa96b96`。

## Closed qualification inputs

Suite 与 Oracle 分离保存；模型只能收到 synthetic sealed case input，Oracle 在该 case 的唯一 Provider call 返回后才由独立
evaluator packet materialize：

- suite `ITER-006-JAVA-WORLD-MODEL-CAPABILITY-SUITE@1.1.0`：
  `sha256:93be2f872fe8531d09ca220b67aa493d8f929cbca1b27309b2d05775684d6716`；
- separate Oracle：
  `sha256:0d563879c5bf53606082d669b9f5650c7a07c7fb2f59d96d741c7a0cf84facb7`；
- stdlib-only evaluator：
  `sha256:266693d32303430c78077b8154dddaec34a068ab026942e761399741a2c0e9cf`；
- evaluation definition：
  `sha256:2f46b4f1a5187f3786c5b2e29c6859c65cd47afbc1735c78adfd02746d9e15b6`。

八个 case 覆盖七类 role，并将 Java method inventory 与 static-call path 分成两个 generic planning case。Result 只有八题逐题
exact projection 全部 PASS、forbidden event 为 0、failure/unknown 均为 0、Provider request 恰为 8，才可成为
`PASS_VALID` qualification。

## Freeze and authorization boundary

最终 freeze 位于本机 `var/iteration-006/capability/run-002/`：

- qualification freeze：
  `sha256:7a3948a358ba309539b1362b7b26ee659c9edfa5ec4738deccb9c4c633fced26`；
- authorization request：
  `sha256:2366710912ce660972dcf4d15ca291f28d01f62d9d2eb247f79cb0ad52bd1d3f`；
- zero-provider verification：`PASS_AWAITING_USER_AUTHORIZATION`；
- `external_model_called=false`，Production Activation 与 Git stage/commit/push 均 `NOT_EXECUTED`。

所需新授权只针对该 freeze/suite 向火山引擎 Ark 分派八个 synthetic capability case，每题一次、无 retry；不向 Codex 分派，
也不发送产品问题、Java source closure 或 Evidence payload。Preflight 只检查 credential 是否配置，未创建 transport、socket 或
Provider call，credential value 未写入任何证据。

run-003 grant 已消费且不匹配本 suite，不能复用。只有新的 capability run 得到 `PASS_VALID` 后，才能另行生成三路产品
comparison freeze；该后续 comparison 仍需绑定新 suite 和 payload boundary 的独立用户授权。

## Subsequent evidence

本 Result 的候选事实保持不变。后续用户 exact 单次授权已由
[Java Capability run-002](java-capability-run-002.md) 消费并取得 8/8 `PASS_VALID`；新的三路候选另见
[Product Candidate Freeze run-007](product-candidate-freeze-run-007.md)。这些后续 Result 不追溯改写本 freeze 生成时的
zero-provider 状态。
