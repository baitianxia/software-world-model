# 通用任务能力评估执行手册

## 当前状态

六类职责的真实执行入口、结果密封、独立复核材料和最终资格登记已经连通。当前实现已使用真实模型完成六个固定用例，由Codex依据封存条件逐项独立复核通过，并生成有效至2026-08-14 11:14（北京时间）的能力证明。随后六题未见项目产品验收也已独立通过；两类证明均没有触发生产启用。

本轮固定检查：需求保真、源码调查、事实与证据绑定、逐问题充分性、只从正式知识选择答案、最终语义复核。需求保真和事实绑定各包含“生成 + 独立角色复核”，因此六个用例合计八次模型调用。

封存输入位于 [`validation/agentic_capability_iteration_001/suite.json`](../../../validation/agentic_capability_iteration_001/suite.json)，摘要为 `sha256:2d1eb05c461ad2efc6d5f5c7f31f9af33de469a79c032d056a1bc1b6468da03d`。每个用例同时包含执行输入和仅供独立评审使用的预期条件；执行模型只接收输入，不接收预期条件。

## 执行顺序

先做不联网检查：

```bash
PYTHONPATH=src:. python3 -m validation.agentic_capability_iteration_001.cli verify-inputs
```

真正验收时，先针对当前代码重新运行模型接口符合性检查。代码、接口地址或适配器发生变化后，不允许复用旧结果：

```bash
PYTHONPATH=src:. python3 -m software_world_model.interface.provider_cli conformance \
  --result-directory var/conformance \
  --operator acceptance-operator
```

随后运行六个职责用例。该命令会进行八次真实模型调用，输出分别保存在 `outputs/`；每个用例使用独立数据库，重试时复用已记录调用：

```bash
PYTHONPATH=src:. python3 -m validation.agentic_capability_iteration_001.cli run-all \
  --conformance-result var/conformance/<当前结果>.json \
  --result-directory var/general-capability
```

模型输出完成后，由 Codex 独立查看每个密封输出、封存预期条件和必要源码，形成复核草稿。草稿不能由生成答案的火山模型自行判断。每个草稿通过以下命令密封，输出目录统一使用 `reviews/`：

先由程序根据精确输出生成一份所有判断均为空的复核表。该步骤只绑定用例、输出和预期条件，不会自动填写“通过”：

```bash
PYTHONPATH=src:. python3 -m validation.agentic_capability_iteration_001.cli prepare-review \
  --output var/general-capability/outputs/<用例>.json \
  --result-directory var/general-capability/review-drafts
```

Codex 查看真实输出和封存条件后填写复核者身份、规则符合性、预期条件匹配、未经授权引用数量、重大遗漏、重大错误、发现项和带时区的复核时间。未填写字段不能密封。然后执行：

```bash
PYTHONPATH=src:. python3 -m validation.agentic_capability_iteration_001.cli seal-review \
  --output var/general-capability/outputs/<用例>.json \
  --review-draft var/general-capability/review-drafts/<用例>.json \
  --result-directory var/general-capability/reviews
```

六个复核全部形成后才登记能力评估。任何必测用例失败、遗漏、调用用量不完整、评审来源与生成来源相同或材料被修改，都不会产生资格：

```bash
PYTHONPATH=src:. python3 -m validation.agentic_capability_iteration_001.cli finalize \
  --conformance-result var/conformance/<当前结果>.json \
  --evidence-directory var/general-capability \
  --evaluation-database var/general-capability/evaluation.sqlite3 \
  --result-directory var/general-capability
```

最终命令只形成有时效的能力资格，仍不会启用生产。当前两个未见工程的六题产品对照已经取得独立评审通过；后续只在用户明确决定时执行限定范围的生产启用。

## 恢复与安全边界

- 每个模型调用先写入本地数据库，再发送请求；已完成调用按原逻辑请求恢复。
- 结果文件只允许首次写入或完全一致的重放，不允许覆盖成不同内容。
- 输出记录包含实际模型身份、每次请求标识和完整用量。
- 评审材料绑定精确输出摘要和仅供评审使用的预期条件摘要。
- 能力资格绑定当前方案代码摘要、接口符合性结果、模型配置、模型身份和适配器版本；任一依赖变化都会失效。
