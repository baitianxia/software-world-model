# 新一轮未见项目验收输入 002

| 项目 | 当前值 |
|---|---|
| 状态 | PASS；当前实现的六题系统答案已与密封直接源码答案配对，并由Codex逐维度独立复核通过 |
| 封存日期 | 2026-08-07 |
| 输入清单 | [`suite.json`](../../../validation/product_holdout_iteration_002/suite.json) |
| 清单摘要 | `sha256:b4821e583a038bbeb2bb08006f1094c552427d53927ff762b780dcccbadb2fc7` |
| 本地校验 | 278项生产测试与Python编译检查通过；两个冻结工作区校验通过 |
| 能力证明 | `var/general-capability-current-v58/capability-qualification.json`，有效至2026-08-14 11:14（北京时间） |
| 产品验收记录 | `product_validation_158ce6cc0a4398e932c497a7fea34110`，有效至2026-08-14 11:40（北京时间） |
| 验收记录摘要 | `sha256:67b6a7e6db3bbeded2707d00f4e59b013455d93366badcf026948b74197d00f9` |
| 生产启用 | 未执行；验收记录不会自动启用生产 |

## 1. 已封存的输入

本轮使用两个此前未参与系统开发调试的公开工程。每个工程固定到一个发布标签、精确提交、源码树、远程仓库身份和许可证摘要；本地工作区必须保持干净。

| 工程 | 发布标签 | 精确提交 | 源码树 | 问题数 |
|---|---|---|---|---|
| 线程上下文传播库 | `v2.14.5` | `9c6552bbd7eda52b7bfb03c24c4f9aee514e91f3` | `2f8c335e9027e0341042aedc99a52ba08a9ae1c8` | 3 |
| 文档模板引擎 | `v1.12.2` | `58fdb6c7d9db7da53cd420ff1ebde49813bd7af2` | `c04630a020cc6b1d2ca01014aea1e6c61a651083` | 3 |

六个问题覆盖：任务上下文生命周期、执行器集成、计划任务删除修复、文档渲染流程、命名标签扩展策略、远程资源超时修改。问题同时包含冻结版本行为和精确父提交到目标提交的变化分析。

## 2. 公平性和独立性

- 直接回答路径和本系统辅助回答路径读取完全相同的题目、提交边界、允许文件和资源限制。
- 每个路径最多进行 34 次模型调用和 12 次只读源码操作；每次源码操作最多读取 16000 字节，模型总输入、总输出、单次输出和单次等待上限也完全相同。34 次是八个子问题上限、十二步来源调查和所有独立复核阶段共同构成的最坏情况上限，不是正常任务必须消耗的次数。
- 发给两侧模型的任务输入不包含评分维度、参考答案或评审规则。
- 参考答案与评分依据只能在两侧答案都密封后交给独立评审方。
- 独立评审方必须同时区别于两侧答案生成来源。
- 任意一个问题中，本系统答案的正确性或完成度低于直接回答，或者出现重大事实错误，整轮验收都失败；其他问题的高分不能抵消。

## 3. 防篡改和漂移关闭

输入清单使用代码内固定摘要，而不是只依赖清单自带摘要。因此，修改题目后重新计算文件摘要仍不能绕过封存版本。

每次执行前都会重新检查：

1. 当前提交和源码树与封存值一致；
2. 发布标签精确指向当前提交；
3. 远程仓库地址和许可证内容没有变化；
4. 工作区没有未提交修改；
5. 历史分析的目标提交可从冻结版本到达，且父提交一致；
6. 每个问题只能读取清单允许的文件。

任一检查失败都停止该次验收，不允许自动改题、换提交或扩大源码范围。

每个任务、每条回答路径和每个运行标识使用独立的本地运行数据库。同一运行标识可以恢复原调用，不同运行标识不会复用旧启用记录或模型调用；数据库文件名只包含运行标识的摘要，不直接使用外部输入作为路径片段。

## 4. 最终执行结果

用户已明确授权把清单中每题允许范围内的源码片段发送给已配置的火山模型。最终运行没有复用实现指纹变化前的诊断答案：六个系统答案全部来自`var/product-holdout-final-v59/path-results/`，并绑定当前实现摘要`sha256:8973e07290336c5443f00a93f00ac27401423fbf2e7e02b17c2b250b3159f301`与当前能力证明。直接源码答案来自先前已密封且任务输入完全相同的`var/product-holdout-final-v31/path-results/`。

Codex在两侧答案密封后读取冻结源码和全部验收维度，独立填写复核表。结果如下：

