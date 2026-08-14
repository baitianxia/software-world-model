---
id: ITER-008-PROPOSAL
kind: iteration-proposal
status: proposed
authority: project-proposal
owners: [product, architecture, engineering, quality]
depends_on: [SYS-PRODUCT-SUCCESS, ROADMAP-M-002, ROADMAP-CANDIDATE-BOUNDED-WORLD-MODEL-INVESTIGATION, ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-ACCEPTANCE, ITER-007-RESULT-SLICE-001-STOP-DECISION, FINDING-007-008, FINDING-007-009, SYS-ADR-014, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-APPLICATION-AGENTIC-TASK, SYS-QUALITY-SECURITY, SYS-QUALITY-ACCEPTANCE, SYS-OPS-LOCAL-BROWSER]
code: []
tests: []
iteration: ITER-008
coding_input: false
---

# ITER-008 Proposal：受限 Agent 驱动的 World Model 调查问答

## Trigger and evidence

ITER-007 run-004 已经证明问题所需的登录方法和实现语义进入了 World Model，模型调用、正式 Web、隔离与 Citation 也都成功。
产品仍失败，因为固定管道要求先唯一选择一个方法，不能根据结果继续调查其他方法；对源码中不存在的下单功能，候选查询又返回了
无关登录方法，无法形成可靠的负向结论。

因此本轮不继续增加 Java 语义类型，也不改名或转做“源码 Agent”。它先修复 `ROADMAP-M-002` 最早未证明的 Step 1：让受控 Agent
在 World Model 内进行多步、结果驱动的调查，验证现有正式知识是否足以回答通用源码问题。

## Product-goal alignment and cumulative delta

- MVP target reference：`SYS-PRODUCT-SUCCESS`。
- Capability path：`ROADMAP-M-002 / step-1-java-result-driven-world-model-investigation`；ITER-007 是同一步骤的首个失败方案，
  本轮是 redirect，不跳步。
- Accepted predecessor evidence：`ITER-005-RESULT-ACCEPTANCE`、`ITER-006-RESULT-ACCEPTANCE`。
- Failure evidence reused：`ITER-007-RESULT-SLICE-001-STOP-DECISION`、`FINDING-007-008/009`，但这些不是 accepted capability。
- Current gap：World Model 已有相关事实，问答协议却不能跨候选、跨方法继续调查，也不能分别证明查询、表示和业务发现三层完整性。
- End-of-iteration Web capability：用户无需写类名或方法名，即可从正式 Web 获得基于预构建 World Model 的多方法实现流程答案；
  三层完整时获得有界不存在结论，不完整时获得具体 Limitation。
- Measurable delta：两个代码冻结前未见的小型真实 Java 工程，共 4 条 answerable、2 条 boundary；至少 2 条需要多方法组合、至少 3 条
  不含类名/方法名；逐题不低于成熟源码 Agent，重大错误为 0，并达到编码前冻结的 World Model 正向差异化价值阈值。
- Cumulative composition：同一答案的 Support chain 必须组合 ITER-006 已接受的 declaration/`CALLS` 与 ITER-007 待重新验收的
  condition/return/throw 等实现语义。
- Earliest Web checkpoint：`SLICE-001` 结束即从现有正式产品 Web 人工提问并执行全新早期 canary；`SLICE-002` 结束再次从同一 Web
  执行最终隐藏题与现场题。CLI、View 或 validation launcher 均不能替代。
- Next blocking gap after success：`ROADMAP-M-002` Step 2 的常见 Java 语法、跨类、多文件与真实框架工程广度。

## Critical assumptions and falsification plan

