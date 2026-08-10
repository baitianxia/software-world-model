---
id: ITER-002-RESULT-PRODUCT
kind: iteration-result
status: pass
authority: evidence
owners: [product, quality]
depends_on: [ITER-002-VERIFICATION, FINDING-002-024, FINDING-002-027, FINDING-002-028, FINDING-002-029, FINDING-002-030]
code: [validation/product_holdout_iteration_002]
tests: [tests/test_product_holdout_evidence_answer.py, tests/test_product_holdout_manifest.py]
iteration: ITER-002
---

# ITER-002 Result：Product Validation

## Claim and scope

该结果证明 Evidence-first Strategy `1.0.0` 在两个冻结陌生 Java 工程的六个真实源码问题上，答案正确、完整、可读且引用实际源码。Oracle 由 Codex 独立阅读冻结源码后判断，不使用火山生成的 Oracle，也不把同一模型的直接答案当裁判。它只支持本机体验，不构成生产启用。

## Exact inputs / baseline

- Suite：`product-unseen-repositories-2026-08-07@2.0.5`，digest `sha256:19b955badc095cf4fb6d8b20f3b2d02aec228c1f32b1ad26f13198e048474f25`。
- 工程：冻结的 `transmittable-thread-local` 与 `poi-tl`，共六个任务、33 个验收维度。
- Strategy：`evidence-first-software-answer@1.0.0`，implementation digest `sha256:319f9d89cc4b4c23531d9db6766d35bff37978e84d7f6a50a306602addfc92bd`。
- Capability Qualification：`sha256:3d529903152c6485372dbfe6671d3adffab72496e4c3c6a23a18a6766abacd54`。
- 原始本机证据：系统路径位于 `var/evidence-product-v8/path-results/`，六个答案对及独立 Review 位于 `var/evidence-product-v8/evidence/`；直接源码基线复用 `var/evidence-product-v1/path-results/`。

## Execution and evidence

六个任务分别覆盖线程上下文生命周期、执行器包装选择、定时任务移除回归、文档两阶段渲染、定制策略扩展和远程资源超时变化。系统针对每题执行通用问题理解、只读检索、Evidence Packet、自然答案和独立审核；每题实际使用 3—6 次模型调用和 3—7 次来源动作，没有因调用次数减少检索、引用或审核。

Codex 对每个系统答案、直接源码答案、冻结问题、源码证据和 33 个验收维度逐项复核。六份 Review 均将直接路径与系统路径标记为 `CORRECT_COMPLETE`；系统答案没有重大错误、关键遗漏、机械证明转储或未经源码支持的目的解释。

## Result, failures and limitations

Product Validation 结论为 PASS：

- 系统路径正确率/完整率：`1.000 / 1.000`。
- 直接源码基线正确率/完整率：`1.000 / 1.000`。
- 重大错误：`0`。
- Attestation ID：`product_validation_dc02535f3c837cc0b469e14f51fef93d`。
- Attestation digest：`sha256:ce9cb1ee93e63c05a0e050c8cb0410643e6a7090cbe6f83c0bfc212075b5f5c4`。
- 有效至：`2026-08-16T19:19:40.502387+00:00`。

开发过程中旧正式知识路径的多次失败仍保留为 ADR-013 的根因证据，但没有被计入新路径 PASS。当前套件仅冻结两个 Java 工程，不代表所有语言和所有问题已经穷尽；通用性主张来自统一协议、无定制分支的实现与通用能力反例，而不是样本数量。

## Browser experience

`local-browser` Activation `activation_decision_af90ea83192f441eb7140a011340221c` 已绑定上述资格与产品证明。真实页面连接 `poi-tl@58fdb6c7d9db` 后，询问 `ByteUtils.getUrlStream` 的超时及失败传播；答案正确说明连接/读取超时均为 15000 毫秒、`getUrlStream` 抛出 `IOException`、`getUrlByteArray` 记录后返回 `null`、`toByteArray` 自身失败与关闭流边界，并显示固定版本复核、两条事实和两处源码位置。页面未暴露内部审核模板或降级答案。

## Findings and system write-back

架构耦合、审核顺序/意图、草稿语义修正、相关性/可读性和角色契约恢复分别登记为 `FINDING-002-024`、`FINDING-002-027`—`FINDING-002-030`，已处置到 ADR-013、Evidence Answering Contract、能力套件、代码与测试。没有未处置 Finding。

## Validity / supersession

Strategy、资格、模型、Adapter、配置、源码、Suite 或有效期变化即失效，必须重新执行对应 Gate。Production Activation 未执行，不能从本结果推导。
