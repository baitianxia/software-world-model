---
id: ITER-007-RESULT-SLICE-001-LIVE-RUN-002-FAILURE
kind: iteration-result
status: failed-preserved
authority: execution-evidence
owners: [engineering, quality, security, product]
depends_on: [ITER-007-RESULT-SLICE-001-PRODUCT-CANDIDATE-FREEZE-RUN-002, FINDING-007-007]
code: [src/software_world_model/interface/world_model_runtime.py]
tests: [tests/test_world_model_evaluation_grant.py]
iteration: ITER-007
---

# ITER-007 SLICE-001 Live run-002 Failure

## Decision

替代 freeze run-002 的正式 Web 现场运行 **FAIL**。修复后的 Answer 已越过 run-001 的隔离导入失败；用户发起两个独立请求，
controller 均只执行一次、无 retry。第一个请求在 `ANSWER` 阶段以 `DomainError` 失败；第二个请求成功完成严格
Plan→Draft→Review 三调用，却被遗留的单连接 role audit 在 `ROLE_POSTCONDITION` 阶段误判。

因此两个请求都没有可交付 Citation projection 或可接受产品 terminal；`V-WEB-001`、`V-XD-001` 和用户正确性 verdict 仍未通过。

## Exact evidence

- product freeze report digest：
  `sha256:f47fe21bdd0b56be39434dd973ef9adb5364bedf0b54f73511235b931f418cbb`；
- live grant/startup receipt digest：
  `sha256:0671865671bd482b2a09bf4b58b909c2d1c7f7c113739ae4f2ba88530a20de5a` /
  `sha256:08de90c5cb4c9cc762046368e22436639cd28f0f4add7a2a79ee39b2cd585d79`；
- evaluation subject commit/tree：
  `82bf20a890907c55cea29e3e3415fa413cfe9719` / `c4c1d9c8b35a9eedd170b629b4aee68b0b44f07d`；
- first request terminal：
  `sha256:74769ae4635a3ae0933815fe8a8d56fe76ebdf5138f367c4a67dafb0ef339cbc`，
  `failure_stage=ANSWER`、Answer `failure.type=DomainError`、Gateway database 只有一个 completed Plan call；
- second request terminal：
  `sha256:d924454db7c10a802829982beacca550c656a603bea97f4364a67dafb0ef339cbc`，
  `failure_stage=ROLE_POSTCONDITION`、Gateway database 三个 model call 全部 `COMPLETED`；
- second request Answer/Gateway role report digest：
  `sha256:c94406ff0d359ca9a27d3454666f3c463f252bb692f0ec94c473b0f1e9782dd0` /
  `sha256:ae536a06d5b2a68ccb6c4f8e9ee367854f20bb312eb26d11dd896298d5764281`，两者 status 均为 `PASS`；
- second request Answer/Gateway summary digest：
  `sha256:12951cf6ff597f3179773e2826389c34ed3643adb77bed07cb799c14ceafca94` /
  `sha256:9640c9ff368007ed1af61aada932f09c09bbe968f7c78442dc3318d70c9bd50a`，两者 status 均为 `PASS`；
- Answer role audit 的 `unix_connect=3` 与 frozen dispatch policy
  `THREE_ORDERED_CALLS_PER_QUESTION_NO_HIDDEN_RETRY` 一致，禁止项全 0。

## Disposition

根因和最小修复见 `FINDING-007-007`。run-002 freeze、grant、session、两个 terminal、Gateway databases 和 role reports 全部
原地保留，不删除、不覆盖。现有 run-002 服务不得用于修复后验证；新代码必须通过相关/全量测试和 docs check，并形成新 product
freeze。新的正式 Web 模型分派仍需要匹配该新冻结的 post-freeze 用户授权。

Production Activation 与 Git stage/commit/push 均未执行。