| 假设 | 最早证据与反证 | 反证后的动作 |
|---|---|---|
| A1：ITER-007 的主要问题是查询/编排，而不是已有知识表示缺失 | SLICE-001 登录回归、early canary 与 `V-DIAG-001` 逐层定位；若关键事实未进入 Snapshot 才判表示缺口，已进入但不可查询才判 Query API 缺口 | `REDIRECT`，停止查询层加固，回到同一 Roadmap Step 修正被证伪的精确层 |
| A2：受限 Agent 只用 typed World Model 查询即可跨多个方法形成完整 Support | SLICE-001 无符号多方法题；若必须读源码、原始 Evidence 或无界展开才可回答，则反证 | 若 typed 查询仍有可验证替代则 `REDIRECT`，否则 `REJECT`；禁止 Source/Direct 补丁 |
| A3：最小调查闭环在冻结步数、调用、query/result 字节、总时延、Support/trace 和成本预算内可用 | SLICE-001 公开题和 early canary 的实测预算；至少允许两个结果驱动调查回合，最小题仍耗尽预算或 P95 不可体验即反证 | 若能明确改换查询粒度/协议则 `REDIRECT`，否则 `REJECT`；不得进入完整性加固 |
| A4：对不存在或未覆盖功能，系统不会制造无关证据，并能诚实区分 Gap 与 Limitation | SLICE-001 下单回归与包含命名/同义词/不同入口反例的 boundary canary | 无关支持或伪不存在结论直接 `REJECT`；完整性缺口则 `REDIRECT` |
| A5：该方案相对成熟源码 Agent 不会产生实质正确性或完整性退步 | SLICE-001 先做 early canary 同题密封对照；SLICE-002 再做最终 4+2 逐题对照 | 已有明确替代路线则 `REDIRECT`，否则 `REJECT`；不把差距推迟到最终验收 |
| A6：World Model 除了“不退步”，还能达到编码前冻结的至少一项正向差异化价值阈值 | Readiness 先冻结指标、阈值、复用周期和源码 Agent 缓存政策；SLICE-001 1+2 同题对照即测早期值，SLICE-002 用最终问题复核 | 未达阈值即 `REDIRECT/REJECT`；不得用事后改指标、审计口号或仅报告成本替代价值证明 |
| A7：查询、表示和业务发现三层完整性在扩展反例矩阵中仍可分别由独立 Oracle 证明 | SLICE-001 的最小闭包只作早期反证；SLICE-002 才对完整矩阵下最终 Verdict | 早期反证立即 `REDIRECT`；最终不能证明则 `REDIRECT/REJECT` |
| A8：加固后的最终评测仍走同一正式 Web 产品链，没有测试/评测平行捷径 | SLICE-001 Web 只作早期反证；SLICE-002 以最终 hidden、现场题、audit 与 Source-off 下最终 Verdict | 任一不同链路或 fallback 直接 `REJECT` |

`SLICE-001` 只对已经到期的 A1—A6 下正式 Verdict；A7/A8 的早期 Case 仍是阻断反证，但不能被写成已经最终证明。
若 `V-NEG-EARLY-001` 或 `V-WEB-001` FAIL，阻断 Result 必须分别追加 A7 或 A8 的结构化 `FALSIFIED/UNRESOLVED` 行并引用该 Case；
`SLICE-002` 必须重新复核 A1—A6，并对 A7/A8 下最终 Verdict，因此最终 Reflection 覆盖 A1—A8。任何 `CONTINUE/ACCEPT`
都要求该段绑定的假设全部为 `SUPPORTED`。

每个 Slice 都必须在产品 Gate 后形成方案复盘 Result。中间段只有 `V-REFLECT-001 PASS + reflection_decision: CONTINUE` 才取得
申请下一段授权的资格；最终段只有 `V-REFLECT-002 PASS + reflection_decision: ACCEPT` 才可申请本轮 Acceptance。Reflection PASS
只表示复盘做完，不表示方案本身正确。

SLICE-001 还必须用 `V-DIAG-001` 冻结同一问题的逐层诊断链：Source ground truth → Snapshot atom/Coverage → typed-query
reachability → investigation trace use → Draft/Review → Web delivery。失败归因必须落到首次发生偏差的层，不能只凭“源码 Agent 能答、
World Model 没答”猜测是表示或 Agent 问题。

## Outcome and users

