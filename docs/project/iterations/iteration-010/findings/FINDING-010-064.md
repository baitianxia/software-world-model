---
id: FINDING-010-064
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-062, FINDING-010-063]
code: [src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_model_source.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: require-downstream-response-owner-evidence-and-separate-transport-from-body-code
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-064：上游认证或授权状态不能替代下游响应映射证据

## Observation and evidence

clean candidate `656b549b3f87cd3a3ded132807be7cd91b66b625` / tree
`f444c08db8113c0fe8c6d1e59c9c39307eaaa584` 的隔离 clone 通过 Engineering QA 102/102、docs 457/457、compile 与 diff Gate。run-023
fresh DeepSeek Conformance 2/2 PASS，Result digest 为
`sha256:6acad0552986c042759da2134fe720e6c610c02743c4fa45bbb328d4a27ae7a1`，文件 SHA-256 为
`6273bcfadca6ba0925dbb9fe7b267183195a039ef203dc9a99ff0679dd704c42`，actual model `deepseek-v4-pro`、retry 0。

fresh session authority `sha256:de0224bb4d07bfd5f41e1f1499d9df9df6ec684a928572ca76adb255140421bf` 绑定 exact candidate、mall
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`、Source Profile、run-023 qualification 与 user root authorization。同一 listener 顺序完成
三道固定题，dispatch 为 8/8/7，共 23 次，retry/switch 0、verified TLS、每题单连接复用、private session/launch/terminal/SQLite files，
Production `NOT_EXECUTED`。66,000-byte UTF-8 输入在 Provider 前拒绝，Gateway dispatch 仍为 23，listener 保持可用。terminal receipt
文件 SHA-256 为 `a99fb04360c2916b15a48d964a8f2ae42784c5561c80030292aef442ad9bbdbd`，document digest 为
`sha256:02f0e2fd2d59eaa4b1620f02ab65798476dd0256ef83e9a0e75653c0f428d7d7`。

Q1 登录流程与 Q2 本地启动/安全接入均得到模型 `APPROVED`，独立技术复核没有发现重大错误。Q3 询问 401/403 链路排障时，Package、
Answer 与 Reviewer 却把同一“没有建立认证上下文”的上游状态同时映射为两个不同的外部结果：Filter 分支断言为 401，动态授权管理器的
unauthenticated 分支又断言为 403。所读三份实现只能证明 token filter 的提取/校验与上下文建立行为、metadata lookup 和 authorization
deny decision；它们不拥有最终 HTTP status、API error category 或 response body 映射。Review 仍把
`claim_consistency` 标为 PASS 并逐字复述同一无据冲突，因此 Q3 虽为模型 `APPROVED`，独立质量裁决为重大错误 FAIL。

本地只读复核另确认安全配置注册了自定义 authentication-entry-point/access-denied handlers，而 handler implementation 决定响应写法；
该两份实现不在 run-023 的 Provider source allowlist，未向 Provider 披露。因而 run-023 能支持上游局部机制，但不能补写 handler 输出，
也不能假定框架默认。即使 handler 写入响应体中的 unauthorized/forbidden application code，也仍须与 transport HTTP status 分开核对。

## Decision and disposition

- Question Understanding 对经过多阶段才产生的外部 status/error/body 结论，必须把下游 response/exception mapper 的 full-content
  implementation 纳入最小决定性证据；若该 owner 未授权或不可用，则把外部结果保留为独立 unknown，不因上游状态或接线删除它。
- Initial/Verification Investigation、Answer 与 Reviewer 统一遵守 ownership rule：空认证上下文、抛出异常、deny decision 以及自定义
  handler registration/class name 只证明局部状态或选择关系，不证明 handler output，更不得用 framework default 补齐。
- transport HTTP status 与 application/response-body error code 是两个不同结论；只有 exact evidence 分别支持时才能同时断言。
- Reviewer 必须拒绝缺少 mapping-owner implementation 的外部结果，还必须拒绝把同一局部条件同时解释为 authentication failure 与
  authorization denial 的互斥结果；不能自行引入 Package 外证据。

本次不扩张 mall Provider disclosure allowlist，不读取或发送 `src/main/resources`，不引入题目、工程、类、方法、fixture 或 Oracle
特判。Prompt identity 升为 `engineering-qa-adaptive-investigation-prompt@26`；三模块定向 65/65、Engineering QA 102/102、compile 与
diff PASS。完整 docs/full 与新 clean/fresh live 仍待闭合，run-023 永久保留为 Q1/Q2 可接受、Q3 独立重大质量 FAIL 的证据。
