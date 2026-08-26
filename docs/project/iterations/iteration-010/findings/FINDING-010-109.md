---
id: FINDING-010-109
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, product, architecture, security, interface, quality]
depends_on: [FINDING-010-107, SYS-ADR-018, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, SYS-OPS-LOCAL-BROWSER]
code: [src/software_world_model/application_services/engineering_conversation.py, src/software_world_model/interface/engineering_chat_session_artifact.py, src/software_world_model/interface/engineering_chat_browser.py, src/software_world_model/application_services/__init__.py]
tests: [tests/test_engineering_conversation.py, tests/test_engineering_chat_session_artifact.py, tests/test_engineering_chat_browser.py, tests/test_engineering_chat_provider_launcher.py, tests/test_engineering_chat_provider_runtime.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: binding-owned-empty-context-referent-clarification-before-source-or-provider
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-109：新 Conversation 没有可信的 Provider 前指代澄清所有者

## Observation and root cause

`FINDING-010-107` 的新 Conversation 确实为空且没有旧消息泄漏，但“它呢？”仍进入 Provider route；只是因为五个 Provider Turn 的 Session
Authority 已消费完，attempt 在 dispatch 前被拒绝。通用失败文案没有要求用户明确对象。现有模型 Prompt 虽要求歧义时返回
`CLARIFICATION`，但让 Provider 决定就已经违反“Source/Provider dispatch 前澄清”；Session budget 也不应冒充语言理解。

核心 Conversation reducer 又禁止项目、问题、关键词、语言、fixture 或 Oracle 特判，因此不能在 UI 写一个 mall probe 分支。语言差异必须
通过显式版本化、Binding-owned capability 进入 Session identity。

## Decision and disposition

- `EngineeringChatBinding@2` 新增 exact `conversation_input_policy_ref`。current artifact Session 固定注册
  `EMPTY_CONTEXT_REFERENT_CLARIFICATION_ZH_CN@1`；第二语言仍是 Slice1 非目标，非 `zh-CN` artifact 现在失败关闭，不能静默缺少保护。
- 该 policy 只在真正空的新 Conversation 上运行：没有 messages/turns、included user message、Work State 或 reviewed conclusion。它识别
  versioned zh-CN anaphoric markers；普通显式首问仍进入同一 Agent executor，不按工程、题目、源码 identifier 或答案内容路由。
- 命中时 Application 密封 `CLARIFICATION / APPLICATION_INPUT_CLARIFICATION`，要求用户明确组件、流程或请求。它不是工程 Draft，不包含
  软件事实，不创建 Agent/Provider attempt，不查询 World Model、Source 或 credential，也不伪造 Package/Review/Delivery。Conversation 保持
  ACTIVE，用户可以下一 Turn 补充对象。
- 所有 Answer 和 evidence-bearing Limitation 仍必须走 Work State、Evidence Package、fresh Review 与 Delivery Authorization；这个例外只属于
  non-semantic input validation。Browser health 升级为 `@2` 并投影 policy identity/capability，便于现场核对。

Conversation 11/11、artifact 2/2、Browser/launcher/provider-runtime 15/15、compile 与 `git diff --check` 已通过；回归同时证明“它失败时会记录
什么？”在空上下文以 Provider dispatch 0 要求澄清，显式“登录流程是怎样的？”仍到达 executor，executor 也不能为显式输入伪造
Application clarification 来绕过 Evidence/Review/Delivery。该结果只证明 local deterministic
candidate；run-035 的负测仍为 FAIL，新 exact product freeze 与 Session grant 后必须重新真实浏览器验证。

联合 Gate 另有 docs 80/80、ITER-010 相关实现 97/97 与 509-document check PASS。完整本地套件在允许 AF_UNIX 后执行 1274 项，其中
1268 PASS；剩余 4 FAIL + 1 ERROR 是冻结 V-009 对 current implementation drift 的既有 fail-closed hold，另 1 FAIL 是本机 Codex
可执行文件 digest `09db9560…` 与历史 prepared digest `9f6748b4…` 不同。两类都不在本次改动模块，不能写成 full-suite PASS，也不应通过
改写历史 oracle 消除。
