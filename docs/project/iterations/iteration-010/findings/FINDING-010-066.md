---
id: FINDING-010-066
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-064, FINDING-010-065]
code: [src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: remove-provider-cross-field-finish-duplication-and-derive-parent-reference-closure
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-066：Provider FINISH 不应重复维护父子引用与 disposition 分区

## Observation and evidence

clean candidate `740c74ac6abecb34e0c3037b8505d912db716100` / tree
`4e050ad1e1f13623c179201f540352954604ab6d` 的隔离 clone 通过三模块 65/65、Engineering QA 102/102、docs
459/459、compile 与 diff Gate。run-024 fresh DeepSeek Conformance 2/2 PASS，Result digest 为
`sha256:b07e31c5b779ad49f4ad5b0dfa4bf59921defa34595cff3ace9b8f6066a06054`，文件 SHA-256 为
`4b700b3e99a086717676f2b5d52591ac82e783d458c8ae27d17049de6379b2fe`，actual model `deepseek-v4-pro`、retry 0。

fresh session authority `sha256:7d5b85a2987dd1e5f2b28031401b605b7b4e8980c0f14b94928c109a0366c73d` 绑定 exact
candidate、mall `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`、Source Profile、run-024 qualification 与 user root
authorization。同一 listener 接受三道固定题，dispatch 为 6/14/5，共 25 次；retry/switch 均为 0，逐题 verified TLS，Production
`NOT_EXECUTED`。66,000-byte UTF-8 超限输入在 Provider 前拒绝，accepted question 与 dispatch 仍为 3/25。terminal receipt 文件
SHA-256 为 `70beb3ea9c97f49aa96a87a97393b2cc3de8f842da9bf000b1c179c2e885f4a0`，document digest 为
`sha256:e24bd432f6fc3ffee36d58050a3480586f8cd62c7801e45524f9ddaa48ae2b0d`；session、launch、terminal 与 SQLite
文件均为 `0600`，listener 已正常停止。

Q1 的 FINISH 已正确形成登录链原子观察，但 `check-3` 的一个 child observation 引用了 Controller full-content item，Provider 又必须在
parent `evidence_references` 中手工重抄全部 child 引用；该 Controller reference 漏抄后，既有 Domain subset invariant 正确拒绝整题。
Q3 的 FINISH 则把 `check-4/check-5` 两个 `UNKNOWN` 同时放入 supported 与 non-supported arrays；既有 exact-once/partition
校验同样正确拒绝。两个输出的事实语义大体合理，失败均来自 Provider 同时维护不能由 JSON Schema 表达的跨字段等式。Prompt `@26` 已逐项
要求 child refs retained by parent、两个数组 disjoint/exact-once，真实输出仍重复失败，证明继续增加文字约束不是可靠修复。

## Decision and disposition

- Provider-facing FINISH 改成唯一 `finish_dispositions` 数组；每个 item 由 outcome-tagged closed variant 联动 affirmative/limitation
  observation kind，不再让 Provider 把同一 checklist item 分装到两个集合。
- Provider disposition 不再重复返回 parent `evidence_references`。可信 Adapter 按 material observations 的出现顺序，对 child
  references 做稳定 first-occurrence union，并以该结果构造既有 Domain parent closure；不改写 outcome、statement、observation 或引用。
- Application Domain 继续独立重建 identity，并校验 checklist exact-once、outcome/kind、全局 observation uniqueness、support/boundary
  eligibility 与完整 Package closure；简化 Provider 表达不放宽语义或安全约束。

owning System Contract、ADR 与 Slice 已改为单一 outcome-tagged `finish_dispositions`；Provider Schema 删除 parent references，trusted
Adapter 按 child observation 顺序稳定汇总，Domain exact-once/kind/reference eligibility 不变量保持。Initial/Verification output schema
identity 升为 `@9`，strategy identity 升为 `@17`，Prompt identity 升为 `@27`；定向回归包含两个不同 child references 的稳定 parent
closure 与旧双数组/parent 字段拒绝。本次不扩张 mall disclosure，不读取或发送 `src/main/resources`，不执行 Production Activation；
run-024 保留为不可追认的失败证据。
