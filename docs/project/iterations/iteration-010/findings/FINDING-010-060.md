---
id: FINDING-010-060
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [product, application, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-057, FINDING-010-058, FINDING-010-059]
code: [src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: exact-once-finish-partition-and-post-mandatory-adaptive-exhaustion
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-060：FINISH 分区必须 exact-once，mandatory minimum 不能变成调查上限

## Observation and evidence

clean candidate `dfba244c166596101baaa9051f7147b2c0d24642` / tree
`92aadb61653380dd8d720a2a3ffa1915dbf725b7` 的隔离 clone 通过 Engineering QA 101/101 与 docs 453/453。run-021 fresh
DeepSeek Conformance 2/2 PASS，Result digest 为
`sha256:50accfd5add005540c9f7f690c7867a13a1fbf64593f0d89ca3d75fcb3f25608`，文件 SHA-256 为
`932d1b8fb198ca4b1720ad5c579742867e9cf80b5d4f98acc36ceac48f8bd3cd`，actual model `deepseek-v4-pro`、retry 0。

session authority `sha256:88d819cf07faaffe6c89299399d86bcc58e88f7551a2ddbb3f98060cad9286eb` 绑定 exact candidate、mall
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`、Source Profile、run-021 qualification 与既有 user root authorization。同一持续 Alpha：

- 原登录题用 8 次 dispatch 得到 `engineering_result_bb93af1f47767e3e03bb043fc8a5c45d / APPROVED`，默认正文覆盖 endpoint、凭据与启用
  校验、JWT、SecurityContext、失败响应和登录日志；
- 构建/安全/resources 题的 4 个 mandatory path 全部由 direct locator 连续 READ，没有 SEARCH、零命中或 no-progress；第 5 个 Investigation
  call 发出 FINISH 时 `remaining_initial_investigation_calls_including_current=8`，却把全部 7 个 disposition 放入
  `supported_finish_dispositions`，其中 3 个实际 outcome 为 `UNKNOWN`，随后又把同 3 项复制到
  `non_supported_finish_dispositions`。本地 Schema 以 `STRUCTURED_OUTPUT_INVALID` 正确关闭；
- 该失败后同一 listener 接受 401/403 题；它用 8 次 dispatch 得到
  `engineering_result_bbfe6e5b041aad1e4e2643f02335a4c8 / APPROVED`，默认正文区分 token 提取/校验、认证上下文建立、动态权限判定和
  401/403 分流，并引用四个决定性源码文件；
- 真正的超限输入使用 22,000 个中文字符，即 66,000 UTF-8 bytes，服务在 Provider 前以 local preview limit 拒绝；Gateway dispatch
  根保持 22。terminal receipt 文件 SHA-256 为 `f06f7b1099e120ce61abfc94d5b054ad9e86455e3fdcad5958846a9ccdd7c9d1`，document
  digest 为 `sha256:d38d94bb7bd7d678f1e46f0b2a32a2bc57aec3cc9da3bc10f16521c999ae6dbb`，记录三题 8/6/8 dispatch、
  retry/switch 0、verified TLS、private session/launch/terminal/SQLite files 和 Production `NOT_EXECUTED`。

因此 direct locator 已修复 run-020 的 mandatory-path rediscovery，但“分成两个数组”仍不足以让非 strict-json-schema Provider 始终生成合法
partition；同时 required paths 被模型误当成完整调查计划，使尚有充足预算和授权来源的 material Unknown 过早结束。run-021 只保留为
Q1/Q3 可接受、Q2 FAIL 与安全边界 PASS 的诊断证据，不能取得三题 Gate。

## Decision and disposition

- Provider-facing 两数组继续保持，不容忍或静默重分区非法输出。Schema description 与 Prompt 必须明确：supported array 不是完整
  checklist 副本；每项按 outcome 只进入一个数组，两数组 disjoint，union 恰好覆盖 checklist 一次；返回前执行 exact-once preflight。
- `required_evidence_paths` 是 mandatory minimum，不是 investigation maximum。闭合它们且 `untried_required_evidence_classes` 为空后，
  non-supported FINISH 仍须比较 material gap、Question Understanding evidence needs、allowlist、已消费路径和剩余 fuse；若授权未读来源可在
  `SEARCH + READ/PARSE + FINISH` 预算内缩小缺口，必须继续调查，不能因同 evidence class 已读过别的文件而结束。
- Question Understanding 选择 mandatory set 时，跨 build declaration 与 runtime behavior 的问题不能把全部 capacity 用于重叠 module
  declaration 而漏掉决定性实现；可选佐证保留给 mandatory closure 后的自适应调查。

Strategy / Initial / Verification Schema / Prompt identity 升为 `@15 / @7 / @7 / @24`。可信 adapter 和 Domain 仍拒绝 mixed、duplicated、
错误 reference 或非 exact-once 输出；本次不引入工程、问题文本、类、方法、fixture 或 Oracle 特判。Engineering QA 101/101、docs、
compile/diff 与允许 AF_UNIX 的 full 1167/1162 exact historical hold 已由 `FINDING-010-061` 闭合；新 clean/fresh live 仍待执行。