| 问题 | 维度数 | 直接源码答案 | 本系统答案 | 重大错误 | 结论 |
|---|---:|---|---|---:|---|
| 任务上下文生命周期 | 5 | 全部正确且完整 | 全部正确且完整 | 0 | PASS |
| 执行器包装选择 | 5 | 全部正确且完整 | 全部正确且完整 | 0 | PASS |
| 计划任务删除变化 | 5 | 全部正确且完整 | 全部正确且完整 | 0 | PASS |
| 文档两阶段渲染 | 6 | 全部正确且完整 | 全部正确且完整 | 0 | PASS |
| 命名标签扩展策略 | 6 | 全部正确且完整 | 全部正确且完整 | 0 | PASS |
| 远程资源超时变化 | 6 | 全部正确且完整 | 全部正确且完整 | 0 | PASS |

最终材料位于`var/product-holdout-final-v59/evidence/`，权威记录位于`var/product-holdout-final-v59/authority.sqlite3`。执行顺序为：

1. 确认模型接口符合性结果和当前通用方案能力证明仍有效；
2. 为每个问题生成同一份路径无关输入；
3. 分别运行直接回答和本系统辅助回答并密封结果；
4. 由独立评审方根据冻结源码建立参考依据并逐题比较；
5. 六题全部不退步后，才写入有时效的产品验收记录；
6. 仍需用户显式作出限定范围的启用决定，系统不会因验收通过自动启用。当前只剩这一步未执行。

上述顺序已有统一命令入口。先执行不联网校验：

```bash
PYTHONPATH=src:. python3 -m validation.product_holdout_iteration_002.cli verify-inputs \
  --workspace-root .
```

取得当前能力资格后，对每个封存问题分别执行 `run-direct` 和 `run-system`。两条路径使用各自独立的运行数据库，完成结果写入只写一次的密封文件；相同运行可以恢复，内容不同不能覆盖。随后使用 `seal-pair` 固定同题的两份答案。只有配对完成后，评分维度才允许交给 Codex 进行独立源码复核，并通过 `seal-review` 形成逐维度评审记录。

每个问题使用以下顺序；`<问题名称>`取自封存清单，`<本轮运行名称>`由操作者为本次验收指定：

```bash
PYTHONPATH=src:. python3 -m validation.product_holdout_iteration_002.cli run-direct \
  --workspace-root . --task-id <问题名称> --run-id <本轮运行名称> \
  --conformance-result var/conformance/<当前结果>.json \
  --result-directory var/product-holdout/path-results

PYTHONPATH=src:. python3 -m validation.product_holdout_iteration_002.cli run-system \
  --workspace-root . --task-id <问题名称> --run-id <本轮运行名称> \
  --conformance-result var/conformance/<当前结果>.json \
  --evaluation-database var/general-capability/evaluation.sqlite3 \
  --qualification-proof var/general-capability/capability-qualification.json \
  --result-directory var/product-holdout/path-results

PYTHONPATH=src:. python3 -m validation.product_holdout_iteration_002.cli seal-pair \
  --direct-result var/product-holdout/path-results/<问题名称>--direct.json \
  --system-result var/product-holdout/path-results/<问题名称>--world_assisted.json \
  --result-directory var/product-holdout/evidence

PYTHONPATH=src:. python3 -m validation.product_holdout_iteration_002.cli prepare-review \
  --pair var/product-holdout/evidence/<问题名称>--pair.json \
  --result-directory var/product-holdout/review-drafts
```

最后一条命令只生成判断为空的复核表，并自动列出该问题的全部验收维度。Codex 必须查阅两份答案和冻结源码，为两侧逐维度填写“正确且完整、正确但部分完成、未回答、错误”之一及理由，再密封：

```bash
PYTHONPATH=src:. python3 -m validation.product_holdout_iteration_002.cli seal-review \
  --pair var/product-holdout/evidence/<问题名称>--pair.json \
  --review-draft var/product-holdout/review-drafts/<问题名称>--review-draft.json \
  --result-directory var/product-holdout/evidence
```

六题评审全部不退步且没有重大错误时，`record-acceptance` 才会写入有时效的产品验收记录。该命令还会重新检查源码工作区、当前接口符合性和当前能力资格。写入验收记录仍不会自动启用生产。

```bash
PYTHONPATH=src:. python3 -m validation.product_holdout_iteration_002.cli record-acceptance \
  --workspace-root . --evidence-directory var/product-holdout/evidence \
  --conformance-result var/conformance/<当前结果>.json \
  --evaluation-database var/general-capability/evaluation.sqlite3 \
  --qualification-proof var/general-capability/capability-qualification.json \
  --authority-database var/product-holdout/authority.sqlite3
```

本轮同时修正了系统答案的质量边界：正式知识不再只能保存逐字源码。解释性结论必须绑定提出结论和独立复核的两次模型调用，并证明复核时看到的源码片段、最终证据和被接受结论完全一致；否则继续按原规则拒绝入库。

## 5. 命名说明

代码中的 `product_holdout_iteration_002` 表示“第二版产品未见项目验收材料”，不是产品功能名称；`direct` 表示直接查阅来源形成答案，`world_assisted` 表示通过本系统的正式知识路径形成答案。与用户沟通时优先使用这些中文含义。
