---
id: ROADMAP-M-002
kind: roadmap-milestone
status: planned
authority: planning-only
owners: [product, project, architecture]
depends_on: [SYS-PRODUCT-SUCCESS, ITER-005-RESULT-ACCEPTANCE, ITER-006-RESULT-ACCEPTANCE, ITER-007-RESULT-SLICE-001-STOP-DECISION, FINDING-007-008, FINDING-007-009, ROADMAP-CANDIDATE-BOUNDED-WORLD-MODEL-INVESTIGATION]
code: []
tests: []
coding_input: false
---

# M-002：通用软件工程问答 MVP 能力路径

## Final outcome

本路径只服务 `SYS-PRODUCT-SUCCESS`：系统在提问前将授权软件来源构建为版本固定、可更新、可复用的软件世界模型，
然后从同一个正式 Web 入口接受自由软件工程问题。“通用”不表示每题必须有答案，而是不依赖预编题型、工程名、
问题文本或关键词补丁；授权来源不足时必须返回有边界的 Gap。

## Ordered capability path

| Step ID | User-visible capability | Entry evidence | Completion evidence | Current state |
|---|---|---|---|---|
| `step-0-version-fixed-baseline` | 用户选择本地项目，系统在无问题状态更新 Snapshot，并从正式 Web 查询窄范围结构和静态调用 | ITER-005/006 Acceptance | 已接受的 Workspace、Update、Snapshot、Web、Citation 与窄范围 `CALLS` | **achieved / narrow** |
| `step-1-java-result-driven-world-model-investigation` | 用户用自由语言询问 Java 实现；Agent 只查询世界模型，能跨多方法继续调查；查询、表示与业务发现三层完整时给有界不存在结论，否则给具体 Limitation | `ITER-007-RESULT-SLICE-001-STOP-DECISION`；`FINDING-007-008/009` | 未见工程的多方法题、不存在功能题和现场题通过同一 Web，逐题不低于成熟源码 Agent | **next / blocked；ITER-008 proposed** |
| `step-2-common-java-real-project-breadth` | 同一问答链在未参与实现的常见 Java 工程上处理跨类、多文件、常见语法与框架边界 | Step 1 Product Result | 独立 held-out 工程与源码 Agent 对照，不因换工程而回到固定题型或 Gap | planned after Step 1 |
| `step-3-revision-driven-update-and-reuse` | 项目从 R1 变为 R2 时无需先提问，系统能发现变更、更新或标记受影响知识，后续问答不把 R1 当当前事实 | Step 2 Product Result | 跨会话复用、R1→R2 失效/更新和无来源访问重建通过真实 Web 问题验证 | planned after Step 2 |
| `step-4-repository-multi-source-composition` | 用户可询问系统用途、模块职责、业务规则、配置和部署；回答组合源码、仓库文档、构建与配置 | Step 3 Product Result | 代码+文档+配置的隐藏跨源题在同一 Web 与同一 Support chain 通过 | planned after Step 3 |
| `step-5-second-language-ecosystem` | 用户选择不同语言/构建生态的项目，仍获得同一问答、更新、证据和 Gap 体验 | Step 4 Product Result | 至少第二个语言/生态的未见项目通过同一产品 Gate，不复制独立问答入口 | planned after Step 4 |

无问题建模、exact revision、Support/Citation、提问时 Source/Update/Direct fallback 为零和正式 Web 人工验证是每一步的累积不变量，
不是只在某一个后续步骤补做。

## Iteration selection rule

下一个产品 Iteration 只能推进当前最早未通过的 Step。一轮可以缩小工程、语法或题目范围，但结束时必须交付该 Step 中
可在正式 Web 人工验证的用户能力增量。只产出 parser、Schema、View、Agent 编排、CLI 或测试 PASS 的方案只能是技术实验，不能标记该 Step 前进。

Step 内的方案被早期 Web 或隐藏 Gate 证伪时，保留失败证据并在同一 Step 重新选路；不得跳到后续知识域。Roadmap 只规划顺序，不授权任何编码。
