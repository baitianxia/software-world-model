---
id: FINDING-005-004
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, security]
depends_on: [ITER-005-SLICE-002, SYS-ARCH-DEPLOYMENT, SYS-CONTRACT-AI-MODEL-GATEWAY]
code: [src/software_world_model/interface/world_model_runtime.py, src/software_world_model/interface/world_model_runtime_assets/gateway_authorized_workload.py]
tests: [tests/test_world_model_gateway_authorization.py]
iteration: ITER-005
classification: local-implementation
disposition: require-current-session-gateway-authorization-receipt
target: src/software_world_model/interface/world_model_runtime_assets/gateway_authorized_workload.py
---

# FINDING-005-004：继承的 Gateway freeze 含历史披露确认

## Observation

把 accepted ITER-003 Gateway package 接入 ITER-005 launcher 时，`g3b-freeze.json` 仍声明 ITER-003 的
`codex-user-confirmation`、`repeat_confirmation_required: false` 和旧 permission digest。外层 evaluation grant 能阻止当前未授权
启动，但 Gateway summary 若继续把旧 permission 当作本次 authority，会错误地把历史披露确认复用于新仓库问题。

## Evidence

- inherited `gateway_workload.py` 的 `_verify_g3b_freeze` 固定接受旧 permission digest；
- inherited summary 把该 digest 命名为 `permission_digest`；
- ITER-005 Manifest 明确规定编码授权不能推导为 World Model、controlled Direct 或成熟 Source Agent 的披露授权；
- 新聚焦测试证明非 `AUTHORIZED` 的当前 receipt 在调用 qualified Gateway baseline 前失败，合法 receipt 的最终 summary 不再
  暴露旧 permission 字段，而把旧 freeze 标成 `QUALIFIED_CAPABILITY_BASELINE_ONLY`。

## Impact and classification

System 已要求每次新披露使用明确授权；缺口是 trusted launcher/Gateway 装配没有把历史资格证据与当前 authorization authority
分开，分类为 `local-implementation`。Owner、Provider、endpoint、Prompt、Strategy 与网络 capability 不变。

## Decision and disposition

新增产品自有 `gateway_authorized_workload.py` 作为唯一 active Gateway entrypoint：

1. trusted launcher 从 exact evaluation grant 生成当前 session 的 no-secret authorization receipt；
2. wrapper 精确验证 grant digest、disclosure digest、用户、payload boundary 与 `NOT_EXECUTED` Activation；
3. 验证通过后才进入 byte-pinned 的 qualified Gateway baseline；
4. 最终 Gateway summary 绑定当前 receipt，并把旧 freeze 仅标记为能力资格基线，不再把旧 permission 声称为当前授权。

该 wrapper 与 launcher 都进入 exact launcher/package manifest。因为 active Gateway entrypoint 改变，候选 role package 必须与
FINDING-005-003 的 Answer 变更一起重新密封、隔离预检和完整验证。

## Verification after disposition

`tests.test_world_model_gateway_authorization` 的未授权短路与合法 receipt 重绑定均通过；真实 OS preflight、一次 Provider call 与
Gateway postcondition 仍由 V-007/V-009 在单独披露授权后闭合。
