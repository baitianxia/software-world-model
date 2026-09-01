---
id: FINDING-010-269
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [project, engineering, quality]
depends_on: [ITER-010-PDR-014, FINDING-010-263, FINDING-010-266]
code: [validation/iteration_010_mvp/independent_supervision.py, validation/iteration_010_mvp/direction_check.py]
tests: [tests/test_iteration_010_independent_supervision.py, tests/test_iteration_010_direction_check.py]
iteration: ITER-010
classification: iteration-design
scope: systemic
disposition: converge-all-active-development-and-supervision-to-two-bound-lanes
target: ITER-010-PDR-014
---

# FINDING-010-269：分支增殖、监督目标错绑和开发自报晋级使偏航监督失效

## Observation

主仓库同时保留多个 ITER-008/009/010 开发、修订、轻量、successor 和监督分支；实际产品提交位于临时 worktree 的
`codex/iter-010-capability-alpha`，主工作树则停留在 `codex/iter-010-routing-correction` 并含三处旧协议未提交修改。独立监督分支的 control
仍绑定较早基线和单次 assessment，监督交接依靠自由文本路径和一次性 sentinel；在候选继续变化后，没有可观察的周期 heartbeat、最新
assessment 或直接纠正记录。

同一时期，候选工作树的未提交文档把 Phase B 写成 `5/5 PASS` 并继续推进 Reviewer/recovery，但真实 Browser 事务追问已证明世界模型虽然
包含接口 `@Transactional`，有界认知检索却没有稳定返回声明/继承闭包。开发自报阶段与独立证据发生冲突，监督没有阻止越阶段工作。

## Evidence

- 主仓库存在 `codex/iter-008*`、`codex/iter-009`、多个 `codex/iter-010*` 和独立监督分支，无法从名称唯一确定当前产品目标；
- `268b4546a893ff346da34d4f4d06057d860e2aa3` 是最后一个包含轻量 Agent、认知构建/查询和恢复调度的 clean 已提交候选；
- 主工作树的三处旧协议修改与 capability-alpha 的 Reviewer/recovery/自行晋级修改均未提交，且属于不同责任层；
- 监督 control/assessment 指向早期基线，只有静态检查结果；创建目标 sentinel 后没有持续 heartbeat 或候选变化后的新 assessment；
- `FINDING-010-263/264` 的 exact-source 对照证明旧 Phase B `5/5` 没有覆盖真实声明/继承检索闭包，不能作为 Phase C 入口。
- 首版连续 watcher 虽每 30 秒刷新 heartbeat，但候选变化时只返回 `STALE / CONTINUE`；它没有运行监督方拥有的方向检查，也没有生成开发任务
  可消费的纠正指令。开发工作树曾新增版本化 Agent 协议时，机械检查已能报错，而 watcher 和语义监督仍先后给出继续/正常，证明“进程存活”
  并不等于完成监督职责。

## Root cause

分类为 **iteration-design / systemic**。开发目标、阶段状态和监督目标分别依赖分支名、临时路径、开发者自报和自由文本交接，没有一个稳定、
可机器核验的唯一绑定。监督只复核一次提交，既不持续观察工作树变化，也不独占阶段晋级；分支越多，监督检查错误目标却仍产生“正常”结论的
概率越高。

首版 watcher 的后续失效属于同一系统性根因：实现只观察“状态是否变化”，没有把“按当前唯一目标检查实现方式 → 立即纠正 → 开发任务消费”
接成闭环；运行进程还只显示当前监督 HEAD，无法证明内存中加载的就是该 HEAD 的监督代码。

## Disposition

全部历史开发分支和 dirty 候选先转换为可恢复 `archive/*` 标签，然后退出活动开发。仓库只保留 `main`、`codex/development`、
`codex/supervision`；固定工作区位于仓库忽略的 `var/workspaces/development` 和 `var/workspaces/supervision`，后续迭代继续使用这两个职责分支。

监督 control 必须同时绑定开发分支、可信产品基线、当前 HEAD 和 Phase；每次候选变化立即检查，最长每 30 分钟写 heartbeat 与 assessment。
开发分支的阶段自报不产生进度；只有监督方用 exact Source 和独立原始任务对 clean commit 给出 `ADVANCE` 才能晋级。发现旧协议扩张、越阶段、
无产品增量或单题拟合时，监督直接向同一开发任务发送 `CORRECT` 和唯一下一动作。目标错绑或监督失联只修复监督链，不暂停开发、不重复授权。

连续监督实现必须在每个 poll 使用监督分支自身的方向检查审计当前 clean/dirty 候选；硬性偏航必须覆盖 stale assessment 并立即写
`CORRECT`。任何候选变化还必须写出语义 assessment request，要求独立监督按目标一致、实现方式、体验进展和通用根因复核；结论通过共享的
machine-readable directive 交给开发任务。heartbeat 同时记录运行时加载代码与监督 HEAD 的 digest，二者不一致时只恢复 watcher。端到端
验收以真实候选偏航能产生具体纠正指令为准，不以进程、心跳或测试数量为准。

Phase B 已由独立证据推进完成；当前 Phase C 的唯一下一任务是 cognition→Source Gap→Answer/Citation→fresh review→loopback Web 最小纵切。
归档的 Provider recovery、回答 Prompt/Schema 和 Phase D 内容只能在相应阶段重新取得独立证据后选择性恢复。
