---
id: FINDING-010-168
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [FINDING-010-160, FINDING-010-167, ITER-010-PDR-012]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: surface-bounded-json-syntax-location-and-repeat-exact-serialization-preflight
target: src/software_world_model/ai_infrastructure/conversational_engineering_model.py
---

# FINDING-010-168：closed shape 预检生效，但复制用户双引号时可在 JSON 词法层重复失败

## Observation

fresh `run-056-mvp-experience` 绑定 exact product
`04b3022b463af80f6c35faeba3448b8f86475a60 / be010b82097e8f896aaad5db9174aaa4906ed02a` 与 mall Source
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7 / 047d79d8588b76013c260f3f1a9565707301a60a`。同一 Conversation 的登录链
Turn 1 与失败分支 Turn 2 分别以 `8 / 5` 次 Ark dispatch 达到 `SUCCEEDED / ACCEPTED`；用户把“登录日志”纠正为仅指
`UmsAdminLoginLog` 持久化后的 Turn 3，以 `4` 次 Ark dispatch 在 Draft 初始调用和 fresh same-profile repair 后达到
`FAILED / AGENT_MODEL_CALL_REJECTED`，Conversation 保持可审计但该候选不再继续提交冻结问题 4/5。

最早偏差不是 `action.operation`、Source、World Model、route、Provider availability 或授权。初始 call
`model_call_899f51726af2489bb55f2e9a68324470` 与 repair call
`model_call_2c251c4625854c3584461d86abb9f3db` 都返回 Ark completed/`stop`，且在 `draft.content` 中逐字生成：

`## UmsAdminLoginLog 写入路径修订结论（按"仅指 UmsAdminLoginLog 持久化"口径）`

其中标题内两个双引号没有按 JSON string 规则转义，使整个输出在 closed schema 检查前就无法解析。旧本地诊断只回退为
`output text is not JSON`；`ENGINEERING_AGENT_OUTPUT_PREFLIGHT@1` 只重复 closed shape 和 repair message，没有提供受信语法位置或明确的
JSON string 序列化规则，所以 deterministic repair 原样重复了同一词法错误。

Turn 2 另有一个独立的答案质量证据：正文断言 `Asserts.fail` 抛出的异常会被 `AuthenticationException` 捕获，同时自己的 evidence boundary
又承认内部异常类型未被当前证据确认。它不是 Turn 3 的 first divergence，也不因本次语法修复而被追认为正确；既有冻结“失败分支”问题在
fresh successor 中必须继续直接复测，若该矛盾重现则仍是质量失败。

## Evidence

- `terminal.json` 密封 `STOPPED_AFTER_DISPATCH`、Conversation `1`、Turn `3`、Ark dispatch `17`、request retry `0` 与 Production
  `NOT_EXECUTED`。Ark Gateway 有 `17` 个 call root；DeepSeek Gateway 的 root/manifest 均为 `0`，终态审计的 credential resolution、TLS
  handshake、HTTP dispatch 和 invoked dispatch 也全部为 `0`。
- 两个失败输出分别为 `7967 / 8417` 字符，均有完整 raw output 与 receipt；repair 的 preflight 已携带 generic parse failure，但没有语法
  location。没有旧 request retry、fallback、DeepSeek 或写操作。
- 新定向 fixture 精确构造含未转义 Draft 双引号的 malformed JSON，验证 trusted diagnostic 只给出 parser line/column/character 与 parser
  message、不回显 malformed content；fresh repair 返回正确转义 JSON 后成功。Primary 与 Reviewer 都收到同一 exact
  `json_serialization` preflight，且 preflight 不包含 `prior_output_text`。
- Agent、routing、launcher、runtime、artifact 与 CLI 受影响组合 `75/75` PASS。该本地修复没有发起 Provider/network dispatch，也没有修改
  已资格化 Provider adapter 字节。

## Classification and disposition

这是 `local-implementation`；系统 Owner、一次 fresh same-profile repair、fail-closed、Evidence/Review/Delivery 权限和 Provider wire contract
均不改变：

- Agent/Application boundary 现在在 `json.loads` 失败时生成有界、受信的 JSON syntax diagnostic，只包含标准 parser 的 line、column、
  zero-based character position 与 message，不回显输出片段；可解析输出仍沿用原 closed-object field diagnostic。
- final preflight 升级为 `ENGINEERING_AGENT_OUTPUT_PREFLIGHT@2`，对 Primary 与 Reviewer 明确重复 parseable object、embedded double quote、
  backslash、line break、copied text 与 parse-before-return 规则；Prompt 同步要求先闭合 JSON 词法，再做 schema shape 检查。
- Application 不转义、不归一化、不补写模型输出；初始与一次 repair 均不合法时仍只关闭当前 Turn。`run-056` 是不可改写的历史证据，不能用
  新代码追认其 Turn 3，也不能消费同名 authority。

fresh Browser successor 必须使用新的 product identity 与单独的 `run-057` 外发授权。获得该授权前只继续本地开发与门禁；冻结问题、mall
revision、Ark-only、无 resources/credential/write/DeepSeek/Production 的边界不得自行扩大。
