---
id: FINDING-008-034
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [interface, ai, quality, project]
depends_on: [ITER-008-SLICE-001, FINDING-008-033, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-OPS-LOCAL-BROWSER]
code: [src/software_world_model/interface/world_model_runtime_assets/gateway_authorized_workload.py]
tests: [tests/test_world_model_gateway_authorization.py]
iteration: ITER-008
classification: local-implementation
disposition: code-and-tests-only-existing-integrity-contract
target: src/software_world_model/interface/world_model_runtime_assets/gateway_authorized_workload.py
---

# FINDING-008-034：Gateway wrapper 的 bounded workload integrity pin 已过期

## Observation

修复 `FINDING-008-033` 后，formal `run-005-freeze` 以 source snapshot commit/tree
`f7796993abc80c50750064dc2a83b211e3f3eb8d` / `1ab58acd457b5390c5bd6c18e0e6e897b6cf1428` PASS。report 与
authorized grant digest 为 `sha256:93200c783292c9c7971aba5ce4f7d6f5321e14a844e2b7cab390e7a830eea7ff` /
`sha256:72949de71aa3dfcd66076e5efe558b12356acdcb5a975619023ecd682060684d`；focused 88/88、candidate package 37/37，full
1030 中 1025 PASS，唯一 4 FAIL + 1 ERROR 精确属于 `FINDING-008-020`。freeze 阶段没有外部模型调用。

新 Web startup receipt `sha256:869287ecb6bbbbf5528a4bf49ef6da1cf668642ba1f4a85c17a8336c04788a00` PASS，页面也正确显示
4—6 calls。首个公开问题 `登录流程是怎样的？` 随后在 560 ms 内返回 502。terminal
`sha256:5288b0c2354251d2b762d755807b3ab8bde4bece21e4de5fd152e692ca00a791` 将首次失败定位为 `ANSWER`：Answer
只尝试一次受控 AF_UNIX Gateway connect，Gateway 自身以 `RuntimeError` 在接受请求前退出。

Gateway audit 的 network operation count 为 0；预建的三个 Provider socket 均为 credential-free TCP handoff，TLS/HTTP operation
count 为 0。没有读取 credential、没有发送 Provider HTTP request、没有模型调用、没有 retry、没有 Source/Update/Direct/Evidence
payload 访问。浏览器 console 为空。下单与跨域问题未执行。

## Evidence and root cause

`gateway_authorized_workload.py` 在加载 qualified baseline 前按常量校验同目录 entrypoint 的 raw SHA-256。run-005 candidate stage 中：

- `bounded_java_source_semantics_gateway_workload.py` 实际 raw SHA-256 为
  `af5059c2b7ed34ac25817995570bb7d7f174f46e117752d7535141992e2ce3c3`；
- wrapper 仍期待旧值 `ac0cf321990b463d6924bf5ce395bb039d5e7a07bfaa946da8ae51934403f49c`。

因此 Gateway 在 receipt/freeze 文件校验后、listener accept 和 credential/TLS/HTTP 前按设计失败关闭。现有 wrapper 测试 mock 了
`_load_qualified_baseline`，freeze 测试只证明资产被复制，二者都没有核对常量与 packaged file 的实际一致性；这解释了 deterministic
freeze 为什么未提前发现。

根因是产品资产演化后遗漏同步 self-integrity pin，不是 DeepSeek 可用性、Provider wire、资格、问题语义或隔离策略。System
Contract 已要求 exact entrypoint digest，因此本次只修复实现一致性，不改变安全边界。

## Decision and disposition

1. bounded Gateway pin 更新为当前 packaged entrypoint raw SHA-256 `af5059c2…e3c3`；其他历史/current entrypoint pin 不变。
2. 新回归直接对三份当前 packaged Gateway baseline 重新计算 SHA-256，并与 wrapper 常量逐一比较，不再通过 mock 绕过真实
   self-integrity relation。该测试进入 formal focused 集合。
3. 修复提交为 `54bc8c8fa7d2ab9709191d448dbd7509c3aa4095` / tree
   `4cc184e1c61178cd825904271777774c1dea5cf7`。定向 gateway/freeze 14/14 与 ITER-008 扩展 focused 110/110 PASS；
   `compileall` 和 scoped diff check PASS。
4. run-005 freeze/grant/session/terminal 永久保留为 pre-provider failure evidence；原 request 不 retry。修复改变 launcher source 与 digest，
   必须生成全新 formal freeze/grant，不能继续旧 session。

## Verification and closure

本 Finding 以 code/tests-only 处置闭合，因为 exact entrypoint pin 与失败关闭语义已经属于 `SYS-CONTRACT-AI-MODEL-GATEWAY`；没有新
Owner、协议、资格或安全决定。新的 deterministic freeze 必须证明新增 self-integrity 回归通过，然后才可重新执行公开登录题。
hidden canary 未披露，Production Activation 保持 `NOT_EXECUTED`。
