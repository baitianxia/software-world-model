---
id: ITER-010-PROPOSAL
kind: iteration-proposal
status: accepted
authority: project-proposal
owners: [product, project, architecture, engineering, quality]
depends_on: [SYS-PRODUCT-SUCCESS, ROADMAP-M-002, ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST, ITER-006-RESULT-ACCEPTANCE, ITER-009-RESULT-SLICE-001-STOP-REDIRECT, SYS-ADR-013, SYS-ADR-014, SYS-ADR-015, SYS-ADR-016, SYS-CONTRACT-AI-CAPABILITY-EVALUATION, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-KNOWLEDGE-JAVA-SOURCE-SEMANTICS, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-QUALITY-SECURITY, SYS-OPS-LOCAL-BROWSER]
code: []
tests: []
iteration: ITER-010
coding_input: false
---

# ITER-010 Proposal：让系统回答工程问题，代码作为证据而不是正文模板

## Trigger and evidence

`ITER-009-RESULT-SLICE-001-STOP-REDIRECT` 证明真实本机 Web、精确版本、独立审核、Limitation 和 Citation 已经能够组成可运行链路；
同时也证明其三条现场回答都被方法、分支、静态调用、源顺序和返回值主导。即使用户没有询问实现细节，答案仍像代码走读；Reviewer
没有把“是否直接回答用户真正的问题、抽象层级是否合适”作为阻断条件。继续原加固计划只会稳定错误方向。

用户进一步指出，工程问题不能因为 `WORLD_MODEL` 的 Source-off 验证目标而拒绝在提问时读取源码。用户随后明确接受以下新边界：

- World Model 是可复用的工程地图、手册和调查入口，不是每道问题唯一允许的事实来源；
- LLM 像高级工程师一样理解问题、控制调查和综合答案，但不是事实权威；
- exact revision 下授权的源码、仓库文档、构建配置和测试是丰富并核实回答的手段；
- 密封 Evidence Package 才拥有本题事实权威，Answer 与 Reviewer 只能读取该包；
- 严格 `WORLD_MODEL` 模式继续保留原 Source-off 语义，新默认能力使用显式 `ENGINEERING_QA`，不是静默 Direct fallback。

这是一项架构边界变更，而不是 Prompt 文风修补。原 `SYS-PRODUCT-SUCCESS`、`SYS-ADR-014`、`SYS-ADR-015` 和
`SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING` 把通用 Web 目标及 `WORLD_MODEL` 限定为提问期 Source-off。本次环境准备已先建立
`FINDING-010-001`，新增 `SYS-ADR-016` 与 `SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING`，并同步更新 owning
Product/Contract/运行流程/安全/浏览器/治理文档。Slice1 从该已闭合 current 边界开始开发，`V-ARCH-001` 负责在代码变化前后持续复核，
不能在 Prompt 或实现中再次混淆三种模式。

## Product-goal alignment and cumulative delta

- MVP target reference：`SYS-PRODUCT-SUCCESS`；Slice1 会先把默认通用工程问答与严格 `WORLD_MODEL` 评测模式的关系写回该目标。
- Capability path reference and current step：`ROADMAP-M-002 / step-1-java-result-driven-world-model-investigation`；本轮仍解决同一最早阻断，
  但从“Snapshot 是同步回答唯一来源”转向“预构建模型优先引导、提问期受控核实”的显式混合主路径。
- Accepted predecessor evidence：`ITER-006-RESULT-ACCEPTANCE` 提供 exact Snapshot、声明与静态 `CALLS`、Citation 和本机 Web 基线；
  `ITER-009-RESULT-SLICE-001-STOP-REDIRECT` 提供真实方向反证，不提供 Acceptance。
- Current product gap and real-question evidence：系统能展示源码行为，却不能按用户目的和期望层级直接回答工程问题；知识范围又受
  Source-off Bundle 限制，导致用途、运行、故障、配置、影响等问题容易退化为代码走读或内部 Limitation。
- Accepted capabilities reused：Workspace/exact revision、问题前 World Model、no-payload Snapshot、typed Result、Citation、只读来源、
  Model Gateway、独立 Review 和 loopback Web。
- New capabilities integrated into the same answer chain：问题理解、预构建 World Model 与提问期隔离检索合并成一个密封 Evidence
  Package、结论优先答案、层级匹配审核、受控补检索、同包最多一次重写及异步知识沉淀。
