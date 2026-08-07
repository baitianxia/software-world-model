# Generated documentation indexes

本目录由 `python3 scripts/docs.py generate` 从 current System/Project 文档的 front matter 生成，用于 Agent 快速检索和自动追溯。

- `catalog.json`：文档 ID、类型、状态、权威、旧来源和路径；
- `dependency-graph.json`：文档 ID 依赖；
- `traceability.json`：文档到代码与测试的引用；
- `current-context.md`：当前开发入口与按权威分组的紧凑索引。

这些文件不是规范，不得人工编辑。`python3 scripts/docs.py check` 会验证它们与源文档一致。
