---
id: FINDING-010-091
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [product, project, engineering, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-090]
code: []
tests: []
iteration: ITER-010
classification: iteration-design
scope: systemic
disposition: experience-first-recovery-after-no-user-visible-delivery
target: ITER-010-PDR-003
---

# FINDING-010-091：长时间返工没有形成新的用户可体验结果

## Observation and evidence

用户以 `codex-user-message:sha256:47a3421d48fe3f36000e45696ea9c41b49b7e362332bc724306c10ca42fe119c`
报告：ITER-010 已连续开发约 14 小时，仍没有形成可供其体验的新版本，同时消耗了大量 DeepSeek token。14 小时是用户对本轮开发经过的
直接记录；当前没有完整、可信的逐 run 成本汇总，因此本 Finding 不补造 token 数或金额。

仓库证据与该反馈方向一致：Slice1 在已有 Web、Citation、调查和审核纵切可运行后，仍从 run-013 持续推进到 run-034，多次采用
“修改 Prompt/Schema/Contract → 完整确定性验证 → fresh Conformance → 三题 live”的长反馈环。其间虽然产生了大量内部修复和永久保留的
失败证据，但当前 `V-ANSWER-REWORK-001` 仍为 FAIL，run-034 又在 Conformance 阶段终止，没有启动 Alpha 或 Browser。内部结构变化没有
形成新的用户可操作页面或可评价答案，因此不能算作用户可见增量。

问题属于迭代拆分与执行纪律的系统性缺陷，不是单一模型输出缺陷：Access、答案 Quality、完整回归、Provider 资格和后续 hardening 被
串成同一个前置链，导致任一质量问题都把体验推迟到下一轮完整闭环。

用户进一步纠正根因：上述循环主要是 `answer-chasing`，不是 `root-cause fixing`。每次输出失败后直接增加 Prompt、Schema 或 Contract
规则，却没有先沿 Source truth、World Model Cognition、Question Understanding、Investigation、Evidence Package、Answer、Review、Web
定位最早偏差，也没有提出可由本地最小复现推翻的根因假设。因此相同职责错误可以换一种答案表象再次出现，完整回归和 live 重跑只能放大
时间与 token 消耗，不能证明根因已经消失。

## Decision and disposition

- 处置到 `ITER-010-PDR-003`：把 Access 与 Quality 拆为独立 Gate，先交付明确标记“质量未验收”的真实 Web，再用一题 canary 决定是否
  值得运行三题质量集。
- 从本决定生效起，到首个新用户可见版本完成前，停止扩张 Answer/Review Prompt、Schema 和 System Contract；只允许页面启动、真实失败
  展示、安全、当前 Provider route 和一次资格/一次 live smoke 所必需的最小工作。
- 一个 sealed 产品版本上的 question run 只要到达任何外部模型 dispatch，就计为一次 live attempt；内部字段、Prompt 或 Schema 变化不
  自动构成新的用户可见增量。
- 同一 failure signature 最多再执行一个 successor live attempt；连续两次 live attempt 没有用户可见增量时停止外部重跑，回到本地诊断。
- 任何 Prompt、Schema 或 Contract 变化前必须记录最早偏差层与可证伪 root-cause hypothesis；先通过本地最小复现和两个未参与修复的相邻
  案例，才允许一题 live canary。同 signature 修一次仍复现时停止堆规则并评审架构职责。
- 首次体验前只运行 targeted impact、startup、safety 和失败真实性检查；full regression 只在 Alpha `CONTINUE` 后 hardening 和正式验收前
  执行。
- 本 Finding 不否定已经闭合的安全与证据边界，也不把 Access PASS 写成答案 Quality PASS。
