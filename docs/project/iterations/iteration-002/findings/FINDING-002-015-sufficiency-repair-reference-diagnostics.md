---
id: FINDING-002-015
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-002-SLICE-001, FINDING-002-014]
code: [src/software_world_model/ai_infrastructure/agentic_knowledge_strategy.py]
tests: [tests/test_agentic_knowledge_strategy.py]
iteration: ITER-002
classification: iteration-design
disposition: expose-exact-sufficiency-reference-diagnostics
target: ITER-002-SLICE-001
---

# FINDING-002-015：充分性修正缺少精确的引用和限制差异

## Observation

Strategy `2.0.196` 在产品任务中完成 127 次模型调用并进入充分性判断。第一次输出认为证据充分，但附带了一条并非从所选正式记录原文复制的限制；平台拒绝后，后两次输出又在 `supporting_reference_ids` 中重复同一引用，最终以 `Need sufficiency exhausted bounded contract retries` 结束。

## Evidence / reproduction

`var/product-generic-v196-suite205-exact-key-diagnostics/` 的运行数据库保存了三次充分性输出。第一次的错误详情列出了不受支持的限制，但修正动作回退为笼统的“复制有效编号”；第二、三次都重复 `knowledge_fact_73e7b08a9757a3757823530360d57cf0`，平台仅返回“引用无效”，没有指出字段和重复编号。该运行还包含一次 Provider 结果未知，因此无论契约是否收敛都不能作为最终验收证据。

## Impact

重复引用、越界引用、字段类型错误和未引用原文的限制是所有工程都可能出现的结构化输出缺陷。抽象错误让模型无法针对违规字段修正，提高重试次数只会重复无效输出；减少审核或接受重复项则会损害证据集合的完整性和可审计性。

## Classification rationale

问题位于通用充分性闭合集合契约及其修正反馈，不依赖产品任务所用语言、框架、文件或问题内容，因此归类为当前切片的 iteration-design 修订。

## Decision and disposition

平台保持原质量门槛，不自动去重、不接受越界编号，也不保留无原文支持的限制。校验失败必须给出具体字段，以及适用的 `duplicate_reference_ids`、`unknown_reference_ids`、非字符串位置或 `unsupported_limitations`，并提供对应修正动作。充分性提示明确要求引用数组内每个编号至多出现一次，并在契约修正时先读取精确差异。

重试仍然有界；边界用于防止无进展循环，不得成为删减证据、审核步骤或质量规则的理由。

## Verification after disposition

新增测试验证重复引用会被精确诊断并在下一次修正中收敛，以及无原文支持的限制会收到可执行的删除或逐字替换指令。Strategy 升级为 `2.0.197`；`2.0.196` 的能力资格和失败产品运行均不能继承到新 Strategy。
