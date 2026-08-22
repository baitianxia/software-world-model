---
id: FINDING-010-018
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-016, FINDING-010-017]
code: [src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_model_source.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: distinguish-literal-search-queries-from-semantic-descriptions-and-opaque-locator-reference-ids-from-paths
target: src/software_world_model/ai_infrastructure/engineering_question_model_source.py
---

# FINDING-010-018：调查角色混淆了字面搜索、路径与 opaque locator reference

## Observation

candidate `e35d8f72a7a877abb73c285192eb64420da09592` 使用 17 个 exact 文件 capability 和 current DeepSeek qualification 启动第三次
`V-WEB-000`。Question Understanding 后，Initial Investigation 先提交 `search / SOURCE / "mall-admin 职责"`；Worker 完整检查 12 个
SOURCE 文件并正确返回 0 items。下一步模型提交 `read`，但把 allowlist 中的
`mall-security/src/main/java/com/macro/mall/security/util/JwtTokenUtil.java` 路径写进 `locator_reference`，而不是复用 typed Result 发出的
`source_locator_<id>`。当前 input 没有任何 locator reference，因此领域适配失败关闭。

页面错误仍为 `Engineering QA initial investigation output violates the domain contract`，但这次不是 Schema cardinality 或 Source fuse：
terminal receipt 证明 3 次 dispatch 均在 Gateway 完成；Source Result 是 `COMPLETE`、files 12、matches/items 0、无 failure code。

## Evidence and root cause

- Initial Prompt 原来只称 query 为“literal search expression”，没有说明它应是可能在所选证据中逐字出现的短 token，而非自然语言语义描述；
- Prompt 只说复用 exact locator，没有明确 typed item 同时暴露 human-readable `locator/path` 与 opaque `locator_reference`，模型复制了路径；
- Request/source allowlist 中出现路径是 capability disclosure，不会让该路径自动成为 READ authority；Broker/Application 正确拒绝未经先前
  Result 发出的 locator reference；
- run terminal audit：3 HTTP dispatch、1 次成功 TLS handshake、connection reuse 2、credential resolution 3、retry 0、Provider
  switch 0、Production Activation `NOT_EXECUTED`。

根因是 `local-implementation / systemic` 的 Prompt contract ambiguity，不是 mall/JWT 特例。任一自然语言问题、任一 Source Profile 都可能
把语义描述用于 literal search，或把 allowlisted path/human locator 误当成 opaque authority ID。

## Decision and disposition

Prompt identity 升级为 `engineering-qa-adaptive-investigation-prompt@3`。Initial 与 Verification Investigation 都明确：search query 是可能在
选定证据中逐字出现的短 literal token；READ/PARSE 只能复制当前允许的 typed retrieval item 中 exact opaque `locator_reference` ID，不能
使用其 human locator/path 或 allowlisted path；没有该 ID 时只能继续 SEARCH 或诚实 FINISH。

不把路径自动映射为 locator ID，不从 allowlist 合成 Result，不根据 mall、JWT、类名、文件名或题目写分支，也不放宽 Broker/Application
membership 校验。System Contract 已经规定模型只提 abstract proposal、Broker 编译 exact authority，本次只消除 Prompt 对既有字段的
歧义，因此处置到代码与测试，无需 System 文档或 ADR。

## Verification

Prompt regression 同时覆盖 Initial/Verification，冻结 `@3` identity、literal-token 指令、opaque ID 复制和 path 禁止语义；直接模块 9/9、
扩展 focused 69/69、docs 394/394、`py_compile` 与 `git diff --check` PASS。允许 AF_UNIX 的 full discovery 共 1112 项，其中 1107
PASS；唯一 4 FAIL + 1 ERROR 的 exact identity、类型和 marker 与 `FINDING-008-020` 历史 hold 相同，没有新增失败。由于 DeepSeek
implementation manifest 不包含该 role-specific Prompt source，现有 qualification 的 implementation digest 不因本修正改变；新 clean
candidate run 仍须绑定新的 Prompt digest。
