---
id: FINDING-002-014
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-002-SLICE-001, FINDING-002-013]
code: [src/software_world_model/ai_infrastructure/agentic_knowledge_strategy.py]
tests: [tests/test_agentic_knowledge_strategy.py]
iteration: ITER-002
classification: iteration-design
disposition: expose-exact-fact-review-key-set-diagnostics
target: ITER-002-SLICE-001
---

# FINDING-002-014：事实复核重试缺少精确的候选键差异

## Observation

Strategy `2.0.195` 通过六角色能力评估后执行产品任务。事实补丁新增两个候选键，同时按补丁契约保留两个未被替换的旧候选，因此实际审核集合有 17 条。模型连续八次只返回其中 15 个键并标记全部接受；平台正确拒绝不完整 ACCEPT，但最终以 `fact reviewer exhausted bounded contract retries` 停止。

## Evidence / reproduction

`var/product-generic-v195-suite205-final-focused-audits/` 的运行数据库记录 26 次完整模型调用。最后八次 `FACT_CANDIDATE_REVIEW` 均接受 `c1` 至 `c15` 的新集合但漏掉仍被平台保留的 `c8`、`c9`。授权状态包含全部 17 条候选；错误详情此前只说明事实复核决定无效，没有向契约修复明确给出已知、缺失、未知和重复键集合，模型因而重复同一不完整输出。失败发生在顺序分析之前，与全局调用上限和来源证据无关。

## Impact

候选补丁允许新增键并保留未替换的已验证事实，这是通用增量修复语义。若事实复核只收到抽象的“决定无效”，较大的候选集合容易在每次重试中遗漏相同键；提高重试次数只会延长无进展循环，降低次数又会截断可修复工作，两者都不能解决根因。

## Classification rationale

问题属于通用闭合集合契约和错误诊断，不依赖具体工程、源码、自然语言或问题形式，因此归类为当前切片的 iteration-design 修订。

## Decision and disposition

事实复核的 ACCEPT 语义在平台公共校验点直接要求每个已知候选键恰好出现一次。拒绝时的结构化详情必须给出 `known_candidate_keys`、`accepted_candidate_keys`、`missing_candidate_keys`、`unknown_candidate_keys` 和 `duplicate_candidate_keys`，并明确 ACCEPT 与 REJECT 的修复动作。复核提示要求契约重试先读取这些差异：有效但重叠的候选仍属于 grounding 集合，不能以精简为由遗漏；真正无效的候选必须改为 REJECT 并说明事实依据缺陷。

不通过自动补齐缺失键来伪造模型复核，也不删除旧事实或放宽 ACCEPT 完整性。重试仍有界，但每次都得到可执行的精确修复信息。

## Verification after disposition

新增单元测试验证不完整 ACCEPT 会失败关闭，并精确返回漏掉的键和修复动作。Strategy 升级为 `2.0.196`；`2.0.195` 能力资格和未完成的产品结果不能继承。
