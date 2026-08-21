---
id: ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST
kind: roadmap-candidate
status: candidate
authority: planning-only
owners: [product, project, architecture, application, quality]
depends_on: [SYS-PRODUCT-SUCCESS, SYS-ADR-015, SYS-ADR-016, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, ITER-009-RESULT-SLICE-001-STOP-REDIRECT]
code: []
tests: []
coding_input: false
---

# Candidate：工程问题答案优先

## Trigger and evidence

ITER-009 已证明真实本机 Web、Snapshot-only 调查、独立 Review、Limitation 与 Citation 可以运行，但三条现场答案都被方法、分支、
静态调用、源顺序和返回值主导。无符号问题仍得到代码走读式正文，Reviewer 把这种正文的相关性与可读性判为通过；边界回答虽然没有
编造不存在的功能，用户仍看到候选数、召回能力和内部限制代码。用户方向反馈是系统像代码走读或代码实现说明，而不是工程问答助手。

这不是单一 Prompt 文风问题。当前 Question Need、查询操作、typed Result、Draft 完整性、Review obligation 和页面信息架构共同把自由
问题收敛为 `implementation-answer`。继续按原 SLICE-002 加固只会提高这一路径的稳定性，不能证明产品目标。

## Outcome

普通用户通过同一个本机 Web 提出自然工程问题后，首先得到针对其目标和抽象层级的直接答案、关键解释、证据边界和可核对 Citation；
代码实现只在问题明确要求或支撑结论确有必要时展开。系统不能回答时，应使用用户能理解的语言说明目前能确认什么、不能确认什么以及
缺少哪类知识，不能暴露内部候选、召回、Profile、authority 或限制代码。

本 Candidate 继续服务 `ROADMAP-M-002` 的长期目标，但明确挑战 `SYS-PRODUCT-SUCCESS` 与现行 WORLD_MODEL Contract 的“提问期完全
Source-off”实现边界。问题前仍构建 exact World Model；提问时由隔离检索 Worker 对同一授权 exact revision 的源码、仓库文档、构建
和配置执行只读检索，并与 Snapshot typed Result 一起密封当前问题的 Evidence Package。该模式必须在请求开始前显式固定，不能在失败后
静默切换到旧 Direct Investigation。Answer 与 Reviewer 都不能直接访问 Repository、Source 或检索工具，只能读取密封 Package。

这样仍保留版本固定、授权、复用和审计，同时避免“知识没有预先建模就只能拒答”。同步答案通过后，可把高质量证据和结论异步提议为
正式知识；知识沉淀成功与否不阻塞当前回答。采用前必须先形成 Finding，并更新拥有该边界的产品标准、ADR 和 Application Contract，
不能只在 Prompt 中绕开现行规范。

## General protocol

1. 问题理解形成用户目标、受众、期望抽象层级、待回答结论清单和证据需求；它们是原问题的通用语义投影，不是按关键词选择的题型枚举。
2. 受控检索先利用 exact Snapshot/Read Set 缩小范围，再由隔离 Worker 读取 allowlist 内同 revision 的必要 Source 片段；两类证据共同
   密封 Evidence Package。检索计划同时受原问题检查清单和 World Model 提示驱动；World Model 没有候选或候选无关时，不能阻断
   仍在授权与预算内的独立 Source 检索。Package 固定来源、操作、内容 digest、locator 和问题清单，不取得正式知识身份。
3. Draft 先回答结论，再组织必要解释、条件、影响与 unknown/limitation；代码细节放在确有需要的层级。每个重要结论绑定对应 Result。
4. 独立 Reviewer 从原问题重建检查清单，检查直接回答、抽象层级、正确性、完整性、相关性、可用性、证据和未知边界，并返回具体 finding
   与 rewrite instruction，而不只返回笼统 code。
5. 仅当现有 Evidence Package 足够时，允许在 digest 不变的同一 Package 上最多一次针对性重写并重新 Review。Reviewer 证明证据缺口
   时，Application 可以授权针对性补检索并密封新 Package；新旧 digest 和原因必须可见，不能伪装成同包重试。资源或安全上限耗尽时
   交付具体 Limitation 或失败关闭，不切换 Provider，也不因固定调用次数牺牲正确性或审核质量。
6. 页面以答案为主，结论级 Citation 可直接核对；Read Set、调用数、Authority、Trace、内部 Claim 和诊断默认折叠到开发者详情。

任何实现不得包含工程名、题目文本、关键词、类名、方法名、fixture 或 Oracle 特判。用途、架构、使用运行、故障定位、变更影响、业务
流程和实现细节只是验证覆盖维度，不是产品路由规则。

## Staged validation

### Stage 1：快速真实 Web 方向体验

在一个真实工程和同一 product-owned loopback Web 上，先用 4 条跨不同覆盖维度的自然问题及至少一条用户现场问题验证答案层级。
允许当前知识尚不支持的问题形成具体 Limitation，但至少 3 条应形成非“逐方法走读”的 supported answer。页面必须继续标记方向体验、
非验收、非生产，并保持 Source 只由隔离检索 Worker 读取、Secret 隔离、独立审核、Citation、零隐藏重试和失败关闭。

用户只裁决：它是否开始像工程问答助手、答案是否直接有用、代码细节是否按需出现、Citation/未知表达是否可接受。决定为
`CONTINUE / REDIRECT / REJECT`；没有 `CONTINUE` 不进入下一阶段。

### Stage 2：知识范围与跨工程夯实

方向确认后，再按真实问题缺口把仓库内文档、构建与运行配置、测试、API/数据结构等授权来源纳入预构建 World Model 和同步检索的统一
证据协议，并用第二个未参与实现的工程验证。每个新增知识域必须能与已有声明、调用和行为证据在同一答案中组合，不能形成平行入口或
题型专用实现。

同时完成 current identity 的资格、完整回归、安全、早期 hidden canary、成熟源码 Agent 对照、逐层偏差诊断、成本和正向价值测量。

### Stage 3：正式验收

产品代码冻结后才执行最终未见工程、跨类型自由问题、现场问题和独立对照。重大错误为零、逐题完整性不低于成熟源码 Agent、Citation
支持重要结论；Source 读取只发生在授权检索 Worker 且与 exact Evidence Package 对账，Answer/Reviewer 的 Source/Update/Direct tool
访问为零，并由用户作出 `ACCEPT / REDIRECT / REJECT`。本机 PASS 不产生 Production Activation。

## Stop conditions

- 默认答案仍以方法、分支、调用顺序、内部对象或诊断术语为中心；
- 只有通过问题、工程、关键词或符号特判才能改变回答层级；
- Reviewer 仍批准未直接回答、抽象层级错误、关键结果含糊或无关 Citation；
- 为获得自然答案必须让 Answer/Reviewer 直接访问 Source、开放未授权路径、静默 Direct fallback、Secret、公网监听或取消独立审核；
- supported 结论有重大错误，或 Limitation 暗示了证据无法支持的不存在/完整性结论；
- 用户决定 `REDIRECT` 或 `REJECT`。

本 Candidate 是规划输入，不是编码、Provider 调用、Web 运行、隐藏披露或 Production Activation 授权。
