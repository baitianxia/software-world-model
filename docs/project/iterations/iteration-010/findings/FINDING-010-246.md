---
id: FINDING-010-246
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai, quality, operations]
depends_on: [FINDING-010-228, FINDING-010-244, FINDING-010-245, ITER-010-PDR-012, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: replace-provider-opaque-citation-copy-with-one-based-ordinal-selection-and-application-resolution
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-246：run-113 越过 Ark 网络故障后因长 Citation ID 抄写漂移而失败

## Observation and execution evidence

run-113 绑定 product commit/tree
`722a73609df5f5963f11bedc982d91b0e72dff3b / ecaf6bf8144e60a5b3adc45c81951a4840509e70`、Session/Turn-scope file SHA-256
`63b3ccc459ffe1fb2b78a957cbc4342f6fc06769643538ffdc75493c79ea7ad9 /
5a6a5cbeec65c0ca0a0c2b235b252c6b1cbcd9d2e1fbd29a814570d1f97d5c47` 与 current `@12 / 1.12.0` Ark qualification。fresh Browser
Conversation `conversation_5e39509b34c64a438e4686c2625ebafb` 提交 run-112 相同的 Q4。

Ark 网络重试已成功：7 个 attempts 的 TLS、credential resolution 与 HTTP dispatch 均为 `7/7/7`，pre-dispatch TLS failure、post-dispatch
outcome unknown 与 request retry 均为 0；DeepSeek dispatch 为 0。7 个 Ark HTTP responses 均为 actual `glm-5.3` completed，input/output tokens
依次为 `9957/570`、`15491/659`、`41342/900`、`46078/965`、`48688/3083`、`51165/8192`、`48827/3097`。前五次已形成
World Model query、Source search、两次 full Source read 和第一份 `RESPONSE_READY / ANSWER` Draft，因此 run-112 的第五次 pre-dispatch TLS
故障不再是当前最早分歧。

第一份 Draft 的 Claim 3 选择了一个 broad Source Search SUPPORT Observation，并试图逐字复制其 Citation ref
`source_locator_9462f5f24f65c6f0f2d435f6dae1cd3f`；Provider output 漏掉最后的 `f`。Application 的 exact-domain validator 正确以
`$.draft.claims[3].support_citation_refs[1] must copy an exact reference from the Claim's selected SUPPORT observations` 拒绝。第一次
same-profile closed-contract repair 输入约 5.1 万 tokens，并把 `8192` output tokens 全部耗在隐藏推理，termination `length`、visible content
为空；`@12` 正确保留 Usage 并分类 `STRUCTURED_OUTPUT_INVALID`。第二次 distinct-category repair 返回完整 JSON，但把同一 ref 尾字符改成 `b`，
仍不属于 exact domain，故 Turn 以 `AGENT_MODEL_CALL_REJECTED / PROVIDER_OUTPUT_INVALID / STRUCTURED_OUTPUT_INVALID` 失败关闭；没有 Draft seal、
Review、Delivery 或 MVP verdict。

terminal receipt digest 为 `sha256:cfc627cabd0ef36ae3d2f7aabee976c6003c09eceda9535dcfbd16028a620a61`；terminal/Ark DB/DeepSeek DB
file SHA-256 分别为 `1695fa2b110c7ec7c93711a0f10f46d1f453803071855e20da9613cde2d9f76a /
f457577281052678b38fa37af34f57fcea2e5bff988846d7264138febbf532a6 /
e951c232a7d6ed051340cc5c530fac95e52102bd12a024363fad1e8a340af239`。public Session authority、Session runtime、preparation digests 分别为
`sha256:b1070fc53bee5dff6056861f68876e386902c0f21ea7b36fa79bb890ef947b9c /
sha256:efdaf5df3dba2e20491a83763c8ac398e789ebeb5f5639e6d4564747bb79f245 /
sha256:bbe158bec433c6831dfce2fce7357ef1a08aef9af87b7d7a1a774006036627d8`。

## Exact first divergence

`FINDING-010-228` 正确要求 Claim 选择最小 exact Citation set，却让 Provider 在一个 Search Observation 的数十个随机 opaque refs 中回传
完整长字符串。模型已经作出正确的语义选择，但 copy channel 把单字符遗漏/替换变成语义 contract failure。repair 又要求在约 5 万 token
完整上下文中重写整个 Work State/Draft，既放大 GLM-5.3 强制思考的 token 风险，也没有消除相同的 opaque copy surface。

这是 Provider-facing reference selection representation 的系统性缺口，不是 mall-search、特定 locator、Ark 网络或 output parser 特例。
GLM-5.3 的 current official contract 中 `low` 已是最低 reasoning effort 且不能关闭 thinking；继续降低参数不是可用修复。

## Decision and disposition

1. Domain `EngineeringAgentClaimProposal.support_citation_refs`、Evidence/Citation identity、authority receipt 与 Browser projection 保持 exact opaque
   refs，不降低安全或引用精度。
2. Provider-facing Primary output 改为 `support_citation_selections`。每项只返回 Claim `support_observation_ids` 中的 1-based
   `support_observation_ordinal` 与该 SUPPORT Observation ordered Citation domain 中严格递增的 1-based `citation_ordinals`；Provider 不再回传
   opaque Citation ref。
3. trusted Application 从 current invocation 重算 ordinal domain，要求每个 selected citation-bearing SUPPORT Observation 恰好一个 selection，
   拒绝缺项、重复、乱序、越界、非 SUPPORT 或无 Citation Observation，然后稳定解析成 exact Domain refs。重复 exact ref 只作 first-occurrence
   去重；每个 Observation 的 selection coverage 仍独立满足。序号不新增 Evidence、authority 或语义，也不做 fuzzy ID 修复。
4. 协议族升级为 `conversational-engineering-agent@31 / prompt@31 / ENGINEERING_AGENT_PRIMARY_INPUT@30 /
   engineering-agent-work-state-proposal@4 / ENGINEERING_AGENT_OUTPUT_PREFLIGHT@25`；Reviewer/Domain Draft、route、Source、budget、fallback、adapter、
   qualification 与 Production 边界不变。
5. 该表示修复写回 owner System Contract，不改变组件职责，故无需 ADR。完成定向/文档/计划门禁与 fresh live qualification 后，以 fresh run-114
   复验同一 Q4；不得把 run-113 的失败 Draft 或 request 重放。

## Verification

新增回归已验证：合法 1-based selections 稳定解析为原 exact refs；Provider 回传旧 opaque-ref field 被 closed schema 拒绝；越界 ordinal 在
Application decode 前失败关闭；final preflight 同时投影 ordinal selector contract。model-boundary、Agent、Tool、Conversation、runtime、
Browser、holdout、live harness 与 model-source 目标集合共 `146/146` PASS。文档检查 `652 current documents`、trusted-base plan snapshot/diff
与 whitespace check PASS。clean implementation commit/tree 为
`912712cffc625348887837382d0b4cadf57ab5cb / e40ba2f83ef672f5d4f2ac2b54eb600b89280fe2`。

该 clean identity 随后以 fresh `ccrun_d92ca17528c84bb7a403b3f3ea48d463` 再次取得 Ark `@12 / 1.12.0` 13/13 case PASS：actual
`glm-5.3`、input/output `387/76`、TLS/credential/HTTP `2/2/2`、retry/post-dispatch unknown 0，duration `5879ms`。result digest 与
artifact file SHA-256 分别为
`sha256:45e2d53abb5fc07bb4f5778a095077780a01b089e0a79399961287d235cbcc76 /
c88824d8091f5fa3b8ed477b97614eabbd2f97e11075ea067f253973d5c0b45a`，有效至 `2026-09-30T16:28:47.475684Z`。该短资格只确认
Adapter/provider compatibility 与当前网络探针，不替代 ordinal output 的长产品验证；fresh run-114 仍是下一证据。
