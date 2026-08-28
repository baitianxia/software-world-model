---
id: FINDING-010-154
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, application, ai, security, operations, quality]
depends_on: [FINDING-010-140, SYS-ADR-019, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION, SYS-CONTRACT-AI-MODEL-GATEWAY]
code: [src/software_world_model/application_services/public_source_model_authority.py, src/software_world_model/application_services/conversational_engineering_routing.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py, src/software_world_model/interface/engineering_chat_session_artifact.py]
tests: [tests/test_public_source_model_authority.py, tests/test_conversational_engineering_model.py, tests/test_conversational_engineering_routing.py, tests/test_engineering_chat_session_artifact.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: implement-public-source-standing-authority-machine-derivation-chain
target: src/software_world_model/application_services/public_source_model_authority.py
---

# FINDING-010-154：文档站立授权尚未进入 Session/Turn/call 运行时链

## Observation

当前 System Contract 与 ITER-010 已明确接受公开来源 standing authority，但 product runtime 仍只接受
`authorization_message_digest`，并把 Session ref 硬编码为 `codex-user-message:<digest>`。因此已有的逐 Turn Provider attempt、逐角色
disclosure authorization、Gateway consume 与 DeepSeek admission 虽然都是 exact/one-use，却没有可验证的 standing parent；旧 Artifact
Session `@3` 可以装载并运行，但不能证明人工重复审批请求为 0，也不能机械区分 standing scope 与任意配置自述。

这是 `FINDING-010-140 / SYS-ADR-019` 已定义语义的运行时实现缺口，不是新的权限模型或用户授权不足。若继续用旧字段启动真实体验，会把
文档决定冒充 live 能力。

## Root cause

- Artifact Session schema 没有明确的 standing-authority closed object、source-publication identity 或 parent digest；
- source preparation 只解析 exact revision，不验证 local mirror 的 canonical upstream、clean HEAD、exact tree 与许可证路径对象；
- Provider Session authority 只接受 exact user-message ref，导致 Turn attempt 与 role receipt 只能绑定旧 Session digest；
- terminal/public receipt 没有直接展示 standing parent、exact public-Source Session child 或人工重复审批计数。

最早责任层是 trusted artifact/Application composition，不是 Gateway、Provider Adapter、模型 Prompt 或 Browser。

## Disposition

实现一个通用、与 mall/题面无关的两层 authority chain：

1. `PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY@1` 密封 human evidence ref/digest、authority evidence、purpose、Source Authority、canonical
   HTTPS upstream、license/path、revision policy、exact commit/tree、Source Profile/allowlist/exclusion、qualification-independent
   Provider/model/endpoint/Adapter/credential account/disclosure/admission scope、预算、时窗与 loopback `EVALUATION_ONLY` Sink；
2. Artifact Session `@4` 删除兼容名 `authorization_message_digest`，在 listener、Source disclosure、credential 或 network 前重验 private
   closed document、clean product、public mirror metadata、World Model、current qualification/config 与 admission input，并派生 exact
   `PUBLIC_SOURCE_MODEL_SESSION_AUTHORITY@1`；
3. 两条 Provider Session authority、每 Turn `ENGINEERING_PROVIDER_ATTEMPT_AUTHORITY@2` 与每次
   `SWM-ENGINEERING-AGENT-ROLE-DISCLOSURE-AUTHORIZATION@2` 都直接或经 immutable digest chain 绑定 standing parent；既有 one-use consume、
   dispatch fuse、zero retry 与 terminal audit 不放宽；
4. launch/terminal/public status 显示 parent/Session digest 和 `human_approval_request_count=0`。旧 `@1—@3` 保持 exact-human-delta 只读兼容，
   不取得新 preparation 状态。

本地正向、伪造 authority、Source upstream/clean/tree、Provider scope、预算、过期、Turn parent 和 one-use call parent 测试已通过。该处置只证明
`PUBLIC_SOURCE_STANDING_AUTHORITY_DERIVATION_LOCAL_CANDIDATE`；current mall `@4` artifact、真实 Provider dispatch、terminal reconciliation、
Citation 与 Browser 体验仍未执行，`V-PUBLIC-OSS-AUTHORITY-001` 和 `V-MVP-EXPERIENCE-001` 保持 `NOT-RUN / blocking`。本地 message digest
与配置仍不是平台认证签名或不可绕过的远端 trust root。
