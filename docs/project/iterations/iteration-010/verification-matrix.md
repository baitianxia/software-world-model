---
id: ITER-010-VERIFICATION
kind: iteration-verification
status: failed
authority: execution-evidence
owners: [quality]
depends_on: [ITER-010-PROPOSAL, FINDING-010-095, FINDING-010-097, FINDING-010-098, FINDING-010-099, FINDING-010-100, FINDING-010-101, FINDING-010-102, FINDING-010-103, FINDING-010-104, FINDING-010-105, FINDING-010-106, FINDING-010-107, FINDING-010-108, FINDING-010-109, FINDING-010-110]
code: []
tests: []
iteration: ITER-010
product_goal_gate: V-000
product_goal_outcome: user-visible-general-engineering-qa-delta
product_goal_evaluation: independent-hidden-plus-live-ad-hoc
product_goal_result_id: ITER-010-RESULT-SLICE-001-STOP-REDIRECT
---

# ITER-010 Verification Matrix

## PDR-004 current verification target

本 Matrix 的既有 FAIL/PASS 行保存旧单轮 Engineering QA 执行事实与原 Case 定义，不因新方向改写。PDR-004 Readiness 已由
`f76ba3e8…` 接受，当前 Iteration/Slice1 已授权；current 产品 Gate 只是：
`V-ALPHA-ACCESS-001` PDR-004 pre-execution revision → `V-TIMEBOX-CHAT-001/V-CHAT-EXPERIENCE-001/V-CHAT-001/V-CHAT-QUALITY-001/V-CHAT-XD-001` →
`V-COMP-ALPHA-001` → `V-PREVIEW-002` PDR-004 pre-execution revision。Case 仍属于同一 Slice，但不再被解释为一次性大交付：Access 只阻断
首次用户交付，Chat/Quality/XD 阻断五轮方向证据，Comparison/Preview 阻断 hardening；后项不得反向阻塞前项交付。新架构为
`ACCESS_BROWSER_PASS / AGENT_EXECUTOR_LOCAL_CANDIDATE / EVIDENCE_TOOLS_LOCAL_CANDIDATE / MODEL_BOUNDARY_LOCAL_CANDIDATE /
PROVIDER_ROUTE_COMPOSITION_LOCAL_CANDIDATE / PROVIDER_RUNTIME_COMPOSITION_LOCAL_CANDIDATE /
SESSION_RUNTIME_COMPOSITION_LOCAL_CANDIDATE / ARTIFACT_SESSION_FIXED_COMMAND_LOCAL_CANDIDATE /
ARK_TRANSPORT_SESSION_AUDIT_LOCAL_CANDIDATE /
ARK_CONFORMANCE_PASS / DEEPSEEK_CONFORMANCE_PASS / DUAL_PROVIDER_QUALIFICATION_CURRENT /
FIRST_LIVE_CHAT_FAILED / COMBINED_FIVE_TURN_DETERMINISTIC_SUCCESSOR_PASS /
NEW_EXACT_PRODUCT_SESSION_AUTHORITY_REQUIRED / NOT_ACCEPTED / NOT_PRODUCTION`。`V-ALPHA-ACCESS-001` 已有独立真实执行证据；首次五轮
Chat 与新对话 probe 也已有失败执行证据，不能再标记为 NOT-RUN。一次 Access/browser 或已消费的 live Session grant 不等于修复后
Provider/live Chat、hidden、后续 Slice 或 Production 授权。

## Current Chat Access evidence

`FINDING-010-095` 已把首个 Access 纵切实现为独立 `swm-engineering-chat`：Application 持有不可变 Conversation/Revision/Context、Message
和 Turn，页面展示完整历史与“新对话”；Provider 未配置时提交仍形成真实失败 Turn，dispatch/retry 为 0，Conversation 保持 `ACTIVE`。
固定 launcher 无运行参数，只接受 clean exact product 和 `mall@0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`，固定
`127.0.0.1:8765`，不装载 Provider/credential/Source/World Model payload。新 Access 定向 17/17、既有 QA 相邻兼容回归 18/18、Browser
JavaScript syntax、四模块 compile 和 diff check 均 PASS。

`FINDING-010-096 / ITER-010-RESULT-V-ALPHA-ACCESS-001` 随后在 clean exact
`cf2883bef861e0345afc36415d4216f943d31cf4` / tree `a720afbb36e05410d8e9e830b4f51f261e494852` 上按固定命令启动真实 listener，并用
in-app Browser 完成普通用户交互。第一 Conversation 连续两个失败 Turn 后为 `revision 3 / ACTIVE` 且完整四条历史仍在；“新对话”产生不同
identity、`EMPTY CONTEXT` 和空消息历史，隔离探针只显示新 Conversation 的两条消息。最终 health 为 Conversation 2、Turn 3、Provider
dispatch 0，browser console 无 warning/error，Production Activation `NOT_EXECUTED`；listener exit 0 且端口已关闭。因此
`V-ALPHA-ACCESS-001` 为 `PASS / access-only`。本次没有 Provider/model、Source/World Model、源码/resources 或主 Agent 执行，不能产生
Chat/Quality/XD PASS。

## First live five-Turn Chat failure evidence

`FINDING-010-107` 记录 exact product `eb835f58b75831fc6f2c5a2513a13f32bdb3f7fe` / tree
`e5508f17f99201876ecf932550e1bd30f67127d0` 与 `mall@0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` 的 owner-private
`run-035-chat-alpha`。同一 Conversation 的五个固定问题全部失败：Turn 1/2/3/5 为
`AGENT_NO_PROGRESS_LIMIT_REACHED`，Turn 4 为 `AGENT_MODEL_OUTCOME_UNKNOWN`；逐 Turn logical dispatch 为 `4/4/3/4/5`，没有任何
Answer、Citation、Review 或 Delivery。新 Conversation 初始确为 `EMPTY CONTEXT` 且没有旧消息，但省略指代“它呢？”返回
`AGENT_PRE_DISPATCH_REJECTED` 通用失败，而不是澄清。因此 transcript isolation 成立，Chat/Quality/XD 和要求的泄漏负测仍失败。

terminal receipt `sha256:7bf6a2553cb952db281e56d8c15924476359e522f26148fff082178a8d0ac1ba` 密封 2 Conversation、6 Turn、20
logical Provider dispatch、request retry 0、private artifact/Gateway files 与 Production Activation `NOT_EXECUTED`；listener 已正常停止，
browser console clean。最早系统性偏差是 model-facing `SOURCE_SEARCH` 错称可作 semantic proposal，而 Worker 只做大小写敏感 literal
match；519 个授权 Java entry 又按 canonical 顺序在 64-file fuse 前扫描不到目标。新对话则没有可信的 Provider 前指代策略，第六 Turn 的
零 dispatch 实际来自已耗尽的 Session Authority，不能冒充正确澄清。

`FINDING-010-108/109` 已分别形成 literal-search contract + authorized-path candidate ordering，以及 binding-owned 空上下文指代澄清的本地
修复候选。它们不能追认 run-035；新的真实验证必须绑定修复后的 exact commit/tree、owner-private artifact 与新 Session Authority。

组合审计随后发现，默认 64 文件总预算下的截断 SEARCH 会在 locator READ 前耗尽全部预算。`FINDING-010-110` 让 Broker 只在同一总熔断
内为后续 READ/PARSE 保留 1 个名额，不提高任何资源上限。新增 deterministic successor canary 使用 71 个授权临时 Java 文件和 run-035
同一固定五轮：每轮 SEARCH 读取 63 个文件并保留 `PARTIAL / SOURCE_FILE_FUSE_EXHAUSTED` boundary，随后 opaque locator READ 使用第 64
个名额，五轮均形成 Package、fresh Review 和 Delivery；Work State revision 为 `3/6/9/12/15`，fake Agent/Reviewer logical dispatch
合计 20。空的新 Conversation probe 又以 0 dispatch 返回 Application clarification，旧 Conversation digest 不变。六个相邻模块合计
`99/99 PASS`；允许本机 socket 的完整 1275 项为 1269 PASS，剩余 5 FAIL + 1 ERROR 精确属于既有 V-009/Codex drift hold，没有本次模块
新增失败。该 canary 不验证五个答案的产品质量或 World Model + Source 组合质量，也没有 mall、外部 Provider/model、credential、
listener/browser 或 Production 活动，因此所有 live Chat/Quality/XD verdict 仍为 FAIL，下一 Gate 不变。

## Current local Agent executor evidence

`FINDING-010-097` 在 Access 之后闭合了不接外部系统的 Application-owned bounded executor：同一 Conversation 的 Work State identity 跨
Turn 稳定且 revision 递增；主 Agent 只提交 full Work State 与 closed-catalog action/Draft；工具 Result、support/boundary Observation、
Package、Claim、fresh Review、Finding 和 Delivery Authorization 均按 exact digest 绑定。Reviewer 要求补证后，没有新 Observation 就不能
重交 Draft；同包重写复用 Package，新 Observation 形成 successor Package 与 fresh Review。伪造 Tool/Delivery binding、Source authority
缺失、malformed executor outcome、并发同 Conversation、无进展及资源熔断都只关闭当前 Turn并保留既有 Context。

Agent/Conversation/Browser 与相邻旧 QA 定向组合实际 `48/48 PASS`，四模块 `py_compile`、Browser JavaScript `node --check` 和
`git diff --check` PASS。测试只使用 fake ports，
没有 listener/browser、Provider/model、mall 源码/resources 或 Production 执行。因此这只把实现状态更新为
`AGENT_EXECUTOR_LOCAL_CANDIDATE`；World Model/Source Broker/Worker、完整 Ledger/Citation、Provider driver/Reviewer、Disclosure/
fallback、fixed launcher 与五轮 live Chat 仍未集成或资格化，下面所有 Chat/Quality/XD/Comparison/Preview verdict 保持不变。

## Current local evidence-tool adapter evidence

`FINDING-010-098` 在 executor 后复用现有 World Model projector、Source Broker 与 Local Git Retrieval Worker：一个工具动作可分别返回
support/boundary Observation；每条 Observation 带 exact Turn/Tool/evidence Request/repository revision、可重算的完整 Ledger entry
chain/prefix 与 Citation content digest。Source `search→read` 只能复制当前 Turn 已签发 opaque locator，raw path 与包含
`src/main/resources` 的父 allowlist 都在 Worker 前拒绝。World Model fixture 同时产生 supported behavior 与 unknown boundary，分别进入
Package 两个分区。

新增 4 个 adapter 案例与 Agent/Conversation/Browser/旧 QA 相邻组合实际 `61/61 PASS`；Local Git 只读取测试生成的临时仓库。没有读取
mall 源码/resources，没有 listener/browser、Provider/model、credential、外部网络或 Production Activation。因此状态只增加
`EVIDENCE_TOOLS_LOCAL_CANDIDATE`；当时 Provider-backed Agent/Reviewer、Disclosure/fallback、Citation browser projection、fixed launcher 与
五轮 mall Chat 尚未集成或资格化；下节记录随后形成的单 Provider model-boundary 候选，所有 live verdict 仍保持不变。

## Current local model-boundary and candidate-preflight evidence

`FINDING-010-099` 为 primary Agent 与 independent Reviewer 分别密封 closed no-tools input/output。每个角色 input 绑定 current Turn、
relevant Conversation Context、Work State/Observation 或 Package/Draft、exact tool proposal contract、Provider configuration、完整输入与逐 leaf
Disclosure digest；session authority 不作为模型内容发送，credential reference 不进入 rendered message。Provider output 不能自报 call ID，
Gateway call identity 由可信 Adapter 注入 proposal，并以 typed receipt 贯穿 Application Turn 与 Browser developer view。

真实本地 `ModelGateway + SQLite + OFFLINE_FIXTURE Adapter` 证明：binding drift 在 dispatch 前计 0；fresh offline Adapter call 计 1 但不能
取得 live eligibility；outcome unknown 计 1 且 retry 0；repository replay 计 0。Gateway `preflight` 不 prepare、不 dispatch、不读取 Secret。
新的 candidate preflight 只核对调用者已解析的 product commit/tree、Chat binding、World Model/Source/evidence tools、单 Provider config 和
Session Disclosure；listener、credential、Source read、Provider dispatch 均保持 0，且 `ready_for_live=false` 明示 fallback、fixed launcher
和 live 尚未闭合。

