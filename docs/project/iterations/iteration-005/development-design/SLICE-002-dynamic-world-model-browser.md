---
id: ITER-005-SLICE-002
kind: development-slice
status: completed
authority: historical-development
owners: [engineering]
depends_on: [ITER-005-PROPOSAL, ITER-005-SLICE-001, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE, SYS-CONTRACT-KNOWLEDGE-PERSISTENCE, SYS-CONTRACT-APPLICATION-STRUCTURE-VIEW, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-ARCH-DEPLOYMENT, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-OPS-LOCAL-BROWSER, SYS-QUALITY-SECURITY, SYS-QUALITY-ACCEPTANCE]
code: [src/software_world_model/interface]
tests: [tests]
iteration: ITER-005
coding_input: false
---

# SLICE-002：正式本机 World Model Web 问答入口

## Status and dependencies

SLICE-001 Result 已由用户接受；用户于 `2026-08-11T19:32:39+08:00` 授权本 Slice 编码。已冻结的新仓库 Catalog、
Answer/Prompt/Strategy/Provider subject 与有效资格见 Manifest。`run-006` 的浏览器验收 PASS、comparison FAIL 原样保留；
修复后的 `run-007` 已取得绑定新 suite 的三条 exact disclosure 授权，并完成三路 population、independent comparison 与
真实浏览器验收，结果全部 PASS。用户于 `2026-08-12T08:44:55+08:00` 接受本 Slice 与 ITER-005；本文件转为历史设计，
Production Activation 未执行。

## Current vs expected behavior

开发前的通用 HTTP adapter 已存在，但可执行 trusted launcher 位于 iteration-specific validation，并把 product commit、
工件根、三个 dataset 和 mall/fixture 展示固定在代码中。现在 `src/software_world_model/interface` 已提供稳定产品启动入口
`python -m software_world_model.interface.world_model_http`：它从已验证的动态 Read Set Catalog 装配合格 Bundle，显示
Workspace、exact revision、Snapshot、Profile/Coverage 和 Bundle identity，并通过同一隔离 Answer/Gateway/Projector 链回答。

## System contracts and invariants

1. Browser question request 只接受 `request_id + read_set_id + question`；仓库路径、Source、Update command、Snapshot
   override、authority DB 和 Evidence payload 不得进入请求或 Answer capability。
2. launcher 只装配已验签、queryable、Profile 兼容的 exact Read Set；固定项目名、commit、dataset ID、问题文本、模块名或
   拓扑不能成为隐藏分支。
3. 提问前后 CURRENT、Update Attempt、Bundle Receipt 和 Source Operation 计数不变；缺 Bundle 或知识只返回对应
   Limitation/Gap，不能临时更新、回源或切换 Direct。
4. Answer 只读 package + chosen no-payload Bundle；Gateway、Broker、Projector 沿用 `SYS-ARCH-DEPLOYMENT` 的文件与网络
   边界。动态 Catalog 不放宽任何 Answer capability。Answer/View/Projector 看不到权威数据库；Result 密封后，trusted
   Citation Broker 仍在独立受控边界通过窄 Knowledge Evidence Port 读取 exact allowlist observation 并生成 disposable
   Citation Store。若 broker 的 authority access 被全局关闭，本次只能验证无 Citation 的 View，不能声称 Citation 可用。
5. 页面只宣称当前 Profile 的 reactor child membership、POM 本地直接内部依赖与 exact Snapshot diff，不宣称 plugin、
   property、parent/effective/transitive/runtime 关系。
6. 若 Answer package、Prompt、Strategy、Provider config 或 isolation workload 改变，旧资格失效并完整重做；不变也要对新
   仓库执行 held-out Product Validation。
7. 每个实际分派的问题最多 1 次 Provider call、0 hidden retry；资格/commit/tree/Catalog/Bundle/OS preflight 在监听前重验。
   pre-dispatch validation failure 为 0 call，不能通过改写问题、重试或 Direct fallback 变成成功。
8. 每个动态 Workspace 的 preflight 必须先在 sandbox 外证明 actual repository POM/`.git`、authority DB 与 Evidence Store
   确实可达，再证明 Answer workload 对这些 exact canonical targets、其他角色输出、DNS/公网/Source remote 的访问均由
   OS capability policy 拒绝。Projector 继续拒绝 authority DB 与全部网络；Broker 的窄读取不能变成 Answer capability。
