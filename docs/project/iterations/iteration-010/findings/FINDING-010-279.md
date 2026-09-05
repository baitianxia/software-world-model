---
id: FINDING-010-279
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, quality]
depends_on: [FINDING-010-277, FINDING-010-278, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/lightweight_engineering_agent.py]
tests: [tests/test_lightweight_engineering_agent.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: bounded-duplicate-action-replan-and-unread-candidate-ordering
target: src/software_world_model/application_services/lightweight_engineering_agent.py
---

# FINDING-010-279：同一主 Agent 的重复动作必须在 Application 层收敛

## Observation

run-160-phase-c-loopback 的 q5 在同一调查中重复了相同的 Source 搜索和读取动作。Reviewer 返回 MORE_EVIDENCE 后，已有但尚未读取的认知导航候选没有稳定地占据下一步的可用前缀，导致 Primary 继续重复或偏离当前证据缺口。
该偏差发生在 Application Agent 的 action history 与 candidate presentation，而不是 cognition provenance、Source Broker、Provider 或 Reviewer
职责。

## Evidence

- run-160-phase-c-loopback 的 sealed q5 轨迹记录相同搜索、相同读取和 Reviewer MORE_EVIDENCE 后仍存在的未读候选；监督 directive
  指定最早责任层为通用 evidence planning/duplicate-action recovery。
- tests.test_lightweight_engineering_agent 的 21 项定向测试通过，新增夹具验证重复 READ_SOURCE 不产生第二次 Tool dispatch、同一主
  Agent 收到 bounded feedback 后完成合法 FINISH，以及无进展 Observation 形成 replan feedback。
- _ordered_read_candidates 仍保留全部 authority-owned candidates 和原始 Citation identity；只将同角色候选的排序稳定为较早的未读认知来源
  优先，不解析答案正文或题目内容。

## Disposition

在现有 Application loop 内以 action fingerprint 记录已经执行的调查动作；重复动作消费既有 action fuse、写入审计事件并反馈同一主 Agent
选择不同的合法动作，不再次调用 Tool。progress=false 的唯一动作也写入 bounded replan feedback。Reviewer 要求更多证据时，只追加通用的
“优先已有未读 Source candidate、避免已完成动作”反馈，并按内部 sidecar 的既有来源顺序呈现候选。该修复不增加预算、不修改
model-facing 字段、Prompt、Provider、Reviewer 或 Citation/Source identity，也不包含工程、类名、方法名或题目规则。System contract 已有的
duplicate/no-progress fuse 继续作为跨实现不变量；本 Finding 仅记录本实现的闭合，不宣告 Phase C 完成或 ADVANCE。