- Evaluator/user-owned hidden held-out before/target counts：最终两个未参与实现的真实工程，10 条 answerable + 2 条 boundary；问题和工程
  在产品代码冻结前由用户持有，baseline/target 在披露时同批密封。
- Cross-domain questions combining old and new knowledge：每个 Slice 至少一题在同一答案中组合 ITER-006 的预构建 declaration/`CALLS`
  与本轮检索到的源码、文档、配置或测试证据，不允许平行答案入口。
- Earliest product-owned Web checkpoint and live ad-hoc questions：`SLICE-001 / V-WEB-001` 是最早真实入口，使用一个真实工程 4 条跨类型
  问题和至少一条用户现场题；最终 `SLICE-003 / V-ADHOC-001` 再接收两条冻结后现场题。
- Minimum direction-preview checkpoint, representative tasks and explicit non-goals：`V-PREVIEW-001` 只判断“是否开始像工程问答助手”，
  不声称跨工程泛化、生产可用、完整知识覆盖或正式 Acceptance。
- Direction decision owner and allowed outcomes before hardening：用户拥有 `CONTINUE / REDIRECT / REJECT`；没有新的 `CONTINUE` Result 和
  后续授权，`SLICE-002` 不得执行。
- End-of-iteration user-visible Web capability：普通用户无需认证即可在本机 Web 自由询问工程用途、架构、运行使用、业务流程、配置、
  故障、变更影响和实现细节，获得层级匹配、证据支持的答案或诚实 unknown/limitation，并核对结论级 Citation。
- Next blocking gap after success：第二语言、跨仓库关系、大型单体性能、持续后台知识更新和非本机受控部署。
- Stop / redirect conditions：系统仍默认输出方法/分支走读；需要题目、工程、关键词、类名或方法名路由；Question Understanding 改写用户
  意图；Answer/Reviewer 能直接读 repo；Citation 不支持结论；补检索无界；错误或遗漏；安全/授权失守；或用户决定转向/拒绝。

## Critical assumptions and falsification plan

| 假设 | 最早证据与反证 | 反证后的动作 |
|---|---|---|
| A1：显式 ENGINEERING_QA 可以在保留严格 WORLD_MODEL 模式的同时，把预构建 World Model 与提问期 exact-revision 只读检索定义为一个无静默 fallback 的主路径 | SLICE-001 的 V-ARCH-001 与 V-HYBRID-001；若 ADR、Contract、权限和审计不能明确区分两种模式，或实现必须伪装成 WORLD_MODEL/DIRECT 切换，则反证 | REDIRECT 架构边界；停止产品实现，不在 Prompt 或接口中隐藏模式切换 |
| A2：通用 Question Understanding 和密封 Evidence Package 能让跨类型答案优先回应用户目标与抽象层级，而不是默认生成代码走读 | SLICE-001 的 V-QINTENT-001、V-ANSWER-001、V-PREVIEW-001；若 4 条跨维度任务仍以代码事件为正文，或只有题型/关键词/工程规则才能改善，则反证 | REJECT 特判；REDIRECT 问题理解、证据组织或答案合同中的首次系统性偏差 |
| A3：隔离检索、Answer/Reviewer 无源码权限、结论级 Citation、具体审核 Finding 与诚实 limitation/fail-close 可以同时保持首版正确性和安全边界 | SLICE-001 的 V-ISOLATION-001、V-REVIEW-001、V-LIMIT-001、V-SEC-001；出现无依据结论、无关引用、越权读取、审核降级或资源耗尽后放行即反证 | 停止体验；按首次偏差修复授权、Evidence Package、Response Control 或 Reviewer，不以减少检查换取交付 |
| A4：相同协议以及有界 rewrite/reretrieval 生命周期可以在第二个未参与实现的真实工程和不同来源组合上泛化，不依赖问题、项目、关键词、符号、fixture 或 Oracle 路由 | SLICE-002 的 V-RERETRIEVE-002、V-CANARY-002、V-GENERAL-002、V-XD-002；修复不收敛，或任一新工程/新表达必须新增特殊分支或同类问题回到代码走读即反证 | REDIRECT 到通用表示、检索或审核层；烧毁暴露输入并保留失败 Result |
| A5：在不因调用次数削减调查或审核质量的前提下，混合链相对成熟源码 Agent 保持零重大错误、逐结论不退步并证明预构建 World Model 的可测复用价值 | SLICE-002 的 V-COMP-EARLY-002 提前验证，SLICE-003 的 V-COMP-001、V-HIDDEN-003 与现场题最终裁决；质量退步或预提交价值阈值未达即反证 | REDIRECT 或 REJECT；不取消独立审核、不压缩证据清单、不把安全上限改成质量配额 |

