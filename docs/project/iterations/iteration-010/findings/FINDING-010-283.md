---
id: FINDING-010-283
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [knowledge, quality]
depends_on: [FINDING-010-282]
code: [src/software_world_model/knowledge_engine/capability_cognition.py]
tests: [tests/test_capability_cognition.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: code-tests-only-no-system-contract-change
target: src/software_world_model/knowledge_engine/capability_cognition.py
---

# FINDING-010-283：宽 cognition 页面方法候选 cohort

提交 `f21bd99` 修正宽查询首屏的方法候选提升：仅在相关 METHOD 少于两个时
进行稳定 cohort promotion；方法已充足时保持原序。exact snapshot 的 broad
查询均保留两个 METHOD，method-heavy 查询与无 cohort 基线一致；相关定向测试
通过。该变化不修改系统契约、协议、提示词、Provider 或预算，故按 code/tests-only
处置；fresh C1 运行证据仍待补齐。
