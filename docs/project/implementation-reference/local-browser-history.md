---
id: SYS-OPS-LOCAL-BROWSER-HISTORY
kind: system-operations
status: historical-evidence
authority: operational
owners: [operations, interface]
depends_on: [SYS-ARCH-DEPLOYMENT, SYS-ADR-014, SYS-ADR-015, SYS-ADR-016, SYS-ADR-017, SYS-ADR-018, SYS-ADR-019, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, SYS-QUALITY-SECURITY]
derived_from: [FINDING-010-029, FINDING-010-140, FINDING-010-154, FINDING-010-156, FINDING-010-157, FINDING-010-158]
code: [pyproject.toml, src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/application_services/conversational_engineering_routing.py, src/software_world_model/application_services/public_source_model_authority.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py, src/software_world_model/interface/http_api.py, src/software_world_model/interface/browser_ui.py, src/software_world_model/interface/world_model_browser.py, src/software_world_model/interface/world_model_browser_ui.py, src/software_world_model/interface/world_model_http.py, src/software_world_model/interface/world_model_runtime.py, src/software_world_model/interface/world_model_product.py, src/software_world_model/interface/engineering_chat_candidate.py, src/software_world_model/interface/engineering_chat_provider_launcher.py, src/software_world_model/interface/engineering_chat_provider_runtime.py, src/software_world_model/interface/engineering_chat_session_runtime.py, src/software_world_model/interface/engineering_chat_session_artifact.py, src/software_world_model/interface/engineering_chat_browser.py, src/software_world_model/interface/engineering_chat_browser_ui.py, src/software_world_model/interface/engineering_chat_alpha_cli.py, src/software_world_model/interface/engineering_qa_browser.py, src/software_world_model/interface/engineering_qa_browser_ui.py, src/software_world_model/interface/engineering_qa_live.py, src/software_world_model/interface/engineering_qa_preview_cli.py, src/software_world_model/interface/engineering_qa_alpha_cli.py]
tests: [tests/test_browser_chat_interface.py, tests/test_world_model_browser.py, tests/test_iteration_004_interactive_browser.py, tests/test_world_model_http.py, tests/test_world_model_evaluation_grant.py, tests/test_world_model_gateway_authorization.py, tests/test_iteration_007_slice1_freeze.py, tests/test_iteration_008_slice1_freeze.py, tests/test_iteration_008_slice1_live_authorize.py, tests/test_world_model_product.py, tests/test_engineering_question_model_source.py, tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_tools.py, tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_routing.py, tests/test_public_source_model_authority.py, tests/test_engineering_chat_candidate.py, tests/test_engineering_chat_provider_launcher.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_chat_browser.py, tests/test_engineering_chat_alpha_cli.py, tests/test_engineering_qa_live.py, tests/test_engineering_qa_preview_cli.py, tests/test_engineering_qa_alpha_cli.py, tests/test_engineering_qa_browser.py]
---

# 本机浏览器体验

> 当前唯一产品体验入口是 `swm-engineering-chat`。`swm-http-evaluation`、`swm-browser-evaluation`、`swm-engineering-qa-evaluation`、`swm-engineering-qa-preview-evaluation` 和独立 World Model
> 页面均为兼容或评估入口，不得用来代表当前产品 Chat，也不得并行占用同一端口进行方向判断。

当前已有启动命令和运行证据的本机浏览器仍只有两个不可混淆的历史入口：Evidence-first `DIRECT_INVESTIGATION` 用于源码调查；独立的
`WORLD_MODEL / EVALUATION_ONLY` 入口用于体验 Snapshot-first Maven Structure 或已授权候选 Java Static Call Behavior
World Model。两者不能静默互相兜底。

## 当前对话式目标

普通用户的默认目标是 `ENGINEERING_CHAT_EXPERIENCE@1`：同一浏览器 Conversation 接受多个 Turn，并由
`CONVERSATIONAL_ENGINEERING_AGENT@1` 主工程 Agent 理解追问、指代、纠正、深入和总结。页面把 World Model 提供的版本化系统认知、
可丢弃的 Agent Work State、current Turn Evidence Package 和用户可见消息明确分开；主 Agent 经 Broker/Worker 使用只读工具调查 exact
revision，答案继续绑定 Citation，并在显示为已审核结果前经过 fresh independent Reviewer。单 Turn 失败关闭只结束该 Turn，不自动结束仍
有效的 Conversation，也不允许旧答案授权、旧 Review、未密封工具结果或 Provider memory 跨 Turn 取得权威。