第一段验证 A1—A3，并用 `V-XD-001` 与 `V-SEC-001` 提前暴露 A4/A5 的明显反证；第二段累积验证 A1—A4，并以成熟源码 Agent
对照提前验证 A5；最终段按原顺序覆盖 A1—A5。调用次数不是质量目标；只有 wall time、bytes、文件数、模型调用和补检索轮次的高安全
上限，触发后失败关闭，不删除问题清单、证据需求、Citation 或独立审核。

## Outcome and users

首要用户是希望理解或维护一个陌生工程的普通开发者。他不需要选择内部模式、填写类名或学习 Profile/authority/candidate 等代号。
系统先识别其目标、受众、抽象层级、必须回答的结论和证据需求，再以预构建 World Model 作为工程地图，同时从同一授权 exact revision
只读检索必要的源码、仓库文档、构建配置和测试，形成一个密封证据包。最终页面先展示答案；诊断、调用数、Read Set 和内部 Trace
折叠到开发者详情。

LLM 拥有问题理解、调查提议、答案综合和审核判断，不拥有事实。Application 拥有 allowlist、exact revision、来源操作、预算、密封、
重检索授权和最终交付；Evidence Package 拥有本题事实权威。高质量证据与结论可在回答完成后异步提议知识更新，但同步回答不等待其
Admission/Publication。

## Scope / non-goals

本轮范围是 loopback、普通用户无认证、一个统一 `ENGINEERING_QA` Web 入口、授权本地 Git exact revision、Java 工程，以及源码、
仓库内文档、构建/运行配置和测试。第一段只实现架构闭合与最小方向体验；第二段补齐跨工程、来源组合、资格、安全、性能与回归；
第三段执行正式隐藏与现场验收。

不包括公网服务、Production Activation、团队权限、多用户隔离、远程仓库写入、任意 shell、工程修改、第二语言、跨仓库知识、长期
Memory 或同步正式知识生产。严格 `WORLD_MODEL` Source-off 入口保留用于模型复用和隔离验证，不作为 `ENGINEERING_QA` 的静默降级或
兜底。`DIRECT_INVESTIGATION` 也保留为显式模式；新模式不会看到缺证据后临时换标签调用它。

## Adopted system IDs

当前设计输入包括：

- `SYS-PRODUCT-SUCCESS`
- `SYS-ADR-013`
- `SYS-ADR-014`
- `SYS-ADR-015`
- `SYS-ADR-016`
- `SYS-CONTRACT-APPLICATION-AGENTIC-TASK`
- `SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING`
- `SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING`
- `SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING`
- `SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE`
- `SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE`
- `SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL`
- `SYS-CONTRACT-AI-MODEL-GATEWAY`
- `SYS-CONTRACT-AI-CAPABILITY-EVALUATION`
- `SYS-CONTRACT-SOURCE-ARTIFACT`
- `SYS-OPS-LOCAL-BROWSER`
- `SYS-QUALITY-SECURITY`

本次环境准备已通过 `FINDING-010-001`、新 `SYS-ADR-016` 和
`SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING` 正式授权该边界，并同步更新 Product Success、runtime flow、Agentic Task、
Evidence/World Model Answering、Response Control、Source、安全、Browser 与治理检查器/测试。Manifest/Readiness 绑定更新后的 exact
Contract fileset。Slice1 只在该 current 语义上实现，`V-ARCH-001` 持续阻断任何 Contract/code 漂移。

## Development slices and dependencies

1. `SLICE-001`：架构一致性与真实方向体验。从已闭合的 Finding/ADR/Contract/治理门禁开始复核，再实现 `ENGINEERING_QA` 最小混合链、本地确定性测试、
   一个真实工程 4 条跨类型问题和至少一条现场题。真实 Web 另行授权，结束时由用户决定 `CONTINUE / REDIRECT / REJECT`。
