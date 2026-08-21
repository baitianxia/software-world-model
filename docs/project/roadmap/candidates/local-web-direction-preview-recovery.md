---
id: ROADMAP-CANDIDATE-LOCAL-WEB-DIRECTION-PREVIEW-RECOVERY
kind: roadmap-candidate
status: candidate
authority: planning-only
owners: [product, project, architecture, application, quality]
depends_on: [SYS-PRODUCT-SUCCESS, PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ITER-007-RESULT-SLICE-001-STOP-DECISION]
code: []
tests: []
coding_input: false
---

# Candidate：本机 Web 方向体验恢复

## Trigger

用户报告 ITER-008 的后续开发在 Codex/OpenAI 客户端遇到 `Invalid prompt: your prompt was flagged as potentially violating our
usage policy`，当前开发对话无法继续。该错误在 ITER-008 的项目文档和本机运行证据中没有对应记录，因此只能先归类为
**外部开发工具的提示词准入阻断**，不能据此断言产品运行时、DeepSeek、Provider 配置或 ITER-008 架构违反政策。

与此同时，本机已有更直接的产品证据：ITER-008 run-012 的正式产品冻结 PASS，且同一候选已经从正式 Web 成功回答“登录流程”并
给出四个 Citation；第二个“下单流程”边界问题在四次 Provider HTTP 200 后，由 Draft 正确形成 Limitation，却被 Review 以
`QUERY_INCOMPLETE` 拒绝。因此，当前最快的产品路径不是继续扩大 Prompt、Schema 或资格套件，而是先复用已跑通的 Web 链确认
“问题—证据—自然答案—独立审核—Citation”方向，再处理通用的 Limitation 交付边界。

## Evidence classification

| 类型 | 当前内容 | 计划中的处理 |
|---|---|---|
| 已验证事实 | clean HEAD 为 `2cd743b2…753`；run-012 freeze PASS；登录题真实 Web 成功；下单边界题在 Answer/Review 衔接处失败关闭 | 作为新计划的只读 baseline，不把候选运行误写成 Acceptance |
| 用户报告 | Codex/OpenAI 客户端返回提示词准入错误并阻断继续开发 | 作为外部开发工具阻断处理；补收 receipt 后再缩小具体阶段 |
| 尚未证明 | 错误是否来自产品 runtime、是否已外部分派、具体 request/model/provider，以及哪段文本触发 | 不猜测、不用改产品配置或切换产品 Provider 来“修复” |
| 未接受资产 | 当前工作树中尚未接受的 `1.5.12` Prompt、资格和 Answer/Review 修改 | 原样保留并隔离审查；不作为新一轮 baseline，不整包继承 |
| 规划判断 | 先启动已冻结 Web 做最小真实体验，再决定继续、转向或拒绝 | 本 Candidate 只描述顺序，不授权编码或运行 |

## Outcome

尽快交付一个普通用户可从浏览器操作的本机方向体验版：无需认证，输入自然语言问题后能看到自然答案或诚实限制，并能打开实际
Citation。首次体验只验证产品主线是否值得继续，不承担完整泛化、性能、生产可用性或最终验收。

本 Candidate 若被选择，仍推进 `ROADMAP-M-002` 的 Step 1，不新建另一条产品目标。由于 ITER-008 已发生正式执行，任何换路都应先
按其 Result 证据形成 `REDIRECT` 或 `REJECT`，再建立并授权新的 Iteration；不得在本规划文档中静默重启 ITER-008，也不得把本
Candidate 当作编码授权。

## Non-goals before direction confirmation

- 不扩展第二语言、第二类知识域、多工程管理、认证或公网部署；
- 不执行完整 hidden suite、成熟源码 Agent 最终对照、性能优化或 Production Activation；
- 不为了形成体验版重写整套 Prompt、Schema、Oracle、能力资格或治理证明；
- 不以固定问题、工程名、类名、方法名或关键词分支实现答案；下列体验题只是验证输入，不是产品逻辑；
- 不以减少模型调用次数作为质量目标；独立 Review、Citation、只读和失败关闭边界保持。

## Prompt-admission recovery rule

