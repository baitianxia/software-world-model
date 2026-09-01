---
id: FINDING-010-271
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [ai, application, quality]
depends_on: [ITER-010-PDR-014, FINDING-010-270, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/volcengine_ark_chat_adapter.py, src/software_world_model/ai_infrastructure/ark_chat_conformance.py]
tests: [tests/test_volcengine_ark_chat_adapter.py, tests/test_ark_chat_conformance.py, tests/test_lightweight_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: compose-semantic-and-schema-authority-without-localizing-protocol-tokens
target: SYS-CONTRACT-AI-MODEL-GATEWAY
---

# FINDING-010-271：相互竞争的 system turns 会让非英语 Reviewer 翻译闭合协议 token

## Observation

Phase C 首个 `@5` Artifact Session `run-128-phase-c-integrated` 已在 exact product
`1e07f7798dbf468d6078cef3b8a28dd596ae3281`、mall Source
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` 和 capability cognition
`sha256:d552b3d8df62271ac24c85d82fcf046eb67852397eb923212f7f1eb21ba7a243` 上启动真实 loopback Browser。首题的 Ark
前八次 call 完成 cognition search/detail、Source search/read 和 `FINISH`；fresh Reviewer 的第九次 HTTP/model call 也正常完成，但把闭合
Schema 的 `verdict/findings` 及 `MORE_EVIDENCE` 翻译为 `结论/发现/需要更多证据`。Gateway 因而以
`STRUCTURED_OUTPUT_INVALID` 如实拒绝，DeepSeek dispatch 为 0，Conversation 保持 active。

Ark wire 当时先注入只含 JSON Schema 的 system message，再原样附加 Gateway 的 semantic system message。两个相邻 system authority 在中文
Reviewer 输入上发生竞争；`response_format=json_object` 只保证 JSON object，不能保证字段名和枚举 token。该失败发生在 AI infrastructure
structured-output boundary，不是 knowledge construction、Source retrieval、题面语义或 fallback eligibility。

## Affected scope and classification

受影响对象为所有 Ark JSON-mode closed-schema role，不只当前 Reviewer；任何非英语任务都可能把协议 token 当作自然语言正文翻译。分类为
**system-contract / systemic**。系统契约已经要求 Provider-specific schema authority 与 Gateway leading semantic authority 组合，不能形成
相互竞争的 system turns；当前 Ark 实现没有满足该通用不变量。

## Disposition

Ark Adapter 与既有 DeepSeek Adapter 对齐：当 Gateway 已提供 leading semantic system message 时，把任务语义与 closed output contract 合并为
恰好一个 leading system message，保留其余 user/assistant 顺序。closed Schema validator、field name 与 enum 继续严格不变；不接受中文或其他
语言别名，不增加题面、类名、方法名、路径、关键词或 substring 判断，也不修改回答 Prompt/Schema、Provider routing 或 retry/fallback。
Ark Conformance 的 strict wire oracle 同步要求恰好一个 system message。

定向契约以中文 semantic authority、中文正文和 `verdict/findings/MORE_EVIDENCE` 验证 wire 中只有一个 system authority 且 token 原样保留；
Ark Adapter/Conformance/轻量 model boundary 相关 40 项测试通过。真实 Phase C 必须在包含本修复的 fresh clean commit 与新 Session 上重跑原题；
本地测试和本 Finding 均不把该 rerun 预报为成功，也不推进 Phase D。
