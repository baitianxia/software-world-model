---
id: ITER-010-RESULT-V-LAYER-ATTRIBUTION-001
kind: iteration-result
status: passed-diagnostic
authority: execution-evidence
owners: [application, knowledge, source, ai, quality, interface, project]
depends_on: [ITER-010-PDR-005, ITER-010-VERIFICATION, FINDING-010-130, FINDING-010-132, FINDING-010-133, FINDING-010-134]
code: []
tests: []
iteration: ITER-010
case_id: V-LAYER-ATTRIBUTION-001
case_verdict: PASS
external_model_calls: 0
acceptance: NOT_ACCEPTANCE
production_activation: NOT_EXECUTED
---

# ITER-010 V-LAYER-ATTRIBUTION-001 离线逐层归因 Result

## Verdict

`V-LAYER-ATTRIBUTION-001: PASS / diagnostic-only`。run-042 的行为、失败和职责事实最早在 **Knowledge
construction/admission** 缺失：唯一 World Model authority 只有 Maven 模块和依赖。该缺失随后被 question-independent Cognition 整包投影；同一
run 还独立存在 Agent 未读取决定性源码、Evidence Package 缺项，以及 Reviewer 放行不完整 Limitation 或扩大问题范围的守门故障。现有 Web
忠实显示已授权 Result/失败，没有 display first divergence。

本 Result 只密封责任层，不证明新 Cognition、答案质量、Provider、Browser、Comparison、Acceptance 或 Production。归因期间没有修改
Prompt、答案 Schema、Tool policy、Source query policy 或 Reviewer，也没有发起外部模型调用。

## Exact evidence freeze

- product：`3b8d09c71796e3c9b91ec6a9ea21697497319bbc` / tree
  `6728a5ad63bedf65b1315cb7d7fdf27f111dc0d9`；source：
  `mall@0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` / tree `047d79d8588b76013c260f3f1a9565707301a60a`；
- Session/terminal SHA-256：`6d7f07509df62e8aa1ffc0dbeed060ec7b65791ae9580b77b29da22a22585dc3` /
  `74456d732d97af7d2de63f9993ef82bb053bf9317f3883113e8ed1cec4bb2e9e`；terminal receipt digest
  `sha256:201f984bc08aa68e640a0b3b431787e78f6b3aaa2354f9073766767a180bab5b`；
- Ark/DeepSeek Gateway DB SHA-256：`0d00129071815496a4cd77698901a650c71e206c519fb5df051f22c0e496c831` /
  `3737567921fed8a7d0980fae2150b12baef127d333fd2af307a0138ebd4d0605`；WAL 均为空；只读查询得到 12/31 个 logical model call，
  terminal 总计 43、retry 0；
- ordered/Snapshot file SHA-256：`b54233af8f259fe23bcd27d1d16c4902401cd525b824476e1684325fe794de39` /
  `02f094a8d816e2466ce34c44bd23c17e254ad6d0b73564e66395152ff4d3ad87`；Snapshot
  `structure_snapshot_5033a7fc944141d08ecd5ad3879ce1ba`、Bundle
  `sha256:aba230958a990ed7e7a2f8069a34de50e23bd35b6e4dcf274189c3cb1b9b6b6a`；
- Snapshot 只有 8 个 `SOFTWARE_SYSTEM/MAVEN_MODULE` Entity、15 个 `CONTAINS_MODULE/DEPENDS_ON` Relation、0 Literal；记录的
  Cognition 对各行为问题都返回相同 34 项，并明确写出 `Projection is question-independent`；
- exact Source truth：`UmsAdminController.java:57-68` 定义 `/admin/login`、失败消息及成功 token/tokenHead；
  `UmsAdminServiceImpl.java:99-118` 定义认证、token、成功登录审计以及 `LOGGER.warn("登录异常:{}", e.getMessage())`；
  `SecurityConfig.java:60-62` 接入 authentication entry point、access denied handler 与 JWT filter；两个 handler 分别写出
  `CommonResult.unauthorized/forbidden`，`ResultCode.java:11-12` 将应用响应 code 定义为 401/403。handler 没有设置 HTTP status，故本报告
  不把应用响应 code 扩张成 transport HTTP status。

## Per-material-fact chain

