---
id: ITER-010-PDR-009
kind: project-decision
status: accepted
authority: project-decision
owners: [product, project, engineering, quality, ai]
depends_on: [FINDING-010-141, SYS-PRODUCT-SUCCESS, SYS-QUALITY-ACCEPTANCE, PROJECT-GOVERNANCE-PLAN-EXECUTION]
code: [scripts/docs.py, scripts/plan_gate.py, .github/workflows/plan-compliance.yml]
tests: [tests/test_docs_gate.py, tests/test_plan_gate.py]
iteration: ITER-010
decision: REWORK
rework_strategy: VALUE_FIRST_FOUR_ARM_GATE_WITH_MACHINE_ENFORCED_NEXT_ACTION
decision_ref: local-user-message-utf8:sha256:612341017bef3d98db372608d22b0d57744a96883e23dd51a6552c13da183989
enforcement_ref: local-user-message-utf8:sha256:63962a3f18667dd3727dd76d72c45ae8224e40a06be2d8c12622aca3a4ef0ae5
effective_scope: ITER-010-SLICE-001-and-future-plan-governance
coding_input: true
---

# PDR-009：先验证产品价值，并用机器锁定唯一下一动作

## Context

ITER-010 已迭代多日，却仍把“机器收据、页面 canary、完整 Chat、比较”排成串行链。该顺序允许开发者在知道系统是否比直接证据、同类
源码 Agent 和 current Codex 更好之前，继续修 Prompt、Reviewer、Provider 和 Web；活动 Slice 又覆盖大量产品路径，`docs.py check`
只能阻止跳过 Slice，不能阻止 Slice 内偏航。历史 run-035—043 因而形成了高成本的答案追逐：失败后反复改下游规则和全量重跑，却没有
先证明世界模型和 Agent 的总体方向是否产生正价值。

用户要求完全纠正 ITER-010，并指出不能只靠文字约束。本决定同时修正产品 Gate 和执行机制，不改变“软件世界模型 + 主工程 Agent”的
总体架构，也不追认任何历史失败为成功。

## Decision

### 1. 四路价值 Gate 前移为最早产品动作

复用已经 PASS 的分层归因、工程认知资格、当前备用配置的本地准入插件验证和 Web Access。任何新的产品代码、Prompt/Reviewer 调整、Web canary、
hardening 或 full regression 之前，先在同一 exact mall revision 上完成以下四路隔离比较：

1. **直接相关证据：** 把独立冻结的原始相关源码、配置、测试或文档字节直接给与系统臂相同的生成模型；不经过世界模型、Agent 或检索
   协议。它是复杂度控制组，不是 Oracle。
2. **同一 Agent + 仅源码：** 使用目标系统同一主 Agent、工具、Prompt、预算、cache、Reviewer 和状态，只关闭世界模型认知。
3. **同一 Agent + 世界模型认知 + 源码：** 目标系统臂；相对第 2 路唯一差异是已通过资格的、问题相关的世界模型认知。
4. **当前 Codex：** 使用运行时实际客户端、模型、reasoning、工具和权限的 fresh 隔离任务。它是最低产品强基线，不是标准答案、Oracle
   或裁判。

前三路固定同一个 `preferred` 执行配置、语言、输出边界和问题集合；第 2、3 路还固定完全相同的 Agent/Reviewer/tool/budget/
cache。任何一路不能看到其他输出。事实真值来自独立读取 exact revision 形成的 source-truth ledger，不来自任何模型答案；答案先密封、
随机匿名，再由未参与生成的独立技术评测读取原问题与 ledger 逐项裁决。

最小问题集为三条异质真实工程问题，覆盖系统用途/入口或结构、行为/调用与物质副作用、失败/权限/Unknown 边界；至少两条未参与历史修复，
且没有一条允许只靠 POM 模块/依赖完成。三条是快速判向的最小值，不是正式验收样本。

### 2. 通过标准立即采用严格 Codex 下限

第 3 路必须先满足：重大事实错误、物质遗漏、无据实质结论、错误 Citation 和 Reviewer 重大漏判均为零，Unknown/边界准确。随后还必须：

- 逐题不低于直接相关证据路和同 Agent 仅源码路；
- 相对同 Agent 仅源码路至少有一项可验证、非 locator 的世界模型贡献；
- 逐题不低于 current Codex，且总体盲评质量差值严格为正；
- 全体打平、任一物质性退步、双方失败、无法裁决或盲化失效均为 `FAIL`；
- 成本、时延、调用数、缓存或复用不能补偿答案质量失败。

这把 PDR-002 原定从 ITER-012 生效的最低标准前移到 ITER-010 当前返工。方向 Gate 失败不自动 `REDIRECT`，但绝不解锁 Web/hardening。

### 3. 失败只解锁最早责任层

