# Software World Model

Software World Model 把软件来源转化为可追溯、可审核、可复用的正式知识，并通过受控的 Agentic 任务路径回答软件问题。生产实现是 Python 模块化单体，历史验证 Demo 与生产代码严格分离。

## 从哪里开始

- 当前开发状态与唯一入口：[docs/project/current.md](docs/project/current.md)
- 系统本质、架构和稳定契约：[docs/system/README.md](docs/system/README.md)
- Roadmap、迭代与开发过程：[docs/project/README.md](docs/project/README.md)
- 完整文档导航：[docs/README.md](docs/README.md)
- Agent 阅读和回写规则：[AGENTS.md](AGENTS.md)

Iteration 001 的 pre-Git 历史记录在本机体验范围给出完成裁决；提交 `476517b` 是其后的重构前仓库快照，不是原始运行身份。生产启用未执行。当前未提交工作区的 Strategy 实现与历史证明绑定的 `1.38.0` 不同，因此旧 Capability / Product 证明不能授权当前工作区，浏览器真实模型路径必须保持关闭。精确当前版本由代码拥有，状态只以 [current.md](docs/project/current.md) 及其引用的证据为准。

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
| `docs/archive/` | 被替代材料和迁移记录；不得作为当前编码依据 |
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

浏览器体验、证明绑定和失效后的处理方式见 Iteration 001 的结果记录。服务没有认证时只能绑定本机回环地址。
