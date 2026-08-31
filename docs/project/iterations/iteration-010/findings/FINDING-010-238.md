---
id: FINDING-010-238
kind: implementation-finding
status: dispositioned
authority: human-authority-and-execution-evidence
owners: [ai, operations, quality, project, security]
depends_on: [FINDING-010-237, ITER-010-PDR-008, ITER-010-PDR-012, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-OPS-CONFIGURATION]
code: [src/software_world_model/ai_infrastructure/volcengine_ark_chat_adapter.py, src/software_world_model/ai_infrastructure/ark_chat_conformance.py]
tests: [tests/test_volcengine_ark_chat_adapter.py, tests/test_ark_chat_conformance.py]
iteration: ITER-010
classification: system-contract
scope: general
disposition: update-current-ark-preferred-profile-to-exact-glm-5-3-request-contract-and-require-fresh-qualification-before-run-108
target: SYS-OPS-CONFIGURATION
---

# FINDING-010-238：用户批准 Ark preferred actual glm-5.3 与对应 request contract

## Observation and authority evidence

用户在 `FINDING-010-237` 已证明 Provider identity drift 后，明确授权把 ITER-010 Ark preferred profile 的 actual model 从
`glm-5.2` 更新为 `glm-5.3`，并仅在此前相同的数据、预算、loopback evaluation 与非 Production 范围内继续 run-108。该 UTF-8
human authority delta（不含尾随换行）的引用与 digest 均为
`local-user-message-utf8:sha256:d27184be5bb47c2526e275232aac3c2b2091e3405310b4d4239b98af2edf1cfd`。

`FINDING-010-237` 的 one-field differential 已提供独立 Provider evidence：requested alias 仍是 `glm-5-2-260617`，两个成功响应的 actual
fingerprint 均是 `glm-5.3`；保留 `thinking={"type":"disabled"}` 会触发 current Ark HTTP 400，只移除 `thinking` 可越过参数校验。

## Decision and disposition

1. current preferred request alias、endpoint、credential reference、route role、数据范围和全部预算保持不变；expected actual fingerprint 更新为
   `glm-5.3`。DeepSeek 仍只可在 Ark 受信 unavailable verdict 后按既有 admission policy 作为 fallback，Production 仍为
   `NOT_EXECUTED`。
2. Ark Adapter 升级为 `openai-chat-completions-no-tools@9`。新 exact wire contract 只删除不再兼容的 `thinking` top-level field；
   `response_format=json_object`、closed schema instruction、no-tools、stateless、no-retry 与 verified-TLS transport contract 均不变。
3. Ark Conformance fixture 升级为 `1.9.0`，wire allowlist 和 strict oracle 都要求 `thinking` 缺席。旧 Adapter、configuration fingerprint 与
   Conformance 自动失效，不能被新 profile 复用。
4. 本 Finding 与 `SYS-OPS-CONFIGURATION` 同步处置授权和 current profile；只有新实现的目标测试、文档/计划门禁及 fresh Ark Conformance
   全部通过，Engineering Chat runtime 才能为 run-108 派生新 standing/session authority 并执行产品披露。
