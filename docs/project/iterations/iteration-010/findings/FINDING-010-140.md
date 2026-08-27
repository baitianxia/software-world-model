---
id: FINDING-010-140
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [project, engineering, quality, ai, security, operations]
depends_on: [ITER-010-PDR-005, ITER-010-PDR-006, ITER-010-PDR-007, SYS-CONTRACT-SOURCE-ARTIFACT]
code: []
tests: []
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: define-public-source-standing-model-authority-and-iteration-execution-amendment
target: SYS-ADR-019
---

# FINDING-010-140：把逐调用机器收据误当成逐次人工授权

## Observation

ITER-010 的固定测试工程不是用户私有源码。它是公开仓库 `https://github.com/macrozheng/mall.git`，许可证为 `Apache-2.0`；当前测试输入
固定在 clean commit `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`、tree
`047d79d8588b76013c260f3f1a9565707301a60a`。用户已经授权活动 Slice 开发，并反复要求开发持续到可体验交付；在同一公开测试工程、同一
已接受目的和同一受控 Provider route 内，每次向模型执行评测仍要求用户重新批准，没有保护新的用户资产或扩大新的目的，反而持续中断开发。

用户指出这种做法不合理；该消息的本地 UTF-8 摘要为
`sha256:6dd1e3f4c444b69539f2c9082e26f605d4b0ff84b5dcf99cfb53b42cdb334bdb`。该纠正不授权 DeepSeek 峰时调用、私有/非公开来源、不同工程、
隐藏评测集、生产激活或超出当前冻结预算的外部执行。

## Evidence and root cause

- 当前 Readiness/Slice root authorization 已授权为公开工程构建并验证可体验 Web 版本，Provider route 又在 Session 级固定为
  Ark→DeepSeek；这已经提供了当前目的下的人类执行权威；
- 历史实现需要逐 run、逐 Turn、逐 dispatch receipt 来绑定 exact product/source/session、披露、预算、模型、时间和结果。这些是机器可审计
  的执行派生物，不等于每一层都要重新取得人工同意；
- PDR-006 正确地区分了 Slice 开发授权与一次性 external grant，却仍把 successor canary 默认归为新的 human grant gap；PDR-007 又把
  DeepSeek 的逐 request admission receipt 与 `authorization identity` 绑定，但没有明确它可从 standing human authority 自动派生；
- 因而规划把“每次执行必须有精确收据”错误实现成“每次执行前必须再次问用户”。根因是 authority model 分层错误，不是开源许可证缺失、
  Source 安全故障或用户没有授权本轮开发；
- run-035—043 的历史人工 grant、消费和失败事实必须保留；新的 standing authority 只改变接受之后的 current/future 派生规则，不追溯
  改写历史。

## Decision and disposition

该发现的通用 System Contract 语义处置到 `SYS-ADR-019`，ITER-010 当前执行方式由 `ITER-010-PDR-008` 收窄：

- 对上述公开 mall exact revision，现有 Slice/root 开发授权构成
  `PUBLIC_OSS_EVALUATION_STANDING_AUTHORITY@1` 的持续 human authority；在 ITER-010-SLICE-001 当前目的、Provider route、披露边界和预算内，
  无需为每个 run、Turn 或 dispatch 再向用户申请；
- exact run/Turn/dispatch 仍必须密封机器收据。系统从 standing authority、当前 clean product identity、固定 source identity、route、预算、
  disclosure 和时间门禁自动派生 one-use machine receipts，并在漂移时失败关闭；“自动派生”不是“取消审计”；
- Ark 在 current route/budget 内可直接执行；DeepSeek 只有在 PDR-007 允许窗口、Ark fallback 条件和完整质量链成立时可直接执行，仍不得从
  standing authority 推导峰时 override；
- 只有真正的 scope delta 才重新请求人类授权，例如私有/未知/dirty 来源、不同 upstream 工程、Provider/model/endpoint/account 变化、扩大
  披露、超过冻结调用/token/时长、DeepSeek 峰时 override、hidden、后续 Slice 或 Production Activation；product successor 的 clean
  commit 变化、同 approved upstream/revision policy 内由 Source Authority 复核的新 clean source commit、同一问题内的 Turn/dispatch 以及
  例行收据刷新本身不是 scope delta；未验证 revision drift 失败关闭但不自动转成人工审批；
- 当前 successor 不再等待用户授权。下一开发入口是实现并验证 standing-authority → machine-receipt 自动派生 Gate，然后在合规时间窗内
  执行一个方向 canary；运行时实现尚未由本 findings 证明，必须由 `V-PUBLIC-OSS-AUTHORITY-001` 失败关闭。

## Documentation boundary

本 Finding 记录本轮项目执行合同纠正；通用 authority 语义由 `SYS-ADR-019` 拥有，ITER-010 的 current scope 由 PDR-008 拥有。当前未修改
产品代码、测试或历史 Result，也不把文档决定冒充 runtime PASS。
