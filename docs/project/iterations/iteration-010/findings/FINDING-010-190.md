---
id: FINDING-010-190
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai-infrastructure, interface, quality]
depends_on: [FINDING-010-187, FINDING-010-188, FINDING-010-189, ITER-010-PDR-012]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: systemic
disposition: preserve-run-077-real-referent-display-and-route-evidence
target: ITER-010-VERIFICATION
---

# FINDING-010-190：run-077 真实验证复数指代和失败分层显示，Ark raw HTTP signature 仍重复

## Observation

fresh Browser `run-077-mvp-experience` 绑定 exact product
`1336ca73a3200d8b946c483f56acb14ca42eab68 / 7bdbd3398070ec81da7c6b97a9aaa1973057d1c4` 与 mall exact Source
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7 / 047d79d8588b76013c260f3f1a9565707301a60a`。角色重分配题的首个 Ark call
再次以 raw `PROVIDER_HTTP_ERROR` 关闭。Browser 不再只显示上层阶段码，而是同时显示
`Execution AGENT_MODEL_CALL_REJECTED`、`Provider evidence PROVIDER_HTTP_ERROR / PROVIDER_HTTP_ERROR` 和 dispatch 1。

实现者没有继续提交其余三个外部质量问题；run-076 已出现 5 次同一 raw signature，run-077 的 fresh first call 再次复现且没有新的
availability evidence。继续碰同一签名只会增加外调，不会验证产品质量，违反 PDR-012 的 no-new-evidence stop rule。

随后在同一 listener 新建第二个 Conversation，并于 EMPTY CONTEXT 提交冻结原句“这些失败也会回滚吗？”。Application 立即交付
`APPLICATION_INPUT_CLARIFICATION`，明确要求组件、流程或请求；Provider dispatch 0，证明 `FINDING-010-188` 的 plural/class demonstrative
修复越过 run-076 的真实失败点。该 probe 没有工程事实、Package、Review 或 Delivery Authorization，不冒充答案。

## Evidence

- exact launcher 仅使用
  `python3 -m software_world_model.interface.engineering_chat_alpha_cli --session-config <absolute-path>`，listener 绑定
  `127.0.0.1:8765` 并已优雅停止。preparation digest 为
  `sha256:62add8164792d33cb398ad76ca4ee9017519ea1cbcb98b29caaff54e2e8551cc`，public Source Session authority digest 为
  `sha256:f0bccb9cc300e9ad21e4c2a57d32611dc86836120af271f14d8420ee7431f7b0`。
- terminal payload digest 为 `sha256:b791303fa723b5596721161ac39575b91c70777cd5169bd037fd56ecf44bd30b`，terminal 文件
  SHA-256 为 `6a660323e6fa5fd240c8607980f55f02a41370b4da91fbe68220b3afe30fb520`。它密封 2 Conversation、2 Turn、Ark
  dispatch/TLS/credential/HTTP `1/1/1/1`、DeepSeek `0/0/0/0`、retry 0、human approval request 0 与 Production
  `NOT_EXECUTED`。
- Ark Gateway 只有 `model_call_18664df6d1a841a4974342a73c5f6187`，终态为 `FAILED / PROVIDER_HTTP_ERROR`；DeepSeek
  manifest 0。fresh 官方 pricing check 让 admission 得到 `ALLOWED_OFF_PEAK`，但 raw HTTP error 没有受信
  `PREFERRED_EXECUTION_PROFILE_UNAVAILABLE` verdict，因此 fallback 0 正确。
- Turn scope 与 Session config 文件 SHA-256 分别为
  `728117184942f00592be4a3cf44fb38c1cf838db02371922d3cb2f68a49da6a5` 和
  `9486090ff199443c00f8b46bbc00c9c01bde7db04e6192f36d132e1e48c9004c`；private files 与 Gateway DB 保持 `0600`。

## Classification and disposition

这是 `verification / systemic` Finding，主处置写入 `ITER-010-VERIFICATION`。它真实验证 `FINDING-010-188/189`，并再次确认 DeepSeek 没有因
raw HTTP string 自动启动；但它没有交付工程 Answer/Review，不能验证 `FINDING-010-186`、异质质量或 current Codex 比较。质量 Gate 继续
`NOT-RUN / blocking`；本地开发继续，新的 Provider 外调只能等待 materially new availability evidence 或新的 product divergence，不能重复
同一 raw signature。
