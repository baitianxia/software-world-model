---
id: ITER-001-RESULT-ARCHITECTURE
kind: iteration-result
status: completed
authority: evidence
owners: [architecture, quality]
depends_on: [ITER-001-SLICE-002, ITER-001-SLICE-003]
code: [demo, src/software_world_model]
tests: [demo/tests, tests]
iteration: ITER-001
---

# Architecture Validation Result

## Claim

阶段性验证支持现有顶层模块和正式知识单路径，但多份早期静态或机械结果不能单独证明真实模型能力。Iteration 001 的最终产品裁决来自后续生产路径 CC、CE 与 Product Validation，而不是把早期 Demo 结果升级为 PASS。

## Evidence timeline

| 阶段 | 结果 | 处置 |
|---|---|---|
| 历史 Demo 机制切片 | 支持 Source → Artifact → Formal Knowledge → Application 的顶层方向 | 保留为可行性证据，不作为生产实现 |
| 首轮 Product Holdout | `33.75 / 50`，P0 FAIL | 暴露能力守恒、覆盖和旁路问题，触发修订 |
| Formal Mapping Audit 001 | 初始 Schema 无法完整表达目标 | 实施 Hold |
| Audit 002 | 曾报告 `33 / 33 static supported` | 后续可执行性复核发现缺口，候选修订被撤回；不得视为当前 PASS |
| Candidate-only mechanism witness | 有界 Application/Engine seam PASS | 只证明机械路径，不证明真实模型或完整任务 |
| JWT formal/conformance revisions | 多轮静态、机械和真实运行验证 | 历史失败保留；最终 JWT CE PASS 仍不等于产品 PASS |
| 生产路径通用 CE + Product Validation | 六类能力与六题陌生工程 PASS | 支持本机体验范围接受 |

## Design variances absorbed

- Prompt 禁止 Tool 不能证明隔离，改为 Provider/Adapter 机械 no-tools 与绑定 Receipt；
- 模糊 Target 改为 exact Canonical Build Target 与 Coverage；
- 相关知识存在改为逐 Need/Joint Support Proof；
- 答案审核不再读取来源或与生成共享上下文；
- 单次 Candidate 发布改为正式前提和原子 Snapshot 路径；
- CC、CE、Product Validation 与 Activation 被拆成独立门禁。

这些结论已提炼进 current Invariants 和 Contracts。完整阶段性原件由基线 `476517b` 按原路径保存：`docs/validation/architecture/Architecture_Validation_Log.md`、`docs/validation/architecture/Architecture_Capability_Formal_Mapping_Audit_001.md`、`docs/validation/architecture/Architecture_Capability_Formal_Mapping_Audit_002.md` 和 `docs/validation/architecture/Architecture_Feasibility_Review_JWT_002.md`；使用 `git show 476517b:<原路径>` 读取。

## Limitations

历史 Demo 与生产实现是不同代码入口，测试结论不能互相替代。未验证的多 Scope、Schema Evolution、Semantic View、生产部署和长期模型泛化仍不属于当前能力。
