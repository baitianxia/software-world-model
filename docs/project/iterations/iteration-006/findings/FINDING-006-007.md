---
id: FINDING-006-007
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, security, quality]
depends_on: [ITER-006-SLICE-001, ITER-006-VERIFICATION, SYS-CONTRACT-AI-MODEL-GATEWAY]
code: [validation/structure_world_model_iteration_006/live_authorize.py, validation/structure_world_model_iteration_006/live_comparison.py]
tests: []
iteration: ITER-006
classification: verification
disposition: require-explicit-provider-and-java-source-payload-authorization
target: ITER-006-VERIFICATION
---

# FINDING-006-007：泛化同意不足以授权 Java 源码向指定 Provider 披露

## Observation and evidence

run-003 freeze 后，用户回复“同意授权”。虽然本机授权文档生成器能把任意 non-empty reference 机械绑定 suite，真正 external
dispatch review 仍因消息未明确点名火山引擎 Ark、OpenAI Codex 以及 exact sealed Java source closure payload 而拒绝命令；
Provider calls 为 0。

随后用户以绑定 `run-003` suite `sha256:32de10fb…` 的完整文字明确授权，消息引用为
`codex-user-message:sha256:4f48e0d5…`。新授权文档通过安全审查并执行；此前 non-operative 文档没有被复用。执行结果与新的
资格 blocker 见 `ITER-006-RESULT-LIVE-RUN-003`，不反向改变本 Finding 对“泛化同意”的判断。

## Classification and disposition

Model Gateway Contract 已要求每次外部披露绑定当前用户授权，本 Finding 不改变系统契约；它把本轮 verification 的“明确”落实
为可审计要求：授权文字必须同时列出两个外部目的地、World Model 的 no-payload Structure 边界、Direct/Codex 的 exact Java
source closure 边界、`EVALUATION_ONLY` 与 Production Activation 排除项。此前生成的候选授权文档标记为 non-operative；新授权
到达后必须绑定新消息重新生成，不得复用。