用户先在没有任何问题输入的状态下，对授权 Local Git revision 构建 exact Snapshot。随后源码访问关闭，用户在正式 Web 输入自由
Java 实现问题。系统执行下面的受限调查链：

```text
Question
  → immutable Needs
  → Agent 提议一个 typed World Model 查询
  → 平台校验并执行
  → Agent 根据 typed result 决定继续查询或结束
  → sealed investigation trace
  → Draft
  → independent Review
  → Web Delivery + Citation
```

Agent 可以查询多个候选、方法实现、声明清单、邻接关系、路径和 Coverage，不再要求先唯一选择一个方法。平台仍拥有 exact
Snapshot、操作白名单、typed Ref、Support、预算、授权和失败关闭。回答中的事实只能来自 World Model；Citation 可以在交付后向
用户展示原始位置，但回答 Agent 不得读取源码正文。

“不存在该功能”不是关键词判断，也不能由分页结束直接推导。系统必须分别证明：查询结果完整性（没有未读取页或截断结果）、知识
表示 Coverage（授权单元均有明确 disposition）和业务语义发现召回完整性（相关实现不会因命名、同义词或不同入口漏检）。三层均
有独立 Oracle 时才可给出有界负向结论；任一层不足都必须返回具体 Limitation。

## Adopted system IDs

继续采用 `SYS-PRODUCT-SUCCESS`、`SYS-ADR-014`、`SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE`、
`SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE`、`SYS-QUALITY-SECURITY`、`SYS-QUALITY-ACCEPTANCE` 和
`SYS-OPS-LOCAL-BROWSER`。

Readiness 前必须新增一项正式架构决策并修订 `SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING`、
`SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY`、`SYS-CONTRACT-APPLICATION-AGENTIC-TASK`、runtime flow、Gateway 与 Capability
Evaluation。当前固定“每题恰好三次模型调用”的规范不能直接支撑结果驱动调查，不能只改实现绕过 Contract。

新架构决策必须明确拒绝：直接取排名第一的方法、一次性无界展开所有候选、以及让回答 Agent 读取源码的 Direct fallback。

## Development slices and dependencies

### SLICE-001：最小调查闭环与早期正式 Web Gate

先做足以验证架构的最小闭包：bounded investigation Contract、至少两个结果驱动调查回合、多个候选/方法的结果驱动查询、query/result/时长/Support/trace 平台预算与禁止面、sealed trace、
Draft/Review/Citation 和正式 Web。公开登录题必须形成多方法答案；下单题至少不得生成无关登录支持，若三层完整性尚未闭合则必须
诚实返回 Limitation。

产品代码冻结后，再由用户或独立方披露一份全新小型真实 Java 工程及至少 1 条无符号多方法 answerable 和 2 条 boundary 问题。
两个 boundary 必须分别覆盖“完整最小闭包可证明 bounded absence”和“Coverage 不完整只能给 Limitation”，并含命名/同义词/不同入口
反例；最小闭包若不能证明前者，A4 当场被证伪，并同时构成 A7 的早期反证。
成熟源码 Agent 必须先在同 revision、同问题和冻结的等价资源上限下运行并密封结果，再运行 World Model；Agent 可答而 World Model
Gap、发生任何重大错误或逐 Need/Claim 退步时不得进入下一段。正式 Web/canary、early absence/diagnostic Gate 与 Agent 对照通过后，
还必须完成 `V-REFLECT-001` 方案复盘并决定
`CONTINUE`，才允许由用户另行授权 SLICE-002。任何内部组件、确定性测试或公开 LoginService PASS 都不能替代这一早期 stop Gate。

### SLICE-002：完整性加固与最终产品验证

只在 SLICE-001 PASS 后加固 pagination/total/truncated、三层完整性、cycle/progress、预算、安全与独立 Review，再执行两个最终
隐藏工程的 4 answerable + 2 boundary、成熟源码 Agent 对照和 2 条现场题。两条现场题中至少一条既不含符号名，又必须在同一
Support chain 组合 accepted `CALLS` 与本轮重新验收的实现语义。

