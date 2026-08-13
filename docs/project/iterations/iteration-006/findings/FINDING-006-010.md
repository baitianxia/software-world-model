---
id: FINDING-006-010
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-006-SLICE-001, SYS-QUALITY-ACCEPTANCE]
code: [src/software_world_model/ai_infrastructure/world_model_answer_strategy.py, src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py]
tests: [tests/test_iteration_003_v009.py, tests/test_world_model_answer_strategy.py, tests]
iteration: ITER-006
classification: local-implementation
disposition: preserve-qualified-legacy-artifact-and-isolate-new-version
target: src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py
---

# FINDING-006-010：已资格化旧 Strategy 的文件字节不能承载新版本实现

## Observation and evidence

Java 1.1.0 初版虽保留了 Maven 1.0.2 的 Strategy、Prompt 与 output contract 逻辑 digest，却把新 contract 类和 Java Prompt
追加在原 `world_model_answer_strategy.py` 文件内。完整回归中的四个 ITER-003 V-009 case 因冻结的
`implementation_file_digest` 漂移而失败。这不是旧测试过严：ITER-003 qualification 精确绑定的就是该文件字节，逻辑 digest
相同不能替代原 artifact identity。

## Classification and disposition

旧模块已恢复为原始 SHA-256
`520580b24f46a94439602e987268b24575746383b5e9e0c8e6845189664f2ebc`，与 Git 基线逐字节相同。Java 1.1.0 及 profile
binding 被迁入独立 `versioned_world_model_answer_strategy.py`；默认 Maven contract 仍委托旧 1.0.2 逻辑和 digest，新 Java
contract 则独立密封 Strategy/Prompt/vocabulary/operation set。

新增回归确认 profile binding 返回独立 exact Strategy，旧 V-009 四个失败项恢复 PASS；最终完整套件 835/835 PASS。该发现不
改变系统语义，长期“关键输入变化必须重新验证”已由 `SYS-QUALITY-ACCEPTANCE` 规定，故处置到代码与兼容测试。
