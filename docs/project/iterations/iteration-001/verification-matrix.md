---
id: ITER-001-VERIFICATION
kind: iteration-verification
status: pass
authority: evidence
owners: [quality]
depends_on: [ITER-001-PROPOSAL, PROJECT-GOVERNANCE-VERIFICATION]
code: [validation]
tests: [tests, demo/tests]
iteration: ITER-001
migration: reconstructed-from-existing-iteration-records
---

# Iteration 001 Verification Matrix

本矩阵重建 pre-Git 历史裁决，不把事后提交 `476517b` 冒充原始运行身份，也不裁决任何后续工作区或不同 subject；旧 CE 与 Product Validation 不能跨实现继承。

| Case | 层级 | 判定 | 最终状态 | 证据 |
|---|---|---|---|---|
| V-01 | Production regression | 旧实施记录声称当时生产自动化测试全部通过 | `288 / 288 PASS` historical attestation；原日志与 Git identity 未版本化 | [Implementation Result](results/implementation.md) |
| V-02 | Historical Demo regression | Demo 自身回归通过；不替代生产测试 | `121 / 121 PASS` | [Architecture Validation](results/architecture-validation.md) |
| V-03 | Adapter CC | exact Ark @8 两次真实调用与 12 项 Oracle 全部通过 | PASS，点时有效 | [Contract Conformance](results/contract-conformance.md) |
| V-04 | General CE | 六类模型职责真实执行并由独立来源复核 | Baseline PASS；different subject not covered | [Capability Evaluation](results/capability-evaluation.md) |
| V-05 | Product holdout | 两个未见工程六题，系统逐题不低于同条件直接调查且无重大错误 | Baseline PASS；different subject not covered | [Product Validation](results/product-validation.md) |
| V-06 | Local browser | 回环绑定、资格门禁、项目连接、聊天和恢复冒烟 | Baseline READY；different subject requires revalidation | [Implementation Result](results/implementation.md) |
| V-07 | Production activation | 不在本轮授权范围 | `NOT EXECUTED`，不阻断本轮本机范围完成 | [Acceptance](results/acceptance.md) |

V-01 至 V-05 相互独立，不能用一项替代另一项。原始 Provider、CE 和 Product Runtime Evidence 位于本机 `var/`，不受 Git 管理；版本化 Result 保存 ID、Digest、摘要、有效期和限制。

本次文档迁移另在 `476517b` 的独立临时 checkout 与冻结外部工程上新运行 production `290 / 290`、Demo `121 / 121`；它只验证该事后快照的机械行为，记录在 Migration Record，不改变本矩阵的历史身份边界。
