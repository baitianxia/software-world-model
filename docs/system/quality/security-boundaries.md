---
id: SYS-QUALITY-SECURITY
kind: system-quality
status: current
authority: normative
owners: [security, architecture]
depends_on: [SYS-ARCH-INVARIANTS, SYS-ADR-017, SYS-ADR-018]
derived_from: [FINDING-008-024, FINDING-008-036, FINDING-010-008, FINDING-010-009, FINDING-010-011, FINDING-010-012, FINDING-010-029, FINDING-010-031, FINDING-010-070, FINDING-010-071, FINDING-010-073, FINDING-010-092, FINDING-010-093, FINDING-010-104]
code: [src/software_world_model/ai_infrastructure, src/software_world_model/source_integration, src/software_world_model/application_services/citation_projection.py, src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/infrastructure/file_structure_read_bundle.py, src/software_world_model/infrastructure/file_citation_observation_store.py, src/software_world_model/interface, validation/structure_world_model_iteration_003/isolation, validation/structure_world_model_iteration_003/g3b, validation/structure_world_model_iteration_007/slice1_live_evaluator.py, validation/structure_world_model_iteration_008/slice1_live_evaluator.py]
tests: [tests/test_model_gateway.py, tests/test_source_operations.py, tests/test_browser_chat_interface.py, tests/test_structure_read_bundle.py, tests/test_structure_view_cli.py, tests/test_citation_projector.py, tests/test_iteration_003_g2_isolation.py, tests/test_iteration_003_g3b.py, tests/test_model_egress_gateway.py, tests/test_pinned_ark_https.py, tests/test_pinned_deepseek_https.py, tests/test_world_model_http.py, tests/test_world_model_evaluation_grant.py, tests/test_world_model_gateway_authorization.py, tests/test_iteration_007_slice1_freeze.py, tests/test_iteration_007_slice1_live_evaluator.py, tests/test_iteration_008_slice1_freeze.py, tests/test_iteration_008_slice1_live_evaluator.py, tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_tools.py, tests/test_conversational_engineering_model.py, tests/test_engineering_chat_candidate.py, tests/test_engineering_conversation.py, tests/test_engineering_chat_browser.py, tests/test_engineering_chat_alpha_cli.py, tests/test_engineering_question_answering.py, tests/test_engineering_question_cognition.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py, tests/test_engineering_qa_source.py, tests/test_engineering_qa_live.py, tests/test_engineering_qa_preview_cli.py, tests/test_engineering_qa_browser.py]
---

# 安全边界

## 不可信输入

用户输入、软件来源内容、模型响应、Provider 元数据、外部工具输出和交付确认均不可信。它们必须通过其 Owner 的授权、Schema、身份和语义检查后才能影响权威状态。

## 权限规则

- 模型不能获得 shell、Web、MCP、文件或来源工具；领域 Tool Proposal 由平台授权执行。
- Source Operation 必须绑定当前授权、精确 Binding、Target 和预算，且只读。
- Engineering Conversation 在任何执行前固定 exact repository/Binding/revision、World Model Read Authority、source path/content allowlist、
  Binding-scoped versioned Source Profile ref/digest、closed Tool Catalog 和文件/字节/时间/Agent Attempt/Package Revision 熔断。主 Agent
  只能读取 Application 密封的 current Turn、relevant Conversation/Work State、World Model Cognition 和 Ledger prefix，并提交 World
  Model query 或 Source Tool Proposal。Source Broker 把 Proposal 及其 evidence class、path/query/locator 当作不可信建议，重新校验
  authorization、global/class allowlist、revision、operation 与 expected modality 后编译 caller 不可伪造的操作。只有隔离 Retrieval Worker
  可以挂载两层 allowlist 交集内的 exact-revision regular files；它拒绝 traversal、symlink escape、submodule/remote fetch、binary/
  oversize、类型重标、写、任意命令、新网络、credential 和 Knowledge Update。每个 Proposal、Decision、Operation 和 Result 都追加到
  Evidence Ledger。模型、用户消息、Conversation state、来源内容或 Worker 均无路径、分类或授权权威。