Model/Agent/candidate/Conversation/Browser 与旧 QA 相邻组合实际 `86/86 PASS`，相关 `py_compile` 与 `git diff --check` PASS。本次没有
外部网络、Provider/model、listener/browser、mall Source/resources、credential 或 Production Activation。因此状态只增加
`MODEL_BOUNDARY_LOCAL_CANDIDATE`；在该证据点，ADR-017 Ark→DeepSeek 独立 full-chain fallback、真实 Adapter/transport/fixed launcher、
Citation browser projection 与五轮 mall Chat 仍为 `NOT_INTEGRATED / NOT_QUALIFIED / NOT_LIVE`。下节记录随后形成的 route composition
本地候选；所有 live verdict 保持不变。

## Current local Provider-route composition evidence

`FINDING-010-100` 将 raw Provider failure code 与 trusted owner classification 分开；只有已验证 Gateway terminal Result 或 closed output decoder
产生的五类 ADR-017 outcome 可触发 fallback，Application/Source/Security、qualification、Gateway identity 和 runtime creation failure 均失败
关闭。Ark primary 与 DeepSeek fallback 从 immutable original Turn、relevant sealed Context、exact World Model authority 和 Source Profile 启动
独立 full-chain attempt；同 Provider retry 为 0，fallback 至多一次，primary 临时 Work State 不写入 Application-owned committed repository。
logical Turn 聚合两个 attempt 的 dispatch/receipt audit，只投影最后完整 attempt 的 Outcome；outcome unknown 后 fallback 会记录潜在重复计费，
late primary 固定 quarantine 且没有 overwrite/merge API。

non-starting fixed composition 将 exact product tree/commit、Chat Binding、evidence tools、双 route/configuration/Session Disclosure、lazy attempt
factory、Conversation Service 和 Browser Application 绑定在一起。预检不创建 attempt，不解析 credential，不读取 Source，不启动 listener，也不
调用 Provider；公开 `swm-engineering-chat` 仍是 Access-only launcher。相关定向命令实际 `76/76 PASS`，`compileall`、`py_compile` 与
`git diff --check` 同时通过；没有外部网络、Provider/model、listener/browser、mall Source/resources、credential 或 Production Activation。
因此在该 evidence point，状态只增加 `PROVIDER_ROUTE_COMPOSITION_LOCAL_CANDIDATE`；真实 Ark/DeepSeek Adapter/transport/credential-reference、
Source/World Model runtime、fixed command Session wiring、资格与五轮 mall Chat 仍为 `NOT_ATTESTED / NOT_QUALIFIED / NOT_LIVE`。下节记录
随后形成的 Provider runtime composition；所有 live verdict 保持不变。

## Current local Provider-runtime composition evidence

`FINDING-010-101` 将已验证 typed Conformance identity 转换为 exact Agent model configuration，并使用生产 Ark/DeepSeek Adapter、
credential-lazy direct transport、Model Gateway、Session-scoped Disclosure Authorizer 和 closed Agent/Reviewer model boundary。两条 runtime
生成 distinct attempt dependencies 并接入上一节 non-starting route/Browser composition；构造不调用 credential resolver、不建 TLS/socket、
不 prepare Gateway、不创建 Turn 或 Provider dispatch，公开 receipt 也不投影 secret reference。

新增 3 个 runtime 案例后的相关组合实际 `79/79 PASS`。这些测试使用本地构造的 typed qualification identity，没有加载 current sealed
Conformance 文件，也没有外部网络、Provider/model、credential、listener/browser、mall Source/resources 或 Production Activation。因此状态
只增加 `PROVIDER_RUNTIME_COMPOSITION_LOCAL_CANDIDATE`；current qualification、published World Model、exact Source Profile/Worker、两个
private Gateway repositories、fixed command Session 与五轮 Chat 仍为 `NOT_LOADED / NOT_QUALIFIED / NOT_LIVE`，下面所有 verdict 保持不变。

## Current local Session-runtime composition evidence

`FINDING-010-102` 把两条生产 Provider runtime、exact Chat Binding/Evidence Tool Configuration、World Model projector identity、Source
Broker/Worker、per-attempt fresh evidence Tool/Response Control、Application-owned committed Work State、Ark→DeepSeek route、Conversation
Service 与 Browser Application 接入同一 non-starting Session runtime。两条 attempt 共享同一只读 Cognition/Source control plane，但各自持有
独立 Tool Ledger/progress/locator state 与 one-use Response Control；失败 primary 的私有中间态不能进入 fallback。

新增 2 个 Session 案例并纳入 Source runtime 相邻回归后的相关组合实际 `89/89 PASS`，其中一例在空临时目录上构造真实
`LocalGitEvidenceClassProfile / SourceBroker /
LocalGitRetrievalWorker`，并证明 preparation 不读取 Source 或投影 cognition。receipt 同时证明此时 attempt/tool、credential、Provider dispatch
与 listener 均为 0/false，Production Activation 为 `NOT_EXECUTED`。测试仍使用本地构造的 typed qualification identity，没有加载 current
sealed Conformance 或 canonical private artifact Session Configuration，也没有 mall Source/resources、外部网络、Provider/model、credential、
listener/browser 或 Production 执行。因此状态只增加 `SESSION_RUNTIME_COMPOSITION_LOCAL_CANDIDATE`；artifact loader、fixed command wiring
与五轮 Chat 仍为 `NOT_LOADED / NOT_QUALIFIED / NOT_LIVE`，下面所有 verdict 保持不变。

## Current local artifact Session and fixed-command evidence

`FINDING-010-103` 实现 `SWM-ENGINEERING-CHAT-ARTIFACT-SESSION-CONFIG@1` 的 owner-private closed loader：product/source Git identity、
published ordered/snapshot World Model、exact Source Profile、mandatory `src/main/resources` exclusion、ordinal 1 Ark/ordinal 2 DeepSeek、两份
Conformance result、两个 distinct private Gateway repositories、Session authority、5 Turns × 每 Turn 每 Provider 15 dispatch 与每 Provider
总计 75 都由同一 artifact 密封。unknown/missing/duplicate/reordered field、公开权限、relative path、identity drift 与 profile/exclusion
overlap 在外部活动前失败关闭。

`swm-engineering-chat` 无参数继续是已验证 Access-only；唯一新增 selector `--session-config` 不暴露 host/port/project/revision/Provider/
question/credential/authority。fake listener lifecycle 证明两个 private database exclusive-create 后，launch receipt 在 listener 构造前写入，
terminal receipt 在 shutdown 后写入；固定 URL 仍是 `127.0.0.1:8765`。artifact/CLI/provider-runtime 直接组合实际 `13/13 PASS`；包含 Agent、
Conversation、Tools、Model、Route、Candidate、Launcher、Provider runtime、artifact、Source、Browser、CLI、Gateway、Conformance、Cognition 与
Structure 的聚焦组合实际 `117/117 PASS`，application/AI/interface compile 与 diff check 通过。

测试通过 patched/local typed artifacts 与 fake listener 证明零 I/O composition，没有读取 mall Source/resources、解析 credential、访问网络、
调用 Provider/model、启动真实 listener/browser 或执行 Production Activation。current actual artifact 未生成或执行；terminal receipt 当前有
Disclosure/model-boundary/model-call audit、dispatch total 与 DeepSeek transport Session audit，但没有 Ark transport-level Session audit。因此在该 evidence point 状态只增加
`ARTIFACT_SESSION_FIXED_COMMAND_LOCAL_CANDIDATE`；`V-CHAT-*`、资格、live 与 Acceptance verdict 均保持不变。

## Current local Ark transport Session-audit evidence

`FINDING-010-104` 将 Ark transport 固定为 exact host/path、每 request 一个 verified TLS session、certificate 验证后才解析 credential、
每 session 一个 HTTP dispatch、`Connection: close` 与 request retry 0。`SWM-VOLCENGINE-ARK-TRANSPORT-SESSION-AUDIT@1` 分列 TLS、
credential、HTTP、reuse、post-dispatch unknown 和 retry；terminal receipt 现在对 Ark/DeepSeek 都要求 strict transport audit。HTTP 前 TLS
不可用通过 Model Gateway owner-typed `ProviderUnavailable` 密封为 fallback-eligible `PROVIDER_UNAVAILABLE`；HTTP 已开始后的失败仍单独是
outcome unknown。

Ark Conformance fixture/result identity 升级为 `1.7.0 / @2`，新增 `CC-ARK-13` 并把 Session audit 纳入 PASS verifier；configuration
fingerprint 又绑定 connection/credential/retry policy，旧 qualification 因 fixture、implementation 与 configuration drift 失效。最小相关组合
48/48、相邻聚焦组合 141/141、compileall 与 diff check 通过；V-009 定向模块仍保留既有 3 FAIL + 1 ERROR 的 exact implementation-drift
historical hold。本证据没有真实 TLS、credential、Provider/model、Source、listener/browser 或 Activation，状态只增加
`ARK_TRANSPORT_SESSION_AUDIT_LOCAL_CANDIDATE`。

## Current fresh Ark Conformance evidence

`FINDING-010-105` 记录用户精确授权的 clean `1e99e9b…` fresh run：`CC-ARK-CHAT-NO-TOOLS-001 / 1.7.0 / @2` 以 2/2
request、13/13 Case PASS，actual model `glm-5.2`，Result digest 为
`sha256:d0e9d49f234b770f9c22ad38276622f04168cbb17e1cada3b18586431ba40a15`。strict audit 为 TLS/credential `2/2`、HTTP 2、
reuse/retry/post-dispatch unknown 0；sealed file mode `0600`，raw prompt/response persistence false。没有 mall Source/resources、DeepSeek、
listener/browser 或 Activation 活动。current Ark qualification 有效到 `2026-09-25T01:00:39.148494Z`。

artifact Gate 同时要求 current DeepSeek qualification。由于 DeepSeek implementation manifest 也包含本次变化的 `model_gateway.py`，current
digest `sha256:a680b0c8…bb07` 与旧 PASS Result 的 `sha256:1022fdd1…3d4b` 不同；current loader 实际以
`QUALIFICATION_INVALID` 拒绝旧 Result。下节记录另行授权的 fresh DeepSeek Conformance。

## Current fresh DeepSeek Conformance evidence

`FINDING-010-106` 记录用户精确授权的 clean `653eff3…` / tree `d0cab3a…` fresh run：
`CC-DEEPSEEK-CHAT-NO-TOOLS-001 / fixture 1.2.0 / result @2` 以 2/2 request、12/12 Case PASS，actual model
`deepseek-v4-pro`，Result digest 为 `sha256:3e43921a5e0ebf00d0805b7c66f609c29b0d29a3fd8b848a8b3e491e641e6a4d`。
strict persistent transport audit 为 TLS attempts/successes `1/1`、credential resolutions `2/2`、HTTP dispatch 2、connection reuse 1、
request retry/post-dispatch unknown 0；sealed file mode `0600`，raw prompt/response persistence false。current DeepSeek qualification 有效到
`2026-09-25T01:22:41.700955Z`。本次没有 mall Source/resources、Ark、listener/browser 或 Activation 活动。

结合 `FINDING-010-105`，Ark 与 DeepSeek current qualification 现在同时可用。Conformance grant 不授权 artifact 中的 Source/
World Model disclosure 或五轮 Browser Session；下一 Gate 是 exact five-Turn Session authorization，之后才生成 current owner-private
artifact 并执行 fixed canary。`V-CHAT-*` 与所有质量 verdict 继续 `NOT-RUN / blocking`。

## Pre-freeze implementation evidence

