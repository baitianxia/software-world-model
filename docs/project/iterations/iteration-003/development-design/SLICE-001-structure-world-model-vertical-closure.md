---
id: ITER-003-SLICE-001
kind: development-slice
status: completed
authority: historical-development
owners: [engineering]
depends_on: [ITER-003-PROPOSAL, SYS-ADR-014, SYS-ARCH-INVARIANTS, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-CONTRACT-KNOWLEDGE-ENTITY, SYS-CONTRACT-KNOWLEDGE-FACT, SYS-CONTRACT-KNOWLEDGE-ADMISSION, SYS-CONTRACT-KNOWLEDGE-SCHEMA-CORE, SYS-CONTRACT-KNOWLEDGE-STRUCTURE-MODEL, SYS-CONTRACT-KNOWLEDGE-SNAPSHOT-PUBLICATION, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE, SYS-CONTRACT-APPLICATION-STRUCTURE-VIEW, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-AI-CAPABILITY-EVALUATION, SYS-OPS-LOCAL-BROWSER]
code: [src/software_world_model/source_integration, src/software_world_model/knowledge_engine, src/software_world_model/application_services, src/software_world_model/infrastructure, src/software_world_model/interface]
tests: [tests]
iteration: ITER-003
coding_input: false
---

# SLICE-001：Structure World Model 纵向闭环

## Status and dependencies

本 Slice 已按 `ITER-003-RESULT-ACCEPTANCE` 完成并转为历史开发材料，不再是当前编码输入。G0、G1、G2、G3a、V-009、修复后的全新 G3b batch/evaluator 与 G4 均 PASS。最终 V-009 在 checkpoint `019f9fced69110c6a7e357a4ea2394ec6742fd2e` 上以 freeze `1.0.5` 取得 Conformance PASS、closed CE 7/0/0 PASS/VALID，并在任何 G3b 产品结果可见前密封 controlled Direct 与 Mature Source Agent 各 55 个 run。Direct 为 15 SUCCESS/40 preserved FAILURE，Mature 为 55 SUCCESS/0 FAILURE；初始 G3b 58/60 FAIL 与后续修复后 60/60 PASS 的 lineage 均永久保留。接受不包含 Production Activation，也不把新 Profile 扩成旧数据 Schema Migration。

## Current vs expected behavior

当前 Formal Fact 把关系目标保存为字符串，查询不保留 subject；Entity ID 受 revision-bound Context/Evidence 影响；Publisher 无条件继承旧成员；浏览器 Evidence-first 主路径直接读源码。这些实现不能证明世界模型结构可稳定更新和复用。

期望路径是：独立手动更新读取 exact Git → Maven Structure Candidate → Admission → `REPLACE_COVERAGE` Snapshot → Source-off Structure View → 浏览器 `WORLD_MODEL` 回答。提问只读固定 Snapshot，不触发前半段。

## System contracts and invariants

执行遵守 `INV-003`—`INV-015`，包括 `INV-011` 的逐问题完整性。关系必须使用 typed EntityRef；Root 与 State 分离；View 不创知识；世界模型与直接调查模式不混淆。

## Interfaces and affected code

- Knowledge Engine DTO/Admission/Query：Literal/Relation Fact、Root/State、endpoint closure。
- SQLite Formal Repository/Publisher：无损 typed persistence、`ENRICH`/`REPLACE_COVERAGE`、exact Snapshot 与 diff。
- Knowledge Update：`MAVEN_REACTOR_STRUCTURE@1` builder、完整 Coverage、独立手动命令。
- Structure View/Application：受控 entity candidates、模块、边、路径、diff、关系 modality、Support Map、Entity Resolution/View Limitation；Knowledge Use 才能按 Requirement 形成 Knowledge Gap。
- HTTP/Browser：显式模式、更新操作、Snapshot/View 元数据和可点击引用。
- Validation：名称反例、mall A→B→A、Source-off、直接调查对照与重复真实模型运行。

## Compatibility, data and security boundaries

