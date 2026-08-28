# 治理模板

复制最小模板并替换占位符，不要复制上一轮的 Commit、模型、Digest、测试数字、时间点或结果：

- `iteration-proposal.md`
- `iteration-index.md`
- `manifest.yaml`
- `development-design-index.md`
- `development-slice.md`
- `findings-index.md`
- `verification-matrix.md`
- `readiness-review.md`
- `implementation-finding.md`
- `system-adr.md`
- `project-decision.md`
- `iteration-result.md`
- `results-index.md`
- `iteration-acceptance.md`

模板不是当前事实来源。替换全部 `NNN`、`<...>` 和需要冻结的 `pending` 后再运行文档检查。

## 最小落位

| 目标位置 | 模板 |
|---|---|
| `iterations/iteration-NNN/README.md` | `iteration-index.md` |
| `iterations/iteration-NNN/proposal.md` | `iteration-proposal.md` |
| `iterations/iteration-NNN/manifest.yaml` | `manifest.yaml` |
| `iterations/iteration-NNN/verification-matrix.md` | `verification-matrix.md` |
| `iterations/iteration-NNN/readiness-review.md` | `readiness-review.md` |
| `iterations/iteration-NNN/development-design/README.md` | `development-design-index.md` |
| `iterations/iteration-NNN/development-design/SLICE-NNN-*.md` | `development-slice.md` |
| `iterations/iteration-NNN/findings/README.md` | `findings-index.md` |
| `iterations/iteration-NNN/findings/FINDING-NNN-*.md` | `implementation-finding.md` |
| `iterations/iteration-NNN/results/README.md` | `results-index.md` |
| `iterations/iteration-NNN/results/<type>.md` | `iteration-result.md` |
| `iterations/iteration-NNN/results/acceptance.md` | `iteration-acceptance.md` |

## 默认迭代顺序

当当前系统还没有能代表目标方向的 MVP 时，默认顺序只有三段：

1. 一个长运行的完整体验动作，贯通世界模型认知、主 Agent、受控源码读取、Evidence/Citation、独立审核和浏览器 Chat。开发可跨多个普通提交；失败仍在同一动作中归因和修复。
2. 第一次完整浏览器主链（独立 first-delivery Case）可操作后立即交给用户；该交付 `requires_result=false`、不移动计划游标，也不等待 current Codex 比较。随后在同一候选上执行至少 3 个异质问题（至少 2 个未参与修复）与 actual current Codex 的严格比较。
3. 完成真实体验和独立方向判断后，按需密封最终完成/方向 Result。普通失败继续同一开发动作；用户明确 `CONTINUE` 后，同一 standing
   scope 内直接进入四路因果消融、full regression、hidden、跨工程和正式验收，只有真实 scope delta 才申请新授权。

首次体验不是“有一个页面”：它必须可重复启动、固定本地地址、版本与限制可见，真实经过完整回答链，支持语义追问、纠正、总结和新对话隔离，且单题失败不关闭服务。

## 轻量但机械的执行约束

- 每个活动 Iteration 使用 `schema_version: 2` 和 `DEVELOPMENT_PLAN_EXECUTION_CONTROL@1`，恰好一个 `current_action`。
- 当前动作镜像工作计划与可信路径；权限来自活动 Slice 和 standing authority，候选计划不能给自己的 diff 扩权，也不能因普通失败撤销权限。
- 完整体验动作可以跨多个提交、测试、失败和 Provider dispatch。普通失败不创建新 action 或 Result。
- 首次可操作浏览器交付不创建 Result、不移动游标。Result 只在最终方向/完成 handoff 或确需迁移项目状态时密封；普通失败继续同一开发
  动作。交接验证只核对必要事实，不复制产品工作流，也不使用 Activation 时钟、分钟合法性或 whole-Manifest 摘要。
- 交付前运行 `python3 scripts/plan_gate.py diff --base <trusted-base-ref>`；开发前运行 `python3 scripts/plan_gate.py snapshot`。
- 首次体验前只运行 targeted impact、startup、safety 和 failure-truthfulness 检查。full regression、hidden、跨工程和 hardening 在用户
  `CONTINUE` 后进行；只有真实 scope delta 才申请新授权。

用户方向 Result/receipt 只记录方向，不自行扩权；本地消息 digest 只能作为内容证据引用，不能冒充平台认证身份、签名或授权。

## 授权与外部调用

人类 standing authority 与系统派生的每次 exact runtime receipt 必须分离。公开开源、来源与许可证可确认、符合已批准 revision policy、clean、allowlisted、只读的测试工程，在已批准 route、预算、调度、有效期和 loopback `EVALUATION_ONLY` 范围内，不按 run、问题、Conversation 或 Turn 重复申请人工授权；每次外部分派仍须在网络和 credential 前生成一次性 receipt 并失败关闭越界。

只有真正的 scope delta 才申请最小授权，例如私有/来源未知/dirty 数据、超出来源或 revision policy、新外部接收方或 route identity、预算增加、外部写入、非 loopback 暴露或 Production。通用模板不得写死 Provider/model 名称。

失败必须先定位 `Source truth → World Model cognition → conversation/task understanding → Agent work state/plan → tool observation/evidence → answer → independent review → Web` 的最早偏差，形成可证伪假设，再做通用修复和 targeted recheck；不能围绕单题追加特判或反复碰答案。
