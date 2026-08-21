---
id: FINDING-010-011
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai-infrastructure, application, interface, security, quality]
depends_on: [ITER-010-SLICE-001, FINDING-010-003, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-QUALITY-SECURITY]
code: [src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py, src/software_world_model/interface/engineering_qa_live.py, src/software_world_model/interface/engineering_qa_browser.py, src/software_world_model/interface/engineering_qa_browser_ui.py]
tests: [tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py, tests/test_engineering_qa_live.py, tests/test_engineering_qa_browser.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: narrow-one-exact-user-run-authorization-into-one-use-full-input-role-disclosure-grants-and-revalidate-at-the-gateway
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-011：结构化输出 receipt 不是 Provider 披露授权

## Observation

`FINDING-010-003` 已封闭五类角色输入/输出，但其 output source 仍只有确定性 fixture。直接把 role Manifest 交给现有 `ModelGateway` 会缺少
三项机械证明：immutable Request 本身允许当前 disclosure policy；动态产生的每个完整角色输入已在 dispatch 前取得一次性授权；Gateway
侧独立重验同一用户 run grant、Prompt/schema、Provider configuration 与角色顺序。历史 DeepSeek Conformance 只能证明 Adapter wire，
不能授权新的 Cognition/Ledger/Package 内容。

## Evidence and root cause

- Role input Manifest 固定 `external_disclosure_status=NOT_AUTHORIZED`，正确地阻止开发 receipt 被误当授权，但此前没有后续授权边界；
- Answer/Review 等动态输入在前一模型 Result 后才形成，无法只用一个预先猜测的 input digest 列表；
- 现有 Gateway 能记录 Manifest/configuration receipt 与 Adapter qualification，却不知道 ITER-010 用户对哪个根 Request、哪些 role fields 和
  哪个 product subject 的披露授权；
- 浏览器固定 factory 只允许 `NO_EXTERNAL_DISCLOSURE`，health/developer details 也固定报告零 dispatch，因此真实组合不能诚实呈现；
- 根因是把 Provider Conformance、产品 run authority、每次内容 disclosure 和 output receipt 四种不同证明停在了接口两侧，没有建立可验证
  的 narrowing chain。

该链决定跨 Application/Gateway/interface 的安全不变量，分类为 `system-contract / systemic`。

## Decision and disposition

- 每个 role Manifest 显式绑定根 `request_digest`；Question/Initial 从 Request 取得，Verification/Answer/Review 从 current Package 链取得，
  防止跨问题内容混用；
- 用户级 Run Disclosure Authorization 必须绑定 exact Request（且该 Request 已选择当前 disclosure policy）、evaluation subject、Provider/
  model/endpoint/Adapter/configuration fingerprint、qualification/expiry、secret reference、Prompt/output contract digest、角色集合、总调用上限、
  redaction、授权消息摘要、`NOT_EXECUTED` Activation 和 no-retry/no-switch；
- 每个动态角色调用在 dispatch 前形成完整 Disclosure Request，密封 role/context/root Request、完整 Gateway Manifest/full input digest、所有
  model-visible JSON leaf path、片段摘要、payload bytes、output schema、Prompt、Provider binding 和资源上限；受信 authorizer 只能按顺序把
  Run Authorization 收窄为 `maximum_dispatches=1` 的 exact sub-authorization；
- Source 在 Gateway 边界前消费 sub-authorization。此后任何 exception、outcome unknown、资格/identity drift 或 replay 都写一次 audit 并
  终止，绝不 retry 或切 Provider；secret reference 与 authorization receipt 均不进入模型消息；
- Gateway-side Policy 独立重验 run grant、三项 Manifest（instruction、sealed role input、model-invisible run authority）、完整 payload
  identity、root Request、current Prompt/schema、Provider/configuration/qualification 和由前一结构化输出决定的角色顺序；Result 再验证
  conformance receipt、actual model fingerprint、usage、eligibility 与 digest；
- DeepSeek composition 只复用 current exact Conformance 来构造 Adapter/Gateway，不继承 ITER-008 Capability/Product/Disclosure；真实
  Request/run grant 仍属于 ITER-010；
- Web live 组合只能使用一个 exact prepared Request factory，health 与 developer details 显示真实 Provider/run binding；本地确定性 factory
  继续机械禁止外发。页面始终是 Direction Preview / NOT_ACCEPTANCE / NOT_PRODUCTION。

主处置同步进入 Engineering Question Answering Contract 与安全/本机浏览器说明。它没有执行真实 Provider、listener/browser、hidden、
Slice2/3 或 Production Activation；这些证据仍须 exact product freeze 后另行形成。

## Verification

确定性测试证明：本身为 `NO_EXTERNAL_DISCLOSURE` 的 Request 不能获得 run grant；另一 Request、过期 grant、重复 input、重复授权、错误角色
顺序和 Conformance identity drift 均失败关闭；provider outcome unknown 恰好一次且不可重试；完整 input leaf/fragment digest 与子授权一致；
wire 中不存在 secret reference 或 authorization ref。另以真实 DeepSeek Adapter + ModelGateway + policy 的 fake transport 组合验证单一 system
message/closed schema、actual model/usage/receipt 和 Web exact-runtime metadata，未读取 credential、未建立网络连接。
