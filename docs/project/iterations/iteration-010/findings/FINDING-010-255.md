---
id: FINDING-010-255
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [ai, application, quality, operations]
depends_on: [FINDING-010-254, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: iteration-design
scope: systemic
disposition: rejected-by-agent-first-convergence-cutover
target: ITER-010-PDR-013
---

# FINDING-010-255：run-127 的 Reviewer repair 错把不可编辑 Draft 当成可改对象

## PDR-013 scheduling disposition

本 Finding 只保存 run-127 的真实失败证据。PDR-013 已否决下述 `@40` 实现方向：不提交该 candidate、不执行 run-128、不再增加旧
Answer/Review/preflight 协议或机械正文校验。后文“current candidate/下一步”均为发现形成时的历史处置，不再具有调度权威。

## Observation and execution evidence

whole-assertion candidate 的 clean product commit/tree 为
`188afa75e95043915b41504a9a2427dc99c49ee2 / e36c2fc86a59d227f0e854be9048d07eed8af8c8`。fresh Ark qualification
`ccrun_d6bd704521214c49bef5c75616dc36e6` 为 13/13 cases PASS、actual `glm-5.3`、TLS/credential/HTTP `2/2/2`、retry/unknown 0；
result digest 与文件 SHA-256 分别为
`sha256:8b9dd46a972fa45c3d58ab41e1c9790fb66ec39de9d6e07e38e2e002fbef3816 / 95bc4d6a74cc6f0f4e83ea4b7536e3b5d96a4ee22ffdabe5c74e93beca57a611`，
有效至 `2026-10-01T00:47:31.588369Z`。

run-127 绑定同一 exact mall revision `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`，turn-scope/session/launch/terminal 文件 SHA-256
分别为
`9e1dd0858680992950d78c2c7609a3721d8b586f3f53ec7af9a19ad7202476ad / 9940a72b9c471a43f3e7cd63b673c8153c322917ce540046f646c3f1bded41b3 /
19b7b0c9d1e5df3251ed9f483ff8826413f0bb865276566bf2b4cc6d04615577 / 7ce3adfeb8bf00af464d04b554fa6a0e390b715b4dda3dc92451f36705c5b9c7`；
session 初始模式为 `0600`。preparation/session-runtime/session-authority/terminal digests 分别为
`sha256:97a1ad2a1fd4c2236f62e5bc65e85734c063c939bf51c46c2823cc6b195f4aa2 /
sha256:2beab332a297020ecdef6a0b6f9a10a5a68d4ea0b57bbb3394109482f0d7d93c /
sha256:fa9ff68d36ae23c3ab568ded3f4d2bb912b9331cb4c22b67b4d8c0443ff576ab /
sha256:da1fe1289b85f08d01fc4b3e9689ae92e35d4e2b9704dfb9dd0a962a615698a1`。

Browser 的冻结 mall-portal 题形成 Conversation `conversation_1d0b6ede941a443097def14713a99c80`、Package
`agent_evidence_package_28849f5b614a49ca9def79fd1b35117d` 与未交付 Answer `agent_answer_5753cffdaa424ba8a33bfaf5c540820f`，最终为
`FAILED / REVIEWER_MODEL_CALL_REJECTED / PROVIDER_OUTPUT_INVALID / STRUCTURED_OUTPUT_INVALID`，fresh Review 与 Delivery 均不存在。Ark 9 calls
全部得到确定响应，TLS/credential/HTTP `9/9/9`、request retry 与 post-dispatch unknown 都为 0；DeepSeek dispatch 为 0，Production 未执行。
因此这仍不是 Ark 网络失败，也没有可安全重放的 transport unknown。

## Exact first divergence

Primary 的第 7 个 visible unit 把 affirmative technical anchor 与 unresolved boundary 写在同一行：

> 证据边界：上述各 Mapper/Dao 调用仅确认源码中的调用与本地顺序……以及 `cancelOrderSender.sendMessage` 的消息投递成功与消费方可见效果，均无法由当前源码证据确认。

focused Reviewer 同时正确提出 5 个 caller/effect Findings，却把该 unit 标成只映射 Boundary 的 `COVERED`。Application 首先给出 exact
`COVERED_ANCHOR_ABSENT_FROM_MAPPED_REFERENCE` diagnostic；Boundary content 不含
`cancelOrderSender.sendMessage`，所以该 mapping 不闭合。旧 repair directive 要求“replicate/preserve/split”，但 Reviewer 无权编辑 sealed Draft。
第一次 repair 因而把 Claim 3 加入 mapping，随即触发
`COVERED_ASSERTION_REPLICA_ABSENT_FROM_MAPPED_CLAIM`；第二次 repair 又退回原 Boundary-only mapping，两个 bounded slots 耗尽。

最早可修偏差不是 assertion/anchor validator，也不是 Provider transport，而是 Reviewer prompt 与 closed repair directive 暗示该角色能
“rewrite/split”当前 Draft，却没有明确要求：当 sealed Draft 本身不可由现有 references 闭合时，Reviewer 必须把 exact unit 标为 `DEFECT`、清空
Claim/Boundary refs、绑定一个 Finding，再由 Primary successor 改写 Draft。

## Historical proposed disposition（已被 PDR-013 否决）

以下五项是发现形成时针对旧协议路线提出的候选方案，只用于解释未提交代码的来历，不是当前 System Contract、开发任务或验收标准：

1. Reviewer 永远不能编辑 sealed Draft。初审或 format repair 都只能重算 Review；任何需要改写、拆分或删除 Draft 字节的修复必须以 exact-unit
   `DEFECT` 加一个 bound Finding 交回 Primary successor。
2. assertion-closure repair 对每个 listed unit 只有两类合法动作：改映射到现有且能同时闭合 whole assertion 与每个 exact anchor 的 references；
   或标为 `DEFECT`、清空所有 Claim/Boundary refs 并绑定一个 Primary rewrite/split Finding。不得在不闭合的 `COVERED` mappings 间摆动，也不得
   改标普通正文为 `NON_ASSERTIVE`。
3. mixed affirmative/boundary unit 若当前 Draft 没有可用现有 Claim/Boundary 精确闭合，Reviewer 必须选择第二类动作；Application 仍不静默
   改写或替 Reviewer 做 semantic choice。
4. 两次 fresh same-profile repair 与 15-call logical Turn budget、Provider retry/fallback/no-replay、Source/Tool bounds 和非 Production 边界不变。
5. 协议族升级为 `conversational-engineering-agent@40 / prompt@40 / ENGINEERING_AGENT_PRIMARY_INPUT@34 /
   ENGINEERING_AGENT_REVIEW_INPUT@28 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@34`；Primary/Review output 与 sealed Review shape 不变。

## Historical candidate verification

新增 fixture 证明 Reviewer 可把含 unmatched technical anchor 的 mixed boundary unit 标为 `DEFECT`、清空 refs 并绑定 global Finding，同时保留
其他 supported Claim；closed repair directive 明确投影 Reviewer 不可改 Draft、existing-reference remap 或 exact-unit defect 二选一。Model 定向
集合初次为 45/45 PASS；Agent/Model/Tool、相邻链路、文档/计划门禁、clean commit、fresh Ark qualification 与 live successor 尚待完成。
run-127 永久保持 Quality FAIL；45/45 只说明被否决候选的局部 fixture 曾通过，不取得合并、System Contract 或后继 live run 资格。不得把门禁
成功拒绝错误 Review 误报为答案质量 PASS。