旧 Schema、Scope、Snapshot 和 Evidence-first 接口保持可读；本轮不迁移或改写历史。Structure Profile 建立新 Scope并执行 INITIAL adoption。Source 只在 Update 或显式 Direct Investigation 中可用；Snapshot query/answer 进程只挂载无 Evidence payload 的 exact Snapshot Read Bundle，并注入调用即失败的 Source Provider。含 Evidence payload 的权威/旧数据库和 Evidence Store 均不得挂载。源码片段、Evidence excerpt 或由其形成的结构结果只有在首次外部 CE/模型分派前获得本轮明确披露授权后才可发给外部 Provider。

## Blocking development gates

### G0 — 冻结输入

在产品代码前运行并保存 `tests.test_iteration_003_fixture` 与 `tests.test_iteration_003_validation_assets`，核对已提交的防名称/GAV 拼接 Maven fixture、exact Schema/Evaluation Context/Canonicalization digest、mall Oracle、closed CE suite、相互隔离的 Product input/evaluator suites、同模型 Direct Source 与成熟 Codex Source Agent protocols、变形生成器的确定性/隔离、调用/时延边界和失败保存位置；Maven、冻结的成熟 Agent CLI 或任一必需工具缺失/漂移必须阻断，不能 skip-pass。含旧 Snapshot 的兼容性 fixture 已由 ITER-002 baseline 生成并冻结；首次持久化修改前必须再次核对其 generation commit、数据库/report digest 和人工查询结果。人工可查看物是 fixture POM、三个 Definition JSON、Oracle、问题输入/评测、两条 Agent 对照协议、旧 Snapshot 报告、测试原始输出与 Verification Matrix。

授权治理提交 Q 完成后运行 V-001，并写 `ITER-003-RESULT-G0` 绑定 Q、全部输入 digest 和人工核对结论。G0 PASS 提交前禁止任何产品代码修改。

### G1 — Knowledge Kernel

实现 typed Relation/Literal Fact、稳定 Entity/Fact Root、State、endpoint Admission 与 `REPLACE_COVERAGE`。`ENRICH` 对已有 Root 的不同 State 必须拒绝；Coverage ownership 本轮禁止重叠。运行 A→B→A 和歧义/悬空/重叠反例。人工可查看 CLI 报告必须逐行展示 Snapshot ID、revision、Entity Root/State、source/predicate/target、Fact Root/State、Evidence locator、Coverage Root/State、每条依赖声明的 resolved GAV/profile exclusion、删除项和旧 Snapshot 查询；exclusion 报告不得作为 Source-off 答案知识使用。

G1 不通过，禁止实现 Structure View、浏览器和模型答案。

G1 已由 `ITER-003-RESULT-G1` 在 checkpoint `ddb8f5feba1e0c52d2f788c2bb66c93810f2b469` 上裁决为 PASS；该结论只解除 G2，不替代 G2 的 Bundle 与 OS 隔离证明。

### G2 — Source-off Snapshot/View

完成构建后关闭更新进程，为 A1/B/A2 生成并机械验证不含 Evidence payload 的 exact Snapshot Read Bundle。把产品 package 与这些 Bundle 复制到独立临时回答目录；answer worker 的**应用/产品输入**只有 package 与 Bundle，目标 Git 仓库、原工作树、权威/旧数据库、Evidence Store、Citation Store 和另一角色输出都不得落入递归数据读取 capability。重启读取进程，按 exact A1/B/A2 Snapshot 查询 entity candidates、模块、全部简单路径、diff 和历史状态；同名 `common-lib` 必须返回两个 typed candidates，只有 full GA 或 exact Ref 才能唯一绑定。Bundle 必须证明 payload 字段/表为 0，查询不得新建 Snapshot；A2 表示 B 后再次对 source revision A 执行 replacement 得到的新 Snapshot，不是第三个 revision。

