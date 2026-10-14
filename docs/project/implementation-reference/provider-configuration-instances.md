---
id: PROJECT-REFERENCE-PROVIDER-CONFIGURATION-INSTANCES
kind: implementation-reference
status: historical
authority: historical-evidence
owners: [engineering, project]
depends_on: [SYS-ARCH-BASELINE]
code: []
tests: []
coding_input: false
source_path: docs/system/quality/security-boundaries.md
as_of: 2026-10-14
---

# Provider 配置实例与实现证据

以下内容原样从系统文档归位（2026-10-14）。它们记录某一时期的 Provider 映射、连接策略和实现证据，不是系统规范。

## 来源：`docs/system/quality/security-boundaries.md`

当前 ITER-010 配置把 Ark 映射到 `preferred` execution profile，把 DeepSeek 映射到 `fallback` execution profile。备用 profile 使用
`DEEPSEEK_DISPATCH_ADMISSION@1` 和非高峰策略插件；当前 bounded connection policy 预置 3 个 descriptor、最多 3 次 credential-free TLS
acquisition，并把每条 verified session 限制为最多 20 次 HTTP dispatch。当前 Ark profile 使用其独立 connection policy。这些映射、策略和
数值只属于当前配置实例，不定义系统路由、质量或授权语义。

`ENGINEERING_CHAT_EXPERIENCE@1` 的 Access scaffold 已本地实现 exact loopback/Origin/JSON/input 边界和 0-dispatch 失败真相；
`CONVERSATIONAL_ENGINEERING_AGENT@1` 的 Application-owned executor、Work State/Observation/Package/fresh Review/Delivery exact binding
已形成确定性本地候选，并对 forged binding、未授权 Source operation、缺证后无新 Observation 重写、无进展和 malformed outcome 失败关闭。
World Model/Source/Ledger trusted tool adapter 与单 Provider Agent/Reviewer 的 one-use Disclosure/Gateway receipt 已分别形成
`EVIDENCE_TOOLS_LOCAL_CANDIDATE / MODEL_BOUNDARY_LOCAL_CANDIDATE`；确定 pre-dispatch 与 replay 计 0，fresh dispatch/unknown 计 1，
retry 仍为 0。non-dispatching candidate preflight 不读取 Source/credential、不启动 listener、不调用 Provider，并固定
`ready_for_live=false`。ADR-017 双 attempt、生产 Provider runtime、artifact fixed launcher 与 Ark/DeepSeek terminal Session audit 已形成本地
确定性候选；Ark HTTP 前不可用也已 owner-typed 为 raw availability evidence，但受信 availability-owner verdict 尚未闭合，不得追认为 fallback eligibility。fresh Ark 与 DeepSeek Conformance 均已 PASS，
双 Provider qualification 当前同时可用；Artifact Session `@4` 已形成
`PUBLIC_SOURCE_STANDING_AUTHORITY_DERIVATION_LOCAL_CANDIDATE`：owner-private closed standing scope 经 public upstream、clean HEAD、exact
commit/tree/license object 重验后，派生 exact Session authority，Provider route/Turn attempt 和 one-use role receipt 均绑定 parent digest，
且 Source/provider/account/profile/budget/time 漂移在 disclosure/credential/network 前失败关闭。current actual artifact、Citation 内容与
live Chat 仍为 `NOT_LIVE`。以上边界不能由 fake/offline port、Access、旧 `@1—@3` 运行、浏览器连续提交外观或既有 Provider 资格推导已经满足。

## 来源：`docs/system/contracts/ai/model-gateway.md`

当前 ITER-010 配置把 Ark 映射到 `preferred` execution profile，把 DeepSeek 映射到 `fallback` execution profile。当前 Ark 与 DeepSeek
Adapter contract 都把 schema authority 与 leading semantic authority 合并为恰好一个 leading system message；自然语言任务或审核正文不得
翻译 closed Schema 的 field name 与 enum protocol token，Adapter 也不得通过语言别名接受漂移输出。当前 Ark Engineering Chat profile 固定
每 request 一个 verified TLS session、每 session 一个 HTTP dispatch、`Connection: close`、TLS 后逐 dispatch 解析 credential 与 retry 0。
Ark Gateway request/result 对调用方仍为非流式单终态；Provider wire 使用 `stream:true`、`stream_options.include_usage:true`、
`reasoning_effort:low` 与 SSE，`thinking` field 保持缺席。Adapter
在 framing 层忽略 SSE comment keep-alive 和重复空分隔，但 application event 仍要求恰好一个 `data:` field，其他控制字段失败关闭；随后只在
内存中按稳定 response/model identity、单 choice、finish reason、Usage 和 `[DONE]` 严格重组一个 terminal response。comment、partial content
和 Provider reasoning channel 均不投影或持久化。已重组 choice 的 string content（包括 empty）进入 finish/schema 层：non-`stop`
termination 与 closed-schema failure 都保留 terminal AdapterResponse/Usage 并分类为 `STRUCTURED_OUTPUT_INVALID`；missing/non-string content
仍是 `PROVIDER_RESPONSE_INVALID`。中途断连仍为 outcome unknown，不能 retry 或直接授权 fallback。这些差异由各自
Conformance 和 execution profile 拥有，不定义通用 route 分支。

当前 DeepSeek profile 使用 `PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@2`，每条 session 最多 20 次 dispatch、transport lifetime 最多
3 次 acquisition，并使用 `DEEPSEEK_DISPATCH_ADMISSION@1`。Engineering Chat 以独立 runtime lifecycle ref
`DEEPSEEK_PERSISTENT_VERIFIED_TLS_HTTP11_NO_RETRY@3` 包住 exact qualified transport：fully consumed persistent socket 在下一次
qualified transport call 前若 non-blocking readiness probe 为可读或异常，或自最后一次 HTTP completion 起已 idle 至少 60 秒，则 runtime
先关闭，再由 base transport 在上述 acquisition bound 内取得 verified TLS。该 wrapper 不改变 Adapter request/response/TLS/credential/HTTP
bytes 或 Session audit；已经开始的 HTTP 仍不 replay/retry。当前产品已用本地确定性测试闭合 logical-Turn/provider-attempt 双层身份、双 route、完整链
fallback、late-result quarantine、typed unavailable raw evidence 与 Ark/DeepSeek Session audit；fresh Ark 与 DeepSeek Conformance 又已分别在 exact
clean identity 上 PASS。当前状态是
`ARK_QUALIFIED / DEEPSEEK_QUALIFIED / DUAL_PROVIDER_QUALIFICATION_CURRENT / DEEPSEEK_SCHEDULE_GATE_LOCAL_PASS /
HTTP_EVIDENCE_AVAILABILITY_OWNER_LOCAL_CANDIDATE / LIVE_ROUTE_NOT_YET_REATTESTED /
PUBLIC_SOURCE_STANDING_AUTHORITY_DERIVATION_LOCAL_CANDIDATE / NOT_LIVE`。Artifact Session `@4` 已在本地确定性测试中把 standing parent
逐级绑定到 exact Session、Provider route、Turn attempt 与 one-use role disclosure receipt，并对 Source/provider/account/profile/budget/time
drift 失败关闭；旧 `@1—@3` 不取得该状态。这些名称、策略与状态是当前配置实例和本地实现证据；current actual artifact、真实
Gateway/transport dispatch 与 Browser 体验仍须验证，不能由 local candidate 推导 live PASS。