ADR-016 的固定 Understanding/Initial Investigation/Answer/双 Review/Verification Investigation 拓扑和
`ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3` 页面属于已实现兼容路径与历史运行证据，不再定义默认 Agent 本体。独立 Chat Access 当前为
`ACCESS_BROWSER_PASS`，已实现 Conversation/Turn/Context、消息历史和“新对话”；Application-owned Agent executor 与浏览器 success/failure
投影为 `AGENT_EXECUTOR_LOCAL_CANDIDATE`。World Model/Source/Ledger tool adapter 与单 Provider Agent/Reviewer model boundary 已分别达到
`EVIDENCE_TOOLS_LOCAL_CANDIDATE / MODEL_BOUNDARY_LOCAL_CANDIDATE / PROVIDER_ROUTE_COMPOSITION_LOCAL_CANDIDATE`。Application-owned
generic `preferred → fallback` router（当前配置实例映射 Ark→DeepSeek）和 fixed Browser composition 已在不创建 attempt 的预检中绑定；listener、credential、Source read、Provider dispatch
仍全部为 0。Ark/DeepSeek model runtime 已以生产 Adapter/credential-lazy transport 形成
`PROVIDER_RUNTIME_COMPOSITION_LOCAL_CANDIDATE`；Session runtime 又绑定 exact evidence authority、per-attempt fresh Tool/Response Control、route、
Conversation 与 Browser。`FINDING-010-103` 进一步实现 owner-private artifact loader 和固定命令分支，加载 product/source identity、published
World Model、Source Profile、Ark/DeepSeek qualification identity 与 distinct private Gateway repositories，状态为
`ARTIFACT_SESSION_FIXED_COMMAND_LOCAL_CANDIDATE`。`FINDING-010-104` 又把 Ark per-request verified TLS Session audit 接入 Conformance 与
terminal receipt，并 owner-type HTTP 前 unavailable raw evidence；状态增加 `ARK_TRANSPORT_SESSION_AUDIT_LOCAL_CANDIDATE`。该 raw evidence 未经受信 availability owner 形成 exact verdict，不具备 fallback eligibility。这些状态来自本地构造/
patched typed artifacts 和 fake listener lifecycle；fresh Ark 与 DeepSeek Conformance 随后已分别以 2/2 request、strict Session audit
PASS，双 Provider qualification 当前同时可用。Artifact Session `@4` 已把公开来源 standing authority 到 exact Session/Turn/call 的自动派生
形成 `PUBLIC_SOURCE_STANDING_AUTHORITY_DERIVATION_LOCAL_CANDIDATE`；current actual sealed artifact 和 Browser Chat 仍未生成或执行，故仍为
`NOT_LIVE`。在双 route Adapter 资格、
真实模型审计和人工体验均闭合前，页面不得把
`ENGINEERING_CHAT_EXPERIENCE@1` 标成 PASS 或生产可用。

ADR-016 曾接受第三个、面向普通用户的 `ENGINEERING_QA` 兼容入口。`ITER-010 / SLICE-001` 已实现 loopback WSGI 页面、本地
no-disclosure Request factory、exact authorized prepared-Request factory、内存 Result/Citation 投影、逐角色 disclosure/Gateway policy、
current DeepSeek 组合和历史 prepared launcher；factory 还必须固定与 repository Binding 一致的 versioned Source Profile
ref/digest，不能从问题或文件名推断 evidence class。launcher 在 listener 前证明自身来自 clean exact candidate，装载 published Bundle、
exact Source revision/Profile、prepared Request/run grant，并先写 0600 launch receipt；graceful exit 再写 role/Gateway/TLS terminal audit。
确定性 fake transport 已证明组合不读取 credential、不建立网络。页面要求 exact `127.0.0.1` remote/Host 并持续显示“方向体验 / 非验收 /
非生产”；live health/developer details 必须显示 exact Provider/configuration/qualification/run digest 和预备 Request，local health 则明确
`external_provider_dispatch=false`。

截至 `2026-08-22`，ITER-010 已在 exact loopback listener 与 in-app browser 上执行 14 个永久保留的方向体验 run，共 87 次
Engineering QA role dispatch；另有 2 次 current DeepSeek qualification call。全部 run 都绑定 exact candidate/Request/Source Profile/Maven
Bundle/grant，retry/provider switch 为 0，Production Activation `NOT_EXECUTED`，并排除 `src/main/resources`。前 8 个 run 依次暴露并关闭
role-progress、Schema/cardinality、Source Profile、literal/locator、no-progress、fresh Ledger/eligible locator、call-reserve、FINISH 字段组合和
disposition reference eligibility 缺口，永久保持失败关闭。

第 9 个 clean candidate run `web-v-web-000-012` 在 24-call 每题安全熔断内实际消费 9 次 role dispatch，完成 Understanding、adaptive
Investigation、密封 Package、Answer 与独立 Review，Browser 返回 `APPROVED / REVIEWED RESULT`。6 个 Source/World Model Citation 均由
in-app Browser 实际打开并绑定同一 Package/Result，console 为空；terminal audit 为一次 verified TLS handshake、8 次 reuse、retry/switch
0、Production Activation `NOT_EXECUTED`，全部 model manifest 对 `src/main/resources` 匹配数为 0。因此 `V-WEB-000` 最早微检查点为
PASS；它仍是 `DIRECTION_PREVIEW / NOT_ACCEPTANCE / NOT_PRODUCTION`，不能替代 `V-XD-001`、完整方向体验、Reflection 或 Slice Acceptance。