本机 G2 的实际 OS enforcement 固定为 macOS `/usr/bin/sandbox-exec` 与两个独立 deny-default Seatbelt profile，不声称建立了 Linux mount/network namespace，也不把宿主机仍存在的拒绝路径写成已经 unmount。两个 profile 都显式 `(deny network*)` 与 `(deny process-fork)`。应用输入以外只允许以下运行 capability：exact `sys.executable`；`/dev/null`、`/dev/random`、`/dev/urandom`、`/private/etc/localtime`；recursive `/System/Library`、`/usr/lib`、`/private/var/db/dyld` 与 exact `sys.base_prefix`；bundled xpkg 解释器只额外开放当前 worker 实际加载的 OpenSSL、SQLite、zlib canonical version root，不开放整个 package-manager root；以及各角色自己的 package/output，answer 的 Bundle root，或 Projector 的 Store root 与 literal sealed Result。所有 sandboxed Python 固定使用 `-I -S -B`，不得加载 user site、`site` 或 `.pth` 启动代码。`ANCESTOR_00`—`ANCESTOR_39` 由 exact Python executable parent、上述 runtime roots/aliases 和各角色 canonical roots 的自身及父目录组成、按路径深度和文本排序并用 literal `/` 补齐；Seatbelt 的 literal `file-read*` 允许路径穿越、metadata 和该 exact directory 的直接条目名枚举，但不递归开放其子文件内容。名称披露必须进入 executor limitation；若目录名本身也属机密，须更换为自包含 staged launcher 或 VM/container。全部参数、profile/executable/worker digest、实际 allow roots、dependency alias→canonical root 和 runtime dependency manifest 都必须进入原始证据，runtime root 不得包含任何受限产品数据，也不得被描述为应用输入。

View Result 密封后，受控进程中的 trusted Citation Observation Broker 才按 Result 的 typed Evidence allowlist 从 Knowledge owner 重读 observation，并预先物化物理成员严格等于 allowlist 的 disposable Citation Store。独立 Citation Projector worker 的应用输入只有 package、只读 Result seal 与该 exact Store，另有独立输出目录；它不直接挂载权威数据库或完整 Evidence Store，也没有出站网络、模型、Query、Update 或回传答案链的端口。父级 harness 只在 answer 成功后按 digest 单向复制 seal，不能形成 worker 间通信。

实际 `run` 必须先在 sandbox 外证明 exact forbidden file、SQLite、Git target、Source remote、公网 endpoint 与 DNS 可读/可达；随后每个角色先运行不加载产品代码的固定 digest-bound probe child，再以同 profile 运行独立 workload child。probe 必须证明 Source remote、公网、DNS、本机 TCP、Unix socket、越界 `open()`、SQLite、Git 文件/进程、subprocess 与 Answer↔Projector callback 全部被 OS 拒绝，workload 则必须以独立 PID 成功并产生与声明集合精确相等的 closed output manifest。两个角色使用不同 nonce，所有 probe/workload PID 必须互异。正常 workload 的 Source、Git、Evidence-payload-in-answer、权威 DB/Evidence Store、越界 file 与 network Operation 必须为 0；主动拒绝探测单独审计，不能伪装成业务读取。`plan`、Mock、probe-only 或 worker 自报都不能完成 V-007；原始 isolation report 只裁决 OS boundary，最终 Gate 还必须结合 Bundle/View/Citation 与人工核对。保存 capability policy/参数、PID/nonce/命令/环境、executable digest、allow/deny 审计、运行前后 protected-input digest、最终 closed output manifest、单向 seal transfer、Bundle/Store manifest/digest、JSON 与文本报告。

G2 不通过，禁止实现浏览器模型回答。

G2 已由 `ITER-003-RESULT-G2` 在 checkpoint `82aef7563556c70527b3c92227d0711a28437587` 上裁决为 PASS；该结论只解除 G3a 无外部分派实现，不授权外部披露、Provider/Model、CC/CE、baseline 或 G3b。

### G3a — Offline answer-chain implementation

在不分派任何外部 Provider 且无任何出站网络 route 的条件下实现 World Model Answering 和评测页面投影，以确定性 test strategy 完整走通 `Requirement Revision → Needs/Joint Constraints → candidate resolution → Query Plan → Query Result → Need Assessments → Draft → Review → Authorization → Delivery`。补齐 Need 遗漏、直接伪造 EntityRef、0/N candidate、跨 Session candidate、tampered Query Result、wrong Snapshot/Read Set、生成与审核同一 invocation、Evidence payload/网络读取和无授权 Delivery 反例，全部失败关闭。该范围已由 `ITER-003-RESULT-G3A` 在 clean exact checkpoint `f2269ecca5c1e85e69fafd93fe599c841227f3c7` 上裁决为 PASS，且只解除 V-008 阻断。V-009 又由 `ITER-003-RESULT-V009` 独立裁决为 PASS；该 Result 只解除 G3b 的技术前置阻断，G3b 仍需单独披露确认。

