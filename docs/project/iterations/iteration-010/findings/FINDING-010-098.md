---
id: FINDING-010-098
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, source, knowledge, security, quality, project]
depends_on: [FINDING-010-097, SYS-ADR-018, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/application_services/conversational_engineering_tools.py, src/software_world_model/application_services/__init__.py]
tests: [tests/test_conversational_engineering_tools.py, tests/test_conversational_engineering_agent.py, tests/test_engineering_conversation.py, tests/test_engineering_chat_browser.py, tests/test_engineering_chat_alpha_cli.py, tests/test_engineering_qa_source.py, tests/test_engineering_qa_browser.py, tests/test_engineering_qa_alpha_cli.py]
iteration: ITER-010
classification: verification
scope: systemic
disposition: evidence-tools-local-candidate
target: ITER-010-VERIFICATION
---

# FINDING-010-098：World Model 与 Source trusted tool adapter 形成本地候选

## Observation

`FINDING-010-097` 的主 Agent executor 只在 fake Tool Port 上证明控制循环；它把每次工具调用压成一个 disposition，也没有携带可由
Application 重验的 Ledger/Citation authority receipt。该形状无法诚实表示同一个 World Model Context 同时含 supported cognition 与
unknown/coverage boundary，也无法证明 Source READ 使用的是本 Turn 先前搜索签发的 opaque locator，而非模型提交的 path authority。

## Evidence

- Tool Result 升为一个或多个 typed evidence observations；同一工具动作可以分别密封 `support` 与 `boundary`，每条 Observation 继续绑定
  exact Tool Request、Work State 和 Result digest。World Model fixture 同时返回一条 supported behavior 与一条 unknown boundary，二者进入
  Package 的不同分区。
- 新 trusted adapter 从 immutable current Turn 派生 exact `EngineeringQuestionRequest`，复用现有
  `WorldModelCognitionProjector → EvidenceLedger` 与 `SourceBroker → CompiledSourceOperation → RetrievalWorker`，没有另建直接 Source/FS
  旁路。`SOURCE_SEARCH` 只接受 closed evidence class + query；`SOURCE_READ` 只接受当前 Turn Ledger 已签发的 opaque locator reference，raw
  path 在 Worker 前失败关闭。
- 每个工具 evidence 携带 Application 可重算的 authority receipt：exact Turn/Tool/evidence Request/repository revision、完整 append-only
  Ledger entry chain/prefix、evidence digest 和 Citation content digest。Application 重算原 `EVIDENCE_LEDGER_ENTRY@1` 与
  `EVIDENCE_LEDGER_PREFIX@1` 身份，并要求后继工具 receipt 保留前一完整 prefix；Source search→read 的同 Turn Ledger 由 6 条扩展到 11 条，
  包含 Cognition、Proposal、Broker Decision、Compiled Operation、Result 与 Resource Receipt。
- Source adapter 继续复用 Local Git Worker 的 exact committed object、global/class allowlist、UTF-8/binary/symlink/byte fuse 与 revision 重验；
  `src/main/resources` 是配置必需 exclusion，任何包含该目录的父 allowlist（包括 `.`）在配置阶段被拒绝。
- 定向命令
  `PYTHONPATH=src:. python3 -m unittest tests.test_conversational_engineering_tools tests.test_conversational_engineering_agent tests.test_engineering_conversation tests.test_engineering_chat_browser tests.test_engineering_chat_alpha_cli tests.test_engineering_qa_source tests.test_engineering_qa_browser tests.test_engineering_qa_alpha_cli -v`
  实际得到 `61/61 PASS`。本次只对临时 Git fixture 执行 Local Git search/read；没有读取 `mall` 源码或 resources，没有 listener/browser、
  Provider/model、credential、外部网络或 Production Activation。

## Decision and disposition

- 当前实现状态增加 `EVIDENCE_TOOLS_LOCAL_CANDIDATE`。Application-owned Agent 已能在本地确定性纵切中使用真实的现有 World Model/Source
  authority adapter，并把完整 Ledger prefix 与 Citation receipts 密封进双分区 Package；这仍不是 mall/live/答案质量证据。
- Provider-backed 主 Agent driver、fresh Reviewer、逐 dispatch Disclosure/failure receipt、ADR-017 fallback、固定 launcher wiring、Citation
  浏览器投影与冻结五轮 Chat 仍为 `NOT_INTEGRATED / NOT_QUALIFIED / NOT_LIVE`。默认 `swm-engineering-chat` 继续是已验证的 Access-only
  launcher，不能因本 Finding 自动切换到 Provider-ready。
- `V-TIMEBOX-CHAT-001`、`V-CHAT-EXPERIENCE-001`、`V-CHAT-001`、`V-CHAT-QUALITY-001`、`V-CHAT-XD-001`、Comparison 与 Preview
  verdict 均保持不变；本 Finding 不授权任何外部调用、mall Source 读取或 live 验证。
