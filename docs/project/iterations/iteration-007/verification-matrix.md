---
id: ITER-007-VERIFICATION
kind: iteration-verification
status: not-run
authority: planned-verification
owners: [quality]
depends_on: [ITER-007-PROPOSAL]
code: []
tests: []
iteration: ITER-007
product_goal_gate: V-000
product_goal_outcome: user-visible-general-source-qa-delta
product_goal_evaluation: independent-hidden-plus-live-ad-hoc
product_goal_result_id: not-run
---

# Iteration 007 Verification Matrix

| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |
|---|---|---|---|---|---|---|
| V-000 | 本轮相对 baseline 可测缩短通用源码问答 MVP 差距，并与既有能力完成跨域组合 | product / comparison | 未参与实现的真实工程；独立评测方/用户持有且实现阶段不可见的 held-out 自由问题；验收现场临时问题；旧+新知识跨域问题；成熟源码 Agent protocol | 支持率提高；重大错误为 0；逐题完整性不退步；提问时 Source/Update/Direct fallback=0；同一正式 Web 可人工验证 | not-run | not-run / blocking |
| V-PRE-006 | ITER-006 exact baseline 可诚实继承 | contract / product | ITER-006 Acceptance 或重新验证 Result；限制/Finding disposition | 不修改实现后沿用旧 run-008；若接受窄范围则三项限制显式进入 SLICE-001；若先修复则重新 freeze/资格/Product Validation | not-run | not-run / readiness blocking |
| V-001 | 固定 Java frontend 形成确定语法闭包 | contract / parser | exact parser/version/license/offline artifact；可见 corpus independent AST Oracle | SLICE-001 最小语法与 SLICE-002 common Java identity/range/order 一致；每单元有 disposition | not-run | not-run / blocking |
| V-002 | 方法实现语义在问题前独立形成 | update / security | exact source manifest、Build Objective、semantic Oracle、model-input audit | condition/state/return/throw/catch/call-order grounded；输入无问题/suite；tamper fail-closed | not-run | not-run / blocking |
| V-002A | no-payload 保持必要信息且不搬运源码 | security / oracle | semantic allowlist、信息保持 Oracle、信息越界/可逆性 Oracle | 目标 claims 可从 Bundle 重建；raw source/comment/token/expression text/reversible full AST 均不存在 | not-run | not-run / blocking |
| V-003 | 新 Profile 保留旧语义并正确表达 completeness | knowledge / regression | accepted ITER-006 Oracle、新 predicate/modality Oracle、完整 disposition manifest | 旧 declaration/CALLS exact rebuild 一致；新关系不扩张 CALLS；只有 COMPLETE 方法支持闭世界结论 | not-run | not-run / blocking |
| V-004 | 不点名符号的功能问题能发现正式知识 | application / capability | paraphrase；无 class/method/signature 问题；歧义/0/N 候选；operation contract | `implementation_candidates` 返回有 Support 的 typed candidates；每 Need 有合法 query 或 explicit Gap；无 enum/工程/题目/关键词补丁 | not-run | not-run / blocking |
| V-004A | 三调用模型协议与隔离边界闭合 | application / capability | exact Prompt/operation vocabulary/gateway workload/qualification | Call 1 Plan、Call 2 Draft、Call 3 independent Review；每题恰好 3 次、无 retry；deterministic validation；失败关闭 | not-run | not-run / blocking |
| V-XD-001 | `ITER-006-RESULT-ACCEPTANCE` 与 `ITER-007-SLICE-001` 在最小无符号问题中组合 | product / integration | 可见 development 工程的一条无符号名跨域题 | 一个 Need/Support chain 同时绑定旧 CALLS 与新 branch/return/throw，不是正文拼接 | not-run | not-run / blocking |
| V-XD-002 | `ITER-006-RESULT-ACCEPTANCE` 与 `ITER-007-SLICE-002` 在可见 common-Java corpus 中组合 | product / integration | 可见 qualification corpus 的独立跨域题 | 同一 Need/Support chain 组合旧 CALLS 与 condition/state/return/exception | not-run | not-run / blocking |
| V-XD-003 | `ITER-006-RESULT-ACCEPTANCE` 与 `ITER-007-SLICE-003` 在 held-out 工程中组合 | product / integration | 产品代码冻结后才披露的独立跨域题 | 同一 Need/Support chain 共同回答；任一知识缺失则 FAIL/Gap | not-run | not-run / blocking |
| V-WEB-001 | `ITER-007-SLICE-001` 通过正式 Web 执行 `V-XD-001` | product / browser | 正式产品 Web、真实已资格模型、V-XD-001 和一条 boundary | 用户可见 Profile/Coverage、答案/Gap、Citation；console clean；禁止 stub、预制答案、fixture 分支和 validation-only launcher | not-run | not-run / blocking |
| V-CANARY-001 | SLICE-001 在进入加固前通过真正隐藏的最小 Java 泛化检查 | product / independent-hidden | 独立评测方持有的小型真实 Java 工程及至少一条可回答、无符号名、组合旧 CALLS 与新实现语义的问题；身份/源码/问题在本 Slice 产品代码冻结前隐藏；exact code-freeze/project/suite digest 与披露收据 | Slice Result 匹配冻结代码和 canary 摘要，曝光后产品变更数为 0；同一正式产品链给出有证据答案，Gap 不算 PASS；未 PASS 不得进入 SLICE-002 | not-run | not-run / blocking |
| V-WEB-002 | SLICE-002 加固后从同一正式 Web 复验 | product / browser | 5 条自由问题，至少 2 条无符号名，覆盖四类源码问题 | 全部给证据答案或正确 Gap；严格三调用；无 fallback | not-run | not-run / blocking |
| V-CANARY-002 | SLICE-002 在进入最终 held-out 验证前通过隐藏 common-Java 泛化检查 | product / independent-hidden | 独立评测方持有的 common-Java 小型真实工程及至少一条可回答无符号问题；身份/源码/问题在本 Slice 产品代码冻结前隐藏；exact code-freeze/project/suite digest 与披露收据 | Slice Result 匹配冻结代码和 canary 摘要，曝光后产品变更数为 0；同一正式产品链给出有证据答案，Gap 不算 PASS；未 PASS 不得进入 SLICE-003 | not-run | not-run / blocking |
| V-WEB-003 | SLICE-003 在正式 Web 执行冻结 held-out 产品验证 | product / browser | 两个 held-out 工程、12+4 问题与 `V-XD-003` | hidden 和跨域 Case 均走同一产品 Web；答案/Gap/Citation 可人工检查；无 fallback | not-run | not-run / blocking |
| V-005 | Source-off restart 可答且问题不改权威状态 | isolation / security | repository、Source、authority DB、Evidence Store denied | 支持/Gap 正常；Source Operation、Update Attempt、Direct Attempt delta=0 | not-run | not-run / blocking |
| V-006 | R1→R2 在零问题状态更新并可重启 | update / integration | 两个 exact revisions 与一个 invalid revision | 旧 Session 固定 R1；有效 R2 可用；无效 R2 保持旧 CURRENT/Bundle | not-run | not-run / blocking |
| V-007 | 两个未参与实现工程的隐藏自由题有实质增量 | product / comparison | 12 answerable + 4 boundary；至少 6 条 answerable 无符号名；exact digests/target | answerable supported ≥ `min(12,max(baseline+4,8))`；两工程/四类均增量；boundary 4/4；Gap 不计支持 | not-run | not-run / blocking |
| V-007A | held-out 没有被实现污染 | isolation / product | disclosure log、code freeze digest、project/suite digests | 冻结前实现方看不到项目身份/源码/题目；曝光后若改产品，失败保留且工程+问题同时更换 | not-run | not-run / blocking |
| V-008 | 世界模型支持答案不低于成熟源码 Agent 且旧能力不退步 | product / regression | 同 revision/source/resource protocol 与 ITER-003—006 accepted regression | supported answer 逐题正确性/完整性不低；Agent 可答而模型 Gap=FAIL；成本完整披露 | not-run | not-run / blocking |
| V-ADHOC-001 | `ITER-007-SLICE-003` 通过正式 Web 接受现场临时问题并覆盖 `V-XD-003` | product / browser | 3 条现场题；至少 2 条无符号名；含 answerable 跨域与真实 boundary | answerable 给证据答案；boundary 给诚实 Gap；无 fallback | not-run | not-run / blocking |
| V-009 | 本机 PASS 不产生 Production Activation | activation | exact Iteration Result | `NOT_EXECUTED` | not-run | not-run / blocking |

