---
id: FINDING-008-017
kind: implementation-finding
status: superseded
authority: development-evidence
owners: [ai, engineering, quality, project]
depends_on: [ITER-008-SLICE-001, FINDING-008-016, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
code: [src/software_world_model/application_services/bounded_world_model_investigation.py, src/software_world_model/ai_infrastructure/deepseek_chat_adapter.py, validation/structure_world_model_iteration_008/capability/live_runner.py]
tests: [tests/test_bounded_world_model_investigation.py, tests/test_deepseek_chat_adapter.py, tests/test_iteration_008_capability_harness.py]
iteration: ITER-008
classification: iteration-design
disposition: stop-deepseek-qualification-and-require-explicit-model-or-protocol-redirect
target: ITER-008-SLICE-001
superseded_by: FINDING-008-018
---

# FINDING-008-017：run-009 最终资格仍违反 path semantic intent

## Observation

temperature-zero protocol repair 的 clean candidate `5d2bce381e9c9495571c148a69c3fb43ee3f6dc8`（tree
`52f6d7b9bfe6da58055f75801b9a2b989761f28a`）先完成 DeepSeek Conformance run-009。preflight/authorization digest 为
`sha256:7408d2ee7f49d4f3ff83b93321510e38003d9da4436af77f1bb0d2a485860d4e` /
`sha256:650835ddc1cf2d62250013a1526fc34568e2da473a4561c1b4393f333d02651a`；Adapter
`deepseek-chat-completions-no-tools@2`、fixture `1.0.1` 恰好执行 2 次 request 并 12/12 PASS。result/terminal digest 为
`sha256:c2b999fb4c313e0913a49284ddb3783672761fd6155924f9a7154a0d6298db76` /
`sha256:197a15e21fa90d2e001db8fe0cdb1357c2abf0537adbf29cf7fd64a90bb873c1`，wire 已证明 numeric temperature 0；模型 identity 仅为
`deepseek-v4-pro`，tokens 为 377/77，usage 完整。

同候选 Capability run-009 绑定 freeze
`sha256:d436a104be64ef22caf8f499c950863b36cecf12cede1fb4c624b14e1a6eec35` 与 single-use authorization
`sha256:82db651b002ef2d02df2c587cb93cf3953460eb93dfa2eb8a8ceb9ab3c110a9f`。前 7 个 required Case 全部取得独立 Review PASS；第 8 个
`WM-JSS-I8-ALL-SIMPLE-PATHS-008:call-3` Provider response 完成后，compiler 以 `INVALID_ARGUMENT / path intent requires two
exact prior Result refs` 失败关闭。failure/terminal digest 为
`sha256:beadc9bbca1544bebcf29620a13b98128e65bdcc9c72364515c1fc2a38e763fb` /
`sha256:99fc7923db8696f4a3a3b81ac5960459b81698737597a2a0325d82a28e4f422c`。没有 Capability Qualification、retry、hidden canary
disclosure、正式 Web 或 Production Activation。

## Evidence and root cause

8 个 per-Case SQLite records 证明本次实际 18 个 Provider request 全部到达 `COMPLETED` revision，response identity 均为
`deepseek-v4-pro`、usage 均完整，总 tokens 为 46,946/1,021。failure document 的 `completed_provider_request_count=15` 只统计 7 个
已密封 Case 的 request；terminal 的 exact provider request count 和第 8 个 runtime record 均为 18，不代表 3 次 outcome unknown。

前 7 个 PASS 覆盖 first candidates、zero candidates、N candidates、result-driven batch、四步 declared inventory、direct
neighborhood 和 path exists。失败 Case 的三次 normalized semantic intent 为：

1. `implementation_candidates`；
2. `all_simple_paths`，`relation_intent=null`，由 `three_candidates` 中前两个 Ref 合法编译；
3. `all_simple_paths`，但额外返回 `relation_intent=BOTH_CALLS`。

第三步的 sealed `method_batch_complete` Result 实际含 3 个 exact `JAVA_METHOD` Ref。compiler 的错误消息合并了“relation intent 必须为
null”与“至少两个 Ref”两个前置条件；本次真正失败条件是前者，不是 Ref 缺失。Path operation 的 predicate、Ref 顺序和 bounds 由平台
编译，`BOTH_CALLS` 只属于 direct-neighborhood relation intent；将它静默丢弃可能把双向关系意图改写为有向 path，不能视为无损
canonicalization。compiler 正确失败关闭。

Conformance、temperature=0、TLS、模型 identity 和 usage 均已单独证明，故本次不是 transport 或未冻结采样配置问题。一个完整 live run
仍不能证明 temperature 变化对前 7 项 PASS 的因果作用；它只消除了 run-008 的配置歧义。剩余事实是该模型在严格、无 retry 的 closed
semantic-intent 协议上仍不能达到 18/18。

## Impact and classification

产品 bounded investigation、Application authority compiler、Prompt/suite/Oracle、18/18 threshold、41-call 上限和 no-retry 都没有新
缺陷证据；放宽 relation field 或 threshold 会改变已冻结的正确性边界。影响是 ITER-008 当前 DeepSeek qualification path 已耗尽预提交的
最终尝试，主分类为 `iteration-design`，目标为 `ITER-008-SLICE-001`。正式 runtime 仍是 Ark，且没有合格的 bounded Provider 可以进入
V-WEB-001 或 hidden canary。

## Decision and disposition

执行 `FINDING-008-016` 的停止规则：不 retry run-009，不创建 run-010，不继续改 Prompt、Provider 参数、compiler、suite、Oracle 或
threshold，也不把前 7 项 PASS 推导成部分资格。DeepSeek `@2` 保留为已通过 Conformance、未通过 bounded Capability 的候选；所有授权均
已消费。

继续 SLICE-001 live Product Gate 前必须有新的显式 redirect decision，并选择其一：恢复 Ark 对 Python/OpenSSL 的 verified TLS 路径后从
全新资格开始；接入另一个具有独立 Adapter/Conformance 的模型；或重新设计比自由 JSON semantic intent 更强的 constrained transition
协议并重新审查 System/Iteration 边界。上述任一选择都不是当前失败 Result 可自动授权的实现步骤。

## Verification after disposition

- 7 份 independent review 均为 PASS，失败 Case 没有被密封成 verdict；18 个 call record 均为 `COMPLETED` 且 usage 完整。
- run-009 preflight、authorization、Conformance、Capability freeze/failure/terminal 的目录边界和 0600 authority records 已复核；
  configured secret 不在 run-009 artifacts 中，credential 与 raw HTTP envelope 未持久化；资格所需的 authorized input manifest 与
  normalized model output 只保存在受保护的本机 Result 边界。
- 本次只形成资格失败证据；Production Activation 保持 `NOT_EXECUTED`。

## Supersession

run-009 的调用、失败位置和未形成 Qualification 等事实继续有效；但“非适用 relation slot 不能丢弃、因此停止等待 redirect”的设计判断，
已由用户消息 `codex-user-message:sha256:375246d919e8541021acd7b319f13d5af928794ff23a022ae01a82531a09a8e2`
明确重定向，并由 [FINDING-008-018](FINDING-008-018.md) 取代。新决定把 `operation` 作为 semantic-intent discriminant，
由 Application 只解释所选 operation 拥有的 slot；这不是 retry run-009，也不改变其历史 Result。
