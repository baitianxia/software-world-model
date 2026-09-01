---
id: FINDING-010-258
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai, security, quality]
depends_on: [ITER-010-PDR-014, FINDING-010-257, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/lightweight_engineering_agent.py, src/software_world_model/ai_infrastructure/lightweight_engineering_model.py, src/software_world_model/interface/lightweight_engineering_chat.py, src/software_world_model/interface/engineering_chat_session_runtime.py]
tests: [tests/test_lightweight_engineering_agent.py, tests/test_lightweight_engineering_model.py, tests/test_engineering_chat_provider_runtime.py, tests/test_engineering_chat_session_artifact.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: adopt-lightweight-loop-with-explicit-application-delivery-control
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-258：Phase A 最小循环可绕过旧回答协议而保留安全边界

## Observation

从 PDR-014 基线建立的干净候选证明，现有 Conversation、Provider route、Gateway、只读 Source Broker/Worker、authority receipt 和 Citation
可以在不继续 Claim/Boundary/content-unit 回答协议的情况下复用。必要的新产品面只有紧凑目标/计划、Source action、Observation、停止判断、
自然回答和 fresh 独立 Review。

旧 Response Control 与旧 Draft/Review 证明结构强耦合，不能直接用于轻量答案而不把已终止协议重新带回候选。因此轻量路径使用新的
Application-owned one-use Delivery Control：它只在 fresh Reviewer 成功回执、空 Finding、Answer 的非空 Citation、每项 Citation identity
可重算且 source revision 与 Turn Binding 完全一致时放行。Agent 和 Reviewer 都不能创建或重复消费 Delivery Authorization。

Source adapter 仍通过已有受信请求和 authority receipt 执行 exact-revision search/read；轻量模型只看 Application 分配的数字
`read_index` 和 Observation/Citation ordinal，不制造 locator authority。每次模型调用又自动产生绑定 product/source/session/route、完整
disclosure digest、共享 budget、Provider binding 和 Secret Reference 的 one-use runtime authorization；模型仍无文件、Shell、网络、凭据或
写权限。

## Evidence

- 确定性三轮测试覆盖两个异质问题和一个语义追问；每轮 trajectory 均为 `SEARCH_SOURCE → READ_SOURCE → FINISH → independent review`，
  三次计划随 Observation 改变，最终答案携带 exact-revision Citation，Work State 从 Revision 1 连续到 Revision 3；
- Provider runtime 与 artifact-session preparation 定向测试 14/14 通过，证明新增输出能力装配没有在准备阶段解析凭据、读取 Source、创建
  attempt 或网络 dispatch；
- 轻量模型边界测试验证每次真实调用的完整 disclosed-input digest/bytes、exact product/source/session/route、共享 fuse、Secret Reference、
  Provider dispatch receipt 与 malformed-output failure truth；terminal receipt 读取当前轻量模型审计而不再误读未执行的历史模型边界；
- 旧 `conversational_engineering_model.py` 和对应测试相对 `8131cae` 净行数均为 0；轻量方向检查 PASS；
- 方向检查原先把“引用基线已有工具请求身份”误判为“新增旧协议版本”。检查现改为只拒绝 trusted baseline 中不存在的新 token，并增加
  正负测试；这允许最薄安全适配，但仍阻止协议版本扩张。

## Disposition

Engineering Conversation 当前加入 PDR-014 capability-oriented execution profile，并明确其在冲突时覆盖同文档内旧版本化 Answer/Review
实现细节。Phase A 的真实 Provider/browser 两题一追问仍须用 exact candidate artifact 执行；在该证据出现前，本 Finding 只接受本地 harness
与边界设计，不宣称浏览器基线或 MVP 已完成。