截至 `2026-08-22`，candidate `b8360a3…` 的 focused 58/58、docs 389/389、full 1108/1103，以及修复
`FINDING-010-015` 后 candidate `50b08b5…` 的 focused 59/59、docs 391/391、full 1109/1104 均作为历史证据保留。后续 live
暴露 `FINDING-010-016—019` 后，Prompt `@4` 实现 focused 69/69、docs 395/395、`py_compile`、`git diff --check` 均 PASS；允许 AF_UNIX 的 full
discovery 共 1112 项，其中 1107 PASS，唯一 4 FAIL + 1 ERROR 的测试 identity、结果类型和 marker 仍精确等于
`FINDING-008-020`。因此 raw full suite 仍为 FAIL，deterministic gate 仅为
`PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD`。这些证据只允许提交新的 clean product freeze，不提前给真实产品 Case 下 PASS。
`FINDING-010-020/021` 的 latest-basis/eligible-locator 与 exact call-reserve 修复随后通过 focused 117/117、docs 397/397、`py_compile`、
`git diff --check`；full discovery 增至 1113 项，其中 1108 PASS，唯一 4 FAIL + 1 ERROR 仍保持同一历史 hold identity、marker 与 Codex
digest，没有新增失败。
`FINDING-010-023` 的 fail-closed Browser presentation 与 current Operations write-back 最终通过 focused 118/118、docs 399/399、
`py_compile`、`git diff --check`；full discovery 为 1114 项，其中 1109 PASS，唯一历史 4 FAIL + 1 ERROR identity/type/marker/digest 不变。
首次 full run 曾以新增 ITER-007 system fileset digest mismatch 阻断；同步 ITER-007/010 exact current fileset digest 后针对性 84/84 与最终
full gate 均闭合，因此没有把该新增失败混入 historical hold。
`FINDING-010-024/025` 随后把 FINISH 字段组合与 disposition support/boundary eligibility 提升为 Prompt + 动态 Application 控制；最终
Engineering QA focused 63/63、docs 401/401、`py_compile`、`git diff --check` PASS，full discovery 增至 1115 项，其中 1110 PASS；唯一
4 FAIL + 1 ERROR 的 identity/marker/Codex digest 仍精确保持同一历史 hold。
V-BASELINE/V-ARCH/V-QINTENT/V-COGNITION/V-INVESTIGATE/V-BROKER/
V-LEDGER/V-ISOLATION/V-REVIEW/V-LIMIT/V-SEC 的确定性子断言已有测试证据，但它们的 Case verdict 仍等待 clean freeze 或所要求的真实链；
`V-WEB-000` 前六次永久失败的真实尝试如下。candidate `b8360a3…` 在第二个 Provider output 暴露 live role-progress 大小写错误；2 次
dispatch，见 `FINDING-010-015`。修复后的 candidate `50b08b5…` 继续完成 4 次 dispatch，但目录级 SOURCE capability 的首个 search
耗尽 64 文件上限，后续 Broker 拒绝；模型随后提交含空引用的 FINISH，暴露 Schema/Prompt/shared validator 与领域 invariant 不一致，见
`FINDING-010-016/017`。第三个 candidate `e35d8f7…` 已用新 2-call qualification 和 17 个 exact 文件 Profile 运行；SOURCE search
完整检查 12 文件且未触发 fuse，但自然语言 literal query 返回 0 items 后，模型把 allowlisted path 误作 opaque locator reference，3 次
role dispatch 后失败关闭，见 `FINDING-010-018`。三次 Web run 共 9 次 role dispatch，另有 2 次 current qualification call，累计
11/20，见 `FINDING-010-018`。第四个 candidate `91dffec…` 正确完成 literal search 和 opaque locator read，但重复读取已返回完整内容的
同一路径；相同 progress digest 连续两次触发 no-progress fuse，5 次 role dispatch 后在 Answer/Review 前失败关闭，见
`FINDING-010-019`。四次 Web run 共 14 次 role dispatch，另有 2 次 current qualification call，累计 16/20；全部 retry 0、switch 0、
Production Activation `NOT_EXECUTED`。用户随后把总上限提高到 28；Prompt `@4` clean candidate `1f4e1b0…` 的第五次 run 完成 5 次
dispatch 后，模型未引用紧邻的最新 Ledger Result，并再次选择已返回 full content 的 locator。Application 在 Source operation 前失败关闭，
见 `FINDING-010-020`。五次 Web run 共 19 次 role dispatch，另有 2 次 current qualification call，累计 21/28；第五次仍为 retry 0、
switch 0、Production Activation `NOT_EXECUTED`。Prompt-only 控制已改为显式 latest-basis/eligible-locator 投影与 Application validation；同时
Preview Request call fuse 与 exact run grant 对齐以预留 Answer/Review，见 `FINDING-010-020/021`。旧 candidate/run 不能由后续修复追溯
覆盖。candidate `d6d8d02…` 随后在 7-call exact grant 下完成 Understanding、literal search 和 3 个不同 full-content READ；每步都满足
latest basis/eligible locator，no-progress 0。第 4 次 Investigation 后仍未完成全部 material conclusions，Application 在第 6 个 Provider
dispatch 前保留 Answer/Review 所需 2 次调用并以 `INDEPENDENT_REVIEW_RESERVE_EXHAUSTED` 关闭，Draft/Review 均为 0，见
`FINDING-010-022`。六次 Web run 共 24 次 role dispatch，另有 2 次 current qualification call，累计 26/28；全部 retry 0、switch 0、
Production Activation `NOT_EXECUTED`，剩余 2 次未使用。该 run 还暴露 fail-closed Result 被 UI 固定标成 `REVIEWED RESULT` 的显示缺口，
已按 `FINDING-010-023` 修复；因此 `d6d8d02…` 也成为 burned candidate。用户随后以
`sha256:815d868ca3df4795276934acbc21d12584fcfd4cb49b31c67696c72d3a5a6b74` 取消本次累计调用上限，其他披露/零重试/resources 排除/
非生产边界不变。candidate `31b1a19…` 的第七次 run 完成 7 次 dispatch，Prompt `@5` FINISH 错带 SOURCE evidence class，见
`FINDING-010-024`；candidate `449e925…` 的第八次 run 也完成 7 次 dispatch，字段组合已合法，但把 `SOURCE_RESULT` Ledger entry ID
误作 Package support/boundary reference，见 `FINDING-010-025`。两次都在 Answer/Review 前失败关闭。

clean candidate `f38f6cc…` 的第九次 run `web-v-web-000-012` 以 Prompt `@7` 完成 9 次 dispatch：Understanding、6 次
Investigation、Answer、Review。5 个 Broker Decision 全部授权，no-progress 0；Package 为 37 support/citation + 14 boundary/audit；
Answer 形成 5 个 affirmative claim 和 1 个测试覆盖 limitation，独立 Review `APPROVED`。Browser 显示 `REVIEWED RESULT`，6 个 Source/
World Model Citation 全部实际打开且绑定同一 Package/Result，console 为空。terminal receipt 为 retry 0、switch 0、一次 TLS handshake
复用 8 次、Production Activation `NOT_EXECUTED`；全部 manifest 对 `src/main/resources` 匹配数为 0。九次 Web run 共 47 次 role
dispatch，另有 2 次 current qualification call；详见 `ITER-010-RESULT-V-WEB-000-LIVE-RUN-009`。因此 `V-WEB-000` 由当前 exact run
获得 PASS；旧失败不改写。`V-XD-001` 仍因 `mall` 未形成 declaration/`CALLS` Result 保持独立 blocking，见 `FINDING-010-014`。
随后冻结 4 条不同覆盖维度的公开方向题，suite digest 为
`sha256:f75f2e7881b8b57b4e9dd1b7ff01da9ac322bb4c853ed1853f881db9ca74f100`；现场题仍由用户持有。第一题绑定 clean candidate
`aa14234…`，在 5 次 dispatch 后因调查角色重复 `SOURCE / search("mall-security")` 触发 `NO_PROGRESS_FUSE_EXHAUSTED`，retry/switch 0、
Production Activation `NOT_EXECUTED`。`FINDING-010-026` 已把此前未投影的 attempt-scoped query/locator intent 加入 Ledger/角色输入，并由
Broker 在 Worker 前拒绝重复工作；Prompt 升级为 `@8`。该题与 candidate 永久失败，不重放。

修复后的 clean candidate `17cff66…` 只消费 successor freeze 中的 Q2—Q4，三题分别以 8/8/9 dispatch、0 no-progress 到达独立 Review
`APPROVED`；11 个 Citation 全部打开，公开题总分为 3 supported / 1 fail，达到两个非实现维度阈值。用户随后以 exact message digest
`sha256:684849e3…e9c9` 现场提出“登录流程是怎样的？”。clean candidate `8632904…` 的全新 onsite run 以 10 dispatch、6 个只读 Broker
operation、0 no-progress 形成 Result `engineering_result_e5f3c335944de0f2f57e8f9fdd48b419` 和 Review `APPROVED`；3 个 exact Source
Citation 全部打开、console `[]`、retry/switch/outcome-unknown 0、resources match 0、Production Activation `NOT_EXECUTED`。因此公开 4 题
与现场题合并后 `V-WEB-001` 技术 PASS。`FINDING-010-027` 同时保留正文仍以 Controller/Service/Filter 方法调用序列为主且省略
`insertLoginLog` 副作用的方向信号；用户随后以
`codex-user-message:sha256:d746968f58cea4d2b7689b5902c0ff97f42f63c93ffc4cbc40551cfa2c0359e0` 要求实现者自行复核并修复已知问题；旧记录曾将其解释为 `REDIRECT`。
`FINDING-010-028` 将共同根因定位到自由文本抽象层级、扁平 Answer Claim 和不可执行的 Review 方向质量 Gate。因此历史
`V-ANSWER-001`、`V-REVIEW-001`、`V-XD-001` 与 `V-PREVIEW-001` 继续为 FAIL；`V-REFLECT-001` PASS 只表示失败复盘完整。

[PDR-001](decisions/PDR-001-resume-as-rework.md) 依据最新用户收据修订的是迭代级决定，不改写上述执行事实。旧消息 `d746968f…` 没有明确
表达 `REDIRECT`；后续 `32b298de…` 收据已恢复 ITER-010/Slice1 的编码，live 仍未获得新 freeze 后授权。当前必须先执行以下持续 Web
Alpha Case，不能用旧的单题启动器、测试或固定 1+1 回放代替。

用户随后提供的 root + exact mall/DeepSeek scope 已授权持续 Alpha。candidate `b6e13eb…` 的首次会话真实启动并以 8 次 role dispatch、
retry/switch 0 回答现场登录题；完整 `UmsAdminServiceImpl` 已进入 Package/Reviewer，但正文再次遗漏成功登录审计写入，Reviewer 错误
`APPROVED`。该 Result 只把 `V-EXPERIENCE/V-ANSWER-REWORK` 推进为 in-progress，并以 `FINDING-010-033` 保留失败，不能取得 PASS。会话还
暴露 Gateway SQLite 主文件为 `0644`，见 `FINDING-010-034`。当前 worktree 已升级
`ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3`：FINISH 原子 evidence observations、Answer observation/evidence closure、Reviewer 独立
Package/Draft observation audit，以及 SQLite 主文件/WAL/SHM `0600` 创建测试均通过；新协议仍须 clean freeze、current Conformance 和完整
原题 + 两道异质题 + 受控失败的持续 browser run。

Engineering QA 83/83、docs/freeze/browser 86/86、current docs 427/427 PASS；在允许 AF_UNIX 的本机执行面运行 full 1144 项得到 1139 PASS，
raw 仍精确为既有 4 FAIL + 1 ERROR，见 `FINDING-010-035`。默认沙箱额外出现的 AF_UNIX denial 不属于产品回归，raw full suite 仍不写成
PASS。

clean candidate `fc827ce…` 已取得 current DeepSeek Conformance `sha256:c6f6a0f…` 并真实提交原题。5 次 role dispatch、retry/switch 0；
Package 与 Answer affirmative 正文已显式覆盖 `loginLogMapper.insert` 审计写入，Gateway 主文件/live WAL/SHM 为 `0600`。但 Answer 的末尾
coverage-only Limitation 因非空 link 规则错绑全部 supported observations，Application 以 `answer claim kind differs from its material
observation` 失败关闭；见 `FINDING-010-036`。该 Result 不能取得答案或体验 PASS。

coverage-only Limitation 收窄后的 Answer/strategy/model-source 49/49、Engineering QA 86/86、current docs 430/430 PASS；最终 full 1147 项
中 1142 PASS，raw 仍精确为既有 4 FAIL + 1 ERROR，见 `FINDING-010-037`。新修复尚未取得 clean freeze 后的 live Result。

clean candidate `e15ec50…` 与 current Conformance `sha256:5ef04be6…` 的原题 run 同样为 5 次 role dispatch、retry/switch 0、private SQLite。
上一修复的空-link coverage Limitation 已生效；但 Investigation 只读 README 后过早 FINISH，Answer 将 limitation observations 错标为
process/impact roles，Domain 以 structured-output violation 失败关闭。`FINDING-010-038` 已形成 closed kind/role mapping 与跨 evidence-class
unknown 消减规则，尚待新 clean candidate live 重验。

closed mapping/跨 evidence-class 修复后的 clean candidate `c7e32b5…` 以 current Conformance `sha256:8802280…` 启动同一持续会话。原现场题
用 7 次 dispatch 形成 `APPROVED` Result：固定 revision 的 Controller/Service Source、正文和独立 Reviewer 都覆盖登录主链、
`SecurityContext`、JWT、失败分支与 `loginLogMapper.insert` 审计副作用，private SQLite 成立。随后两道异质题均在首个角色调用收到
`PROVIDER_HTTP_ERROR`，每题一次调用、retry/switch 0，listener 继续；受控超限页面请求在 Provider 前拒绝，调用根不增加且 health 保持
`READY`。旧实现却把已知 HTTP 失败在页面/terminal audit 重标为 binding drift/outcome unknown，见 `FINDING-010-039`。因此该会话只证明
原题质量修复和请求隔离，不能取得三题 PASS；错误传播/审计修复的 Engineering QA 全组 87/87 PASS，仍须新 clean candidate live 重验。
允许本机 AF_UNIX 的完整回归为 1148 项、1143 PASS，raw 唯一 4 FAIL + 1 ERROR 仍与既有 V-009/Codex historical hold 完全相同，见
`FINDING-010-040`；默认沙箱额外 6 ERROR + 1 FAIL 精确属于 socket permission noise，不进入产品失败集合。

