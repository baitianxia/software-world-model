---
id: ITER-010-TASK-1-STEP-A
kind: development-design
status: current
authority: current-development
owners: [engineering, architecture]
depends_on: [ITER-010-EXECUTION-PLAN-CURRENT, SYS-ADR-021, SYS-ADR-020]
code: [src/software_world_model/source_integration/exact_revision_tools.py]
tests: [tests/test_exact_revision_tools.py]
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

## 剩余工作（按顺序）

1. **新的精简执行器。** 新建 `application_services/chat_agent.py`，实现既有 `EngineeringConversationTurnExecutor` 接口，使对话服务与
   浏览器无需改动即可接入。循环：模型提出一个动作 → 执行只读工具 → 观察追加到本轮台账 → 模型决定继续或作答。
   - 工具目录：`list_paths / search / read / log / blame`（上面的工具），步骤 B 再加世界模型操作。
   - 读取不需要先登记候选；Citation 只能引用本轮实际返回的条目（定位符 + 内容摘要），由执行器重算校验。
   - 预算：按 token、时延、字节和无进展检测；耗尽时由同一模型基于已有证据给出带限制的答案并照常复核。
2. **模型输入输出。** 通过 `ModelExecutionPort`（ADR-020）调用模型；新写精简的 Agent 与 Reviewer 提示和 JSON 输出格式，
   不复用旧 `conversational_engineering_model` 的协议版本与正文校验。
3. **复核。** fresh Reviewer 读取用户问题、相关对话、证据包和草稿；可经同一工具做有界核验读取（不进入证据包）；返回 verdict 与具体
   Finding，最多一次整体改写或一次补证尝试。
4. **接线与开关。** 会话运行时增加执行器选择：默认使用新执行器，旧执行器保留为回退，便于对比；Turn Trace 写入 `var/` 下的本地文件。
5. **验证。** 离线：用脚本化模型覆盖工具调用、引用校验、预算耗尽、复核改写与失败隔离；在线：在你的 Mac 上用既有 Provider 配置
   启动浏览器，跑 D1—D6 并记录逐题结果（模型凭据只在 Mac 上可用）。

## 完成判据

- 浏览器请求实际进入新执行器，D1—D6 全部产出答案或诚实限制，且每个实质结论都有本轮引用；
- 记录每题的工具调用、读取字节、时延、模型调用次数；
- 失败按责任层归因，到期按失败出口交付。

## 完成后的清理

新执行器在 D1—D6 上稳定后，评估退役旧对话协议模块（`conversational_engineering_model`、`engineering_question_answering` 中仅服务旧协议
的部分、`lightweight_engineering_agent` 的候选排序与屏蔽补丁），并在架构评审中报告。
