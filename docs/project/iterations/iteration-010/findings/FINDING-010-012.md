---
id: FINDING-010-012
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [interface, operations, security, quality]
depends_on: [ITER-010-SLICE-001, FINDING-010-011, SYS-OPS-LOCAL-BROWSER, SYS-QUALITY-SECURITY]
code: [src/software_world_model/interface/engineering_qa_preview_cli.py, src/software_world_model/interface/engineering_qa_browser.py, src/software_world_model/interface/__init__.py, pyproject.toml]
tests: [tests/test_engineering_qa_preview_cli.py, tests/test_engineering_qa_live.py, tests/test_engineering_qa_browser.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: require-a-clean-exact-product-origin-and-sealed-launch-terminal-receipts-before-the-loopback-preview-is-an-executable-product-entry
target: SYS-OPS-LOCAL-BROWSER
---

# FINDING-010-012：可组合的 WSGI 对象不是可执行的产品微纵切

## Observation

`engineering_qa_browser.py` 和 `engineering_qa_live.py` 已能组合 exact prepared Request、DeepSeek Gateway、Cognition Projector、
Broker/Worker 和 WSGI 页面，但它们刻意不监听端口。若没有可信 launcher，`V-WEB-000` 仍只能在单测内证明对象可组合；操作者也可能从
dirty/另一代码树启动、把任意工程或问题塞入页面、在 listener 后才检查授权，或无法留下每次动态 disclosure 的执行收据。

## Evidence and root cause

- 既有 `EngineeringQuestionBrowserApplication` 的模块说明明确把 loopback binding 交给“separate trusted launcher”，仓库此前没有该入口；
- `ExactAuthorizedEngineeringQuestionRequestFactory` 可以拒绝浏览器改题，却不负责验证运行中的 Python 模块来自哪个 product candidate；
- role output source 保留一次性 disclosure/Gateway audit，DeepSeek transport 保留 TLS/credential/no-retry audit，但没有 launcher 将其密封为
  可复核的 launch/terminal artifact；
- 根因不是 WSGI 或角色实现错误，而是产品 composition root 尚未拥有 freeze identity、输入装载、listener 顺序和运行证据生命周期。

该缺口决定真实本机入口的授权与审计语义，属于 `system-contract / systemic`。

## Decision and disposition

- 新增通用 `swm-engineering-qa` launcher；它不内置工程、问题、关键词、符号、fixture 或 Oracle route；
- listener 前验证 launcher 模块确实位于 caller 声明的 product repository，且该文件被 exact HEAD 跟踪、worktree clean、commit/tree 与
  freeze 输入相等；
- exact Source repository revision 必须解析为同一 full commit；published ordered/snapshot Bundle 的 semantic/file digest、Cognition
  Binding/revision/read authority、四类 versioned Source Profile 和 Request 必须一致；
- evaluation subject 绑定 product commit/tree、Request、所有 Bundle semantic/file digest、Provider binding 与 current Conformance；用户根
  authorization 只在这些输入形成后收窄为本次 exact Request/run grant；
- Gateway database、launch receipt 和 terminal receipt 都必须是 caller 指定的新 canonical path。launcher 只绑定 `127.0.0.1`，先取得
  listener、再以 `0600` 写入 `AUTHORIZED_NOT_DISPATCHED` launch receipt，写入失败不进入 serve；
- graceful terminal receipt 密封逐角色 disclosure authorization/Gateway call audit、TLS/credential/session audit、zero retry/switch 和
  `NOT_EXECUTED` Production Activation。Secret value 从不进入参数、receipt、health 或模型消息；credential 仍在 verified TLS 后延迟解析。

处置同步进入本机浏览器运维规范和安全边界。它只使 Slice1 入口可执行，不等于已经完成真实 Provider/browser session，也不授权 hidden、
Slice2/3 或 Production Activation。

## Verification

`tests/test_engineering_qa_preview_cli.py` 验证 clean exact candidate/dirty denial、candidate+Request+Bundle+Provider subject binding、新 canonical
database path，以及真实 typed Bundle + Source/Profile + fake DeepSeek qualification 的完整无分派组装；既有 live/browser/model-source 测试继续
证明 prepared input 不可扩张、secret/authorization ref 不上 wire、每个动态输入一次性授权且 outcome unknown 不重试。CLI `--help` 可加载，
`py_compile` 与 `git diff --check` 通过。真实 listener/Provider/browser 证据仍必须在 clean product freeze 后形成。
