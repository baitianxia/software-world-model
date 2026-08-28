---
id: FINDING-010-161
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [FINDING-010-159, FINDING-010-160, ITER-010-PDR-010]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_routing.py, tests/test_engineering_chat_provider_launcher.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_chat_alpha_cli.py]
iteration: ITER-010
classification: verification
scope: systemic
disposition: stop-product-repair-after-original-and-two-heterogeneous-rechecks
target: ITER-010-VERIFICATION
---

# FINDING-010-161：一次通用修复后，原失败与异质复验仍在 Ark 输出合同边界失败

## Observation

owner 纠正后的 exact candidate `a5c780f51fa5242ee8209766712ad408ed023f80` / tree
`4dcf8b0eca2f50b7618d0af1c43eca1613bace94` 已完成原失败和两个异质案例的 fresh Browser 复验。没有任何一次结构化输出失败被解释为模型不可用，
也没有为等待 DeepSeek 硬门禁而延迟 preferred-only listener。

- `run-051` 中，前一个 Ark closed output 因 JSON 外叙述失败后，fresh same-profile repair 成功恢复 closed JSON，证明新的 exact
  `validation_failure_code/message` 诊断已真实进入修复输入。随后一个新的 Ark call 在 credential/HTTP 前发生唯一 TLS failure，Gateway 才密封
  canonical `PROVIDER_UNAVAILABLE`；只有这次真实 availability 事件使 fallback eligible，DeepSeek 逐请求 admission 随即在 credential/TLS/HTTP
  前以 `DENIED_PRICING_CHECK` 关闭。
- `run-052` 立即复验原登录调用链问题。两个 Ark call 均完成 verified TLS、credential resolution 和 HTTP dispatch；初始与 fresh repair 输出的
  `action` 都只有 `arguments/evidence_need`，连续遗漏 `operation`。Turn 以 `AGENT_MODEL_CALL_REJECTED` 失败，DeepSeek dispatch/credential/TLS/
  HTTP 全部为 0。
- `run-053` 执行两个未参与修复的异质案例。第一个“商品查询入口与职责边界”在用户明确空上下文指代后执行 7 个 Ark call；最终 Answer Claim
  把 `BOUNDARY` observation 当作 support，validator 给出 `Engineering Agent answer Claim references unavailable support evidence`，fresh
  same-profile repair 又提交同一非法引用。第二个“未登录与权限不足”案例执行 10 个 Ark call；最后初始/repair 输出再次连续遗漏
  `action.operation`，repair input 已明确携带 `$.action ... missing=[operation]`。两个 Turn 都失败关闭，DeepSeek 全程为 0。

这不是 Ark 不可用，也不是 DeepSeek 窗口问题。17 个 run-053 Ark dispatch 全部完成 TLS、credential 和 HTTP；同一 missing-operation signature
在原失败和一个异质案例中跨问题复现，另一个异质案例又证明 closed shape 之外的 typed Evidence binding 仍不合约。

## Evidence

- `run-051-mvp-experience`：Ark dispatch=`7`、TLS attempt/success=`7/6`、credential/HTTP=`6/6`、DeepSeek dispatch/credential/TLS/HTTP=`0`；
  terminal digest `sha256:c45e3f6697baee46a8978f22dd42dbd7621c93c0502771c2fe70ed3a503cf985`。
- `run-052-mvp-experience`：Ark dispatch/TLS/credential/HTTP=`2/2/2/2`、DeepSeek 全部 0、retry=0；terminal digest
  `sha256:cc36b27fdbf1412bd20eacc558471e61f5ce7415b830f42c637b79b3fbc6169e`。初始/fresh repair calls 为
  `model_call_9a252241044f46b088014de6a906e2e8` / `model_call_0ded87bd80314a6d93095d9c1ae12f6e`，两个 exact output
  均缺 `operation`；原始 SQLite/receipt 保留完整 identity。
- `run-053-mvp-experience`：Browser 显示一个 0-dispatch clarification、两个失败关闭的异质 Turn 和新 Conversation 空 Context；Ark
  dispatch/TLS-success/credential/HTTP=`17/17/17/17`，DeepSeek 全部 0，retry=0，human approval request=0，Production=`NOT_EXECUTED`；
  terminal digest `sha256:bbdda9e84cd962736db6b91e7d15d08d294dda42f4492679b1bc4a3b59bb4912`。
- 商品边界最终 initial/repair calls 为 `model_call_7828b77e8c96444880d2a71a4d2fb4a2` /
  `model_call_566cc0f2197e48e0a8090b90e6b9166f`；后者的 sealed repair input 原样绑定前者 output 与
  `Engineering Agent answer Claim references unavailable support evidence`。
- 授权边界最终 initial/repair calls 为 `model_call_49354a32c5bf4ccc9184858d7ca5c736` /
  `model_call_fee18f9efaf0426a9db04a20a1bc8321`；后者绑定 trusted diagnostic
  `$.action object fields do not match the closed schema (missing=[operation]; unexpected_count=0)`，输出仍缺 `operation`。

## Disposition

按 `ITER-010-PDR-010`，原失败经一次有证据的通用修复后，又在两个未参与修复的异质案例中复验；同一 missing-operation signature 仍复现。
因此停止 Prompt 规则累积、同题重跑和无新证据外调，不再修改产品或等待/碰备用模型。`V-CHAT-EXPERIENCE-001` 保持 FAIL，严格方向质量未执行；
当前质量结论只能是 `QUALITY_FAIL_AFTER_ONE_GENERAL_REPAIR`。

该证据应进入 `V-MVP-EXPERIENCE-001` 的失败 handoff，而不是继续产品修复。冻结 verifier 无法表达这类答案前失败的问题由
`FINDING-010-162` 单独处置；在该治理缺口解决前不得伪造系统答案、Citation、Review、Codex 比较或 Result PASS。
