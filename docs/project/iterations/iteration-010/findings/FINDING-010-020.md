---
id: FINDING-010-020
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-019]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: expose-and-enforce-fresh-ledger-and-single-use-locator-controls
target: src/software_world_model/application_services/engineering_question_answering.py
---

# FINDING-010-020：Prompt-only 没有可靠约束 fresh Ledger 消费与 full-content locator 单次使用

## Observation

用户把本次 DeepSeek 调用总上限提高到 28 后，clean candidate
`1f4e1b0deba025183333e61072cc342ee2bdc51e` 的第五次 `V-WEB-000` run 完成 Question Understanding、literal
`JwtTokenUtil` search、`JwtTokenUtil.java` READ 和 `JwtAuthenticationTokenFilter.java` READ。第五个角色输出随后同时出现两项错误：

- `basis_entry_ids` 引用了旧 Ledger entry，没有包含紧邻的最新 SOURCE_RESULT entry
  `ledger_entry_669302f1fe7c70b9a167f156067ace26`；
- `locator_reference` 选择了已经返回 `JwtTokenUtil.java` exact full content 的新 locator，准备重复读取同一 human path。

Application 在执行该 Source operation 前以
`investigation proposal must explicitly consume the immediately prior Ledger result` 失败关闭。页面没有形成 Draft 或 Review；terminal receipt
`sha256:bccdf1435a9d9bbed401f5d3ab1d6bf2bd6db9c3f232f6484b526d7b83059daa` 记录 5 次 role dispatch，全部
Gateway `COMPLETED`，retry/provider switch 为 0，TLS handshake 1 次、connection reuse 4 次，Production Activation
`NOT_EXECUTED`。连同此前 14 次 Web role dispatch 和 2 次 current qualification call，累计为 21/28。

## Evidence and root cause

角色实际收到的最新 Ledger entry 和 typed Result 都是正确且 exact 的，但 sealed role input 已增长到 73,102 bytes：

- 必须复制的 entry ID 只存在于 `evidence_ledger.entries[-1].entry_id` 深层位置；
- READ Result 仍按证据协议携带自己的 locator reference，外观上与 search-hit locator 相同；
- Prompt `@4` 用自然语言要求 prior-result、single-use path 和 progress-aware 转移，却没有给出一个小而明确的动态控制投影；
- Application 已验证 latest basis，但只在 Source Broker 阶段验证 locator 是否由当前 Ledger 发出，没有先把“search hit 且 path 尚未返回完整内容”
  冻结为本步可用集合。

因此 `FINDING-010-019` 的 Prompt 补强是必要但不充分的。根因属于 `local-implementation / systemic` 的 model-input affordance 与
application validation 缺口，不依赖 mall、JWT、类名、路径或特定问题。

## Decision and disposition

Initial/Verification Investigation 输入新增三个由 Application 计算并随当前 Ledger prefix 重新密封的控制字段：

- `required_basis_entry_id`：当前 Ledger 最后一个 entry 的唯一 ID；
- `eligible_locator_references`：只包含 search/line locator，并排除已经返回 full content 的 path；
- `consumed_full_content_paths`：已经完成 READ/PARSE 类完整观察的 canonical path。

Prompt identity 升级为 `engineering-qa-adaptive-investigation-prompt@5`，要求每个 action 的 `basis_entry_ids` 精确包含
`required_basis_entry_id`，READ/PARSE 只能从 `eligible_locator_references` 复制 opaque ID。Application 同时机械拒绝集合外 locator；证据 Result
仍保留完整 identity，未被重写或伪装，Source Broker 与 no-progress fuse 继续作为后续防线。

该变化没有让 Application 自动替模型选 operation，也没有按项目、问题、符号或 fixture 加分支；它只把既有通用不变量变成显式动态控制并
在 Owner 层执行。因此主要处置到代码与测试，无需改写 System Contract。

## Verification

新增回归覆盖 required latest basis、初始空 locator 集合、search 后 locator 可用、full-content READ 后同 path locator 被移除，以及模型仍提交
full-content locator 时的 Application 拒绝。包含 docs gate 的 focused 117/117、docs 397/397、`py_compile` 与 `git diff --check` PASS；允许
AF_UNIX 的 full discovery 共 1113 项，其中 1108 PASS，唯一 4 FAIL + 1 ERROR 的 identity、marker 与 Codex digest 精确保持
`FINDING-008-020` 历史 hold，没有新增失败。live 重验必须使用新的 clean candidate 与 Prompt-bound grant；旧 run 永久保持失败证据，不能由
本修复追溯改写。