clean candidate `31a9ccd…` 随后使用正确 DeepSeek CLI 发起新的 current Conformance；run
`ccrun_717391edb4c6482d8809dd45be405626` 在第一次 dispatch 收到 HTTP 402，Result `sha256:44bf29b…` 为 FAIL、qualification
`NOT_ISSUED`、request 1、retry 0、TLS/credential 成功。官方错误码将 402 定义为余额不足，见 `FINDING-010-041`。旧 run-008 adapter
qualification 仍在有效期且 implementation/config digest 相同，但不证明当前账户可用或新候选三题质量；因此 live 保持 environment-blocked，
不得重试、切 Provider 或用旧答案补齐。

余额恢复后的后续候选最终推进到 clean `5ce5ab0…` 与 run-015 fresh DeepSeek Conformance 2/2 PASS。同一持续会话 3 题共 32 dispatch、
retry/switch 0，但 raw SQLite 复核否定页面的两个 `APPROVED`：原登录题再次漏掉 `insertLoginLog` 审计副作用；混合 support/unknown 题
输出两个 `DIRECT_ANSWER` 而失败关闭；401/403 题用 `SecurityConfig` 接线替代未读取的动态 manager 自身实现。见
`FINDING-010-048`。受控超限仍在 Provider 前拒绝，private files 与 Production `NOT_EXECUTED` 成立；这些安全/隔离事实不构成答案质量
PASS。当前 mandatory-read path、唯一 direct-answer shape 与独立 side-effect audit 的定向组合 96/96、docs 442/442 PASS；允许本机
AF_UNIX 的 full 1162 项中 1157 PASS，唯一 4 FAIL + 1 ERROR 仍精确为冻结 V-009/Codex historical hold。仍须 clean freeze、fresh
Conformance 和完整三题重验。

该处置形成 clean `00afecd…`，run-016 fresh DeepSeek Conformance 2/2 PASS；同一持续会话三题分别用 12/13/13 次 dispatch，全部未形成
交付答案。原题的第 12 次总 dispatch 为 post-dispatch `PROVIDER_OUTCOME_UNKNOWN`，Gateway raw state 正确但页面误报 binding drift；
另两题的 Question Understanding 分别声明 8/6 个 mandatory-read paths，12 次 Investigation 被 search/read 和非必读 locator 消耗，无法
FINISH。terminal receipt `sha256:b3c94c2…` 记录 38 dispatch、retry/switch 0、private files、Production `NOT_EXECUTED`；22,000 字符
输入仍在 Provider 前拒绝且 call root 不增加。见 `FINDING-010-049`。当前 4-path/fuse reachability、required-locator priority、remaining-fuse
投影与 exact outcome-unknown propagation 的 Engineering QA 组合 97/97、docs 444/444、compile/diff PASS；允许 AF_UNIX 的 full
1163 项中 1158 PASS，raw 唯一 4 FAIL + 1 ERROR 仍精确为冻结 V-009/Codex historical hold，见 `FINDING-010-050`。新 clean candidate
与 fresh live 仍待执行。

该处置形成 clean `d12223f…`，run-017 fresh DeepSeek Conformance 2/2 PASS。三题调查均在 4-path/12-call contract 内进入 Answer；混合
构建/安全/resources unknown 题以 14 次 dispatch 获得 `APPROVED`，并把 resources 中运行参数保留为未知。原登录题与 401/403 题分别以
9/12 次 dispatch 到达 Answer，却都因 follow-up claims 的 role 次序为“process → impact → process …”在 Review 前失败关闭；raw claims 的
checklist、observation、evidence links 完整。terminal receipt `sha256:e901faf2…` 记录 35 dispatch、retry/switch 0、private files、
Production `NOT_EXECUTED`，22,000 字符输入在 Provider 前拒绝且 call root 不变。见 `FINDING-010-051`。可信 adapter 的受控稳定排序回归
已使 Engineering QA 98/98 PASS；docs 446/446、compile/diff PASS，允许 AF_UNIX 的 full 1164/1159，raw 唯一 4 FAIL + 1 ERROR 仍为
冻结 historical hold，见 `FINDING-010-052`。新 clean/fresh live 尚未闭合。

该处置形成 clean `88e33bd…`，run-018 fresh DeepSeek Conformance 2/2 PASS。原登录题与构建/resources unknown 题分别以 13/15 次
dispatch 得到 `APPROVED`；401/403 题以 8 次 dispatch 形成三个检查面、401/403 区分、Citation 和独立
`IMPLEMENTATION_EVIDENCE` 核对依据，但后者独自绑定的 3 个 material observations 被默认正文无条件隐藏，因而在 Review 前失败。
terminal receipt `sha256:08d84045…` 记录 36 dispatch、retry/switch 0、private files、Production `NOT_EXECUTED`，22,000 字符输入在
Provider 前拒绝且 call root 不变。见 `FINDING-010-053`。conditional implementation-evidence visibility 的 Engineering QA 99/99 PASS；
docs 448/448、compile/diff PASS；允许 AF_UNIX 的 full 1165 项中 1160 PASS，raw 唯一 4 FAIL + 1 ERROR 仍为冻结 historical hold，见
`FINDING-010-054`。确定性 Gate 已闭合，新 clean/fresh live 尚未执行。

该处置形成 clean `c65617e…`，run-019 fresh DeepSeek Conformance 2/2 PASS。同一持续会话三题分别以 12/15/12 次 dispatch 获得模型
`APPROVED`，且第三题 requested implementation evidence 已进入默认正文；但独立技术复核发现其一处把未认证与权限不足都归为 403，后一处
又正确区分为 401/403。raw Review 逐字复述冲突仍将四项 quality 全部 PASS。terminal receipt `sha256:cfed19a1…` 记录 39 dispatch、
retry/switch 0、private files、verified transport、Production `NOT_EXECUTED`；超限输入在 Provider 前失败且 call root 保持 39。见
`FINDING-010-055`。新增第五项 closed `claim_consistency` 已有三模块 62/62 定向证据，完整 deterministic 与 fresh live 尚未闭合。

上述修复最终通过 Engineering QA 99/99、docs 450/450、compile/diff；允许 AF_UNIX 的 full 1165 项中 1160 PASS，raw 唯一 4 FAIL +
1 ERROR 仍为冻结 historical hold，没有 ITER-010 新失败，见 `FINDING-010-056`。确定性 Gate 已闭合，新 clean/fresh live 尚未执行。

该处置形成 clean `274e5ea…`，run-020 fresh DeepSeek Conformance 2/2 PASS。Q1 以 10 次 dispatch 获得独立可接受的 `APPROVED`；Q2 已
声明 4 个 mandatory paths，却因没有 direct locator 而把 path/filename 当内容搜索词，5 次 dispatch 后触发
`NO_PROGRESS_FUSE_EXHAUSTED`；同一 listener 随后接受 Q3，后者以 11 次 dispatch 完整读取四个决定性实现，却在一个 `SUPPORTED`
FINISH item 混入 `LIMITATION` 与 search-only boundary reference，被本地 validator 以 `STRUCTURED_OUTPUT_INVALID` 正确关闭。22,000
ASCII 字符约 22 KB，低于 65,536-byte server limit，合法发生 1 次 dispatch 后人工停止；terminal receipt `sha256:1408e827…` 记录
4 题、27 dispatch（10/5/11/1）、retry/switch 0、verified transport 与 Production `NOT_EXECUTED`。见 `FINDING-010-057/058`。
Request + attempt + Profile-bound direct locator、结构互斥 FINISH arrays 和 modality-minimal Understanding Prompt 的 Engineering QA
101/101、docs/compile/diff PASS；允许 AF_UNIX 的 full 1167 项中 1162 PASS，raw 唯一 4 FAIL + 1 ERROR 仍为冻结 historical hold，见
`FINDING-010-059`。确定性 Gate 已闭合，新 clean/fresh live 尚未执行。

该确定性处置形成 clean `dfba244…`，run-021 fresh Conformance 2/2 PASS。同一持续 Alpha 中，Q1/Q3 各以 8 次 dispatch 得到独立可接受的
`APPROVED`；Q2 的 4 个 mandatory paths 已全部通过 direct locator READ，但第 5 个 Investigation call 在仍有 8 个含当前动作 call 时
FINISH，并把 3 个 UNKNOWN 同时放入 supported 与 non-supported arrays，被本地 Schema 以 `STRUCTURED_OUTPUT_INVALID` 正确关闭。
Q2 后 listener 继续接受 Q3；66,000-byte 输入在 Provider 前拒绝且 Gateway 根保持 22。terminal receipt `sha256:d38d94bb…` 记录
8/6/8 dispatch、retry/switch 0、verified TLS、private files 和 Production `NOT_EXECUTED`。见 `FINDING-010-060`。当前 exact-once
partition 与 post-mandatory material-gap exhaustion 的 Engineering QA 101/101、docs/compile/diff PASS；允许 AF_UNIX 的 full 1167 项中
1162 PASS，raw 唯一 4 FAIL + 1 ERROR 仍为冻结 historical hold，见 `FINDING-010-061`。deterministic Gate 已闭合，新 clean/fresh live
尚待执行。

该处置形成 clean `be15a0a…`，run-022 fresh Conformance 2/2 PASS。Q1 的 Understanding 正常；第一个 Investigation 选择合法 direct
locator、current required basis 与空 FINISH partitions，却返回空 `checklist_item_ids`。Domain 以 structured-output violation 正确关闭，
证明 Provider Schema 与 non-empty/unique Domain binding contract 不一致。会话在 2 次 dispatch 后停止，未提交 Q2/Q3 或超限输入；
retry/switch 0、verified TLS、private files 和 Production `NOT_EXECUTED`，不能借 run-021 补齐。见 `FINDING-010-062`。当前修复把 Initial/
Verification checklist/basis binding arrays 的 Provider Schema、Prompt 与 Domain 对齐；完整 deterministic 与新 clean/fresh live 待闭合。

该 Schema—Domain 修复的三模块定向 65/65、Engineering QA 102/102、docs/compile/diff PASS；默认 sandbox full 1168 项为 5 FAIL +
7 ERROR，允许 AF_UNIX 后为 1163 PASS，raw 唯一 4 FAIL + 1 ERROR 仍精确是冻结 V-009/Codex historical hold，没有 ITER-010 新失败。
见 `FINDING-010-063`。deterministic Gate 已闭合，新 clean candidate/fresh live 仍待执行。

该处置形成 clean `656b549…` / run-023：fresh Conformance 2/2 PASS，同一 listener 顺序完成三题 8/8/7 dispatch，retry/switch 0、
verified TLS、private files、Production `NOT_EXECUTED`；66,000-byte UTF-8 输入在 Provider 前拒绝且 Gateway 根保持 23。Q1/Q2 独立
可接受；Q3 虽获模型 `APPROVED`，却仅凭 empty authentication context 与 authorization deny 推导最终 401/403，把同一局部条件赋予
互斥外部结果，Reviewer 仍误判 consistency PASS。见 `FINDING-010-064`。Prompt/Contract 现要求下游 response/exception mapper
full-content ownership evidence，拒绝用 handler wiring/framework default 补写外部输出，并区分 transport status 与 response-body code；
定向 65/65、Engineering QA 102/102、compile/diff PASS，完整 docs/full 与新 clean/fresh live 待闭合。

`FINDING-010-065` 已闭合该修复的 deterministic Gate：current docs 459/459、compile/diff PASS；默认 sandbox full 1168 项为 5 FAIL +
7 ERROR，其中新增 1 FAIL + 6 ERROR 精确来自 AF_UNIX 禁止；允许 AF_UNIX 后同一 1168 项为 1163 PASS，raw 唯一 4 FAIL + 1 ERROR
仍是冻结 V-009/Codex historical hold，没有 ITER-010 新失败。新的 clean candidate/fresh live 仍待执行。

