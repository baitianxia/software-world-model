---
id: ITER-007-VERIFICATION
kind: iteration-verification
status: failed
authority: execution-evidence
owners: [quality]
depends_on: [ITER-007-PROPOSAL]
code: []
tests: []
iteration: ITER-007
product_goal_gate: V-000
product_goal_outcome: user-visible-general-source-qa-delta
product_goal_evaluation: independent-hidden-plus-live-ad-hoc
product_goal_result_id: ITER-007-RESULT-SLICE-001-STOP-DECISION
---

# Iteration 007 Verification Matrix

| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |
|---|---|---|---|---|---|---|
| V-000 | 本轮相对 baseline 可测缩短通用源码问答 MVP 差距，并与既有能力完成跨域组合 | product / comparison | 未参与实现的真实工程；独立评测方/用户持有且实现阶段不可见的 held-out 自由问题；验收现场临时问题；旧+新知识跨域问题；成熟源码 Agent protocol | 支持率提高；重大错误为 0；逐题完整性不退步；提问时 Source/Update/Direct fallback=0；同一正式 Web 可人工验证 | `ITER-007-RESULT-SLICE-001-STOP-DECISION` | **FAIL / blocking；最早正式 Web Gate 已证伪固定单方法协议，Iteration rejected** |
| V-PRE-001 | exact Java frontend artifact 可在当前冻结执行环境重验 | readiness / frontend | `TREE_SITTER_JAVA_FRONTEND@1` runtime/grammar/version/ABI/license/fileset digest；JDK canonicalization Oracle | 当前 macOS/Python 3.14/`javac 21.0.8 --release 17` 环境的 import/ABI/parse/range Oracle PASS；不回退手写 parser；跨平台 artifact/lock 在 SLICE-001 内、首次产品 Gate/资格前补齐 | Unicode-prefix corpus 上 javac char→UTF-8 byte normalization vs tree-sitter 12 records exact PASS；result `sha256:0c94665…` | **PASS with environment limitation / readiness blocking gate closed for local slice** |
| V-PRE-002 | 新系统语义在编码前由 current Contract 拥有 | readiness / contract | Java Source Semantics、Implementation Query、Knowledge Update/Use、World Model Answering、Security/Operations exact docs digest | docs gate PASS；Profile、no-payload、completeness、operation 与三调用边界无 pending 语义 | Manifest exact contract fileset `sha256:5a8ac62…`；`python3 scripts/docs.py check` PASS on 274 documents | **PASS / readiness blocking gate closed** |
| V-PRE-003 | 信息保持与信息越界 Oracle 在实现前冻结 | readiness / security | exact schema allowlist、typed value/budget/semantic-closure validation、Support Map、direct/base64/gzip/nested-AST/ref reconstruction probes、full legacy `CALLS` consistency Oracle | exact Oracle digest 已冻结且可重跑；不得由产品结果反向修改 | 3 required claims + exact Support reconstructable；6/6 deliberate direct/reversible/distributed-ref leaks rejected；legacy `CALLS` 2 Relations/3 call sites/3 Supports exact；result `sha256:0c94665…` | **PASS / readiness blocking gate closed** |
| V-PRE-004 | 用户持有现场问题，开发阶段不向实现方披露 | readiness / isolation | 用户消息 `codex-user-message:sha256:68df2434…`；product-code-freeze→live-question→Result 绑定规则 | 编码前不要求用户提交题库；开发者自拟题不得冒充用户问题；问题只在产品代码冻结后披露 | 用户明确“你开发，我提问”；Manifest mode `user-held-live-after-product-code-freeze` | **PASS / readiness blocking gate closed; live execution remains Slice blocking** |
| V-PRE-005 | 用户审核 Product-goal alignment 并只授权首个 Slice | readiness / product | V-PRE-001—004 evidence、Proposal、Manifest、first Web/cross-domain/stop bindings | 用户明确接受该评测职责分工并且只授权 SLICE-001 | `codex-user-message:sha256:68df2434a0e31c7996d57ce124d1e3b309f08705cd7e508537c82dbac4de8147` | **PASS / readiness blocking gate closed** |
| V-PRE-006 | ITER-006 exact baseline 可诚实继承 | contract / product | `ITER-006-RESULT-ACCEPTANCE`；commit `8f305ed396899c8f8e5d175fe7fcecb6ceb48f3f`；tree `89d645c…` | 只继承 accepted Java declaration/static-call 窄范围；现场限制进入 SLICE-001 新验证，不修改后沿用 run-008 | [Iteration 006 Acceptance](../iteration-006/results/acceptance.md); clean accepted baseline commit | **PASS / readiness blocking gate closed** |
| V-001 | 固定 Java frontend 形成确定语法闭包 | contract / parser | exact parser/version/license/offline artifact；可见 corpus independent AST Oracle | SLICE-001 最小语法与 SLICE-002 common Java identity/range/order 一致；每单元有 disposition | replacement run-004 product freeze focused 67/67、candidate package 25/25、full 912/912；visible fixture deterministic update/projection PASS | **deterministic SLICE-001 scope PASS / Slice acceptance remains blocking** |
| V-002 | 方法实现语义在问题前独立形成 | update / security | exact source manifest、Build Objective、semantic Oracle、model-input audit | condition/state/return/throw/catch/call-order grounded；输入无问题/suite；tamper fail-closed | run-004 在 user suite 仍为空、question 未披露时完成 visible repository update；source revision/read-set/snapshot 与 probe `sha256:7ac5f44a…` 密封 | **frozen visible candidate PASS / live product evidence remains blocking** |
| V-002A | no-payload 保持必要信息且不搬运源码 | security / oracle | semantic allowlist、信息保持 Oracle、信息越界/可逆性 Oracle | 目标 claims 可从 Bundle 重建；raw source/comment/token/expression text/reversible full AST 均不存在 | readiness 6/6 leak probes + run-004 focused/full regression PASS；candidate stage `sha256:1b83463f…`；exact Answer import 不加载 parser | **frozen visible candidate PASS / Slice acceptance remains blocking** |
| V-003 | 新 Profile 保留旧语义并正确表达 completeness | knowledge / regression | accepted ITER-006 Oracle、新 predicate/modality Oracle、完整 disposition manifest | 旧 declaration/CALLS exact rebuild 一致；新关系不扩张 CALLS；只有 COMPLETE 方法支持闭世界结论 | run-004 deterministic probe 保留 2 个 legacy CALLS、生成 6 个 ordered atoms，`legacy_calls_direction=OUTGOING`；全量 912/912 | **frozen visible candidate PASS / live product composition remains blocking** |
| V-004 | 不点名符号的功能问题能发现正式知识 | application / capability | paraphrase；无 class/method/signature 问题；歧义/0/N 候选；operation contract | `implementation_candidates` 返回有 Support 的 typed candidates；每 Need 有合法 query 或 explicit Gap；无 enum/工程/题目/关键词补丁 | deterministic run-004 选择 `LoginService#authenticate(boolean)`；live“登录流程”发现 authenticate/issueSession/recordFailure 三个候选，但唯一 selector 约束导致 `ENTITY_RESOLUTION_NOT_UNIQUE` Limitation；下单题又返回三个无关登录候选；Findings `007-008/009` | **FAIL / blocking；发现候选不等于完成多方法调查或可靠负向判定** |
| V-004A | 三调用模型协议与隔离边界闭合 | application / capability | exact Prompt/operation vocabulary/gateway workload/qualification | Call 1 Plan、Call 2 Draft、Call 3 independent Review；每题恰好 3 次、无 retry；deterministic validation；失败关闭 | capability run-003 12/12 `PASS_VALID`；product run-004 首个请求 model calls 3、network ops 3、retry 0，Answer/Gateway/terminal PASS，修复后的 role audit 接受 `unix_connect=3` | **PASS / execution boundary closed; Slice acceptance remains blocking** |
| V-XD-001 | `ITER-006-RESULT-ACCEPTANCE` 与 `ITER-007-SLICE-001` 在最小无符号问题中组合 | product / integration | 可见 development 工程的一条无符号名跨域题 | 一个 Need/Support chain 同时绑定旧 CALLS 与新 branch/return/throw，不是正文拼接 | `ITER-007-RESULT-SLICE-001-STOP-DECISION` | **FAIL / blocking；登录流程没有形成 supported 多方法答案** |
| V-XD-002 | `ITER-006-RESULT-ACCEPTANCE` 与 `ITER-007-SLICE-002` 在可见 common-Java corpus 中组合 | product / integration | 可见 qualification corpus 的独立跨域题 | 同一 Need/Support chain 组合旧 CALLS 与 condition/state/return/exception | SLICE-002 未授权 | **NOT-EXECUTED / blocking；Iteration 已 rejected** |
| V-XD-003 | `ITER-006-RESULT-ACCEPTANCE` 与 `ITER-007-SLICE-003` 在 held-out 工程中组合 | product / integration | 产品代码冻结后才披露的独立跨域题 | 同一 Need/Support chain 共同回答；任一知识缺失则 FAIL/Gap | SLICE-003 未授权 | **NOT-EXECUTED / blocking；Iteration 已 rejected** |
| V-WEB-001 | `ITER-007-SLICE-001` 通过正式 Web 执行 `V-XD-001` | product / browser | 正式产品 Web、真实已资格模型、V-XD-001 和一条 boundary | 用户可见 Profile/Coverage、答案/Gap、Citation；console clean；禁止 stub、预制答案、fixture 分支和 validation-only launcher | run-001/run-002 失败均保留；run-004 post-freeze Web terminal SUCCESS，3 calls/0 retry、Citation direct 200、console `[]`，技术链 PASS；登录题拒答、下单题返回无关候选；`ITER-007-RESULT-SLICE-001-STOP-DECISION` | **technical Web PASS / product FAIL / blocking** |
| V-CANARY-001 | SLICE-001 在进入加固前通过真正隐藏的最小 Java 泛化检查 | product / independent-hidden | 独立评测方持有的小型真实 Java 工程及至少一条可回答、无符号名、组合旧 CALLS 与新实现语义的问题；身份/源码/问题在本 Slice 产品代码冻结前隐藏；exact code-freeze/project/suite commitment 与披露收据 | Slice Result 匹配冻结代码和 canary commitment；披露→Result seal 产品变更数为 0；同一正式产品链给出有证据答案，Gap 不算 PASS；seal 后 capsule consumed；未 PASS 不得进入 SLICE-002 | 早期必要产品 Gate 已 FAIL，按 stop 规则未披露 canary | **NOT-EXECUTED / blocking；Iteration 已 rejected** |
| V-WEB-002 | SLICE-002 加固后从同一正式 Web 复验 | product / browser | 5 条自由问题，至少 2 条无符号名，覆盖四类源码问题 | 全部给证据答案或正确 Gap；严格三调用；无 fallback | SLICE-002 未授权 | **NOT-EXECUTED / blocking；Iteration 已 rejected** |
| V-CANARY-002 | SLICE-002 在进入最终 held-out 验证前通过隐藏 common-Java 泛化检查 | product / independent-hidden | 独立评测方持有的 common-Java 小型真实工程及至少一条可回答无符号问题；身份/源码/问题在本 Slice 产品代码冻结前隐藏；exact code-freeze/project/suite commitment 与披露收据 | Slice Result 匹配冻结代码和 canary commitment；披露→Result seal 产品变更数为 0；同一正式产品链给出有证据答案，Gap 不算 PASS；seal 后 capsule consumed；未 PASS 不得进入 SLICE-003 | SLICE-002 未授权 | **NOT-EXECUTED / blocking；Iteration 已 rejected** |
| V-WEB-003 | SLICE-003 在正式 Web 执行冻结 held-out 产品验证 | product / browser | 两个 held-out 工程、12+4 问题与 `V-XD-003` | hidden 和跨域 Case 均走同一产品 Web；答案/Gap/Citation 可人工检查；无 fallback | SLICE-003 未授权 | **NOT-EXECUTED / blocking；Iteration 已 rejected** |
| V-005 | Source-off restart 可答且问题不改权威状态 | isolation / security | repository、Source、authority DB、Evidence Store denied | 支持/Gap 正常；Source Operation、Update Attempt、Direct Attempt delta=0 | run-004 deterministic source-off Query PASS；未授权 grant prelisten fail-closed；authorized live Answer audit 的 Source/Evidence/authority/product-oracle/baseline/git/process/other-role 禁止项均 0 | **PASS deterministic and live isolation / Slice acceptance remains blocking** |
| V-006 | R1→R2 在零问题状态更新并可重启 | update / integration | 两个 exact revisions 与一个 invalid revision | 旧 Session 固定 R1；有效 R2 可用；无效 R2 保持旧 CURRENT/Bundle | SLICE-002 未授权 | **NOT-EXECUTED / blocking；Iteration 已 rejected** |
| V-007 | 两个未参与实现工程的隐藏自由题有实质增量 | product / comparison | 12 answerable + 4 boundary；至少 6 条 answerable 无符号名；exact digests/target | answerable supported ≥ `min(12,max(baseline+4,8))`；两工程/四类均增量；boundary 4/4；Gap 不计支持 | SLICE-003 未授权 | **NOT-EXECUTED / blocking；Iteration 已 rejected** |
| V-007A | held-out 没有被实现污染 | isolation / product | disclosure log、code freeze digest、project/suite digests | 冻结前实现方看不到项目身份/源码/题目；曝光后若改产品，失败保留且工程+问题同时更换 | SLICE-003 未授权 | **NOT-EXECUTED / blocking；Iteration 已 rejected** |
| V-008 | 世界模型支持答案不低于成熟源码 Agent 且旧能力不退步 | product / regression | 同 revision/source/resource protocol 与 ITER-003—006 accepted regression | supported answer 逐题正确性/完整性不低；Agent 可答而模型 Gap=FAIL；成本完整披露 | 早期正式 Web 已在可见题暴露产品退步，未进入最终对照 | **FAIL / blocking；ITER-008 必须重新验证同一判据** |
| V-ADHOC-001 | `ITER-007-SLICE-003` 通过正式 Web 接受现场临时问题并覆盖 `V-XD-003` | product / browser | 3 条现场题；至少 2 条无符号名；含 answerable 跨域与真实 boundary | answerable 给证据答案；boundary 给诚实 Gap；无 fallback | SLICE-003 未授权 | **NOT-EXECUTED / blocking；Iteration 已 rejected** |
| V-009 | 本机 PASS 不产生 Production Activation | activation | exact Iteration Result | `NOT_EXECUTED` | `ITER-007-RESULT-SLICE-001-STOP-DECISION` 明确 Production Activation 未执行 | **PASS / blocking safety invariant；不改变产品 FAIL** |

