---
id: FINDING-010-164
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [project, quality, engineering]
depends_on: [FINDING-010-163, ITER-010-PDR-011]
code: [validation/iteration_010_mvp/value_gate/runner.py]
tests: [tests/test_iteration_010_mvp_value_gate.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: align-failure-verifier-with-model-gateway-canonical-string-digest
target: validation/iteration_010_mvp/value_gate/runner.py
---

# FINDING-010-164：@3 首次真实回放暴露 Gateway output digest codec 错配

## Observation

PDR-011 治理恢复提交 `772105ca5b65834c893922311366d0f749c1da2f` 冻结 @3 runner 后，首次把既有 run-052/053
原始 Gateway 字节送入它。回放在 run-052 第一个 call 立即失败：SQLite 的 `output_digest` 为
`sha256:6926ad24ade3e18a40a8af5ff51e7ca539496d1661a8b59c721a4697863fd2ca`，而 runner 对同一
`output_text` 直接做 UTF-8 SHA-256 得到
`sha256:d2ca5dff45ad267932accece0d9de7d0b59846c540e2235c357c6d59d60bd144`。

产品 `AdapterResponse.create` 和 SQLite repository 的当前合同并不是 raw-text SHA-256；它们使用
`cross_cutting.canonical.digest_of(output_text)`，即先把 Python string 编码为 canonical JSON string value，再做 SHA-256。@3 的
synthetic fixture 曾把 Gateway digest 也造成 raw-text digest，因而没有覆盖真实 repository codec。

## Classification

这是 frozen failure verifier 的本地实现错误，不是新的产品失败、Provider 不可用或运行证据变化。run-052/053 的数据库、
terminal、browser capture 和模型输出均未修改，新 Provider/browser dispatch 为 0。不能把 JSON-quoted string 字面量
冒充 raw model output 来绕过该错配。

## Disposition

- `initial_model_output_digest / repair_model_output_digest` 继续对内嵌的原始模型文本做 raw UTF-8 digest，保持原始字节绑定。
- 与 Gateway `output_digest` 对账时改用与产品 `digest_of(str)` 相同的 canonical-string digest；不改产品代码或历史数据。
- fixture 同步生成 canonical Gateway digest，并新增反向测试，确认把 raw digest 填入 Gateway 字段必须失败。
- 修正后对 run-052/053 真实形状的 dry replay PASS：2 个 Artifact Session、19 个 Ark call、DeepSeek
  dispatch/credential/TLS/HTTP 全为 0，两个 Gateway DB digest 分别为
  `sha256:0d9fbe37fb90a5ba39bb58c061979edea03fead19ae26a24bb4cb804f683f427` 与
  `sha256:edf27e17f53268e695d44fc7571489a05181ba79cb6781dac04460c0b1acc9b7`。

该修正仍属用户授权的同一最小 governance recovery，必须在 Result 之前单独提交成为新 trusted parent；它不密封
Result，也不声称通过当前 action 的路径门禁。
