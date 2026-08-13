---
id: ITER-006-RESULTS-INDEX
kind: iteration-result-index
status: completed
authority: evidence
owners: [project, quality]
depends_on: [ITER-006-VERIFICATION, ITER-006-RESULT-IMPLEMENTATION-VERIFICATION, ITER-006-RESULT-LIVE-CANDIDATE-FREEZE, ITER-006-RESULT-LIVE-RUN-003, ITER-006-RESULT-JAVA-CAPABILITY-CANDIDATE-FREEZE, ITER-006-RESULT-JAVA-CAPABILITY-RUN-002, ITER-006-RESULT-PRODUCT-CANDIDATE-FREEZE-RUN-007, ITER-006-RESULT-LIVE-RUN-007, ITER-006-RESULT-PRODUCT-CANDIDATE-FREEZE-RUN-008, ITER-006-RESULT-LIVE-RUN-008, ITER-006-RESULT-ACCEPTANCE]
code: []
tests: []
iteration: ITER-006
---

# Iteration 006 Results

- [Java 静态调用实现验证](implementation-verification.md) — frozen R1/R2/R3、独立 declaration/call/Evidence Oracle、原子
  update、Source-off 新进程、Behavior/Product/Citation、零 Provider 浏览器状态与 819 项完整回归 PASS；这是 live run 前的
  implementation-only 证据。
- [Live Candidate Freeze](live-candidate-freeze.md) — run-003 随机 Java source closure、六题 suite、三路协议、独立 evaluator、
  role package 与 disclosure boundary 冻结并通过 zero-provider Gate；早先泛化授权被拒绝的历史证据保留。
- [Live run-003](live-run-003.md) — 明确授权后的三路执行：Direct 6/6、Codex 6/6、World Model 4/6；两个 generic planning
  case 因继承 qualification 不包含 Java operation vocabulary 而在 Provider 前失败，冻结 evaluator 又暴露失败-terminal crash。
- [Java Capability Candidate Freeze](java-capability-candidate-freeze.md) — 独立 Java proposal 1.1.0、Prompt @4、vocabulary @2、
  八题 closed suite/evaluator、exact Gateway policy 与授权门禁实现；835/835 回归和 zero-provider preflight PASS，等待一份绑定
  exact freeze 的新 Ark capability 授权。
- [Java Capability run-002](java-capability-run-002.md) — 用户 exact 单次授权已消费；八题 8/8 PASS、恰好 8 个唯一 Ark request、
  无 retry，形成 `PASS_VALID` qualification；未发送产品问题、Java 源码或 Evidence payload，未创建 Codex task。
- [Product Candidate Freeze run-007](product-candidate-freeze-run-007.md) — 绑定新 qualification 的六题 suite、修复后 evaluator、三路
  protocol 与 role package 重新冻结；55/55、18/18、835/835、docs、pre-dispatch/pre-listen 均 PASS，等待独立三路披露授权。
- [Live run-007](live-run-007.md) — exact 授权后三路执行：Direct/Codex 各 6/6；World Model 六次内部 Ark call 均完成，但 Java
  baseline digest 与授权 wrapper 外层 digest 同名冲突，6/6 在 `ROLE_POSTCONDITION` fail-closed，comparison report 为 FAIL。
- [Product Candidate Freeze run-008](product-candidate-freeze-run-008.md) — 排除 wrapper 隐藏 digest input 的最小修复重新冻结；
  56/56 focused、18/18 Answer package、836/836 full regression、docs、pre-dispatch/pre-listen 均 PASS，freeze 时外部调用为 0；
  后续 exact 授权与 live PASS 由独立 run-008 Result 保存。
- [Live run-008](live-run-008.md) — 用户 exact 单次授权后三路执行：Direct/Codex/World Model 各 6/6，controller retry 0；
  comparison `sha256:857085c4…` PASS、blocker 0、无 filter/interpolation；Source/Evidence payload/Oracle access 为 0，授权已消费。
- [Final Acceptance](acceptance.md) — 用户接受 run-008 受保护 candidate stage 已证明的 Java static-call `EVALUATION_ONLY`
  窄范围；明确不接受当前评测页为正式最终 Web Chat，也不扩张到系统用途、架构意图、总体介绍或通用源码问答。

本目录只记录实际发生的证据和限制。capability qualification 不是 Product Validation，candidate freeze 也不是 live PASS；
run-003/run-007 FAIL、授权消费和最终交互限制永久保留，没有被 Acceptance 覆盖。Production Activation 未执行。