- 工程 Chat 读取的源码、注释、README/其他仓库文档、配置和测试全部是不可信 data。其中任何 prompt、命令、URL、路径、evidence class
  声明、工具建议、权限或外发声明都不得成为 instruction，不得扩大操作集、路径、类型能力、revision、Source Profile、Provider disclosure
  或预算。用户纠正可以改变对话目标和待验证假设，但不能成为 Source truth。
- Secret 只保存 Reference，并在 exact endpoint 的 TLS/SNI/certificate 验证成功后、HTTP 分派前解析；不得进入文档、命令参数、数据库正文、日志或 Result。每个 Provider transport 必须以 strict Session audit 分列 TLS attempt/success、credential resolution、HTTP dispatch、connection reuse、post-dispatch unknown 与 retry。HTTP 前已知不可用只能由 transport owner 产生 typed unavailable，且 audit 的 credential/HTTP count 必须与实际阶段一致；HTTP 已开始后的失败必须保持 outcome unknown，二者不得互换。
- 编码、Conformance、Capability Qualification、历史 Product PASS 或历史披露许可都不能推导新的外部分派授权。每次新的
  `EVALUATION_ONLY` 问题披露必须由 exact grant 记录用户、时间、authorization ref 和 payload boundary；未授权 grant 必须在
  创建 session、Provider socket 或 listener 前拒绝。Gateway 必须再验证由同一 grant 派生的当前 session receipt，才能解析
  credential 或进入 qualified baseline；历史 permission 只能保留为 capability baseline provenance。
- 主工程 Agent 与独立 Reviewer 使用彼此隔离的上下文，Provider 会话记忆不能成为正式输入或恢复状态。主 Agent 只消费 Application
  密封的 current Turn、Conversation/Work State、Cognition 与 Ledger prefix；Reviewer 只消费 current Turn、受信 relevant Conversation
  Context、当前 Package 和 Draft。Reviewer 无 World Model/Source Tool、Broker dispatch、shell、网络、credential 或写权限；具体 Finding
  只能由 Application 路由为同包 Agent 修订或新 Agent evidence Attempt。包内冲突、部分或未知必须留在 boundary/audit 分区，不得通过
  模型记忆、用户陈述或临时工具补齐。
- `ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3` 兼容运行仍须执行其 Initial/Verification Investigation、Answer、双 focus Review、typed
  `VERIFICATION_GAP`、五类 closed schema/receipt 和 consumed-path/gap-boundary 规则；这些规则不能被复用为
  `CONVERSATIONAL_ENGINEERING_AGENT@1` 的固定角色拓扑，也不能证明新协议已实现。
- 把 Conversation Context、Agent Work State、World Model Cognition、Evidence Ledger 或 Question Evidence Package 的任何片段发送到外部
  Provider 前，必须另行授权并密封 exact Provider/model/endpoint/configuration、Agent/Reviewer purpose、允许字段/片段、redaction、secret
  reference 和完整 input digest。每个动态模型输入都形成一次性授权，Gateway 在 credential/HTTP 前独立重验 root Turn、Conversation/
  Work State Revision、run grant、完整 payload 和 Provider qualification；secret reference 与 grant/receipt 不进入模型消息。开发授权、
  历史 Provider PASS 或同一内容对另一 invocation 的披露不能推导本次外发。授权或 input 越过 Gateway 即消费；同 Provider 异常、outcome
  unknown、drift 或 replay 均不 retry。ADR-017 fallback 使用新 Agent attempt，从受信 original Turn input、exact Conversation Context 和
  Cognition 重跑完整链，不能复用前一 Provider 的隐藏状态或未密封中间产物。
- Engineering Conversation trusted launcher 必须证明自身来自 clean exact product candidate；listener 前重验 exact Source commit、published
  World Model Bundle digest/read authority、Source Profile/allowlist、Tool Catalog、Provider qualification 与 Conversation authority，并用新
  `0600` 文件密封零分派 launch receipt。Gateway database/sidecar 和 launch/terminal receipt 从创建起保持 private mode。terminal receipt
  按 Conversation/Turn/provider attempt 密封一次性 disclosure、Gateway/TLS/credential 计数、同 Provider retry 0、fallback/quarantine、
  潜在重复成本和 `NOT_EXECUTED` Activation，不得包含 Secret value。
