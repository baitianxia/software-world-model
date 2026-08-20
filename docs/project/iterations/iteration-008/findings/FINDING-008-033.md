---
id: FINDING-008-033
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [interface, application, quality, project]
depends_on: [ITER-008-SLICE-001, FINDING-008-032, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-OPS-LOCAL-BROWSER]
code: [src/software_world_model/interface/world_model_http.py, src/software_world_model/interface/world_model_browser_ui.py]
tests: [tests/test_world_model_http.py, tests/test_world_model_browser.py]
iteration: ITER-008
classification: local-implementation
disposition: code-and-tests-only-existing-dispatch-contract
target: src/software_world_model/interface/world_model_http.py
---

# FINDING-008-033：正式 Web 仍按旧三调用假设校验有界结果

## Observation

run-023 已资格化的正式 bounded route 明确声明
`FOUR_TO_SIX_ORDERED_CALLS_PER_QUESTION_NO_HIDDEN_RETRY`。随后 product `run-004-freeze` 通过 deterministic Gate，report/document
digest 为 `sha256:909c8d4b9989b4611f9a52ecf9ced987579373117ad7430c859ad04d2ad77352`，并形成 post-freeze
authorized grant `sha256:95a2562dfcdbd81daf717e2e0c446907dbbfed98180f448a50fd5f8681a8334f`。

正式 Web 启动收据 `sha256:cfc8695282c1009ba72ec7acaafcb9ec1d08652a9f9f771562c9a285918d2b30` 与 startup
preflight `sha256:61ae7e8fec6e1968226919bf424f414a781dd8e037329f771effb7843271429e` 均 PASS，页面却在任何问题 POST 前显示
`Plan → Draft → Review · 3 次模型调用`。检查 product adapter 又发现 `DynamicCatalogWorldModelRunner` 按
`JAVA_SOURCE_SEMANTICS@1` Profile 固定期待 3 calls；因此合法的 4—6 call bounded Result 即使生成，也会被 public boundary
错误拒绝。

该次浏览器会话只发生页面、asset、health 与 Read Set GET。`run-004-live-session/requests` 为空，外部模型调用为 0；旧 grant
没有产生问题 Result，但其 candidate identity 已被后续修复改变，不得再用于分派。

## Evidence and root cause

System Contract 已规定当前 Profile 每题实际调用为 4—6，并要求页面披露该边界。执行器 startup receipt 也已把 exact
`dispatch_policy` 暴露给 trusted HTTP adapter。偏差来自两个遗留实现假设，而不是 Provider、模型或 qualification：

1. HTTP result validator 从 Profile 推导 `3/1`，没有使用同一启动时已校验的 dispatch policy；
2. 浏览器静态 HTML 把 ITER-007 的三调用文案写死，health 成功后也不更新。

这属于既有规范的本地实现漂移，不改变 Owner、调用协议或 System 语义，因此无需改写 `docs/system/`。原 formal freeze PASS 只证明
其冻结门禁当时没有覆盖这项正确断言，不能把错误文案或 validator 行为提升为新规范。

## Decision and disposition

1. HTTP adapter 以 startup health 中已校验的 exact `dispatch_policy` 为唯一调用数事实源：one-call 只接受 1，legacy ordered
   three-call 只接受 3，bounded policy 只接受 4—6；布尔值、未知 policy、越界数或 network count 不一致继续失败关闭。
2. Web 页面从同一 health `dispatch_policy` 渲染调用边界；health 完成前只显示校验中状态，未知 policy 阻止页面进入 ready。
3. 回归覆盖 bounded 4/5/6 全部接受、3 拒绝，以及页面不再硬编码旧值而绑定 health policy。代码修复提交为
   `41b766a179bcc1bf78aed3278f6687a5e1c15abd` / tree
   `e78427b474dc401308f1f69a0fe1adfb68b00e37`。
4. run-004 freeze、grant 与零请求 startup 证据永久保留；因为修复改变 product source，必须生成全新 formal product freeze 和新的
   post-freeze grant，不能在旧会话继续提问。run-023 Provider qualification authority chain 本身未改变，仍只按其有效期与 exact
   resource binding 使用。

## Verification and closure

HTTP/browser 定向回归 21/21 PASS；ITER-008 focused 集合加 HTTP/browser 共 109/109 PASS。后者在允许 AF_UNIX listener 的执行面
运行；受限 sandbox 的 socket denial 不作为产品失败。`compileall` 与 scoped `git diff --check` PASS。

本 Finding 已以 code/tests-only 处置闭合，因为 `SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING` 与
`SYS-OPS-LOCAL-BROWSER` 已拥有 4—6 call 与页面披露语义，没有新系统决定。新的 deterministic freeze、正式 Web Result、Citation
与 browser console 验证仍是下一 blocking Gate；hidden canary 未披露，Production Activation 保持 `NOT_EXECUTED`。
