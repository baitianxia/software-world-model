---
id: FINDING-010-257
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [architecture, engineering, ai, quality]
depends_on: [FINDING-010-256, SYS-ADR-018]
code: [src/software_world_model/knowledge_engine, src/software_world_model/application_services/conversational_engineering_agent.py, src/software_world_model/application_services/conversational_engineering_tools.py]
tests: [tests]
iteration: ITER-010
classification: iteration-design
scope: systemic
disposition: adopt-proven-harness-and-graph-retrieval-principles-without-provider-coupling
target: ITER-010-PDR-014
---

# FINDING-010-257：成熟 Agent harness 与代码认知研究揭示当前能力缺口

## Observation

当前实现把大量能力放进一个封闭模型输出协议，却没有先证明三个基础能力：Agent 能否在多轮工具循环中持续维护目标并根据观察重规划；
世界模型能否用适合模型的工具提供相关、紧凑、可遍历的工程认知；相同 Agent 加入世界模型后能否比仅源码路径更好。成熟 harness 和近期
代码检索研究都把这些能力视为独立设计对象，而不是依赖最终回答 Prompt 一次性解决。

## External primary evidence

以下材料只提供设计经验，不是本项目的验收真值：

- OpenAI 的 [Codex harness 说明](https://developers.openai.com/blog/codex-as-a-platform) 将任务理解、跨轮状态、工具、进度、失败处理和结果
  交付定义为可复用 Agent loop，并把产品上下文、业务规则和工具留给宿主应用；
- OpenAI 的 [model guidance](https://developers.openai.com/api/docs/guides/latest-model) 建议从精简 Prompt 开始、每条规则只写一次，并用代表性
  任务验证；其内部 coding-agent 样本中更精简的系统 Prompt 同时提高分数并减少 Token；
- Anthropic 的 [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) 区分固定 workflow 与由模型动态决定
  过程和工具的 Agent，并建议从简单可组合模式开始；
- Anthropic 的 [agent eval 实践](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) 区分 Agent harness、完整 trajectory、
  environment outcome 和 grader，强调多 trial 与分能力评估，而不是只匹配单次最终文本；
- [SWE-agent](https://arxiv.org/abs/2405.15793) 证明 Agent—Computer Interface 会显著改变仓库导航和软件工程任务表现；
  [OpenHands](https://arxiv.org/abs/2407.16741) 则把 Agent、事件流、安全运行时、工具和 benchmark evaluation 分离；
- [LocAgent](https://arxiv.org/abs/2503.09089) 使用 `SearchEntity / TraverseGraph / RetrieveEntity` 三类紧凑工具，让 Agent 在实体、包含、
  import、调用和继承关系上多跳探索；其消融显示搜索、图遍历和实体读取都有独立贡献；
- [RANGER](https://arxiv.org/abs/2509.25257) 分开精确实体查询和自然语言图探索，并在检索、问答、跨文件依赖和代码补全上分别评测。

## Capability gaps

1. **Agent harness 缺口：** 现有主路径仍更像多阶段封闭 workflow。缺少一个小而稳定、Provider 透明的
   `目标/计划 → 工具动作 → 观察 → 重规划 → 回答` 循环及紧凑的 Conversation memory。
2. **Agent 工具接口缺口：** 世界模型主要以大包投影或 locator 列表进入上下文，没有稳定的实体搜索、关系遍历和按需详情工具；Source 工具
   也被协议字段塑形，而不是以 Agent 易用性和真实评测迭代。
3. **世界模型能力缺口：** 既有内核和 Java 静态语义资产没有在本轮继续发展；结构、行为、条件/异常/状态影响、来源、Coverage 和 Unknown
   没有形成一个可独立测量的最小认知纵切。
4. **评价缺口：** 最终回答失败无法区分 knowledge construction、knowledge retrieval、Agent tool use、answer synthesis 或 review；Codex
   对照也没有先建立 same-Agent source-only 消融。
5. **实现策略缺口：** 项目从头扩张专有 harness 和输出协议，未先以成熟 harness 的最小行为集建立可用基线，也未用 ablation 决定哪些
   控制层确实必要。

## Disposition

`ITER-010-PDR-014` 采用成熟 harness 的**能力模式**，不把 Codex、Claude、OpenHands 或任何 Provider 固化为产品依赖：保留现有模型网关，
建立小型 Provider-neutral Agent Runtime；世界模型通过紧凑、可组合、可遍历的只读工具服务 Agent；分别验证知识、Agent 和集成增益。外部
harness 的直接复用只允许在同一短时可运行 spike 中证明比薄运行时更快且不破坏 Provider 透明，否则立即停止该集成尝试并继续薄运行时，
不得形成新的研究等待阶段。
