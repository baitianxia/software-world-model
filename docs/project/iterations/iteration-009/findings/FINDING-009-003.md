---
id: FINDING-009-003
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [product, architecture, application, quality]
depends_on: [ITER-009-SLICE-001, ITER-009-VERIFICATION]
code: [src/software_world_model/application_services/world_model_answering.py, src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, src/software_world_model/interface/world_model_browser_ui.py]
tests: [tests/test_world_model_answering.py, tests/test_world_model_answer_strategy.py, tests/test_world_model_browser.py]
iteration: ITER-009
classification: roadmap
disposition: redirect-to-engineering-question-answer-first
target: ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST
---

# FINDING-009-003：真实 Web 回答系统性地收敛为代码走读

## Observation

ITER-009 run-001 在同一个 product-owned 本机 Web 上执行了三条用户可见问题。技术链均返回页面结果，但用户的整体判断是回答像
“代码走读或者代码实现”，不是在回答工程问题。该现象同时出现在直接流程题、无符号等价改述和证据边界题，范围不是单一问题。

## Evidence

- “登录流程是怎样？”的正文从 `LoginService#authenticate(boolean)` 开始，逐项展开布尔分支、两次 `recordFailure()`、异常构造、
  `issueSession()` 和返回值；文件 digest 为
  `sha256:63e1cbb6d07310528babdf7080adfdd65de8098a2cdb7eb8a0e7b9e6e8f6178f`；
- “下单流程是怎样的？”交付了诚实 Limitation，但正文直接暴露“Java 方法实现候选”“查询返回 0 个候选”和“业务发现召回能力未经
  证实”；文件 digest 为 `sha256:2846bf0edc68ce01292d790834e9defb4b7574ece08524cc99785e3c683552e0`；
- 无符号问题“认证凭据失败和成功时，系统分别怎样处理？”仍逐项展开参数槽、`NOT` 分支、源顺序、静态直接调用、异常与返回；文件
  digest 为 `sha256:af82f7551f89942b85f88dd51c401be92858299307771f7472ba14bb50498d62`；
- 三条结果的独立 Reviewer 均把 `RELEVANCE_READABILITY` 判为 `APPROVE`。因此现行审核无法识别“事实正确但抽象层级和用户目标不
  匹配”的产品失败；
- 用户方向决定为 `REDIRECT`，收据是
  `codex-user-message:sha256:1b3270242962b8d099ac9166304dc6188be22054cfc2a685b2ade5616d4cc2f4`。

## Classification and scope

这是 systemic product/architecture direction finding。当前 Question Need 固定为 `implementation-answer`，可查询内容、Draft 完整性、
Review obligation 和页面呈现都围绕方法实现与调用事实组织。单独润色 Prompt 或隐藏几个术语不能改变这条共同主线；继续原
`SLICE-002` 只会把代码走读路径做得更稳定。

已有证据同时说明底层源码事实不是无价值：三条回答都有真实来源、独立 Review 和零提问期 Source access。需要改变的是用户问题、
证据和最终答案之间的产品协议，而不是丢弃已构建的只读、版本、Citation 和审核资产。

## Decision and disposition

ITER-009 立即按 `REDIRECT` 结束，不授权 `SLICE-002/003`。主要处置进入
`ROADMAP-CANDIDATE-ENGINEERING-QUESTION-ANSWER-FIRST`：后续方案默认先回答用户目标、流程、影响、用法或建议，代码只作为支持证据
或在用户明确询问实现细节时展开；Reviewer 必须检查是否直接回答、抽象层级、可用性、完整性和未知边界。

该 Candidate 是 planning-only，不构成新 Iteration、编码、Source 读取、Provider、Web、hidden 或 Production 授权。它若改变提问期
Source-off Owner 或 Evidence Package 边界，必须在新 Iteration 中先更新 owning System Contract/ADR，不能由本 Finding 静默重定义。