该处置形成 clean `740c74a…` / run-024：fresh Conformance 2/2 PASS，同一 listener 完成 Q1/Q2/Q3 共 25 次 dispatch（6/14/5），
retry/switch 0、逐题 verified TLS、private files、Production `NOT_EXECUTED`；66,000-byte UTF-8 输入在 Provider 前拒绝且 Gateway 根保持
25。Q1 的 child observation 引用未被 Provider 完整重抄到 parent，Q3 把 UNKNOWN item 重复分装进两个 FINISH arrays；Q2 Reviewer
两次明确识别 dynamic authorization implementation 缺证，却分别维护成 `REWRITE_REQUIRED + null request` 并触发 same-Package rewrite
fuse。见 `FINDING-010-066/067`。现已将 FINISH 收敛为单一 outcome-tagged array 并由 trusted Adapter 派生 parent reference closure；Review
只返回 typed Finding remediation，由 Application 派生 action 与 Verification Request。`FINDING-010-068` 同时校正历史 ITER-007 oracle
把冻结摘要用 current System 文档重算的测试缺陷。最终 Engineering QA 106/106、current docs 463/463、含 docs Gate 139/139、compile/diff PASS；默认
sandbox full 1172 项为 5 FAIL + 7 ERROR，其中额外 1 FAIL + 6 ERROR 精确属于 AF_UNIX 禁止；允许 AF_UNIX 的同一 full 为 1167 PASS，
raw 唯一 4 FAIL + 1 ERROR 仍为冻结 historical hold，见 `FINDING-010-069`。deterministic Gate 已闭合，
新的 clean candidate/fresh live 仍待执行。

该处置形成 clean `7fb7e7c…` / run-025：fresh Conformance 2/2 PASS；同一 listener 完成 Q1/Q2/Q3 共 33 次 dispatch（8/13/12），
retry/switch 0、逐题 verified TLS、private files、Production `NOT_EXECUTED`；66,000-byte UTF-8 输入在 Provider 前拒绝。Q1 独立可接受且
四个 Citation 已打开核对。Q2 的 Reviewer 正确派生只绑定 `check-3` 的 Verification Request，补证 FINISH 也正确返回单项 delta，却被
Application 旧“全 Checklist exact-once”规则拒绝。Q3 所需 handler implementation 不在 exact allowlist，重复 intent 被 Broker 拒绝并由
no-progress fuse 安全关闭。见 `FINDING-010-070/071`。当前处置把 Verification FINISH 收窄为 authorized single-gap delta，由可信
Application stable merge，并投影 Package full reads 与最新 Broker rejection；run-025 仍为 1 PASS + 2 FAIL，新 deterministic Gate 与
clean/fresh live 均待闭合。

`FINDING-010-072` 已闭合该修复的 deterministic Gate：Engineering QA 109/109、docs 组合 142/142、历史 oracle 组合 74/74、current docs
466/466、compile/diff PASS；默认 sandbox full 1175 项为 5 FAIL + 7 ERROR，允许 AF_UNIX 后为 1170 PASS，raw 唯一 4 FAIL + 1 ERROR
仍精确属于冻结 V-009/Codex historical hold，没有 ITER-010 新失败。新的 clean candidate/fresh Conformance 与三题仍是下一 Gate。

clean `32a00a3…` / run-026 完成 fresh Conformance 与同一 Browser 会话三题：8/12/14 dispatch、retry/switch 0、66,000-byte 输入在
Provider 前拒绝、private files 与 Production `NOT_EXECUTED` 成立。Q1 `APPROVED`；Q2 证明 Verification limitation 可错借 predecessor
Package 的无关 cognition unknown，Q3 证明 Reviewer 可重复请求已经 bounded Verification 穷尽且诚实披露的同一 gap。两题均安全失败，
run-026 保持 1 PASS + 2 FAIL。`FINDING-010-073` 已排除 predecessor boundary、强制每个非支持 child 绑定 current gap，并投影 terminal
typed `VERIFICATION_GAP` 给 Reviewer；三模块 76/76 PASS，扩展 deterministic/fresh live Gate 待闭合。

`FINDING-010-074` 已闭合 deterministic Gate：Engineering QA 113/113、docs 组合 146/146、历史 oracle 组合 78/78、
current docs 468/468、compile/diff PASS；默认 sandbox full 1179 项为 5 FAIL + 7 ERROR，允许 AF_UNIX 后为 1174 PASS，raw
唯一 4 FAIL + 1 ERROR 仍精确属于冻结 V-009/Codex historical hold。新 clean candidate/fresh live 仍是下一 Gate。

clean `b709fad…` / run-027 的 fresh Conformance 2/2 PASS；同一 Browser 会话三题共 23 dispatch、retry/switch 0，66,000-byte 输入在
Provider 前拒绝，private files、console clean 与 Production `NOT_EXECUTED` 成立。Q1 独立复核 PASS；Q2/Q3 虽被页面错误标为
`APPROVED`，但 raw evidence 证明 placeholder 被扩张为具体 header、caller/import 被扩张为未挂载 DTO fields/handler output、上游
local decision 被扩张为下游 401/403。23 calls 没有 Verification，唯一 Reviewer 复述同一扩张并五项全 PASS，实际仍为 1 PASS + 2 FAIL。
`FINDING-010-075` 已要求 comprehensive provisional Review 后运行 fresh evidence-boundary challenge，Application 投影三类通用 leads，
Gateway 强制 focus 顺序，Authorization 只接受 challenge。focused 78/78、Engineering QA 115/115 PASS；docs/oracle/full deterministic
Gate 与新 clean/fresh live 仍待闭合。

`FINDING-010-076` 已闭合 deterministic Gate：docs 组合 148/148、历史 oracle 组合 80/80、current docs/compile/diff PASS；默认
sandbox full 1181 项为 5 FAIL + 7 ERROR，允许 AF_UNIX 后为 1176 PASS，raw 唯一 4 FAIL + 1 ERROR 仍精确属于冻结
V-009/Codex historical hold，没有 ITER-010 新失败。新 clean candidate/fresh live 仍是下一 Gate，run-027 不追认。

clean `f832ceb…` / run-028 的 fresh Conformance 2/2 PASS；同一 Browser 会话三题共 26 dispatch（9/9/8）、retry/switch 0，66,000-byte
输入在 Provider 前拒绝且调用数不变，private files、console clean、listener continuity 与 Production `NOT_EXECUTED` 成立。Q1/Q3 独立
PASS；Q2 虽保留具体配置值为未知，却把 caller getter 扩张为未挂载 DTO field/wire property。fresh challenge 已收到 exact type lead 仍原样
复述并错误 `APPROVED`，实际为 2 PASS + 1 FAIL。`FINDING-010-077` 已要求 Application-owned stable challenge ID、逐项
evidence/Draft scope assessment、exact ID 集合重算与越界 Finding-on-challenged-Claim 绑定；focused 78/78、Engineering QA 115/115
PASS，扩展 deterministic 与新 clean/fresh live 待闭合。

`FINDING-010-078` 已闭合 deterministic Gate：docs 组合 148/148、历史 oracle 组合 80/80、current docs/compile/diff PASS；默认
sandbox full 1181 项为 5 FAIL + 7 ERROR，允许 AF_UNIX 后为 1176 PASS，raw 唯一 4 FAIL + 1 ERROR 仍精确属于冻结
V-009/Codex historical hold，没有 ITER-010 新失败。新 clean candidate/fresh live 仍是下一 Gate，run-028 不追认。

clean `e0ad3c8…` / run-029 的 fresh DeepSeek Conformance 2/2 PASS；同一持续 Browser 会话三题共 28 dispatch（9/11/8），retry/switch/
outcome-unknown 0，66,000-byte 输入在 Provider 前拒绝且调用数不变，private files、console clean、listener continuity 与 Production
`NOT_EXECUTED` 成立。答案质量为 0/3：Q1 被错误 `APPROVED` 但遗漏 Service full entry 中的登录审计持久化副作用；Q2 正确识别未挂载
DTO 扩张后，rewrite 又丢掉另一个安全 material observation，并由 Application 失败关闭；Q3 正确识别 401/403 扩张，但 assessment 的
Finding Claim 与 exact challenge scope 错绑并由 Application 失败关闭。`FINDING-010-079` 已投影逐 cited full-content Java entry 的
material-effect scan，增加 `DRAFT_OMITS_MATERIAL_EFFECT`，为 Answer 提供 early exact observation coverage table，并明确所有非 passing
assessment 的 exact challenged-Claim binding。focused 79/79、Engineering QA 116/116 PASS；扩展 deterministic 与新 clean/fresh live
待闭合，run-029 不追认。

`FINDING-010-080` 已闭合 deterministic Gate：docs 组合 149/149、历史 oracle 组合 81/81、current docs/compile/diff PASS；默认
sandbox full 1182 项为 5 FAIL + 7 ERROR，允许 AF_UNIX 后为 1177 PASS，raw 唯一 4 FAIL + 1 ERROR 仍精确属于冻结
V-009/Codex historical hold，没有 ITER-010 新失败。新 clean candidate/fresh live 仍是下一 Gate，run-029 不追认。

clean `9ae982b…` / run-030 的 fresh DeepSeek Conformance 2/2 PASS；同一持续 Browser 会话三题共 36 dispatch（14/14/8），retry/switch/
outcome-unknown 0，66,000-byte 输入在 Provider 前拒绝且调用数不变，private files、console clean、listener continuity、clean SQLite
checkpoint 与 Production `NOT_EXECUTED` 成立。Q1 最终覆盖登录审计持久化，Q3 正确区分 token 校验、SecurityContext 与动态权限并保留
handler mapping unknown，两题独立 PASS；Q2 虽被页面错误 `APPROVED`，却没有把登录响应 token/tokenHead 交接为受保护请求输入，也没有
明确 configuration-backed header/prefix unknown，实际 2 PASS + 1 FAIL。见 `FINDING-010-081`。

`FINDING-010-082` 已增加 operational Question Understanding/Answer handoff、通用 `ORIGINAL_QUESTION_FULFILLMENT_SCAN`、
`DRAFT_OMITS_MATERIAL_REQUIREMENT` 与专用 disposition/challenge-kind matching。focused 80/80、Engineering QA 117/117 PASS；
`FINDING-010-083` 再以 docs 组合 150/150、历史 oracle 组合 82/82、current docs/compile/diff 与允许 AF_UNIX 的 full 1183/1178
exact historical hold 闭合 deterministic Gate；没有 ITER-010 新失败。新 clean candidate/fresh live 仍是下一 Gate，run-030 不追认。

clean `3c45072…` / run-031 的 fresh DeepSeek Conformance 2/2 PASS；Q1 使用 12 dispatch，retry/switch/outcome-unknown 0，但第二次
challenge 发现 cache write 时没有声明 Application observation omission，错误请求第二次同包 rewrite，最终
`SAME_PACKAGE_REWRITE_FUSE_EXHAUSTED` / Q1 FAIL；Q2/Q3 与 66,000-byte 负测未执行。`FINDING-010-084` 要求 exact omitted-effect
statements 与 `APPLICATION_PACKAGE / DEFAULT_DRAFT` layer，并由 Application 重算 observation membership、entry/evidence class 与
remediation；不放宽 rewrite fuse。`FINDING-010-085` 以 focused 80/80、Engineering QA 117/117、docs 组合 150/150、历史 oracle 组合
82/82、current docs/compile/diff 与允许 AF_UNIX 的 full 1183/1178 exact historical hold 闭合 deterministic Gate。新 clean/fresh live
仍待执行，run-031 不追认。

| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |
|---|---|---|---|---|---|---|
| V-EXPERIENCE-001 | 同一产品成为可持续体验的 Web Alpha | product / browser | 一条固定且文档化的启动命令；`http://127.0.0.1:8765/`；固定一个工程和 exact revision；同一启动会话提交原失败题、至少两个相邻或异质问题及一个受控失败场景 | 无认证；体验者不拼装逐题 freeze/grant/run 参数；连续自由提问无需逐题重启；页面显示产品/工程版本、已知限制、答案/Citation/请求失败；受控失败只关闭当前 Request，服务继续且 identity 不串扰；Gateway DB/WAL/SHM 从创建起为 `0600`；答案真实经过世界模型—调查—Broker/Source—证据链而非预制回放；无平行演示入口 | run-033 完成同会话三题与 Provider 前负测，但答案为 Q1/Q2 FAIL、Q3 OUTCOME_UNKNOWN；run-034 又在 fresh Conformance 第一次 dispatch 收到 HTTP 402，因而无 Alpha。持续运行或确定性 PASS 都不能替代新的完整 live 质量 Gate | FAIL / blocking |
| V-ALPHA-ACCESS-001 | PDR-004 下在答案质量验收前先交付真实、可操作 Chat Web | product / access | 固定启动命令、loopback 页面、消息历史、“新对话”、Provider/失败状态；最多一个 Provider 前本地或 Mock Access smoke | 页面无需认证；能建立/继续/新建 Conversation 并真实提交 Turn；明确“质量未验收/非生产”；Provider 未配置/未资格/失败如实显示而不阻塞页面；完成后立即把命令、URL、版本和限制交给用户，不等待 Chat/Quality/Comparison；静态回放不通过 | `ITER-010-RESULT-V-ALPHA-ACCESS-001 / FINDING-010-096`：clean `cf2883b…` 固定 listener + in-app Browser；同会话两次失败仍 ACTIVE/历史完整，新会话不同 identity/EMPTY CONTEXT/旧消息不泄漏；2 Conversation、3 Turn、Provider dispatch 0、console clean、Production 未执行；listener 已优雅停止 | PASS / blocking |
| V-TIMEBOX-001 | 体验优先、根因优先与轻量 live-attempt 纪律成立 | project / delivery | Slice 授权后首个产品变化时间、page/alpha/hard-stop 时间、qualification/smoke/full-regression 计数、sealed version/question/provider dispatch audit、failure signatures、最早偏差层、可证伪根因假设、本地最小复现、两个未参与修复的相邻案例、用户可见增量 | 60/180/240 检查点可核对；本轮已超过 hard stop 并停止 scope expansion/external batch；首次体验前 qualification≤1、smoke≤1、full regression=0 且仅跑 targeted impact/startup/safety；无根因假设不得改 Prompt/Schema/Contract；本地最小复现与两个相邻案例通过后才跑一题 canary；同签名只修一次，复现则架构职责评审；连续两次无用户可见增量停止外部重跑；full regression 只在 Alpha CONTINUE 后 hardening 与正式验收前 | 用户报告约14小时无新体验；PDR-003 hard-stop/root-cause recovery active | FAIL / blocking |
| V-TIMEBOX-CHAT-001 | PDR-004 下体验优先、根因优先与逐 Turn live-attempt 纪律成立 | project / delivery | 四个微检查点的 60/180/240/360/480 审计与逐点用户交付；Turn1 前冻结的同一五轮 Conversation 脚本及前三轮中间交付；qualification/Access-smoke/full-regression 计数；Conversation/Turn/provider dispatch、failure signature、根因与用户可见增量 | 60 分钟页面；180 分钟同一五轮脚本前三轮方向 Alpha 交付线，未交即 timebox FAIL；181—239 分钟迟到 Alpha 只作 `FAIL / REWORK` 证据；240 分钟绝对停止；360 分钟五轮方向证据；480 分钟独立比较与用户判向；每个检查点立即交付用户；三轮停止时五轮 canary 为 `INCOMPLETE / FAIL`；计划/测试/文档完成不算用户可见增量；错过时交付最后可运行版本与最早根因并停止扩张；每个 Provider-dispatched Turn 分别计 live attempt 且不削减证据/Citation/Review | `FINDING-010-107 / run-035-chat-alpha`：固定五轮全部执行但 5/5 失败且没有用户可见 Answer/Citation/Review；比较未启动 | FAIL / blocking |
| V-CHAT-EXPERIENCE-001 | 同一产品成为可持续体验的多轮 Chat Alpha | product / browser | 一条固定启动命令；loopback；固定工程/exact revision；一个冻结五轮 Conversation 脚本；“新对话”泄漏负测 | 无认证；体验者不拼装内部参数；消息历史显示语义 follow-up/correction/deepening/summary；失败只关闭当前 Turn；新 Conversation 必须澄清省略指代且不继承旧 Context/Evidence/provider memory；不得反向阻塞已完成的页面用户交付 | `FINDING-010-107 / run-035-chat-alpha`：五轮均失败；新 Conversation 隔离但省略指代返回通用失败而非澄清 | FAIL / blocking |
| V-CHAT-001 | 主 Agent 完成真正语义多轮 Chat 且新对话不泄漏 | product / chat | 一个 Conversation 的五轮脚本：初始问题→省略指代追问→用户纠正前提→进一步区分/深入→按当前 Context 总结；随后新 Conversation 省略指代 probe | Context 维护确认目标/约束、实体/主题、开放问题、reviewed/superseded conclusion refs 与 provenance；模糊指代先澄清；每轮独立 Evidence/Answer/Review；新对话 probe 必须澄清且不继承旧 Context/evidence/provider memory；不得反向阻塞首次用户交付 | `FINDING-010-107 / run-035-chat-alpha`：5/5 Turn 无 Answer；新 Conversation 没有旧消息，但 probe 未澄清 | FAIL / blocking |
| V-ANSWER-REWORK-001 | 答案与 Reviewer 的已知缺陷以通用机制修复 | product / quality | 一题 live canary 独立 PASS；原现场登录题；至少两个相邻或异质题；至少一题非实现走读；独立技术复核 | canary 失败不启动三题；重大错误 0；重要结论有 Citation；comprehensive 首审后必须由 fresh challenge 按 stable ID 逐项阻断层级错配、逐 full-entry material effect 遗漏、原问题动作/handoff/known-unknown 履约遗漏、配置值/未挂载类型/下游 status 扩张、无据结论和错误 Citation；material-effect omission 必须绑定 exact `APPLICATION_PACKAGE / DEFAULT_DRAFT` layer 与合法补证/rewrite；rewrite 必须保留全部安全 observation；所有非 passing assessment 必须绑定 exact challenged Claim；无工程/问题/关键词/符号/类/方法/fixture/Oracle 特判 | run-033 因 supported predecessor observations 被 replacement 删除而不通过；`FINDING-010-088/089` corrective deterministic Gate 已闭合。run-034 仅取得 HTTP 402 Conformance FAIL，未生成新答案证据 | FAIL / blocking |
| V-CHAT-QUALITY-001 | 五轮每个 Turn 的答案与独立审核以主 Agent 通用机制满足质量 | product / quality | `V-CHAT-001` 五轮逐 Turn Context/Work State/Ledger/Package/Answer/Review；fresh independent Reviewer | 每 Turn 重大错误 0、重要结论有 Citation；prior Answer/Review 不作事实；旧 evidence 仅 exact identity/coverage 匹配且重绑当前 Package；Reviewer 只返回 Finding，Finding 回主 Agent 补证或重写并形成全新 identity；主 Agent/Reviewer 无直接 Source/FS/Shell/network/credential/write 权限；无特判；不得反向阻塞首次用户交付 | `FINDING-010-107 / run-035-chat-alpha`：五轮均未形成 Answer、Citation、Review 或 Delivery | FAIL / blocking |
| V-CHAT-XD-001 | 主 Agent 在同一多轮答案链中组合 World Model Cognition 与 query-time Source 证据 | product / integration | 五轮 Conversation 中至少一个需要 accepted World Model 认知与 repository source/doc/config/test 证据的 Turn；exact Context/Work State/Ledger/Package/Answer/Review | 一个主 Agent 在同一 Turn 组合两类认知，结论分别绑定正确 Citation；World Model 不退化为 locator，Source 不绕过 Broker/Worker；无两个平行答案、模式拼接或旧 `V-XD-001` 证据追认；不得反向阻塞首次用户交付 | `FINDING-010-107 / run-035-chat-alpha`：Source 调查在 evidence/Answer 组合前耗尽 no-progress fuse，未形成认知+Source 答案链 | FAIL / blocking |
| V-COMP-ALPHA-001 | Chat canary 后立即产出主 Agent/World Model 方向信号 | product / comparison | 同一 exact revision、冻结 Conversation 脚本、可比较输出和 rubric；current Codex external baseline；same-agent source-only；same-agent full World Model cognition + source；各臂输出预先密封 | Codex 保留实际客户端/model/reasoning/tools/权限，只作强外部基线，不是 Oracle/裁判；只有 source-only/full-cognition 两系统臂共享同一主 Agent/model/tool/budget/cache/Reviewer；不同能力完整披露；独立评估者在不知臂身份时用同一 rubric 判读；只作 ITER-010 方向信号，不冒充 ITER-012 严格优越性 Gate；不阻塞更早的用户交付 | not-executed | NOT-RUN / blocking |
| V-PREVIEW-002 | 用户基于 A1—A3/A6 复盘、多轮 Chat 和三臂方向信号决定是否进入夯实 | product / direction + architecture / reflection | `V-ALPHA-ACCESS-001/V-TIMEBOX-CHAT-001/V-CHAT-EXPERIENCE-001/V-CHAT-001/V-CHAT-QUALITY-001/V-CHAT-XD-001/V-COMP-ALPHA-001` 的真实 Result、限制、Findings 和假设证据 | 独立技术复核给出 A1—A3/A6 exact Verdict 与 A4/A5 early signal；用户实际追问、纠正、深入、总结并查看三臂方向信号后决定 CONTINUE/REWORK/REDIRECT/REJECT；只有 CONTINUE 解锁 hardening；单 Turn 失败默认 REWORK，不自动 REDIRECT | PDR-004 pre-execution revision；旧定义从未执行，无证据可追认 | NOT-RUN / blocking |

| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |
|---|---|---|---|---|---|---|
| V-000 | 本轮相对 rejected baseline 可测缩短通用工程问答差距并证明完整 World Model Cognition 的独立价值 | product / comparison | 三个唯一 Slice Result；最终隐藏 10+2；现场题；完整认知、locator-only/empty 同链、成熟源码 Agent 三臂；新收据预提交 protocol | 完整认知与成熟 Agent 先过零重大错误/boundary/逐结论质量门；完整认知再相对 locator control 达到预提交质量或非 locator 调查成本增益；计建模成本/复用周期；同一 Web/Citation/Source 隔离成立 | ITER-010-RESULT-SLICE-001-STOP-REDIRECT#V-000 | FAIL / blocking |
| V-PRE-001 | exact product baseline、planning input 与 ITER-009 rejected 产品结论被准确分离 | readiness / baseline | product commit `1fb997bab6444523f82ebf1a514a1abbf79656c7` / tree `1369ce932c778c57a118123e8257ede476229d73`；planning commit `01dcfe2233625dfaa021495850fb18ae1323063b` / tree `8e364ae854bfaa48580ab080a3e0d9c9c43c3d6f`；predecessor Result | 技术资产复用；不继承 Acceptance/live grant/qualification；授权只基于 exact planning input；dirty baseline 禁止 | Git object/tree/branch inspection；Proposal/Manifest/Readiness | PASS / readiness blocking |
| V-PRE-002 | ITER-009 用户反馈被判为系统性架构/产品方向证据而非单题文风 | readiness / evidence | `ITER-009-RESULT-SLICE-001-STOP-REDIRECT`、ROADMAP Candidate、现场答案与用户裁决 | baseline gap 是默认实现走读、Reviewer 层级 Gate 缺失和 Source-off 通用问答边界，不按个别问题修 Prompt | Proposal Trigger、Result、Candidate | PASS / readiness blocking |
| V-PRE-003 | ENGINEERING_QA、严格 WORLD_MODEL 和显式 DIRECT 三种模式及新自适应调查职责已冻结 | readiness / architecture | FINDING-010-002、ADR-013/014/015/016、owning Contract list、V-ARCH-001 | World Model 概念不变；ENGINEERING_QA 使用 Investigation→Broker/Worker→Ledger→seal→Answer/Review；无 silent fallback | Proposal、Readiness、Slice1 Phase0 | PASS / readiness blocking |
| V-PRE-004 | 新收据只授权 Slice1 产品开发，没有扩大 live、Source disclosure、credential、Provider、browser、hidden 或 Production 权限 | readiness / authorization | planning receipt `d3b60bda…`、development receipt `585f02c4…`、此前设计绑定的 `1b327024… + 5cdb7000…`、Manifest authorization | Slice1 authorized/coding true 且是唯一 active Slice；Slice2/3 proposed/coding false；所有 live/disclosure 另取 exact grant | Readiness、Manifest、Current、Slice1 | PASS / readiness blocking |
| V-PRE-005 | hidden、成熟 Agent 历史输入、三臂消融授权边界、burn 和方向体验顺序明确 | readiness / comparison | final 10+2、early 5+2；旧 `6ca47f7d…` Agent/rubric/cache/source-bytes protocol；新增 `engineering_qa_ablation` proposed mapping | 首段 preview 可先执行；新三臂 protocol/digest/阈值不得伪用旧收据，Slice2 前须新用户收据；披露后产品变化烧毁输入 | Proposal、Manifest bindings | PASS / readiness blocking |
| V-PRE-006 | A1—A5、逐 Slice Reflection、自适应调查、证据分区、独立补证调查和资源/质量边界可机械核对 | readiness / architecture | Proposal assumption catalog、Manifest 三 nested mappings、System fileset、answer_protocol | prior-result/Broker/Ledger/seal 精确；support/citation 与 boundary/audit 不混；Slice1 仅 preview 一次补证，后续无永久一轮上限；answerable 超限 FAIL | Proposal、Manifest、Readiness、docs gate | PASS / readiness blocking |
| V-PRE-CHAT-001 | PDR-004 current planning freeze 与 rejected product baseline 精确分离 | readiness / baseline | product baseline `1fb997bab6444523f82ebf1a514a1abbf79656c7` / tree `1369ce932c778c57a118123e8257ede476229d73`；planning commit `b66ff9f058b92cebd78d5644ffef042753567b4d` / tree `30e437eea83e048e3fb59ddd90a8d1b76242d82c` | 技术资产与历史失败保留；新编码只依据 exact PDR-004 planning freeze；不继承旧答案、资格、grant 或 Acceptance | Git object/tree inspection；Current、Proposal、Manifest、Readiness | PASS / readiness blocking |
| V-PRE-CHAT-002 | 双核心主 Agent/Conversation System Owner 已冻结且旧固定角色只作兼容 | readiness / architecture | ADR-018、Engineering Conversation、Agentic Task、Response Control、Source Artifact、Security、ADR-016 legacy markers | World Model/Conversation Work State/Turn Evidence 分离；主 Agent 负责目标—观察—重规划；平台拥有权限/执行/证据；fresh Reviewer 独立；旧固定角色不得成为 current delivery | System contract set、Manifest cutover、docs gate | PASS / readiness blocking |
| V-PRE-CHAT-003 | 最早体验顺序、五轮 Chat 和逐 Turn attempt 语义可执行 | readiness / experience | `V-ALPHA-ACCESS-001/V-TIMEBOX-CHAT-001/V-CHAT-EXPERIENCE-001/V-CHAT-001/V-CHAT-QUALITY-001/V-CHAT-XD-001`；五轮脚本与新对话负测 | Access 先于 Quality；Provider 前最多一个本地/Mock smoke；首个 live canary 是五轮 Conversation；每个 dispatched Turn 分别计 attempt；首次体验前 full regression=0 | Proposal、Slice1、Verification current rows、PDR-003/004 | PASS / readiness blocking |
| V-PRE-CHAT-004 | 本次用户收据只恢复 Slice1 开发而不扩大外部执行权限 | readiness / authorization | `codex-user-message:sha256:f76ba3e864f6612b3dcc14c83392ec54db686fdb5653e408fa300785b97ceef5`；Readiness；Manifest；Current | Slice1 是唯一 active/coding input；授权产品/System 代码与本地确定性验证；Provider/model、credential、动态源码披露、live browser、hidden、Slice2/3、Production 仍未授权 | Readiness/Manifest/Current/Slice1 exact authorization fields | PASS / readiness blocking |
| V-PRE-CHAT-005 | Codex 外部基线与 World Model 因果消融已严格分开 | readiness / comparison | current Codex external baseline；same-agent source-only；same-agent full-cognition + source；盲化独立评估协议 | Codex 保留实际客户端/model/reasoning/tools/权限且不是 Oracle/裁判；仅两个系统臂共享 Agent/model/tool/budget/cache/Reviewer；独立评估者技术判读，用户决定产品方向 | Proposal A5、Manifest comparison bindings、V-COMP-ALPHA-001 | PASS / readiness blocking |
| V-PRE-CHAT-006 | A1—A6、REWORK 历史、根因优先和体验后夯实边界机械一致 | readiness / architecture + delivery | current A1—A6 catalog；historical A1—A5/Case/Result；PDR-003/004；rework/experience policies | 历史证据不改写；新 Chat Gate 不复用历史 Case；失败先定位最早偏差；同签名一次修复上限；跨重启、第二工程、完整矩阵和 full regression 延至用户 CONTINUE 后 | Manifest cutover、Readiness、Verification、docs gate | PASS / readiness blocking |
| V-PRE-CHAT-007 | Access browser grant 精确收窄且已消费 | execution / authorization | `codex-user-message:sha256:7256a886d863712b27a7012c1c791eaca91c98f7183f732b463ce98543a469b6`；exact `cf2883bef861e0345afc36415d4216f943d31cf4`；`ITER-010-RESULT-V-ALPHA-ACCESS-001` | 只启动 `127.0.0.1:8765` 并执行 V-ALPHA 本机浏览器；Provider/model、源码/resources、Production 均禁止；完成后 listener 停止；不扩展后续 live 权限 | Result、health counters、shutdown/port check | PASS / consumed |
| V-BASELINE-001 | Slice1 实际开发 subject 仍是 exact baseline 且没有未记录产品变化 | development / baseline | Git ancestry/tree、worktree、predecessor Result | baseline 可复现；任何变化归属 Slice1；旧运行 identity 不继承 | not-executed | NOT-RUN / blocking |
| V-ARCH-001 | 新模式先取得正式架构与 Contract Owner，世界模型概念及旧模式边界不被静默改写 | architecture / contract | FINDING-010-001/002、SYS-ADR-016、Product Success、runtime/Agentic/Evidence/World Model/Response/Source/Security/Browser、Manifest fileset、docs gate/tests | ENGINEERING_QA 明确为 adaptive investigation；World Model 保持持久外部认知；strict WORLD_MODEL source-off 与 DIRECT identity 保留 | not-executed | NOT-RUN / blocking |
| V-QINTENT-001 | Question Understanding 忠实表达用户目标、受众、抽象层级、物质结论和证据需求 | application / contract | 用途/架构/运行/故障/影响/实现、多条件、改述、不同受众 fixture | 原问题约束不丢失/新增；无题型/工程/关键词/符号路由；输出 schema 可审计 | not-executed | NOT-RUN / blocking |
| V-COGNITION-001 | World Model 作为 exact、持久、版本化、可验证、可更新的软件外部认知进入问答 | architecture / knowledge | context/scope/schema/snapshot、实体/关系/行为/约束/状态/evidence/coverage/unknown fixtures | 手册/地图只作为投影；认知不退化为 cache/hints；coverage 不足不成为 Source recall Gate | not-executed | NOT-RUN / blocking |
| V-INVESTIGATE-001 | Investigation LLM 根据 prior Ledger Result 自适应提出下一步并合法结束 | application / investigation | 至少两步依赖链、partial/zero cognition、no-progress、premature finish、改述 fixture | 每步引用 prior result/progress；不是 upfront 固定计划；无题目/工程/关键词/符号/类/方法/fixture/oracle 分支 | not-executed | NOT-RUN / blocking |
| V-BROKER-001 | Source Broker/Worker 在模型无直接 Source 权限下编译并执行受控读操作 | security / integration | 合法抽象 proposal、request/attempt/profile-bound mandatory-path locator、跨 attempt/forged locator、path/symlink/write/exec/network/secret/disclosure probes、exact revision drift | Broker policy 决定唯一合法操作；direct locator 不赋予模型 path authority；Worker execution only；所有模型 direct FS/Shell/network/credential/source=0；完整操作/bytes/outcome audit | not-executed | NOT-RUN / blocking |
| V-LEDGER-001 | Evidence Ledger 只追加，调查结束后才密封双分区 Package，identity 与 seal 语义正确 | application / evidence | append/overwrite、finish/stop、admissible/rejected、gap/failure/partial/conflict/unknown、old/new revision、single-gap delta fixtures | 历史不可改；未 finish 不 seal；support/citation 仅 admissible；boundary/audit 强制保留且不得支持肯定 Claim；seal 非 truth；Verification Ledger 记录单 gap delta，trusted merge 只形成 successor 且保留非目标 disposition；predecessor boundary 不得进入 delta，非支持 child 必须绑定 current gap；旧 Review 不批新包 | `FINDING-010-070/072/073/076`；focused/full deterministic regression closed，clean exact candidate pending | NOT-RUN / blocking |
| V-ISOLATION-001 | Investigation、Answer、Reviewer 与实际 Source 权限物理/应用隔离 | security / isolation | source injection、path/write/exec/network/secret probes；role package/import/mount audit | 只有 Broker/Worker 受控读；Source untrusted；Investigation/Answer/Reviewer 直接 repo/source/tool access=0；非法动作失败关闭 | not-executed | NOT-RUN / blocking |
| V-ANSWER-001 | Preview 跨类型问题先给直接、层级匹配的答案，代码细节按需 | product / answer | 一个真实工程 4 条不同覆盖维度问题、exact Package、结论级 rubric | 至少 3 supported 且覆盖至少 2 个非实现维度；重大错误 0；每个物质结论 Citation；无内部诊断平铺 | ITER-010-RESULT-SLICE-001-STOP-REDIRECT#V-ANSWER-001 | FAIL / blocking |
| V-REVIEW-001 | Reviewer 阻断缺陷并以具体 gap 启动独立 Verification Investigation | application / review | 对抗 Draft、current Package/Ledger、configuration placeholder、status literal absent from cited content、unmounted application type、specific/invalid gap、两步结果驱动补证、predecessor consumed path/boundary、Broker rejection 与 terminal verified gap fixture | comprehensive approval 只放行 fresh challenge；Gateway 强制 focus 顺序；每个 lead 有 stable ID，challenge 必须逐项返回 evidence/Draft scope 与 disposition，Application 重算 exact 集合，越界项绑定被挑战 Claim Finding，只有全 within + empty Finding 才可授权；Reviewer 不提可执行操作；新调查用新上下文读一个 authorized gap+current Package/Ledger，经 Application/Broker/Worker 多步适应；Package full reads 不重复、predecessor boundary 不借用、最近拒绝显式；FINISH 单 gap delta 可信合并后新包重答双审；诚实 terminal unknown 不重复请求；非 material Draft 扩张不扩大调查；不回初始调查 | run-028 证明仅投影/focus 仍可跳过 lead；`FINDING-010-077/078` deterministic regression closed，fresh live pending | FAIL / blocking |
| V-LIMIT-001 | Preview 在调查或证据不足、安全熔断耗尽时保持诚实 | application / boundary | 可回答、证据不足、合法补证、无进展、上限耗尽、answerable/boundary fixture | 不伪造、不把未查到写成不存在；Slice1 最多一次补证；answerable 因熔断未回答计 FAIL；boundary 仅可独立审核 Limitation 或 fail closed | not-executed | NOT-RUN / blocking |
| V-SEC-001 | Slice1 exact revision、allowlist、untrusted Source、Provider disclosure、Secret、预算与 Web 安全成立 | security / integration | drift、oversize、injection、unauthorized fragment/provider、review tamper、outcome unknown、late primary、non-loopback probes | 每个 attempt 失败关闭；same-Provider retry/source write/update/silent mode fallback=0；只有 ADR-017 预授权、重跑完整链的一次 DeepSeek attempt 合法；跨 attempt 中间态/late overwrite=0；合法本地确定性路径完成 | not-executed | NOT-RUN / blocking |
| V-XD-001 | 同一 ENGINEERING_QA 答案组合 ITER-006 accepted World Model 认知与 query-time 新来源 Evidence | product / integration | declaration/`CALLS` Result + repository document/config/test/source conclusion；无符号自然问题 | 同一 Ledger/Package/Answer/Review；结论分别绑定正确来源；不是两个正文或模式拼接 | ITER-010-RESULT-SLICE-001-STOP-REDIRECT#V-XD-001 | FAIL / blocking |
| V-WEB-000 | Slice1 在完整夯实前交付最早可体验的真实 Web 微纵切 | product / browser | exact freeze/live grant、普通用户无认证、一条 World Model + query-time Source 代表问题 | 最小真实链可用；exact revision/read-only/untrusted Source/support-citation 分区/Citation/独立 Review 全部成立；非回放/CLI | `ITER-010-RESULT-V-WEB-000-LIVE-RUN-009`；candidate `f38f6cc…` / exact mall `0504e86…` / Result `engineering_result_2025ba4a523a363c6a8f463e670dfc31` / 9 dispatch / 6 opened Citation / Review APPROVED / retry 0 / switch 0 / Production Activation NOT_EXECUTED；前 8 run 永久失败保留 | PASS / blocking |
| V-WEB-001 | 微纵切后从同一 product-owned ENGINEERING_QA loopback Web 执行完整方向体验 | product / browser | V-WEB-000 后 exact freeze/live grant、4 条任务和至少一条现场题 | 页面交付答案/limitation与可打开 Citation；诊断折叠；console clean；持久恢复/复杂矩阵未完成不冒充 Acceptance | ITER-010-RESULT-SLICE-001-STOP-REDIRECT#V-WEB-001 | PASS / blocking |
| V-PREVIEW-001 | 在全面夯实前取得真实用户方向裁决 | product / directional-preview | V-WEB-001、4 个不同覆盖维度、现场题、非验收/非生产标识 | 用户能判断是否像工程问答助手并决定 CONTINUE/REDIRECT/REJECT | ITER-010-RESULT-SLICE-001-STOP-REDIRECT#V-PREVIEW-001 | FAIL / blocking |
| V-REFLECT-001 | Slice1 复盘架构迁移、真实 preview 和 A1—A3 | architecture / reflection | Slice1 exact Result、A1—A5、owned Cases、Findings、用户新 decision receipt | A1—A3 exact Verdict；A4/A5 early signal；完整决策 CONTINUE/REDIRECT/REJECT | ITER-010-RESULT-SLICE-001-STOP-REDIRECT#V-REFLECT-001 | PASS / blocking |
| V-GENERAL-002 | 同一协议跨第二工程、不同命名/结构/来源仍不依赖特判 | product / generalization | 第二真实工程、改述、不同目录/框架、source/doc/config/test mixes | 问题层级正确；无 project/question/keyword/symbol/class/method/fixture/oracle branch | not-executed | NOT-RUN / blocking |
| V-RERETRIEVE-002 | 主工程 Agent 根据 Reviewer Finding 在复杂 gap、冲突、重复和 no-progress 上可重规划并收敛 | application / contract | current Conversation Context/Work State/Package/Ledger、omission、unsupported inference、citation gap、specific/duplicate/conflicting gap、持久恢复和 no-progress cases | Reviewer 只返回具体 Finding；主 Agent 依观察决定同包重写或继续受控调查；新证据形成新 Ledger/Package/Answer/fresh Review identity；去重/恢复正确；不可修复时失败关闭；不启动固定 Verification Investigation 角色 | not-executed | NOT-RUN / blocking |
| V-ASYNC-002 | 知识沉淀不阻塞或改写当前问答 | application / knowledge | approved Package/Answer、async proposal success/reject/failure | Delivery 独立完成；异步路径重新走 Update/Admission/Publication；任何结果不追认/撤销原答案 | not-executed | NOT-RUN / blocking |
| V-HARDEN-002 | Conversation/Turn/Agent Work State、持久 Ledger/Package、coverage/conflict/dedup 和安全熔断闭合 | application / reliability | 追问/纠正恢复、recovery/truncation/pagination/conflict/oversize/cycle/no-progress/drift/stale context/package；revision/call/ops/bytes/wall-time/no-progress fuses | 无跨对话泄漏、漏页、越权、无界循环、历史回写、旧包/旧 Review 放行或伪完整；不固定补证轮数；answerable 超限 FAIL，boundary 只交付准确 limitation 或 fail closed | not-executed | NOT-RUN / blocking |
| V-SEC-002 | 第二段保持 Source/role/Provider/Secret/loopback 与 no-retry 隔离 | security / integration | 合法/非法 end-to-end probes、Gateway disclosure/transport audit | 合法路径完成；非法全部失败关闭；模型 direct source/FS/Shell/network=0，write/update/unauthorized fallback/same-Provider retry/secret exposure=0；授权 fallback attempt 独立全链 | not-executed | NOT-RUN / blocking |
| V-XD-002 | 第二工程同一答案组合 accepted Snapshot 与本轮多来源 Evidence | product / integration | accepted declaration/`CALLS` + new doc/config/test/source evidence、无符号题 | 同一 answer/limitation 和 Citation 完成真实组合 | not-executed | NOT-RUN / blocking |
| V-WEB-002 | Slice2 从同一真实 Web 执行 V-XD-002 | product / browser | product-owned loopback Web、第二工程、exact qualification/run grant | answerable/boundary 用户可见；Citation 可核对；无平行入口 | not-executed | NOT-RUN / blocking |
| V-CANARY-002 | Slice2 通过独立第二工程 5 answerable + 2 boundary canary | product / independent-hidden | Slice2 code freeze 后用户披露 exact project/suite；burn rule | 5/5 supported、2/2 boundary、重大错误 0、无特判；披露后产品变化=0 | not-executed | NOT-RUN / blocking |
| V-NEG-EARLY-002 | bounded absence 与 coverage limitation 在第二工程保持区分 | product / early falsification | canary 两类 boundary、不同命名/入口/同义改述 | 三层完整才 absence；否则具体 limitation；无关证据 FAIL | not-executed | NOT-RUN / blocking |
| V-COMP-EARLY-002 | 正式验收前分开复验产品外部强基线与 World Model 因果消融 | product / comparison | 新用户收据冻结 protocol；current Codex 保留实际 model/reasoning/tools/permissions/budget；same-agent source-only 和 same-agent full-cognition + source 共享系统 runtime；同 exact revision/Conversation 脚本/输出约束/盲评 rubric；各臂先密封 | 独立评测分别报告系统对 Codex 的产品质量差异，以及 full-cognition 相对 source-only 的预提交质量或 normalized non-locator cost 增益；Codex 不是 Oracle/裁判，不强制三臂 runtime identity；计建模成本/复用周期 | not-executed | NOT-RUN / blocking |
| V-DIAG-002 | 对同一 Turn 逐层定位首次偏差 | architecture / diagnostic | Source truth、World Model Cognition、Conversation Context/Turn goal、Agent Work State/plan/tool observation/replan、Broker/Worker、Ledger/Package、Answer、independent Review、Web exact refs | 每层独立 verdict；首次偏差决定分类；不从最终答案猜根因 | not-executed | NOT-RUN / blocking |
| V-REGRESSION-002 | accepted scope、strict WORLD_MODEL、DIRECT 与 Preview 主线无退步 | regression / product | ITER-003—006 accepted oracles、Slice1 Result、current full suite | accepted behavior与三模式隔离保持；无新增 fallback/入口分叉 | not-executed | NOT-RUN / blocking |
| V-REFLECT-002 | Slice2 复盘跨工程、多轮 Chat、主 Agent、合同、安全与 value | architecture / reflection | Slice1/2 Results、A1—A6、Findings、用户新 decision receipt | A1—A4/A6 exact Verdict；A5 early verdict；CONTINUE/REWORK/REDIRECT/REJECT | not-executed | NOT-RUN / blocking |
| V-HIDDEN-003 | 最终两个未见工程 10 answerable + 2 boundary 验证泛化 | product / independent-hidden | final code freeze 后用户披露 exact projects/suite；至少 8 no-symbol、每工程至少 3 | answerable 10/10、boundary 2/2、重大错误 0、披露后产品变化=0 | not-executed | NOT-RUN / blocking |
| V-COMP-001 | 最终分开证明工程 Chat 产品质量与完整 Cognition 增益 | product / comparison | current Codex 保留实际 model/reasoning/tools/permissions/budget；same-agent source-only 与 full-cognition + source 系统臂共享 runtime；final same exact revision/Conversation 脚本/输出约束/盲评 rubric；frozen comparison + ablation protocol | 系统与 Codex 各自先过质量门并由独立评测报告产品差异；full-cognition 再相对 source-only 达预提交质量或 normalized non-locator cost 增益；Codex 非 Oracle/裁判；建模成本按冻结复用周期摊销；exact report 可重放 | not-executed | NOT-RUN / blocking |
| V-SEC-003 | 最终产品链保持全部授权、安全、role 和 disclosure 边界 | security / product | final hidden/live sessions、source/Gateway/transport/Ledger/package/Citation audit | Source only via Broker/Worker；所有模型 direct source/FS/Shell/network=0；write/update/unauthorized fallback/secret/same-Provider hidden retry=0；ADR-017 fallback 完整隔离；loopback | not-executed | NOT-RUN / blocking |
| V-XD-003 | 最终问题在同一答案链组合 accepted Snapshot 与多来源 Evidence | product / integration | final hidden no-symbol cross-source question、accepted Result、新 protocol | 同一正式答案和 Citation 支持旧+新能力 | not-executed | NOT-RUN / blocking |
| V-WEB-003 | Slice3 从同一正式 ENGINEERING_QA Web 执行 final suite | product / browser | exact frozen Web、final 10+2、run grant | 页面交付答案/limitation/Citation；console clean；与内部链相同 | not-executed | NOT-RUN / blocking |
| V-ADHOC-001 | 用户从正式 Web 提出两条现场问题 | product / browser | product freeze 后现场题；至少一条 no-symbol 且跨域 | answerable supported；真实 boundary 正确；Citation 可核对；无 silent mode fallback；Provider fallback 仅按 ADR-017 对用户透明且完整审计 | not-executed | NOT-RUN / blocking |
| V-REGRESSION-003 | 最终候选保持 accepted scope与 Slice1/2 结果 | regression / product | prior oracles、两个 Slice Results、full suite | 无新增失败、能力降级、source leak 或三模式分叉 | not-executed | NOT-RUN / blocking |
| V-010 | 本机验证和 Acceptance 不产生 Production Activation | activation | exact final Iteration Result | NOT_EXECUTED | not-executed | NOT-RUN / blocking |
| V-REFLECT-003 | 最终复盘 A1—A6 并由用户裁决 | architecture / reflection | 三个 exact Slice Results、10+2、现场多轮对话、Agent/value、安全、Findings | A1—A6 exact Verdict；只有全部 SUPPORTED 与用户新 ACCEPT 才能申请 Acceptance | not-executed | NOT-RUN / blocking |

