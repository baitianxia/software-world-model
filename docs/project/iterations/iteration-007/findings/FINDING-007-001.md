---
id: FINDING-007-001
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [product, project, quality]
depends_on: [ITER-007-READINESS, ITER-007-SLICE-001, PROJECT-GOVERNANCE-ITERATION-LIFECYCLE]
code: [scripts/docs.py]
tests: [tests/test_docs_gate.py]
iteration: ITER-007
classification: iteration-design
disposition: use-user-held-live-questions-after-product-code-freeze
target: ITER-007-SLICE-001
---

# FINDING-007-001：用户现场问题无需在编码前交给实现方

## Observation

原 Readiness 把“实现阶段不可见”实现成 external evaluator-owned ACL、预冻结题集与公开 commitment receipt，导致用户必须先
提供外部 runner 或回执。用户澄清实际协作方式是“开发者开发、用户提问”：问题本来就由用户持有，开发阶段不会进入实现方环境。

## Evidence

- 用户消息 `codex-user-message:sha256:68df2434a0e31c7996d57ce124d1e3b309f08705cd7e508537c82dbac4de8147`
  明确“你开发，我提问”；
- `PROJECT-GOVERNANCE-ITERATION-LIFECYCLE` 已允许问题由独立评测方**或用户**持有并在实现阶段不可见；
- 共享 workspace 无法提供 external evaluator-owned ACL，但用户不披露问题即可维持实现期不可见性；
- 开发者若在编码前接收问题，或用自己编写的测试题冒充现场题，都会破坏该边界。

## Impact and classification

这是 ITER-007 的评测交付方式，而非产品运行时接口变化，分类为 `iteration-design`。预冻结的公开 HMAC 协议仍可用于外部
evaluator，但不再是 `SLICE-001` 编码前置；用户现场问题仍严格阻断本 Slice Result 和后续 Slice 授权。

## Decision and disposition

Manifest 使用 `user-held-live-after-product-code-freeze` 模式。编码前只冻结问题数量下限、判定规则、Source-off/无 fallback、
跨域与 boundary 要求；未知的 project/suite/baseline/target 使用封闭 marker，而非伪造 digest。产品代码冻结后，用户第一次披露
问题时生成 exact 输入、问题、baseline、target 与结果 digest；披露后若修改产品代码，必须保留结果并更换现场问题后重试。

`scripts/docs.py` 只在该显式模式且 owner 为 `user` 时接受未披露 marker；普通 independent-evaluator 模式仍要求 exact digest。
完成 Slice/Iteration 时 Result 的 exact digest 规则不放宽。

## Verification after disposition

- `V-PRE-004/005` 绑定用户消息并只关闭编码前 readiness；`V-CANARY-001`、真实 Web 和用户问题仍未执行；
- `SLICE-001` 是唯一 active Slice，SLICE-002/003 仍 proposed；
- 文档门禁测试覆盖普通预冻结模式不退步，以及用户持有模式只允许两个封闭 marker。
