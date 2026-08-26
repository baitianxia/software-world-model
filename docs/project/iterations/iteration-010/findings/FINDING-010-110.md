---
id: FINDING-010-110
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [source, application, quality, security]
depends_on: [FINDING-010-108, FINDING-010-109, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/engineering_question_answering.py, scripts/docs.py]
tests: [tests/test_conversational_engineering_tools.py, tests/test_engineering_qa_source.py, tests/test_engineering_question_answering.py, tests/test_conversational_engineering_agent.py, tests/test_conversational_engineering_model.py, tests/test_engineering_conversation.py, tests/test_docs_gate.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: reserve-one-follow-up-read-slot-within-the-unchanged-total-source-file-fuse
target: SYS-CONTRACT-SOURCE-ARTIFACT
---

# FINDING-010-110：截断搜索会在 locator 读取前耗尽总文件熔断

## Observation and root cause

对 `FINDING-010-108/109` 修复后的本地纵切做组合审计时，单独通过的 path-ranked Search 与 opaque-locator Read 仍不能在默认大目录条件下
连成一条链。默认 Request 总文件上限为 64；SEARCH operation 原先可以消费全部剩余 64 个文件。即使候选排序让目标文件第一个命中，
Worker 为保持真实 Coverage 仍继续扫描到 operation fuse，并返回带 locator 的 `PARTIAL / SOURCE_FILE_FUSE_EXHAUSTED`。随后 Broker 因
累计 `source_files == 64` 拒绝 READ，所以“找到目标”仍不能保证主 Agent 取得该 locator 的完整内容。

这是 Source Broker 的系统性预算编译问题，不是模型质量、mall 特判或提高熔断即可解决的问题。只让 Worker 在首个命中后伪装完整、丢弃
PARTIAL boundary，或把总上限从 64 调高，都会削弱既有 Coverage 或安全边界。

## Decision and disposition

- 当 SEARCH 注册了后续 READ/PARSE、当前总文件预算至少还剩 2 个名额时，Broker 将本次 SEARCH 的 operation 上限最多编译为
  `remaining_files - 1`；若总预算高于单 operation 的既有 64 上限，则仍使用较小者。
- 保留名额属于同一个 Request 总熔断，不增加任何文件、字节、operation、结果或时间预算。默认大目录路径现在是 SEARCH 最多 63 个文件，
  后续 exact locator READ 最多再读 1 个文件，累计仍不得超过 64。
- SEARCH 的大小写敏感 literal、path-metadata ordering、allowlist、Source Profile、exact revision、PARTIAL、Coverage、truncation 和
  boundary 语义全部不变。预算不足以同时搜索和读取时不伪造能力或结果。

新增 deterministic successor canary 使用 71 个授权临时 Java 文件，并提交 run-035 的同一五个固定问题。每个 Turn 都以
`SOURCE_SEARCH("LoginService")` 在 63 个文件处保留 `SOURCE_FILE_FUSE_EXHAUSTED / PARTIAL` boundary，再使用当前 Turn 签发的 opaque
locator 完成第 64 个文件 READ，随后形成 Package、fresh Review 和 Delivery；五轮 Work State 在同一 Conversation 中从 revision 3
递增到 15，fake Agent/Reviewer 的 logical dispatch 为每轮 4、总计 20。新 Conversation 的“它呢？”在 Application policy 中以
`CLARIFICATION / APPLICATION_INPUT_CLARIFICATION` 完成，Agent/Reviewer/Source 调用数和 dispatch 总数均不增加，旧 Conversation digest
保持不变。

Source、旧 Engineering QA、Agent、Model 与 Conversation 相邻回归合计 `99/99 PASS`，compile 与 `git diff --check` PASS。完整套件共
1275 项；默认沙箱为 6 FAIL + 7 ERROR，其中额外 1 FAIL + 6 ERROR 来自 AF_UNIX denial；允许本机 socket 后为 1269 PASS、5 FAIL +
1 ERROR，精确保持冻结 V-009 implementation-drift 的 4 FAIL + 1 ERROR 和本机 Codex binary digest drift 的 1 FAIL，没有本次模块新增失败。

测试只读取临时 Git fixture，使用本地 fake model ports；它验证的是五轮执行、证据预算、状态连续性和隔离机制，不验证五个答案的产品质量
或 World Model + Source 组合质量。没有读取 mall 或 resources，没有 credential、外部网络、Provider/model、listener/browser 或 Production
Activation。本证据关闭本地组合缺口，但不追认 run-035，也不把五轮 Chat/Quality/XD live Gate 改为 PASS；successor artifact 和真实
canary 仍要求绑定新 exact commit/tree 的 Session Authority。
