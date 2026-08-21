---
id: FINDING-008-043
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [project, engineering, quality]
depends_on: [ITER-008-SLICE-001, ITER-008-VERIFICATION, ROADMAP-CANDIDATE-LOCAL-WEB-DIRECTION-PREVIEW-RECOVERY]
code: []
tests: []
iteration: ITER-008
classification: roadmap
disposition: redirect-development-execution-path-in-next-iteration
target: ROADMAP-CANDIDATE-LOCAL-WEB-DIRECTION-PREVIEW-RECOVERY
---

# FINDING-008-043：外部开发工具的提示词准入阻断不能冒充产品根因

## Observation

用户报告 ITER-008 的后续开发在 Codex/OpenAI 客户端收到 `Invalid prompt: your prompt was flagged as potentially violating our
usage policy`，导致当前开发路径不能继续。本地 `docs/project/iterations/iteration-008/` 和 `var/iteration-008/` 中没有该错误的
执行记录，也没有可以把它绑定到产品阶段、产品 Provider、模型 request 或网络 dispatch 的 receipt。

该现象对当前开发路径是系统性阻断，但现有证据只能把它归为外部开发工具的环境/配置问题。它不能证明 ITER-008 产品运行时、
DeepSeek route、World Model 数据或某项 System Contract 违反政策。

## Evidence and scope

- 用户报告是触发本次转向的外部输入，不是本机产品 Result；
- run-012 的正式产品 freeze 已独立 PASS，正式 Web 的登录题也已真实完成 5 次模型调用和 4 个 Citation；
- 同一 Web 的下单边界题完成 4 次 Provider HTTP 200，随后在 Answer/Review 交付合同处失败；这个本地产品缺口与外部客户端的
  prompt admission 错误是两条不同证据链；
- 当前无法证明被拦截的 exact prompt、检查阶段、request identity 或外部分派状态，因此不得补写这些事实。

## Decision and disposition

1. 不重试、拆词、混淆或以其他方式规避外部工具的安全检查；
2. ITER-008 以现有产品证据失败保留并转向，不继续扩大其 Prompt、Schema 或资格流程；
3. 后续开发执行面由新 Iteration 重新冻结；优先复用已经跑通的正式 Web 主线，先取得方向体验，再加固通用边界；
4. 如果后续能取得外部工具的 exact receipt，再单独缩小该环境问题；没有 receipt 时不得把它写成产品故障；
5. 本 Finding 处置到规划候选 `ROADMAP-CANDIDATE-LOCAL-WEB-DIRECTION-PREVIEW-RECOVERY`，不修改任何 System Contract。

## Closure

本 Finding 的处置是“更换下一 Iteration 的开发执行路径并保留证据”，不是声称外部阻断已经修复。ITER-008 的产品结果仍只由
run-012 freeze、正式 Web 正向成功、边界 Answer/Review 失败及未执行的验证项决定。
