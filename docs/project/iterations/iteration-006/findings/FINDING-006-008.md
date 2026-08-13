---
id: FINDING-006-008
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality, security]
depends_on: [ITER-006-SLICE-001, ITER-006-VERIFICATION, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING]
code: [src/software_world_model/interface/world_model_product.py, src/software_world_model/ai_infrastructure/model_egress_gateway.py, src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, src/software_world_model/ai_infrastructure/java_model_egress_qualification.py]
tests: [tests/test_behavior_view.py, tests/test_world_model_answer_strategy.py, tests/test_iteration_006_capability_qualification.py, tests/test_model_egress_gateway.py]
iteration: ITER-006
classification: system-contract
disposition: bind-profile-versioned-proposal-contract-and-requalification
target: SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING
---

# FINDING-006-008：Java generic operation vocabulary 没有继承旧 Answer qualification

## Observation and evidence

获明确授权的 `run-003` 按冻结顺序执行后，World Model 的 `WM-006-001` method inventory 与 `WM-006-003` positive path
均返回 HTTP 502。两个 request 的 isolated terminal 都是 `failure_stage=ANSWER`，Gateway SQLite 没有 Model Call revision，
server audit 为 `REJECTED`；因此失败发生在 Provider dispatch 之前，不是网络或 Ark 输出失败。

两条 server response digest 分别为 `sha256:fbc2b487…` 与 `sha256:bb478056…`。把各自 request digest 与
`code=reason_code=QUALIFICATION_INVALID` 按 Gateway response schema 重新计算，可精确得到这两个 digest。候选 Product 的
generic proposal 输入包含 `declared_method_inventory`；继承的 ITER-003 exact egress policy 只资格化旧 Maven operation
vocabulary，故正确地失败关闭。其余不经过该 generic vocabulary 的四题成功，进一步排除了全局 listener、credential 或
Provider 配置故障。

## Classification and disposition

这是已在 Slice risk 中预告、现由 live evidence 证实的跨 Profile system-contract blocker，不应通过删除
`declared_method_inventory`、伪造旧 vocabulary、放宽 Gateway exact check 或选择性重跑来掩盖。下一候选必须：

1. 为 Java method inventory 与 generic path planning 建立版本化 Strategy/Prompt/input contract；
2. 以独立 closed capability suite 完整重新资格化，不能继承 ITER-003 qualification；
3. 重新冻结实现、evaluator、suite 与 grant，并取得绑定新 suite 的用户披露授权；
4. 把 `run-003` 两个失败永久保留。

该跨 Profile 不变量已写入 `SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING`；具体实现以 Java contract/Strategy 1.1.0、
Prompt @4、vocabulary @2、八题 closed suite 和 exact Java Gateway policy 闭合。用户对 exact freeze 的单次授权已由 capability
run-002 消费，八题 8/8 PASS 并形成 proof `sha256:65d18436…` 的 `PASS_VALID` qualification；新的 run-007 product candidate/suite
也已 zero-provider 冻结。该段的下一 Gate 后续经 run-007 FAIL 与 wrapper 修复继续推进；全新 run-008 最终三路各 6/6、
comparison `sha256:857085c4…` PASS。run-003 的 qualification failure 仍永久保留，Iteration 则进入最终用户 Acceptance Gate。
