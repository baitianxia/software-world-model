---
id: ITER-007-INDEX
kind: iteration-index
status: rejected
authority: project-decision
owners: [product, project, engineering, quality]
depends_on: [PROJECT-GOVERNANCE-ITERATION-LIFECYCLE, ITER-007-PROPOSAL, ITER-007-READINESS, ITER-007-VERIFICATION, ITER-007-SLICE-001, ITER-007-SLICE-002, ITER-007-SLICE-003, ITER-007-RESULT-SLICE-001-STOP-DECISION]
code: []
tests: []
iteration: ITER-007
coding_input: false
---

# ITER-007：Java 源码实现语义与通用源码问答首个累积切片

## Status and authorization

`REJECTED / SLICE-001 PRODUCT FAIL / REDIRECTED WITHOUT ACCEPTANCE`。

用户曾明确采用“开发者开发、用户在代码冻结后现场提问”的验收方式，并只授权 `SLICE-001`。run-004 的技术链完成，
但正式 Web 无法回答已有足够知识的登录流程，也无法对不存在的下单功能形成正确的 Coverage 结论。因此：

1. **已闭合：** ITER-006 Acceptance、clean baseline `8f305ed…`，以及 Acceptance 现场暴露的全局清单误路由、静态示例和
   terminal 错误呈现限制；
2. **已闭合：** Java frontend artifact、Source Semantics/no-payload/功能发现/三调用模型 Contract，以及 JDK canonicalization、
   信息保持、信息越界和 legacy consistency Readiness Oracle；
3. **产品失败：** `ITER-007-RESULT-SLICE-001-STOP-DECISION` 将 run-004 密封为“技术 PASS / 产品 FAIL”；
4. **终止边界：** `SLICE-001` 为 blocked，`SLICE-002/003` 未授权且永久 not-executed。ITER-007 没有 Acceptance，不授权任何后续产品代码、Production Activation、提交或推送。

## Required inputs

- [Proposal](proposal.md)
- [Manifest](manifest.yaml)
- [Readiness Review](readiness-review.md)
- [Development Design](development-design/README.md)
- [Verification Matrix](verification-matrix.md)
- [Findings](findings/README.md)
- [Results](results/README.md)

## 开发顺序

1. `SLICE-001` 完成最小方法体语义和技术 Web 链，但早期产品 Gate 证伪了固定单方法问答协议；
2. 按 Proposal 的 stop/redirect 规则立即停止，不执行 hidden canary，不进入 Java 语义加固或 held-out 验证；
3. 失败证据路由到 `ROADMAP-M-002` Step 1，但路线图和 proposed ITER-008 均不构成编码授权。

本轮不把 README、配置、运行数据或多语言混进同一 Slice。它先回答一个更根本的问题：预先构建的软件世界模型能否在不读源码的
问答阶段，仅凭正式 Java 实现语义，定位业务功能并解释代码实现和调用逻辑。
