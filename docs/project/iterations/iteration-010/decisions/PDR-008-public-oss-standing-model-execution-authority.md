---
id: ITER-010-PDR-008
kind: project-decision
status: accepted
authority: project-decision
owners: [product, project, engineering, quality, ai, security, operations]
depends_on: [ITER-010-PDR-005, ITER-010-PDR-006, ITER-010-PDR-007, FINDING-010-140, SYS-ADR-019]
code: []
tests: []
iteration: ITER-010
decision: REWORK
rework_strategy: PUBLIC_OSS_STANDING_HUMAN_AUTHORITY_WITH_AUTOMATIC_MACHINE_RECEIPTS
decision_ref: local-user-message-utf8:sha256:6dd1e3f4c444b69539f2c9082e26f605d4b0ff84b5dcf99cfb53b42cdb334bdb
effective_scope: ITER-010-SLICE-001-public-mall-evaluation
coding_input: true
---

# PDR-008：公开开源测试工程采用持续执行授权和自动机器收据

## Context

ITER-010 当前测试工程是公开 Apache-2.0 项目 `https://github.com/macrozheng/mall.git`，测试 revision 固定为 clean
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` / tree `047d79d8588b76013c260f3f1a9565707301a60a`。活动 Slice 已由用户授权，
目标就是在该工程上开发、运行并验证可体验问答。此前计划却在每次 successor canary 前再次要求 external human grant，把必须逐运行生成的
审计收据误当成必须逐运行取得的用户同意。`FINDING-010-140` 将其归因为权限模型错误。

本决定不取消 exact identity、只读 Source、披露、预算、Provider qualification、DeepSeek 闲时、零同 Provider retry、完整 Review 或
Production 边界。它只明确两层权威：人类对稳定范围作出持续授权，机器对每次具体执行自动派生并核验一次性收据。

## Decision

### 1. 当前公开评测范围具有持续 human authority

建立 `PUBLIC_OSS_EVALUATION_STANDING_AUTHORITY@1`。它是 `SYS-ADR-019` 的
`PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY@1` 在 ITER-010 mall 评测中的项目实例，不创建第二套权限语义，至少绑定：

- 当前 Iteration/Slice、已接受的体验优先方向和用户 root authorization；
- source origin、Apache-2.0 license、current exact commit/tree、同一 approved upstream 内的 clean revision selection policy 与只读要求；
- Ark→DeepSeek current route、允许的 model/configuration/credential reference 和 qualification；
- 可披露的源码/世界模型/对话字段、redaction、结果保存位置和安全边界；
- 每 run/Turn 和总 Session 的最大 calls、tokens、duration、retry 与完整质量链；
- DeepSeek PDR-007 时间门禁，以及 hidden、Slice2/3、Production 等 exclusions。

在上述字段没有 scope delta 时，现有 Slice/root 开发授权就是持续 human authority。clean product successor、run identity、Turn identity、
dispatch identity、同一公开工程上的方向 canary 和收据刷新不要求再次询问用户。

### 2. 每次执行继续使用自动派生的机器收据

运行时仍须在任何 Source disclosure、credential resolution 或 Provider network 前，由 current standing authority 自动派生 exact run authority；
每个 Turn/dispatch 再从该 run authority 派生 one-use machine receipt。收据必须绑定并核验 exact product/source/session、Provider/model、
角色/input digest、disclosure、预算、时间、fallback reason 和父 authority digest。

缺失、过期、已消费、identity/budget/disclosure/time 漂移的机器收据必须在对应副作用前失败关闭；实现不得静默放宽字段，也不得通过人工
重复批准来掩盖派生逻辑缺失。自动派生只消除重复人工审批，不降低可审计性、最小权限或 fail-closed 强度。

### 3. Ark 与 DeepSeek 的 current 执行规则

- Ark：standing authority、current qualification、route/budget/disclosure 与 exact machine receipt 有效时，无需新人工批准即可执行；
- DeepSeek：除上述条件外，还必须满足 PDR-007 的 allowed window、fresh official check、Ark terminal fallback reason、逐 request 时间复验和
  完整质量链预算；满足时无需新人工批准；
- DeepSeek 峰时：standing authority 绝不构成 peak override，仍需绑定 exact Provider/model/run/Turn/reason/calls/tokens/duration/expiry 的
  一次性用户授权；
- 等待 DeepSeek 窗口时继续 Ark/local 工作，不能因没有 peak override 停止整个开发。

### 4. 只有真正 scope delta 才重新申请

下列变化超出 standing authority，必须按 PDR-006 在 exact freeze 后直接申请最小 delta：私有/未知/仅本机或 dirty 来源、不同 upstream
工程、新增或改变 Provider/model/endpoint/credential account、扩大源码/资源/World Model 披露、超过冻结 calls/tokens/duration、DeepSeek
峰时 override、hidden evaluation、Slice2/3、写操作、非 loopback 部署或 Production Activation。审批后自动续跑，不再请求第二次确认。

产品代码 successor、模型调用的 run/Turn/dispatch 编号变化、同一范围内的失败后通用修复、current qualification/official-check 刷新和机器
收据重建本身不是 scope delta。同一 approved upstream 与 revision policy 内的新 clean exact commit 经 Source Authority 重新验证后也只需
重派生收据；未验证的 revision drift 必须失败关闭，但不自动变成人工审批。exact identity 仍在 standing authority 的显式集合内时，系统
重新派生收据即可。

### 5. 当前入口和验证

新增 `V-PUBLIC-OSS-AUTHORITY-001`：

- 正向证明同一公开 mall revision、current Slice、Ark current route/budget 的 run/Turn/dispatch 能从 standing authority 自动派生完整收据，
  人工审批请求计数为 `0`；
- 正向证明 DeepSeek 在 PDR-007 允许窗口和合法 fallback 下同样自动派生；
- 负向证明 private/unknown/different-upstream source、未验证 revision drift、Provider/model/endpoint/account drift、预算/披露扩大和
  DeepSeek peak 均在网络/凭据/Source disclosure 前失败关闭；另证明同 approved upstream/policy 的新 clean commit 经 Source Authority
  复核后无需人工批准即可重派生，二者都不自动扩大 standing authority；
- 证明 parent/child digest、one-use/expiry/consumption、terminal reconciliation 完整，历史 grant/run 不被改写；
- 不运行 full regression，不把测试收据当成 live evidence。

该 Case 的文档与设计现已闭合，但 runtime 自动派生尚未由执行证据证明，因此保持 `NOT-RUN / blocking`，不得把“尚未执行”写成
`FAIL`。PDR-009 已修订本决定的执行顺序：完整 `V-PUBLIC-OSS-AUTHORITY-001` 不是独立开发入口，也不在方向 Gate 前单独实施；当前唯一
入口仍是零外部调用的 `ITER-010-ACTION-DIRECTION-FREEZE-001 / V-DIRECTION-FREEZE-001`。Freeze 同步产出较窄的
`V-PUBLIC-OSS-AUTHORITY-ADMISSION-001`，完整 Case 只能由后续真实 Quality/最小 Web terminal receipts 聚合证明。该状态不撤销 Slice
编码权威，也不要求再次向用户申请同一公开 mall/current route 范围的授权。

## Consequences

- PDR-006 中“真正权限 gap 才申请”继续成立，但 current public mall successor 不再是 human grant gap；
- PDR-007 的 admission/dispatch receipt 继续逐 run/逐 request 强制，只是 authorization identity 改为可追溯到 standing human authority 的
  自动机器派生链；峰时规则不变；
- PDR-009 拥有当前执行顺序：Ark 质量批次 `INVALID` 时，只能进入预注册、零外部调用、零人工授权请求、零 Provider dispatch 的统一
  DeepSeek refreeze；它不得借本决定再次请求当前 standing scope 的用户授权；
- run-035—043 的人工授权、消费、成本和失败仍是历史事实，不追溯改写；
- 本决定不声明 runtime 已实现，不授权任何新测试工程、私有源码、峰时 DeepSeek、hidden、后续 Slice 或 Production。