G3a 的 process-local authority store、deterministic strategies 与唯一 `EVALUATION_ONLY` sink 只服务本 Gate，不替代 live `ResponseControlService` 的 Task/Use/qualification/permission/persistent dispatch authority。应用层 Provider/network port count 为零只证明端口未被使用；全局无 Source/Evidence/network I/O 还必须复用 G2 deny-default Seatbelt 机制，以 package-owned strategy、exact Bundle 输入、正常 workload operation audit 和独立拒绝 probe 共同证明。评测页内部公开 digest 只能证明一致性：staging 必须把环境 commit 绑定 clean Git HEAD/tree，并从独立、递归验证通过且与 isolated workload 输入完全相同的 connected chain 预先冻结 expected PAGE digest；Projector 必须以带外 commit/PAGE 双锚点校验单向 seal。strategy 的语义资格仍由 V-009 CC/closed CE 裁决。

### V-009 — External strategy qualification and baseline preflight

V-009 不修改或替换 G3a offline authority。资格 subject 是独立的 `model-snapshot-first-world-model-answer@1.0.2` proposal strategy：每个 synthetic Case 恰好一次 no-tools Model Gateway 调用、零 hidden retry，Manifest 只有通用 instruction、sealed Case input 与 exact Conformance qualification reference。Evaluator-only 的 projection、expected result、forbidden events 和任何 Product suite/oracle 不得进入 Strategy、Manifest 或 Provider request。前两轮 `1.0.0` / `1.0.1` 的 6/1/0 FAIL 与第三至五轮 `1.0.2` 的 7/0/0 PASS/VALID 证据永久保留；三次 PASS qualification 均因随后发现的 baseline input drift 不可继承。最终 freeze `1.0.5` 全量运行取得可继承的 7/0/0 PASS/VALID，并完成两条 baseline；所有失败仍禁止选择性重跑。

Adapter Conformance 必须由 V-009 runner 从 enclosing clean checkpoint 发起：在第一次网络分派前以 O_EXCL 密封包含 exact Provider、endpoint、operator、timeout、token cap、披露引用、HEAD/tree 和 input-freeze digest 的 invocation receipt；运行后再把 immutable Conformance Result 绑定到独立 binding receipt。closed CE 只接受该 binding，不接受裸 Conformance Result；Provider outcome unknown 只形成阻断性 UNKNOWN evidence，不能在同一 freeze run 内重试。

closed CE 的七个 Case 由独立 `python -I -S -B` 标准库 evaluator 进程裁决；它只读取 sealed evaluator packet 与 normalized Result，记录独立 PID、implementation digest、exact projection digest 和 forbidden-event audit，不导入被评 planner/drafter/reviewer。generic Capability Evaluation authority 必须形成 closed Result；只有七 Case 全 PASS、FAIL/UNKNOWN=0 且 Validity=`VALID` 才产生 qualification。

Mature Source Agent 必须使用 protocol `1.0.3` 的 exact Codex binary、`gpt-5.6-sol` / `low` 与 strict config；不得带会回退到 legacy policy 的 `--sandbox`。sandboxed command filesystem 先 root deny，只开放冻结的 minimal runtime 与每个 isolated exact source workspace 只读，并拒绝 temp 与 network；Web Search、Apps 和 multi-agent 关闭。model-generated command 另固定 no-login、environment inherit-none，只注入冻结的非秘密 PATH/locale/timezone；operator credential/environment 不得进入模型消息或 tool output。首次模型请求前必须以同 profile 和**最终物理 staging root**证明 isolated workspace 可读而 original workspace、checkout parent、evaluator sibling、home、temp 与 network 均由 OS 拒绝；不能只按 `:slash_tmp` 名称推定 canonical `/private/tmp` 已拒绝。每个 run 的 workspace 只能包含授权 POM、answer schema 和 local Git metadata，保存 exact argv/event/stdout/stderr/exit/file-operation audit，任何失败不得筛掉。