随后 4 个 `V-WEB-001` 公开方向题 run 绑定预提交 suite。第一题在 5 次 dispatch 后因重复相同 SOURCE query 触发 no-progress，永久
失败关闭；`FINDING-010-026` 将此前未投影的 attempt-scoped query/locator intent 加入 Ledger/角色输入，并由 Broker 在 Worker 前拒绝
重复工作。剩余三题在新 clean candidate `17cff66…` 上分别以 8/8/9 次 dispatch、0 no-progress 完成，Review 全部 `APPROVED`；公开题计数
为 3 supported / 1 fail，覆盖启动/配置、故障定位、变更影响/测试边界等非单一实现维度。11 个 Citation 全部实际打开，来源为 exact
Build/Source 或 World Model Cognition，同题内绑定 exact Package/Result，suite 结束后 Browser developer log 为 `[]`。四题合计 30 次
dispatch，retry/switch/outcome-unknown 0，全部 model manifest 对 `src/main/resources` 匹配数为 0，Production Activation
`NOT_EXECUTED`。

用户随后从同一 Web 现场提出“登录流程是怎样的？”。exact candidate `8632904…` 的新 run 完成 10 次 dispatch、6 个 Broker-authorized
只读 operation、0 no-progress，Answer/Review 到达且 Review `APPROVED`；3 个 exact Source Citation 全部打开，console `[]`。terminal
audit 为 TLS handshake 1、reuse 9、HTTP/credential 10/10、retry/switch/outcome-unknown 0，30 个 manifest item 对
`src/main/resources` 匹配数为 0，Production Activation `NOT_EXECUTED`。因此公开 4 题与现场题合并后 `V-WEB-001` PASS。现场正文仍
主要按 Controller/Service/Filter 方法调用顺序展开，并省略 exact Source 中的 `insertLoginLog` 副作用；`FINDING-010-027` 将其保留为
质量失败输入。旧记录曾把用户要求实现者自行复核并修复的消息推断为 `REDIRECT`；PDR-001 已纠正为同一 `ITER-010/Slice1` 的
`REWORK`，历史 `V-PREVIEW-001` 与答案/审核 FAIL 不改写。`FINDING-010-028` 定位答案层级根因，`FINDING-010-029` 定位单题 prepared
launcher 与持续体验冲突；后续收据曾恢复 Slice1 开发，但 PDR-004 已再次暂停旧编码权威，旧 question/run grant 仍不可复用。

ADR-016 / `@3` 兼容 Alpha 目标在 listener 前固定一个升级后的 Engineering QA Session Authority，而不是固定一条问题。公开开源工程路径
从 `PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY@1` 自动派生该 Session Authority；它绑定 clean product、exact 工程/
revision、World Model、Source Profile/allowlist、通用 `preferred → fallback` route role 与 execution-profile refs，以及每条 profile 配置内的 model/configuration/qualification/credential reference/
披露边界、有效期和 logical-question/provider-attempt 两级安全熔断。
页面显示这些边界；体验者只输入问题并提交，服务签发 request/run identity 并由 System Owner 从 standing authority 编译该题 exact
machine authority/receipt，不要求人工逐题批准。每题后续动态 Ledger/Package 输入仍逐角色、逐 Provider attempt 自动形成 one-use
authorization。preferred attempt 无 authorized answer 且其登记的受信 availability owner 密封 exact
`PREFERRED_EXECUTION_PROFILE_UNAVAILABLE` verdict 时，系统可对同一 logical question 自动启动一次完全隔离的 fallback attempt；用户不重提问题或重启 Session。
Raw unavailable/HTTP/outcome 信号不直接启用 fallback；格式无效、Reviewer 拒绝、Capability/qualification、Application、Source、authorization/admission 或 Security failure 均 non-eligible。
格式修复、答案重写、补证后重答和 fresh Review 使用同一 profile 下的新 authorized call，不是重发同一 request。
题目最终失败只关闭该 logical question，服务继续接受下一题；session authority 漂移、过期或总熔断耗尽则拒绝后续新题。问题 POST 仅接受当前 `http://127.0.0.1:8765` 页面发出的 same-origin `application/json`；跨站或
`text/plain` 请求在 receipt 与 transport 前拒绝。当前实现与确定性证据闭合前，不得把该目标写成 live PASS。

PDR-003 将 Access 与答案 Quality 分离：页面可启动、可提交 Turn、能如实显示 provider-attempt 进度/失败且标记“质量未验收”即可进入
`V-ALPHA-ACCESS-001`；它不能取得 `V-CHAT-001` 或 `V-ANSWER-REWORK-001`。当前 ITER-010 已超过 240 分钟 hard stop，首次新体验前只允许启动安全、失败
真实性、一次 current Provider qualification 和一个 Provider 前本地/Mock Access smoke，不执行 full regression。首次方向 live canary
必须是 PDR-004 的一个五轮 Conversation；任一 Turn 失败即停止后续方向套件并回到本地根因诊断。

`swm-engineering-chat` 无参数模式保留独立 Chat Access，不接受 host、port、project、revision、Provider、question 或授权参数：

```bash
PYTHONPATH=src:. python3 -m software_world_model.interface.engineering_chat_alpha_cli
```

