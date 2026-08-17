---
id: FINDING-008-011
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [quality, engineering]
depends_on: [ITER-008-SLICE-001, FINDING-008-005, FINDING-008-010]
code: [validation/structure_world_model_iteration_008/capability/cli.py]
tests: [tests/test_iteration_008_capability_harness.py]
iteration: ITER-008
classification: local-implementation
disposition: repair-capability-freeze-verifier-import-and-cover-valid-freeze-path
target: validation/structure_world_model_iteration_008/capability/cli.py
---

# FINDING-008-011：Capability freeze 正向校验路径缺失指标契约 import

## Observation

DeepSeek Conformance run-001 PASS 后，同一 clean candidate 在零 Provider 调用下成功生成 Capability freeze
`sha256:ad1ba1fd75739e3dcbc5e127301bb0817a3cd6b3c3258af4d86782f6d7d72551`。在请求 39-call 授权前执行独立
`verify-capability-freeze` 时，校验器不是返回 PASS，而是在计算 metric contract digest 时触发
`NameError: BOUNDED_JAVA_SOURCE_SEMANTICS_EVALUATION_METRIC_CONTRACT is not defined`。

## Evidence

- freeze 生成器从 `software_world_model.ai_infrastructure` 正确导入并使用该常量，因此可以密封 freeze；
- CLI verifier 引用了同一常量却没有导入，执行到有效 freeze 的 metric binding 分支时确定性失败；
- 既有测试只先验证篡改 freeze 的早期拒绝，并直接把内存中的有效 freeze 传入 runner，未覆盖“密封的有效 freeze 经独立 verifier
  接受”这一正向边界；
- live 失败发生在 authorization 创建、credential resolution 和 Provider transport 之前，因此该 Capability freeze 没有授权、没有消费
  credential，也没有产生任何 39-call Provider request。

## Impact and classification

缺陷只影响 ITER-008 本地验证 CLI 的可执行性；Provider contract、Capability metric、suite/oracle/evaluator、runtime 语义和安全 Owner
都没有改变。修复是补齐已有常量的 import，并让 fake-transport 端到端测试先用独立 verifier 接受有效 freeze，再继续验证篡改拒绝和
39-call 闭环。因此分类为 `local-implementation`，主处置落在代码和回归测试，不修改 System Contract。

该修复会改变 exact Git candidate 与 capability package manifest。按 `FINDING-008-005` 已处置的同候选规则，旧 Capability freeze 即使
其文档 digest 正确也不得执行；已通过的 Conformance run-001 作为历史 live 证据保留，但不能授权修复后 candidate 的 Capability。

## Decision and disposition

在 CLI 的 `software_world_model.ai_infrastructure` import 中加入
`BOUNDED_JAVA_SOURCE_SEMANTICS_EVALUATION_METRIC_CONTRACT`，并在 full fake-transport flow 中增加有效密封 freeze 的正向校验断言。
不改 metric 值、不增加 dependency、不绕过 verifier，也不对旧 freeze 请求授权。

代码、测试和本 Finding 写回后形成新的 clean exact candidate；随后重新生成 2-call Conformance preflight 并取得新的 exact 用户授权。
只有该新候选 Conformance PASS，才可生成、离线验证并申请新的 39-call Capability freeze。

## Verification after disposition

- 新增的有效 freeze 正向校验断言 PASS，且原篡改 freeze 拒绝与 18-case / 39-call fake-transport 闭环仍在同一测试中执行；
- live Conformance run-001 的 2 次调用和证据不被修改或重试；
- 问题 freeze 未授权，Capability、正式 Web、hidden canary、SLICE-002、Production Activation 与 push 均未执行。
