---
id: FINDING-010-233
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai, quality, operations]
depends_on: [FINDING-010-232, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: preserve-trusted-boundary-presence-through-comprehensive-review-redaction-without-transferring-focused-ownership
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-233：run-104 暴露 comprehensive Boundary redaction 的假 absence 与 DeepSeek 402

## Observation and execution evidence

validated Engineering Chat launcher 在 product commit/tree
`09ce1a2bfa7e374ba42192ef60cc61addd516950 / b99de9912df04b0417e411c7fe139109787a2b3e` 上启动
`run-104-mvp-experience`。Browser 于 `2026-08-31T05:07:57Z` fresh 读取 DeepSeek 官方 pricing page；visible-text digest 仍为
`sha256:9c9dd4d22764599ade403c0ba6cd95abcb947810d5230ee95cb96a56a62d7668`，周一 `13:07 CST` 命中
`MONDAY-FRIDAY 12:00-14:00` off-peak。first real DeepSeek preflight 在 `2026-08-31T05:09:39.010436Z` 密封
`ALLOWED_OFF_PEAK` receipt `sha256:95f2db0be6722d5a6d0326d3d82682080b602588648d58844ca80662b4681b59`。

本次按外部同签名停止边界执行了三个 Turn：

- Q1：`FAILED / AGENT_PRE_DISPATCH_REJECTED`，Ark 1 + DeepSeek 14 = exact 15 dispatch；DeepSeek 14/14 completed，shared logical
  Turn fuse 没有越界；
- Q2：fresh Conversation 的 Ark 1 个 sealed 429 后，DeepSeek 第一次 dispatch 返回 sealed `HTTP 402 / invalid_request_error /
  unknown_error`，故为 `FAILED / AGENT_MODEL_CALL_REJECTED / PROVIDER_HTTP_ERROR`，总 dispatch 2；
- Q4：fresh Conversation 的省略指代继续形成 `SUCCEEDED / APPLICATION_INPUT_CLARIFICATION / dispatch 0`。

Q2 的 402 是 materially new raw Provider response，不是 PDR-007 闲时门禁、TLS、credential、Ark availability 或本地代码 verdict。为避免对同一
外部签名重复发送，Q3/Q5 未再 dispatch；这不撤销 standing authority，也不阻止本地开发。terminal 状态
`STOPPED_AFTER_DISPATCH`，3 Turn / 3 Conversation / 17 dispatch；Ark 0 completed、2 failed，DeepSeek 14 completed、1 failed，retry、人工审批、
post-dispatch unknown 与 Production 均为 0。DeepSeek 15 次 HTTP dispatch 复用同一 verified TLS session 14 次。

session、turn scope、pricing capture、launch、terminal、Ark DB 与 DeepSeek DB 的 SHA-256 分别为：

- `fbee45b0af23d2abfd4d816500b21ea12f1238be901fd986befff8019a5dc1f0`
- `409c4bdaa9a434196e2073a56644d94cc6cb4a97d658313050b2a3afd83ea6f1`
- `ce6aa0d1d72b26a016a2f6c9399e6db3bdd3bd9fbb5b6ceef09bd5cbc1e7e1d4`
- `6950e3ca0bdcbe7a7b57cca547d73d1ccb8068dbdd27b6202ea39935e2d2e7a6`
- `fe61774c25d07c3ee16fa8d0cdd208436440985ff06b56fa471d93985940c433`
- `5a9047e345d0b414aed282fcd80f5e1f19e36530f8570624a755fbf80576dee9`
- `c171bdb089ac06d8fe1851ea1aaa4e2bd54470a8a491f3a26aef9e7ceb8b7df4`

terminal internal digest 为 `sha256:adc7ca9efd26658bd196775f65d712dd61b7a6edbc8979248937c29936ec82cc`；preparation、session
runtime、public-source session authority 与 shared logical-turn budget digest 分别为
`sha256:363fd133f7d87a3ee81c48f970ef906f2a8a7545e7b21f3cb9092f62ed7a0c82`、
`sha256:e868785f48221049ec7c006db2e38ed9714e60ae49791d2e81d39491d1bd5821`、
`sha256:199301ecfbc1cc156fa39aeebf70185315059467bb78ea7cc7788e346754a7d1` 与
`sha256:2baf121e44b5afdfff5d0d7ce8b22d8df5404bcb68eb9fe0449ceae24c0ae9fb`。

## Exact first divergence

Q1 的 14 个 DeepSeek calls 中没有 format-repair invocation：前 7 个 Primary 调查/起草之后，链路是 4 个 fresh
`COMPREHENSIVE` Review 与 3 个 same-Package rewrite。第一次 Review 合理要求补充 exact revision 与分类；第一次 rewrite 后，Draft 已有两个
SUPPORTED Claim、`FULLY_ADDRESSED` coverage，并在真实 Draft 中绑定 1 个 reportable Boundary ID。真实 Package 同时含 3 个 Boundary
Observations。

但 comprehensive ownership separation 会把 Reviewer input 的 `evidence_package.boundary_observations` 与
`draft.boundary_observation_ids` 都投影为空，只附带“空值不是 absence evidence”的布尔规则。Reviewer 仍把这个阶段性空数组当成真实 absence：第二次
Review 要求为 honest unresolved-boundary sentence 添加 SUPPORT/Boundary binding；rewrite 收窄后，第三次 Review 又要求把同一句加成 Claim；删除
diagnostic 后，第四次 Review 反向要求恢复数据库变化、缓存刷新和权限生效的 uncertainty 分类。它在 add/delete 之间振荡，下一 Primary preflight 被
exact 15-call logical Turn fuse 拒绝。

因此最早偏差不是 run-103 semantic anchor：本次没有 repair call，anchor 没有机会介入。问题是 comprehensive redaction 删除了 exact values 的同时也
删除了可信 presence，弱模型把 redaction 误读为 absence；单一布尔警告不足以表达“真实 Draft 已绑定 Boundary，但具体判断仍由 focused owner 完成”。

## Decision and disposition

1. comprehensive input 继续把 exact Boundary IDs、content 和 materiality challenge 投影为空，不能把 focused ownership 重新交给
   comprehensive Reviewer。
2. `boundary_challenge_projection` 另行投影 Application-trusted 的 actual Package Boundary count 与 actual Draft-declared Boundary-reference
   count。它们只是 presence metadata，不是 Evidence、Boundary 内容或 approval；nonzero Draft count 禁止 Reviewer仅从 redacted arrays 推导
   missing binding、missing Claim inventory 或 missing SUPPORT。
3. comprehensive 仍须报告独立可识别的普通 Claim、requirement coverage 或其他非 Boundary 语义缺陷；presence 不放行完整 Draft。exact binding
   validity、materiality、resolved-acquisition 与 reference add/remove 继续由 fresh focused Review 独占。
4. Strategy/prompt 升级到 `conversational-engineering-agent@30 / prompt@30`，Review input 升级到
   `ENGINEERING_AGENT_REVIEW_INPUT@20`；Primary input `@29`、output preflight `@24`、Review output、Draft/Answer、Tool/Source、route、budget、
   fallback、retry 与 Production contracts 不变。
5. DeepSeek 402 只作为本次外部运行证据；不得用本地 Prompt 或 route patch 掩盖，也不得在同签名上重复 dispatch。下一 live run 需要 materially
   new DeepSeek availability evidence 或 Ark 可用证据，不需要重复人工授权。

模型协议测试 `37/37`、相邻 Engineering Chat/route/authority 定向测试 `137/137` PASS。run-104 永久保持 Quality FAIL；当前继续完成
System Contract/active iteration 校验、可信父计划门禁与提交。