launcher 只在 product worktree 与固定
`validation-projects/mall@0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` 都 clean 时绑定 `http://127.0.0.1:8765/`；页面显示 exact product/source revision、
完整消息历史、“新对话”、Provider/World Model/Source 未配置状态和“质量未验收 / 非生产”。提交消息会创建真实 server-owned Turn；当前没有
Provider executor，故 Turn 以 `PROVIDER_NOT_CONFIGURED`、dispatch/retry 0、Delivery `NOT_AUTHORIZED` 密封，Conversation 继续可用。状态只在
进程内保存，停止服务后不恢复。该模式已在 exact `cf2883bef861e0345afc36415d4216f943d31cf4` 完成一次真实 listener/browser handoff，
`V-ALPHA-ACCESS-001` 为 `PASS / access-only`；该次运行 dispatch 0，且没有读取 credential、Provider/Source payload 或
`src/main/resources`，也没有执行 Production Activation。

同一命令的 artifact-backed 模式只新增一个 operator selector；sealed artifact 是全部运行 scope 的唯一输入：

```bash
PYTHONPATH=src:. python3 -m software_world_model.interface.engineering_chat_alpha_cli \
  --session-config /absolute/private/engineering-chat-session.json
```

所有 Artifact Session 配置必须是 canonical absolute path 上 mode `0600` 的 unique-key UTF-8 JSON，根对象字段 exact match。当前
`SWM-ENGINEERING-CHAT-ARTIFACT-SESSION-CONFIG@4` 固定 5 Turns、每 Turn 每 Provider 15 dispatch、每 Provider 总计 75；Provider routes 必须恰好为 ordinal 1 Ark、
ordinal 2 DeepSeek。数据库与 receipt 路径必须是互异、尚不存在的 absolute paths；product/source repositories 必须互异；
`src/main/resources` 必须在排除项且不能与 Source Profile overlap。下面的 `@1` 仅展示共享字段和历史单 Profile 兼容形状，不是 current
standing-authority 输入：

```json
{
  "schema": "SWM-ENGINEERING-CHAT-ARTIFACT-SESSION-CONFIG@1",
  "product_repository": "/absolute/clean/software-world-model",
  "product_commit": "<exact-40-hex-product-commit>",
  "product_tree": "<exact-40-hex-product-tree>",
  "project_name": "mall",
  "repository": "/absolute/exact/source-repository",
  "repository_id": "<stable-repository-id>",
  "binding_id": "<world-model-binding-id>",
  "repository_revision": "<exact-40-hex-source-commit>",
  "source_profile_ref": "<versioned-source-profile-ref>",
  "source_paths": ["src/main/java"],
  "document_paths": ["README.md"],
  "build_paths": ["pom.xml"],
  "test_paths": ["src/test/java"],
  "excluded_source_paths": ["src/main/resources"],
  "ordered_envelope": "/absolute/published/ordered.json",
  "snapshot_bundles": ["/absolute/published/snapshot.json"],
  "cognition_snapshot_id": null,
  "response_language": "zh-CN",
  "session_ref": "<unique-session-ref>",
  "authorization_message_digest": "sha256:<standing-or-delta-authority-digest>",
  "authorized_at": "<canonical-UTC-time>",
  "expires_at": "<canonical-UTC-time-not-after-both-conformance-expiries>",
  "provider_routes": [
    {
      "ordinal": 1,
      "provider_type": "VOLCENGINE_ARK",
      "conformance_result": "/absolute/current/ark-conformance.json",
      "gateway_database": "/absolute/new/ark-gateway.sqlite3"
    },
    {
      "ordinal": 2,
      "provider_type": "DEEPSEEK",
      "conformance_result": "/absolute/current/deepseek-conformance.json",
      "gateway_database": "/absolute/new/deepseek-gateway.sqlite3"
    }
  ],
  "launch_receipt": "/absolute/new/chat-launch.json",
  "terminal_receipt": "/absolute/new/chat-terminal.json",
  "required_conversation_turns": 5,
  "maximum_dispatches_per_turn": 15,
  "maximum_total_dispatches_per_provider": 75,
  "known_limitations": ["Alpha evaluation only", "src/main/resources is excluded"]
}
```

current `@4` 保留上述 shared product/source/session/route/receipt/budget 字段，但删除 `authorization_message_digest`，并要求三个 closed
对象：`cognition_profiles` 逐 Profile 密封 Bundle 与 file digest；`deepseek_dispatch_admission` 密封 plugin、official pricing trusted inputs、
token/duration budget 与可选 exact peak override；`standing_authority` 密封
`PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY@1` 的 human evidence ref/digest、authority evidence refs、purpose、Source Authority、canonical
upstream/license/license path/revision policy/exact tree、route policy、两个 qualification-independent Provider/account/disclosure/admission
scope、总预算、时窗与 exact loopback evaluation Sink。loader 用 top-level exact revision、Source Profile/allowlist 和上述 standing fields
重算 parent digest；任何缺失、未知字段或边界扩大都在 listener/credential/network 前失败关闭。

