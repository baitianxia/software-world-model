---
id: FINDING-010-291
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [project, application, quality]
depends_on: [FINDING-010-290]
code: [pyproject.toml, src/software_world_model/interface/http_api.py, src/software_world_model/interface/engineering_qa_alpha_cli.py, src/software_world_model/interface/engineering_qa_preview_cli.py]
tests: [tests/test_engineering_chat_alpha_cli.py, tests/test_engineering_qa_alpha_cli.py, tests/test_engineering_qa_preview_cli.py, tests/test_browser_chat_interface.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: code-and-tests-only
target: pyproject.toml
---

# FINDING-010-291：隔离兼容入口，收敛当前开发阅读路径

代码盘点确认，仓库同时暴露产品 Chat、旧 Evidence HTTP、旧 Engineering QA 和 Preview 多套入口，且部分入口复用端口和不同 Agent/Provider 路径，容易让体验测试进入错误实现。

本次只做可逆的边界清理：

- 保留底层兼容模块和测试，不直接删除仍有 import 依赖的旧实现；
- 将安装命令改为明确的 `*-evaluation` 名称，唯一产品命令保留为 `swm-engineering-chat`；
- 将 Engineering Chat Session 的默认 Agent mode 改为 Source-only Lightweight；Legacy 只有兼容测试或显式调用才可启用；
- 将旧浏览器运行说明和 Slice 阶段记录移入实现历史参考；
- 当前活动 Slice 只保留用户价值纵向目标和唯一执行计划入口；
- 不修改架构基线或跨模块职责，不增加协议、Prompt、字段或题面特判。

`docs.py`、计划形状检查、架构锁检查和 55 项入口/运行时/浏览器定向测试均通过。兼容代码的最终删除仍需在唯一 Agent 主路径完成并迁移依赖后单独处理。
