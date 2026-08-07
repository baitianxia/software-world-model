# Software World Model

平台文档统一维护在 [docs/](docs/README.md)。当前状态为`模型接口符合性 PASS / 通用能力评估 PASS / 六题产品验收 PASS / 本机浏览器体验已启用 / 生产启用未执行`。CLI、本地浏览器聊天、本地HTTP接口、本地Git知识、受控源码调查、正式知识生成、答案复核、能力评估、产品对照和显式启用入口均已实现。直接源码答案与本系统答案都由火山`glm-5.2`生成，比较结论由Codex独立重读源码后形成，没有把两侧答案交回火山自评。当前实现已达到本轮产品验收和本机人工体验标准；生产启用仍按约定保持关闭，不能描述为已经上线。

## 入口

- [完整文档导航](docs/README.md)
- [概要架构基线](docs/architecture/Software_World_Model_Architecture_Baseline.md)
- [详细设计总纲](docs/detailed-design/Software_World_Model_Detailed_Design.md)
- [Iteration 001 实施计划](docs/implementation/iteration-001/Implementation_Plan_Iteration_001.md)
- [Design Baseline Manifest — Revision 002](docs/detailed-design/governance/Design_Baseline_Manifest_Iteration_001_Revision_002.md)
- [Implementation Baseline Manifest — Revision 002](docs/implementation/iteration-001/Implementation_Baseline_Manifest_Iteration_001_Revision_002.md)
- [Offline Implementation Result — 001](docs/implementation/iteration-001/Offline_Implementation_Result_001.md)
- [Preconfiguration Functional Acceptance — 001](docs/implementation/iteration-001/Preconfiguration_Functional_Acceptance_001.md)
- [Live Provider Configuration — 001](docs/implementation/iteration-001/Live_Provider_Configuration_001.md)
- [Ark Chat Conformance Fixture](docs/implementation/iteration-001/conformance/CC-ARK-CHAT-NO-TOOLS-001.md)
- [Capability Evaluation Runtime — 001](docs/implementation/iteration-001/Capability_Evaluation_Runtime_001.md)
- [JWT Capability Run Harness — 001](docs/implementation/iteration-001/JWT_Capability_Run_Harness_001.md)
- [JWT Capability Run Result — 001](docs/implementation/iteration-001/JWT_Capability_Run_Result_001.md)
- [通用模型任务运行链路实施记录 — 001](docs/implementation/iteration-001/General_Model_Task_Runtime_001.md)
- [本机浏览器聊天体验说明 — 001](docs/implementation/iteration-001/Browser_Chat_Experience_001.md)

## 仓库目录

| 目录 | 用途 |
|---|---|
| [src/](src/software_world_model/) | 按当前实施计划开发的生产模块化单体代码 |
| [tests/](tests/) | 生产代码的单元、契约、事务和恢复测试 |
| [docs/](docs/README.md) | 架构、详细设计、实施契约、Conformance 和验证记录 |
| [demo/](demo/README.md) | 历史架构验证 Demo，不是生产实现 |
| [validation-projects/](validation-projects/README.md) | 外部验证工程，不属于平台设计 |

2026-08-05 完成的目录重组记录在[文档结构迁移记录](docs/history/Documentation_Structure_Migration_Record_001.md)中。迁移前冻结树已保存为只读快照；当前有效基线为 `SWM-DBM-ITER-001-REV-002 + SWM-IBM-ITER-001-REV-002`。

## 离线开发验证

生产代码测试不需要外部Provider配置：

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

`demo/`历史验证回归继续使用其独立入口；两套测试结论不能互相替代。

```bash
PYTHONPATH=demo python3 -m unittest discover -s demo/tests -q
```

当前离线生产套件为`288 / 288`，历史Demo回归为`121 / 121`。新增覆盖自然语言需求规划与保真复核、受控来源调查、经两次独立调用复核的解释性正式知识、逐问题语义充分性、任一提示词命中的候选证据召回、分职责的有界契约修正、无害授权版本回显归一化、重复答案事实去重并合并证明引用、来源关闭的答案草稿、答案语义复核、模型调用及其完整输入恢复、知识缺口触发更新后的全量重评、六类职责真实评估入口、Codex独立评审证据、完整能力资格登记、逐任务产品对照、浏览器页面、项目连接、上下文追问、结果展示，以及能力评估与独立产品验收必须同时有效的启动门禁。当前六类通用能力和六题未见项目产品验收均已由真实模型执行并由Codex独立复核通过；本机浏览器体验已启用，生产未启用。证明过期或实现、模型、接口配置变化后必须重新评估。

## 本地验收入口

```bash
# 查看全部CLI命令
PYTHONPATH=src python3 -m software_world_model.interface.cli --help

# 启动已验收、仅绑定本机的浏览器聊天与JSON接口
PYTHONPATH=src python3 -m software_world_model.interface.http_api \
  --database var/browser-experience/swm.sqlite3 \
  --host 127.0.0.1 \
  --port 8765 \
  --enable-activated-model \
  --conformance-result var/conformance-v8/CC-ARK-CHAT-NO-TOOLS-001-ccrun_66bbedf18020445c9df5fac11526fda1.json \
  --activation-environment local-browser
```

启动后打开`http://127.0.0.1:8765/`。完整使用和到期处理见[本机浏览器聊天体验说明](docs/implementation/iteration-001/Browser_Chat_Experience_001.md)。

CLI现支持本地项目配置、精确目标解析、知识更新与查询、运行记录查看和本机浏览器体验启用。HTTP根路径提供普通用户聊天页面，浏览器接口自动管理技术标识、固定版本、知识快照和受控调查；原有结构化接口继续保留。聊天支持连接本地Git项目、可选版本比较和最近六条消息的跟进提问，回答仍必须经过正式知识与独立复核。模型方案未评估并激活时安全关闭。当前无认证，因此服务端强制只允许本机监听。

## 模型Provider配置

当前非敏感配置为火山方舟Coding Plan北京地域Base URL `/api/coding/v3`、实际Chat Completions Endpoint `/api/coding/v3/chat/completions`和模型`glm-5-2-260617`，密钥仅引用`env:ARK_API_KEY`：

```bash
# 不访问网络、不回显密钥
PYTHONPATH=src python3 -m software_world_model.interface.provider_cli status

# 本地安全注入轮换后的ARK_API_KEY后，执行最小在线探测
PYTHONPATH=src python3 -m software_world_model.interface.provider_cli probe

# 模型服务或适配器变化后重跑接口符合性验证；当前@8结果已PASS
PYTHONPATH=src python3 -m software_world_model.interface.provider_cli conformance \
  --result-directory ./var/conformance \
  --operator local-operator
```

`probe`不等于完整模型接口符合性测试；接口符合性、完整任务运行、独立比较、能力评估、产品未见项目验收和生产启用是彼此独立的门禁。启动代码强制要求当前通用能力评估和独立产品验收同时有效；这两项当前均已通过，生产启用仍未执行。配置与命名说明见[真实模型Provider配置记录](docs/implementation/iteration-001/Live_Provider_Configuration_001.md)。

完整JWT评测链、目录隔离、命名规则和后续命令见[JWT Capability Run Harness 001](docs/implementation/iteration-001/JWT_Capability_Run_Harness_001.md)。
