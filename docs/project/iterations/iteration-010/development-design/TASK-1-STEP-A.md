---
id: ITER-010-TASK-1-STEP-A
kind: development-design
status: current
authority: current-development
owners: [engineering, architecture]
depends_on: [ITER-010-EXECUTION-PLAN-CURRENT, SYS-ADR-021, SYS-ADR-020]
code: [src/software_world_model/source_integration/exact_revision_tools.py, src/software_world_model/application_services/chat_agent.py, src/software_world_model/ai_infrastructure/chat_agent_model.py, src/software_world_model/interface/lightweight_engineering_chat.py]
tests: [tests/test_exact_revision_tools.py, tests/test_chat_agent.py, tests/test_engineering_chat_session_artifact.py]
iteration: ITER-010
coding_input: true
as_of: 2026-10-14
---

# TASK-1 步骤 A：只读源码组达到工具对等（截止 2026-10-16）

## 目标

浏览器里的一个问题真正进入主 Agent；主 Agent 用与主流编码 Agent 相当的只读工具在 exact revision 上调查，给出带引用的答案并经
fresh 复核；在冻结的开发可见问题 D1—D6 上得到只读源码组的逐题结果。

## 已完成

- `source_integration/exact_revision_tools.py`：全树列举/glob、字面与正则搜索、按路径与行段读取、历史与 blame；绑定 exact commit 与
  include/exclude 范围；结果有界、截断时报告 `PARTIAL`、每项带引用定位与内容摘要。12 项测试通过；在 mall `0504e86` 上全树搜索约 30 ms。

## 已完成（2026-10-14 第二批）

- `application_services/chat_agent.py`：`ChatAgentTurnExecutor` 实现既有 `EngineeringConversationTurnExecutor` 接口。每步最多 4 个工具调用；
  证据按本轮实际返回条目分配 `E<n>` 编号，交付前重算校验；预算按每轮 15 次模型调用（与 standing authority 一致，预留 3 次给复核）、
  24 次工具调用和观察字符数控制；耗尽时关闭工具，由同一 Agent 基于已有证据作答并照常复核；Reviewer 可做一轮最多 4 次的核验读取，
  核验结果不进入证据包；最多两次复核，仍未通过则失败关闭并给出复核意见；Turn Trace 写入产品仓库 `var/turn-trace/`。
- `ai_infrastructure/chat_agent_model.py`：新的 Agent 与 Reviewer 指令和封闭输出格式，复用既有授权输入清单、共享调度预算与 Gateway 收据。
- 接线：会话准备时由 exact revision、Source Profile 白名单和排除路径构造只读范围；默认使用新执行器，设置环境变量
  `SWM_CHAT_EXECUTOR=legacy` 可回到旧执行器做对比。
- 测试：执行器 11 项（并行工具、无需候选的读取、未知引用纠正、无引用答案拒绝、越界与重复动作、预算耗尽、核验读取、改写与补证回路、
  复核未通过失败关闭、追问只带历史不带旧证据）；会话准备测试确认默认选择新执行器。容器内全量 1,222 项测试中，仅 tree-sitter 未安装导致
  的模块无法导入，其余全部通过或按环境跳过。

## 已完成（2026-10-14 第三批：仅 DeepSeek 路由）

- 用户 2026-10-14 重新授权公开源码评测（至 2026-10-31，mall `0504e86`，本机、仅评测）；随后告知 Ark 订阅已过期，指示直接使用 DeepSeek。
- 会话产物新增“仅 DeepSeek”路由：standing authority 只含一个 DeepSeek PRIMARY scope 时，会话配置可只声明一条 DeepSeek 路由；
  旧版（无 standing authority）配置、路由与授权 scope 不一致、或仍传入 Ark Gateway 时一律拒绝。DeepSeek 作为唯一路由时仍经过
  PDR-007 调度准入（闲时窗口、价格页 15 分钟新鲜度、调用/令牌/时长上限），运行时层原本已支持单路由，无需改动。
- 启动入口按配置只创建实际路由的 Gateway 数据库；启动与结束收据对单路由输出一条 Provider 审计，Ark 资格结果摘要记为空。
- 测试：新增加载约束与单路由准备各 1 项；容器全量 1,224 项，仅 tree-sitter 未安装的模块导入失败。
- 运行脚本：`var/iteration-010/slice-001/task1-step-a/launch.py`（主仓库，不入库）。

## 剩余工作

1. **在线运行（需在你的 Mac 上，北京时间闲时窗口内）。** 运行 `launch.py a`（D1—D5）与 `launch.py b`（D6）。
2. **按结果修正。** 在线运行暴露的问题按责任层归因修复；不按题面写规则。

## 完成判据

- 浏览器请求实际进入新执行器，D1—D6 全部产出答案或诚实限制，且每个实质结论都有本轮引用；
- 记录每题的工具调用、读取字节、时延、模型调用次数；
- 失败按责任层归因，到期按失败出口交付。

## 完成后的清理

新执行器在 D1—D6 上稳定后，评估退役旧对话协议模块（`conversational_engineering_model`、`engineering_question_answering` 中仅服务旧协议
的部分、`lightweight_engineering_agent` 的候选排序与屏蔽补丁），并在架构评审中报告。
