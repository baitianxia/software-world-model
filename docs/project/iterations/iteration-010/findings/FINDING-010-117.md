---
id: FINDING-010-117
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai, security, quality]
depends_on: [FINDING-010-113, FINDING-010-115, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: require-complete-claim-assessments-and-json-only-role-output
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-117：Reviewer 必须结构化承载正向 Claim 判断

## Root cause and decision

run-037 Turn 1 的 Reviewer 三次把它自己判定为“已确认、完全支持、没有 defect”的 Claim 编码成 `FINDINGS`。旧 Reviewer output 只有
top-level decision 与负向 Finding；正向 Claim 判断没有字段，Application 只能验证 `APPROVED⇔empty Findings` 的形状，不能验证每个
claim-index 的正负判断与 Finding 是否一致。继续提高 review 次数只会复制同一个矛盾。

Reviewer input 升级为 `ENGINEERING_AGENT_REVIEW_INPUT@2`，显式投影 exact ordered `claim_indices` 和一致性规则；Reviewer output 升级为
`engineering-agent-independent-review-proposal@2`，要求对每个 Claim 精确返回一个 `SUPPORTED` 或 `DEFECT` assessment。decoder 重算：

- assessment index 必须按 exact Draft Claim 顺序完整且无遗漏；
- claim-bound Finding 只能绑定 `DEFECT` assessment；每个 `DEFECT` 必须至少有一个绑定 Finding；
- `SUPPORTED` Claim 不得有 Finding；`APPROVED` 必须全部 `SUPPORTED` 且 Findings 为空；
- global completeness/relevance Finding 仍可使用 `claim_index=null`，不把所有缺陷错误压到某个 Claim。

Primary/Reviewer 共享 strategy/prompt 升级为 `conversational-engineering-agent@3` /
`conversational-engineering-agent-no-tools-prompt@3`。两个 role 都被明确要求首个非空白字符为 `{`、最后一个为 `}`，禁止 JSON 外的分析、
叙述或 Markdown fence。run-037 Ark 长前言仍保持历史 `STRUCTURED_OUTPUT_INVALID`；实现没有增加任意 JSON substring 提取、没有删除前言后
追认对象，也没有放宽 closed schema。

## Verification and disposition

聚焦测试证明完整正向 assessments 可 APPROVED；“SUPPORTED assessment + claim Finding”、缺失 assessment、DEFECT 无 Finding、未知 Claim
和额外字段均被拒绝；合法 DEFECT + Finding 保持可用。与 `FINDING-010-116` 联合的 Model/Agent 组合 27/27、七组相邻组合 43/43 和
`py_compile` 均 PASS。

该输出/prompt identity 变化使 `FINDING-010-114` 的两份 Conformance 和 run-037 artifact 立即成为历史证据，不能资格化 successor。
下一外部 Gate 是新 exact commit/tree 上的 fresh Ark/DeepSeek Conformance；本 Finding 不授权外部调用、Browser 或 Production Activation。
