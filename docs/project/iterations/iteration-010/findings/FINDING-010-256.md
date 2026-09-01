---
id: FINDING-010-256
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [project, architecture, engineering, quality]
depends_on: [ITER-010-PDR-012, ITER-010-PDR-013, FINDING-010-255, SYS-ADR-018]
code: [src/software_world_model/knowledge_engine, src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: iteration-design
scope: systemic
disposition: replace-failed-execution-plan-with-capability-separated-recovery
target: ITER-010-PDR-014
---

# FINDING-010-256：ITER-010 的投入结构证明执行计划已经系统性偏航

## Observation

ITER-010 的总体目标一直是“真正的软件世界模型 + 优秀的主工程 Agent + 可体验的浏览器 Chat”，但实际开发把回答、审核和输出修复协议的
闭合作为主要进度单位。连续运行发现一个答案缺陷后，通常新增一项 Prompt、Schema、正文映射或 Reviewer 规则，再重放相同或相邻问题；
知识构建和 Agent harness 没有获得与产品目标相称的持续投入。

这不是某一次执行没有遵守计划。PDR-004、PDR-005、PDR-010、PDR-012 和 PDR-013 已多次用文字要求 Agent-first、知识归因、尽快体验和
停止逐题修补，但计划仍允许“协议版本增加 + 定向测试通过”被计为有效进展，也没有把世界模型、Agent 和端到端产品拆成可独立验证的能力。
因此偏航可持续发生而不触发计划纠正。

## Evidence

以 ITER-010 起点 `fa7ab92` 至可信 `HEAD 01b0be4` 为范围，Git 历史给出以下可重复事实：

- 共 186 个提交；
- `conversational_engineering_model.py` 被 68 个提交修改；对应测试也被 68 个提交修改；
- Engineering Conversation System Contract 被 82 个提交修改；
- `conversational_engineering_agent.py` 被 27 个提交修改；
- `src/software_world_model/knowledge_engine/` 被 0 个提交修改；Java 语义/静态调用/认知投影三个相邻能力文件合计只有 6 个提交；
- 模型边界文件从首次提交 `d3317c9` 的 2,645 行增长为可信 HEAD 的 9,643 行；对应测试从 433 行增长为 8,357 行；
- 可信 Manifest 已增长到 Agent strategy `@39`、Review input `@28`、output preflight `@33`；未提交的 `@40/@34` candidate 已由
  PDR-013 拒绝，不计入上述可信统计；
- 这些投入之后仍没有达到五个异质问题质量门，也没有证明世界模型相对同 Agent 仅源码路径的独立增益。

复现命令是 `git rev-list`、按路径的 `git log`、`git show <commit>:<path> | wc -l`。统计只读取可信 Git 对象，不包含当前工作树中隔离的
未提交 candidate。

## Classification and root cause

分类为 **iteration-design / systemic**。总体产品架构尚未被反证：`SYS-ADR-018` 中世界模型负责持久认知、主 Agent 负责动态解决问题、平台
负责权限和证据的职责仍合理。被证伪的是本轮执行计划及其进度定义：

1. 最终答案质量是唯一被频繁观察的结果，知识质量、检索质量和 Agent 行为无法独立归因；
2. Prompt/Schema/Validator 修复没有投资上限，也不要求先证明它是最早偏差；
3. 定向协议测试和版本号增长可以推动工作叙事，即使没有新的用户能力；
4. “首次体验”和“最终超过 Codex”被绑在同一长闭环中，导致每个局部缺陷都能推迟新的体验；
5. PDR-013 只提出 Agent-first 简化，没有把知识构建恢复为第一等交付，也没有先建立可比较的成熟 harness 行为基线。

## Disposition

由 `ITER-010-PDR-014` 完全替换 PDR-013 的执行路线。ITER-010 保持同一产品目标和 standing authority，不新建治理恢复动作；旧协议代码仅作
历史资产和迁移来源，不再是产品候选。新计划分别验证世界模型认知、Agent harness、二者集成增益和浏览器产品质量，并用机械约束阻止
协议继续增长。普通失败触发责任层切换和继续开发，不触发暂停或重复授权。
