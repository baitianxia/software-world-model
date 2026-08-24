---
id: FINDING-010-047
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-046]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_model_source.py, tests/test_engineering_question_strategy.py, tests/test_engineering_qa_live.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: refine-required-evidence-closure-and-condition-finish-output
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-047：全注册来源闭包扩大调查，FINISH Schema 未表达 outcome/observation 联动

## Observation and evidence

`FINDING-010-046` 的 Application closure 修复形成 clean candidate
`8575517f446786d0e8a3c8dcc754b39490e6496d` / tree
`e0d185143a8291c3675b16de39c1a61d924e119b`。fresh DeepSeek Conformance run-014 以 2/2 PASS 形成
Result `sha256:85c52d9af857bcc3586c821edf9a500539d82de0a56b58bc2cf5beb39f94fefa`，2 次 request、retry 0，actual model
`deepseek-v4-pro`。同候选 Session Authority
`sha256:bcf7c9c8652b363e540dbb49d6e40c9fda4a13df8790122b4d8d26bbeeba02fc` 在固定 mall revision
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` 上连续提交三题。

第一题“登录流程是怎样的？”以 8 次 dispatch 得到 `APPROVED`：Question Understanding 保留了 `SOURCE` 需要，Investigation 实际搜索并读取
Controller、Service 与登录实现，答案覆盖 `/admin/login`、用户名密码、用户加载、密码与 disabled 校验、`SecurityContextHolder`、JWT、
`token/tokenHead`、失败信息及管理员 ID/时间/IP 登录日志。这证明 `FINDING-010-046` 消除了只读 README 后过早全局 Unknown 的原缺陷，
但不证明相邻题已通过。

第二题询问本地启动、构建依赖、安全接入及 resources 排除造成的运行参数未知。它执行 13 次 dispatch，读取构建配置与多份源码后，最终
FINISH 把构建项标为 `SUPPORTED`，却在该 disposition 内附加 `LIMITATION` observation，且错误声称 Source Profile 明确列出的根 `pom.xml`
“未授权读取”。第三题询问 JWT 受保护接口 401/403 排障，执行 10 次 dispatch；最终同样在 `SUPPORTED` 的令牌检查项内混入
`LIMITATION` observation，并因机械遍历 README、POM、TEST 等全部 registered class 耗费调查预算，未读取已列入 SOURCE allowlist 的
`DynamicAuthorizationManager.java`，把动态权限判定留为 `UNKNOWN`。两题均被既有 Domain invariant 以
`Engineering QA initial investigation output violates the domain contract` 正确失败关闭，Answer/Review 未发生；失败输出没有被消费或修补。

会话已优雅停止。terminal receipt
`sha256:3f68c27c30207861368da71e4f12ea6bb7ab7d389ef7e457dd8259ab3afbaa0f` 记录 3 个 accepted question、31 次
dispatch、retry 0、Provider switch 0、Production Activation `NOT_EXECUTED`，launch/Gateway/terminal 文件均为 `0600`。同一 listener 上的
22,000 字符受控超限题在 Provider 前返回 `request body is empty or exceeds the local preview limit`；dispatch 保持 31、health 仍为
`READY` 且页面可继续提交。

## Root cause

- registered evidence class 表达“Profile 能读什么”，不是“这道题直接需要什么”。把两者等同会强迫 non-supported FINISH 遍历所有已注册
  class，挤占决定性源码的调查预算，并把无关 class 变成伪完整性条件；
- Question Understanding 只有自由文本 evidence needs，没有可由 Application 执行的受控语义最小 evidence-class 集合；
- Domain 已要求 `SUPPORTED` 只能含 affirmative observation、non-supported outcome 只能含 `LIMITATION`，但 Provider-facing closed
  output schema 仍允许任意 outcome 与任意 observation kind 组合。零重试路径只能在完整 Provider 调用后拒绝这种本可在结构层表达的矛盾；
- Prompt 没有明确区分 allowlisted path 与 opaque locator，模型因而能把已列入 Source Profile 的父 POM 错称为未授权。这些都是跨问题、
  工程与 Provider 的契约缺口，不是 mall 文件名、登录/JWT 关键词或 fixture 特例。

## Decision and disposition

- Question Understanding closed output 新增非空、去重的 `required_evidence_classes`，只允许 `SOURCE / REPOSITORY_DOCUMENT /
  BUILD_CONFIGURATION / TEST`。它声明回答 checklist 直接需要的最小集合，不复制 registered registry；可独立支持与明确未知的结论必须拆成
  不同 checklist item；
- Application 分别投影 `registered / required / investigated / untried_required / unregistered_required`。non-supported FINISH 只在
  `(required ∩ registered) - investigated` 非空时追加命名下一 class 的 GAP；unregistered required class 是显式能力边界，全部无关
  registered class 不再被强制遍历。Verification Attempt 的 required 集合仍精确绑定 Reviewer concrete gap；
- Initial/Verification FINISH schema 使用条件化 `anyOf`：`SUPPORTED` 只允许 `PROCESS_STAGE / OUTCOME / STATE_CHANGE / SIDE_EFFECT`，
  `UNKNOWN / CONFLICT / FAILED` 只允许 `LIMITATION`；Domain invariant 保留为第二道独立防线；
- Prompt 明确 Source Profile `source_allowlist` 中的路径已经授权，模型不得称其未授权；有 material Broker locator 时须先 read/parse，
  但 unlisted path 仍不得获得授权。Prompt/Strategy 与 output schema identity 同步升级；
- 当前定向 Engineering QA/Web/CLI 组合 94/94 PASS，包含 required closure 和两种 outcome/observation 反向混类的 schema 拒绝测试。
  完整回归、clean candidate、fresh Conformance 与同会话三题必须在本处置后重新执行；旧两题失败和旧第一题 PASS 均不追认为新候选证据。
