---
id: PROJECT-GOVERNANCE-PLAN-EXECUTION
kind: project-governance
status: current
authority: project-governance
owners: [project, engineering, quality]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, PROJECT-GOVERNANCE-DEVELOPMENT-DESIGN, PROJECT-GOVERNANCE-VERIFICATION]
code: [.githooks/plan-pre-commit, scripts/docs.py, scripts/plan_gate.py]
tests: [tests/test_docs_gate.py, tests/test_plan_gate.py]
---

# 开发计划机械执行门禁

## 目的

自然语言计划只能解释意图，不能阻止实现者在一个较大的活动 Slice 内改变顺序、扩大范围，或把计划与结果同时改写为“已获授权”。
所有采用本政策的活动产品迭代必须把唯一下一动作写入 Manifest，并由单树校验、基线差分校验和合并必需检查共同执行。文档正文不是
执行权威；机器可读游标才是当前允许工作的最小边界。

## 唯一下一动作

采用 `DEVELOPMENT_PLAN_EXECUTION_CONTROL@1` 的 Manifest 必须且只能有一个 `current_action`。它至少绑定：

- 计划修订、活动 Slice、Verification Case、动作类型和状态；
- 已通过的前置 Case、唯一允许生成的 Result ID/path；
- exact evidence schema/path/verifier、受保护 runner identity paths 和本动作可产出的 Case 集；
- 是否允许编码和外部执行；
- 可变更路径、禁止变更路径和当前全部锁；
- `PASS / FAIL / INVALID` 各自唯一的后继动作。

所有可能由当前动作直接迁移到的后继必须在 base Manifest 的 `next_action_contracts` 预注册完整 action、transition 和 locks；未预注册 ID
一律拒绝。候选树只能把预注册 contract 原样提升为 `current_action`，不能自行补写或放宽字段。

`PROJECT-CURRENT` 必须复制计划修订、动作 ID 和 Case ID，文档检查必须与 Manifest 精确比对。活动 Slice 的广义 `coding_input=true`
不能覆盖动作级白名单；动作未列出的产品代码、Prompt、Reviewer、Provider、Web、hardening 或测试范围一律未授权。

## 状态转换

动作可以保持不变或前进一步，不能跳步、一次推进多步或回写已完成历史。前进一步必须同时满足：

1. 基线 Manifest 中当前动作指定的唯一 Result 已生成；
2. Result 必须为 `sealed iteration-result / evidence`，绑定原动作 ID、计划修订、Case、exact 输入、verifier、runner/report/subject digest、
   外部调用数和允许的 Verdict；同一动作的 JSON evidence artifact 必须位于预注册路径，摘要覆盖 Git blob 或工作树中的原始 bytes 并与
   Result 一致；UTF-8 解码只用于解析，不得先把 CRLF、LF 或其他字节差异规范化后再计算摘要；
3. Verification Matrix 不得已明确 `FAIL/INVALID`；若 Matrix 因当前动作路径锁保持 `NOT-RUN/UNKNOWN`，Result frontmatter 只作为迁移
   索引，实际迁移真源是受保护门禁校验通过的 Result + JSON 收据；收据必须精确覆盖预注册 `produced_case_ids`，Verdict 按
   `INVALID > FAIL > PASS` 聚合，不能使用别名或自行声明额外 PASS Case；凡是 action graph 声明会产出的 prerequisite Case，Matrix
   文本 `PASS` 也不能满足前置，必须解析到唯一 digest-bound sealed Result receipt；只有 graph 之外的历史 Case 才可继续使用 Matrix
   索引。后续允许的索引动作再回写 Matrix，不得为了迁移放宽当前白名单；
4. 新动作 ID 等于原动作对应 Verdict 的唯一后继；
5. diff 没有越过原动作允许路径，也没有触碰锁定范围。

`evidence_verifier` 不是 Result 可以自报的标签。每个 action 的 `runner_identity_paths` 必须恰好包含一个
`*/value_gate/runner.py`；该 Python runner 必须自包含。迁移时 trusted gate 必须读取 **trusted base** 的 runner identity，把 runner 复制到
隔离临时目录，以清理后的最小环境、受限超时执行
`python -I -S <temporary-runner> verify-plan-evidence`，并把 evidence JSON 的 exact raw bytes 通过 stdin 输入。stdout 必须是且只能是一个
JSON object，精确包含并绑定以下字段：`evidence_verifier`、`action_ref`、`verification_case_id`、`plan_gate_verdict`、
`execution_input_digest`、`runner_identity_digest`、`verification_report_digest`、`subject_digest`、`external_model_call_count`；非零退出、
stderr、超时、字段缺失/多余或任何值不一致均使迁移失败。runner 必须先在一个独立提交中冻结，Result/JSON receipt 与 cursor transition
在下一提交产生；runner 与自己的 Result 同提交属于自签并被拒绝，候选 runner 也不能替代 base runner。

每份 JSON receipt 还必须包含顶层 `action_evidence` object。通用门禁把其 exact bytes 一并交给 trusted runner；动作 runner 负责对本次
工件内部的结构、计数、收据和值失败关闭。跨动作的 predecessor Result 原始字节、evidence 原始字节、Freeze root input、execution profile
和 admission plugin 绑定必须由 trusted-parent `plan_gate.py` 从基线树重新计算并逐值比较，不能由只看到当前 stdin 的 runner 自证；文档检查
只能重复核对而不能替代两者。没有动作专属字段时该 object 仍必须存在并为空对象，禁止用任意 SHA-256 外形字符串或未注册顶层字段绕开
通用 Schema。