默认拒绝 egress policy 固定 G3b 产品路线为 `Answer→AF_UNIX Model Egress Gateway→https://ark.cn-beijing.volces.com:443/api/coding/v3/chat/completions`，credential 只在 Gateway 最终 HTTPS dispatch 注入；Answer 不得解析 DNS 或直连 INET/INET6，Projector 全部出站拒绝。V-009 Conformance、CE 和两条 baseline 可使用 policy 明确标记的 direct Adapter qualification transport，但其 Result 不证明 G3b distinct Gateway process 或 OS network denial。任何 input、Strategy/Prompt/schema/tool/config、Provider identity、policy、suite/evaluator 或 checkpoint 漂移都使 qualification/baseline 失效。

最终 `ITER-003-RESULT-V009` 绑定 checkpoint `019f9fc…`、Conformance binding、closed CE qualification、55-run plan、Direct 15/55 success 与全部 40 preserved failures、Mature 55/55 success、7/7 permission preflight 和联合 baseline seal `sha256:7be049fe746a71cb3b9c3941d81e8e51076256d0f8dac61ba5a5c88c873ecbdd`。V-009 至此 PASS；后续修复后 G3b/V-010/V-011 与 G4 的最终 PASS 分别见 `ITER-003-RESULT-G3B` 与 `ITER-003-RESULT-G4`。

### G3b — Evaluation-only browser model run

事后 evaluator invocation 中的 `comparator digest` 必须同时密封 V-009 baseline seal 的原始文件
SHA-256、复算后的内部 document digest 以及 baseline comparison preflight digest。

只有 World Model Capability Result 对 G3a exact checkpoint 为 PASS/VALID，且同模型 Direct Source 与成熟 Codex Source Agent 的全部 baseline 已按冻结协议密封后，才在与 G2 同级的无仓库隔离环境分派真实模型。通信白名单固定为 `Browser→Answer`、`Browser→Projector`、`Answer→exact Model Egress Gateway`、`Gateway→Manifest exact Provider endpoint`；Answer 的其他出站与 `Answer→Projector`、Projector 的全部出站都由 OS/network namespace 拒绝并审计。当前 macOS Seatbelt 不能把公网 TCP capability 原生限定到单一 remote IP：Gateway supervisor 在 invocation 已密封后解析并匿名连接一个 exact external peer，trusted evaluator 另绑定 exact `0600` AF_UNIX Gateway listener，再把两个 descriptor 继承给 distinct sandboxed Gateway child；supervisor 不持有 credential、不发送模型请求或读取响应，收据如实区分 public unicast 与 executor synthetic external address，后者不得误报为公网 IP。Seatbelt 对 inherited TCP 数据面所需的 `remote tcp "*:443"` 规则不能单独作为 endpoint allowlist；child 同时以 `syscall-unix` firewall 拒绝 `SYS_socket`/`SYS_socketpair`/`SYS_socket_delegate`，preflight 必须证明 Provider descriptor 已连接 exact peer、inherited listener 往返与 TLS 成功、所有新 AF_UNIX/INET socket 创建失败。该 macOS executor 只在 digest-sealed 闭合 Python workload、禁止 fork 与正常运行 `connect`/`bind` 零计数前提下合格；它不是抵抗任意 native code execution 的 exact destination firewall，后者必须使用 VM/container/per-process network namespace 或等价机制。child 在解析 credential 前继续复核 peer、TLS certificate/SNI 和 exact HTTP endpoint。证据必须分列 supervisor connect、listener handoff、child connected-state/new-socket denial/TLS 与 Provider dispatch，不能伪称 Seatbelt 具备 remote-IP filter。页面必须显示永久 `EVALUATION_ONLY` 水印、`WORLD_MODEL`、commit、Snapshot/Read Set、Read Bundle digest、View、Profile/关系 modality、Coverage、View Limitation/Knowledge Gap、Fact/Evidence 引用、A/B diff 和完整权威链。问题请求不得调用 Update、Direct Investigation 或 Evidence payload；点击引用只走浏览器单独请求、不能回流答案进程的 Citation Projector。连格式修正总调用最多 5 次，未通过审核或超限即失败，不交付降级答案，不需要也不产生 Product Activation。若 60-run 已完整且 immutable，仅事后独立 evaluator 实现需要修正，可在产品 checkpoint 的 descendant clean commit 上做纯本地评估，但必须在扫描 individual terminal 前密封 product/evaluator commit+tree、evaluator digest、batch/prepared/oracle/comparator digest 与严格限定为 evaluator/测试/文档的 Git delta；任何产品 runtime、runner/profile、prepared input、Suite/Oracle/baseline 漂移仍要求重新判断授权并形成全新 batch。

