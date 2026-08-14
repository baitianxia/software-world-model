---
id: ITER-007-FINDINGS
kind: iteration-findings-index
status: dispositioned
authority: development-evidence
owners: [engineering, architecture, quality]
depends_on: [ITER-007-PROPOSAL]
code: []
tests: []
iteration: ITER-007
---

# ITER-007 Findings

本轮登记九条已处置 Finding：

- [FINDING-007-001](FINDING-007-001.md)：用户现场提问本身已经提供实现期不可见性，不应要求用户预制外部 runner；编码前冻结
  判定规则，代码冻结后才密封 exact 问题与结果。
- [FINDING-007-002](FINDING-007-002.md)：固定 Ark transport 每次请求关闭连接；三调用 Profile 必须由 supervisor 预建并按
  Plan、Draft、Review 顺序交接三个独立 Provider socket，数量或审计不一致时失败关闭。
- [FINDING-007-003](FINDING-007-003.md)：首次 12 次资格运行 9/12；Plan 概念覆盖和 Review finding code 词表未闭合，升级
  Strategy/Prompt/vocabulary/schema，旧失败资格不可复用。
- [FINDING-007-004](FINDING-007-004.md)：独立 evaluator 的 first-alias 位置算法误判正确动作顺序；改为单调 occurrence 匹配，
  同时保留真实逆序反例。
- [FINDING-007-005](FINDING-007-005.md)：run-002 达到 11/12 后仍遗漏 returning→return；把 Profile 静态语义词形归一写入
  `1.2.2` Prompt vocabulary，不降低阈值、不加入工程或题目分支；run-003 已以 12/12 `PASS_VALID` 关闭资格 Gate。
- [FINDING-007-006](FINDING-007-006.md)：run-001 正式 Web 的 Answer 隔离进程因 package root eager import 引入未封装
  `tree_sitter` 而失败；改为 lazy interface exports，并把 runtime exact `-I -S -B` 真实 entrypoint import 纳入候选冻结 Gate。
- [FINDING-007-007](FINDING-007-007.md)：run-002 的成功三调用 Answer 被遗留的 `unix_connect=1` role audit 误判；改为从
  frozen dispatch call count 显式传入连接期望，并用三连接 role report 回归固定。
- [FINDING-007-008](FINDING-007-008.md)：run-004 技术链成功，但“登录流程”匹配三个相关方法后因唯一 typed selector 约束返回
  Limitation；保留为 V-004/V-XD-001 非通过证据，禁止按已披露问题加入特判。
- [FINDING-007-009](FINDING-007-009.md)：run-004 的下单题只因 `return` / `throw` 命中登录方法，证明固定单方法协议同时缺少结果驱动调查和可靠负向判定；触发本轮 stop/redirect 并路由到 `ROADMAP-M-002` Step 1。

Iteration 已因产品 Gate 失败而 rejected；所有 Finding 均已有唯一处置。本索引完成只表示反馈闭环，不表示 ITER-007 获得 Acceptance。
