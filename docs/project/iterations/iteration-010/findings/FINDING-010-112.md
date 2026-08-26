---
id: FINDING-010-112
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, source, quality, security]
depends_on: [FINDING-010-110, FINDING-010-111, SYS-CONTRACT-SOURCE-ARTIFACT]
code: [src/software_world_model/application_services/engineering_question_answering.py, scripts/docs.py]
tests: [tests/test_conversational_engineering_tools.py, tests/test_engineering_question_answering.py, tests/test_docs_gate.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: separate-per-search-scan-fuse-from-whole-turn-source-file-fuse
target: SYS-CONTRACT-SOURCE-ARTIFACT
---

# FINDING-010-112：目录扫描与整轮 exact READ 共用一个文件熔断是职责错误

## Root cause and decision

`FINDING-010-111` 证明单名额 reservation 仍让真实 Agent 在第二个 exact locator READ 前失败。根因不是需要把 1 调成 2 或 3，而是
Broker 只有整轮 `maximum_source_files=64`，却把每次 SEARCH 的 scan 上限也编译为几乎全部剩余预算。SEARCH coverage 与后续多文件
flow 的执行容量因此互相吞噬；fake canary 只读取一个文件，遗漏了这个架构缺口。

资源契约现在显式区分两个高安全熔断：

- 整轮 `maximum_source_files` 继续为 64，所有 SEARCH/READ/PARSE 实际读取仍累计进入同一个总量；
- 每次 SEARCH 新增 `maximum_source_search_files`，current default 为 56 且强制不得大于总文件熔断；
- Broker 对 SEARCH 使用 `min(remaining total, per-search scan fuse)`，若 late SEARCH 时预算不足，仍至少为已注册 READ/PARSE 保留一个
  exact locator 名额；allowlist、Profile、revision、bytes、result、operation、wall-time、PARTIAL 和 Coverage 语义均不变。

该编译为一个默认 bounded Agent attempt 留出最多 8 个 exact file 名额，但不承诺模型一定使用它们，也不增加一次实际读取。它是通用资源
编译，不按 mall、问题、query、类名或路径分支。

## Verification and disposition

新增 73 文件相邻复现：literal/path-ranked SEARCH 在 56 个文件处以
`PARTIAL / SOURCE_FILE_FUSE_EXHAUSTED` 保留真实 Coverage，随后三个不同 opaque locator READ 全部成功，最终累计 59/64。原固定五轮 fake
canary 继续 5/5 成功并通过新 Conversation 零 dispatch 澄清；其每轮 SEARCH + READ 为 57/64。相关 Source/Agent/Model 聚焦组合当前
63/63 PASS，相邻 Chat/Source/docs 组合 217/217 PASS，docs gate 80/80 PASS，`scripts/docs.py check` 检查 513 份 current document
通过，受影响模块 `py_compile` 与 `git diff --check` 通过。允许本机 AF_UNIX 的全量 discovery 共 1277 项，1271 PASS；余下
5 failures + 1 error 均为既有 ITER-003 V-009 frozen implementation drift 或本机 Codex binary digest drift，本次 Source/Agent/Model/docs
模块没有新增失败。System truth 写回 Source Artifact Contract；这仍只是 local candidate，不追认 run-036 或授权新的 Provider/browser 执行。