两个 Slice 都是纵向产品切片，不按 Planner、查询工具、Web 或评测等内部组件拆分；每段都必须以正式 Web 人工体验结束。

## Scope / non-goals

本轮固定在 ITER-007 已声明支持的 Java Source Semantics 闭包内，验证查询架构，不扩大 parser、Schema 或框架语义。每段隐藏工程
都必须在对应代码冻结前由独立方确认落入该闭包；若仍暴露表示缺口，该 Slice 按 FAIL 保留，并把证据用于 Step 2，而不是看到
工程后修改产品。

本轮不包括：

- README、ADR、配置、部署或运行数据的多源问答；
- 常见 Java 全语法、动态分派、Spring 运行时拓扑或第二语言；
- 通用自治 Agent、插件平台、工作流引擎或长期 Agent Memory；
- 提问触发 Knowledge Update、源码读取、Evidence payload、Direct fallback；
- Production Activation 或公网部署。

## Risks and unknowns

- 当前 Query API 的 limit/truncated 语义可能不足以证明穷尽，需要先形成分页、总量和 Coverage Contract；
- 自适应调查会增加调用次数与时延，Readiness 必须冻结最大步数、模型调用、结果字节、总时长和失败语义；
- 如果世界模型表示本身缺少答案，Agent 循环不能制造事实；该情况必须作为产品 FAIL 暴露，而不是扩预算掩盖；
- Reviewer 不能只检查格式，还必须发现漏查关键候选、无依据负向结论和 Support 不完整；
- 已公开的 LoginService 不能再作为隐藏泛化证据。
- 若只在最终 4+2 才与源码 Agent 对照，仍会重复“开发很久后才发现价值不成立”；因此 SLICE-001 必须先做小规模同题对照和方案复盘。

## Verification and acceptance

公开回归必须先关闭两个已知反例：

- “登录流程”：答案组合 `authenticate`、两次 `recordFailure()`、异常路径和 `issueSession()` 成功路径；
- “下单流程”：不得把登录方法当作支持证据；只有 Coverage 足够时才说明当前授权源码没有下单实现，否则给具体 Limitation。

SLICE-002 产品代码冻结后，由用户或独立评测方披露两个未参与实现、也未用作早期 canary 的小型真实 Java 工程及 4+2 自由问题。
成熟源码 Agent 在 World Model 结果产生前先按同 revision、同问题和等价资源上限运行并密封答案。Readiness 必须先冻结逐
Need/Claim 评分表、重大错误定义、独立裁决人、争议/同分/失败规则，并把 World Model 建模成本、单题问答成本、多题摊销成本与
源码 Agent 调查成本分开统计。World Model 路径必须满足：

- 4 条 answerable 全部给出 supported answer，2 条 boundary 全部正确；
- 至少 2 条多方法题和 3 条无符号名题通过；
- 重大错误为 0，逐题正确性与完整性不低于成熟源码 Agent；
- Agent 可答而 World Model 返回 Gap，直接 FAIL；
- 提问阶段 Source、Update、Direct fallback 全部为 0；
- 同一正式 Web 再接受 2 条现场题，至少 1 条不含符号名且执行 `V-XD-002` 的跨域组合；
- Production Activation 为 `NOT_EXECUTED`。

立即停止并判定产品 FAIL 的条件包括：登录题仍因多候选拒答、不存在功能仍产生无关支持、出现题目/工程/关键词/符号补丁、需要
读取源码或触发更新、正式 Web 与测试走不同链路、最小多方法题耗尽预算、成熟源码 Agent 能答而 World Model 明显遗漏，或证据表明
缺失的是知识表示而不是查询方式。

## Authorization decision

**PROPOSED / NOT READY / NOT AUTHORIZED。** 本 Proposal 只确定 ITER-008 内容。不得在新的架构决策、Contract、exact baseline、
调查预算、隐藏评测协议、机械门禁和用户 Readiness Acceptance 闭合前修改产品代码。