9. 正式入口的启动参数只接收 database/catalog/bundle roots、loopback host/port、exact evaluation grant/qualification
   references 和资源限制；本 Slice 必须拒绝 Production Activation reference。不得内置 iteration ID、项目名、accepted
   `var/` 路径或凭据；无认证时非 loopback host 必须拒绝启动。

## Interfaces and affected code

- Browser Runner 从动态 Catalog 列举数据集并验证 Read Set/Bundle Receipt；
- 在 `src/software_world_model/interface` 建立产品自有的通用 trusted launcher/runner public boundary；它只依赖 sealed Catalog、
  public Bundle/Answer/Gateway/Projector ports，不导入 ITER-003/004 validation 私有函数；
- 提供稳定 `software_world_model.interface.world_model_http` 启动模块，复用现有 `/`、`/health`、
  `/v1/world-model/datasets`、`/v1/world-model/questions` 与独立 Citation GET；
- 新的 `validation/structure_world_model_iteration_005` 只验证该 public boundary，不修改或继承历史 ITER-003/004 验收实现；
- 浏览器支持刷新动态数据集、选择 exact single/ordered Read Set，并诚实展示支持范围；
- supported、Entity Resolution Limitation、View Limitation、Knowledge Gap 和 fail-closed error 使用可理解的状态投影；
- 问答写路径保持不存在；工作区登记和更新继续走独立管理 CLI。

具体模块名由局部实现决定，但 launcher 的 Owner 与代码边界已冻结在产品 `src/`；历史 validation 代码保持只读证据，
不能继续充当产品运行主体。

编码前固定 product launcher 的 public contract，以及 Answer、Gateway、Broker、Projector、worker、sandbox profile 的
既有 exact commit/tree/file digests，并逐项裁决历史 Conformance/Qualification 的继承范围。新增 launcher 尚无实现 bytes，
按 `FINDING-005-002` 必须在实现完成后、任何监听或真实分派前密封其 exact package/tree/file digests；这不是允许开放
qualification subject 或延后安全预检。

## Compatibility, data and security boundaries

ITER-004 三个固定 dataset 可作为历史兼容输入，但不能成为新验证 Oracle。旧 `/v1/browser/chat` 仍是
`DIRECT_INVESTIGATION`，不得改名或作为 fallback。服务继续只绑定 `127.0.0.1`、显示 `WORLD_MODEL / EVALUATION_ONLY`，
不产生 Production Activation。

## Open questions and implementation risks

- 当前 ProductQuestionInterpreter 使用封闭词法映射；若新仓库支持题在 Provider 前失败，应先形成 Finding 并判断是通用
  Requirement/Entity Resolution 缺陷还是题目超出 Profile，不能按项目加关键词补丁。
- accepted product package 与动态 Catalog 的身份绑定必须可重建；复用历史 package 不能复用历史 mall Product Result 代替
  新仓库验证。
- 动态数据集刷新不能让页面中已选或正在执行的 Read Set 随 CURRENT 漂移。

## Acceptance scenarios

1. 页面从动态 Catalog 显示一个从未写入 launcher 的多模块仓库及 R1、R2、R1→R2 exact Read Sets。
2. Source/工作树与权威 DB 对 Answer/View 不可见时，模块清单、直接内部依赖、路径、负向路径和 diff 支持题得到正确
   可读答案；trusted Broker 只在 Result seal 后通过窄 Knowledge Port 读取 Citation allowlist。
3. 同名模块返回受控 0/N candidate Limitation；设计动机、plugin/parent/effective dependency 等覆盖外问题返回 Gap。
4. 每个成功结果显示 original question、read binding、Profile/modality、Coverage、Claims、十阶段 Authority 和可独立打开的
   Citation；Citation 不回流 Answer。
5. actual Workspace repo/`.git`/authority DB/Evidence Store 的动态 OS deny probes 与正常 workload audit 均通过；不能复用
   mall 固定路径结果代替。
6. 提问前后 Update/CURRENT/Source counters 完全不变；每问最多 1 call/0 hidden retry；篡改 read set、Bundle、Result、
   Citation 或资格全部失败关闭。
7. 在 World Model 结果前冻结的 independent evaluator、controlled Direct 和成熟 Source Agent 对照上，全部失败保留，逐题
   重大错误为 0且完整性不低于两条可评 baseline 中较强者；任何筛选、插值或逐题退步阻断接受。
8. focused、full regression、docs check 与真实浏览器人工核对全部通过；Production Activation `NOT EXECUTED`。