动作图、动作 ID/kind、迁移条件、质量标准和 `action_evidence` 字段名只允许使用 `preferred/fallback` 路线角色与 execution-profile/plugin
引用，不得包含当前配置的 Provider 或 model 身份。具体身份只允许出现在独立运行配置对象和不可变执行收据的值中；更换模型只重封配置、
资格和调用收据，不修改状态机。

`provider_neutral_root_input_set` 使用关闭 Schema：顶层只能是 `schema/question_ids/system_arm_ids/entries`，恰好三个唯一 `Q-*` 问题 ID，
system arm 必须等于当前 Gate 冻结的三个系统臂，entries 必须恰好覆盖问题×系统臂的完整笛卡尔积；每项只能包含 question ID、system-arm ID
和 exact root-input digest。Provider/model/route/profile/plugin 控制字段即使使用未登记身份也不能进入该对象；问题正文等数据由 trusted runner
通过 root-input digest 绑定和验证，不能被通用门禁解释为路由控制。

若 action 允许外部执行且 Result 为 `PASS`，JSON `execution_counters` 中 `external_model_call_count`、`provider_dispatch_count`、
`http_dispatch_count` 必须都大于 0，并且 `full_regression_run_count` 必须等于 0。零调用不能伪装真实 Quality PASS，首次方向 Gate 也不能
借 PASS 偷跑完整回归。禁止外部执行的 action 则全部外部计数必须为 0。

`FAIL` 不授权针对答案表象继续调参。它只能进入预先冻结的归因/返工动作；`INVALID` 只能修复输入、身份、盲化或执行完整性后重跑。
需要改变计划本身时，必须先形成 Finding、Project Decision 和明确用户授权引用；同一变更不能同时以新计划为自己补造成功证据。
只有预注册 `kind: governance` 动作可以修订计划；它必须先在独立基线提交中形成 digest-bound `PASS` Result，修订提交只能读取该 base
Result，不能同时补 Result、改 verifier 或迁移动作。新 `plan_revision_ref` 必须仍属于同一 Iteration、PDR 数字序号严格大于 base PDR，
新 PDR 的 `depends_on` 必须包含 base governance action 的 sealed Result，而且 `decision_ref` 必须在整个 trusted base 文档树的所有授权字段中
从未出现；只检查当前 Manifest 的引用集合不足以阻止复用更早 PDR 的授权。
所有非自环后继都必须已注册，且动作图必须至少保留一个此类治理出口。

## 两类检查

- `python3 scripts/docs.py check` 校验当前树：Schema、唯一动作、活动 Slice、Verification、Current 镜像、锁和文档一致性。
- `python3 scripts/plan_gate.py diff --base <git-ref>` 校验基线到候选树：路径白名单、受保护 runner identity、Result/JSON 原始摘要、Case
  聚合、trusted-base verifier 重执行、外部执行 Admission/正计数和单步状态迁移。

首次启用只能提交治理 cutover：允许计划、治理、验证工具及其测试，禁止夹带产品代码。cutover 之后，所有开发变更都用基线版本的
`current_action` 审核，候选树不能通过修改自己的白名单来扩大权限。

本地开发仓库必须把受保护的 `.githooks/plan-pre-commit` 安装为 `.git/hooks/pre-commit`。它通过 `git write-tree` 只校验暂存树，避免把
未暂存的隔离实验误带入提交，同时从 trusted `HEAD` 提取 `scripts/plan_gate.py`，禁止执行候选门禁并拒绝 merge commit。该钩子用于自动
阻止普通误操作；`--no-verify` 或直接修改 `.git` 仍属于本地管理员能力，不能替代下述远端不可变规则。

## 合并强制与不可绕过边界

仓库 CI 必须把逐 commit trusted-parent 差分门禁放在任何候选 Python、候选测试、文档工具或 snapshot 执行之前。Pull Request 使用真实 head
SHA，而不是平台合成的 merge SHA；base 到 head 的每个提交必须恰好一个 parent，且该 parent 必须等于前一可信节点。每个提交都由其
trusted parent 的 `scripts/plan_gate.py` 校验，不能执行候选自己削弱后的 verifier，也不能用 merge commit、并行父节点或聚合 diff 把多次
迁移压成一次。trusted-parent 门禁 PASS 后才可执行候选治理单测、文档检查和当前 snapshot。

托管仓库还必须把该 workflow 设为不可由候选变更绕过的分支必需检查/ruleset，并保护门禁脚本、workflow、Manifest、Current 和活动
Slice；仅把命令写进 AGENTS、README 或仓库内 workflow 不构成对恶意仓库管理员的不可绕过边界。没有远端不可变 required workflow/
ruleset，也没有独立签名的用户授权与 Provider 执行证明时，只能声明“本地结构、执行重放和合并前门禁已实现”，不能声称用户意图、外部
调用或管理员行为已经由仓库内文件做了密码学认证，更不能宣称门禁绝对不可绕过。

紧急修订也不绕过本政策：先用专门的 governance action 修改规则并取得对应决定，再执行新的唯一动作。安全事件可以停止动作，但不能
把停止本身解释为后续开发授权。
