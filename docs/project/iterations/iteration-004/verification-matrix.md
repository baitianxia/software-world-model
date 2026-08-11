---
id: ITER-004-VERIFICATION
kind: iteration-verification
status: not-run
authority: planned-verification
owners: [quality]
depends_on: [ITER-004-PROPOSAL, ITER-003-RESULT-G3B]
code: []
tests: []
iteration: ITER-004
---

# Iteration 004 Verification Matrix

| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |
|---|---|---|---|---|---|---|
| V-001 | Web 请求明确进入 WORLD_MODEL 且没有 Direct fallback | unit / contract | fake runner、非法 mode/dataset/request | 页面永久标记模式；只调用 injected World Model runner；非法或 runner failure 均失败关闭 | tests + `var/iteration-004/` | not-run / blocking |
| V-002 | 交互 launcher 只使用 accepted package、allowlisted Read Set 与无 payload Bundle | architecture / security | ITER-003 product `b9b329a…`、三个 selector、tampered/missing artifact probes | 启动重验 digest 与 stage；Answer/Gateway/Projector 保持原 OS capability；Source/Evidence/Oracle/baseline 不可见 | tests + startup preflight | not-run / blocking |
| V-003 | Answer 与 Citation 仍是分离浏览器读取 | contract / interface | sealed page、Citation projection、wrong request/result/digest | 答案响应只给 result-scoped citation URL；独立 GET 验签后返回 Projection；换绑拒绝 | tests | not-run / blocking |
| V-004 | 新自由问题真实走一次完整隔离链路 | product | `ORDERED_A_B`；此前未作为 exact suite 文本出现的 Maven Structure 问题 | 1 Provider call、0 retry；WORLD_MODEL 页面、Read Binding、权威链和 Citation 完整 | immutable live Result | not-run / blocking |
| V-005 | 超出 Structure Coverage 的自由问题诚实返回 Gap | product | `ORDERED_A_B`；新的 design-intent 问题 | 同一链路 1 Provider call；Knowledge Gap；无正文 Citation；无 Source fallback | immutable live Result | not-run / blocking |
| V-006 | 用户能在真实本机浏览器输入、发送并查看最新流程 | human / product | loopback service、两条 live Result | 输入框可用；loading/失败可见；答案、A/B View、Coverage、Citation、authority 可检查；console 无 error | browser manual review | not-run / blocking |
| V-007 | 变更不破坏已有功能和文档 | regression | focused tests、完整 suite、docs gate | 全部 PASS；现有 DIRECT_INVESTIGATION 明确独立且未被静默替换 | logs | not-run / blocking |
| V-008 | Production Activation 未被推导或执行 | boundary | launcher config、Result | 永久 `EVALUATION_ONLY`；只绑定 loopback；Production Activation=`NOT_EXECUTED` | tests + Result | not-run / cannot be inferred |

## Exploratory failure interpretation

`EXACT_FIXTURE_VALID` 的一个新自由问题在 accepted Answer workload 内于 Provider dispatch 前失败，原始 failure terminal
必须保留。V-006 的交互结论只在页面明确失败关闭、无 Direct fallback、无隐藏重试且随后独立新 request 可成功时成立；
不得把“可以自由输入”解释为“任意问题必然回答”。见 `FINDING-004-002`。
