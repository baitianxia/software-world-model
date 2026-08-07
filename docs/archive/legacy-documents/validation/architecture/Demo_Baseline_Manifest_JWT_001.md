# JWT Commit 架构能力 Demo 基线清单 001

| 元数据 | 值 |
|---|---|
| Manifest ID | `SWM-DEMO-BASELINE-JWT-001` |
| Status | `Frozen for Harness Implementation — Run Configuration Pending` |
| Validation Slice | `SWM-ACV-SLICE-JWT-001` |
| Runtime State | `NOT_RUN` |
| Production Authorization | `NONE` |
| Frozen Date | 2026-08-05 |

> 本清单只授权JWT验证Harness的Conformance实现。它不授权完整Capability Run、Iteration 001生产编码或任何production Registry / Snapshot写入。

## 1. 冻结文档

| 产物 | 规范身份 | 文件SHA-256 |
|---|---|---|
| [JWT Validation Formal Contract](../../implementation/iteration-001/contracts/ITER-001-JWT-Validation-Formal-Contract.md) | `0.1.0 / payload sha256:468db1c92419faad5e66597496c2103c92d83331ab28a9a01e90e108072f36b9` | `821141f8dc8fbaaaafe7cdd49e4232d940dca32f43892c17a6ae4ff7472ca3bd` |
| [JWT Architecture Capability Validation Slice](Architecture_Capability_Validation_Slice_JWT_001.md) | `SWM-ACV-SLICE-JWT-001` | `fcd96cf619a3c6825918c14a129880d69a6da2fc612877419cfb187c25f428fc` |
| [JWT Formal Mapping Audit 001](Architecture_Capability_Formal_Mapping_Audit_JWT_001.md) | `6 / 6 STATIC SUPPORTED` | `6e6ddf05753b8a03698c596788400c74dc878892d24f4dfbe015ed74f1e568cb` |
| [Base Knowledge Schema](../../implementation/iteration-001/contracts/ITER-001-Initial-Knowledge-Schema.md) | `iter-001.initial.1 / payload sha256:1ba1a4090032464b4970bbc13a2a29685bb5b7f5d00fbf35b5da914e266c64fa` | `7dfb27cfc8d9652f97c64d466a01662521870c08cc868e97fc4d0a442342a494` |
| [Local Git Provider Profile](../../implementation/iteration-001/contracts/ITER-001-Local-Git-Provider-Profile.md) | `0.1.0 / payload sha256:d1eacb1e2c61c160c239b840cc84d660fef9fe282acd465358ae41f07bf76d1f` | `24cd748572ef69dd2bddd2b4a0f157288b6ce55aa32becba694fa160b8e0d855` |
| [OpenAI no-tools Adapter Profile](../../implementation/iteration-001/contracts/ITER-001-OpenAI-No-Tools-Adapter-Profile.md) | `0.1.0 / Conformance Required` | `f222ea0b86db6994db2f09baa2f9ad44cd4dd8b7746b88ef09573410db8add60` |
| [Product Holdout Baseline](../product-value/Product_Value_Holdout_Baseline.md) | `PV-HOLDOUT-001` | `d5ebc4921fcddbfdf942f7bf2a63fb4a396237a242af858530285c56a33a0587` |
| [Holdout Errata](../product-value/Product_Value_Holdout_Baseline_Errata.md) | exact Errata | `4e68e70cf9b96fc832416612c0e5cc645fadb1e32d828cc189df16b4bc506984` |

文件发生任一字节变化时，本Manifest立即`STALE`；不能只重算摘要后继续运行。规范修改必须发布新的Contract / Manifest revision。

## 2. 冻结来源与问题

| 项 | 值 |
|---|---|
| Repository | `https://github.com/macrozheng/mall.git` |
| Local validation project | `validation-projects/mall`，仅作为Provider注册输入，不进入知识身份 |
| Target Commit | `dacce5f28dfc1734f2db09668d928d7fac2a3a7a` |
| Parent Commit | `00bd03591cfd91f82ebe48787315eed613754277` |
| Target Tree | `1a39a7d550ce802f46b68ca56a59362b09b5bdbe` |
| Requirement | JWT验证切片§2的冻结问题与`JWT-N01…JWT-N06` |
| Direct comparison | H-04冻结10分量表；Direct Agent只作为外部Oracle，不进入被测输入 |

这些值可以作为BuildTarget实例，不能成为Type、Predicate、Rule、Builder或Answer模板分支。

## 3. 已满足的Harness开工条件

- 验证对象已经缩小为一个Commit影响分析纵向切片。
- 六个Need均有Fact / Inference / Unknown / Sufficiency正式承载路径。
- Formal Contract Payload、三个冻结依赖及文件格式已机械复核。
- Source Tool Loop、no-tools输入隔离、Fact先发布、Inference后构建、来源关闭回答和独立Answer Review均有closed对象。
- 历史33/33结论已撤回；三个宽范围候选契约已标记`Withdrawn Draft`且不在本清单依赖图中。

## 4. Harness必须先完成的工作

Harness只能按Formal Contract §12依次实现并运行12个Conformance Case。实现不得包含：

- H-04、JWT、目标Commit、文件名、类名、库名或黄金答案专用Builder / Predicate /分支。
- 直接源码回答、答案阶段Source读取、Direct Agent兜底或双路径择优。
- Fixture冒充真实模型能力；Fixture只允许用于单个机械门禁反例。
- 对已撤回Provider 0.2、Rule Pack或Schema Revision 002的运行时依赖。

Conformance结果必须记录Harness实现Commit、每个Case输入摘要、预期 / 实际Outcome和完整失败轨迹。任一Case失败时停止，不执行完整Capability Run。

## 5. 完整Run前仍需冻结

以下内容有意不在文档设计阶段预选，必须在Conformance通过后形成独立`JWT Run Configuration 001`：

- exact model / provider配置与实际模型身份政策。
- 七个Model Role各自的Capability、Strategy、Prompt和strict Output Contract。
- Tool / file / byte / model-call / duration / cost预算。
- validation Store、CURRENT namespace和Telemetry sink实例身份。
- Oracle评分执行者与独立核对记录。

Run Configuration只填充Formal Contract已有字段，不能新增类型、放宽Role输入或改变六个Need。若配置需要改变Contract，必须先使本Manifest Stale并回到设计复核。

## 6. 下一动作

允许：实现JWT验证Harness的12个通用Conformance Case。

禁止：运行完整JWT Capability Demo、解除Implementation Hold、开始production编码、声明架构能力或产品优势已经通过。
