---
id: ITER-004-VERIFICATION
kind: iteration-verification
status: pass
authority: evidence
owners: [quality]
depends_on: [ITER-004-PROPOSAL, ITER-003-RESULT-G3B]
code: []
tests: []
iteration: ITER-004
---

# Iteration 004 Verification Matrix

| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |
|---|---|---|---|---|---|---|
| V-001 | Web 请求明确进入 WORLD_MODEL 且没有 Direct fallback | unit / contract | fake runner、非法 mode/dataset/request | 页面永久标记模式；只调用 injected World Model runner；非法或 runner failure 均失败关闭 | `tests/test_world_model_browser.py`；focused 11/11 | PASS / no Direct route |
| V-002 | 交互 launcher 只使用 accepted package、allowlisted Read Set 与无 payload Bundle | architecture / security | ITER-003 product `b9b329a…`、三个 selector、tampered/missing artifact probes | 启动重验 digest 与 stage；Answer/Gateway/Projector 保持原 OS capability；Source/Evidence/Oracle/baseline 不可见 | `tests/test_iteration_004_interactive_browser.py`；startup `sha256:00814adb…` | PASS / protected stage unchanged |
| V-003 | Answer 与 Citation 仍是分离浏览器读取 | contract / interface | sealed page、Citation projection、wrong request/result/digest | 答案响应只给 result-scoped citation URL；独立 GET 验签后返回 Projection；换绑拒绝 | focused tests；Projection `sha256:45024d95…` / `sha256:5eeb8c79…` | PASS / independent GET verified |
| V-004 | 新自由问题真实走一次完整隔离链路 | product | `EXACT_B`；此前未作为 exact suite 文本出现的 Maven Structure 问题 | 1 Provider call、0 retry；WORLD_MODEL 页面、Read Binding、权威链和 Citation 完整 | terminal `sha256:2fe0c5bd…`；browser terminal `sha256:e2267719…` | PASS / 1 call each, 0 retry |
| V-005 | 超出 Structure Coverage 的自由问题诚实返回 Gap | product | `ORDERED_A_B`；新的 design-intent 问题 | 同一链路 1 Provider call；Knowledge Gap；无正文 Citation；无 Source fallback | terminal `sha256:a423ce36…`；page `sha256:b80b8be4…` | PASS / gap, 0 citation |
| V-006 | 用户能在真实本机浏览器输入、发送并查看最新流程 | human / product | loopback service、success/gap/failure live Result | 输入框可用；loading/失败可见；答案、A/B View、Coverage、Citation、authority 可检查；console 无 error | request `wm-b0dbe1c0-6190-43a2-bc0b-8b3f2b778597`；manual browser review | PASS / success and fail-closed checked |
| V-007 | 变更不破坏已有功能和文档 | regression | focused tests、完整 suite、docs gate | 全部 PASS；现有 DIRECT_INVESTIGATION 明确独立且未被静默替换 | focused 11/11；full 761/761；`scripts/docs.py check` | PASS / regression complete |
| V-008 | Production Activation 未被推导或执行 | boundary | launcher config、Result | 永久 `EVALUATION_ONLY`；只绑定 loopback；Production Activation=`NOT_EXECUTED` | tests、startup、全部 live terminal | PASS / NOT_EXECUTED |

## Exploratory failure interpretation

`EXACT_FIXTURE_VALID` 的一个新自由问题在 accepted Answer workload 内于 Provider dispatch 前失败，原始 failure terminal
必须保留。V-006 的交互结论只在页面明确失败关闭、无 Direct fallback、无隐藏重试且随后独立新 request 可成功时成立；
不得把“可以自由输入”解释为“任意问题必然回答”。见 `FINDING-004-002`。
