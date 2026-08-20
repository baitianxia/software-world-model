---
id: FINDING-008-021
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [architecture, application, ai, engineering, quality, project]
depends_on: [ITER-008-SLICE-001, FINDING-008-019, FINDING-008-020, SYS-ADR-015, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING]
code: [src/software_world_model/application_services/bounded_world_model_investigation.py, src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, src/software_world_model/ai_infrastructure/model_egress_gateway.py, validation/structure_world_model_iteration_008/capability]
tests: [tests/test_bounded_world_model_investigation.py, tests/test_world_model_answer_strategy.py, tests/test_iteration_008_capability_harness.py, tests/test_iteration_008_capability_qualification.py, tests/test_model_egress_gateway.py]
iteration: ITER-008
classification: system-contract
disposition: candidate-discovery-is-upward-normalized-prerequisite
target: SYS-ADR-015
---

# FINDING-008-021：candidate discovery 不能同时充当可终止证据义务

## Observation

clean candidate `ab87c442218a06292829c0508963508d88d54119`（tree
`190b186656fe3cd29c55d04cb8987cdeb06d5821`）的 run-011 DeepSeek Conformance preflight
`sha256:5661c28fde972b366f89aeb92093acac703a2dbdd83dc6180325df6c4f8c43ee` 经后置单次授权后恰好执行 2 requests，12/12
PASS；Conformance result 为 `sha256:32ff8a4a3a45b55a229c60bfe28486937e6eb24aca3cdb587289a7db4bc1d464`，唯一 actual
identity `deepseek-v4-pro`，usage 完整，input/output tokens 为 381/79，无 retry。

同候选 Capability freeze `sha256:f708e49f453a14959b588be3c91424dccb6f20d5320f4ab10fc6b65a4b7407f8` 经独立后置授权
启动。前 14 Case、35 accepted requests 全部 independent PASS，包括 run-010 的两个 premature-FINISH 反例。第 36 次 Provider request
已完成，但 `WM-JSS-I8-NEGATIVE-QUERY-UNKNOWN-015` call 1 在本地 compiler/runner 边界以
`QUALIFICATION_INVALID: bounded capability call did not preserve the frozen evidence obligations` 失败关闭。terminal 记录
36 requests、无 retry；failure/terminal document digest 为
`sha256:5e9d8a7199bafb8dd46deba170faf2c1f0fe0d4fd59905debc78d2f9f7bc7a6b` /
`sha256:c2847e3fc0597ae503cfc69f3353530099ef341246a1034103cb0c7c6842dbfc`。没有 Qualification、正式 Web、canary 或 Activation。

失败问题是 “Does the authorized scope implement purchase-order cancellation?”。DeepSeek 返回合法 closed JSON、正确 candidate operation
和覆盖问题的 terms，但将 evidence request 选为 `implementation_candidates`；冻结 ledger 要求 `method_implementations`。实际输出
digest 为 `sha256:5e7c73b94a519b2b7f9a07eb3bca23415079457bc562a571b9f308919e9141ba`，transport、identity、usage、shape 和
available operation 均正常。

## Evidence and root cause

当前协议把 `implementation_candidates` 同时定义为每题必经的 discovery transition 和一个可以关闭 ledger 的最终 evidence class。
Prompt 要求只有“requested outcome is the candidate set itself”才选择后者，但“是否实现某能力”天然可被解释成寻找候选是否存在；模型
选择 candidate evidence 是可理解的语义投影，不是权限扩张。

这种双重角色会产生更严重的产品风险：若搜索返回非零候选，candidate-only ledger 会在未读取任何 method semantics 时允许 FINISH；
若返回零候选，它与 method ledger 的合法后继和 Limitation 完全相同。要求模型稳定猜中隐藏 evaluator 所选标签既没有增加知识，也把
平台能够保守收敛的最小证据责任再次推回模型。只放宽 run-011 的 zero-candidate Oracle 则依赖未来 fixture 结果，会让真实非零候选
提前结束，不能接受。

## Decision and disposition

`implementation_candidates` 保留为首轮 raw model vocabulary alias 和强制 discovery operation，但不再形成 canonical terminal evidence
obligation。Application 在冻结 ledger 前把该 raw request 无条件向上归一为 `method_implementations`；如果同一请求还有 graph/inventory
义务，再按既有依赖收敛规则处理。这样：

1. 非零且完整的 candidate Result 必须继续进入有界 method batch，不能只凭排名或存在性结束；
2. 零候选、截断候选或 query incomplete 仍因没有合法 method transition 进入平台生成的 Gap/Limitation，不伪造查询；
3. 模型仍只表达通用语义类别，Application 不读取题目关键词、工程、符号、Case ID、Oracle 或未来 Result；
4. 18 Case、41-call 上限、18/18、temperature 0、no-retry、三层完整性、Source-off 与正式 Ark runtime 不变。

活动 capability/Strategy 升级为 `1.5.1`，prompt/vocabulary 为 `@10`，compiler 为 `@5`，Gateway policy 为 `@1.2.1`，suite/oracle 为
`@1.5.1`。旧 run-011 已消费且不可重试；本地闭包和 clean candidate 完成后只能创建全新 Conformance/Capability freeze。

## Verification required before disposition

- raw `implementation_candidates` evidence request 单独输入时 canonical ledger 必须成为 `method_implementations`；与 graph request 组合时
  继续由 graph subsume method，不扩大预算；
- 非零 candidate 安排 method batch，零候选和截断 candidate 分别形成既有 bounded absence/Limitation，不执行伪 method query；
- production compiler、Gateway dynamic allowlist、fake transport 18 Case / 41 calls 与 independent evaluator 保持 18/18；
- targeted、docs、diff/secret scan 与允许 AF_UNIX 的完整回归重新执行。新的 live qualification 未达到 18/18 前继续阻断正式 Web、
  hidden canary、SLICE-002 和 Production Activation。

## Verification evidence and closure

- core/Strategy/capability/product 56/56，DeepSeek adapter/conformance、diagnostic、runtime/auth/http/static-call 48/48，允许 AF_UNIX
  listener 的 Gateway 12/12，合计相关回归 116/116 PASS；
- fake transport 严格完成 41 calls / 18 Case，并以 18/18 PASS 关闭；raw candidate alias 的非零候选明确投影到唯一
  `method_implementations` transition，既有零候选与截断候选终态回归继续 PASS；
- `python3 scripts/docs.py check` 对 325 份 current documents PASS，compileall、`git diff --check` 与仅输出路径的 secret scan PASS；
- 允许 AF_UNIX 的完整套件执行 985 项，其中 980 项 PASS；四个 failure 和一个 error 仍全部是 `FINDING-008-020` 已隔离的 ITER-003
  frozen Codex CLI exact-binary drift，没有新的 ITER-008 failure。

主处置已写入 `SYS-ADR-015` 及其拥有的 Application Contract，当前 system-contract fileset digest 为
`sha256:11b8b2d56386451802bc64214547abe253d54f26855a1ba7f9428acb43511a54`。Finding 因此置为 `dispositioned`；这只关闭实现与
Contract redirect，不把 run-011 改写为 PASS。clean candidate 后仍须执行全新 run 的 2-call Conformance 和一次 41-call Capability，
18/18 前 V-002 与所有产品 Gate 保持 blocking。