- 直接证据路优于同 Agent 仅源码路：Agent/控制协议产生负价值；
- 同 Agent 仅源码路优于世界模型路：认知构建、资格、投影或使用产生负价值；
- ledger/Snapshot 已有事实而世界模型路遗漏：查询/投影或 Agent 使用故障；
- 两个系统 Agent 路均差、Codex 好：Agent/tool 接口或总体编排故障；
- 离线答案正确而 Web 错：Conversation/Delivery 故障。

`FAIL` 进入同 Slice 的逐层归因，只允许一个最早 Owner 的通用修复、原题和两个未参与修复的相邻案例；随后先重跑受影响路和一个控制路，
再完整重跑四路。连续两次通用架构修复仍不能严格超过 current Codex，必须进入架构职责裁决，不继续碰答案。

### 4. 当前候选与模型透明路由规则

当前工作树中的 v7 prompt/path-search/reviewer diff 是 `QUARANTINED / NOT_INPUT`，不得顺手合入或用于比较。目标系统只允许使用 clean
`3a6089fa0ff1d5df88f43199ae77ae4c4ecc6f19` / tree `b1fd51bb533c8ff393dc42b6864a08e5c94929c0` 的产品语义，或与其产品代码
内容精确等价的新 clean successor；比较工具从独立冻结身份运行。

前三路全部绑定 route role 为 `preferred` 的同一个冻结执行配置，并由
`ITER-010-ACTION-DIRECTION-QUALITY-PREFERRED-001` 形成 Preferred Quality Result。只有该配置在任何授权答案生成前，以已密封的
Provider/模型能力终态不可用结束时，该批次才记 `INVALID` 并进入预注册的
`ITER-010-ACTION-DIRECTION-FALLBACK-REFREEZE-001`；不得把不可用误写成答案质量 `FAIL`，也不得直接跳到 Fallback Quality。

Fallback Refreeze 本身必须是外部模型调用 `0`、人工授权请求 `0`、Provider dispatch `0`。它必须从可信父树绑定 exact Preferred
Quality `INVALID` Result seal、Freeze 的完整 provider-neutral root input set、route role 为 `fallback` 的执行配置 ref/digest、该配置选择的
准入策略插件 ref/digest 以及 `no mixed batch` 约束；不得修改问题、ledger、rubric、Agent、Reviewer、产品或任一已经密封的非路由输入，
也不得因 current standing scope 再次请求用户授权。Refreeze 不生成可能过期的价格、窗口或 live dispatch receipt。

只有首选终态分类为 `TERMINAL_UNAVAILABLE` 且上述绑定全部成立时 Refreeze Result 才能 `PASS` 并进入
`ITER-010-ACTION-DIRECTION-QUALITY-FALLBACK-001`；其他首选 `INVALID` 必须使 Refreeze `FAIL` 并返回 Preferred Quality，Refreeze 自身证据
无效则在 Refreeze 自环失败关闭。Fallback Quality 让前三路统一使用同一个 fallback 执行配置和原 root input set，不能拼接首选配置的
中间输出；实际配置专属的价格、时间、资格和调用准入由该配置的策略插件在 Quality 现场生成收据。`PASS` 进入 Minimum Web，`FAIL` 进入
Direction Rework，`INVALID` 在 Fallback Quality 动作自环失败关闭。备用配置不是并行对照，也不能因成本策略裁剪已开始的完整质量链。

该状态机只认识 `preferred/fallback`、execution profile、admission plugin、通用 terminal class 与不可变收据。动作 ID、kind、分支条件、
质量规则和 `action_evidence` 字段名不得出现任何当前 Provider 或 model 名称。具体身份只能作为运行配置对象和调用收据中的值出现；更换
Provider/model 只重封配置、资格、插件与执行收据，不修改动作图。trusted runner 验证当前工件内部结构；trusted-parent plan gate 另从父树
重算 Result/evidence 原始字节 seal，并强制后继复用相同 Freeze root input、profile 与 plugin，任意外形正确但不可重算的摘要均失败关闭。

### 5. 唯一下一动作和机械锁

Manifest 升级到 `schema_version: 2` 并采用 `DEVELOPMENT_PLAN_EXECUTION_CONTROL@1`。当前唯一动作是
`ITER-010-ACTION-DIRECTION-FREEZE-001 / V-DIRECTION-FREEZE-001`：只实现并冻结四路 runner、source-truth ledger、盲化 rubric、exact
身份和结果 Schema，外部调用为零。该动作 PASS 后唯一后继才是 `ITER-010-ACTION-DIRECTION-QUALITY-PREFERRED-001` 的真实四路运行。

