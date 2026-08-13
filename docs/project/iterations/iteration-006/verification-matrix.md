---
id: ITER-006-VERIFICATION
kind: iteration-verification
status: completed
authority: planned-verification
owners: [quality]
depends_on: [ITER-006-PROPOSAL]
code: [validation/structure_world_model_iteration_006/oracle.json, validation/structure_world_model_iteration_006/capability, src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py]
tests: [tests/test_structure_knowledge.py, tests/test_java_static_call.py, tests/test_java_static_call_update.py, tests/test_behavior_view.py, tests/test_iteration_006_capability_qualification.py, tests/test_iteration_006_live_evaluator.py, tests]
iteration: ITER-006
---

# Iteration 006 Verification Matrix

| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |
|---|---|---|---|---|---|---|
| V-001 | Maven Structure 行为与 digest 不因通用 graph 扩展漂移 | contract | baseline `bc0ecef…` 的既有 Maven fixtures/tests | 全部既有测试 PASS；旧 Profile 仍只声明原类型/谓词与 qualified artifact identity | explicit Maven default-set regression；旧 Strategy 文件恢复原始 SHA-256；run-008 当前 836/836 full suite | **PASS** |
| V-002 | Java lexer/parser 不把注释、字符串或未知接收者误报为调用 | unit/contract | Oracle `sha256:3e4d502c…`；R1/R2 exact source closure | declarations/calls/byte ranges 完全一致；未知与歧义拒绝 | R1/R2 type/method/call/Evidence exact match；zero/N target、variable receiver、truncated、symlink、digest/tree tamper tests | **PASS** |
| V-003 | Java batch 的 Root/State、Coverage、Evidence 与 Schema 闭合 | contract | R1 `db44ddb8…`、R2 `575ef5a1…` 与 frozen Oracle | Admission PASS；任一篡改或缺项 FAIL | exact Schema/Evaluation/Canonicalization digests；independent replay Admission；Root stability、Coverage member closure 与 tamper tests | **PASS** |
| V-004 | 更新独立于问题且失败保持旧 CURRENT | integration | R1 valid → R2 valid → R3 `3ba3459d…` unsupported | R1/R2 原子发布；R3 拒绝且 CURRENT=R2 | true Git Workspace integration；R3 `JAVA_CALL_TARGET_AMBIGUOUS`；Version history 仅 R1/R2 | **PASS** |
| V-005 | Bundle/Catalog 在 Source-off restart 可重建 Behavior View | isolation/product | sealed R1/R2 Read Sets；repo/database denied | inventory/direct/path/diff 与 Oracle 一致；tamper 拒绝 | DB/repo 改名不可达；新 Python process 只挂 Catalog/Bundle 完成四类 View；通用 Bundle/Catalog tamper regressions | **PASS** |
| V-006 | WORLD_MODEL 产品链回答静态调用并诚实报告边界 | product | deterministic supported、negative、diff 与 Gap questions | 同一正式入口、Coverage/modality/Gap/Citation 正确；无 Source 回退 | formal inventory/direct/path/no-path/diff/Gap tests；真实 Java Evidence Broker/Projector Citation；no payload 进入 capability proposal | **PASS / deterministic product chain** |
| V-007 | 问答不改变更新权威状态 | product/security | Source-off View 前后 authority receipt | CURRENT、Update Attempt、Source Operation 计数不变 | CURRENT tuple、Workspace/Update Attempt 与 Source Operation before/after exact equal | **PASS** |
| V-008 | 真实模型相对直接调查不退步 | product/live | run-003 suite `sha256:32de10fb…`；run-007 suite `sha256:66192cdf…`；run-008 suite `sha256:0793db73…` + evaluator `sha256:bb972939…` | 重大错误 0；逐题不低于较强 baseline | run-003/run-007 FAIL 永久保留；capability run-002 8/8 `PASS_VALID`；run-008 Direct/Codex/World Model 各 6/6，World 六题重大错误 0、完整度 1,000,000，report `sha256:857085c4…` PASS、blocker 0、无 retry/filter/interpolation | **PASS / RUN-008** |
| V-009 | 正式本机 Web 人工体验闭合 | product/browser | dynamic Java Behavior Read Set | supported、Gap、Citation、empty console PASS | exact UI `9cc1387f…` 的 in-app Browser 已确认 READY、3 Java Read Sets、Coverage、1280×720、Citation GET 与 empty console；run-008 同一 UI/正式端点 6 POST 均成功，覆盖 supported/negative/diff/Gap 并生成 11 个 Citation projection；未重复模型题目 | **PASS / COMPOSITE EXACT-UI + RUN-008 LIVE ENDPOINT** |
| V-010 | Production Activation 未被推导或执行 | activation | exact iteration result | NOT_EXECUTED | listener stopped；无 activation command/receipt | **PASS / NOT_EXECUTED** |

测试、Capability Evaluation、Product Validation 与 Activation 互不替代。当前 V-001—V-007 的确定性实现 Gate PASS，V-010
保持 NOT_EXECUTED；run-003 与 run-007 V-008 失败均永久保留，各自 grant 不可重试或复用。Java generic proposal 的八题
capability 资格已用于 exact run-008；修复后的三路各 6/6 且 comparison PASS，当前 V-001—V-010 均有闭合证据。run-008
authorization 已消费，不得重跑。Matrix 只支持“技术验证完成”，不拥有最终 Acceptance；Iteration 仍须由用户对 exact Result
单独裁决，且任何 Acceptance 都不能推导 Production Activation。

`FINDING-006-013` 同时确认：这六道封闭题只证明 Java 静态调用子集，不证明“基于源码回答通用问题”的 MVP，也不证明新增
能力已经与既有 Maven/Structure 能力形成可供用户自由提问的累积产品能力。新的产品目标对齐 `V-000` 从 `ITER-007` 起执行；
本 Matrix 不追溯改写为该 Gate 的通过证据，最终 Acceptance 也必须保留这一限制。用户随后于
`2026-08-13T11:45:33+08:00` 接受 exact run-008 的窄范围结果，最终裁决见
[Iteration 006 Acceptance](results/acceptance.md)；Production Activation 仍为 `NOT_EXECUTED`。
