---
id: FINDING-010-272
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [ai, operations, quality]
depends_on: [FINDING-010-271, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-OPS-CONFIGURATION]
code: [src/software_world_model/ai_infrastructure/volcengine_ark_chat_adapter.py, src/software_world_model/ai_infrastructure/ark_chat_conformance.py]
tests: [tests/test_volcengine_ark_chat_adapter.py, tests/test_ark_chat_conformance.py, tests/test_lightweight_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: version-and-freshly-qualify-the-changed-ark-wire-identity
target: SYS-OPS-CONFIGURATION
---

# FINDING-010-272：Ark wire rendering 改变必须取得新的版本身份与 fresh Conformance

## Observation

包含 `FINDING-010-271` 通用单一 system authority 修复的 clean product
`6a4966d1c6bf9857ae5809ae5a0e75fe826c5814` / tree
`153cde11860c408663f34eaf6b439fe7d254118d` 启动 fresh `run-129-phase-c-review-boundary` 时，在 listener、credential 与模型 dispatch 前以
`QUALIFICATION_INVALID: Ark conformance result is stale for the current implementation or configuration` 失败。两个 Gateway repository 只完成
schema 初始化，model roots/outputs 与 HTTP failure 均为 0；没有 launch 或 terminal receipt，因此该 run 不是答案质量或 Provider availability
证据。

Ark Conformance 会密封 `volcengine_ark_chat_adapter.py`、`ark_chat_conformance.py` 及相邻 Gateway/transport exact bytes 的 aggregate
implementation digest。`FINDING-010-271` 把 Provider wire 从两个相邻 system turns 改为包含 semantic 与 closed-schema authority 的恰好一个
leading system turn；这是真实 rendering identity 变化，不能以旧 `@12 / 1.12.0` qualification 运行。与
`FINDING-010-160` 中不应落在 Adapter 的 Application 诊断不同，本次修复本身属于 Adapter contract，不能恢复旧 bytes 规避资格门禁。

## Disposition

- Ark Adapter identity 升为 `openai-chat-completions-no-tools@13`，Conformance fixture 升为 `1.13.0`；endpoint、model、credential、TLS、
  retry、tools、SSE、reasoning effort、预算和 Provider route 均不改变。
- strict Conformance oracle 继续要求恰好一个 leading system message，并验证 closed Schema authority；必须在 clean exact product 上取得 fresh
  live PASS result 后，才可创建 successor Artifact Session。
- 这不是 Provider recovery，也不授予 fallback、重试、输出别名或题面专用处理。run-129 只保留为 pre-dispatch qualification failure 证据；
  fresh model quality 复验必须使用新的 run identity、private runtime artifacts 与 current qualification。

Adapter、Conformance、Gateway、Conversation、Session/runtime/launcher 与相邻 live harness 的 182 项相关测试通过；current candidate 的
configuration fingerprint 为 `sha256:8a9e9f2d7e503b895ec2b4e7df8abd30dda9996083ecd4cf7d9bc03a5f41d197`，implementation
aggregate digest 为 `sha256:8788013e592ec50b87a3d638b326e892bce6769e49b379c13525e121182fdb70`。fresh live Conformance
结果在取得后补记；在此之前不预报 Phase C 运行成功，也不推进 Phase D。
