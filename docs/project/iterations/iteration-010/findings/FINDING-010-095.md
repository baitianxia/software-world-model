---
id: FINDING-010-095
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, interface, security, quality, project]
depends_on: [FINDING-010-094]
code: [pyproject.toml, src/software_world_model/application_services/engineering_conversation.py, src/software_world_model/interface/engineering_chat_browser.py, src/software_world_model/interface/engineering_chat_browser_ui.py, src/software_world_model/interface/engineering_chat_alpha_cli.py]
tests: [tests/test_engineering_conversation.py, tests/test_engineering_chat_browser.py, tests/test_engineering_chat_alpha_cli.py, tests/test_engineering_qa_browser.py, tests/test_engineering_qa_alpha_cli.py]
iteration: ITER-010
classification: verification
scope: systemic
disposition: chat-access-local-candidate-evidence
target: ITER-010-VERIFICATION
---

# FINDING-010-095：真实 Chat Access 状态可与 Provider 资格分开实现和验证

## Observation

PDR-004 之后的实现核对确认：旧 `engineering_qa_browser` 即使持续接受多题，也只有逐题 Request/Result 和覆盖式结果区；直接为它增加消息气泡或改名会继续把兼容单轮协议误标成 Chat。另一方面，首个 Access 检查点不需要先接入 Provider、World Model 或 Source。Application 可以真实创建 server-owned Conversation、不可变 Revision、Context、Message 和 Turn；Provider 未配置时仍可把当前 Turn 以明确失败密封，并保持 Conversation `ACTIVE`。

这使“页面能操作”和“工程 Agent 已实现/答案质量通过”成为可机械区分的状态，而不是 UI 文案约定。新 Conversation 从空 Context 开始；失败 Turn 的 Provider dispatch/retry 均为 0，且没有 Evidence/Answer/Review/Delivery authorization 可被误投影成工程答案。

## Evidence

- `engineering_conversation.py` 新增进程内 Application authority：服务端签发 Conversation/Turn/Message/Result identity，保留每个 Conversation Revision，并对并发旧 revision 失败关闭；该 Access service 明确拒绝 `Provider READY` binding。
- `engineering_chat_browser.py` 使用独立路由和产品 identity，固定 exact `127.0.0.1:8765` Host、same-origin `application/json`、unique-key JSON、body/message 上限和无认证 loopback 边界；页面显示完整消息历史、“新对话”、exact 工程 revision、Provider 状态和“质量未验收 / 非生产”。
- `engineering_chat_alpha_cli.py` 提供无运行参数的 `swm-engineering-chat`，listener 前要求产品与 `mall@0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` 均为 clean exact Git worktree；它不装载 credential、Provider adapter、World Model/Source payload，也不读取 `src/main/resources`。
- 定向命令
  `PYTHONPATH=src:. python3 -m unittest tests.test_engineering_conversation tests.test_engineering_chat_browser tests.test_engineering_chat_alpha_cli tests.test_engineering_qa_browser tests.test_engineering_qa_alpha_cli -v`
  实际得到 `35/35 PASS`；其中新 Access 为 `17/17 PASS`，既有 QA 兼容面为 `18/18 PASS`。新增 Browser JavaScript 的 `node --check`、四个新 Python 模块 `py_compile` 和 `git diff --check` 均 PASS。
- 本证据没有启动 listener、没有使用浏览器、没有调用 Provider/model、没有披露源码，Production Activation 为 `NOT_EXECUTED`。

## Decision and disposition

- 新实现状态记为 `CHAT_ACCESS_LOCAL_CANDIDATE`；Conversation/Turn/Context access scaffold 已实现，但主工程 Agent loop、逐轮 Evidence/Answer/fresh Review、World Model/Source 工具和 Provider route 仍为 `NOT_IMPLEMENTED / NOT_QUALIFIED`。
- `V-ALPHA-ACCESS-001` 继续为 `NOT-RUN / blocking`。单元/WSGI 测试和静态页面不能代替 product freeze 后的真实 fixed-command listener、普通用户 Turn 提交与浏览器交付。
- 后续 exact live/browser grant 只能验证冻结后的 Access 候选；不能由本 Finding 推导 `V-CHAT-001`、`V-CHAT-QUALITY-001`、`V-CHAT-XD-001`、Provider 可用或 Production PASS。
- 旧 `swm-engineering-qa` 保留为 `ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3` 兼容入口；新的 `swm-engineering-chat` 才是 PDR-004 access 入口，避免静默改变旧运行证据的协议身份。