- 持续 Engineering Chat 不得把 prepared Turn/Request grant 当成整段 Conversation 授权，也不得允许浏览器 POST 扩大 session authority。
  listener 前必须固定 clean product、loopback origin、工程/Binding/revision、World Model authority、Source Profile/allowlist、Tool Catalog、
  有序 Provider routes、disclosure scope、redaction、有效期和每 Turn/整 Conversation 熔断。用户提交 exact message 后，受信 ingress 才能
  签发 one-use Turn receipt 和 server-owned identity；后续动态 Agent/Reviewer input 仍须 exact one-use authorization。重复、跨 Turn 复用、
  边界漂移、过期或总熔断耗尽必须在 credential/HTTP 前拒绝；某 Turn 失败不得停止 listener 或使另一 Turn 继承未密封状态。
- Verification 的 target disposition replacement 不是任意覆盖：当 predecessor target 为 `SUPPORTED` 时，Application 必须投影 exact
  observation preservation contract，并在 merge 时机械拒绝删除、改写或重排既有 supported facts 的 delta。caller full content 已可见的
  cache/write/notification/external interaction 只补 caller-boundary typed observation，不借此取得未挂载 callee 内部；lossy replacement
  必须在 successor Package seal 前失败关闭。
- Engineering Conversation 的同包重写保持同一 Package Digest；Reviewer 的具体 evidence gap 只能驱动绑定该 gap 的新主 Agent Attempt，
  并继续经 Broker/Worker 逐步校验执行。越权、Turn/Package/Work State identity 不一致、未密封 Observation 或失败关闭时均不得 merge；新
  Package 必须重走独立 Review。诚实 verified Limitation 不得被同一缺证反复请求绕过熔断，Draft 自行扩张的 non-material 结果也不得扩大
  Source scope。revision/call/operation/bytes/wall-time/no-progress 熔断只能失败关闭，answerable 超限计失败，不得删减用户目标、证据、
  Citation 或 Review。wall-time 不仅在调用前检查；任何 Agent、Reviewer、Projector 或 Worker 返回后、其输出取得权威状态转换权前都必须
  重验，`elapsed >= maximum` 即耗尽。`@3` 的 single-gap delta/preservation 规则继续只约束兼容运行。
- `JAVA_SOURCE_SEMANTICS@1` 的 Investigation step、Draft 与 Review 是独立 Gateway workload：首个调查 step 不读取正式知识
  payload，后续 step 只能读取平台密封的 typed trace prefix；Draft 不得读取 Reviewer 或 Citation observation，Review 不得读取
  Provider 会话记忆或 Source。角色只能通过平台密封的 Requirement/trace/Assessment/Draft 逐阶段传递；role package、model call、
  socket/session receipt 与调用审计不可复用。每题调查 2—4 次，随后 Draft/Review 各一次，无 retry。
- 多 Provider route 只能在 Session 开始与任何问题 dispatch 前预授权；每条 route 都必须分别具有 current exact Conformance、Capability
  Qualification、endpoint、secret reference、disclosure scope 和隔离 transport。当前顺序为 Ark → DeepSeek。一次用户提交创建一个
  logical interaction unit；Engineering Conversation 中该单位是密封 Turn，兼容单轮协议中是 logical question。primary attempt 只有在
  密封 terminal、没有 authorized answer且可信分类为 Provider unavailable/HTTP error/outcome
  unknown/output invalid 或 model Review rejected 后，才可创建最多一个 fallback attempt。Application/Source/Security failure 不得
  fallback。Fallback 从 immutable original interaction input、Chat 时 exact relevant Application-sealed Conversation Context，以及同一 exact
  Cognition Context 重跑完整链；两个 attempt 的 Ledger/Package/Draft/Review/Provider session 不得交叉；同 Provider retry 为 0，late
  primary response 必须 quarantine 且不得覆盖。用户无需选择 Provider、
  重提问题或新建 Session。