### G4 — Human and product acceptance

人工在 `EVALUATION_ONLY` 真实页面逐题核对五个问题、exact 措辞变体、fixture 不同标识、运行时随机身份与拓扑图和一个应返回 Knowledge Gap 的“为什么”问题，点击引用、切换 A/B、执行零问题/零 Session 的独立更新并确认旧页面 Session 不漂移。每题至少五次且包含冷启动，保存全部成功与失败。Structure Coverage 支持的问题与 G3b 前已密封的两条源码 Agent baseline 逐题比较：同 exact Provider/Adapter/Model 的 controlled Direct 用于质量与性能，成熟 Codex Agent 用于质量；世界模型重大错误为零，完整性不得低于两者中更强者。unsupported why 只验证诚实 Gap，不要求追平可回源的 Direct Investigation。请求时延统一从 HTTP request received 到 terminal result persisted，冷启动另从 process start 计量。世界模型首问请求 P95 不超过 controlled Direct 1.5 倍，重复已建模问题请求 P95 不超过 0.5 倍。本轮只形成 Product Validation 证据，Production/本机 Activation 仍为 NOT EXECUTED。

## Anti-name-stitch fixture oracle

fixture 必须包含 nested module、目录路径与 artifactId 不同、两个 `artifactId=common-lib` 但 groupId 分别为 `org.example.shared` 与 `org.example.legacy`，以及声明 shared exact version、legacy 错误 version 和外部依赖的 billing 模块。只允许 `billing → org.example.shared:common-lib`；不得按 GA 把 legacy v2 dependency 连到 reactor legacy v1。Maven parent、`dependencyManagement` 和外部依赖均不形成内部边；重复 effective GA 或 missing module target 必须拒绝发布且 CURRENT 不动。

## Open questions and implementation risks

没有允许实现自行选择的架构分支。自动更新触发、其他构建系统、传递依赖和跨 Schema continuity 明确延后。实现若发现 Maven effective model 无法在本轮边界内确定，必须登记 Finding 并停止相应 Coverage，不得用字符串启发式通过。

## Acceptance scenarios

Verification Matrix V-001 至 V-013 全部满足且人工内容核对完成，才能接受本 Slice。每个 G0/G1/G2/G3a/G3b/G4 都必须有独立 Result，绑定 exact checkpoint、原始证据路径和人工 PASS；上一 Gate Result 未提交为 PASS，禁止修改下一 Gate 的产品代码。单元测试通过但没有 Source-off 报告或浏览器可核对结果不算完成。

## Findings

实现发现登记在本轮 [Findings](../findings/README.md)，并按[实现发现回写规则](../../../governance/implementation-feedback-policy.md)处置。

G2 已处置 `FINDING-003-009`，把 Citation Projector 从直接读取完整 Evidence Store 收窄为 trusted broker 物化的 Result-scoped disposable Store；`FINDING-003-010` 则把本机验证机制明确为 macOS Seatbelt capability boundary，区分应用输入、runtime/ancestor traversal、输出与拒绝目标。两项处置及 V-007 的实际执行已由 `ITER-003-RESULT-G2` 在 exact checkpoint 上联合裁决为 PASS；它们不授权任何 G3a 以后的外部执行。