launcher exclusive-create 两个 private SQLite repositories，在 listener 构造前写 launch receipt，固定绑定 `127.0.0.1:8765`，停止后写
terminal receipt。launch receipt 必须仍是 attempt/tool/cognition/Source/credential/dispatch/listener 0；terminal receipt 密封两条 route 的
Disclosure/model-boundary audits 与各自经过 strict verifier 的 Ark/DeepSeek transport Session audit。current Ark 与 DeepSeek identity 的 fresh
Conformance 均已 PASS；但尚未用 current actual artifact 启动真实 Provider/browser，所以状态只是
`DUAL_PROVIDER_QUALIFICATION_CURRENT / PUBLIC_SOURCE_STANDING_AUTHORITY_DERIVATION_LOCAL_CANDIDATE / NOT_LIVE`，不是 live PASS。

fallback dispatch admission 是逐请求外调门禁，不是整个 listener 的可用性门禁。launcher 在启动前必须构造 admission controller 并从 exact
plan 密封 non-dispatching preparation decision；controller 缺失、artifact 漂移或 decision 无法构造仍关闭 listener。preparation verdict
为 `DENIED_*` 时，状态如实展示当时 fallback 不可调用，但不得阻止资格、authority 和 artifact 均有效的 preferred-only Browser Session 启动；
它为 allowed 也不授予 fallback，且不能从 listener 启动时提前消耗 active duration。只有 registered availability owner 对 exact preferred
attempt 密封不可用 verdict、Application 因而创建 fallback attempt 后，第一次 DeepSeek request preflight 才从同一 plan 重新核验 run authority、
官方检查 freshness、窗口/override、预算和 exact envelope 并激活 active receipt；后续 request 回指同一 receipt。任何拒绝必须发生在 credential
resolution、TLS 和 HTTP 前且三类计数均为 0。

current Artifact launcher 的 registered owner policy 固定为
`GATEWAY_SEALED_PRE_DISPATCH_UNAVAILABLE_ONLY@1`。通用 Router 在没有显式 composition 时继续使用 fail-closed boundary；launcher 只能把
exact preferred attempt 上由 Model Gateway 密封的 closed `PROVIDER_UNAVAILABLE` classification、canonical
`PROVIDER_UNAVAILABLE` failure code、非零 model dispatch count 和至少一个 model call receipt 组合成
`PREFERRED_EXECUTION_PROFILE_UNAVAILABLE` verdict。verdict 必须绑定 exact logical request、preferred profile、attempt receipt 与 runtime
injected aware clock。raw transport reason（包括 `TLS_FAILURE`）、HTTP error、outcome unknown、输出合同无效、Reviewer reject 或没有 model
call receipt 的合成失败都不得形成 verdict。该 Owner 只授权 Router 创建一次隔离 fallback attempt，不授权外调；fallback attempt 仍逐请求通过
上述 admission controller。由此 preferred-only listener 不等待 fallback 窗口，而真正选择 fallback 时仍不能绕过其硬门禁。

字段名 `authorization_message_digest` 只属于 `@1—@3` 兼容实现。公开来源 current `@4` 使用明确 standing parent 与 exact Session child
ref/digest，不要求每次 run 新增用户消息；每个 Turn attempt 和 call receipt 继续自动派生、one-use 并记录人工重复审批数 0。兼容 schema
不能被标成该能力。

已实现兼容 Alpha 的 `swm-engineering-qa-evaluation` 评估命令固定使用端口 `8765`；operator 在 product freeze 后生成一次 exact session configuration，普通体验者不
接触其中的授权或内部参数：

```bash
PYTHONPATH=src:. python3 -m software_world_model.interface.engineering_qa_alpha_cli \
  --session-config /absolute/frozen/engineering-qa-session.json
```

下面的 `SWM-ENGINEERING-QA-ALPHA-SESSION-CONFIG@1` 是当前单 DeepSeek launcher 的已实现兼容格式，不符合 ADR-017 的透明双 route
目标，不能用于宣称 Chat 恢复版本 PASS。新 Chat 必须使用上面的独立 artifact schema，不能把兼容 `@1` 追认为双 route Session。
兼容 `@1` configuration 是 canonical absolute path 上 mode `0600` 的 unique-key UTF-8 JSON，并且根对象恰好包含下列字段；四类路径、
排除项、Snapshot 和已知限制都必须是非空无重复数组：