当前动作以路径白名单锁定；`src/software_world_model/**`、现有产品测试、Prompt/Reviewer、Web canary、Provider dispatch、hardening 和
full regression 全部禁止。每次迁移必须有原动作指定 Result，并通过基线差分门禁；改变计划必须另有 Finding、PDR 和用户授权引用。
CI 运行两组治理单测、文档检查、当前 snapshot 和逐 commit 差分门禁；每个 commit 必须由 trusted parent 版本的 gate 校验，候选不能先削弱
verifier 再自过。trusted-parent gate 必须先于任何候选 Python、测试或文档工具执行；Pull Request 校验 head SHA 而不是 synthetic merge
SHA，且 base 到 head 的每个提交必须恰好一个 parent 并连接前一可信节点。远端仓库还必须把该检查设为不可由候选 workflow 变更绕过的
branch required workflow/ruleset；未完成远端保护时不得声称门禁不可绕过。
治理修订的新授权引用还必须在整个 trusted base 文档树中从未出现，不能复用更早 PDR 的引用。

base Manifest 完整预注册 Freeze、PreferredQuality、FallbackRefreeze、FallbackQuality、FreezeRework、DirectionRework、MinimumWeb、
WebFailureAttribution、UserDirectionDecision 和 ResponsibilityPlan **十个动作**，当前 Freeze 也作为返工返回目标注册。唯一质量路径是：

- Freeze `PASS` → PreferredQuality；
- PreferredQuality `PASS` → MinimumWeb，`FAIL` → DirectionRework，`INVALID` → FallbackRefreeze；
- FallbackRefreeze `PASS` → FallbackQuality，`FAIL` → PreferredQuality，`INVALID` → FallbackRefreeze 自环失败关闭；
- FallbackQuality `PASS` → MinimumWeb，`FAIL` → DirectionRework，`INVALID` → FallbackQuality 自环失败关闭。

所有非自环目标必须属于该 base registry。Preferred Quality Result 与 Fallback Quality Result 都预注册为 `V-DIRECTION-QUALITY-001` 的可能生产者，
但同一次方向判定中最多只能有一个 `PASS` Result；首选配置已 PASS 时不得运行备用配置，首选配置 INVALID 后也不得把其不完整输出与备用配置
结果合并。Minimum Web 失败进入 Web 分层归因，成功进入用户方向决定。三个治理出口只能自环并先密封 Result，随后以独立 Finding/PDR/
用户决定修订计划。

每个转换 Result 不再因 frontmatter 自报 PASS 获信：它必须是 sealed evidence Result，绑定 exact JSON evidence path、原始字节摘要、受保护
runner identity、runner receipt、canonical Case report、subject/input digest 和外部调用计数。收据只能覆盖 action 预注册的
`produced_case_ids`，Verdict 按 `INVALID > FAIL > PASS` 聚合；action graph 产出的 prerequisite Case 只能由该 digest-bound Result receipt
满足，Verification Matrix 文本 PASS 不能替代。摘要覆盖 exact raw blob bytes，CRLF/LF 差异不得规范化。

每个 action 的 runner identity 必须恰好包含一个自包含 `*/value_gate/runner.py`。runner 先在独立提交中冻结；后续 Result/迁移由 trusted
base gate 在隔离 cwd、清理环境和受限超时下，以 `python -I -S <temporary-runner> verify-plan-evidence` 读取 stdin 的 exact evidence JSON
bytes 并重执行。stdout 只能是绑定 verifier/action/Case/verdict/input/runner/report/subject/call-count 的 exact JSON；runner 与自己的 Result
同提交、候选 runner 自签、输出不一致、stderr、非零退出或超时均失败关闭。外部 Quality PASS 的模型调用、Provider dispatch、HTTP
dispatch 必须分别大于 0，且 full regression count 必须为 0。

计划修订只能读取 base 中已验证的 governance PASS Result，不能在同一 diff 补造 Result 或迁移动作；新 PDR 必须保持 ITER-010、编号严格
递增、`depends_on` 包含 base governance Result，并使用不在 base authorization refs 中的新 `decision_ref`。Quality FAIL 不直接获得产品
代码权限；未预注册动作和缺证据收据一律失败关闭。

## Consequences

- PDR-008 机器收据仍是外部执行安全条件，但不再作为早于产品价值的独立产品阶段；Freeze 以零外部调用产出较窄的
  `V-PUBLIC-OSS-AUTHORITY-ADMISSION-001`，只证明 credential/TLS/HTTP 前准入。完整 `V-PUBLIC-OSS-AUTHORITY-001` 当前为
  `NOT-RUN / blocking`，不是独立入口，仍须由真实 Quality/Web terminal receipts 证明，二者不得偷换。
- 已通过的 Web Access、认知资格和历史运行证据保留；Web 语义 Chat 只在四路方向 Gate PASS 后作为最小下一体验纵切。
- Slice2/3、hidden、完整回归、Production 继续锁定；当前不需要新的开发授权，也不因切换开发对话重新确认。
- 本决定只授权验证工具、治理和既定结果路径；不授权当前动作修改产品/System 代码。
- 仓库内门禁只能证明本地结构与 trusted-base 重放；没有远端不可变 required workflow/ruleset 和独立签名的用户/Provider 证明时，不宣称
  它能抵抗恶意仓库管理员或为外部行为提供密码学真实性。
