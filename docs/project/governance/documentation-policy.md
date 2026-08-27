---
id: PROJECT-GOVERNANCE-DOCUMENTATION
kind: project-governance
status: current
authority: project-governance
owners: [documentation, architecture]
depends_on: [PROJECT-GOVERNANCE-BOUNDARY, PROJECT-GOVERNANCE-PLAN-EXECUTION, SYS-ADR-019]
code: [scripts/docs.py, scripts/plan_gate.py]
tests: [tests/test_docs_gate.py, tests/test_plan_gate.py]
---

# Documentation Policy

## Authority and status

当前文档使用 front matter 提供稳定 `id`、`kind`、`status`、`authority`、`owners`、`depends_on`、`code` 和 `tests`。同一 ID 只有一个当前所有者。正文链接用于阅读，ID 用于机器追溯。

常用状态：

- System：`current`、`accepted`；拟议 ADR 留在 Project 且为 planning-only，接受后迁入 System；被替代正文由 Git 历史保存，迁移原因进入 Archive；
- Roadmap Candidate：`candidate`、`selected`、`rejected`；Milestone 可为 `planned`、`in-progress`、`achieved`；
- Iteration：`proposed`、`authorized`、`in-progress`、`paused`、`completed`、`rejected`、`superseded`；
- Development Slice：`proposed`、`authorized`、`in-progress`、`paused`、`completed`、`blocked`；
- Project Decision：`proposed`、`accepted`、`amended`、`superseded`；
- Finding：`open`、`dispositioned`、`rejected`、`superseded`；
- Verification：`not-run`、`pass`、`fail`、`inconclusive`、`stale`。

`paused` 只表示 scope/Owner 变化、用户明确暂停或本地开发授权失效后等待恢复，必须 `coding_input=false`；external scope-delta grant pending 只
阻断对应 action，活动 Slice 仍为 `authorized|in-progress / coding_input=true`。`superseded` 只用于从未执行的计划被其他项目决定替代，
不能伪装执行失败。
`not-reconstructed` 与 `historical-*` authority 只用于迁移后明确不伪造的历史索引/开发材料，不得用于新的活动 Iteration。`coding_input` 是
Slice 级门，不是无限代码授权：Roadmap/Proposal/模板必须为 `false`；活动 Iteration 与被指向的 Slice 必须为 `true`，且仍需 Readiness、
`current.md` 和 Manifest 的唯一 action 同时成立。action-level 白名单比 Slice 的 `code/tests` 范围更窄时，以 action 为准。

状态不得推导：设计 accepted 不表示已实现，测试 pass 不表示产品 pass，产品 pass 不表示生产 activated。

外部权限文档必须区分三类对象，禁止把审计收据写成人工授权门槛：

- `PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY@1` 是人类批准的可重复使用范围；公开开源、来源与许可证可确认、允许的 revision selection policy、每次运行的 exact revision、clean、
  allowlisted、只读的测试工程，在已批准 Provider/model/endpoint/credential account route、预算、调度、有效期和 loopback
  `EVALUATION_ONLY` Sink 内运行时，不因新的 run、问题或 Turn 失效；
- `exact execution/admission receipt` 是系统在每次动作前后派生的机器证据，冻结实际 source/session/route/budget/schedule 并回指 standing
  authority；它不能创建或扩大权限，缺失、失配或越界时仍须失败关闭；
- `scope-delta grant` 才是新的人工授权：私有/来源未知/许可证未知/仅本机存在/dirty 数据，超出 approved upstream/revision selection policy/allowlist，新
  外部接收方或 route identity，预算增加，超出 fallback admission policy 的调度范围或需要一次性 override，外部写入、非 loopback 暴露、
  Production Activation 或 standing authority 的
  其他排除项。

Proposal、Manifest、Readiness、Slice 和 Result 必须分别记录这三类对象。不得为 standing scope 内的公开开源只读测试逐 run 或逐题制造新的
`codex-user-message` 收据，也不得把系统生成的 digest 冒充用户决定。

## Baseline

Git Commit 是仓库内代码和文档的一致基线。Iteration Manifest 固定本轮采用的 System IDs、外部模型/Provider、冻结输入、Oracle、运行证明和有效期；不为每个仓库文件维护第二套人工 Hash 清单。

固定变化前后状态的目的，是让验证、回退和因果判断绑定同一对象：没有 before/after 精确身份，就无法知道结果证明的是哪个实现，也无法区分代码变化、配置漂移和外部状态变化。

## Change rules

- System 只写当前语义；原因进入 ADR，实施发现进入 Finding，运行事实进入 Result。
- 被替代正文由 Git 历史保存；Archive 只保留迁移记录，不复制可由提交精确恢复的旧正文。不得修改历史结果来符合当前结论。
- Roadmap Candidate 必须标记 `authority: planning-only` 和 `coding_input: false`。
- `_generated/` 由脚本生成，不人工编辑。
- Archive 不进入默认 Agent Context；需要 Legacy 原文时按迁移记录从精确 Git 提交读取。

## Automated checks

`python3 scripts/docs.py check` 检查元数据、ID 唯一性、依赖、System→Project 越界链接、代码/测试引用、Roadmap 权威、活动 Iteration/Slice
授权闭包、Manifest 唯一 action、Current 镜像、预注册后继、未替换模板输入、Finding disposition 和完成验收，并验证生成索引没有漂移。
`python3 scripts/plan_gate.py diff --base <trusted-base-ref>` 另用 base plan 检查候选 diff、Result 和单步迁移，防止候选树修改自己的白名单。
两套门禁绕过分别用 `tests/test_docs_gate.py` 与 `tests/test_plan_gate.py` 固化；CI 必须同时执行。
