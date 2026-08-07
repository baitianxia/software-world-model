# Contract Conformance 索引

> Conformance Fixture 定义机械验证方法；Fixture 文档、真实运行结果和 Capability Evaluation 是不同产物。

| Fixture | 状态 | 验证对象 |
|---|---|---|
| [CC-MODEL-NO-TOOLS-001](CC-MODEL-NO-TOOLS-001.md) | Offline Mechanics Implemented — Live Not Executed | OpenAI Responses no-tools Adapter 的输入闭包、无外部访问、模型身份和生产 Sink 拒绝 |
| [CC-ARK-CHAT-NO-TOOLS-001](CC-ARK-CHAT-NO-TOOLS-001.md) | Live PASS / Current | 火山方舟Chat Completions Adapter的两次真实边界、12项Oracle、安全结果封存和资格加载 |

validation-only Adapter与离线机械Oracle已有可重复测试，但当前工作区没有VCS Commit，也尚无冻结的实现Artifact Digest、Provider Configuration Revision、exact Model Reference或真实Run，因此不能标记为Passed，也不能为模型Strategy签发生产资格。

```bash
PYTHONPATH=demo python3 -m unittest demo.tests.test_openai_no_tools_adapter -v
```

该命令不调用真实Provider，不能产生Conformance PASS。

未来真实执行结果应作为独立不可变 Result 保存，并固定：Fixture Revision、实现 Commit、Adapter Profile、Provider 配置、Model Reference、原始 Capture / Log Reference 和 Result Digest。Fixture 本身不因某次 Run 结果而改写。

方舟Fixture已经提供生产CLI运行器；它保存摘要而非原始Prompt / Response：

```bash
PYTHONPATH=src python3 -m software_world_model.interface.provider_cli conformance \
  --result-directory ./var/conformance \
  --operator local-operator
```

该命令产生两次真实Provider调用，只有最终代码稳定后才应执行，避免实现摘要随后变化使结果立即失效。
