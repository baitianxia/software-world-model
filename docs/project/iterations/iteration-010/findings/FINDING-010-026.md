---
id: FINDING-010-026
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, ITER-010-RESULT-V-WEB-000-LIVE-RUN-009, FINDING-010-025]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: project-exact-prior-action-intents-and-reject-duplicate-broker-work
target: src/software_world_model/application_services/engineering_question_answering.py
---

# FINDING-010-026：模型看不到先前 query，无法遵守不重复调查规则

## Observation

`V-WEB-000` 通过后的第一条公开方向题绑定 clean candidate
`aa1423465a240f3155f9773bcd97652cf88e4a1f`，从真实 loopback Web 询问 `mall-admin` 与 `mall-security` 的安全职责、模块边界、依赖方向和
认证/授权分工。Question Understanding 后，调查先执行 `SOURCE / search("mall-security")` 和一次合法 READ；随后又连续两次提交完全相同
的 `SOURCE / search("mall-security")`。第二个重复 observation 触发 deterministic no-progress fuse，Result
`engineering_result_b15fde6075bb591118c4c57c62b5463c` 在 Answer/Review 前失败关闭。

## Evidence and root cause

- 4 题 suite 在外部 dispatch 前密封于
  `var/iteration-010/slice-001/run-004-direction-preview/direction-suite-freeze.json`，digest
  `sha256:f75f2e7881b8b57b4e9dd1b7ff01da9ac322bb4c853ed1853f881db9ca74f100`；现场题仍为 `PENDING_USER`；
- 永久 run 目录为
  `var/iteration-010/slice-001/run-004-direction-preview/web-v-web-001-q1-001/`；Browser 显示 `FAIL CLOSED`，开发者详情记录
  `NO_PROGRESS_FUSE_EXHAUSTED`、5 次 role call、4 个 authorized Broker operation、4 次 Source operation、no-progress 2、Answer/Review
  未到达；terminal receipt 为 retry 0、Provider switch 0、Production Activation `NOT_EXECUTED`；
- Prompt `@7` 已要求“Never repeat an earlier query or locator intent”，但模型可见 `INVESTIGATION_PROPOSAL` Ledger entry 只含 operation 与
  step，既没有 attempt、evidence class、query，也没有 locator intent；typed Retrieval Result 也不携带产生它的 query；
- 因此模型虽收到全部 append-only Ledger 与 progress digest，仍无法机械识别“这个 evidence class + query 已执行”。原规则要求消费一个
  未投影给角色的事实，重复行为不能归因于单次模型随机性；它是 `local-implementation / systemic` 的角色输入闭包缺口。

## Decision and disposition

- Application 在每个 `INVESTIGATION_PROPOSAL` Ledger entry 中只追加本次 attempt 的 exact action intent：attempt、operation、evidence
  class、query 或 opaque locator reference；不加入 Source payload、路径推断或新权限；
- INITIAL/VERIFICATION 输入新增从 authoritative Ledger 派生的 `prior_action_intents`，且按 current attempt 过滤；补证角色不会把旧初始
  investigation 的 raw intent 当作自己的新 Result；
- Source Broker 在 Worker 前机械拒绝同一 attempt 内重复的 SEARCH `(evidence class, query)` 或已用 READ/PARSE locator，reason 为
  `DUPLICATE_ACTION_INTENT`；既有 no-progress fuse 继续在模型持续违规时失败关闭；
- Prompt 升级为 `engineering-qa-adaptive-investigation-prompt@8`，明确同一 `progress_digest` 再现就是“本步无进展”，必须立即换 evidence
  class/query/eligible locator 或诚实 FINISH；
- 不提高调用、operation、bytes 或 no-progress 上限，不重试已失败题，也不添加工程名、题目、关键词、类、方法或 fixture 分支。

该变化把既有“结果驱动且不重复无效工作”职责落实到通用 Ledger/Broker/model boundary，处置到代码与测试，不改变 System Contract。

## Verification

新增回归证明 duplicate search 在第二次 Worker read 前由 Broker 拒绝，并证明两个 investigation role 都能看到 attempt-scoped
`prior_action_intents`；Engineering QA focused 64/64、docs 403/403、`py_compile` 与 `git diff --check` PASS。full discovery 与新 clean
discovery 共 1116 项，其中 1111 PASS；唯一 4 FAIL + 1 ERROR 的 test identity、`QUALIFICATION_INVALID: V-009 Adapter Conformance
implementation drifted` marker 与 Codex actual/frozen digest `7645c3ca… / 9f6748b4…` 精确保持 `FINDING-008-020` 历史 hold，没有新增
失败。raw full suite 仍为 FAIL，只以 `PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD` gate 继续。新 clean candidate 的剩余公开方向题仍须
在提交后执行；本题和 candidate 永久保持失败，不能重放或追认。
