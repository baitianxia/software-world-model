---
id: SYS-ADR-019
kind: system-decision
status: accepted
authority: normative
owners: [architecture, application, security, ai, operations, quality]
depends_on: [SYS-ADR-006, SYS-ADR-017]
derived_from: [FINDING-010-029, FINDING-010-140]
code: [src/software_world_model/application_services, src/software_world_model/ai_infrastructure/model_gateway.py, src/software_world_model/interface]
tests: [tests/test_model_gateway.py, tests/test_world_model_evaluation_grant.py, tests/test_world_model_gateway_authorization.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_chat_provider_runtime.py]
---

# ADR-019：公开来源采用持续模型调用权威

## Context

本机方向体验使用固定版本的外部公开开源工程，模型 Provider route、credential account、披露类别、只读来源边界、预算和
`EVALUATION_ONLY / loopback` 环境也已经由人确认。在这些边界没有变化时，要求人再为每个 run、Turn、Agent step、Reviewer step 或
Provider dispatch 逐次批准，并没有增加新的授权判断；它只是把系统本应完成的 exact identity 和审计派生转嫁给操作者，阻断连续 Chat
和快速方向验证。

但取消逐次人工确认不能取消逐次控制。来源内容仍可能含 prompt injection；Provider input 仍须按实际 payload、purpose 和预算逐次密封；
私有、来源不明、dirty 或仅存在于本机的数据也不能因为位于“测试工程”目录而被推定为公开。

## Decision

1. 人可以一次建立 `PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY@1`。它只覆盖满足下列全部条件的闭合范围：
   - 来源由受信 Source Authority 证明为公开可获取的开源仓库，绑定 canonical upstream identity、许可/公开性记录、允许的 revision
     selection policy、允许路径/内容类别和排除项；每个实际 run 仍须冻结并验证 clean exact commit/tree 与 local mirror；
   - 外发只包含该公开 exact revision 的 allowlisted 只读来源投影、从中形成的 World Model Cognition/Evidence，以及用户在该体验中主动
     提交且未引入更高敏感级别的数据；
   - Provider/model/endpoint/Adapter/credential account、资格、redaction、Agent/Reviewer purpose、有序 route、每 Turn/整会话预算、
     有效期和撤销条件已经明确批准；
   - Sink 固定为 `EVALUATION_ONLY` 的 loopback 本机体验，不执行外部写入或 Production Activation。
   ITER-010 的 `PUBLIC_OSS_EVALUATION_STANDING_AUTHORITY@1` 是该通用合同在当前 mall 评测范围内的项目实例，不是第二套权限语义。
2. 在该持续权威内，用户提交 Turn 即表达本 Turn 的产品请求，不构成新的运维审批。可信 Application 必须从持续权威、exact Turn、相关
   Conversation/Cognition/Work State、当前 Evidence Package、Provider attempt、qualification、预算和调度状态，自动派生 exact
   Session/Turn/run authority、Authorized Input Manifest、one-use disclosure/dispatch receipt 与 terminal audit。派生对象是逐次、不可复用、
   可追溯的机器控制和审计记录，不是等待人签发的审批单；它们不得扩大持续权威。
3. 人工只在发生 material authority delta 时重新决定。需要人工 delta 的事件精确为：
   - 来源或 payload 包含 private、unknown-origin、dirty/uncommitted 或仅本机存在的数据；
   - 新增或改变 Provider、model、endpoint 或 credential account；
   - 扩大已批准的 calls、tokens、duration、Conversation/Turn 或成本预算；
   - 绕过当前 execution profile 所选 admission plugin 的 exact policy override；
   - 任何外部写入、副作用或可变远端操作；
   - 非 loopback 暴露或 Production Activation。
   exact revision、公开性证明、许可/来源记录、allowlist、资格、有效期或 authority chain 无法验证时属于 unknown，必须在读取 credential、
   建立 Provider 网络或披露 payload 前失败关闭，不能自动猜测或降级。
4. 以下控制不因持续权威而改变：每次模型调用的 exact Manifest/receipt/Usage/transport/cost 审计；Provider 内零 request retry；独立
   Reviewer 与完整质量链；exact revision 和只读 Broker/Worker；Source 内容按不可信 data 处理并抵抗 prompt injection；Secret 隔离；
   disclosure redaction；calls/tokens/time/no-progress 熔断；Provider 资格与身份重验；失败关闭；ADR-017 attempt 隔离；以及所选
   admission plugin 的逐 request policy 校验。符合插件策略的 admission 可由可信系统从持续权威自动派生；插件要求 override 时仍必须有
   本次 exact 人工决定。
5. 历史 Conformance、Capability Qualification、Product Result、用户曾经查看过某仓库，或仓库名称中出现“open source”都不能自行
   创建持续权威。持续权威必须可撤销、可到期并绑定可验证 source/provider identities；任何 drift 只阻断受影响的新 dispatch，不能改写
   已密封审计结果。同一已批准公开 upstream 与 revision policy 内的新 clean exact commit 由 Source Authority 重新验证并由系统派生
   新 receipt，不是人工 delta；变成不同来源、无法证明公开或超出 standing policy 时才按 unknown/新边界处理。

### 当前 ITER-010 配置实例

当前 execution profile 配置把 DeepSeek 映射为备用路线，并选择 `DEEPSEEK_DISPATCH_ADMISSION@1` 作为其 admission plugin；该插件把非高峰
窗口作为自动准入条件、把峰时运行作为 exact override。该映射只描述当前可替换配置，不定义本 ADR 的权限状态、分支或质量规则。

## Consequences

- 公开开源测试工程上的正常 Chat、canary 和评测不再因 run/Turn/dispatch 数量重复向人申请同一权限；系统仍为每次真实调用留下更精确的
  审计链。
- “人工授权”与“机器派生 receipt”成为不同概念：前者决定边界及其 material delta，后者执行和证明边界。
- 系统必须可靠证明公开来源分类并检测 authority drift；做不到时按 unknown 处理，而不是把本机目录默认当成公开数据。
- 现有要求 post-freeze exact user-message grant 的 launcher/artifact 是兼容实现，不再是公开来源体验的目标产品契约；后续实现必须以
  standing-authority ref/digest 和自动派生链取代逐 run 人工消息依赖。在该实现和确定性验证完成前，不得把本 ADR 写成 live 能力。

## Rejected alternatives

- **每次 Provider 调用都要求人工批准。** 重复相同判断，无法支持自然 Chat，也没有替代逐次机器审计。
- **公开仓库调用完全不做授权或 receipt。** 无法约束 Provider、预算、payload、调度和 prompt injection，且不能识别私有数据混入。
- **把所有本机 Git 工程都视为公开。** local/dirty/unknown 数据的公开性无法由 Git 形态推出。
- **持续权威同时覆盖 admission-plugin policy override 或生产。** 运行策略例外和部署风险是新的 material decision，必须单独由人决定。