9. 用户只按 `SYS-OPS-LOCAL-BROWSER` 记录的产品命令启动服务，在真实浏览器选择 Read Set，人工提交至少一条 supported
   question 与一条 Gap question；不运行 `validation.*` 模块也能完成整个体验。

## Verification outcome

[Run-007 Live Result](../results/slice-002-run-007-live.md) 已实际闭合上述场景：Direct、Mature 与 World Model 各 9/9，
independent comparison `sha256:e7d16fa4…` 为 PASS；真实产品入口完成 supported、Gap、Citation、第三张动态 Read Set 选择和
空 console 核对；51/51 focused、13/13 protected staged Answer、801/801 full regression 与 docs check PASS。所有请求均为
`EVALUATION_ONLY`，每个浏览器问题 Provider/Network/Retry=`1/1/0`，服务已停止，Production Activation `NOT_EXECUTED`。

这些证据当时使本 Slice 达到等待用户验收状态；用户随后通过独立消息接受本 Slice 与 ITER-005，最终裁决不由
Development Design 自动产生。

## Implemented finding and qualification impact

`FINDING-005-003` 证明 inherited Answer 对显式未知 artifact 不能形成 0-candidate Limitation。实现已用通用的显式
artifact token、exact Snapshot Entity Candidates 与受控 Application Limitation 闭合 0/N 行为，没有增加项目分支。
因此 inherited Answer package 只能作为变更前基线，不能再作为本 Slice 的 active qualified package。Prompt、Strategy、
Provider subject 未变；新的 Answer candidate bytes 必须在任何监听或外部分派前与 launcher 一起密封，并完整重做 role/OS
preflight、Product Validation 与 V-009。未得到新 PASS 证据时正式命令必须失败关闭。

`FINDING-005-004` 进一步把 inherited Gateway freeze 中的历史 permission 降级为 capability baseline：active Gateway
entrypoint 必须先验证由本次 exact evaluation grant 派生的 session authorization receipt，并在 summary 中绑定当前 grant 与
disclosure digest。历史 permission 不能授权 ITER-005 问题。

按 `FINDING-005-005`，首次受控 Product Validation 使用 status=`CANDIDATE` 的 evaluation grant；grant 只绑定 pre-run
deterministic qualification、held-out suite/evaluator、exact provenance、Provider qualification 与当前 disclosure。Product
Result 和 baseline comparison 是该运行的输出，不能作为候选首次启动的循环前置条件；页面也不得提前称其为 accepted。

`FINDING-005-006` 要求 grant 对 qualification/suite 使用 schema-bound document digest 的完整正向解析验证，且 deterministic
qualification 不只在当前源码树运行测试，还要在最终 protected stage 的 exact Answer package 上重跑产品测试并确认 stage
manifest 未因测试漂移。未授权短路测试或 current-source PASS 都不能单独替代这两项证据。

`FINDING-005-007` 已用全新 randomized suite 和全部问题的 deterministic product probe 修正 ambiguous short-name 负向路径题。
`FINDING-005-008` 进一步把 V-009 输入升级为 `SWM-WORLD-MODEL-HELD-OUT-SUITE@2`：内嵌 exact POM source closure、
controlled Direct/Codex 协议与 baseline-first 顺序。comparison terminal 分开记录 external task 和 Provider call；成熟 Codex
内部 Provider call 不可观测，必须为 `null`，不能伪造 `1`。controller 在任何外部 task 前要求 suite-bound 用户授权，首个
World Model 问题前还要匹配 loopback health 的 exact suite/commit/tree。

`FINDING-005-009` 依据 `run-005` 真实浏览器证据约束三列动态 Read Set grid 使用可收缩 track 并允许长 identity 断行；
`run-006` 已在普通语义 click 下证明第三张卡可选择。`FINDING-005-010` 依据 `run-005/006` 的 Direct truncation 与 malformed
JSON terminal，把 controlled Direct response envelope 升为 4096 output token 和严格 JSON-only `@2` contract。该协议作为
held-out suite 的显式字段由 runner/evaluator 双向验证；仍然是每题一次 Provider call、0 retry，所有历史失败保留。

## Findings

链接本轮的 [Findings](../findings/README.md) 与[实现发现回写规则](../../../governance/implementation-feedback-policy.md)。
SLICE-001 与本 Slice 均已接受；`run-006` 与 `run-007` 的 exact 外部分派授权均已消费且不能复用于其他 suite。本设计已
转为历史输入，不再提供编码权限；Production Activation 始终不在授权范围。
