---
id: FINDING-010-022
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [quality, engineering]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-020, FINDING-010-021]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: individual
disposition: retain-sixth-v-web-000-budget-closed-run-as-permanent-verification-evidence
target: ITER-010-VERIFICATION
---

# FINDING-010-022：7-call exact grant 正确预留审核，但不足以完成代表题调查

## Observation

Prompt `@5` 与 exact call-reserve 修复后的 clean candidate
`d6d8d02136ea5a4b41374b3de022ef8ac890c24e` / tree `28dbbbb27d8a68708b1996a0c643314068f8fbb1` 使用剩余 7-call
上限执行第六次 `V-WEB-000`。模型依次完成：

1. Question Understanding；
2. SOURCE literal search `JwtTokenUtil`；
3. READ `JwtTokenUtil.java`；
4. READ `JwtAuthenticationTokenFilter.java`；
5. READ `CommonSecurityConfig.java`。

四个 Investigation Proposal 都包含当前 `required_basis_entry_id`，三个 READ 都从当步 `eligible_locator_references` 选择不同的 opaque
locator；4 个 Broker decision 全部 `POLICY_COMPILED / AUTHORIZED`，`no_progress_steps=0`。模型仍未调查 mall-admin 登录实现和测试证据，因而
没有提前 FINISH 或缩减 Checklist。

Request 的 exact total-role limit 为 7。第 5 个已消费角色调用返回后，下一轮 Investigation 前的 reserve 判定为 `5 + 3 > 7`，Application
以 `INDEPENDENT_REVIEW_RESERVE_EXHAUSTED` 失败关闭，没有发起第 6 个 Provider dispatch，也没有生成 Draft 或伪造 Review。页面 Result 为
`FAILED_CLOSED`，`answer_attempts=0`、`review_attempts=0`。

## Evidence

- request digest：`sha256:1887ffa6bead02a8be0fc7332dfed947b5d255fe84c7c4c5d6967049d57d4790`；
- evaluation subject：`sha256:548dd815665865017f0e9cc859b32433abb116b596cfe007adb891e6c061ac7d`；
- run authorization：`sha256:516a18aa5b66006cf650f35399327ab8e57cf69180a134331f467305f917f2dc`；
- terminal receipt：`sha256:47e0ed72ea9e04aed17cb91601e46cbbbbe7135f20447b4818c2e0979be96025`；
- 5 次 dispatch 全部 Gateway `COMPLETED`，retry/provider switch 0；TLS handshake 1、connection reuse 4；
- Source operations 4、source bytes 56,669、source files 15、no-progress 0；
- Production Activation `NOT_EXECUTED`。

此前 5 次 Web run 共 19 次 role dispatch，加本次 5 次为 24；另有 2 次 current qualification call，所以用户授权的累计调用为 26/28，
剩余 2 次没有使用。

## Classification and disposition

这不是把 Answer/Review 挤出预算的实现失败：`FINDING-010-021` 的绑定和 reserve 正确工作，且 `FINDING-010-020` 的动态 investigation
controls 在真实模型输出上成立。该代表题的 material conclusions 在 4 次 Investigation 内尚未完成，按 Manifest 禁止因剩余调用数裁剪证据、
Checklist 或独立 Review，因此正确 verdict 是 `V-WEB-000 FAIL / blocking`。

该事实分类为 `verification / individual`，主要处置到 `ITER-010-VERIFICATION`。旧 run 与其 7-call grant 永久保留；不能用剩余 2 次开始一个
至少需要 Understanding、Investigation、Answer、Review 的新 Request，也不能把它们解释成 retry。继续 live 验证需要用户再次明确提高累计
上限，并为新的 clean candidate 形成 Prompt-bound exact run grant。
