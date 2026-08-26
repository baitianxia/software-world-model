---
id: FINDING-010-108
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [source, ai, application, security, quality]
depends_on: [FINDING-010-107, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/interface/engineering_qa_source.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_engineering_qa_source.py, tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: align-literal-search-contract-and-rank-authorized-path-candidates-before-file-fuse
target: SYS-CONTRACT-SOURCE-ARTIFACT
---

# FINDING-010-108：Chat 的 semantic search 提示与 literal Worker 不一致

## Observation and root cause

`FINDING-010-107` 的五轮输出证明主 Agent 并非没有发起调查，而是被错误的 model-facing tool contract 引导：Tool Catalog 明确允许
“literal or semantic search proposal”，但 `LocalGitRetrievalWorker` 只接受一个 query，并以大小写敏感的 `query in line` 执行 literal
content match。对于目录级 Source Profile，Worker 又按 canonical tree order 先读文件；64-file fuse 可能在包含 source-native identifier 的
路径之前耗尽。

这是 system-contract / systemic mismatch。把 64-file 上限调高、为 mall/login 写关键词分支，或把 truncated empty result解释为“不存在”
都会破坏既有安全与认识论边界。

## Decision and disposition

- `SOURCE_SEARCH` 的 model-facing contract 现在只允许一个短、大小写敏感、预期在选定 evidence 中逐字出现的 literal token；semantic
  description 和自然语言 search request 明确禁止。主 Agent 应从当前问题、Conversation、World Model 或 prior Observation 选择
  source-native identifier。
- Worker 的 content match 仍保持大小写敏感 literal semantics。执行前只使用已经授权的 Git tree path metadata 做确定性候选排序：stem/name
  exact → name contains → full path contains → canonical fallback。排序不读取额外 blob、不扩大 allowlist/class/revision，也不生成 path authority。
- file/byte/result fuse 全部不变。扫描仍可能为 `PARTIAL`；Coverage 新增
  `QUERY_PATH_RELEVANCE_THEN_CANONICAL@1`，truncation、未检查文件和 absence 边界继续强制保留。

新增回归在 21 个授权文件、`maximum_files=2` 下证明 canonical 顺序末端的 `LoginService.java` 会先被检查并产生真实 literal item，同时仍以
`SOURCE_FILE_FUSE_EXHAUSTED / PARTIAL` 报告未完整扫描；旧实现会先读两个 unrelated 文件并得到 0 item。Source 9/9、Conversational Model
7/7、compile 和 `git diff --check` 已通过。该证据只是 local candidate，不追认 run-035 的五轮答案，也不授权新的 Provider/browser 执行。
