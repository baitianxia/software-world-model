---
id: FINDING-002-031
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [architecture, product, quality]
depends_on: [ITER-002-SLICE-001]
code: [src/software_world_model/application_services/evidence_answer.py, src/software_world_model/interface/http_api.py]
tests: [tests/test_product_holdout_evidence_answer.py, tests/test_browser_chat_interface.py]
iteration: ITER-002
classification: verification
disposition: constrained-iteration-acceptance
target: ITER-002-VERIFICATION
---

# FINDING-002-031：Evidence-first 问答通过不等于软件世界模型通过

## Observation

本轮产品验证证明 Evidence-first 路径能在六个冻结问题上追平直接源码调查，但该浏览器主路径直接读取源码 Evidence Packet，不读取已发布 Snapshot。异步知识沉淀未实现，Structure View 未成为正式能力，也没有验证跨版本稳定身份、删除关系替换或无人提问时更新。

## Evidence / reproduction

V-006 的系统路径与直接路径均为 `1.000 / 1.000`，只证明本机同步问答质量。V-008 明确把后台沉淀排除在本轮实现之外；当前 HTTP 路径在 Evidence-first 激活时不经过 Knowledge Update、Publication、Snapshot 或 View。

进一步反例审查发现：当前 Fact 没有受引用完整性保护的目标 Entity；Entity ID 实现包含 revision-bound Context/Evidence；Publisher 会无条件继承旧 Snapshot 成员。这些事实尚未进入本轮产品场景，不能被现有 PASS 覆盖。

## Impact

若把 ITER-002 接受为“软件世界模型完成”，会把源码 Agent 的局部能力误记为世界模型能力，并允许后续开发跳过最关键的数据模型和快照语义验证。

## Classification rationale

本发现首先改变本轮结果可支持的主张，因此归类为 Verification。后续架构与实现变化必须进入独立 Iteration，不能追写进本轮。

## Decision and disposition

在 Verification Matrix 增加 V-010，并把最终 Acceptance 限定为本机 Evidence-first 同步问答实验。Snapshot-first 世界模型问答、独立更新、Structure View、稳定身份和 replacement 删除语义全部记录为 NOT EVALUATED。

## Verification after disposition

最终 Acceptance 必须逐项列出上述边界，ITER-002 状态完成后不得再作为编码输入；任何软件世界模型完成声明都需要新的冻结场景和独立产品验证。
