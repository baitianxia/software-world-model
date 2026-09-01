---
id: FINDING-010-262
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, knowledge, ai, security, quality]
depends_on: [ITER-010-PDR-014, FINDING-010-260, FINDING-010-261, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/lightweight_engineering_agent.py, src/software_world_model/ai_infrastructure/lightweight_engineering_model.py, src/software_world_model/interface/lightweight_engineering_chat.py, src/software_world_model/interface/engineering_chat_session_runtime.py, src/software_world_model/interface/engineering_chat_session_artifact.py]
tests: [tests/test_lightweight_engineering_agent.py, tests/test_lightweight_engineering_model.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_chat_browser.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: adopt-same-agent-cognition-plus-source-tool-loop
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-262：三类认知工具可接入同一个轻量 Agent 而不转移 Source 与交付权威

## Observation

Phase B artifact 不需要新 Agent 或旧 Claim/Boundary 协议。Phase A 的 goal/plan/action/observation loop 增加
`SEARCH_COGNITION / TRAVERSE_RELATIONS / RETRIEVE_COGNITION_DETAIL` 后，可先取得入口、关系和行为，再用原有 Source search/read 补齐
可引用证据。模型只看到 Application 分配的数字 `cognition_index`；实体 ID、artifact 加载、exact binding、分页和工具执行仍由 Application
拥有。

Session 若不把 query projection 的 path/digest/snapshot/revision/tree 纳入 owner-private config，多个 Turn 虽可共享内存对象，却不能证明
它们使用同一份认知。因此 artifact config 增加 closed `@5`：完整继承 `@4` standing authority，只在 listener/credential/dispatch 前重算并
加载一个 capability artifact；无该字段的 `@4` 保持 same-Agent source-only 消融臂。

## Evidence

- 确定性集成 trajectory 为 `SEARCH_COGNITION → TRAVERSE_RELATIONS → SEARCH_SOURCE → READ_SOURCE → FINISH`，两次 cognition event
  绑定同一 snapshot digest，最终 ANSWER 仍使用 Source Citation 与 fresh Review/Delivery；
- cognition search/traverse/detail 使用有界 page、typed relation/direction/depth/cursor；不可用数字 index、revision drift 或 mode/artifact
  不一致均在 Application 失败关闭；
- `@5` loader 拒绝 capability source tree 漂移，`@4` loader 与 source-only mode 保持兼容；
- Agent、model boundary、Provider runtime、artifact Session、Browser、cognition 与 Source 的 55 项受影响测试通过；旧两处 prompt-heavy
  文件相对 `8131cae` 仍净增 `0/0`。

## Disposition

Engineering Conversation Contract 接受同 Agent 的 cognition-plus-source 工具循环和 `@5` exact artifact binding。该证据只关闭 Phase C 的本地
组合边界；`V-INTEGRATED-ALPHA-001` 仍必须用真实 Browser 完成三个异质问题、一个追问和 same-Agent 消融后才能 PASS。
