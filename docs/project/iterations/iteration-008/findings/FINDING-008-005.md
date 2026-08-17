---
id: FINDING-008-005
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai, quality, security]
depends_on: [ITER-008-SLICE-001, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-QUALITY-SECURITY]
code: [validation/structure_world_model_iteration_008/capability, src/software_world_model/ai_infrastructure/ark_chat_conformance.py]
tests: [tests/test_iteration_008_capability_harness.py]
iteration: ITER-008
classification: iteration-design
disposition: require-separate-current-conformance-before-capability-dispatch
target: ITER-008-SLICE-001
---

# FINDING-008-005：当前 Adapter 没有可继承的 Conformance 资格

## Observation

SLICE-001 的 bounded Capability Evaluation 需要构造当前
`openai-chat-completions-no-tools@8` Adapter，但本机保存的 15 份 Ark Conformance Result 全部属于
`@1`—`@7`。资格加载器会把它们全部判为实现或配置漂移；因此不能直接使用旧 Result 启动 18-case Capability Evaluation，也不能把旧
Conformance、已有 Capability 或本 Slice 编码授权解释为新的 Provider 调用授权。

## Evidence

- 当前 Adapter version 为 `openai-chat-completions-no-tools@8`，当前 Conformance implementation digest 为
  `sha256:b0eed0252ab7bfd723bf9cb06b0e48d3ccd2e1c6f6d51ee2c26cdc027509d774`；
- `var/conformance/` 中共有 15 份密封结果：`@1`—`@5` 各 1 份、`@7` 10 份，`@8` 为 0；
- 对 15 份结果逐一执行 `load_ark_chat_conformance_qualification(...)`，accepted current result count 为 0，15 份均以
  `QUALIFICATION_INVALID` 失败关闭；
- 当前 Conformance fixture 固定执行 2 次 live call；ITER-008 suite 固定 18 个 Case、39 次 Provider call。纯本地 fake transport
  回归证明两段可串联，但没有产生或伪造 live 资格。

## Impact and classification

System Contract 已明确 Conformance、Capability 和每次外部分派授权互不继承；新事实没有改变 Owner、接口或安全不变量。它改变的是本
Slice 的执行顺序和授权粒度：Capability freeze 不能在有效 Conformance 缺失时形成，必须先增加一个独立的当前 Conformance Gate。因此
分类为 `iteration-design`，主处置写回 `ITER-008-SLICE-001`。

## Decision and disposition

执行顺序固定为：

1. 在 clean exact Git candidate 上无网络生成 preflight，并密封当前实现、fixture、Provider 边界及恰好 2 次 Conformance call；
2. 取得只绑定该 preflight 的明确用户授权后，才可读取 credential 并消费一次性 2-call Conformance grant；
3. 仅当新 Result 对当前 `@8` PASS 且仍有效时，才生成绑定同一 candidate、suite、oracle、evaluator、Conformance Result 和恰好 39 次
   call 的 Capability freeze；
4. 取得第二份独立用户授权后，才可执行 Capability Evaluation；任一授权消费后不可重试或扩展；
5. Capability PASS 只允许继续形成产品候选 freeze，不授权 hidden canary、正式 Web、SLICE-002、Production Activation 或 push。

Conformance 与 Capability 的 request、authorization、invocation、terminal 和 sanitized evidence 分别密封；credential、原始 prompt、原始
response、源码、产品题和 hidden canary 不进入这些文档。

## Verification after disposition

- 无授权时，CLI 在 credential resolution 和 transport dispatch 前失败关闭；
- Conformance request 的 exact call count 为 2，Capability request 的 exact call count 为 39；
- fake transport 端到端回归恰好消费 2 + 39 次，并闭合 18/18 PASS Result；
- 旧 Conformance、candidate/manifest 漂移、suite/oracle/evaluator 漂移、授权时间倒置或授权路径复用均被拒绝。
