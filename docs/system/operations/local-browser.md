---
id: SYS-OPS-LOCAL-BROWSER
kind: system-operations
status: current
authority: operational
owners: [operations, interface]
depends_on: [SYS-ARCH-DEPLOYMENT, SYS-ADR-014, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-QUALITY-SECURITY]
code: [src/software_world_model/interface/http_api.py, src/software_world_model/interface/browser_ui.py]
tests: [tests/test_browser_chat_interface.py]
---

# 本机浏览器体验

浏览器入口提供本地 Git 项目连接、版本选择、独立知识更新、模式选择、聊天任务、上下文追问和结果展示。

- `WORLD_MODEL` 显示 source revision、exact Snapshot、Read Bundle digest、View、Profile/关系 modality、Coverage、View Limitation/Knowledge Gap、Fact 与 Evidence 引用；问题请求只读不含 Evidence payload 的 exact Snapshot Read Bundle，不得触发更新或访问 Source、权威数据库或 Evidence Store。点击引用由浏览器另行访问密封结果后的 Citation Projector，不把正文发送回问答进程。
- `DIRECT_INVESTIGATION` 显示 exact Source Target 与 Evidence Packet；它按 ADR-013 调查源码，但不能标成世界模型回答。

两种模式不得静默互相兜底。人工更新是独立操作：即使从未提问也能构建新 Snapshot；计划或来源事件自动更新需要独立启用和运维证明。

在 World Model 路径完成实现和独立 Product Gate 之前，现有 Evidence-first 浏览器只能标记为 `DIRECT_INVESTIGATION`；`WORLD_MODEL` 必须保持不可用，不能仅通过改页面文案提前启用。现有单进程 `http_api` 启动方式不是合格的 `WORLD_MODEL` launcher；新 launcher 必须建立 answer worker / Citation Projector 的独立文件与网络能力边界，并让真实模型调用只能经过 exact Model Egress Gateway。

当前服务没有认证，必须绑定 `127.0.0.1`。启用任何模型生成路径时需要显式加载仍有效且与当前实现、模式匹配的 Provider Conformance、Capability Qualification、Product Validation 和本机 Activation；任一证明缺失、过期或漂移都拒绝该模型路径。确定性 Snapshot/View 读取可独立运行，但不能冒充已经通过模型回答 Gate。

Capability Evaluation 和 Product Validation 可以在显式 `EVALUATION_ONLY` browser sink 中检查同一页面投影，但页面必须持续显示不可关闭的评测标识，禁止生产 Delivery、用户会话复用和正式 Activation；输出只进入隔离验证目录。该例外只用于取得资格和产品证据，不能作为已启用本机模型路径交付。

```bash
PYTHONPATH=src python3 -m software_world_model.interface.http_api \
  --database var/browser-experience/swm.sqlite3 \
  --host 127.0.0.1 \
  --port 8765 \
  --enable-activated-model \
  --conformance-result var/conformance/<current-result>.json \
  --activation-environment local-browser
```

命令中的证明与 Activation 必须匹配启动时的 exact 实现、配置、模型和环境；示例占位符不是可加载资格。历史本机体验、测试通过或日期尚未到期都不能替代启动时的完整重验证，也不能推导生产启用。
