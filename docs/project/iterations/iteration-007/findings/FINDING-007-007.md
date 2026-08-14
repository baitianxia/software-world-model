---
id: FINDING-007-007
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [interface, security, quality]
depends_on: [ITER-007-SLICE-001, ITER-007-RESULT-SLICE-001-PRODUCT-CANDIDATE-FREEZE-RUN-002, ITER-007-VERIFICATION]
code: [src/software_world_model/interface/world_model_runtime.py]
tests: [tests/test_world_model_evaluation_grant.py]
iteration: ITER-007
classification: verification
disposition: bind-answer-role-network-audit-to-frozen-dispatch-count
target: ITER-007-VERIFICATION
---

# FINDING-007-007：三调用 Answer 被遗留的单连接后置条件误判

## Observation

run-002 product freeze 修复隔离导入后，用户从正式 Web 发起两个独立请求。第二个请求“登录流程如何？”的 Plan、Draft、Review
三次 Provider call 全部完成，Answer 和 Gateway role report、summary 均为 `PASS`，但页面仍返回
`the isolated World Model run did not produce a verified terminal`，terminal 在 `ROLE_POSTCONDITION` 阶段失败关闭。

第一个请求“下单流程如何？”是另一条独立失败：它只完成 Plan call，Answer 以 `DomainError` 结束，没有 Answer summary。两个请求
都只有一次 controller attempt、无 retry；不能把它们合并为同一次请求的重试。

## Evidence and root cause

- run-002 freeze report digest：
  `sha256:f47fe21bdd0b56be39434dd973ef9adb5364bedf0b54f73511235b931f418cbb`；
- live grant/startup receipt digest：
  `sha256:0671865671bd482b2a09bf4b58b909c2d1c7f7c113739ae4f2ba88530a20de5a` /
  `sha256:08de90c5cb4c9cc762046368e22436639cd28f0f4add7a2a79ee39b2cd585d79`；
- 两个 terminal digest：
  `sha256:74769ae4635a3ae0933815fe8a8d56fe76ebdf5138f367c4a67dafb0ef339cbc`、
  `sha256:d924454db7c10a802829982beacca550c656a603bea97f4364a570c4ab8741be`；
- 第二个请求的 Answer/Gateway summary digest：
  `sha256:12951cf6ff597f3179773e2826389c34ed3643adb77bed07cb799c14ceafca94` /
  `sha256:9640c9ff368007ed1af61aada932f09c09bbe968f7c78442dc3318d70c9bd50a`；
- 第二个请求 Gateway database 有三个 `COMPLETED` model call，Answer role audit 正确记录 `unix_connect=3`，全部禁止项为 0；
- `_run_one()` 已从 frozen Gateway input 得到 `gateway_call_count=3` 并交接三个 Provider socket，但
  `_verify_role_success()` 仍把 Answer `unix_connect` 固定为 ITER-003 遗留值 1。因此所有成功完成三调用的 ITER-007 Answer 都会被
  系统性误判；这不是前端、题目、Source、模型、Provider 或凭据故障。

## Decision and disposition

role audit helper 改为要求调用方显式传入 exact `expected_unix_connect_count`。Answer 使用同一 `_run_one()` 已从冻结输入推导的
`gateway_call_count`；Gateway 与 Projector 显式传 0。helper 拒绝未知 role、负数/非整数，以及非 Answer role 的非零连接期望。
这样旧单调用 Profile 继续要求 1，ITER-007 三调用 Profile 要求 3，不再存在独立硬编码的协议副本。

回归测试用真实 role-report shape 证明 `unix_connect=3` 在期望 3 时通过、在期望 1 时失败；既有 Answer/Gateway 三调用摘要
后置条件测试继续保留。run-002 freeze、两个请求和失败 terminal 永久保留；修复必须形成新的 product freeze，旧 post-freeze
授权、session 和已披露问题不得改写为新冻结的通过证据。

## Verification after disposition

- 新增 audit regression 与既有三调用后置条件测试 2/2 PASS；
- `test_world_model_evaluation_grant`、Gateway authorization、Slice freeze 相关测试 14/14 PASS；
- run-003 freeze 在 workspace sandbox 的 full 912 项中因 AF_UNIX `EPERM` 产生 6 errors/1 派生 failure，未形成 report 且已保留；
  同一 producer 的受影响测试在允许 AF_UNIX 的执行面 7/7 PASS；
- replacement run-004 freeze 在允许 AF_UNIX listener 的执行面以 focused 67/67、candidate package 25/25、full 912/912、
  docs 和 unauthorized-prelisten 全部 PASS；report digest
  `sha256:07f3431e919706f3c9a6fbe601906d7dd2c5532b53032b3fbefb5702cef725fe`；
- 正式 Web 复验仍待 run-004 post-freeze 用户授权。
