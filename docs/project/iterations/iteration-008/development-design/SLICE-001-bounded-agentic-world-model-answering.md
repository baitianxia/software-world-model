---
id: ITER-008-SLICE-001
kind: development-slice
status: authorized
authority: current-development
owners: [engineering, architecture, quality, product]
depends_on: [ITER-008-PROPOSAL, ITER-008-READINESS, ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-ACCEPTANCE, ITER-007-RESULT-SLICE-001-STOP-DECISION]
code: [src/software_world_model/application_services, src/software_world_model/knowledge_engine, src/software_world_model/ai_infrastructure, src/software_world_model/interface]
tests: [tests, validation]
iteration: ITER-008
coding_input: true
product_goal_gate: V-000
product_goal_accepted_capability_refs: [ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-ACCEPTANCE]
product_goal_cross_domain_case_ids: [V-XD-001]
product_goal_web_checkpoint_id: V-WEB-001
product_goal_reflection_gate_case_id: V-REFLECT-001
product_goal_slice_gate_case_ids: [V-001, V-002, V-003, V-004, V-XD-001, V-SEC-001, V-SOURCEOFF-001, V-WEB-001, V-CANARY-001, V-NEG-EARLY-001, V-DIAG-001, V-COMP-EARLY-001, V-REFLECT-001]
---

# SLICE-001：最小调查闭环与早期正式 Web Gate

## Status and dependencies

`AUTHORIZED / CURRENT DEVELOPMENT`。用户消息 `codex-user-message:sha256:eb381cfd…7221` 接受 ITER-008 Readiness 并只授权本 Slice。
Manifest 已冻结 baseline `38ebed2…`、`SYS-ADR-015`/System Contract fileset、2—4 次调查 + Draft/Review 的预算、隐藏评测协议、
成熟源码 Agent/rubric 与正向价值阈值。本 Slice 是唯一活动编码输入；live disclosure 和 SLICE-002 仍需后续独立授权。

## Product-goal contribution and cumulative integration

- Product gap shortened：把“有相关正式知识但固定单方法协议无法回答”推进为“Agent 只查询 World Model，也能完成多方法自由问答，
  并在不能证明不存在时返回正确 Limitation”。
- Product capability-path step advanced：`ROADMAP-M-002` Step 1，从 ITER-007 rejected 方案转向结果驱动调查。
- Existing capabilities combined：ITER-005 的 Workspace/Update/Web/Citation 与 ITER-006 的 declaration/`CALLS`。
- User-visible Web questions at slice end：登录/下单公开回归、`V-XD-001`，以及代码冻结后才披露的全新 early canary（至少 1 条
  无符号多方法 answerable + 2 条互补 boundary）全部走同一正式 Web。
- Slice stop / redirect signal：任何 Agent 读源码、问题驱动更新、关键词特判、无关支持、early canary 失败、预算无法支撑最小多方法题或
  表示缺口，均保留 FAIL，不扩大本 Slice。
- Critical assumptions tested：对 Proposal A1—A6 下本段正式 Verdict；A6 必须用编码前冻结的价值阈值判断 World Model 是否值得
  继续。A7/A8 的 early Case 只作阻断反证，不提前声称更广完整性或最终 Web 链已经证明。
- Reflection gate and success decision：`V-REFLECT-001`；只有方案复盘决定 `CONTINUE` 才可申请 SLICE-002 授权。

## Current vs expected behavior

当前流程把自由问题压成固定 Need，再要求一个唯一方法 selector；多个相关方法会触发 Limitation，0 候选或无关候选也没有可靠的
处理。预期最小流程允许 Agent 根据 typed 查询结果选择下一项 World Model 操作，直到 Support 足够或预算耗尽；本段不声称分页
结束等于业务语义不存在。

回答事实仍来自提问前构建的 exact Snapshot。Agent 只改变“如何调查”，不改变知识权威、更新时点或证据边界。

## System contracts and invariants

- `Question → immutable Needs → bounded query loop → sealed trace → Draft → independent Review → Delivery`；
- Agent 每一步只能提交 typed operation；平台校验 operation、Snapshot、Context、Ref、limit、budget 和 Support；
- operation 至少覆盖 implementation candidates、method implementation、declared method inventory、direct neighborhood 与 path；
- 多候选是正常输入，不要求唯一；本段只需冻结足以完成 early canary 的最小有界 result contract；
- 下单回归不得输出无关登录支持；查询、表示、业务发现任一完整性未证明时只能 Limitation，不得声称绝对不存在；
- Draft 只能使用 sealed trace 中的 World Model results，Review 独立检查漏查、错误否定和 Support 完整性；
- 回答进程不得访问 Repository、Source、raw Evidence、完整 AST、Update 或 Direct tools；
- 问题不进入 Build Objective，提问前后 CURRENT/Snapshot/Bundle 不变；
- 无 retry 或任何 fallback；超限失败关闭并返回可解释 Limitation；
- 每个问题保留 Source ground truth → Snapshot/Coverage → typed query → trace → Draft/Review → Web 的逐层诊断证据，首次偏差拥有根因分类；
- Production Activation 始终 `NOT_EXECUTED`。

