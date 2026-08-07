# Software World Model Iteration 001 离线开发再准入记录 001

| 元数据 | 值 |
|---|---|
| Record ID | `SWM-IMP-DEV-REENTRY-001` |
| Status | `ACTIVE` |
| Effective Date | 2026-08-06 |
| Amends | [SWM-IMP-READINESS-HOLD-001](Implementation_Readiness_Hold_001.md) |
| Applies To | `SWM-IMP-ITER-001 / WP-1…WP-6 OFFLINE DEVELOPMENT` |
| Development Gate | `D-01 PASSED` |
| Live Integration Gate | `L-01 HELD` |
| Production Activation | `PROHIBITED` |

> 本记录只解除不依赖真实 Model Provider 的离线开发暂停，不撤销原暂停记录发现的架构能力风险，也不把离线测试解释为 Provider Conformance、模型 Capability 或产品验收。真实 OpenAI 配置只在进入真实联调时提供。

## 1. 决定与依据

`WP-0R / 0R-A` 已完成 JWT Revision 002 的 `13 / 13` 机械 Conformance、no-tools Adapter 的离线 Envelope / Recording Transport /失败分类测试和全量回归。现有证据足以支持在外部调用默认关闭的条件下实现模块边界、权威状态、Repository Port、事务、幂等和确定性业务规则；这些工作不依赖 API Key、Provider Project 或 exact Model Reference。

因此，将原先单一的“编码前全部通过”门禁拆分为：

| Gate | 目的 | 进入条件 | 当前状态 |
|---|---|---|---|
| `D-01 Offline Development Admission` | 允许实现不依赖真实 Provider 的生产代码和自动化测试 | `0R-A`完成；外部调用默认关闭；模拟实现不能签发Live资格 | `PASSED` |
| `L-01 Live Adapter Integration` | 允许向真实 Provider 发起受控测试调用 | 固定Endpoint、Project Configuration、exact Model、Prompt、Schema、Capture和凭据注入方式；执行`0R-B` | `HELD` |
| `L-02 Live Capability Validation` | 允许形成模型能力和JWT切片结论 | `L-01 PASS`后完成`0R-C`和`0R-D` | `HELD` |
| `P-01 Production Activation` | 允许激活真实模型Strategy或发布生产版本 | `L-01`、`L-02`和`0R-E`全部PASS并形成新Implementation Baseline | `PROHIBITED` |

## 2. 当前允许范围

- 按 `WP-1` 至 `WP-6` 的依赖顺序实现模块化单体、公共 Port、Owner Repository、单一逻辑 ACID Store、基础类型和确定性业务逻辑。
- 使用内存实现、录制响应或明确标记的 test double 完成单元、契约、事务和故障测试。
- 实现真实 Provider Adapter 的配置读取、Envelope构造和失败关闭路径，但默认配置必须保持禁用，测试不得发出网络请求。
- 保留运行时配置入口；在真实联调前不要求开发机保存 API Key、Provider Project 或 Model Reference。

## 3. 当前禁止范围

- 未通过 `L-01` 时向真实 Provider dispatch，或把任何模型Strategy标记为`ACTIVE`、`QUALIFIED`、`PRODUCTION_ELIGIBLE`。
- 把 test double、Recording Transport、Fixture或离线回归登记为`CC-MODEL-NO-TOOLS-001 PASS`。
- 宣称JWT Capability Run、Provider Conformance、产品Holdout或Iteration 001已经通过。
- 让模拟结果进入生产领域Sink，或为方便开发增加直接来源回答旁路。
- 在 `P-01` 之前对外发布或启用真实模型路径。

## 4. 失效与恢复

以下任一情况使 `D-01` 重新进入审查：实现绕过Owner Port写入、外部调用不再默认关闭、模拟资格可进入生产Sink、当前切片契约发生不兼容变更，或代码引入直接来源回答旁路。

需要真实模型能力时再进入`L-01`：届时配置凭据并不是继续编写普通代码的条件，而是执行真实Provider Conformance和集成验收的显式条件。`L-01`未通过不会抹除已完成的离线开发，但会继续阻止真实模型激活和生产发布。
