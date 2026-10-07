---
id: PROJECT-REFERENCE-RUNTIME-PROFILE-HISTORY
kind: implementation-reference
status: historical
authority: historical-evidence
owners: [engineering, project]
depends_on: [SYS-ARCH-BASELINE]
code: []
tests: []
coding_input: false
source_path: docs/system/architecture/runtime-flows.md
as_of: 2026-10-01
---

# runtime profile history

以下内容从 `docs/system/architecture/runtime-flows.md` 的实现/运行记录原样移出，保留当时措辞；其中“当前”“下一步”“须执行”均为历史语境，不是现行任务、架构决策或能力验收。读取最新工作状态应回到 [current](../current.md)。

## 当前配置实例与历史实现证据

当前 ITER-010 配置把 Ark 映射为 `preferred` execution profile，把 DeepSeek 映射为 `fallback` execution profile。备用 profile 的
admission plugin 使用 `DEEPSEEK_DISPATCH_ADMISSION@1`，当前允许窗口与价格检查由该插件实例定义；这些具体名称、窗口和价格策略不定义
通用 route 分支、质量或授权语义。

当前 DeepSeek bounded profile 使用 `PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@2`：最多 3 次 credential-free TLS acquisition，每条
verified session 最多 20 次 HTTP dispatch。Engineering Chat runtime 以
`DEEPSEEK_PERSISTENT_VERIFIED_TLS_HTTP11_NO_RETRY@3` 在下一 qualified call 前关闭可读/异常的 fully consumed socket 或 idle 至少
60 秒的 socket，再由 exact base transport 在同一 acquisition bound 内重建 verified TLS；该 product lifecycle rotation 不改变 qualified
Adapter bytes、Session audit 或 request retry 语义。40-call Capability qualification 通常
使用 2 条 session 并保留第 3 次 acquisition 余量，正式产品单题 4—6 calls 通常只使用第一条。当前 Ark profile 使用其独立的一请求一连接策略。这些数值是 execution profile 的当前实例和历史
实现证据，不可借给其他 profile。

当前 runtime 已在 Gateway preflight/invoke 与 Artifact Session `@3` 对备用 profile 的 admission flow 形成本地 Case PASS；当前状态为
`ROUTING_LOCAL_PASS / DEEPSEEK_SCHEDULE_ADMISSION_LOCAL_PASS / STANDING_AUTHORITY_DERIVATION_REQUIRED / NOT_LIVE`。fresh Ark 与 DeepSeek
资格和既有运行只证明具体配置实例；standing-authority 派生链和逐 dispatch receipt 仍须分别实现与验证。

## 从运行附录归位的详细 Profile 记录

以下内容原属于 `docs/system/architecture/runtime-flows.md` 的 `JAVA_SOURCE_SEMANTICS@1` 详细运行说明。它保留历史/实现语境，
不属于概要架构，也不能覆盖 `SYS-ARCH-BASELINE` 或相应 Contract：

首轮 Agent 只用注册 operation/relation vocabulary 提出 bounded evidence obligations 与 search terms；Application 对其归一、去重、
收敛依赖并冻结。candidate discovery 已是强制首 transition，因此 raw `implementation_candidates` evidence alias 被保守向上归一为
`method_implementations`，不能在非零候选后单独关闭 ledger。由于 method Result 已携带 exact supported outgoing `CALLS`，standalone
raw `direct_neighborhood(OUTGOING_CALLS)` 也收敛为 method evidence；path 组合、incoming 与 both directions 保持图义务。每个后续状态由 Application 从 ledger 和 sealed input 推导受限 operation allowlist，再编译 exact Snapshot、前序 Result
binding、Entity Ref、direction/predicate 与 bounds，并校验 obligation、bytes、Support、progress 和剩余预算后执行。模型固定 envelope
中的越权 operation 或过早 FINISH 不改变平台 transition。候选搜索可以返回 0/N；方法实现查询可在同一 candidate result 内选择最多 3 个 exact
method Ref，不取排名第一也不无界展开。至少一个 Result 执行后可以显式 FINISH，但只有 ledger 已关闭或没有合法 evidence-reducing
transition 时才获得终态权力；FINISH 本身计作调用，所以零候选、截断 candidate 或其他没有合法 evidence-reducing transition 的 Result
可在 1 query + FINISH 后形成对应 Gap/Limitation。重复 query、无进展、越界或预算耗尽返回具体 Limitation，并保持 Source/Update/Direct
fallback 为 0。查询、表示与业务发现三层完整性只由平台通过 progress receipt 投影；没有同时证明时不得给 bounded absence，评测 Oracle
identity 不进入 Answer。

该 Profile 每题实际模型调用为 4—6（调查 2—4、Draft 1、Review 1），不重试。Gateway connection policy 是 execution profile 的资格身份，
不能从调用上限推导 descriptor 数。每个 execution profile 必须冻结连接方式、credential-free TLS acquisition 上限、每条 verified session
的 dispatch 上限、连接轮换和 terminal close 规则；只有取得 exact 资格的 persistent policy 才能复用 TLS session，同时仍为每次 stateless
request 保持独立 Manifest、call identity 和 receipt。任何 HTTP bytes 可能已发送后的失败都立即记为 `OUTCOME_UNKNOWN` 且不重发。
terminal 后关闭未使用 descriptor，通用 transport/call receipt 必须分别闭合 TLS attempts、successes、reuse、Provider calls、per-session
dispatch bound 与 `provisioned = attempts + unused_closed`。旧资格或不同 profile 的 connection receipt 均不得复用。
