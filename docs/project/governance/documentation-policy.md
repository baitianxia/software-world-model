---
id: PROJECT-GOVERNANCE-DOCUMENTATION
kind: project-governance
status: current
authority: project-governance
owners: [documentation, architecture]
depends_on: [PROJECT-GOVERNANCE-BOUNDARY]
code: [scripts/docs.py]
tests: [tests/test_docs_gate.py]
---

# Documentation Policy

## Authority and status

当前文档使用 front matter 提供稳定 `id`、`kind`、`status`、`authority`、`owners`、`depends_on`、`code` 和 `tests`。同一 ID 只有一个当前所有者。正文链接用于阅读，ID 用于机器追溯。

常用状态：

- System：`current`、`accepted`；拟议 ADR 留在 Project 且为 planning-only，接受后迁入 System；被替代正文进入 Archive/Git 历史；
- Roadmap Candidate：`candidate`、`selected`、`rejected`；Milestone 可为 `planned`、`in-progress`、`achieved`；
- Iteration：`proposed`、`authorized`、`in-progress`、`completed`、`rejected`；
- Development Slice：`proposed`、`authorized`、`in-progress`、`completed`、`blocked`；
- Project Decision：`proposed`、`accepted`、`amended`、`superseded`；
- Finding：`open`、`dispositioned`、`rejected`、`superseded`；
- Verification：`not-run`、`pass`、`fail`、`inconclusive`、`stale`。

`not-reconstructed` 与 `historical-*` authority 只用于迁移后明确不伪造的历史索引/开发材料，不得用于新的活动 Iteration。`coding_input` 是独立门：Roadmap/Proposal/模板必须为 `false`；活动 Iteration 与被指向的 Slice 必须为 `true`，且仍需 Readiness 和 `current.md` 同时成立。

状态不得推导：设计 accepted 不表示已实现，测试 pass 不表示产品 pass，产品 pass 不表示生产 activated。

## Baseline

Git Commit 是仓库内代码和文档的一致基线。Iteration Manifest 固定本轮采用的 System IDs、外部模型/Provider、冻结输入、Oracle、运行证明和有效期；不为每个仓库文件维护第二套人工 Hash 清单。

固定变化前后状态的目的，是让验证、回退和因果判断绑定同一对象：没有 before/after 精确身份，就无法知道结果证明的是哪个实现，也无法区分代码变化、配置漂移和外部状态变化。

## Change rules

- System 只写当前语义；原因进入 ADR，实施发现进入 Finding，运行事实进入 Result。
- 被替代内容移动到 Archive 或由 Git 历史保存；不得修改历史结果来符合当前结论。
- Roadmap Candidate 必须标记 `authority: planning-only` 和 `coding_input: false`。
- `_generated/` 由脚本生成，不人工编辑。
- Archive 不进入默认 Agent Context；Legacy 链接只用于审计。

## Automated checks

`python3 scripts/docs.py check` 检查元数据、ID 唯一性、依赖、System→Project 越界链接、代码/测试引用、Roadmap 权威、活动 Iteration/Slice 授权闭包、Manifest 精确字段、未替换模板输入、Finding disposition 和完成验收，并验证生成索引没有漂移。门禁绕过用 `tests/test_docs_gate.py` 固化为回归测试。
