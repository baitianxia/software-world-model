---
id: FINDING-010-103
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, source, ai, security, interface, operations, quality, project]
depends_on: [FINDING-010-102, SYS-ADR-017, SYS-ADR-018, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, SYS-OPS-CONFIGURATION, SYS-OPS-LOCAL-BROWSER]
code: [src/software_world_model/interface/engineering_chat_session_artifact.py, src/software_world_model/interface/engineering_chat_session_runtime.py, src/software_world_model/interface/engineering_chat_alpha_cli.py, src/software_world_model/interface/__init__.py]
tests: [tests/test_engineering_chat_session_artifact.py, tests/test_engineering_chat_alpha_cli.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_provider_launcher.py, tests/test_engineering_chat_browser.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: artifact-session-fixed-command-local-candidate
target: SYS-OPS-CONFIGURATION
---

# FINDING-010-103：artifact Session 与固定命令形成零外部 I/O 本地候选

## Observation

`FINDING-010-102` 已形成完整但 non-starting 的 Session runtime 对象图；公开命令仍不能从一个 sealed operator artifact 确定性恢复 exact
product/source Git identity、World Model、Source Profile、双 Provider qualification、private Gateway repository 和 Session authority。
如果把这些值拆成命令行参数，operator 可以在启动时重新组合工程、revision、Provider、授权和预算，既破坏 freeze，也无法证明 launch
receipt 在 listener 前绑定的就是后续 Session。

## Evidence

- 新 `SWM-ENGINEERING-CHAT-ARTIFACT-SESSION-CONFIG@1` 只接受 canonical absolute、owner-private mode `0600`、unique-key UTF-8 JSON，根字段
  closed。它固定 distinct product/source repositories、exact commit/tree/revision、published ordered/snapshot Structure artifacts、exact Source
  Profile、`src/main/resources` 排除、Ark→DeepSeek ordered routes、两份 Conformance result、两个 distinct private Gateway databases、Session
  disclosure authority 和 launch/terminal receipt 路径。
- 当前 Alpha bounds 固定为 5 Turns、每 Turn 每 Provider 最多 15 dispatch、每 Provider Session 总计 75；route 必须精确为 ordinal 1
  `VOLCENGINE_ARK`、ordinal 2 `DEEPSEEK`。缺字段、未知字段、重复 key、逆序/重复 Provider、公开权限、相对路径、重叠 allowlist/exclusion 或
  identity 漂移均在 attempt、credential、Source read、Provider dispatch 和 listener 前失败关闭。
- artifact preparation 从配置加载 typed product/source Git identity、published World Model、Source Profile、current-format Ark/DeepSeek
  qualification 和两条生产 Provider runtime，再复用完整 Session composition。公开 Gateway repository reference 只包含 artifact digest 与
  route identity，不序列化 private database path；公开状态也不包含 secret value/reference。
- `swm-engineering-chat` 无参数继续保留已经验证的 Access-only 行为；唯一新增 selector 是 `--session-config <owner-private-artifact>`，不暴露
  host、port、工程、revision、Provider、question、credential 或单项 authority。artifact 分支固定 `127.0.0.1:8765`，在构造 listener 前
  exclusive-create 两个 private SQLite repositories 并写 launch receipt，listener 停止后写 terminal receipt；测试以 fake server 证明顺序，
  未启动真实 listener。
- 新 artifact/CLI/provider-runtime 直接组合 `13/13 PASS`；Agent/Conversation/Tools/Model/Route/Candidate/Launcher/Provider runtime/
  artifact/Source/Browser/CLI/Gateway 及 Conformance/Cognition/Structure 相邻组合实际 `117/117 PASS`。application/AI/interface `compileall`、
  `py_compile`、`git diff --check` 与 current documentation `503/503` 通过。本次没有读取 mall Source/resources，没有解析 credential、访问网络、调用 Provider/model、启动
  listener/browser 或执行 Production Activation。

## Decision and disposition

- 实现状态增加 `ARTIFACT_SESSION_FIXED_COMMAND_LOCAL_CANDIDATE`。这只证明 loader、完整对象组合、固定命令生命周期和零 I/O preflight；
  测试中的 qualification/artifact loader 使用本地构造或 patched typed evidence，当前实际 sealed artifact Session Configuration 尚未生成或
  执行，不能标成 `QUALIFIED` 或 `LIVE`。
- launch receipt 在 listener 前证明 dispatch/disclosure/tool/source/credential 均为 0。terminal receipt 当前密封两条 route 的 Disclosure 与
  model-boundary audit digest、model-call receipt 和 dispatch 总数，并验证 DeepSeek transport Session audit；Ark adapter 尚未把对应的
  transport-level Session audit 接入该 terminal receipt。
  为避免在没有 fresh Ark Conformance 的情况下改变已密封 Adapter identity，本次不修改 Provider adapter。
- 下一最早 blocker 是在新 clean freeze 上形成 current actual Session artifact，并先补足或重新资格化 Ark transport Session audit，再按 exact
  live grant 执行五轮 Chat/browser。`V-CHAT-*`、答案质量、Acceptance 与 Production Activation 均保持 `NOT-RUN / blocking`。