| Question / material fact | Source truth | Construction / admission | Cognition projection / query | Conversation understanding | Agent investigation | Package / Answer | Review | Web | First divergence and later faults |
|---|---|---|---|---|---|---|---|---|---|
| Turn 1 原题：登录请求的认证、失败与成功流程 | Controller 只覆盖入口/返回；Service 实际拥有认证、token、失败 warn 与成功登录审计 | Maven Snapshot 无方法、分支、调用或 side effect | 34 项 Maven 整包与题无关；行为 Coverage 明确缺失 | 目标“登录流程”正确保留 | 读 Controller/JwtTokenUtil，未读 Service implementation | 局部流程 Draft；一版还无据声称 HS512，最终未交付 | 正确拦截 HS512，但反复要求超出已取证范围的细节，review limit | 页面如实显示失败 | **construction/admission**；另有 Agent investigation、Answer synthesis 和 Review scope 故障 |
| Turn 3：用户纠正为“认证失败，不是权限不足”后，失败时记录什么 | Service `catch (AuthenticationException)` 记录 `登录异常:{message}` | 同上，行为事实未入 Snapshot | 同一 34 项；没有 failure/log behavior | correction message 被接受，目标没有错绑为权限不足 | 只搜索 `AuthenticationException/BadCredentialsException/AuthenticationFailureHandler`，均在 fuse 内零命中；未读 Service | Package 无决定性实现；交付“无法确定” Limitation | 面对 PARTIAL/fuse 与仍开放的 material need 直接 `APPROVED` | 页面忠实显示 reviewed Limitation | **construction/admission**；另有 Agent 未换路径/读实现、Package 缺项、Reviewer 未阻断不完整调查 |
| Turn 4：401/403 应用响应 code 分别由谁产生 | authentication entry point → unauthorized(401)；access denied handler → forbidden(403)；SecurityConfig 接线 | 同上，handler/wiring/response code 均未入 Snapshot | 同一 34 项；无行为或 Literal | 正确解析 401/403 和先前纠正 | 只做数字 `401/403` 搜索，未读取 config、handler 或 ResultCode | Package 无决定性实现；交付“无法确定” Limitation | 对未读授权来源与 terminal search boundary 直接 `APPROVED` | 页面忠实显示 reviewed Limitation | **construction/admission**；另有 Agent investigation、Package 和 Reviewer guard failure |
| Turn 5：只保留用户能看到的登录流程 | Controller 足以支持 POST、失败消息、成功 token/tokenHead，并明确只覆盖后台 API | 行为事实仍未入 Snapshot | 同一 34 项，但 Source 已补足当前题最低事实 | 目标已收窄为用户可见结果 | 读取 Controller | 三项 Draft 均有同一 full-content Source 支持且披露没有前端证据 | 三项均判 `SUPPORTED`，却新增“必须给页面导航/表单/UI”的范围并要求新证据；后继失败 | 页面如实显示终态失败 | 本题可交付 Draft 的首个偏差是 **Reviewer scope expansion**；更早 Cognition 缺口仍存在但已被 Source 补足，不是该 Draft 的致错层 |

同一问题允许多个故障。表中的 first divergence 指该 material fact 在现有链中第一次偏离 Source truth 或用户目标的位置；后续错误没有被上游
标签吞并。

## Controlled layer substitutions

所有替换都重放现有 immutable records，Provider/model dispatch 增量为 0；它们不是新的模型质量试验。

| Arm | Frozen substitution | Observation | Attribution |
|---|---|---|---|
| World Model only | 保留 run-042 exact Maven Context，移除 Source observations | 三个行为/失败/职责问题都只剩模块和依赖；无决定性非-locator 结论 | Maven Profile 正确但对这些 Need 不合格；construction/cognition 是首个 Owner |
| same-Agent source only | 固定已记录的 Agent action sequence 和 Source results，移除 Maven observation；不重新采样 Agent | Turn 1 只有局部 Controller/JWT；Turn 3 未读 Service；Turn 4 无 full-content read | 无关 Maven 整包不是 Agent 漏读的原因；Agent investigation 是独立下游故障 |
| same-Agent eligible-cognition + source | 固定同一 action/Source trace，以 exact Source truth 形成仅供归因的 behavior-oracle items 注入；明确不把它们追认为正式 World Model | 三个 material fact 的决定性内容均可进入 evidence set | 若正式 Cognition 有这些 supported dimensions，知识缺失可被隔离消除；该 oracle 不是 `V-COGNITION-ELIGIBILITY-001` PASS，下一 Gate 仍须真正 Read Authority/Manifest |
| complete-evidence bypass | 绕过调查选择，把上述 exact Source excerpts 直接作为完整 Package oracle | 登录失败 warn、成功审计、401/403 handler ownership 和后台用户可见结果均可逐 claim 机械支持 | Source truth、Broker read 与 Package/Answer 数据通路可承载事实；现有缺项不是“源码没有答案” |
| Reviewer seeded bad/good | bad：在完整 Package 下提交“无法确定”；good：提交逐 claim 绑定 exact excerpts 且不扩张 transport/UI 的 Draft | bad 必须因与 Package 冲突/不完整而拒绝；good 可通过。实际 Reviewer 在 Turn 3/4 放行不完整 Limitation，并在 Turn 5 扩域 | Reviewer completeness/scope guard 是独立下游故障；不因此把 Prompt/Review 当成最早 Owner |
| authorized Result → Web | 对照 terminal/Turn Result 与已保存页面状态、console 与 listener evidence | 页面显示的成功、Limitation 与失败与内部 Result 一致；无 console/display mismatch | Web 不是 first divergence；当前不修改页面壳 |

`same-Agent` 在此严格指“固定 run-042 已记录 action trace 的离线重放”，不声称移除或注入 Cognition 后模型仍会选择相同行为。这个限制避免用
零调用反事实伪装新的 Agent 实验；它不影响“知识层最早缺失、Agent 与 Reviewer 又各自失败”的归因。

## Decision and next owner

最小合法产品改动进入 Knowledge/Application cognition owner：在同一 exact revision 上建立结构+实现/行为的 profile-specific Read
Authorities、Capability Manifest、Question Eligibility 和问题相关只读投影。现阶段继续冻结 v7 Prompt/Reviewer 症状实验，不修改 Web，且不取得
Provider/live 资格。

下一阻断 Case 是 `V-COGNITION-ELIGIBILITY-001`。它必须用真正的正式 Snapshot/Read Authority 取代本报告的 behavior oracle；Source
后续命中仍只能作为 Turn Evidence，不能回填为 World Model contribution。