```json
{
  "schema": "SWM-ENGINEERING-QA-ALPHA-SESSION-CONFIG@1",
  "product_repository": "/absolute/clean/software-world-model",
  "product_commit": "<exact-40-hex-product-commit>",
  "product_tree": "<exact-40-hex-product-tree>",
  "repository": "/absolute/exact/source-repository",
  "repository_id": "<stable-repository-id>",
  "binding_id": "<world-model-binding-id>",
  "repository_revision": "<exact-40-hex-source-commit>",
  "source_profile_ref": "<versioned-source-profile-ref>",
  "source_paths": ["src/main/java"],
  "document_paths": ["README.md"],
  "build_paths": ["pom.xml"],
  "test_paths": ["src/test/java"],
  "excluded_source_paths": ["src/main/resources"],
  "ordered_envelope": "/absolute/published/ordered.json",
  "snapshot_bundles": ["/absolute/published/snapshot.json"],
  "cognition_snapshot_id": "<exact-snapshot-id-or-null>",
  "response_language": "zh-CN",
  "session_ref": "<unique-session-ref>",
  "authorization_message_digest": "sha256:<standing-or-delta-authority-digest>",
  "authorized_at": "<canonical-UTC-time>",
  "expires_at": "<canonical-UTC-time-not-after-conformance-expiry>",
  "conformance_result": "/absolute/current/deepseek-conformance.json",
  "gateway_database": "/absolute/new/gateway.sqlite3",
  "launch_receipt": "/absolute/new/alpha-launch.json",
  "terminal_receipt": "/absolute/new/alpha-terminal.json",
  "maximum_questions": 3,
  "maximum_dispatches_per_question": 24,
  "maximum_total_dispatches": 72,
  "known_limitations": ["Alpha evaluation only", "src/main/resources is excluded"]
}
```

`cognition_snapshot_id` 在单 Snapshot 时可为 JSON `null`，多 Snapshot 时必须是 exact ID。数据库与两份 receipt 路径必须互异且尚不存在；
launcher 必须以 exclusive create 原子创建 Gateway SQLite 主文件并强制 mode `0600`，其整个存活期的 `-wal` / `-shm` sidecar 也必须在
private creation mask 下保持 `0600`。不能先让 SQLite 按进程默认 umask 创建 `0644` 文件后再补 chmod，因为 role input、Source evidence、
Ledger、Package 和 Review 可能已在窗口期落盘。并发占用或权限不满足必须在 listener 前失败关闭。
配置不得包含 Secret value；`@1` 的 DeepSeek credential 只在每题首个已授权 dispatch 前从冻结配置所指的环境引用解析。ADR-017 目标
则要求每个 Provider attempt 只解析自身 route 的 credential，另一 route 的 secret reference 不能进入该 attempt。公开来源配置必须绑定
新 product freeze 与有效 standing authority；只有 material delta 才绑定 post-freeze human delta，且 launcher 不接受
host/port/question/request/run 参数。旧
`engineering_qa_preview_cli` 是历史单题审计兼容面，不是当前 Alpha 或平行演示入口。

历史 exact prepared question/run 的审计复现入口使用：

```bash
PYTHONPATH=src:. python3 -m software_world_model.interface.engineering_qa_preview_cli \
  --product-repository /absolute/clean/software-world-model \
  --product-commit <exact-product-commit> --product-tree <exact-product-tree> \
  --repository /absolute/exact/local-git-repository \
  --repository-id <stable-repository-id> --binding-id <world-model-binding-id> \
  --repository-revision <full-git-commit> \
  --source-profile-ref <versioned-profile-ref> \
  --source-path src/main/java --document-path README.md \
  --build-path pom.xml --test-path src/test/java \
  --ordered-envelope /absolute/published/ordered.json \
  --snapshot-bundle /absolute/published/snapshot.json \
  --question '<exact-authorized-question>' --request-ref <exact-request-ref> \
  --run-ref <exact-run-ref> \
  --authorization-message-digest sha256:<exact-user-message-digest> \
  --conformance-result /absolute/current/deepseek-conformance.json \
  --gateway-database /absolute/new/gateway.sqlite3 \
  --launch-receipt /absolute/new/launch-receipt.json \
  --terminal-receipt /absolute/new/terminal-receipt.json \
  --port 55120
```

安装后的兼容命令名为 `swm-engineering-qa-preview-evaluation`；`swm-engineering-qa-evaluation` 只指向评估 Alpha，避免普通体验者误入逐题 prepared 入口。

所有占位符都必须替换为 freeze 后的 exact 值；多 Snapshot Read Bundle 还必须传 `--cognition-snapshot-id`。三个输出路径必须尚不存在且
彼此不同。命令不接受 host 参数，固定绑定 `127.0.0.1`；它不下载、更新、checkout、推断 evidence class 或读取 hidden 输入。

