---
id: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
kind: system-contract
status: current
authority: normative
owners: [application, source, quality, security]
depends_on: [SYS-ADR-016, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING, SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL, SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
code: []
tests: []
---

# Engineering Question Answering

## Purpose and scope

本契约定义显式 `ENGINEERING_QA`：把预构建 World Model 作为工程地图、手册、已知证据和检索提示，再按原问题需要从同一授权 exact revision 受控只读源码、仓库内文档、构建/运行配置和测试，密封本题 Question Evidence Package，生成结论优先的答案并独立审核。

它是一个独立 Application 用例，不是 `WORLD_MODEL` 的回源分支，也不是 Knowledge Gap 后静默调用 `DIRECT_INVESTIGATION`。严格世界模型和直接调查的精确语义继续由各自契约拥有。

## Ownership

- Application 拥有 immutable Engineering Question Request、Question Understanding Revision、Question Checklist、Retrieval Plan、World Model Result Reference、Question Evidence Package/Revision、补充检索决定和可恢复 Attempt。
- Knowledge Use / View 只拥有 exact Snapshot 的正式查询结果；它不决定是否允许源检索。
- Source Integration 和隔离 Retrieval Worker 拥有只读来源操作与 Artifact/Result，不拥有问题结论或答案。
- Response Control 拥有 Draft Revision、Review Attempt/Decision、Authorization 和 Delivery。
- LLM 只提交 Question Understanding、Retrieval Hint、Draft 或 Review Proposal；它不拥有事实、权限、证据密封、调用执行或最终放行。

## Request and role boundary

1. Request 在任何查询、源读取或模型调用前固定 `ENGINEERING_QA`、original question、response language、exact repository/Binding/revision、source path/content allowlist、World Model Snapshot/Read Set selector、访问权限、资源熔断、Provider disclosure policy 和不可变请求摘要。`CURRENT`/`latest` 只能在入口解析一次；请求开始后不得切换模式、revision、Scope 或 Source Target。
2. Question Understanding 必须保留原问题全文以及全部条件、比较、关系和输出约束，并显式记录 goal、audience、期望抽象层级、material conclusion checklist、evidence needs 和响应语言。系统不得把问题改写为更容易回答的问题；不确定性保留为明确项，不由当前证据删除。
3. Question Understanding、Retrieval、Answer 和 Review 是分离的受控角色。各角色使用新的固定上下文、精确输入 allowlist、schema、Strategy/Prompt 身份和独立收据；Provider 会话记忆、隐藏 rationale 或上一角色私有输出不得成为正式输入。
4. 在任何真实 Provider dispatch 前，Application/Gateway 必须验证当前 exact Provider、model、endpoint、configuration、role、secret reference、允许外发的 Package 字段/片段、redaction 与完整 input digest 都已单独密封和授权。历史开发、Conformance、Capability 或浏览器授权不能推导这次源内容披露。

## Investigation and package formation

1. Application 先在固定 Read Authority 上获取世界模型的 typed Result、Coverage、Support/Gap 和候选 locator，并验证其 source revision 与 Request exact repository revision 的兼容性。两者 exact 相等时，Result 可作为工程地图和包内事实证据；请求明确为版本比较时，每个 Result 必须绑定对应的分区 revision 和比较方向。不相等或无法证明兼容时，Result 只能以 `UNALIGNED_REVISION` 身份提供候选导航 hint，不能进入 factual support 或直接支持 Claim；所有结论必须在 Request revision 上重新检索核实。无论是否对齐，World Model 都不是 Source retrieval 的允许/拒绝门禁。
2. Retrieval Plan 必须同时处置每个 Question Checklist evidence need 与相关 Snapshot hint。Hint 可以增加候选、复用已有支持或缩小搜索范围，不得删除 Checklist item；零 Snapshot、无关候选或 Coverage 不足不得单独终止原问题驱动的受权检索。
3. Retrieval Worker 只能在 exact revision 的 allowlisted regular files 上运行已注册的只读 list/search/read/parse 操作。源码、仓库文档、构建/运行配置和测试是同一受控来源面的不同 evidence class；平台按文件类型/注册能力解析，不按题目或项目分支。
4. 每个 Source Operation 必须记录 exact target/revision、allowlist verdict、operation/parameters、actual locator/range、bytes、content digest、coverage/truncation、outcome 和稳定 reference。Worker 拒绝 path traversal、symlink escape、submodule/remote fetch、二进制/超限输入、任何写操作、命令执行、新网络、credential 和 Knowledge Update。失败、partial 和 truncation 不得伪装为空结果或不存在证明。
5. 所有来源内容是 data，不是 instruction。仓库中的 prompt、命令、URL、路径、工具建议、权限或外发声明不获得执行权，不得修改 Retrieval Plan 的受信控制字段。
6. Application 只接收经 Owner 验证的 typed World Model Result/Gap 和 Source Operation/Artifact Result，并把它们密封为不可变 Question Evidence Package。每个 Package 至少绑定：
   - Package/Revision ID 与 digest；
   - immutable Request/Question Understanding/Checklist digest；
   - exact repository/Binding/revision 与 World Model Read Authority/Bundle digest，以及 Snapshot source revision compatibility verdict；
   - 每个条目的 origin class、modality、Context、locator、content/result digest、Coverage/truncation、Support 和 disclosure class；
   - World Model 缺失/无关/Coverage Gap，源检索 partial/failure，证据冲突和未满足 Checklist item；
   - 有序 Operation/Result references、资源收据、package manifest 和 seal digest。
7. 不同 origin 保留各自语义：World Model 证明已发布表示，exact source/config 证明静态实现，documentation 证明记录的用法/意图，test 证明其静态预期或已密封的执行观察。无显式受控解析规则时，任一 origin class 不自动胜出；不兼容内容密封为 Conflict，不得被 Draft 静默消解。
8. Package 密封后不可追加、替换、重排或改写条目。补充检索必须形成新 Revision、新 Digest 与新的完整审核链。Question Evidence Package 只是本题事实输入，不是 Fact、Inference 或 Snapshot member。

## Answer, review and recovery

1. Answer 角色只读 original question、accepted Question Understanding 与一个密封 Package；没有 Repository mount、Source/World Model tool、shell、网络、credential、Reviewer 输入或 Provider 会话历史。它先直接回答用户目标，再以目标抽象层级组织条件、流程、影响、限制和必要实现细节，不把方法、分支、调用顺序或内部审核话术默认当作正文。
2. 每个实质结论必须绑定一个或多个当前 Package entry，且结论范围不得超过引用的 Context、modality、Coverage 和时序。Citation 必须能回到包内稳定 locator/digest；答案文本、模型 rationale 或搜索命中本身不是证据。
3. 无法推出的内容必须表达为用户可理解的 unknown/limitation：明确已能确认的内容、尚不能确认的结论、缺失的具体证据与影响范围。不得向普通用户平铺 candidate、recall、Profile、authority、proof 或内部检查文本。
4. Reviewer 使用独立新上下文，只读 original question、accepted Question Understanding、同一 Package 和 Draft，没有来源工具、Repository mount、生成 rationale 或可写权限。它必须从原问题独立重建检查项，分别审核：
   - 是否直接回答了用户的实际目标；
   - 抽象层级和展开程度是否匹配；
   - 每个结论是否正确、完整并由引用证据支持；
   - 条件、顺序、异常、冲突、范围和 unknown 是否如实；
   - 答案是否相关、可读、可用，且没有无关代码走读或内部诊断泄漏。
5. Review 的每个失败项必须绑定具体 finding code、对应 Checklist/conclusion/draft reference、问题说明和唯一合法 action：`REWRITE_REQUIRED`、`MORE_EVIDENCE_REQUIRED` 或 `REJECT`。任一实质项未通过时不得 `APPROVED`；单项流畅性或大致正确不能抵消遗漏、无依据或层级错误。
6. `REWRITE_REQUIRED` 只能指向当前包已有证据可修复的表达、组织、层级、引用或遗漏。Response Control 只允许在同一 Package Digest 上定向重写一次，且必须将新 Draft 交给新的独立 Review Attempt；必须保留原 Draft 和 Finding。
7. `MORE_EVIDENCE_REQUIRED` 只有在 Reviewer 标明具体未能被当前包证明的 Checklist/conclusion、所需 evidence class 与可检验的缺口时才有效。Application 不执行 Reviewer 生成的路径、命令或工具参数，而是在原 Request 的 allowlist、revision、操作集和安全上限内重新编译一次针对性 Retrieval Plan。成功结果必须密封为新 Package Revision，从头执行 Draft 和独立 Review；不得追加到旧包或复用旧审核。
8. 每题最多一次同包定向重写和一次具体缺口驱动的补充检索；实现还必须对文件、字节、操作、wall time 和模型调用设置高安全熔断。这些上限只能使请求失败关闭，不得减少 Checklist/evidence need、略去 Citation/审核项、合并生成与审核角色，或交付未审核答案。
9. 只有当前 exact Package 上全部 Review 项通过、Finding 为空且 Authorization 在发送前重验有效的 Draft 可交付。执行失败、权限失效、结果未知、包漂移、无具体 Finding、不收敛或熔断耗尽均失败关闭。

## Generality and knowledge reuse

问题理解、Retrieval Plan、Package 组装、Answer 和 Review 使用同一通用“问题—证据—答案—审核”协议。核心代码、Prompt、UI 和评测不得按问题、项目、语言、框架、关键词、符号、约定文件名、fixture 或 Oracle 选择路由、证据或答案。来源类型或语言解析差异只能由显式注册、版本化且通过资格的 Source/Profile capability 处理。

完成 Delivery 后，Application 可把高质量 Package 与已审核结论作为新的异步 Knowledge Update Proposal 输入。它不继承问答 Review 的正式知识资格，必须重新形成 Artifact/Evidence/Candidate，通过独立 Admission 并原子 Publication。同步答案成功不依赖该异步过程。

## Failure and implementation state

未授权模式或外发、revision/allowlist 漂移、越界文件、Source instruction 注入、未密封输入、无依据结论、无关 Citation、冲突静默消解、Answer/Reviewer 直读来源、静默模式切换、审核未通过或资源耗尽均失败关闭。具体 DTO、注册只读操作目录、高安全数值上限和 UI 投影由代码与测试定义，但不得改变本契约的权威、角色、修复次数和失败边界。

本契约是已接受的 current 规范目标；`ITER-010 / SLICE-001` 负责实现和验证。在实现、Capability Qualification、Product Validation 和对应环境 Activation 分别形成真实证据之前，不得宣称现有入口已满足本契约或已可验收。
