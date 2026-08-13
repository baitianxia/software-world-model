---
id: ITER-006-RESULT-JAVA-CAPABILITY-RUN-002
kind: iteration-result
status: pass-valid
authority: execution-evidence
owners: [engineering, quality, security]
depends_on: [ITER-006-RESULT-JAVA-CAPABILITY-CANDIDATE-FREEZE, FINDING-006-008]
code: [validation/structure_world_model_iteration_006/capability, src/software_world_model/ai_infrastructure/java_model_egress_qualification.py, src/software_world_model/ai_infrastructure/java_model_egress_policy.json]
tests: [tests/test_iteration_006_capability_qualification.py, tests/test_model_egress_gateway.py]
iteration: ITER-006
---

# ITER-006 Java Capability run-002 Result

## Decision

用户对 exact freeze `sha256:7a3948a358ba309539b1362b7b26ee659c9edfa5ec4738deccb9c4c633fced26`
和 suite `sha256:93be2f872fe8531d09ca220b67aa493d8f929cbca1b27309b2d05775684d6716` 的单次授权已按边界执行并消费。
八个 synthetic sealed case 全部 PASS，closed result 为 **`PASS_VALID`**：failure/unknown 均为 0，恰好 8 个唯一 Ark Provider
request，每题一次，hidden retry 为 0。

本 Result 只资格化 Java proposal contract/Strategy `1.1.0`。它没有发送产品问题、Java 源码或 Evidence payload，没有创建 Codex
task，也没有执行三路 Product Comparison、Production Activation、Git stage/commit/push。因此 run-003 的 V-008 FAIL 不被追溯
改写，Slice/Iteration 仍未接受。

## Exact authorization and terminal

- 用户消息引用：
  `codex-user-message:sha256:17abf3f131d3dd99d0b2f13724d2b1cc8db470f28bcda6d5afd8dc9ecc71eee6`；
- 授权时间：`2026-08-12T15:08:50+08:00`；
- authorization document digest：
  `sha256:7ac55d73f7c2dbbdd87ecb4db0fa210c2d9ddaf78f4ca665f3ff81f6d61b95ec`；
- invocation document digest：
  `sha256:5df33e88601db345b6f2ff53582f15901347c75777afbd9bff002d6ffbbe23d6`；
- terminal document digest：
  `sha256:2b6a0f58c8b053fb9be5587c4bfa85446d42eeba4bd041469e66e4c0be91841d`；
- terminal：`status=PASS`、`authorization_consumed=true`、`provider_request_count=8`、
  `retry_permitted_with_same_authorization=false`、Production Activation `NOT_EXECUTED`。

对应文件 raw SHA-256 依次为 `fc07b265…`、`486e7f06…`、`283fa764…`，只保存在本机
`var/iteration-006/capability/`。document digest 与 raw file digest 使用不同的规范化边界，不可互换。

## Closed Result and qualification

- Result ID：`evaluation_result_7ac1e5f69296449f8068cd2853be8c5a`；
- Result digest：
  `sha256:e3423a2e183b90e9c513880c586b7151fa472d296f424227c7869e84d7655c6b`；
- closed Result document digest：
  `sha256:e6d39d16269f0cefec16dcb7aab544936dca47458a47390955c67c32df163439`；
- qualification proof ref：
  `capability-evaluation:evaluation_result_7ac1e5f69296449f8068cd2853be8c5a`；
- qualification proof digest：
  `sha256:65d1843640966e090f53d7c472bd048cf673ad16f0bc470b791d1e23975be6d5`；
- qualification document digest：
  `sha256:cdbda2de8ec5ce0d805ac31ca9be6462c1bae62fc61f28601e23a5cc6f3caea0`；
- validity：`VALID`，截至 `2026-08-19T07:10:03.636096Z`。

closed Result 与 qualification 文件的 raw SHA-256 分别为 `414776c2…`、`4d601e7d…`。资格 loader 已独立重放 exact policy、
contract/Strategy、Prompt、output schema、metric、suite、Oracle、Result、Validity 与 proof 链，返回同一 ref/digest/expiry。

## Isolation audit

八份 case evidence 的独立汇总为：8/8 review `PASS`、model call 8、唯一 Provider request 8、hidden retry 0、source access 0、
repository read 0、Evidence payload access 0、product suite/oracle read 0。实际模型 fingerprint 为 `glm-5.2`，总 input/output token
为 7294/372。每题 evaluator 均从独立 packet 执行 exact projection 与 forbidden-event 检查；没有选择性重跑或插值。

该单次授权已经消费，不得用于新 capability 或 product run。后续产品 comparison 必须绑定新的 held-out suite、三个目的地与各自
payload boundary，另取独立用户授权。
