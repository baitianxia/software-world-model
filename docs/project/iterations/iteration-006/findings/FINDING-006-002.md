---
id: FINDING-006-002
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-006-SLICE-001, SYS-CONTRACT-KNOWLEDGE-JAVA-STATIC-CALL-MODEL]
code: [src/software_world_model/application_services/java_static_call.py]
tests: [tests/test_java_static_call.py]
iteration: ITER-006
classification: local-implementation
disposition: reject-zero-target-in-scope-invocations
target: src/software_world_model/application_services/java_static_call.py
---

# FINDING-006-002：in-scope 调用的 zero-target resolution 被静默跳过

## Observation

Java evaluator 已把无 receiver 或显式 in-scope type receiver 的 invocation 归到确定目标类型后，若该类型中不存在相同
name + arity 的方法，初始实现直接 `continue`。Candidate 因而仍可发布 COMPLETE，并让后续 View 把该 invocation 当作“没有
CALLS 边”；这与同一路径的多目标歧义拒绝不对称。

## Evidence

- 把 R1 的 `Audit.record(input)` 改为 `missing(input)`，同时重建 source digest 与 exact tree Evidence；修正前 evaluator
  会继续形成完整 Candidate，修正后稳定返回 `JAVA_CALL_TARGET_UNRESOLVED`；
- `audit.record(input)` 的变量 receiver 返回 `JAVA_CALL_RECEIVER_UNSUPPORTED`，同名同 arity overload 返回
  `JAVA_CALL_TARGET_AMBIGUOUS`；
- truncated source、symlink source entry、source digest tamper 和 tree metadata tamper 均各自失败关闭；
- Java evaluator/Behavior 测试与最终 819 项完整回归 PASS。

## Impact and classification

当前 Java Static Call Contract 已要求潜在内部调用的 0/N resolution 都拒绝完整 Candidate，且零边结论只能来自完成分类的
COMPLETE Coverage。问题没有改变契约，而是 evaluator 漏掉既有 zero-target 分支，分类为 `local-implementation`。

## Decision and disposition

一旦 receiver 已归一为当前类型或唯一 in-scope type，name + arity 的候选数必须严格为 1：0 个返回
`JAVA_CALL_TARGET_UNRESOLVED`，多个返回 `JAVA_CALL_TARGET_AMBIGUOUS`。显式变量/表达式 receiver 继续以
`JAVA_CALL_RECEIVER_UNSUPPORTED` 拒绝，不尝试变量类型推断。

实现和四类直接负向回归已经处置本 Finding；System 文档无需改变，因为修复恢复了现有 fail-closed 与 COMPLETE 语义。
