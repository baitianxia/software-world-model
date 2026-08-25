---
id: ITER-010-RESULT-V-ALPHA-ACCESS-001
kind: iteration-result
status: passed-access-checkpoint
authority: execution-evidence
owners: [product, application, interface, security, quality, project]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-095]
code: [pyproject.toml, src/software_world_model/application_services/engineering_conversation.py, src/software_world_model/interface/engineering_chat_browser.py, src/software_world_model/interface/engineering_chat_browser_ui.py, src/software_world_model/interface/engineering_chat_alpha_cli.py]
tests: [tests/test_engineering_conversation.py, tests/test_engineering_chat_browser.py, tests/test_engineering_chat_alpha_cli.py, tests/test_engineering_qa_browser.py, tests/test_engineering_qa_alpha_cli.py]
iteration: ITER-010
case_id: V-ALPHA-ACCESS-001
case_verdict: PASS
acceptance: NOT_ACCEPTANCE
production_activation: NOT_EXECUTED
---

# ITER-010 V-ALPHA-ACCESS-001 本机浏览器验证 Result

## Decision and scope

`V-ALPHA-ACCESS-001: PASS`。在 clean exact product commit 上，固定无参数命令真实启动了 loopback Chat Access；普通用户通过本机浏览器
建立和继续 Conversation、提交失败 Turn、查看完整消息历史并创建隔离的新 Conversation。Provider 未配置时，每个 Turn 都如实以
`FAILED / PROVIDER_NOT_CONFIGURED / Provider dispatch 0` 关闭，Conversation 保持 `ACTIVE`，页面始终明确显示“质量未验收 · 非生产”。

这是 Access 检查点，不是主工程 Agent、语义多轮 Chat、答案质量、World Model/Source 组合、独立 Review、Provider qualification、比较、
Slice Acceptance 或 Production PASS。

## Exact freeze and authorization

- product commit/tree：`cf2883bef861e0345afc36415d4216f943d31cf4` /
  `a720afbb36e05410d8e9e830b4f51f261e494852`；启动前 branch `codex/iter-010-rework` worktree clean；
- exact project binding：`mall@0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`；binding digest
  `sha256:dc4fa89cd5fa13a316c918d20f0ac9fe297eeb8a14ea04dce7af423cebb24a05`；
- user run grant：`codex-user-message:sha256:7256a886d863712b27a7012c1c791eaca91c98f7183f732b463ce98543a469b6`，只授权在上述
  product freeze 启动 `127.0.0.1:8765` 并执行本 Case；明确禁止 Provider/model、源码或 `src/main/resources` 读取/披露和 Production
  Activation；
- fixed command：`PYTHONPATH=src:. python3 -m software_world_model.interface.engineering_chat_alpha_cli`；无运行参数；固定 URL
  `http://127.0.0.1:8765/`；
- startup receipt：`READY / CHAT_ACCESS_ONLY / ENGINEERING_CHAT_EXPERIENCE@1`；Provider、Source 和 World Model 均
  `NOT_CONFIGURED`，external/source dispatch 均 false，quality `NOT_ACCEPTED`，Production Activation `NOT_EXECUTED`。

## Browser execution

in-app Browser 实际打开固定 URL，标题为 `Software World Model · Engineering Chat`。首屏显示 exact product/project revision、
`READY · CHAT_ACCESS_ONLY`、`Provider NOT_CONFIGURED · dispatch DISABLED`、完整已知限制、“＋ 新对话”和“质量未验收 · 非生产”。

这是一个 browser Access smoke run；其中三个 Turn 都在本机 Application 内以零 Provider dispatch 失败关闭，不是三个 model/live smoke。
实际交互序列：

1. 页面建立 `conversation_c3c84d82aa1448e48cc8f122eaabbbe7`，状态为 `revision 1 / ACTIVE / EMPTY CONTEXT / NO TURN`。
2. 提交“登录流程是怎样的？”后变为 `revision 2 / ACTIVE / TURN 1 FAILED`；用户消息和诚实限制回执同时显示，Turn 标记
   `PROVIDER_NOT_CONFIGURED / Provider dispatch 0`。
3. 在同一 Conversation 提交“它失败时会记录什么？”后变为 `revision 3 / ACTIVE / TURN 2 FAILED`；页面保留两条用户消息和两条回执，
   证明失败只关闭当前 Turn，没有关闭 Conversation 或覆盖历史。
4. 点击“＋ 新对话”建立不同 identity `conversation_eb7040393285415b843568174d83e6dc`；页面恢复
   `revision 1 / ACTIVE / EMPTY CONTEXT / NO TURN`，旧 Conversation 的消息文章均不存在。
5. 在新 Conversation 单独提交“它失败时会记录什么？”后只出现本轮用户消息与失败回执，状态为
   `revision 2 / ACTIVE / TURN 1 FAILED`。文章列表不含旧“登录流程”消息；输入框示例 placeholder 仍包含该示例文本，但不属于消息历史。

浏览器 warning/error log 为 `[]`。最后状态保留在已交付的本机页面中；没有静态回放替代浏览器交互。

## Runtime counters and shutdown

交互完成后直接读取本机 `/health`，得到：

- `conversation_count=2`、`turn_count=3`、`provider_dispatch_count=0`；
- `external_dispatch=false`、Provider qualification `NOT_EXECUTED`；Source dispatch false；World Model `NOT_CONFIGURED`；
- `production=NOT_PRODUCTION`、`production_activation=NOT_EXECUTED`；
- `excluded_source_paths=[src/main/resources]`，且本 Case 没有读取或披露源码/resources。

验证后 listener 收到 `Ctrl-C` 并以 exit code 0 优雅停止；`lsof -nP -iTCP:8765 -sTCP:LISTEN` 返回无监听器。

## Verdict and remaining gates

`V-ALPHA-ACCESS-001` 的 fixed command、真实 loopback、普通用户 Turn、消息历史、新对话、失败真实性、版本/限制与非生产标识均有执行证据，
因此 Case 为 `PASS`。`FINDING-010-095` 的确定性候选证据继续保留，新的真实执行事实由 `FINDING-010-096` 处置到 Verification Matrix。

仍为 `NOT-RUN / blocking`：`V-TIMEBOX-CHAT-001`、`V-CHAT-EXPERIENCE-001`、`V-CHAT-001`、`V-CHAT-QUALITY-001`、
`V-CHAT-XD-001`、`V-COMP-ALPHA-001` 和 `V-PREVIEW-002`。本次没有调用 Provider/model、没有执行冻结五轮 canary，也没有证明模糊指代澄清、
用户纠正、深入、总结、逐轮 Evidence/Citation/fresh Review 或答案正确性。