### Current Slice1 rework evidence

- run-033（clean `d70a3e6…`）保持 `V-ANSWER-001 / V-REVIEW-001 / V-LEDGER-001` blocking：Q1 的 single-gap Verification
  replacement 删除了 supported predecessor target observations，Q2 被 admissible-reference Gate 正确关闭，Q3 为零重试
  post-dispatch outcome unknown；66,000-byte Provider-before-call negative PASS。总体不是 live PASS。
- `FINDING-010-088/089` 要求并以 focused/Engineering QA/docs/oracle/full exact historical hold 验证 supported target observation 的
  exact/relative-order monotonic merge、caller-visible effect gap 与未挂载 callee boundary；deterministic Gate 已闭合，新 clean/fresh live
  仍必须另行执行，不能以 run-033 或旧 run 补齐。
- run-034（clean `fe6b6b6…`）在用户表示充值后启动，第一条 fresh Conformance request 仍收到 DeepSeek HTTP 402；
  request 1、token 0、retry/switch 0，第二条 canary 未发送，无 Qualification/Alpha/Browser。`FINDING-010-090` 因此
  保持 configuration-environment hold；当前 key 所属账户恢复 Provider 可用性后必须启动新的 fresh run。

## Freeze and scoring rules

- Slice1 先交付真实可操作的 Chat Access；Provider 前最多执行一个本地/Mock Access smoke。首次 live canary 本身就是一段冻结五轮
  Conversation 和新对话隔离负测，每个已 Provider-dispatched Turn 分别计 live attempt。exact revision、只读、不可信 Source、Citation、
  fresh independent Review 和失败真实性不可延后；五轮通过后立即执行 `V-COMP-ALPHA-001`，再由用户决定是否 `CONTINUE`。
- Slice2 early canary 与最终 10+2 互不复用，在所属 Slice code freeze 后由用户披露；披露后任何产品/Prompt/schema/route/disclosure 改动
  烧毁输入并保留失败 Result。最终 10 条 answerable 是 supported 分母，Gap 不计 PASS；2 条 boundary 单独要求 2/2。
- 比较必须拆成两个问题：current Codex 保留其实际客户端、model、reasoning、tools、permissions 和 budget，只固定 exact revision、
  Conversation 脚本、可比输出约束和盲评 rubric；因果消融仅比较 same-agent source-only 与 same-agent full-cognition + source，这两个系统臂
  才共享 Agent/model/tools/permissions/budget/cache/Reviewer。Codex 不是 Oracle 或裁判；独立评测先评绝对质量，再分别报告产品差异和 World Model 增益。
- Reviewer Finding 只返回主工程 Agent；主 Agent 选择同包重写或继续受控取证。current 协议不固定 Verification Investigation 角色、补证轮数或双 Review，
  而用预密封 package revision、model call、Broker operations、source bytes、wall-time 和 no-progress 高安全熔断防止失控；answerable 因熔断未答计 FAIL。
- 调用次数和成本不构成质量裁剪目标；高安全上限触发失败关闭，不能删除用户目标、Evidence、Citation 或独立 Review。
- `V-PREVIEW-002/V-REFLECT-002/V-REFLECT-003` PASS 只表示复盘完整。Slice1/2 需要新的 `CONTINUE` 才能授权下一段；最终需要新的 `ACCEPT` 才能接受迭代。
- Product Result 必须聚合三个唯一 Slice Result；测试数量、模型调用成功、旧 Web result 或旧资格不能替代。
