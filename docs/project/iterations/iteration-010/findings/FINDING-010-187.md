---
id: FINDING-010-187
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai-infrastructure, interface, quality]
depends_on: [FINDING-010-179, FINDING-010-185, FINDING-010-186, ITER-010-PDR-012]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: systemic
disposition: preserve-run-076-layered-browser-and-provider-evidence
target: ITER-010-VERIFICATION
---

# FINDING-010-187：run-076 越过旧 Source 矛盾后遭遇连续 raw Ark HTTP error

## Observation

fresh Browser `run-076-mvp-experience` 绑定 exact product
`bc964f364944be883a5e8de9a2c4f68e270470cb / 12724847fe191e42c829acff445293464d37e971` 与 mall exact Source
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7 / 047d79d8588b76013c260f3f1a9565707301a60a`。角色重分配旧失败题先完成 9 次
Ark model call，取得 World Model、Source Search/Read 和完整 Answer Draft；Application 随后正确发现一个 Claim 把 BOUNDARY observation
当作 support，并要求同 profile repair。第 10 次及后续四个冻结 Turn 的第一次 Ark call 均以 sealed `PROVIDER_HTTP_ERROR` 关闭，因此 5 个
Turn 都没有取得 Delivery，不能评价新的答案/Reviewer 质量或追认为 MVP。

## Evidence and layer attribution

- 第 10 次 repair 的 sealed input 显示 Source file budget `used=61 / maximum=64 / remaining=3 / exhausted=false`、
  `source_read_options=[]`，effective catalog 只有 `WORLD_MODEL_QUERY/SOURCE_SEARCH`。模型没有再看到或提出旧的 dangling READ；此前真实
  Source READ 也已完成并形成 Draft，故 `FINDING-010-185` 已越过 run-075 的最早矛盾。当前失败点是后继 repair 的 Provider HTTP outcome，
  不是 Source budget、catalog 或 Application Claim guard。
- Ark Gateway 共密封 14 个 call：前 9 个 `COMPLETED`，后 5 个 `FAILED / PROVIDER_HTTP_ERROR`。Application/route receipt 保留
  `provider_failure_classification=PROVIDER_HTTP_ERROR` 与同名 raw owner code。raw HTTP evidence 没有自行成为受信
  `PREFERRED_EXECUTION_PROFILE_UNAVAILABLE` verdict，所以 DeepSeek dispatch/TLS/credential/HTTP 全 0；这符合 ADR-017，而不是备用配置
  不可调用。fresh 官方价格检查仍让 DeepSeek admission 在周末得到 `ALLOWED_OFF_PEAK`，但它没有获得 fallback route authority。
- 新 Conversation 的冻结 probe“这些失败也会回滚吗？”在 EMPTY CONTEXT 下仍发生 1 次 Ark dispatch；run-075 含“它”的 probe 则为零
  dispatch Clarification。该差异把本地最早偏差定位到 zh-CN input policy 的复数指代覆盖，见 `FINDING-010-188`。
- Browser projection 已同时含 stage `failure.code=AGENT_MODEL_CALL_REJECTED` 与 raw Provider classification/code，但主消息和 notice 只渲染前者，
  容易让操作者误以为原始 HTTP 证据被吞掉，见 `FINDING-010-189`。数据保存与 fallback 决策本身没有丢失或改写。
- terminal payload digest 为 `sha256:97c0a62e7a2ce7083b2ee8fed8d0e19ac49353ec7f6ddc58d09ed26367956524`，terminal 文件
  SHA-256 为 `7144c3f3641e47dbe1a79aeab2827949b68321d42028650c0c1da806490f2102`。它密封 4 Conversation、5 Turn、Ark
  dispatch/TLS/credential/HTTP `14/14/14/14`、DeepSeek `0/0/0/0`、retry 0、human approval request 0 与 Production
  `NOT_EXECUTED`；launcher 已优雅停止。

## Classification and disposition

这是 `verification / systemic` Finding，主处置写入 `ITER-010-VERIFICATION`。run-076 证明旧 Source 矛盾后的链路进展和 raw failure
归属，但没有成功回答冻结套件，也没有验证 `FINDING-010-186` 的完整容器语义修复。下一 fresh successor 只能在新的 exact product identity
下继续；Ark raw HTTP error 继续保留为 raw evidence，只有 availability owner 的受信 unavailable verdict 才能启动已获闲时 admission 的
DeepSeek fallback。
