---
id: FINDING-008-009
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai, architecture, quality, security]
depends_on: [ITER-008-SLICE-001, FINDING-008-005, FINDING-008-008, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-QUALITY-SECURITY]
code: [src/software_world_model/ai_infrastructure, validation/structure_world_model_iteration_008/capability]
tests: [tests/test_iteration_008_capability_harness.py, tests/test_iteration_008_capability_qualification.py, tests/test_model_egress_gateway.py]
iteration: ITER-008
classification: iteration-design
disposition: hold-provider-dependent-gates-pending-new-provider-contract
target: ITER-008-SLICE-001
---

# FINDING-008-009：Ark 路径诊断完成后转入新 Provider 接入等待态

## Observation

更换代理节点后，exact Ark host 的 credential-free verified TLS handshake 成功；随后单独冻结和授权的一次最小
`ark-code-latest` 模型诊断也成功返回 Adapter-compatible strict JSON，Provider response 中实际模型 identity 为 `auto`。这证明该时点、
该替代路由上的 Ark TLS 与最小模型调用可用，但诊断既不是当前 Adapter `@8` 的 2-call Conformance，也不是 18-case / 39-call
Capability Evaluation。

切回原节点后，同一 credential-free probe 再次在 certificate verification 前得到与 run-001/run-003 完全相同的
`SSLEOFError` / errno 8。与此同时，用户在无痕浏览器访问同一 HTTPS endpoint，得到 Ark 的 HTTP `AuthenticationError` 响应；因此
该节点不是对所有客户端都全局不可达。当前证据只支持 Python/OpenSSL TCP/TLS 流与该节点/规则/协议路径的选择性交互问题，不能进一步把
原因断言为 Ark 服务故障、节点整体故障、证书问题或应用 Adapter 缺陷。

在继续 Provider-dependent Gate 前，用户决定更换模型 Provider，并要求先继续其他开发内容。当前 Slice 的 Provider-independent 实现与
确定性验证已经闭合，没有发现需要为等待新 Provider 而修改的产品代码。

## Evidence

- changed-node TLS diagnostic run-004 绑定 freeze
  `sha256:7eb8eae0bd1894f6c2ee1b8d274bfce3efb07f793640c0b50f998ff7fdee196a`，恰好执行一次 credential-free verified
  handshake 并 PASS；terminal digest 为
  `sha256:d868f21440577c14fd916ed3988564ea66e17e476a6d5b1dbfa02ccf4fba64f`，result digest 为
  `sha256:a079a426f0b4cd12873f8569f3ba5a71c62d1a39c33069fef8d763025e40eb4c`；
- `ark-code-latest` model diagnostic run-001 绑定 freeze
  `sha256:ac10787939dd4bd47893ab0b40cf373b075802914218fc131c32177ebc80f9c3`，恰好执行一次最小模型调用；请求模型为
  `ark-code-latest`，响应模型为 `auto`，结果为 Adapter-compatible strict JSON，input/output token 分别为 147/11；terminal/result
  digest 分别为 `sha256:ea9c19ac32bc6fbe2aaea2181f9b8baa43cc57b9f598b6cf213ec9cbf82b1705` 和
  `sha256:191ce2ba7bb3cd64b77d497812f008070ce9961e364f6d5e1024464ec5f86b1c`；原始 prompt/response 与 credential 未持久化；
- original-node TLS diagnostic run-005 绑定 freeze
  `sha256:db2eaf8d973931587a245f1e9b95431406cdb9e99149ef37db8600cdc46c90a6`，恰好执行一次 credential-free verified
  handshake；它在 certificate verification 前以 `SSLEOFError` / errno 8 失败，result digest 与 run-001/run-003 相同，为
  `sha256:78ec3d31d4bb4c0b878c169995a62848da4d582698a31f2df6cf628b3e78df50`，terminal digest 为
  `sha256:501549a54f1f45682d5e0b12a583b190235d331b0a3eed80d1b29ecc65e6136d`；
- 用户报告全新无痕浏览器对同一 endpoint 收到 Ark HTTP `AuthenticationError`；该现场事实仅证明浏览器路径到达 Ark HTTP 层，
  不证明 Python/OpenSSL 路径等价，也不构成 Provider 资格证据；
- 更换 Provider 的用户决定 ref 为
  `codex-user-message:sha256:d68755b1031a67a2dc19b7e621abd10da09dbcbcdff8405bf2a5e8676dd64a1b`。

## Impact and classification

新 Provider 不能仅凭“OpenAI-compatible”描述继承 Ark Adapter、模型 identity、网络边界或既有资格结果。它至少需要冻结 exact Provider、
endpoint/host/path、protocol envelope、请求模型 identity 与实际响应 identity、secret reference、proxy/TLS boundary、retry/error semantics，
然后重新完成与该 Provider 绑定的 Conformance 和 Capability Gate。若这些事实改变现有 System Contract、安全 Owner 或 credential 目标边界，
必须先暂停并更新对应 System 文档及必要 ADR；在 Provider 细节提供前，不假设任何合同变更。

该事实改变当前 Slice 的执行顺序，但尚未证明 System Contract 已变，因此分类为 `iteration-design`，写回
`ITER-008-SLICE-001`。Ark 诊断保留为环境证据，不能升级为 Product Result。

## Decision and disposition

停止对 Ark 生成新的 freeze、Conformance、Capability 或模型调用，也不修改 Ark Adapter/default model。当前只保留已完成的
Provider-independent 实现和验证；Provider-dependent Gate 进入等待态，直到用户给出新 Provider 的 exact 接入信息并授权所需 live
调用。新 Provider 必须从自己的 clean candidate、preflight 和一次性授权开始，不能继承已消费的 Ark grant。

在新 Provider 未明确前，不创建猜测性的 Adapter，不更改 `docs/system/` 当前 Provider 真相，不执行 hidden canary、正式 Web、
SLICE-002 或 Production Activation。

## Verification after disposition

- Provider-independent focused suite 共 124 项：受 sandbox 禁止 AF_UNIX 影响的 11 项已在允许 listener 的执行面 11/11 PASS，其余
  113 项 PASS；
- full deterministic suite 共 956 项：sandbox 中仅 7 项 AF_UNIX 受限；对应两个 test module 在允许 listener 的执行面 25/25 PASS，
  因此 956 个唯一测试均在其预期执行面通过；
- `python3 scripts/docs.py check` 在写回前 PASS（312 份 current documents），写回并重建派生索引后再次 PASS（313 份）；
- 该用户决定之后没有发起新的 Ark/TLS/Provider 调用，也没有修改产品代码或 Provider 配置；
- Capability、正式 Web、hidden canary、SLICE-002 与 Production Activation 均未执行。
