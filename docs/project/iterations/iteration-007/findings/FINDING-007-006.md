---
id: FINDING-007-006
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [interface, security, quality]
depends_on: [ITER-007-SLICE-001, ITER-007-RESULT-SLICE-001-PRODUCT-CANDIDATE-FREEZE-RUN-001, SYS-QUALITY-SECURITY]
code: [src/software_world_model/interface/__init__.py, src/software_world_model/interface/world_model_browser_ui.py]
tests: [tests/test_iteration_007_slice1_freeze.py, tests/test_world_model_browser.py]
iteration: ITER-007
classification: system-contract
disposition: isolate-interface-package-imports-and-qualify-real-role-entrypoint-dependency-closure
target: SYS-QUALITY-SECURITY
---

# FINDING-007-006：普通测试环境掩盖 Answer 隔离包的非必要 parser 依赖

## Observation

run-001 product freeze 通过 focused 66、candidate package 24 和 full 911 后启动正式 Web。用户提交“登录流程是怎样的？”时，页面
返回 `the isolated World Model run did not produce a verified terminal`。用户共发起四个独立请求；四个 terminal 均在
`ANSWER` 阶段失败，Answer role report 为 `ModuleNotFoundError`，每次 controller retry 为 0。

## Evidence and root cause

- run-001 freeze report digest：
  `sha256:1f3f79084ccc2feeaf6fb03c7d807c153e11d62f8316ff8945e477d0c7027bfc`；
- live grant digest：
  `sha256:764c93cdbfa5806c7420c19cae89b360a5273d9f1b3727915c3d2a3a334d152e`；
- 四个 terminal document digest：
  `sha256:3461b4f8f013147bdbfd3101560a82f90d0da63ed7ad38e3d063da7b9b8254c9`、
  `sha256:be3fdc6b203f669027194554c83d69d7ddbf900289aa221855b032acbf9742ec`、
  `sha256:891ca9781eb8b0cf6fa022e2e10c0e7d81eea7ed993b9490acddd446795aeaf0`、
  `sha256:578306707e29d2cd0c209e52cf3ae22de2283965fc158c5b13471368a7d6e9a2`；
- 四个 Gateway SQLite 的 `ai_model_call_*` 表均为 0 行；三个 Provider descriptor 只完成 supervisor TCP provisioning，
  Answer 未连接 Gateway，未形成 TLS/HTTP/model request；
- runtime 用 `-I -S -B` 和 `PYTHONNOUSERSITE=1` 启动 role。Answer 导入窄
  `software_world_model.interface.world_model_evaluation` 前，Python 先执行 `interface/__init__.py`；其 eager
  `agentic_runtime → runtime → maven_structure_update → java_source_semantics` 链最终要求仅存在于普通环境
  `site-packages` 的 `tree_sitter`，因此在真实隔离角色中失败；
- 原 candidate package tests 使用普通 Python 环境，OS preflight 只运行 capability probe，没有导入真实 Answer entrypoint，
  所以错误未在冻结前暴露。

这是通用 package/dependency closure 与验证规则问题，不是题目、模型、Ark、Source 数据或浏览器脚本问题。

## Decision and disposition

`software_world_model.interface` package root 保留既有 public API，但改用 PEP 562 lazy exports。导入窄 interface submodule 不得
附带加载 agentic runtime、Update 或 parser；需要旧 package-root export 的调用方仍在首次访问时加载相同 owner module。不能通过
把平台相关 `tree_sitter` wheel 复制进 Answer 来掩盖边界，因为 source-off Answer 不拥有 parser 能力。

候选冻结测试必须先按 runtime exact `-I -S -B` flags、sanitized role environment 和 frozen package root 导入真实 Answer
entrypoint，并证明 `tree_sitter`/`tree_sitter_java` 未加载。页面执行边界同步修正为 Plan→Draft→Review 三次调用；测试固定该文案，
避免用户看到旧单调用协议。

系统规则写回 `SYS-QUALITY-SECURITY` 与 `SYS-OPS-LOCAL-BROWSER`。run-001 freeze 和四次失败永久保留；任何修复后体验必须生成新的
product freeze、post-freeze live grant 和 session，不能覆盖旧证据或对旧请求重试。

## Verification after disposition

- exact `-I -S -B` direct import probe PASS，`tree_sitter` 与 `tree_sitter_java` module count 均为 0；
- targeted slice-freeze/browser 11/11 PASS；
- isolation/Web focused 51/51 PASS；
- full regression 911/911、documentation check 283 documents PASS；
- replacement run-002 product freeze focused 66/66、candidate package 24/24、full 911/911、docs 与 unauthorized-prelisten Gate
  PASS；report digest `sha256:f47fe21bdd0b56be39434dd973ef9adb5364bedf0b54f73511235b931f418cbb`；
- run-002 冻结 Answer entrypoint 在 exact `-I -S -B` 下再次 import PASS，parser module count 为 0；
- 修复后的正式 Web 现场结果仍待新的 post-freeze 用户授权和新问题。