- `WORLD_MODEL` 显示 source revision、exact Snapshot、Read Bundle digest、View、Profile/关系 modality、Coverage、View Limitation/Knowledge Gap、Fact 与 Evidence 引用；问题请求只读不含 Evidence payload 的 exact Snapshot Read Bundle，不得触发更新或访问 Source、权威数据库或 Evidence Store。点击引用由浏览器另行访问密封结果后的 Citation Projector，不把正文发送回问答进程。
- `DIRECT_INVESTIGATION` 显示 exact Source Target 与 Evidence Packet；它按 ADR-013 调查源码，但不能标成世界模型回答。
- 目标 Engineering Chat 页面在 Conversation Authority 中固定 protocol identity、exact repository/revision、World Model Read Authority、Source allowlist、Source Profile identity、Tool Catalog、versioned Conversation input policy、standing authority 和预授权的通用 `preferred → fallback` route role/execution-profile refs。具体 Provider/model 只作为运行配置、资格、Adapter/plugin 和 receipt 详情展示，不得成为产品、Agent 或 route branch 条件。公开来源边界内，浏览器按 Turn 提交 user message 即可，Conversation/Turn/run ID 由服务签发并自动派生 exact authority/receipt；不得要求用户再确认相同模型披露。只有 material delta 才显示并取得新的 human decision。历史 prepared 模式仍只能接受其 grant 中 exact request ID/question。新 Conversation 的空 Context 指代若命中 Binding-owned policy，页面必须在 Source/Provider dispatch 0 下显示可操作澄清，并在 health/developer projection 中展示 policy identity；Session budget rejection 或通用失败文案不能冒充该行为。Provider 选择与 fallback 对普通用户透明；只有受信 availability owner 密封 preferred profile 真实不可用 verdict 时才能进入 fallback。格式无效或 Reviewer 拒绝必须在同一 profile 内以新 authorized call 修复/重写，或如实关闭当前 Turn，不能换路由。默认主视图展示语义连续的消息、结论优先答案、结论级 Citation 与可理解的 unknown/limitation；失败 Turn 必须区分 execution-stage code 与已密封 raw Provider classification/code，不能用前者隐藏后者或从两者推导 fallback。开发者详情才展示 Turn/provider-attempt identity、availability verdict/fallback reason、成本与 quarantine。World Model Cognition、Agent Work State 摘要、Broker Decision、Evidence Ledger/Package digest、调用数和 Review Finding 折叠到开发者详情，不平铺为用户答案。手册或地图只能作为世界模型认知投影展示，不得将其标成完整世界模型。
- Engineering Chat 不根据问题、项目、关键词、符号、fixture 或 Oracle 切换后端。World Model Cognition 缺失或无关不会切换为 Direct；主 Agent 的源码调查是同一受权 Turn 的策略，每个 Proposal 必须由 Broker 编译、Worker 只读执行并追加 Ledger，实际工具、证据来源和重规划必须可审计。兼容 Alpha 当前仍按 `ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3` 单题/固定角色语义运行，不能由 UI 外观推导新协议已经实现。

人工更新是独立操作：即使从未提问也能构建新 Snapshot；计划或来源事件自动更新需要独立启用和运维证明。

现有单进程 `http_api` 仍只属于 `DIRECT_INVESTIGATION`，不是合格的 `WORLD_MODEL` launcher。World Model
入口由产品代码中的独立 WSGI adapter 和 trusted evaluation launcher 提供：启动时读取当前 verified dynamic
`SWM-READ-SET-CATALOG@1`，并以 `CANDIDATE` evaluation grant 绑定 exact source commit/tree、role package、launcher、
held-out suite、independent evaluator、Provider subject 和确定性资格。每个问题创建新的 `0700` run directory，只能按 Profile
已取得资格的 role protocol 通过 exact Model Egress Gateway 调用 Provider 且不重试：既有 Maven/Java Static Call Profile 保持
已接受的单调用协议；`JAVA_SOURCE_SEMANTICS@1` 使用隔离的 2—4 次 Investigation、一次 Draft 与一次 Review，旧固定三调用资格不能
继承。Answer 进程无 Source、Repository、Evidence payload、Oracle 或 baseline；Citation 由浏览器按 request/result 另行 GET，并由
无网络 Projector 的密封 Projection 重新验签。该 Profile 的启动收据声明
`TWO_TO_FOUR_INVESTIGATION_THEN_DRAFT_REVIEW_NO_RETRY`；每题由 supervisor 预建上限 6 个独立 Provider connection，Gateway 按实际
4—6 次调用顺序消费且不能复用，未消费 connection 在 terminal 后关闭并审计。页面必须展示 investigation step count、budget、
Coverage/完整性 verdict、trace digest、实际 Provider 调用数和具体 Gap/Limitation，不能只显示最终正文。

当前服务没有认证，所有现有入口与未来 Engineering Chat 方向体验都必须精确绑定 `127.0.0.1`。启用任何非 `EVALUATION_ONLY` 的模型生成路径时，需要为 Conversation 中每条允许 route 显式加载仍有效且与当前实现、模式匹配的 Provider Conformance、Capability Qualification、Product Validation 和本机 Activation；任一 route 的证明缺失、过期或漂移会使该 route 不可用，不能扩大到未授权 Provider。真实模型运行还必须在每次 Agent/Reviewer dispatch 前密封“哪些 current Turn、受信 relevant Conversation Context、World Model Cognition、Agent Work State、Evidence Ledger 或 Turn Evidence Package 字段/片段可发给哪个 exact Provider/model/purpose”及 redaction/input digest。公开来源 standing boundary 内由可信系统自动派生 one-use disclosure authorization；开发或浏览器启动本身不能替代该派生，也不得要求人工逐 dispatch 批准。首次 `EVALUATION_ONLY` 候选验证不循环要求尚未产生的 Product Result，但必须绑定 exact Conformance、Provider Qualification、候选 package/launcher、确定性资格和预先密封的 Product suite/evaluator；页面保持 `CANDIDATE`，直到运行后 Product Validation 与人工接受完成。它不得伪造或推导 Activation。确定性 Snapshot/View 读取可独立运行，但不能冒充已经通过模型回答 Gate。

