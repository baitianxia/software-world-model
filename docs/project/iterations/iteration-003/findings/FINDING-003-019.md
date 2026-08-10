---
id: FINDING-003-019
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality, security]
depends_on: [ITER-003-SLICE-001, FINDING-003-018, ITER-003-VERIFICATION]
code: [validation/structure_world_model_iteration_003/questions/mature-agent-baseline-protocol-1.0.3.json, validation/structure_world_model_iteration_003/v009]
tests: [tests/test_iteration_003_validation_assets.py, tests/test_iteration_003_v009.py]
iteration: ITER-003
classification: iteration-design
disposition: deny-model-command-environment-inheritance-and-requalify-v009
target: ITER-003-SLICE-001
---

# FINDING-003-019：Mature baseline 还必须隔离 operator 环境变量

## Observation

第五轮 V-009 在 checkpoint `3d09ed1c8f9fe1a0199619e924189f0453822937` 上取得 exact
Conformance PASS 与 closed CE 7 PASS、0 FAIL、0 UNKNOWN、PASS/VALID。随后在任何 baseline 模型请求
发出前，运行器审计发现：Mature protocol `1.0.2` 已封闭文件和网络，但没有固定 Codex
model-generated command 的环境继承。V-009/Direct operator 进程当前需要 `ARK_API_KEY`；如果 Mature
Codex 父进程直接继承该环境，而 shell policy 允许变量进入模型命令，则模型可通过 `env` 等命令把不属于
Mature baseline 输入的 credential 带入 tool output。

这不由 root-deny filesystem profile 解决，因为环境变量不是文件读取。仅依赖变量名称的默认过滤也不是
冻结的、可机械复核的 exact input。

## Evidence

- qualified input freeze：`ITER-003-V009-EXACT-INPUTS@1.0.4` /
  `sha256:359e4e7ac529430fe1374bf09e69b140d01a0c619c450dcf4657278c935cc469`；
- Conformance binding：`sha256:8a009865fb3abbedc6f00a9e44b383488cca2470f7fd6f847e9ffd47d1c985d5`；
- closed Result：`evaluation_result_8763cb0d957046d880856addc7395894` /
  `sha256:9815e699187f696db083f24edf0029f8eea583033c9961d69738a2ac63b12c14`；
- qualification：`capability-evaluation:evaluation_result_8763cb0d957046d880856addc7395894` /
  `sha256:5b206e6d39752652039ea9765f58f4da7f92f685d67fa09bbbbbc205387f9d60`；
- 原始证据目录：`var/iteration-003/v009/3d09ed1c8f9fe1a0199619e924189f0453822937/`；
- frozen Provider credential reference 为 `env:ARK_API_KEY`，本机 `verify-inputs` 已机械确认其配置存在；
- Codex 当前 config reference 提供 `shell_environment_policy.inherit`、`set`、secret-name exclusion 与
  `allow_login_shell` 控制；
- 尚未发起 controlled Direct 或 mature Agent baseline 请求。

## Impact and classification

该缺口不会自动泄露 credential，但原协议不能证明 Mature model input 与工具输出只来自授权问题和 POM。
因此它阻断 baseline，而不是作为运行时 warning 接受。它只修正验证协议/exact gate input，不改变 System
Contract、产品实现或产品 Oracle，分类为 `iteration-design`。第五轮 V009 PASS 保留为历史证据但不可
授权改变后的 protocol。

## Decision and disposition

新增 `ITER-003-MATURE-SOURCE-AGENT-BASELINE@1.0.3`。在 `1.0.2` 的 root-deny permission profile
基础上，exact command 增加：

- `allow_login_shell=false`；
- `shell_environment_policy.inherit="none"`；
- `shell_environment_policy.ignore_default_excludes=false`；
- 只显式注入非秘密的 `PATH=/usr/bin:/bin:/usr/sbin:/sbin`、`LANG=C`、`LC_ALL=C`、`TZ=UTC`。

Mature runner 还必须在启动 Codex 时移除 Ark 及其他不需要的 API credential 变量；该父进程环境只用于
Codex 自身的标准 ChatGPT authentication，不能进入模型消息或生成命令环境。事件审计若出现 env dump、
credential 名称或非冻结环境变量即标记该 run 失败并保留。

新 `ITER-003-V009-EXACT-INPUTS@1.0.5` 绑定第五轮 PASS、本 Finding 与 Mature protocol `1.0.3`。
按 exact-input drift rule，必须从新 clean checkpoint 再完整执行 Conformance 与七个 CE Case，之后才可
开始 baseline。

## Verification after disposition

资产测试机械验证 exact argv 的 no-inherit、no-login、secret exclusion 与四个显式非秘密变量，并用真实
CLI strict parse smoke 拒绝未知 config。V-009 runtime verifier 绑定新 protocol digest 与 shell environment
identity；聚焦测试、全量测试和文档检查通过后形成 clean checkpoint。
