---
id: FINDING-010-296
kind: implementation-finding
status: dispositioned
authority: implementation-evidence
owners: [project, engineering, quality]
depends_on: [FINDING-010-295, ITER-010-EXECUTION-PLAN-CURRENT]
code: [src/software_world_model/application_services/conversational_engineering_routing.py, src/software_world_model/interface/engineering_chat_provider_launcher.py, src/software_world_model/interface/engineering_chat_session_runtime.py, src/software_world_model/interface/lightweight_engineering_chat.py]
tests: [tests/test_conversational_engineering_routing.py]
iteration: ITER-010
classification: local-implementation
disposition: code-and-tests
target: src/software_world_model/application_services/conversational_engineering_routing.py
scope: systemic
---

# FINDING-010-296：首选路径可以先独立形成实验候选

## Observation

Route-0 的运行时组合把“备用路径已构造”误当成“首选路径可以运行”的必要条件。这样在首选路径成功时也会提前加载和构造备用路径，阻塞首选路径的方向体验，并把两条路径的配置问题混入同一启动失败。

## Evidence

- `EngineeringProviderRoutePlan`、Provider attempt factory、Launcher 和 Session runtime 过去都强制要求两条 route。
- Router 只有在首选执行失败且收到可信不可用判定后才会创建备用 attempt；首选成功时不会创建备用 attempt。
- 新增 preferred-only route composition：只保留首选 route，首选成功时不创建备用 authority 或 attempt；首选失败时保持失败关闭，不伪造备用模型。
- 定向 `tests.test_conversational_engineering_routing`：22/22 PASS。

## Decision / Disposition

这是 Route-0 的局部通用实现修复，不改变架构语义、答案协议或提供方透明策略。保留原双 route 兼容；preferred-only 候选仅用于先验证首选 Agent 纵切，不能宣称已具备备用路径。后续把 artifact Session loader 接入该候选时，只有可信不可用判定才允许加载当前有效的备用配置；加载失败必须失败关闭。

## Verification

- `python3 -m compileall -q src`：通过。
- `tests.test_conversational_engineering_routing`：21/21 PASS。
- Provider launcher、artifact session、provider runtime、Chat CLI 定向回归：44/44 PASS。
- 真实 Ark 现场验证仍返回 HTTP 400 `InvalidSubscription`；本次未调用 DeepSeek，尚未形成浏览器 Agent 闭环，因此 FINDING-010-295 仍保持 open。
