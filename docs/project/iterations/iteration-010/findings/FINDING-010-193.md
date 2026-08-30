---
id: FINDING-010-193
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [FINDING-010-170, FINDING-010-191, FINDING-010-192, ITER-010-PDR-012]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: separate-audit-retention-from-user-visible-material-boundaries
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-193：审计保留的 Boundary 被误当作用户答案必须披露的当前 Limitation

## Observation

继续审计 `run-076-mvp-experience` 的 pre-delivery Draft 和完整 Work State 后发现，后续 `SOURCE_READ` 已成功取得
`UmsAdminServiceImpl` full content，Draft 仍把更早的 `SOURCE_SEARCH_FILE_LIMIT_REACHED` 写入答案，并把它保留在 Hypothesis 中。
Draft 还向用户报告 World Model 全局清单的 `INCOMPLETE_IMPLEMENTATION_METHODS:559` 与 `UNSUPPORTED_EXCLUDED_UNITS:866`；这些数字没有
说明用户要求的 HTTP 入口、关系变更、缓存调用或仍未知时序中的任何具体缺口。

Evidence Ledger 与 Package 保留这些 Boundary/Audit 记录是正确的，但保留并不要求把每个记录作为 user-visible Limitation。该 Draft 已因
cross-disposition Claim 被 Application 更早拒绝，Reviewer 尚未运行；如果 repair 只纠正引用分区，以上无关或已由后续 SUPPORT 闭合的诊断
仍可能留在正文并降低相关性。

## Evidence and first divergence

- `agent_observation_812d5d5cc8554fadbe8186a1a91b9b53` 记录 `UmsAdminServiceImpl` Search 的 PARTIAL Boundary；随后
  `agent_observation_723c8af99cb546939dc2865e3f6ec9ab` 已由 full READ 提供该资源的完整当前 Source SUPPORT。
- 最终 Work State 的 `open_items=[]`，但 Hypothesis 仍称 Search truncated；Draft 第 4 节和 Claim 11 再次披露该采集诊断。
- Draft Claim 10 及正文披露 559/866 全局 inventory counts，却没有把它们绑定到仍未回答的 material requirement。用户明确要求未知时序，
  因此 transaction/consumer path 的具体 Evidence boundary 相关；全局方法计数并不能替代该具体边界。
- first divergence 位于 Primary 的 Work State/Draft boundary relevance 选择。正式 Ledger/Package 不应删除历史审计证据；Application 的
  cross-disposition guard 也已正确工作。尚未运行的 fresh Reviewer 是必须独立阻断无关披露的后继 guard。

## Classification and disposition

这是 `system-contract / systemic` Finding，不按 mall、Java、具体 failure code、数字、问题或自然语言关键词特判。

1. Ledger/Package audit retention 与 user-visible answer disclosure 分离。Primary 只有在 Boundary 仍使 current User Message 的 material
   requirement 未解决，或用户明确询问该诊断本身时，才把它写入 Draft。
2. 早期 partial/truncated Search、budget、Provider 或其他 acquisition diagnostic 在后续 current SUPPORT 已闭合同一 material need 时只作
   audit；Work State 必须删除或纠正已解决 Hypothesis/Open Item，不能把它保留成答案 caveat。
3. global inventory count、Profile-wide coverage metric 只有在其实际限制用户要求的具体 conclusion 时才进入答案；具体未知必须报告具体
   Evidence boundary，不能用全局数字制造完整性免责声明。
4. Primary 与 Reviewer 获得对称 sealed policy/prompt。Reviewer 对无关或已解决诊断返回 `requires_evidence=false` 的 relevance Finding，
   因为删除这些内容不损失任何已支持的 requested conclusion。Application 不按 failure code 或关键词自动删改模型正文。
5. 模型边界直接 `28/28` PASS，含 Tool、Agent、Conversation、Browser、Candidate 和 Session 的相邻七模块 `91/91` PASS，外部
   dispatch 0；fresh Browser successor 仍须验证，不能把 Prompt/policy 测试称为答案质量 PASS 或 MVP。
