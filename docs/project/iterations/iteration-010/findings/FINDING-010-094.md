---
id: FINDING-010-094
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [product, architecture, application, interface, security, quality, project]
depends_on: [SYS-ADR-016, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-OPS-LOCAL-BROWSER]
code: [src/software_world_model/interface/engineering_qa_browser.py, src/software_world_model/interface/engineering_qa_browser_ui.py, src/software_world_model/application_services/engineering_question_answering.py]
tests: []
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: true-multi-turn-engineering-chat
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-094：共享运行 Session 的连续单轮问答不是 Chat

## Observation and evidence

用户以 `codex-user-message:sha256:f164d65a815c67b86d427ee8057f41b20d47bbbd0e8febec8ec1e02c28448068`
指出：当前体验是一问一答，而目标是能够 Chat。

现有持续 Alpha 只共享工程/revision、World Model、Source Profile、Provider route、授权和资源熔断。浏览器每次提交一个独立 question，
结果区覆盖上一题；Application 为每题新建只含当前 `original_question` 的 Request、Question Understanding、Ledger、Package、Answer 和
Review。服务能在一题失败后继续接受下一题，但没有 Conversation、Turn、消息历史、当前目标、指代、用户纠正、未解决问题或“新对话”
隔离语义。因此 `continuous_same_session_free_questions=true` 只能证明持续单轮 Q&A，不能证明 Chat。

这也是系统性架构缺口，而不是增加聊天气泡即可修复的 UI 问题。把全部历史直接拼入模型 Prompt 同样不成立：上一轮答案不是事实证据，
旧 Ledger/Package/Review 也不能静默取得当前轮权威。

## Decision and disposition

- 一个固定 Runtime Session 可以承载一个或多个 Conversation；Conversation 由 server-owned identity、ordered Turn lineage 和当前
  Conversation Context Revision 组成。每个 Turn 绑定 parent/head、当前用户消息、上下文投影、结果与 Delivery。
- Conversation Context 至少保存当前目标、已解析指代、用户约束与纠正、未解决问题和 prior Delivery references。它用于理解对话，不是
  软件事实权威；用户纠正形成新的不可变 revision 和 supersede 关系，不删除历史，也不能机械追加在错误理解之后。
- 每轮仍拥有独立 Request、调查、Evidence Ledger、Question Evidence Package、Answer、Review、Citation 和 Provider attempt。上一轮
  答案文本只能作为对话 assertion，不能直接支持当前 Claim。
- 旧证据只有在 same exact repository/revision、Source Profile、content digest 和 current-turn need 下，由可信 Application 重新纳入当前
  Ledger/Package 并保留 provenance 后才可复用；否则重新调查。软件世界模型可以按其正式 Snapshot/Read Authority 跨轮、跨对话复用。
- “新对话”只继承固定产品/工程权限边界和 exact World Model，不继承旧 transcript、working state、referent、Ledger、Package、Review、
  Citation 或 Provider 会话。无旧上下文的代词或省略表达必须请求澄清，不能泄漏上一 Conversation。
- Slice1 Alpha 可以先使用 server-side、进程内 Conversation state，并把跨重启恢复列为后续 hardening；“长期 Memory 非目标”不再被误读为
  “当前会话没有工作状态”。

## Minimum experiential proof

同一 Conversation 至少连续执行：

1. “登录流程是怎样的？”
2. “它失败时会记录什么？”
3. “我指的是认证失败，不是权限不足。”
4. “那 401 和 403 分别由谁产生？”
5. “总结一下，只保留用户能看到的流程。”

第二轮必须正确解析指代，第三轮必须修订当前理解，第四轮必须在纠正后的目标上按需补证，第五轮必须遵守新的摘要和抽象层级约束。
每轮独立证据和 Review 继续成立。隔离负测是在“新对话”后直接问“它失败时会记录什么？”；系统必须要求澄清，不能继承登录指代。