## 计数与冻结规则

- 12 条 answerable 是 supported count 的唯一分母；4 条 boundary 单独计量，Gap 不能计入 supported。
- target 在 Readiness 前由独立方运行当前 baseline 后冻结，至少为 `min(12, max(baseline + 4, 8))`。
- boundary 必须由独立 Oracle 证明同一授权 Java 源不足；若成熟源码 Agent 能回答，World Model Gap 直接 FAIL。
- `V-CANARY-001/002` 分别是 SLICE-001/002 的独立隐藏阻断 Gate，不属于最终 12+4 计数，也不得复用为最终 held-out 工程。
- 每个 canary 的身份、源码和问题在所属 Slice 产品代码冻结前隐藏；曝光后任何产品改动都保留失败并烧毁该 canary，只能换全新
  工程和问题后重试。任一 canary 未 PASS 时禁止进入下一 Slice。
- held-out 项目身份、源码和问题在产品代码冻结前都对实现方隐藏。曝光后任何产品变化都会烧毁项目和 suite，重试必须同时换新。

当前 Matrix 只是计划，不是执行证据。Readiness 前必须填入 exact frontend、可见 corpus、held-out 工程/suite、baseline、target、
三调用协议、Agent protocol、source scope 和全部 digest；每个 Slice 完成时，其全部 Gate Case 必须逐项绑定该 Slice Result Evidence。
最终 Product Result 只聚合并依赖三个 Slice Result，不覆盖逐 Case Evidence。