- `WORLD_MODEL` 答案进程的应用输入只能读取 package 与不含 Evidence payload 的 exact Snapshot Read Bundle；解释器、系统 runtime、精确 ancestor directory traversal 和独立输出 capability 必须单列，且不得包含目标来源、工作树、权威/旧数据库、Evidence/Citation Store 或另一角色输出。其网络默认拒绝：无模型阶段禁止全部出站；真实模型阶段只能连接 evaluator-owned exact Model Egress Gateway，由网关校验 Manifest 固定的 Provider scheme/host/port/path 并注入 credential。答案进程不能直连 DNS、公网、Source remote 或 Citation Projector。若本机 OS 不能按单一公网 IP 过滤 Gateway connect，允许由无 credential、无请求/响应 payload port 的 Gateway supervisor 预解析，并按已资格 connection policy 建立有界 exact peer TCP descriptor set，再把这些 descriptor 与 evaluator 已绑定的 exact `0600` AF_UNIX listener 交给 sandboxed Gateway child。默认一请求一连接的 transport 必须明确发送 `Connection: close`；显式取得资格的 persistent verified TLS transport 才能在同一授权 run 内发送 `Connection: keep-alive` 并复用 session。当前 DeepSeek bounded policy 预置 3 个 descriptor，读取 credential/Authorization/HTTP bytes 前最多进行 3 次 credential-free TLS acquisition，且每条 verified session 最多 20 次 HTTP dispatch；达到上限后的轮换发生在下一次 credential resolution 前。HTTP bytes 可能已发送后绝不重发 request。每个逻辑调用仍按 Investigation* → Draft → Review 拥有独立 Manifest、receipt、request/response audit。未使用 descriptor 在 Answer terminal 后关闭并审计为 `UNUSED_CLOSED`，且 `provisioned = TLS attempts + unused_closed`；Provider call、TLS attempt/success、reuse、per-session dispatch bound、post-dispatch unknown 与 request retry 必须分列，`request_retry_count` 必须为 0。少于、多于、交换、未资格复用或跨题/session 复用均失败关闭。地址 scope 必须如实区分标准 public unicast 与 executor 明确提供的 synthetic external peer，loopback、普通 private、link-local 与其他 reserved 地址仍拒绝，不能把 synthetic 地址误报成公网 IP。若 Seatbelt 对继承 TCP 数据面仍要求 remote-port `network-outbound`，该规则只能与拒绝 `SYS_socket`/`SYS_socketpair`/`SYS_socket_delegate` 的 syscall firewall 联合使用；child 必须无法创建任何新 AF_UNIX/INET/INET6 socket，并在解析 credential 前复核 peer、TLS certificate/SNI 与 exact HTTP scheme/Host/port/path。该组合只证明 digest-sealed 闭合 workload 的新 socket 创建被 OS 拒绝：它不是抵抗任意 native code execution 的 exact destination firewall，因为 Darwin `disconnectx`/`connectx` 可重定向既有 descriptor。正常 workload 必须另以 digest seal、禁止 fork 与 `connect`/`bind` 零计数审计闭合；若威胁模型包含任意 native code execution，必须改用 VM/container/per-process network namespace 或等价的 exact destination enforcement。preflight 必须真实执行继承 descriptor 已连接 exact peer、继承 listener 往返、继承 TLS 和新 socket denial；审计必须分列 supervisor connection provisioning、credential-free TLS acquisition、unused close、listener handoff 与 child Provider dispatch，并验证数量、复用关系与角色顺序，不能把 remote-port 规则单独描述为 endpoint allowlist，也不能声称 OS 提供了实际不存在的 remote-IP filter。
- Evidence observation 只由 trusted broker 在密封 Result 后通过窄 Knowledge owner Port 读取，并按该 Result allowlist 物化新的 disposable Citation Store。独立 Projector 只能读取 package、Result seal 与这个 exact Store；不能直接挂载权威数据库或完整 Evidence Store，不出网，没有模型、Query、Update 或答案回传端口。Store 缺失、额外、重复、换序或 digest 不匹配均失败关闭。
- OS 隔离证据必须区分应用输入、runtime/ancestor traversal、输出与拒绝目标，绑定实际 policy 和 capability 参数。若 exact ancestor directory capability 可枚举其直接条目名，必须把名称披露作为 executor limitation，不能误称为 metadata-only；这不等于允许读取子文件内容。使用 capability sandbox 时只能声称相关操作被 OS 拒绝，不能声称未实际建立的 mount/network namespace；固定探针、产品 workload 必须分进程，计划、Mock、probe-only 或进程自报不是执行证据。候选冻结还必须在 role 实际使用的隔离解释器 flags、环境和 package root 下导入每个真实 entrypoint；普通测试环境可见的 `site-packages` 不能充当隔离 role dependency closure。source-off Answer 的包初始化不得因无关的 Update/export convenience import 获得 parser 或 Source dependency。
- 无认证 HTTP 服务只能绑定回环地址；非本机部署必须先补认证、授权和威胁模型。HTTP ingress 必须在产品路由前验证声明的 byte count、
  完整读取、UTF-8、unique-key JSON、closed root fields 和字段类型；重复 key、短读或 trailing/ambiguous body 均失败关闭。持续
  Engineering Chat 页面只接受 current conversation identity、user message 与显式 disclosure acknowledgement；Turn/run ID 由服务签发。
  POST 还必须在 receipt/transport/credential 前要求 `Origin` 精确等于已验证的 loopback Host、media type 为 `application/json`，且存在的
  `Sec-Fetch-Site` 只能是 `same-origin`。旧 prepared `@3` 模式只能接受其 exact Request，二者不得混用。