G3a 已处置 `FINDING-003-011`、`FINDING-003-012` 与 `FINDING-003-013`：前者把新 authority chain 固定为 process-local `EVALUATION_ONLY` 路径，禁止自动提升为 live Response Control；第二项要求 V-008 把应用端口零计数与真实 OS operation audit/deny probes 分列，并闭合 bundled Python 最小 sibling runtime capability；第三项要求用 clean HEAD/tree 与带外 commit/PAGE digest 证明评测页来源，并按 exact scalar type 失败关闭。三项处置及 V-008 的实际执行已由 `ITER-003-RESULT-G3A` 在 exact checkpoint 上联合裁决为 PASS；它们不授予外部 strategy/model 资格、外部披露、V-009 或 G3b。

V-009 已处置 `FINDING-003-014`：保留 G3a offline authority 不变，以独立 model proposal strategy 作为 closed CE subject，并把 evaluator oracle 隔离到 standalone deterministic process；V-009 direct Adapter transport 只用于 qualification/comparison，不得冒充 G3b Model Egress Gateway 与 OS denial 证明。

首轮真实 V-009 又处置 `FINDING-003-015`：Prompt 未把自然语言 owner 名称约束为平台 uppercase enum，导致 `WM-CE-GAP-004` exact projection FAIL。修复只澄清 `STRUCTURE_VIEW` / `KNOWLEDGE_USE`，但必须升级 Strategy/Prompt/input-freeze identity，并从新 clean checkpoint 完整重跑 Conformance 与七 Case。

第二轮真实 V-009 处置 `FINDING-003-016`：owner 已正确，但 Prompt 没有逐字段声明 `need_assessment.status=KNOWLEDGE_GAP`，也没有明确 PARTIAL coverage 优先于 pagination completeness，导致同一 Case 错误输出 supported negative。修复只澄清该通用合同，不修改或泄露 suite/oracle；Strategy/Prompt/input-freeze 再次升级，并要求新 clean checkpoint 上完整重跑。

第三轮真实 V-009 已取得 7/7 PASS，但 baseline 调用前审计处置 `FINDING-003-017`：旧 Direct coverage 把 path union 当成 target-only required reads，无法表示 metamorphic fixture 的 A-old/B-new 移动 POM。修复以 union 继续限制 Source access，并按 revision 分别冻结 required POM closure；旧 ITER-002 string policy 保持兼容。该 baseline exact input 变化使第三轮 qualification 不可继承，必须再次完整资格化。

第四轮真实 V-009 同样取得 7/7 PASS，但 baseline 调用前审计处置 `FINDING-003-018`：Mature protocol 的 legacy `--sandbox read-only` 允许 checkout 外广泛只读，不能证明冻结的 exact-source allowlist。修复删除 legacy flag，改为 root deny、minimal runtime/exact workspace read、temp/network deny 的 Codex permission profile，并显式冻结 model、reasoning、Web/Apps/multi-agent config。该 baseline exact input 变化使第四轮 qualification 也不可继承，必须从新 clean checkpoint 再次完整资格化。

第五轮真实 V-009 仍取得 7/7 PASS，但运行器在 baseline 请求前处置 `FINDING-003-019`：文件隔离不能阻止 model-generated command 继承 operator 的 `ARK_API_KEY` 等环境变量。修复把 shell environment 固定为 inherit-none/no-login，只显式注入非秘密 PATH/locale/timezone，并要求 runner 删除不需要的 API credential。该输入变化使第五轮 qualification 不可继承，必须最后再完整资格化。

最终 V-009 baseline 首次正式 Mature preflight 处置 `FINDING-003-020`：当前 CLI/host 下 `:slash_tmp=deny` 不能证明物理 `/private/tmp` sibling 内容已拒绝。失败预检在任何 Mature 模型调用前阻断；控制树物理迁到系统 `$TMPDIR`，保持 runner/plan/profile/Prompt/workspace digest 不变，最终预检 7/7 PASS。

最终 Direct 55-run 分布处置 `FINDING-003-021`：15 SUCCESS、40 preserved FAILURE，其中 13 个 HTTP 429、2 个 Provider outcome unknown。V-011 不得择优成功、插值缺失 Direct 输出或静默过滤 Provider failure；Mature 55-run 完整质量对照仍按冻结规则参与更强者判断。
