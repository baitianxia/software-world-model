---
id: FINDING-010-169
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai-infrastructure, interface, quality]
depends_on: [FINDING-010-160, FINDING-010-168, ITER-010-PDR-012]
code: [src/software_world_model/application_services/engineering_conversation.py, src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py, src/software_world_model/interface/engineering_chat_browser.py, src/software_world_model/interface/engineering_chat_browser_ui.py]
tests: [tests/test_engineering_conversation.py, tests/test_engineering_chat_browser.py, tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_tools.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: require-first-available-source-follow-up-and-project-draft-citations
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-169：真实三轮链暴露过早 Limitation 与 Citation 交付断链

## Observation

`run-057-mvp-experience` 先在 exact product
`17489d63e519243cae81f93f8056370b671b237d / 0040269491fd1bf5ec822d28f0e70722e0347aa3` 上完成 Artifact Session preparation，
但 sandbox 内 listener bind 被 OS 拒绝。该 run 保留 `ARTIFACT_SESSION_PREPARED_NOT_STARTED`、Conversation/Turn/dispatch `0/0/0` 的真实
部分历史，没有被改写为 live。随后同一 product identity 的 `run-058-mvp-experience` 在 standing scope 内启动 loopback Browser，并绑定 mall
Source `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7 / 047d79d8588b76013c260f3f1a9565707301a60a`。

同一 Conversation 的三轮登录链分别为：

- Turn 1 初问以 `8` 次 Ark dispatch 达到 `SUCCEEDED / ACCEPTED`，正文自然说明入口、密码校验、JWT 与持久化登录日志；
- Turn 2 追问用户名不存在与密码错误的失败副作用，以 `4` 次 Ark dispatch 交付 `SUCCEEDED / REVIEWED_LIMITATION`；
- Turn 3 把“登录日志”纠正为仅指 `UmsAdminLoginLog` 持久化，以 `5` 次 Ark dispatch 达到 `SUCCEEDED / ACCEPTED`，证明
  `FINDING-010-168` 的 embedded-double-quote JSON 修复已通过真实 successor。

该链仍不能作为开发体验候选交付。Turn 1/3 的 Agent Package 已有 authority receipt Citation，Application Turn 又有 Package/Answer/Review/
Delivery refs，但 Browser assistant message 只显示正文和状态，没有任何 Citation 或 fresh Review 控件。Turn 2 的 Primary 在 World Model 返回
当前证据 Gap 后，Work State 的 plan/open item 明确保留 Source search/read，却直接提交 Limitation；它没有执行一次可用的 Source follow-up，
Reviewer 又以 empty claim assessments 批准该 Limitation。冻结的商品分类与 mall-search 两个异质问题未提交，因此继续保持 successor 的 unseen
复验资格。

## Evidence and first divergence

- `run-058` terminal receipt 为 `STOPPED_AFTER_DISPATCH`，Conversation/Turn 为 `1/3`，Ark dispatch `17`、request retry `0`、人工重复审批
  `0`、Production `NOT_EXECUTED`。Ark credential/TLS/HTTP dispatch 均为 `17/17/17`；DeepSeek credential/TLS/HTTP/dispatch 全为 `0`。
- Browser DOM 中 assistant `article` 只有 message body 与 Turn status；`engineering_chat_browser_ui.messageNode` 不消费 Turn 的 Package/Answer/
  Review/Delivery refs。`engineering_chat_browser._turn_view` 也没有 Citation 字段。另一方面，Agent Observation 已持有 `citation_refs`，其 authority
  receipt 保存 exact evidence class、source revision、locator、modality、content digest 与 Citation digest。因此最早 Citation 偏差是
  Agent→Application 的交付投影丢失，而不是 Source 没有签发证据。
- Turn 2 的两个初始 Primary call 选择 World Model；第三个 Primary call 在 BOUNDARY 已存在、Source operation 仍有效且从未尝试时把 phase
  改为 `RESPONSE_READY` 并返回 Limitation。旧 `_completion_policy` 只检查“任一 current BOUNDARY 是否存在”，所以把 `LIMITATION` 暴露在
  exhaustive response domain；decoder 无法拒绝。Reviewer 随后批准，但它是下游漏判，不早于 completion domain 的 Application 偏差。

## Classification and disposition

这是 `system-contract`：它新增一个跨 Agent/Application/UI 都必须一致的完成域不变量，并闭合既有“自然答案 + 可打开 Citation + fresh
Review”交付语义：

1. current World Model BOUNDARY 之后，如果第一次受权 Source Search 仍有效且未尝试，`LIMITATION` 必须离开 exhaustive response domain；
   Search 返回 read option 后，在第一次 Source Read 前继续禁止。一次实际 Read、一次没有 read option 的 Search、terminal Source denial
   或没有 effective Source operation 后，才可基于 current BOUNDARY 允许 Limitation。它不强制读取全部文件，也不阻止已有 SUPPORT 完整回答。
   该修复沿用 current
   `conversational-engineering-agent@8 / conversational-engineering-agent-no-tools-prompt@8 / ENGINEERING_AGENT_PRIMARY_INPUT@8` 协议族；每个
   Session/call 仍必须绑定修复后的 exact prompt/input digest，旧 request 字节不能代表新输入。
2. Agent 只沿 Draft Claim 的 support Observation 与 Draft boundary Observation 收集 Citation；Application 重算 authority identity，去重并把
   exact Citation metadata/digest 密封进不可变 Turn Result。未知、重复或 identity 漂移在 Browser 前失败关闭。
3. Browser projection 升级并在每条对应 assistant message 下默认展开 Evidence/Review panel；每项 Citation 可继续展开检查 exact revision、
   locator、modality、content/Citation digest。展示只读已密封 Turn，不产生新的 Source read，也不暴露未被 Draft 引用的 Package Citation。

Engineering Conversation 合同与 ADR-018 的实现状态已在同一变化中回写。确定性测试覆盖过早 Limitation 拒绝、一次 Source search 后的 honest
boundary、Citation authority identity 保留、tamper fail-closed、Browser projection 和真实临时 Git search/read 组合：直接责任层
`48/48` PASS，Agent/routing/launcher/runtime/artifact/CLI 受影响组合 `76/76` PASS，文档 `575` 项检查 PASS。该证据只形成 local candidate；
`run-058` 不被追认，fresh exact product successor 必须重新完成三轮 Browser chain，并继续使用两个未参与修复的异质问题。
