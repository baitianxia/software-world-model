# 验证记录

本目录保存设计实验和产品价值实验的输入、执行记录、失败与结论。验证证据可以触发设计修订，但本身不是规范。

| 分类 | 内容 |
|---|---|
| [架构机制验证基线](architecture/Architecture_Validation_Baseline.md) | 真实项目纵向 Slice 的模块职责、知识边界和控制机制基线 |
| [架构能力验证基线](architecture/Architecture_Capability_Validation_Baseline.md) | 正式知识单路径的能力守恒、架构增益和可证伪硬门禁；完整 Run 待执行 |
| [JWT Commit 架构能力验证切片 001](architecture/Architecture_Capability_Validation_Slice_JWT_001.md) | 历史窄化切片；可执行性复核后不得用于新 Run |
| [JWT Commit 架构能力验证切片 002](architecture/Architecture_Capability_Validation_Slice_JWT_002.md) | 修正后的新 Run candidate：加入 Criterion Obligation / Joint、逐 Claim Oracle、分层 Conformance 和来源访问 attempt 门禁；Live Run仍未授权 |
| [JWT 切片 Formal Mapping 审计 001](architecture/Architecture_Capability_Formal_Mapping_Audit_JWT_001.md) | 对H-04六个Need和validation-only Formal Contract从零执行的静态承载审计；不复用历史33/33 |
| [JWT Demo 基线清单 001](architecture/Demo_Baseline_Manifest_JWT_001.md) | 冻结当前Harness输入、exact摘要、目标Commit和开工/禁止边界；Runtime仍为NOT_RUN |
| [JWT 架构可行性复核 002](architecture/Architecture_Feasibility_Review_JWT_002.md) | 在真实 mall Git 对象上复核旧 Contract、登记 7 项根因、运行 13 项机械 Conformance 与来源关闭机制见证；结论为机制可实现、真实模型能力未证明、不得开工 |
| [Formal Mapping 静态审计 001](architecture/Architecture_Capability_Formal_Mapping_Audit_001.md) | H-01～H-05 的 33 项 exact Schema 映射；ACV-G02 静态预检失败 |
| [Formal Mapping 静态审计 002](architecture/Architecture_Capability_Formal_Mapping_Audit_002.md) | 候选 `iter-001.initial.2` 达到 `33 / 33` 静态支持；只恢复 ACV-G02 重新执行资格，完整 Run 未执行 |
| [Candidate-only 两阶段机制见证 001](architecture/Architecture_Capability_Mechanism_Witness_001.md) | 验证 Fact 先发布、Inference 后引用 exact Base、来源关闭恢复与失败反例；不代表完整 ACV 通过 |
| [架构验证记录](architecture/Architecture_Validation_Log.md) | 架构机制、反例、纠偏结论和架构能力验证运行状态 |
| [产品价值验证](product-value/Product_Value_Validation_Log.md) | Holdout 基线、勘误、执行记录和产品价值判定 |

Demo 实现位于仓库根目录的 [demo/](../../demo/README.md)，外部被测项目位于 [validation-projects/](../../validation-projects/README.md)。当前不得直接执行覆盖 H-01～H-05 的完整 ACV，也不得按旧 JWT Slice 001 / Contract 0.1.0 运行；必须先冻结 JWT Slice 002、Revision 002 Contract、Live no-tools Conformance 和 Direct Claim Oracle。结果不能外推到其余题目。

Demo 的验证对象是架构方案能力：正式知识单路径能否承载、约束并恢复所需语义。确定性 Fixture / Contract Driver只能验证机械门禁，不能作为当前JWT切片的能力通过证据；该切片必须由真实no-tools模型完成调查、知识Candidate和答案路径。Demo不是生产实现、直接来源回答路径或双路径兜底，也不能替代后续跨任务Capability Evaluation与Product Holdout。

`iter-001.initial.2` 候选契约集仍处于修订中。Formal Mapping Audit 002 的历史 `33 / 33` 结论已经被后续严格复核推翻，当前不得用作开工或能力证据；Audit 001和002均保留为历史审计记录。JWT Contract 0.1.0 的 `6 / 6 STATIC SUPPORTED` 也已被可执行性复核证明不足：它缺少 Criterion Obligation / Joint、Manifest Rendering闭包和Entity阶段等运行必需对象。新的 [Revision 002 candidate](../implementation/iteration-001/contracts/ITER-001-JWT-Validation-Formal-Contract-Revision-002.md) 已取得机械见证，但真实no-tools Adapter、真实模型链与逐Claim Direct Oracle仍未运行。
