---
id: FINDING-003-024
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality, security]
depends_on: [ITER-003-SLICE-001, ITER-003-VERIFICATION, FINDING-003-022]
code: [validation/structure_world_model_iteration_003/g3b/answer.sb, validation/structure_world_model_iteration_003/g3b/gateway.sb, validation/structure_world_model_iteration_003/g3b/projector.sb, validation/structure_world_model_iteration_003/g3b/run_g3b.py]
tests: [tests/test_iteration_003_g3b.py]
iteration: ITER-003
classification: local-implementation
disposition: expand-fixed-literal-ancestor-capacity-without-expanding-recursive-capabilities
target: validation/structure_world_model_iteration_003/g3b/run_g3b.py
---

# FINDING-003-024：正式证据路径超过了 Seatbelt profile 的固定祖先参数容量

## Observation

首次正式 G3b dispatch 已先密封 invocation，并由无 credential、无产品 payload 的 supervisor 完成一次固定
Ark peer 的 DNS、TCP connect 和 descriptor handoff；随后在启动第一个 sandboxed Answer preflight 前失败关闭。
正式证据根与 stage 路径共需要 43 个去重后的 literal ancestor，而三个 profile 只预留 40 个参数，因此
`_profile_parameters` 抛出 `G3b profile ancestor set exceeds fixed capacity`。本次失败没有执行 TLS、HTTP、
Provider 模型调用或 Production Activation。

## Evidence

- 失败 dispatch 保存在
  `var/iteration-003/g3b/a00848a939fdd38fe2e32ade73d74fcfe6a947b4/dispatch`；
- invocation 绑定 implementation commit `a00848a939fdd38fe2e32ade73d74fcfe6a947b4`、60 个冻结 run 与
  `NO_SELECTIVE_RETRY_ONE_ATTEMPT_PER_FROZEN_RUN`；
- provider bootstrap 收据记录一次 DNS、一次 TCP connect、一次 descriptor transfer，同时
  `credential_visible=false`、`product_request_payload_visible=false`、`tls_operation_count=0`、
  `http_operation_count=0`；
- 以正式路径复算 ancestor 集合得到 43 项，超过原固定容量 40。

## Impact and classification

该问题只影响验证 runner 对较深证据路径的承载能力；它不改变调用方语义、系统安全不变量、Provider endpoint、
credential owner、递归文件读取根或网络权限，分类为 `local-implementation`。旧 checkpoint 已有外联 provisioning
证据，不能修改或复用为正式 Result；修复后必须形成新提交、新密封输入和全新 evidence root。

## Decision and disposition

三个 role profile 的 literal ancestor 参数槽位从 40 扩展到 64，并保持 `_profile_parameters` 的显式容量检查。
新增槽位只容纳对既有允许根的祖先目录 literal read；未使用槽位继续填充重复的 `/` literal，不产生 `/` 的
recursive read。所有 `subpath`、AF_UNIX、INET/INET6、credential、process 和 write capability 保持不变。

该 Finding 处置到 runner/profile 代码与边界测试，不需要修改 System 文档。测试同时绑定 runner 的固定容量与
三个 profile 的最高参数，防止参数/profile 再次漂移。

## Verification after disposition

在宿主允许本地 AF_UNIX 的条件下重跑 33 项 G3b 聚焦测试。随后以新 implementation checkpoint 重新生成输入，
执行完整 preflight 和不可选择性重试的正式 60-run batch；旧失败目录原样保留。