## Interfaces and affected code

Readiness 接受后，预期影响现有 World Model Answering、Implementation Query、Agentic Task、Structure/implementation query service、
模型 egress strategy/qualification、runtime/HTTP/Web presenter 与 Citation 链。只实现 early Web/canary 所需的最小闭包，不得提前
完成 SLICE-002 的完整加固，也不得新建平行浏览器入口或 validation-only 产品路径。

具体文件只能在 System Contract 与 exact baseline 冻结后由实现设计确定；本 proposal 不把当前目录清单当作已授权改动。

## Compatibility, data and security boundaries

ITER-005/006 的 accepted Snapshot、Workspace、Update、Web、Citation 和 Java static-call 行为保持。ITER-007 的 Source Semantics code、
schema 和 Bundle 只能作为 unaccepted assets 重新通过本 Slice Gate，不能因代码存在就继承产品结论。

调查 trace 必须绑定 question、Need、exact Snapshot/Bundle、每个 proposal/result、Support、预算消耗、Draft、Review 与 terminal；用户可见
Citation 仍通过授权端点读取，Answer worker 不获得源码 payload。

实现期确认显式 `FINISH` 本身也是一次 Investigation 模型调用，并且只能发生在至少两个已执行调查回合之后。因此冻结的
2—4 Investigation / 4—6 total 仍是 Gateway 安全 envelope，但当前可达的正常成功路径实际消费 3—4 次 Investigation、总计 5—6 次；
4-call 下界不作为本 Slice 成功 fixture 的预期值。Supervisor 仍只按上限预建 6 个 descriptor，Result 必须报告 exact consumed count，
并关闭、审计所有未消费项；不得通过隐藏 terminal、伪造调用或放宽 two-Result 规则凑下界。详见
[FINDING-008-002](../findings/FINDING-008-002.md)。

当时的 Ark Adapter `openai-chat-completions-no-tools@8` 没有可继承的密封 Conformance Result，因此 live 资格顺序进一步固定为两个互不继承的
Gate：先在 clean exact candidate 上无网络冻结并单独申请恰好 2 次 Conformance call；只有当前 `@8` Result PASS 后，才可冻结绑定同一
candidate、exact suite/oracle/evaluator 和该 Result 的 18-case / 39-call Capability Evaluation，并另行申请 Provider 授权。任一授权都不
包含 retry、hidden canary、正式 Web、SLICE-002、Production Activation 或 push；未获对应授权时不得读取 credential 或建立 Provider
transport。详见 [FINDING-008-005](../findings/FINDING-008-005.md)。

run-001 的结果未知且旧 runner 缺少 terminal；修复后的 run-002 在第 1 次请求以 `TLS_FAILURE` 密封关闭，两个 grant 均已消费且不得
重试。不得用连续 Conformance grant 猜测网络状态。新的 live 顺序在原两级 Gate 前增加诊断阻断：先冻结并单独授权最多一次、
credential-free、只对 exact Ark host 建立 TLS handshake 的诊断，不发送 bearer 或 HTTP body；只有形成 root cause 并完成必要处置后，
才允许从新的 clean candidate 生成下一份 2-call Conformance preflight。不得通过 ambient proxy、关闭证书验证或扩大 payload boundary
绕过失败。详见 [FINDING-008-008](../findings/FINDING-008-008.md)。

独立授权的 direct TLS diagnostic 证明 TCP connect 完成，但唯一一次 handshake 在 certificate verification 前以 `SSLEOFError` 关闭；
随后独立授权的 loopback proxy 对照成功完成唯一 CONNECT，唯一 TLS handshake 却以相同 EOF 关闭。两次诊断的
credential/Ark HTTP/application payload 均为 0。这排除了 proxy 不可达与“仅因 Adapter 禁用 ambient proxy”解释，当前 live qualification
进入 environment/external-state hold：verified TLS 路径恢复前，不改 Adapter、不生成 Conformance run-003、不申请 Provider 调用。路径恢复后仍从新的
clean candidate 和新 Conformance 授权开始。

