---
id: FINDING-010-097
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, interface, security, quality, project]
depends_on: [FINDING-010-093, FINDING-010-094, SYS-ADR-018, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/application_services/engineering_conversation.py, src/software_world_model/application_services/__init__.py, src/software_world_model/interface/engineering_chat_browser.py, src/software_world_model/interface/engineering_chat_browser_ui.py]
tests: [tests/test_conversational_engineering_agent.py, tests/test_engineering_conversation.py, tests/test_engineering_chat_browser.py, tests/test_engineering_chat_alpha_cli.py, tests/test_engineering_qa_browser.py, tests/test_engineering_qa_alpha_cli.py]
iteration: ITER-010
classification: verification
scope: systemic
disposition: agent-executor-local-candidate-evidence
target: ITER-010-VERIFICATION
---

# FINDING-010-097：主工程 Agent 控制循环已形成本地确定性纵切

## Observation

Access browser PASS 之后，下一最早缺口不是继续扩张页面，而是 Application 仍只能在 Provider 未配置时密封失败 Turn；没有受控执行器把
同一 Conversation 的 Agent Work State、工具 Observation、Evidence Package、Draft、fresh Review 和 Delivery Authorization 串成一个
可失败关闭的 Turn。实现过程中还确认，Work State 若只在单个 Turn 内从 revision 1 重建，就不能承担 PDR-004 要求的多轮目标、纠正和
被取代结论连续性；因此同一 Conversation 必须保持稳定 Work State identity，并跨 Turn 递增 revision。

## Evidence

- `conversational_engineering_agent.py` 新增 Application-owned bounded executor。主 Agent 只提交完整 Work State revision、closed-catalog
  World Model/Source action 或 Draft；实际工具、Reviewer 和 Response Control 均为受信 typed port，Agent 本身没有 filesystem、Source、
  shell、network、credential、write 或 Production Activation 端口。
- 同一 Conversation 的 Work State identity 跨 Turn 保持稳定，revision/digest 严格续接；用户纠正单调追加，先前 reviewed conclusion 只能
  被显式标记 superseded，消息和旧 Result 不被改写。并行提交同一 Conversation 在执行中的第二个 Turn 会在调用执行器前失败关闭。
- Tool Result 必须绑定 exact request；Package 携带并密封完整 `support`/`boundary` Observation 与 digest，肯定 Claim 只能引用 support，
  Limitation 绑定 boundary。Reviewer 读取当前 Turn/Context/完整 Package/Draft；同包 Finding 回同一 Agent 重写，`requires_evidence` Finding
  在取得新 Observation 前不能再次提交 Draft，新 Observation 必然形成 successor Package 和 fresh Review。
- 只有 exact Work State/Package/Answer/approved Review 全部匹配的 Response Control authorization 可以交付。伪造 Tool Result 或 Delivery
  authorization、无进展、步骤/工具/Review 熔断和 malformed executor outcome 都只关闭当前 Turn；Conversation、既有 reviewed Context 和
  已密封 Work State 保持可继续。
- Browser projection 现在能区分 `SUCCEEDED` 与 `FAILED`，投影 Work State revision/digest、Package/Answer/Review/Delivery references 和
 实际调用计数；既有 Access-only launcher 与旧 Engineering QA identity 未被改名或接入外部执行。
- 定向命令
  `PYTHONPATH=src:. python3 -m unittest tests.test_conversational_engineering_agent tests.test_engineering_conversation tests.test_engineering_chat_browser tests.test_engineering_chat_alpha_cli tests.test_engineering_qa_browser tests.test_engineering_qa_alpha_cli -v`
  实际得到 `48/48 PASS`；四个改动模块 `py_compile`、Browser JavaScript `node --check` 与 `git diff --check` 均 PASS。
- 本次验证全部使用确定性 fake ports；没有启动 listener/browser，没有读取或披露 `mall` 源码或 `src/main/resources`，没有调用
  Provider/model，也没有执行 Production Activation。测试中的 model-call reference/count 是本地协议模拟，不是外部 dispatch 证据。

## Decision and disposition

- 当前实现状态更新为 `AGENT_EXECUTOR_LOCAL_CANDIDATE`：Application-owned 主循环、跨 Turn Work State、Observation/Package、fresh Review
  路由与 Delivery binding 已有本地确定性证据；Access browser PASS 保持不变。
- 这不是完整 `CONVERSATIONAL_ENGINEERING_AGENT@1` 资格。真实 World Model query、Source Broker/Worker、完整 append-only Ledger/Citation、
  Provider driver/Reviewer、Disclosure、ADR-017 fallback、固定 Chat launcher wiring 和五轮 live canary 仍为
  `NOT_INTEGRATED / NOT_QUALIFIED / NOT_LIVE`。
- `V-TIMEBOX-CHAT-001`、`V-CHAT-EXPERIENCE-001`、`V-CHAT-001`、`V-CHAT-QUALITY-001`、`V-CHAT-XD-001`、Comparison 与 Preview
  均继续 `NOT-RUN / blocking`；本 Finding 不授权任何外部调用或 live 验证。
- 现有 System Owner 与安全不变量未改变；System 文档只同步当前实现边界，不把本地 fake-port PASS 写成 Provider、Source、答案质量或
  Production PASS。主处置目标为 `ITER-010-VERIFICATION`。