2. `SLICE-002`：通用化与跨工程夯实。仅在前一 Result 为 `CONTINUE` 且取得新授权后，完成第二工程、来源组合、受控补检索、异步沉淀
   边界、early hidden canary、成熟源码 Agent 对照、资格、安全和回归；结束时再次作方向决定。
3. `SLICE-003`：正式验收。仅在第二段 `CONTINUE` 后冻结产品代码，执行最终两个隐藏工程 10+2、两条现场题、逐题对照、价值/成本/时延、
   安全和最终 Reflection；只有用户新 `ACCEPT` 才形成 Acceptance。

每段都在同一个 product-owned Web 入口验证，不允许 validation-only 平行入口。首段方向体验不是 Acceptance，后续加固也不能倒置到
首段之前。

## Risks and unknowns

- 新默认模式改变已接受的 Source-off 产品边界；最危险的失败是系统文档与代码身份不一致，因此架构变更先于实现。
- 提问期源码检索扩大了 prompt injection、敏感内容外发、路径越界和资源消耗面；必须以 exact allowlist、只读 OS/应用隔离、操作审计、
  包密封和 role separation 控制。
- World Model 与实时检索可能冲突；Evidence Package 必须记录来源 identity、revision、时间和 provenance，并定义冲突时不能静默选取。
- Question Understanding 可能把用户问题重新解释成方便回答的问题；原问题和全部约束必须不可变，Reviewer 从原问题重建清单。
- 受控补检索可能退化为无界 Agent 循环；只允许 Reviewer 给出具体证据缺口后由 Application 决定的一轮新包，达到高安全上限失败关闭。
- 答案变自然可能掩盖错误；每个物质结论必须绑定包内 Evidence，unknown/limitation 不得暗示完整性或不存在。
- 混合路径比直接源码 Agent 更复杂；必须证明预构建模型的复用价值，否则即使质量持平也不能接受。

## Verification and acceptance

`SLICE-001` 先以 `V-ARCH-001` 证明新模式有正式 Owner 和机械边界，再用本地确定性 Case 证明问题理解、双来源 Evidence Package、角色
隔离、结论级 Citation、具体 Review Finding 和安全熔断；Review 未通过时允许诚实失败关闭，不要求首版先完成完整重写/补检索矩阵。
取得独立 live grant 后，从真实 Web 对一个真实工程执行 4 条覆盖不同维度的自然问题，加至少一条现场题；至少 3 条 supported，覆盖
至少 2 个非实现维度，其余必须形成准确、可理解的 unknown/limitation。用户只裁决产品方向。

`SLICE-002` 在第二真实工程执行 early canary 5 answerable + 2 boundary，证明无特判、受控补检索、不同来源组合、安全、当前资格和回归，
并与成熟源码 Agent 比较。`SLICE-003` 执行最终两个隐藏工程 10 answerable + 2 boundary、两条现场题和逐题比较。

最终要求重大错误为 0、answerable 10/10 supported、boundary 2/2 正确、每个实质结论有真实 Citation、逐结论完整性不低于成熟源码
Agent、预提交 World Model 复用价值阈值 PASS、源码读取只发生在授权 retrieval worker、Answer/Reviewer source access=0、Update/
repository write/静默 fallback=0、Production Activation=`NOT_EXECUTED`。资源上限不能成为删减审核或交付未审核答案的理由。

## Authorization decision

**ACCEPTED FOR SLICE-001 DEVELOPMENT ONLY。** 用户先以
`codex-user-message:sha256:1b3270242962b8d099ac9166304dc6188be22054cfc2a685b2ade5616d4cc2f4` 要求准备下一迭代环境，随后以
`codex-user-message:sha256:5cdb7000ba36328f5caa27727c6b689ad4e98e7ad13eca72837fa020d0c270c9` 于
`2026-08-21T07:10:28Z` 明确接受 `ENGINEERING_QA` 混合证据架构。因此接受 Proposal/Readiness 并只授权 Slice1 的 System 文档、治理、
产品代码和本地确定性测试。

该授权不允许 credential、Provider/model dispatch、正式 live Web/browser question、隐藏输入披露、`SLICE-002/003` 或 Production。
