---
id: ITER-010-PDR-001
kind: project-decision
status: accepted
authority: project-decision
owners: [product, project, architecture, engineering, quality]
depends_on: [ITER-010-RESULT-SLICE-001-STOP-REDIRECT, FINDING-010-028, ITER-011-PROPOSAL]
code: []
tests: []
iteration: ITER-010
decision: REWORK
decision_ref: codex-user-message:sha256:3112da2512628a1beddf15117a8bd78ed484ad5c6ceece3feac7877e1d7ecf4e
superseded_interpretation_ref: codex-user-message:sha256:d746968f58cea4d2b7689b5902c0ff97f42f63c93ffc4cbc40551cfa2c0359e0
coding_input: false
---

# PDR-001：把整轮拒绝纠正为同轮返工

## Context and evidence

ITER-010 的公开题和现场题已经证明：真实 loopback Web、世界模型认知、自适应只读源码调查、证据包、引用、独立审核与失败关闭能够运行。
同一批证据也证明答案仍可能退化成代码走读，且 Reviewer 会漏判重要副作用。这是必须修复的质量缺陷，但不是“整个产品方向已经被用户
拒绝”的证据。

历史消息 `d746968f…` 的原意是：实现者既然已经知道答案有问题，就应自行复核和修正，不应把已知技术错误再次交给用户裁决。它没有明确
表达 `REDIRECT`。旧 Result 将该消息推断成整轮方向拒绝，超出了消息本身的含义。

最新用户收据 `codex-user-message:sha256:3112da2512628a1beddf15117a8bd78ed484ad5c6ceece3feac7877e1d7ecf4e` 进一步指出：连续十轮仍
没有可持续使用的体验版本，而且单个错误答案直接导致整轮拒绝和另起计划并不合理。

## Options

1. 继续把 ITER-010 视为 rejected，并从 ITER-011 重新建设答案架构；这会继续增加计划和编号，却不能最短交付可持续体验。
2. 删除或改写 ITER-010 的失败证据；这会损害可审计性，不能采用。
3. 保留全部执行事实，把迭代级决定纠正为 `REWORK`，在同一轮复用现有实现并优先交付持续 Web Alpha。

## Decision

采用选项 3：

- ITER-010 及其 Slice1 从“整轮拒绝/阻断”改为 `PAUSED / REWORK / NO CODING INPUT`；历史执行结果继续如实保留，其中具体答案和 Reviewer
  Gate 仍是 FAIL。
- `ITER-010-RESULT-SLICE-001-STOP-REDIRECT` 的 ID 和文件名作为历史定位符保留，但当前项目决定由本 PDR 修订为 `REWORK`。
- 未执行的 ITER-011 标记为 `superseded`；其中“先提供真实体验、答案与审核做通用修复、确认后才夯实”的有效内容吸收回 ITER-010。
- 下一项用户可见交付不是另一组固定测试，而是同一产品的持续 Web Alpha：可重复启动、固定 `127.0.0.1`、无认证、固定工程和精确版本，
  通过一条文档化命令启动到 `http://127.0.0.1:8765/`，同一运行会话连续接受自由问题；页面展示版本、限制、答案、Citation 和失败状态；
  一个坏问题只失败该请求，不关闭服务或否决整轮，普通体验者无需拼装逐题授权或内部运行参数。
- 在同一轮修复答案与 Reviewer 的通用根因，以原失败题和至少两个相邻或异质问题回归；禁止工程、问题、关键词、符号、类、方法、fixture
  或 Oracle 特判。用户实际体验确认方向后，才进入跨工程、持久恢复、安全性能、隐藏输入、对照和完整回归等工程夯实。

## Scope and consequences

单题、版本和架构裁决自此分离：

- 单题有重大错误、遗漏、无据结论或审核漏判时，该题失败并登记缺陷；错误结果不得冒充已审核成功，但服务应继续处理后续问题。
- 只有启动不可用、证据/权限边界失效、错误结果无法隔离等版本级问题才暂停当前 Alpha。
- 只有多个异质问题重复证明核心路径无效、修复必须替换核心架构，或用户在实际持续体验后明确拒绝方向，才允许 `REDIRECT/REJECT`。

本 PDR 只修正项目计划和历史决定解释，不授权产品代码、System Contract 变更、credential、Provider/model 调用、源码披露、live Web、hidden
或 Production Activation。旧授权和运行 grant 均保持已消费；恢复开发必须另有明确授权并更新 current context。

## Revisit condition

同一 Slice 最多先完成两次通用返工尝试。只有连续两次以后，在“原失败题 + 两个异质问题”中仍至少两题出现重大答案错误或 Reviewer
漏判，才触发一次架构转向评审；该阈值也不自动等于 `REDIRECT`。不能用单题失败、一次 Reviewer 漏判或模型调用次数自动触发新 Iteration。