## 计数与冻结规则

- 12 条 answerable 是 supported count 的唯一分母；4 条 boundary 单独计量，Gap 不能计入 supported。
- target 在 Readiness 前由独立方运行当前 baseline 后冻结，至少为 `min(12, max(baseline + 4, 8))`。
- boundary 必须由独立 Oracle 证明同一授权 Java 源不足；若成熟源码 Agent 能回答，World Model Gap 直接 FAIL。
- `V-CANARY-001/002` 分别是 SLICE-001/002 的独立隐藏阻断 Gate，不属于最终 12+4 计数，也不得复用为最终 held-out 工程。
- 每个 canary 的身份、源码和问题在所属 Slice 产品代码冻结前隐藏；披露到对应 Slice Result seal 的任何产品改动都保留原结果并
  烧毁该 canary，只能换全新工程和问题后重试。seal 后 capsule consumed，后续已授权 Slice 不追溯改写；任一 canary 未 PASS 时
  禁止进入下一 Slice。
- held-out 项目身份、源码和问题在产品代码冻结前都对实现方隐藏。披露到最终 Result seal 的任何产品变化都会烧毁两工程、完整
  12+4 suite、baseline 和 target；重试必须同时换新，seal 后 capsule consumed。

本 Matrix 已以 `ITER-007-RESULT-SLICE-001-STOP-DECISION` 终止：Readiness 与部分技术 Case 已 PASS，但第一个正式 Web 产品 Gate FAIL，
所以 hidden canary 与 SLICE-002/003 的 Case 均未执行。未执行项不得推导为 PASS，也不得由 ITER-008 的未来结果追溯改写。