开发工具提示采用“明确目标、强约束、明确输出合同，不规定每一个内部推理步骤”的短任务结构；每次只交付一个可验证的小任务，
避免把完整历史、治理规则和实现细节重复拼入同一个开发提示。该原则与
[OpenAI reasoning prompting guidance](https://developers.openai.com/api/docs/guides/reasoning#advice-on-prompting) 一致。

该调整是正常的任务拆分，不是绕过安全策略：不得混淆、编码、拆字或同义改写被拒文本来规避检查，也不得自动重复提交同一被拒
提示。如果一个最小、正常的软件开发任务仍被客户端拒绝，保留错误 receipt，将该开发执行面标为 unavailable，并由项目 Owner
选择受支持的开发执行面；产品 runtime 和 Provider route 在没有产品证据前保持不变。

如果相同错误后来由产品 runtime 的真实请求复现，则作为独立产品 Finding 处理：请求失败关闭、零隐藏重试、同一请求内不切换
Provider；只有在方向被确认后，才设计更短且职责单一的产品 Prompt，并把权限、预算、引用和状态约束继续放在 Application 与
typed contract 中。任何产品 identity 变化都必须重新取得适用的资格证据。

## Staged delivery plan

### Stage 0：保全与分流，目标不超过 2 个工程小时

1. 记录 clean baseline、run-012 freeze、正向 browser result 和边界 terminal 的 exact digest/path；
2. 原样保存当前未接受工作树，不删除、不覆盖、不把它复制进新 baseline；
3. 若客户端可提供 receipt，记录错误发生时间、任务、请求阶段、request/model/provider identity 和是否 dispatch；没有 receipt 就保持
   `external-development-tool-admission-unknown`，不阻塞 Web 体验；
4. 将后续开发提示拆为“一条目标、一组不可变边界、一个输出合同、一个验证命令”，先用纯规划/只读任务验证执行面可用。

**退出条件：** 已接受/候选/未接受资产明确分开；提示词错误没有被误归因；没有产品代码变化。超出 timebox 仍无法取得 receipt 时，
记录未知并继续 Stage 1，不在诊断上消耗首个体验窗口。

### Stage 1：Web 方向体验版 V0，目标半个工程日内

优先从 run-012 的 exact frozen candidate、Snapshot、Bundle、资格和正式 Web 入口重新形成一次本机评测运行，不修改产品逻辑。若旧的
一次性授权已消费，只允许按同一 exact identity 重新形成新的本机 evaluation authorization；这不等于接受或生产启用。

体验版必须：

- 只监听 `127.0.0.1`，无需普通用户认证，显著显示“方向体验 / 非验收 / 非生产”；
- 固定一个已发布的演示工程、revision 和 Read Set；普通问题入口不接收 repository、Source、Update 或 Direct 参数；
- 提问时 Source、Update、Direct fallback 为 0，Answer 看不到 Provider secret、Oracle 或 baseline；
- 保留 2—4 次有界调查、Draft、独立 Review、真实 Citation、零隐藏重试和失败关闭；
- 先完成一条已知 supported 的多步骤问题，再完成一条不含类名/方法名的等价改述；
- 对当前已知边界失败明确显示为“尚不能交付可靠结论”，不得显示无关登录证据或伪造下单结论。

已密封 browser result 可以作为页面/答案/Citation 的辅助回放，但静态回放不算完成本 Stage。只有普通用户实际提交新问题并看到
结果，才叫“可体验 Web 版本”。

**退出条件：** 浏览器可交互；至少一条 supported 问题及其等价改述无重大错误；Citation 可核对；边界失败诚实可见；安全计数不
退步。若 exact run-012 在不改代码的条件下无法启动，停止并记录启动阻断，不先开发更多内部组件。

### Stage 2：用户方向 Gate，体验完成后立即执行

用户围绕四点判断：输入与交互是否自然、答案组织是否有用、Citation 是否帮助核对、无法确定时的产品表达是否可接受。决定只能是：

- `CONTINUE`：证据—答案—审核—Citation 主线值得继续，允许进入通用边界修复与工程夯实；
- `REDIRECT`：产品价值仍在，但答案/审核职责或交互方向需要改路；终止当前实现路线并另建 Proposal；
- `REJECT`：该产品主线不值得继续；保留证据并停止扩张。

没有新的明确 `CONTINUE`，不得进入 Stage 3。V0 能打开或测试 PASS 均不替代该决定。

### Stage 3：最小通用修复与工程夯实，仅在 CONTINUE 后

1. 以“Draft 形成 typed Limitation 后，独立 Review 应检查其证据边界并允许交付”为通用合同修复 Answer/Review 衔接；
2. 不加入“登录”“下单”、工程名、类名、方法名或问题文本特判；用 answerable、insufficient-coverage、bounded-negative 三类通用
   fixture 验证；
3. 单独审查当前未接受工作树，只按 Finding 逐项选取仍有证据支持的最小变化；边界修复与 Prompt 调整分开提交和验证；
4. 产品 identity 变化后重新完成必要的 Conformance、Capability 和 formal freeze；调用次数由正确性和独立审核需要决定，不能为了
   配额减少调查或审核；
5. 执行 focused tests、相关跨模块回归、完整回归、Source-off/Secret/authorization 检查和真实浏览器正向/边界 smoke；
6. 增加第二个未参与实现的真实工程和少量独立问题，确认不是 demo 工程特判。

**退出条件：** 同一 Web 能交付 supported answer、具体 Limitation 和可核对 Citation；边界题不再变成内部失败；无问题/工程特判；
完整回归和安全门禁 PASS。

### Stage 4：正式验收

在 Stage 3 冻结后才执行 hidden canary、成熟源码 Agent 同题对照、现场临时问题、跨域问题、成本/时延报告与架构 Reflection。任何
产品修改都会烧毁相应隐藏证据并重新冻结。最终由用户作出 `ACCEPT / REDIRECT / REJECT`；本机 PASS 不推导 Production
Activation。

## Direction-preview questions

首次体验只使用少量代表性问题，避免为测试集优化：

1. **Supported multi-step：** 询问一个已有证据的完整行为流程；
2. **No-symbol paraphrase：** 不给类名或方法名，用业务语义询问同一流程；
3. **Boundary：** 询问演示工程中尚无足够发现证据的能力，检查系统是否诚实表达限制；
4. **User ad hoc：** 用户现场再提一题，不提前进入实现 Prompt。

前三类冻结的是能力类型和裁决规则，不把 exact 文本写入产品逻辑。方向体验只需确认主线；它不能替代后续独立 hidden evidence。

## Stop and redirect conditions

出现任一项立即停止当前路线，不以更多内部开发掩盖：

- 已冻结 Web 不能在 timebox 内形成一条新的真实浏览器结果；
- 只有固定问题/关键词/工程特判才能得到可接受答案；
- 为运行体验版必须开放 Source、Update、Direct fallback、Secret 或公网监听；
- 独立 Review 必须取消或弱化才能交付答案；
- 最小正常开发提示在受支持执行面仍持续被准入拒绝，且没有可审计的合规执行路径；
- supported 问题有重大错误、Citation 不能支持结论，或 boundary 只能编造/引用无关证据；
- 用户决定 `REDIRECT` 或 `REJECT`。

## Naming

- **方向体验版（Direction Preview）：** 用真实入口确认产品方向的早期候选，不是验收版；
- **工程夯实（Hardening）：** 方向确认后补齐通用边界、回归、资格和运行质量；
- **正式验收（Acceptance）：** 用冻结、独立和现场证据决定产品增量是否成立；
- **准入阻断（Prompt Admission Block）：** 请求在开发工具或模型服务的提示词政策入口被拒，尚不等于产品架构故障；
- **Limitation：** 证据不足以可靠回答时，面向用户交付的具体限制，不是成功答案，也不是内部异常。

## Selection requirements

选择本 Candidate 前，Product/Project Owner 必须先对 ITER-008 形成基于现有 Web 证据的 continuation decision，并明确授权新 Proposal。
新 Proposal 应只授权 Stage 0—2；Stage 3 必须等待方向体验后的新 `CONTINUE` 消息。新 Iteration 不继承 ITER-008 的 Acceptance，
且任何代码 identity 变化均不得继承旧资格裁决。