用户关闭系统代理并声明全流量 TUN 后，单独冻结和授权的 TUN direct probe 仍以完全相同的 `SSLEOFError` 在 certificate verification 前
关闭；因此环境声明不等于路径恢复。后续恢复证据必须是一次实际 verified handshake PASS，不能再用模式切换或连续失败 probe 替代。

更换节点后，独立 run-004 已取得一次 verified TLS handshake PASS，一次最小 `ark-code-latest` model diagnostic 也 PASS；切回原节点后，
run-005 又复现相同 Python/OpenSSL TLS EOF，而无痕浏览器可以到达 Ark HTTP AuthenticationError。该证据只证明客户端/路由路径分流和
替代路由的时点可用性，不构成 Conformance/Capability，也不支持修改 Adapter。用户随后决定更换模型 Provider，故 Ark live 工作停止。

Provider-independent 实现与确定性验证已经闭合；剩余 Conformance、Capability、正式 Web 和 canary 都是 Provider-dependent Gate。
新 Provider 明确前不创建猜测性 Adapter、不改 Ark default model，也不改写当前 System Provider 真相。新接入必须冻结 exact Provider、
endpoint/path、protocol、请求与响应模型 identity、secret、TLS/proxy、retry/error semantics，并取得独立资格和调用授权；若改变 System
Contract 或安全 Owner，先更新对应 System 文档/ADR。详见 [FINDING-008-009](../findings/FINDING-008-009.md)。

用户现已选择 DeepSeek。当前 exact candidate 使用独立 `DEEPSEEK` Provider、
`https://api.deepseek.com/chat/completions`、默认及期望响应 identity `deepseek-v4-pro`、secret reference
`env:DEEPSEEK_API_KEY` 与 Adapter `deepseek-chat-completions-no-tools@1`；`deepseek-v4-flash` 只允许显式选择，旧 alias 不回退。
独立 2-call Conformance 与 ITER-008 39-call Capability runner 已完成 fake-transport 闭合。按用户要求先验证模型可用性，再调整正式
runtime/product egress policy；当前正式 runtime 继续保持 Ark。DeepSeek 最小 model diagnostic run-001 已在 clean candidate
`8cbb3ab…` 上按 post-freeze 单次授权恰好调用 1 次并 PASS，请求/响应 identity 均为 `deepseek-v4-pro`；这只解除 model availability
顺序阻断，本身不构成 Conformance 或 Capability。后续 Conformance run-001 已 PASS；Capability、正式 Web 与 Production Activation
均未执行。详见 [FINDING-008-010](../findings/FINDING-008-010.md)。

最小模型 diagnostic 先经过独立 zero-network freeze 和 post-freeze 单次授权；runner 在唯一 dispatch 前密封 invocation，并对 PASS、
已知 Provider FAIL 或 outcome unknown 写入 sanitized result/failure 与 terminal。该 1-call grant 不授权或替代后续 2-call Conformance。
该授权现已消费且不可重试。包含诊断证据写回的 clean candidate `45fe1523…` 随后按独立 preflight 和 post-freeze grant 恰好执行 2 次
Conformance call，12/12 case PASS，响应 identity 仅为 `deepseek-v4-pro`；该授权同样已消费且不可重试。

同候选的 Capability freeze 随后在零 Provider 调用阶段形成，但独立 verifier 在授权前因缺失 metric contract import 触发 `NameError`。
因此该 freeze 不可授权或执行，39-call Capability 仍未发生。修复只补齐 verifier import 并增加有效 freeze 正向回归，不改变 Provider、
suite、oracle、evaluator 或产品协议；但 exact Git candidate 已变化。按 `FINDING-008-005` 的同候选规则，下一步必须从修复后的 clean
candidate 重新生成 Conformance preflight、取得新的 2-call 授权并 PASS，之后才能形成和申请新的 39-call Capability freeze。详见
[FINDING-008-011](../findings/FINDING-008-011.md)。

修复后的 candidate `3d2f35c…` 已以新的 exact preflight 恰好完成 2 次 DeepSeek Conformance call 并 PASS。其 Capability run-003
随后在第 25 次 dispatch 以 `TLS_FAILURE / PROVIDER_OUTCOME_UNKNOWN` 密封关闭，24 次 request / 11 Case 已完成且没有 retry；
Adapter 同一 CA fallback 的 credential-free 对照随后 5/5 verified TLS 1.3 PASS。新冻结的 run-004 最终完整执行 39 calls / 18 Case，
`unknown_count=0`，但只有首轮 candidate 与 Draft 两个 Case PASS，其余 16 Case FAIL，因此没有 Capability Qualification 或 Activation。

