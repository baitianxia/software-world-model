---
id: MIGRATION-002
kind: migration-record
status: completed
authority: historical
owners: [documentation]
depends_on: []
code: []
tests: []
---

# 系统文档与项目文档分离

## 背景

重构前，概要架构、8,000 余行主题详细设计、实施选择、运行状态和验证日志需要联合阅读才能判断当前开发输入。详细设计同时承担永久系统语义和局部实现说明，导致人和 Agent 容易把历史状态、条件能力或某轮字段设计误读为当前事实。

## 迁移决定

- `docs/system/` 只描述当前接受且跨迭代稳定的系统本质。
- `docs/project/` 只描述规划、迭代范围、开发设计、发现、决策和结果。
- 22 个 Accepted 主题被提炼为精简 System Contract；字段表、内部状态、算法和错误枚举由代码与测试拥有。
- `Schema Evolution` 与 `Semantic View` 当时仍为 `In Review`，因此迁为 planning-only Roadmap Candidate，不进入当前 System Contract。
- 135 条旧架构决策不机械转换；当前选择合并成少量 ADR，并通过 `derived_from` 保留来源编号。
- 旧树完整移动到 `docs/archive/legacy-documents/`。Git 基线提交 `476517b` 固定了移动前状态。

## 历史状态处理

迁移后的 Iteration 001 摘要属于基于现有记录的重建，不伪装成当时就存在的新格式。旧验证日志保留所有阶段性失败和 `NOT RUN`；当前入口只采用有明确后继关系的最新证据。

## 可逆性

目录移动和内容提炼都由 Git 记录。需要核对未提炼细节时，优先查看提交 `476517b` 或本目录下的 legacy 文档，而不是把旧正文重新设为当前权威。

## 迁移验证

- 22 个 Accepted 旧主题共 7,934 行；对应 current Contract 共 815 行，约减少 90%，未计各级导航文件；每份 Contract 的 `derived_from` 保留一对一旧主题来源。
- `python3 scripts/docs.py check`：98 份 current 文档的元数据、ID、依赖、链接、代码/测试引用、Roadmap 权威、活动授权、Manifest、Finding 与 Acceptance 闭环通过。
- `python3 -m unittest tests.test_docs_gate -v`：14 / 14 PASS；覆盖 Manifest 错层/重复键、Finding 多目标/错误目标/无效替代、活动模板占位符/空章节和完成验收缺失字段等绕过路径。
- Iteration 001 的 pre-Git 旧记录登记 production `288 / 288 PASS`、Demo `121 / 121 PASS`；production 原始日志和 exact Git identity 未版本化，因此不能把 `288` 追溯绑定到后来创建的提交。
- 本次迁移在 `476517b5baf62abcc5a6ddda30b33335d262a8f3` 的独立临时 checkout 中，以 mall `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`、transmittable-thread-local `9c6552bbd7eda52b7bfb03c24c4f9aee514e91f3`、poi-tl `58fdb6c7d9db7da53cd420ff1ebde49813bd7af2` 运行 production `290 / 290 PASS` 与 Demo `121 / 121 PASS`。这是重构期新机械复验，不替代历史 CC、CE、Product 或 Activation 证据。
- 重构期间观察到但不属于本任务的实现与测试工作区变化被完整保留，并排除在文档提交暂存范围之外；它们的当前状态不冻结在本历史记录中。
- 本记录不声称存在绑定“仅文档重构内容”的新 production regression。迁移的机械验证范围是文档结构与引用一致性；实现变化必须进入经授权的 Iteration 并重新取得相应资格。
