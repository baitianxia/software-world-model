---
id: FINDING-010-293
kind: implementation-finding
status: dispositioned
authority: implementation-evidence
owners: [project, engineering, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-EXECUTION-PLAN-CURRENT]
code: [src/software_world_model/interface/http_api.py, src/software_world_model/interface/agentic_runtime.py, src/software_world_model/interface/engineering_chat_alpha_cli.py]
tests: [tests/test_engineering_chat_browser.py]
iteration: ITER-010
classification: iteration-design
disposition: iteration-design
target: ITER-010-SLICE-001
---

# FINDING-010-293：浏览器入口尚未贯通世界模型 Agent

## Observation

当前存在三条浏览器语义：无参数 Chat 启动器是 Access 展示页；artifact 会话才可能进入工程 Agent；另一个 `/v1/browser/chat` 评估入口在激活时
直接进入源码证据回答服务。独立的世界模型浏览器入口也没有证明与用户会话共享主 Agent。因此“已有 Web 页面”不能作为最小完整体验的交付证据。

## Evidence

- `/v1/browser/chat` 在现有运行时优先调用 `prepare_evidence_answer`，其路径没有主 Agent 的世界模型工具选择和重规划证据。
- `WorldModelBrowserApplication` 是独立的评估表面，不接收同一浏览器会话的精确版本源码证据配置。
- 无参数 Chat Access 启动器的公开诊断仍说明 Provider、Agent、世界模型和受控源码工具未连接；只有 artifact 会话才尝试建立这些绑定。
- 现有浏览器测试覆盖 HTTP/证据回答行为，但没有证明一个真实问题依次经过世界模型认知、Agent、源码补证、Citation、fresh Reviewer 和多轮 Chat。

## Decision / Disposition

归因到 TASK-1 的运行时组合层。先把用户默认 loopback 入口绑定到 artifact Agent runtime，并让世界模型和精确版本源码成为并列只读证据工具；保留
Access 和 EvidenceAnswerService 作为诊断/兼容表面，不得把它们的通过结果当作 TASK-1 完成。不得先扩展答案协议或增加题目特判。

## Verification

本 finding 仅记录代码现状和下一动作，不宣称产品完成。必须在同一浏览器会话用一个问题、一个追问和一个新问题取得真实运行记录后，才能关闭。