Capability Evaluation、Product Validation 和本机交互体验只允许在显式 `EVALUATION_ONLY` browser sink 中运行。
页面必须持续显示不可关闭的评测标识，禁止生产 Delivery、跨授权 Conversation 复用和正式 Activation；输出只进入隔离验证目录。对现有 `WORLD_MODEL / EVALUATION_ONLY` 入口，自由文本只在用户选择的 exact、单一 Profile Read Set 与 Coverage 内求解：覆盖外问题应返回 Knowledge Gap；无法形成已验证 Result 时必须显示失败关闭，不能切换 Direct 或回源。目标 `ENGINEERING_CHAT_EXPERIENCE@1 / EVALUATION_ONLY` 则按预先声明的 World Model Cognition + exact-revision Broker/Worker 工具边界，由主 Agent 形成 append-only Ledger，并在当前 Turn 调查结束后密封 Turn Evidence Package；它不受本段 World Model-only Coverage 规则限制，但仍必须失败关闭且不得切换模式。

启动本机 World Model 候选评测入口：

```bash
PYTHONPATH=src:. python3 -m software_world_model.interface.world_model_http \
  --database /absolute/canonical/path/authority.sqlite3 \
  --catalog-root /absolute/canonical/path/catalog \
  --bundle-root /absolute/canonical/path/bundles \
  --evaluation-grant /absolute/canonical/path/evaluation-grant.AUTHORIZED.json \
  --session-root /absolute/path/to/new-private-session-root \
  --socket-root /private/tmp/new-short-swm-socket-root \
  --host 127.0.0.1 \
  --port 55121
```

所有示例路径都必须替换成启动主机上的 exact 路径；database 必须是无符号链接的 canonical regular file，session/socket
root 必须尚不存在。launcher 不从 `validation.*` 推断默认工件，也不会下载、重建或降级。`evaluation-grant` 必须使用
`SWM-WORLD-MODEL-EVALUATION-GRANT@2`。公开来源路径中该 exact grant 由 trusted launcher 从 standing authority、原问题与
no-payload published Structure 自动派生，而不是要求用户逐题签发；private/unknown/dirty/local data 或其他 material delta 仍要求 human
delta。`NOT_AUTHORIZED` grant 会在创建 session、Provider socket 和 HTTP listener 前拒绝。派生之后，launcher 仍会在监听前
重验全部 digest、当前 session Gateway authorization receipt、实际 Workspace/authority deny targets 和 OS isolation
preflight。服务没有认证，固定只绑定 `127.0.0.1`。

候选冻结在派生 authorized browser grant 前，必须用 runtime exact `-I -S -B` flags 和 role package root 导入真实 Answer/Gateway/
Projector entrypoint，且证明 Answer 不依赖未封入 role package 的 `site-packages`。OS capability probe 只证明允许/拒绝操作，不能替代
真实产品入口的 import/dependency closure；任一 entrypoint 不能导入时，页面不得进入可体验候选状态。

确定性资格必须区分 raw full regression 与允许继续的 regression gate。历史 `SWM-WORLD-MODEL-DETERMINISTIC-QUALIFICATION@1`
仍只接受 raw full regression PASS。ITER-008 bounded route 可使用 `@2`：raw suite PASS 时按普通 `PASS`；若当前环境只能精确复现
`FINDING-008-020` 已密封的 ITER-003 prepared Codex binary drift，则只能记录
`PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD`。后者必须证明五个历史测试各执行一次、结果精确为 4 `FAIL` + 1 `ERROR`、测试 ID 和
V-009/prepared-binary 原因 marker 全部相等、其余当前测试全部通过；任何新增、缺失、改名、skip、结果类型或原因漂移都阻断 freeze。
资格文档必须同时保留 raw `full_regression_pass: false`、通过数/总数、完整 held test identity 和 stdout/stderr digest，不能写成
full-suite PASS。该 versioned gate 只允许继续当前 `EVALUATION_ONLY` public Web 验证；它不能形成 Slice Acceptance、hidden canary
豁免、Direct/Production Activation，也不能改写或跳过 ITER-003 的历史 freeze 和断言。

历史 `validation.structure_world_model_iteration_004.interactive_browser` 只保留为已接受证据和回归输入，不再是当前产品
启动入口。

Evidence-first Direct 入口仍使用原命令，并且不能显示为 World Model：

```bash
PYTHONPATH=src python3 -m software_world_model.interface.http_api \
  --database var/browser-experience/swm.sqlite3 \
  --host 127.0.0.1 \
  --port 8765 \
  --enable-activated-model \
  --conformance-result var/conformance/<current-result>.json \
  --activation-environment local-browser
```

Direct 命令中的证明与 Activation 必须匹配启动时的 exact 实现、配置、模型和环境；示例占位符不是可加载资格。
历史本机体验、测试通过或日期尚未到期都不能替代启动时的完整重验证。World Model 的本机评测 PASS 也不产生
Direct Activation 或 Production Activation；Production Activation 仍为 `NOT_EXECUTED`。
