---
id: SYS-OPS-LOCAL-BROWSER
kind: system-operations
status: current
authority: operational
owners: [operations, interface]
depends_on: [SYS-ARCH-DEPLOYMENT, SYS-ADR-014, SYS-ADR-015, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-QUALITY-SECURITY]
code: [src/software_world_model/interface/http_api.py, src/software_world_model/interface/browser_ui.py, src/software_world_model/interface/world_model_browser.py, src/software_world_model/interface/world_model_browser_ui.py, src/software_world_model/interface/world_model_http.py, src/software_world_model/interface/world_model_runtime.py, src/software_world_model/interface/world_model_product.py]
tests: [tests/test_browser_chat_interface.py, tests/test_world_model_browser.py, tests/test_iteration_004_interactive_browser.py, tests/test_world_model_http.py, tests/test_world_model_evaluation_grant.py, tests/test_world_model_gateway_authorization.py, tests/test_iteration_007_slice1_freeze.py, tests/test_iteration_008_slice1_freeze.py, tests/test_iteration_008_slice1_live_authorize.py, tests/test_world_model_product.py]
---

# 本机浏览器体验

本机有两个不可混淆的浏览器入口：Evidence-first `DIRECT_INVESTIGATION` 用于源码调查；独立的
`WORLD_MODEL / EVALUATION_ONLY` 入口用于体验 Snapshot-first Maven Structure 或已授权候选 Java Static Call Behavior
World Model。两者不能
静默互相兜底。

- `WORLD_MODEL` 显示 source revision、exact Snapshot、Read Bundle digest、View、Profile/关系 modality、Coverage、View Limitation/Knowledge Gap、Fact 与 Evidence 引用；问题请求只读不含 Evidence payload 的 exact Snapshot Read Bundle，不得触发更新或访问 Source、权威数据库或 Evidence Store。点击引用由浏览器另行访问密封结果后的 Citation Projector，不把正文发送回问答进程。
- `DIRECT_INVESTIGATION` 显示 exact Source Target 与 Evidence Packet；它按 ADR-013 调查源码，但不能标成世界模型回答。

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

当前服务没有认证，必须精确绑定 `127.0.0.1`。启用任何非 `EVALUATION_ONLY` 的模型生成路径时，需要显式加载仍有效且与当前实现、模式匹配的 Provider Conformance、Capability Qualification、Product Validation 和本机 Activation；任一证明缺失、过期或漂移都拒绝该路径。首次 `EVALUATION_ONLY` 候选验证不循环要求尚未产生的 Product Result，但必须绑定 exact Conformance、Provider Qualification、候选 package/launcher、确定性资格和预先密封的 Product suite/evaluator；页面保持 `CANDIDATE`，直到运行后 Product Validation 与人工接受完成。它不得伪造或推导 Activation。确定性 Snapshot/View 读取可独立运行，但不能冒充已经通过模型回答 Gate。

Capability Evaluation、Product Validation 和本机交互体验只允许在显式 `EVALUATION_ONLY` browser sink 中运行。
页面必须持续显示不可关闭的评测标识，禁止生产 Delivery、用户会话复用和正式 Activation；输出只进入隔离验证目录。
自由文本只在用户选择的 exact、单一 Profile Read Set 与 Coverage 内求解：覆盖外问题应返回 Knowledge Gap；无法形成
已验证 Result 时必须显示失败关闭，不能切换 Direct 或回源。

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
`SWM-WORLD-MODEL-EVALUATION-GRANT@2`，且包含用户对“原问题 + no-payload published Structure”这一精确披露边界的本次
授权；`NOT_AUTHORIZED` grant 会在创建 session、Provider socket 和 HTTP listener 前拒绝。授权之后，launcher 仍会在监听前
重验全部 digest、当前 session Gateway authorization receipt、实际 Workspace/authority deny targets 和 OS isolation
preflight。服务没有认证，固定只绑定 `127.0.0.1`。

候选冻结在签发 authorized browser grant 前，必须用 runtime exact `-I -S -B` flags 和 role package root 导入真实 Answer/Gateway/
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
