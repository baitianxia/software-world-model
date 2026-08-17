---
id: FINDING-008-006
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai, security, quality]
depends_on: [ITER-008-SLICE-001, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-QUALITY-SECURITY]
code: [validation/structure_world_model_iteration_008/capability/authorize.py, validation/structure_world_model_iteration_008/capability/cli.py, validation/structure_world_model_iteration_008/capability/freeze.py]
tests: [tests/test_iteration_008_capability_harness.py]
iteration: ITER-008
classification: local-implementation
disposition: bind-request-authorization-and-invocation-before-dispatch
target: validation/structure_world_model_iteration_008/capability/cli.py
---

# FINDING-008-006：授权文件必须再次绑定实际执行的 freeze

## Observation

初版 runner 分别验证了 freeze 自身 digest，以及 authorization 与同目录 request 的一致性，但没有再次比较 request 中的
`freeze_ref`、`freeze_digest`、`authorization_scope` 是否等于本次实际执行的 freeze。攻击者若修改 request scope、重新计算其公开 digest，
再为该 request 构造格式正确的 authorization，初版链路会接受 authorization 后继续执行另一份 preflight/freeze。

## Evidence

- 回归先生成有效 preflight，再把 request 的 `planned_provider_call_count` 从 2 改为 3，并重新计算 request digest；
- authorization loader 会正确确认该 authorization 与被修改的 request 一致，这证明“文件各自有效”不能替代跨文件 exact binding；
- 修复前 runner 没有 request → executed freeze 比较；修复后同一 fixture 在创建 result directory、读取 credential 或调用 transport 前以
  `QUALIFICATION_INVALID` 失败，transport call count 为 0；
- 另一个 fixture 修改 Capability freeze 中的 evaluation definition 并重新计算 freeze digest，exact verifier 仍拒绝该定义漂移。

## Impact and classification

`SYS-CONTRACT-AI-MODEL-GATEWAY` 和 `SYS-QUALITY-SECURITY` 已要求每次授权绑定 exact freeze、payload boundary 且在 credential resolution
前验证。发现的是 validation runner 未完整实现既有不变量，没有改变 Owner、协议含义或安全边界，因此分类为
`local-implementation`。

## Decision and disposition

主处置进入 Capability CLI：Conformance 与 Capability 两条执行路径都必须在加载 authorization、创建一次性结果目录、解析 credential 和
构造 Provider transport 前，比较 request phase、freeze ref、freeze digest 及完整 authorization scope。Freeze verifier 同时改为 exact
字段集合校验，并重建 proposal contract、suite/oracle/evaluator binding、evaluation definition、Provider/Conformance binding 与 dispatch
contract；公开 digest 只证明文档未无意损坏，不能代替语义验证。

Authorization loader 另要求 exact 字段集合、schema/phase 对应、严格十六进制 user-message ref、授权时间晚于 request，以及所有禁止面保持
`false` / `NOT_EXECUTED`。该 Finding 由代码和 fault test 完整处置，无需修改 System 文档。

## Verification after disposition

- 修改并重新密封 request scope：dispatch 前拒绝，transport 0 call，result directory 不存在；
- 修改并重新密封 evaluation definition：freeze verification 拒绝；
- 合法 fake chain 仍恰好执行 2 次 Conformance 与 39 次 Capability call，并闭合 18/18 PASS；
- 无 hidden retry、hidden canary、Production Activation 或 push。
