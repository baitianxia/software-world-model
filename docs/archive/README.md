---
id: ARCHIVE-INDEX
kind: archive-index
status: historical
authority: historical
owners: [documentation]
depends_on: []
code: []
tests: []
---

# 历史文档

本目录只保存文档权威边界和目录结构的迁移记录，用于解释当前结构如何形成，不是当前开发输入。

- `migration-records/`：目录或权威边界变更的记录。

被替代正文不在当前工作树重复保存。重构前原树由基线提交 `476517b5baf62abcc5a6ddda30b33335d262a8f3` 固定；按原路径读取，例如：

```bash
git show 476517b5baf62abcc5a6ddda30b33335d262a8f3:docs/detailed-design/README.md
```

读取历史材料时必须同时确认其日期、状态和替代文档。旧日志中较早的 `NOT RUN`、`HOLD` 或失败记录不能覆盖后续证据；后续成功也不能删除历史失败。需要恢复整棵旧树时应从该提交建立临时 worktree，不把旧正文重新提交到当前文档树。
