---
id: FINDING-010-019
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-006, FINDING-010-018]
code: [src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_model_source.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: make-query-and-locator-intents-single-use-and-require-progress-aware-investigation-transitions
target: src/software_world_model/ai_infrastructure/engineering_question_model_source.py
---

# FINDING-010-019：模型重复读取已返回完整内容的 locator，触发 no-progress 熔断

## Observation

Prompt `@3` 修正后，candidate `91dffecc0fbe7512cf82baf92180213f43e5ca9d` 的第四次 `V-WEB-000` run 正确提交 literal
`JwtTokenUtil` search，取得 9 个 search-hit locator，并用 opaque `source_locator_…` 读取完整
`mall-security/.../JwtTokenUtil.java`。完整 READ Result 又携带一个指向同一路径的新 locator reference；模型先读取该新 reference，随后再次
读取前一个 full-read reference。两次 Result 的 `progress_digest` 都是
`sha256:ec38a383e35a6c6ed1425409c0313a744f5e20f9e89883265f3f54e4340b5b84`，Application 达到既定
`maximum_no_progress_steps=2` 后失败关闭。

页面形成 `FAILED_CLOSED` Result；Ledger 与 boundary Package 被密封用于审计，但 `answer_attempts=0`、`review_attempts=0`，没有把不完整
调查交付成答案。terminal receipt 证明本 run 只有 5 次 role dispatch，全部 Gateway `COMPLETED`，retry/provider switch 均为 0，Production
Activation `NOT_EXECUTED`。

## Evidence and root cause

- role sequence：Question Understanding → search `JwtTokenUtil` → read search-hit locator → read full-content locator → 重复 read 同一 full-content
  locator；
- Worker 前两次 full read 各读取 6,567 bytes，并产生相同 semantic progress digest；Source result identity/operation ID 不同，没有被误当成
  新观察；
- `FINDING-010-006` 的 deterministic no-progress fuse 按设计工作，拒绝了无界循环；
- Prompt `@3` 已区分 opaque ID 与 path，却没有说明 full-read Result 发出的新 locator 也不能用于重复读取同一 human path，也没有明确要求
  比较历史 `progress_digest` 和避免重复 query/locator intent。

根因是 `local-implementation / systemic` 的 progress-aware Prompt omission。它不依赖 mall、JWT 或特定路径；任何 READ/PARSE 返回可再次
引用的同路径 locator 时都可能出现。

## Decision and disposition

Prompt identity 升级为 `engineering-qa-adaptive-investigation-prompt@4`。Initial/Verification Investigation 都把 query 与 locator/path 视为
single-use 调查意图：不得重复先前 query 或 locator intent，不得再次 READ/PARSE 已返回 exact full content 的 human path，即使新 Result
又发出 locator reference；必须比较 typed Result 的 `progress_digest`，重复进展后改用不同 query/locator/evidence class 或诚实 FINISH。

不关闭既有 no-progress fuse、不把重复 Result 伪装成进展、不按工程/类/路径加分支，也不让 Application 自动替模型选择下一个 locator。
System Contract 的 progress/no-progress 与 Broker authority 语义原本正确，本次只补齐通用角色指令，因此处置到代码与测试。

## Verification

Prompt regression 同时冻结 Initial/Verification 的 `@4` identity、single-use query/locator、full-content path 禁止与 progress-digest 转移要求；
直接模块 9/9、扩展 focused 69/69、docs 395/395、`py_compile` 与 `git diff --check` PASS。允许 AF_UNIX 的 full discovery 共 1112 项，
其中 1107 PASS；唯一 4 FAIL + 1 ERROR 的 exact identity、类型和 marker 与 `FINDING-008-020` 历史 hold 相同，没有新增失败。由于该
Prompt 文件不属于 DeepSeek implementation manifest，现有 current qualification 保持 implementation-compatible，但新的 live run 必须使用
新的 Prompt-bound authorization。

用户授权的 20-call 总上限当前已消费 16 次，只剩 4 次；这不足以从新 Request 完成最少的 Understanding、Investigation、Answer、Review
链。因此本 Finding 的 live 重验不得在原授权下继续，必须等待新的明确调用额度，不能把剩余额度当成 retry 或越界使用。
