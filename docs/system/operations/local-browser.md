---
id: SYS-OPS-LOCAL-BROWSER
kind: system-operations
status: current
authority: operational
owners: [operations, interface]
depends_on: [SYS-ARCH-DEPLOYMENT, SYS-ADR-014, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-QUALITY-SECURITY]
code: [src/software_world_model/interface/http_api.py, src/software_world_model/interface/browser_ui.py, src/software_world_model/interface/world_model_browser.py, src/software_world_model/interface/world_model_browser_ui.py, validation/structure_world_model_iteration_004/interactive_browser.py]
tests: [tests/test_browser_chat_interface.py, tests/test_world_model_browser.py, tests/test_iteration_004_interactive_browser.py]
---

# 本机浏览器体验

本机有两个不可混淆的浏览器入口：Evidence-first `DIRECT_INVESTIGATION` 用于源码调查；独立的
`WORLD_MODEL / EVALUATION_ONLY` 入口用于体验已验收的 Snapshot-first Maven Structure World Model。两者不能
静默互相兜底。

- `WORLD_MODEL` 显示 source revision、exact Snapshot、Read Bundle digest、View、Profile/关系 modality、Coverage、View Limitation/Knowledge Gap、Fact 与 Evidence 引用；问题请求只读不含 Evidence payload 的 exact Snapshot Read Bundle，不得触发更新或访问 Source、权威数据库或 Evidence Store。点击引用由浏览器另行访问密封结果后的 Citation Projector，不把正文发送回问答进程。
- `DIRECT_INVESTIGATION` 显示 exact Source Target 与 Evidence Packet；它按 ADR-013 调查源码，但不能标成世界模型回答。

人工更新是独立操作：即使从未提问也能构建新 Snapshot；计划或来源事件自动更新需要独立启用和运维证明。

现有单进程 `http_api` 仍只属于 `DIRECT_INVESTIGATION`，不是合格的 `WORLD_MODEL` launcher。World Model
入口由独立 WSGI adapter 和 trusted evaluation launcher 提供：启动时固定 accepted ITER-003 product 与三个
allowlisted Read Set，重跑 OS isolation preflight；每个问题创建新的 `0700` run directory，只能通过 exact Model
Egress Gateway 调用 Provider 一次且不重试。Answer 进程无 Source、Repository、Evidence payload、Oracle 或 baseline；
Citation 由浏览器按 request/result 另行 GET，并由无网络 Projector 的密封 Projection 重新验签。

当前服务没有认证，必须绑定 `127.0.0.1`。启用任何非 `EVALUATION_ONLY` 的模型生成路径时，需要显式加载仍有效且与当前实现、模式匹配的 Provider Conformance、Capability Qualification、Product Validation 和本机 Activation；任一证明缺失、过期或漂移都拒绝该路径。`EVALUATION_ONLY` launcher 仍必须绑定 exact accepted Conformance、Qualification、Product Validation 和隔离实现，但不得伪造或推导 Activation。确定性 Snapshot/View 读取可独立运行，但不能冒充已经通过模型回答 Gate。

Capability Evaluation、Product Validation 和本机交互体验只允许在显式 `EVALUATION_ONLY` browser sink 中运行。
页面必须持续显示不可关闭的评测标识，禁止生产 Delivery、用户会话复用和正式 Activation；输出只进入隔离验证目录。
自由文本只在用户选择的 exact Maven Structure Read Set 与 Coverage 内求解：覆盖外问题应返回 Knowledge Gap；无法形成
已验证 Result 时必须显示失败关闭，不能切换 Direct 或回源。

启动已验收的本机 World Model 体验：

```bash
PYTHONPATH=src:. python3 -m validation.structure_world_model_iteration_004.interactive_browser \
  --host 127.0.0.1 \
  --port 55121
```

launcher 默认从 accepted ITER-003 本机工件根读取 package、Bundles 与 Gateway inputs；工件缺失或 digest/stage 漂移时
启动失败，不会下载、重建或降级。服务没有认证，固定只绑定 `127.0.0.1`。

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
