---
id: SYS-OPS-LOCAL-BROWSER
kind: system-operations
status: current
authority: operational
owners: [operations, interface]
depends_on: [SYS-ARCH-DEPLOYMENT, SYS-QUALITY-SECURITY]
code: [src/software_world_model/interface/http_api.py, src/software_world_model/interface/browser_ui.py]
tests: [tests/test_browser_chat_interface.py]
---

# 本机浏览器体验

浏览器入口提供本地 Git 项目连接、版本选择、聊天任务、上下文追问和结果展示。它复用正式知识、能力资格和响应审核路径，不是旁路 Demo。

当前服务没有认证，必须绑定 `127.0.0.1`。启动时需要显式加载仍有效且与当前实现匹配的 Provider Conformance、Capability Qualification、Product Validation 和本机 Activation 记录；任一证明缺失、过期或漂移都停止服务或拒绝模型路径。

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
