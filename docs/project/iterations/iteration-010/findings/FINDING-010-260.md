---
id: FINDING-010-260
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai, quality, product]
depends_on: [ITER-010-PDR-014, FINDING-010-259, ITER-010-VERIFICATION]
code: [src/software_world_model/application_services/lightweight_engineering_agent.py, src/software_world_model/interface/lightweight_engineering_chat.py]
tests: [tests/test_lightweight_engineering_agent.py, tests/test_engineering_chat_provider_runtime.py]
iteration: ITER-010
classification: verification
scope: systemic
disposition: accept-phase-a-diagnostic-baseline-and-continue-phase-b
target: ITER-010-VERIFICATION
---

# FINDING-010-260：真实 Browser 证明 source-only Agent 基线可用但尚未取得质量资格

## Observation

Phase A `run-002` 在 product `88a073454d60ffd11b6ef65afe46ea887a0fe598`、tree
`0a4108df798171a4d9d0fd420e3e30f9daedd56c` 和 mall exact revision
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` 上经真实 loopback Browser 与首选 Ark route 运行。管理员注册问题、其权限/事务语义追问和
搜索导入异质问题均完成并交付自然答案与真实 Citation；折叠 trajectory 分别保存 10、4、14 个 ordered event，证明 Agent 在 Observation
后继续检索、读取或停止，而不是固定流水线。

额外的 portal 登录未见题已完成 11 个调查 event，但第五次模型输出包含非法 JSON escape，Application 以
`STRUCTURED_OUTPUT_INVALID` 诚实失败关闭；这项额外失败不被抹除，也不改变已满足的“两题一追问”基线。搜索导入之外的回答仍可能存在
未经独立质量 Gate 判定的推断，因此 Phase A 只能作为 harness 诊断通过，不能称为世界模型产品或 MVP。

## Evidence

- `var/iteration-010/pdr014-source-only/run-002/` 保存三段成功 Turn、额外真实失败、Source Observation、Citation、trajectory 和逐次 runtime
  authorization；
- terminal receipt digest 为 `sha256:00054ea84396038be4db6c50d417baf268586bee005dfabafd9d54fb95bfaf08`；Ark
  dispatch/TLS/HTTP 为 `21/21/21`，DeepSeek、retry、human approval 和 Production dispatch 均为 0；
- `var/iteration-010/pdr014-progress/phase-a-browser-evidence.json` 将 Agent、Browser、trajectory 与 replacement evidence 分层记录；
- 旧 `conversational_engineering_model.py` 与对应测试相对 `8131cae` 净增长继续为 `0/0`。

## Disposition

`V-HARNESS-BASELINE-001` 记为 `PASS / diagnostic only`，明确质量未接受。Phase A 的 source-only candidate 冻结为后续 same-Agent 消融臂；
开发直接进入 Phase B，不新增旧 Answer/Review 协议，也不针对额外 JSON 失败修改知识或答案规则。
