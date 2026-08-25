---
id: FINDING-010-096
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, interface, security, quality, project]
depends_on: [FINDING-010-095, ITER-010-RESULT-V-ALPHA-ACCESS-001]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: systemic
disposition: chat-access-browser-pass-evidence
target: ITER-010-VERIFICATION
---

# FINDING-010-096：真实浏览器证明 Access 可在零 Provider 调度下独立通过

## Observation

`FINDING-010-095` 的本地候选在 exact clean freeze 上经过真实 fixed-command listener 和本机浏览器操作后，Application-owned
Conversation/Turn/Context 边界与页面投影一致：失败 Turn 没有关闭 Conversation，完整历史没有被下一 Turn 覆盖，新 Conversation 没有继承旧消息，
Provider 未配置也没有阻塞普通用户操作页面。

这使 Access Case 可以在答案质量和 Provider qualification 之前独立裁决。它没有证明主 Agent 的语义上下文处理；新 Conversation 的指代探针只是
确认旧消息未泄漏，并因 Provider 未配置而诚实失败，不能被解释为“系统已正确要求澄清”。

## Evidence

- `ITER-010-RESULT-V-ALPHA-ACCESS-001` 记录 exact product commit/tree、mall revision、固定命令、授权边界、两个 Conversation identity、三个
  真实 Turn、浏览器消息文章和 console 结果。
- 第一 Conversation 连续两个 Turn 后为 `revision 3 / ACTIVE`，保留四条消息；两个 Turn 均
  `FAILED / PROVIDER_NOT_CONFIGURED / Provider dispatch 0`。
- 新 Conversation 使用不同 identity，以 `revision 1 / EMPTY CONTEXT` 建立；隔离探针后文章列表只有本轮两条消息，旧问题不在消息历史。
- 最终 health 计数为 Conversation 2、Turn 3、Provider dispatch 0；external/source dispatch false，Production Activation
  `NOT_EXECUTED`。listener 随后 exit 0，端口无残留监听。
- 本次没有调用 Provider/model，没有读取或披露源码及 `src/main/resources`，没有执行 Production Activation。

## Decision and disposition

- `V-ALPHA-ACCESS-001` 更新为 `PASS / access-only`，目标文档为 `ITER-010-VERIFICATION`。
- `CHAT_ACCESS_LOCAL_CANDIDATE` 的当前执行状态更新为 `CHAT_ACCESS_BROWSER_PASS`；实现范围仍是 `CHAT_ACCESS_ONLY`。
- `V-TIMEBOX-CHAT-001` 及所有 Chat/Quality/XD/Comparison/Preview Case 继续 `NOT-RUN / blocking`。Provider route、主 Agent、逐轮
  Evidence/Answer/fresh Review 和五轮语义 canary 仍未实现、资格化或执行。
- 该执行没有改变 System Owner、接口语义或安全不变量；现有 System Contract 已拥有这些边界，因此主处置仅为 verification，不更新
  `docs/system/`。
