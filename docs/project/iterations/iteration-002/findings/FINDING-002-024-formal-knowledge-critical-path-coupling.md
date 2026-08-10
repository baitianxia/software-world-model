---
id: FINDING-002-024
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, architecture, quality]
depends_on: [ITER-002-SLICE-001, FINDING-002-006, FINDING-002-022, FINDING-002-023]
code: [src/software_world_model/application_services/evidence_answer.py, src/software_world_model/ai_infrastructure/evidence_answer_strategy.py]
tests: [tests/test_evidence_answer.py, tests/test_evidence_answer_strategy.py, tests/test_browser_chat_interface.py]
iteration: ITER-002
classification: system-contract
disposition: evidence-first-synchronous-answering
target: SYS-ADR-013
---

# FINDING-002-024：正式知识生产与同步答案耦合扩大失败面

## Observation

复杂调用链体验已经取得足够源码观察，却需要把同一问题依次通过需求、事实、事实复核、推理、充分性、答案选择、顺序和最终审核。`2.0.204` 的 159 次模型调用最终正确拒绝重复且题外的答案；`2.0.205` 随后的产品复测又在充分性结构化输出阶段失败。继续提高局部重试次数会保留“多个阶段分别决定答案应出现什么”的根因，并让一个阶段变化使后续全部证明失效。

## Impact

问题跨越 Application、Response Control、Knowledge Use 与长期验收规则，属于系统性架构问题而非某个 Prompt 或工程特例。正式知识准入适合跨问题复用，但同步聊天强制等待完整知识生产会同时损害可用性、可读性和故障隔离。

## Decision and disposition

接受 `SYS-ADR-013`。同步路径改为原问题检查清单、授权源码调查、密封 Evidence Packet、引用式自然答案、独立审核和具体 Finding 驱动的同包重写。现有证据足够时不得重新运行调查；确有 Evidence Gap 时才执行针对性补充调查并形成新 Packet。正式知识系统保留为显式或后台沉淀能力，Evidence Packet 和答案审核不能绕过 Admission 与 Publication 获得跨任务资格。

处置已写入 `SYS-ARCH-INVARIANTS`、`SYS-ARCH-FLOWS`、`SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING`、`SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL` 和 `SYS-QUALITY-ACCEPTANCE`。本切片与验证矩阵改以新同步路径为验收对象。

## Verification after disposition

契约测试验证同包重写不新增 Source Operation、Reviewer Evidence Gap 只触发针对性调查、生成与审核都绑定同一 Packet Digest、审核角色没有生成 rationale 或来源工具，以及浏览器优先使用证据路径。真实模型能力与陌生工程产品验证仍须对新 Strategy 重新执行，旧 `2.0.205` 资格不证明新路径成立。
