---
id: FINDING-010-134
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, knowledge, source, ai, quality, interface, project]
depends_on: [FINDING-010-130, FINDING-010-132, FINDING-010-133, SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE]
code: []
tests: []
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: repair-knowledge-construction-and-question-relevant-cognition-first
target: SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE
---

# FINDING-010-134：run-042 的最早偏差是行为知识未构建，Agent 与 Reviewer 另有独立故障

## Observation

`V-LAYER-ATTRIBUTION-001` 对 run-042 原登录题、认证失败日志、401/403 职责和用户可见总结逐层复核后确认：

1. exact Source 包含登录认证、失败 warn、成功登录审计、authentication/access-denied handler 接线和 401/403 应用响应 code；
2. 唯一 World Model Snapshot 只有 Maven 模块/依赖，所有行为问题得到相同 34 项 question-independent projection；因此行为 material fact 的
   first divergence 是 Knowledge construction/admission，而不是 Prompt、Source query、Reviewer 或 Web；
3. 固定同一 Agent action trace、移除无关 Maven observation 后，Turn 3 仍未读 `UmsAdminServiceImpl`，Turn 4 仍没有 full-content read；这是
   独立的 Agent investigation failure；
4. 完整 Source evidence bypass 可以机械支持决定性事实；Reviewer 却放行带 PARTIAL/fuse/开放 need 的 Limitation，并在已有三项支持的用户可见
   API Draft 上扩张到前端 UI；这是独立 guard failure；
5. authorized Result 与页面一致，没有 display first divergence。

## Evidence

- `ITER-010-RESULT-V-LAYER-ATTRIBUTION-001` 固定 product/source、Session/terminal、两个 Gateway DB、ordered Read Authority 与 Snapshot 的
  exact digest，并记录逐 material-fact chain 和六个替换臂；归因过程外部模型调用 0；
- Snapshot 实测为 8 Entity、15 Relation、0 Literal，类型/谓词只含 Maven structure；记录的 Cognition 自报 question-independent；
- exact Source 的 `UmsAdminServiceImpl.java:99-118`、`SecurityConfig.java:60-62`、两个 handler、`CommonResult` 和 `ResultCode` 提供反例；
- Gateway manifest/output 的只读重放证明 Turn 3/4 的实际工具序列、Limitation 与 Reviewer `APPROVED`，Turn 5 的三项 supported claim 与
  `INCOMPLETE_USER_VISIBLE_FLOW` scope finding。

## Decision and disposition

该发现处置到 `SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE`。下一项产品修改只进入 Knowledge/Application cognition owner：

- 形成同一 Binding/revision 上 ordered profile-specific Read Authorities 和 Capability Manifest；
- 至少组合结构与实现/行为维度，不创建 mixed-profile Snapshot/Read Set；
- 从原问题 material Need 形成 Question Eligibility，并只投影相关 cognition 或 explicit Gap；
- 保留每项 Profile/Schema/Context/Coverage/Support/Unknown 与 authority provenance；
- Source 只能核实、补充或纠正当前 Turn，不能被重标为 World Model contribution。

v7 Prompt/Reviewer 继续冻结；Web 当前无需修复。上述候选必须通过 `V-COGNITION-ELIGIBILITY-001` 后，才可讨论一个另行授权的方向 canary。