失败、配置缺失、资格过期、身份漂移、输入截断或结果未知都对当前 provider attempt 采用 fail-closed 行为，且不得把未知伪装成确定失败。
只有 ADR-017 明确允许、预授权且重新执行完整链的 fallback attempt 可以继续同一 logical question；它不能追认或修改已失败 attempt。

Engineering Conversation 中上述 `logical question` 必须解释为密封 Turn；只有同一 Turn 的预授权 fallback 可以继续，不能把整段
Conversation 当成一次交互或复用单位。

`ENGINEERING_CHAT_EXPERIENCE@1` 的 Access scaffold 已本地实现 exact loopback/Origin/JSON/input 边界和 0-dispatch 失败真相；
`CONVERSATIONAL_ENGINEERING_AGENT@1` 的 Application-owned executor、Work State/Observation/Package/fresh Review/Delivery exact binding
已形成确定性本地候选，并对 forged binding、未授权 Source operation、缺证后无新 Observation 重写、无进展和 malformed outcome 失败关闭。
World Model/Source/Ledger trusted tool adapter 与单 Provider Agent/Reviewer 的 one-use Disclosure/Gateway receipt 已分别形成
`EVIDENCE_TOOLS_LOCAL_CANDIDATE / MODEL_BOUNDARY_LOCAL_CANDIDATE`；确定 pre-dispatch 与 replay 计 0，fresh dispatch/unknown 计 1，
retry 仍为 0。non-dispatching candidate preflight 不读取 Source/credential、不启动 listener、不调用 Provider，并固定
`ready_for_live=false`。ADR-017 双 attempt、生产 Provider runtime、artifact fixed launcher 与 Ark/DeepSeek terminal Session audit 已形成本地
确定性候选；Ark HTTP 前不可用也已 owner-typed 为独立 fallback eligibility。fresh Ark Conformance 已 PASS，但旧 DeepSeek qualification
因共享 Gateway implementation drift stale；fresh DeepSeek Conformance、current actual artifact、Citation 内容与五轮 live Chat 仍为
`DUAL_ROUTE_NOT_QUALIFIED / NOT_LIVE`。以上边界不能由 fake/offline port、Access、旧 `@3` 运行、浏览器连续提交外观或既有
Provider 资格推导已经满足。
