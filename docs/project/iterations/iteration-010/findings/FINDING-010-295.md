---
id: FINDING-010-295
kind: implementation-finding
status: open
authority: implementation-evidence
owners: [project, engineering, quality]
depends_on: [ITER-010-EXECUTION-PLAN-CURRENT, FINDING-010-293, ITER-010-PDR-008]
code: [src/software_world_model/interface/engineering_chat_alpha_cli.py, src/software_world_model/interface/engineering_chat_session_artifact.py, src/software_world_model/interface/engineering_chat_session_runtime.py]
tests: [tests/test_engineering_chat_alpha_cli.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_chat_browser.py]
iteration: ITER-010
classification: unclassified
disposition: PENDING-ROUTE-0-RUNTIME-CLOSURE
target: PENDING-ROUTE-0-RUNTIME-CLOSURE
scope: systemic
---

# FINDING-010-295：Route-0 的可体验闭环仍被入口和运行准备阻断

## Observation

本次 Agent 规划修复已经完成，但当前任务的用户可见闭环仍未形成。无参数浏览器启动器构造的是 Access-only 服务，没有主 Agent 执行器；真正的世界模型 + 精确版本源码 + Provider Agent 只在 `--session-config` 分支中组合。该分支在启动准备阶段又无条件加载 Ark 和 DeepSeek 的 Conformance、路由、准入与两个运行时，即使 Ark 可用也要求 fallback 工件齐全。

## Evidence

- `engineering_chat_alpha_cli.py` 的无参数路径调用 `prepare_engineering_chat_access()`，其 `InMemoryEngineeringConversationService` 未绑定 `turn_executor`。
- `engineering_chat_session_artifact.py` 在构造 Session runtime 前无条件读取两个 Provider route 和两个 Conformance；`engineering_chat_session_runtime.py` 的签名也要求两个已构造的 Provider runtime。
- 本轮可生成 exact mall 的 capability-cognition 工件，但当前工作树没有可用的、未过期的 Session artifact/standing authority 组合；旧运行目录中的配置属于历史收据，不能直接冒充当前候选。
- 现有 Chat/Artifact 测试主要使用 fake executor、临时工件和零 dispatch 组合验证，不能证明真实浏览器 listener 到主 Agent 的闭环。

## Next action

只在 Route-0 内继续：把默认 loopback 入口接到当前有效的 artifact Agent runtime，并让 fallback runtime 在首选配置被可信判定为不可用时才准备；随后用一个真实问题、追问、新问题和失败后继续服务的浏览器运行记录证明世界模型、Agent、源码、Citation 和 fresh Reviewer 同一路由。不得通过伪造过期 authority、静态答案、测试 fake 或额外答案协议关闭本 finding。
