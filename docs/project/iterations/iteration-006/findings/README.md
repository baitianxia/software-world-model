---
id: ITER-006-FINDINGS
kind: iteration-findings-index
status: dispositioned
authority: development-evidence
owners: [engineering, architecture]
depends_on: [PROJECT-GOVERNANCE-IMPLEMENTATION-FEEDBACK, ITER-006-PROPOSAL]
code: []
tests: []
iteration: ITER-006
---

# Iteration 006 Findings

本轮登记十三条实现发现，均已处置：

- [FINDING-006-001](FINDING-006-001.md)：通用 graph enum 扩展会经默认参数隐式扩大旧 Maven Coverage；默认值与 Admission
  均改为 Profile-specific explicit set，并增加直接兼容回归。
- [FINDING-006-002](FINDING-006-002.md)：已解析到 in-scope type 的 zero-target invocation 不能静默变成“无边”；改为
  `JAVA_CALL_TARGET_UNRESOLVED` 整体拒绝，并闭合 receiver/歧义/截断/symlink 负向回归。
- [FINDING-006-003](FINDING-006-003.md)：集成 harness 固定 R1/R2/R3 commit/tree identity，并在 DB/repository unmount 后
  从真实新进程执行 Source-off CLI，同时核对权威计数不变。
- [FINDING-006-004](FINDING-006-004.md)：Profile 切换必须同时切换 Coverage/examples 与 Result state；页面不再并置 Maven
  选择和旧 Java answer，也不向辅助技术常驻另一 Profile 的 copy。
- [FINDING-006-005](FINDING-006-005.md)：held-out 问题必须使用正式产品已声明词汇；run-001 的同义词假失败被保留，只有
  deterministic product probe 全题通过的新随机 run 才可授权。
- [FINDING-006-006](FINDING-006-006.md)：受限 sandbox 的 AF_UNIX 拒绝不能伪装为回归失败或跳过；run-002 保留，run-003
  在允许本机 socket、仍为 zero-provider 的环境重新生成并取得 819/819 PASS。
- [FINDING-006-007](FINDING-006-007.md)：泛化“同意授权”不足以披露源码；必须明确点名 Ark、OpenAI Codex、三路 payload
  boundary 与 `EVALUATION_ONLY`，此前机器授权文档不可执行且 Provider calls=0。
- [FINDING-006-008](FINDING-006-008.md)：run-003 证明 Java `declared_method_inventory` 不属于继承的 ITER-003 exact
  qualification；两个 generic planning case 在 Provider dispatch 前正确拒绝，下一 run 必须先完成新版本 closed qualification。
- [FINDING-006-009](FINDING-006-009.md)：冻结 evaluator 未处理失败 terminal 的空 completeness；本地修复和回归已闭合，但
  不能追溯替换 run-003 evaluator，下一 suite 必须冻结新 digest。
- [FINDING-006-010](FINDING-006-010.md)：在旧 Strategy 文件内追加新版本代码会破坏 ITER-003 的 exact file identity；旧文件
  已恢复原始字节，Java 1.1.0 迁入独立版本化模块，835 项完整回归 PASS。
- [FINDING-006-011](FINDING-006-011.md)：product freeze 的 Java-only formal stub 漏掉 exact Strategy identity；产品 fail-closed
  guard 正确拒绝，stub 已显式绑定 `JAVA_PRODUCT_STRATEGY_REF`，同一 suite 6/6 与全新 run-007 835/835 PASS。
- [FINDING-006-012](FINDING-006-012.md)：Java qualified baseline 自带的 `document_digest` 在授权 wrapper 外层 seal 中被同名覆盖；
  run-007 六个真实 call 后均按 postcondition 拒绝。wrapper 已排除 baseline seal 并增加 Java 专用回归，15/15 PASS。
- [FINDING-006-013](FINDING-006-013.md)：run-008 的 Java 静态调用封闭题集 PASS 不能证明产品正在接近通用源码问答 MVP；
  产品成功标准、迭代选择、Roadmap 和治理模板现强制目标差距、能力累积、held-out 自由问题与跨域组合 Gate。

当前没有 `open` Finding。run-003/run-007 FAIL 均永久保留；修复后的 run-008 三路各 6/6 且 comparison PASS。Finding 的处置
闭合不替代用户最终 Acceptance，也不授权 Production Activation。用户随后于 `2026-08-13T11:45:33+08:00` 接受 run-008
已证明的窄范围；run-008 仍只证明 Java 静态调用子集，不能解释为正式最终 Web Chat 或通用源码问答 MVP 已完成。
