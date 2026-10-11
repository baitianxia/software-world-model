# Software World Model

Software World Model 把软件来源转化为可追溯、可审核、可复用的正式知识，并通过受控的 Agentic 任务路径回答软件问题。生产实现是 Python 模块化单体，历史验证 Demo 与生产代码严格分离。

## 从哪里开始

- 当前开发状态与唯一入口：[docs/project/current.md](docs/project/current.md)
- 系统本质、架构和稳定契约：[docs/system/README.md](docs/system/README.md)
- Roadmap、迭代与开发过程：[docs/project/README.md](docs/project/README.md)
- 完整文档导航：[docs/README.md](docs/README.md)
- Agent 阅读和回写规则：[AGENTS.md](AGENTS.md)

Iteration 001 的 pre-Git 历史记录在本机体验范围给出完成裁决；提交 `476517b` 是其后的重构前仓库快照，不是原始运行身份。生产启用未执行。
当前版本和工作树状态以 Git 实际状态为准；当前任务顺序以 [current.md](docs/project/current.md) 引用的执行计划为准，机器执行控制以对应 Iteration Manifest 为准，用户最新指令只改变当前工作范围。历史证明不代表当前候选已通过验证。

## 仓库目录

| 目录 | 作用 |
|---|---|
| `src/software_world_model/` | 生产模块化单体 |
| `tests/` | 生产代码自动化验证 |
| `validation/` | 可执行的能力与产品验证程序 |
| [`validation-projects/`](validation-projects/README.md) | 需独立准备且不纳入父仓库历史的冻结外部工程 |
| `demo/` | 历史架构验证 Demo，不是生产实现 |
| `docs/system/` | 当前接受的系统本质、架构、契约和质量边界 |
| `docs/project/` | Roadmap、迭代设计、进度、发现和结果 |
| `docs/archive/` | 文档迁移记录；被替代正文由 Git 历史保存，不作为当前编码依据 |
| `var/` | 本机运行证据和数据库；生成内容，不受 Git 管理 |

`validation-projects/` 的子仓库不纳入本仓库 Git 历史；完整回归前需按其说明准备精确 Checkout。

## 本地验证

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=demo python3 -m unittest discover -s demo/tests -q
python3 scripts/docs.py check
```

测试通过只能证明被测提交与被测范围；真实 Provider 符合性、模型能力、产品验收和生产启用是相互独立的门禁。

## 本地入口

```bash
PYTHONPATH=src python3 -m software_world_model.interface.cli --help
PYTHONPATH=src python3 -m software_world_model.interface.provider_cli status
```

当前浏览器工作入口见 [current.md](docs/project/current.md) 引用的执行计划；Iteration 001 的结果只作历史证据。
默认浏览器入口接入主 Agent 是当前计划中的开发任务，不能把未连接的页面当作完整体验。服务没有认证时只能绑定本机回环地址。
