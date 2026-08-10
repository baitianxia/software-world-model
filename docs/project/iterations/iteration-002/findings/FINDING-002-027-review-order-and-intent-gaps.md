---
id: FINDING-002-027
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-002-SLICE-001, FINDING-002-026]
code: [src/software_world_model/ai_infrastructure/evidence_answer_strategy.py]
tests: [validation/evidence_answer_capability_iteration_002/suite.json]
iteration: ITER-002
classification: verification
disposition: add-order-and-intent-review-counterexamples
target: ITER-002-VERIFICATION
---

# FINDING-002-027：聚合审核漏过了顺序颠倒和未证实意图

## Observation

第二轮陌生工程验证中，一份答案把源码中发生在 `replay` 和底层任务之前的引用清除说成“执行后”；另一份答案从“普通阶段跳过、重载后单独执行”的控制流推导了源码未说明的预防性设计动机。两份答案均被模型审核错误批准。

## Impact

这是跨语言、框架和题型的证据审核缺口：整体事实看似正确时，审核容易忽略单个时间词，或把观察到的机制当成设计意图。两类问题都会形成证据不蕴含的最终陈述。

## Decision and disposition

通用审核提示明确要求逐个核对 before/after/finally 等时间关系，并禁止用执行顺序或结构变化单独证明目的、动机或“为了避免”的因果解释。能力套件增加“颠倒执行顺序”和“虚构设计目的”两个独立反例；只有二者均被退回定向重写，当前实现才可取得资格。