run-004 的 sealed output 对照 unchanged Oracle 表明：`prompt@4` 没有完整向模型说明每个 operation 的 exact relevant/irrelevant field
shape、本闭包 graph bounds、部分 result-driven operation 选择和三层完整性 Review 条件。System Contract 已拥有这些 Owner 与不变量，
故不改系统语义；本 Slice 将 Proposal Contract 版本化为 capability/Strategy `1.3.1`、prompt/vocabulary `@5`、bounded egress
policy `@1.0.1` 和 suite/oracle identity `@1.3.1`。原 18 Case、39-call、Oracle verdict、metric、阈值与 no-retry 保持不变，禁止
Provider、Case、工程、符号或答案特判。新 exact candidate 必须重新通过 Conformance 和完整 Capability Gate。详见
[FINDING-008-012](../findings/FINDING-008-012.md)。

## Open questions and implementation risks

- 固定三调用门禁需要在 Readiness 前重写，否则实现与规范冲突；
- 模型可能重复无效查询，平台需要 deterministic progress 与 cycle detection，不能靠无限 retry；
- 现有 no-payload atoms 若不足以回答隐藏题，应诚实判为 representation gap；
- 多步调查的 P95 延迟和成本必须在 Result 披露，不能用质量理由忽略预算。

## Acceptance scenarios

1. 零问题构建 exact Snapshot；提问前后权威状态一致，Question/Suite 未进入 Update。
2. deterministic corpus 证明多候选、0/N、最小 progress、预算和非法操作行为；非法操作全部失败关闭。
3. 正式 Web 回答登录流程，组合 `authenticate`、两次失败记录、异常路径和成功会话路径；下单题不返回登录支持，三层完整性不足时
   返回具体 Limitation。
4. `V-XD-001` 在同一 Need/Support chain 组合 accepted `CALLS` 与重新验收的实现语义。
5. 回答进程 Source/Update/Direct/raw Evidence attempt 全部为 0，Citation、console 和 terminal 可人工检查。
6. 冻结本 Slice 产品代码后，用户或独立方才披露一份全新小型真实 Java 工程及至少 1 条无符号多方法 answerable、2 条互补
   boundary；一个必须在完整最小闭包给 bounded absence，另一个必须因 Coverage 不足给具体 Limitation；
   成熟源码 Agent 先按同 revision、同问题和冻结等价资源运行并密封；随后同一正式 Web 给出 supported answer 与正确
   Gap/Limitation，且披露后产品变更数为 0。
7. `V-NEG-EARLY-001` 与 `V-DIAG-001` PASS：最小三层完整性可行，且任何失败都能定位到首次偏差层。
8. `V-COMP-EARLY-001` 按冻结 rubric 核对：零重大错误、逐 Need/Claim 不退步、boundary 无无关支持，且 A6 的预提交正向价值
   阈值 PASS；Result 必须保存 exact JSON value report、measurement input digest、实际数值和独立裁决收据，docs gate 重算报告 digest；
   仅披露时延/成本或自填 PASS 不构成通过。
9. 形成 exact Slice Result 并完成 `V-REFLECT-001`：逐 A1—A6 绑定 exact evidence，另记录 A7/A8 early signal 与下一风险，
   分类问题、复核完整诊断链、处置 Finding，
   作出 `CONTINUE / REDIRECT / REJECT`。只有 `CONTINUE` 才取得申请下一段授权的资格。
10. 本段相关 accepted regression PASS；Production Activation `NOT_EXECUTED`。

## Architecture reflection checkpoint

技术链、正式 Web 或 canary PASS 都不能自动推导方案可继续。Result 的 `reflection_gate_case_id` 必须为 `V-REFLECT-001`，
`reflection_gate_status` 必须为 `PASS`，A1—A6 必须逐项绑定 Expected、exact Evidence、Verdict 与 Impact，并单独记录 A7/A8
early signal、问题分类、逐层诊断、独立 Owner 和 `reflection_decision`。若证据表明是表示缺口、Agent 对照退步、正向价值阈值
未达、预算/复杂度不可接受或验证设计不能证伪
核心假设，决定必须为 `REDIRECT` 或 `REJECT`，当前 Iteration 随即停止；不得先进入 SLICE-002 再讨论。
若 `V-NEG-EARLY-001` 或 `V-WEB-001` FAIL，阻断 Result 还必须分别追加 A7/A8 的结构化 Verdict 行，不能只写 early signal。

## Findings

实现期新事实按 [Implementation Feedback Policy](../../../governance/implementation-feedback-policy.md) 登记到本轮 Findings。任何改变
架构、Contract、产品 Gate 或能力路径的 Finding 必须先处置，不能由 Result 静默改写系统真相。
