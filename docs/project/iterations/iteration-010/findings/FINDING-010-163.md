---
id: FINDING-010-163
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [project, quality, engineering]
depends_on: [FINDING-010-162, ITER-010-PDR-010, PROJECT-GOVERNANCE-PLAN-EXECUTION]
code: [scripts/docs.py, scripts/plan_gate.py, validation/iteration_010_mvp/value_gate/runner.py]
tests: [tests/test_docs_gate.py, tests/test_plan_gate.py, tests/test_iteration_010_mvp_value_gate.py]
iteration: ITER-010
classification: iteration-design
scope: systemic
disposition: one-time-user-authorized-trust-root-recovery
target: ITER-010-PDR-011
---

# FINDING-010-163：冻结 verifier 缺口与治理动作前置条件形成机械自锁

## Observation

`FINDING-010-162` 已证明当前产品停止条件成立，但 `ITER010_MVP_LIGHT@2` 无法诚实表达答案生成前失败。进一步检查
`scripts/plan_gate.py::validate_transition` 发现，常规 plan revision 又同时要求 base current action 的 `kind=governance` 且该动作已有冻结
runner 验证的 PASS Result。当前 base action 是 `mvp-experience-development`；它只能先生成正被错误 verifier 阻止的
`V-MVP-EXPERIENCE-001` Result 才能进入预注册 governance action。因此不存在同时满足“不得伪造 Result”和“先进入 governance action”的
仓库内机械路径。

这不是产品失败，也不是授权不足，而是 plan gate 对 verifier expressiveness failure 缺少恢复入口的治理设计缺口。继续修改产品、继续调用
Provider、把失败文本追认为 Answer，或让候选 Manifest 自行扩权都会隐藏该矛盾。

## Evidence

- trusted base commit/tree：`120a8903462caf04fbf7bda0c1afa07e3133d448` /
  `883bdde37eec62856139e7fc00ee38691d311b73`；工作树 clean。
- `validate_transition` 的普通 revision 分支要求 base action 为 governance、base Result 为 PASS；Result transition 分支又从 trusted parent
  重放 `ITER010_MVP_LIGHT@2`。
- `FINDING-010-162` 已列出 @2 对三份不存在 Answer/Citation/Review/Codex comparison 和单一 Session 的无条件要求。
- ITER-010 既有 `9a8223bc93a45577b695ba8e0989eaa0606ddb74` 先例：一次性用户授权的 trust-root recovery 明确不冒充被中断动作合规，先安装
  governance recovery root，再由后续可信父提交生成 Result。
- 用户明确消息 `授权最小治理修订并继续` 的 UTF-8 内容引用为
  `local-user-message-utf8:sha256:382638cd16fdbc85c08a4202a94e630fe4c973ce03bb0d8a1671cbe4ee151aa7`。该 digest
  只证明本地记录的消息内容，不声称平台身份认证或签名。
- candidate 上 `python3 -m unittest tests.test_docs_gate tests.test_iteration_010_mvp_value_gate tests.test_plan_gate`
  共 189 个定向测试 PASS，`python3 scripts/docs.py check` 与 `python3 scripts/plan_gate.py snapshot` PASS。
- 从 exact trusted base 执行 `python3 scripts/plan_gate.py diff --base 120a890…` 仍如预期拒绝：base action 禁止
  PDR/runner/gate 路径、不是 governance，且缺少那份无法如实生成的 PASS Result。这是本 finding 的可执行复现，
  不是候选通过旧 gate 的声明。

## Disposition

采用一次性、forward-only trust-root recovery，从上述 exact trusted base 安装 `ITER-010-PDR-011`、Manifest failure-handoff action、
`ITER010_MVP_LIGHT@3`、对应定向测试和治理说明。该提交：

- 明确声明不声称通过被自锁的 PDR-010 transition gate；
- 不改产品代码、Prompt、Provider 配置或历史运行证据，不调用外部系统，不生成 Result；
- 将 coding、Provider、Web、hardening、full regression 和 Production 全部锁定；
- 把 product candidate `a5c780f51fa5242ee8209766712ad408ed023f80` 与随后用于密封 Result 的 governance trusted parent
  分开绑定；
- 先提交 @3 runner 成为新的 trusted parent，下一提交才可内嵌 run-052/053 原始记录并密封唯一失败 handoff Result。

通用治理规则同步补充 verifier expressiveness recovery 条款，后续计划必须预留不依赖待修 verifier 的治理恢复入口，避免再次形成同类自锁。
