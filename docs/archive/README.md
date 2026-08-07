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

本目录保存被新结构替代的完整材料和迁移记录。它们用于审计形成过程、核对历史状态和解释旧标识，不是当前开发输入。

- `legacy-documents/`：重构前的 `architecture/`、`detailed-design/`、`implementation/`、`validation/` 和 `history/` 原树。
- `migration-records/`：目录或权威边界变更的记录。

读取历史材料时必须同时确认其日期、状态和替代文档。旧日志中较早的 `NOT RUN`、`HOLD` 或失败记录不能覆盖后续当前证据；后续成功也不能删除历史失败。

Legacy 文件正文保持字节不变，因此其中指向仓库源码或运行目录的相对链接仍按迁移前位置书写，移动后不保证可点击。需要原始导航语境时使用 Git 提交 `476517b`；不要为了修复链接改写历史正文。
