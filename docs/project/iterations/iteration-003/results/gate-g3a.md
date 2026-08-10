---
id: ITER-003-RESULT-G3A
kind: iteration-result
status: pass
authority: evidence
owners: [project, quality]
depends_on: [ITER-003-RESULT-G2, ITER-003-VERIFICATION, ITER-003-SLICE-001, FINDING-003-011, FINDING-003-012, FINDING-003-013]
code: [src/software_world_model/application_services/world_model_answering.py, src/software_world_model/application_services/structure_view.py, src/software_world_model/interface/world_model_evaluation.py, validation/structure_world_model_iteration_003/g3a, validation/structure_world_model_iteration_003/isolation]
tests: [tests/test_world_model_answering.py, tests/test_world_model_evaluation.py, tests/test_iteration_003_g3a_integration.py, tests/test_iteration_003_g2_isolation.py, tests/test_structure_view.py, tests/test_structure_read_bundle.py]
iteration: ITER-003
---

# ITER-003 Result：G3a Offline answer-chain

## Claim and scope

V-008/G3a 在 exact implementation checkpoint `f2269ecca5c1e85e69fafd93fe599c841227f3c7` 上通过。结果证明 package-owned deterministic offline strategy 能以 exact no-payload ordered Snapshot Read Bundle 完整形成 `Requirement Revision → Needs/Joint Constraints → candidate resolution → Query Plan → Query Result → Need Assessments → Draft → Review → Authorization → Delivery` 权威链，递归验证全部 authority/cross-link，并在 `EVALUATION_ONLY` 页面展开；规定的篡改、伪造、遗漏、权限与非精确 scalar 反例均失败关闭。

本结果**只裁决 V-008**。现有“开发 ITER-003”授权不构成源码、Bundle、结构结果、问题文本或其他内容向外部 Provider 的披露确认。Result 提交后执行必须停止在 V-009 之前；只有用户在后续独立消息中明确确认本轮外部披露，并冻结 exact Provider/Adapter/Model、scheme/host/port/path、credential reference、default-deny Model Egress Gateway policy 与 Conformance 输入后，才可开始 V-009。

## Exact inputs / lineage

- 上一 Gate 的已提交 G2 PASS Result commit：`b54fb2ba04d93578af36f8a9ee7467b0e921909e`。
- G3a 实现与执行 checkpoint：`f2269ecca5c1e85e69fafd93fe599c841227f3c7`；其唯一 parent 正是上述 G2 Result，tree 为 `936dc1fcab74f45c0342ad0e7055b9d4b314e2e1`。
- checkpoint Manifest digest：`sha256:c857c11822b6b19d665be0101e74934b1758cb36de0b29d4f10aa4a21799deec`；frozen mall Oracle digest：`sha256:412d2e0381ab46cfc84c95e9769f1227733ac2a523487119a15130bcca74b625`。
- staging 在复制前机械要求环境 commit 等于 Git `HEAD`、工作树 clean，并记录 exact tree。Answer 与 Projector staged `software_world_model` package 均与 checkout 逐文件相等；生成的 `__pycache__`/`.pyc` 不属于 staged package 比较范围。两份 staged workload 与提交文件 byte-equal。
- connected chain 与 isolated Answer 使用相同的 frozen input/strategy identity。connected chain 先递归验证，再冻结 expected PAGE digest `sha256:7fa0f0ab2e568a519d9f4b301bfc0205385def198dda08d80ad5ce33cafc6d69`；Projector argv 在执行前同时冻结该 PAGE anchor 与 implementation commit anchor。

## Execution and evidence

原始证据目录为 `var/iteration-003/g3a/f2269ecca5c1e85e69fafd93fe599c841227f3c7/`。它保存 clean staging summary、connected summary、三份 staged Bundle、两角色 package/input/output、isolation config/raw report、lineage/hash/test/package-comparison 日志、41 项聚合检查、人工十阶段复核与独立只读审计。

- exact clean-checkpoint mall integration/staging：1/1 PASS，2.671 秒，见 `logs/integration.log`。
- G3a focused unit/contract/integration/isolation suites：91/91 PASS，11.143 秒，见 `logs/focused-tests.log`。
- 完整回归：697/697 PASS，54.189 秒且进程退出码为 0，见 `logs/full-tests.log`。
- implementation checkpoint 文档检查：171 份 current documents PASS；Result write-back 后的 current 文档检查另行通过。`py_compile`、`git diff --check`、15 份 evidence JSON 解析、staged package 与 workload byte comparison 均通过。
- `evidence-summary.json` 的 41 项检查全部为 `true`，`all_checks_pass=true`。`manual-review.md` 联合裁决 answer chain/page、fault closure 与 OS report；`independent-audit.md` 对进程、计数、probe、runtime roots、seal 和双锚点作了只读复核并报告 PASS。

## Answer-chain and evaluation-page result

- 页面按顺序展开恰好十个 authority：Question、Requirement Revision、Candidate Resolution Set、Query Plan、Query Result Set、Assessment、Answer Draft、Answer Review、Response Authorization 与 Delivery。它们的 exact ID/digest 汇总为 chain digest `sha256:cb981f54ca783160590939ff7dabf2146bcb70b3f2885d7c3a60225df31cafb1`。
- 原始中文问题和 response language 被保留；Requirement fidelity 对恰好三个 Need 与一个 ordered A1→B Joint Constraint 作出 `APPROVE`。三个 typed candidate resolution 连同隐藏的 candidate proof 都绑定同一 Session、Read Authority、Snapshot 与 Read Set。
- closed capability registry 只产生三个 Query Step；Result Set 只接受三个相应 issued Result，并绑定 ordered Bundle digest `sha256:966dba0ccf369c91f583e9675ef63c5e3d95d88ee01dec8464c7de41e41970f6` 与 Read Set digest `sha256:5312a199f23c2f89ea91226175d4214fbfaf672367cf2b2c7b59345a01416886`。Assessment replay 证明三个 Need 和联合约束全部满足。
- 可读答案与 frozen mall oracle 一致：B inventory=7，B 中 `mall-admin → mall-common` 全部简单内部依赖路径=2，A1→B 新增一个 Entity 与三条 Relation。三个 Claim 分别绑定对应 Result 与 support digest。
- Review 覆盖三个 Need、一个 Constraint、三个 Result 和六个固定维度；generation invocation 与 review invocation 的 ID、stage、strategy 均独立。Authorization 绑定 Question/Permission/Read Authority/Requirement/Plan/Result/Assessment/Draft/Review；Delivery revision 3 只向 `EVALUATION_ONLY` sink 交付，exact receipt accepted，state=`DELIVERED`。
- connected/isolated Answer 与 Projector 均报告 exact integer `provider_call_count=0`、`network_operation_count=0`，且 `provider_route=null`、`external_dispatch_allowed=false`、`source_access_allowed=false`、`evidence_payload_access_allowed=false`。
- isolated Answer 的 actual PAGE digest 等于带外 expected PAGE digest；isolated Projector 同时验证该 PAGE anchor 与 exact implementation commit。单向 seal 的文件 SHA-256 为 `sha256:2144db7832feacd5411c252724ba42d5bbc707d0023542d4b691e982677642ce`，不得与 PAGE domain digest 混用。

## Fault closure

聚焦 fault suites 和真实 Bundle integration 联合拒绝：Requirement Need 遗漏、联合约束 proof 缺失/错绑、caller exact `EntityRef` 伪造、mention qualifier 伪造、0/N/跨 Session candidate、隐藏 candidate proof 篡改、request ref 换输入重用、resource cap 更改/越界、未知 constraint kind、tampered/unissued/duplicate/substituted Result、wrong Read Authority、Assessment 语义重签、Claim grounding/Need coverage 缺失、generation/review 同 invocation、Review dimension 缺失、Receipt/revision 伪造与 unauthorized Delivery。

页面边界另拒绝：body/chain/delivery 协调篡改、全部公开摘要重算但不匹配带外 PAGE anchor、伪造 implementation commit、omitted limitations、duplicate/noncanonical JSON、boolean 冒充 operation count、非 exact bool/int authority scalar，以及任意嵌套 `artifact_bytes`、`excerpt`、`observation`、`provider_input`、`source_bytes` payload key。staging 也拒绝任意不是当前 clean `HEAD` 的 40-hex commit 标签。公开无密钥 digest 只作为一致性 defense-in-depth，不被描述为独立来源证明。

## OS isolation result

- raw `isolation-run.json` 的 `isolation_status=PASS`、`claim_scope=OS_FILE_NETWORK_PROCESS_ISOLATION_ONLY`。沿用通用 harness 的 `v007_gate_status=NOT_EVALUATED` 是刻意的 OS-only 边界：raw harness 不自封任何产品 Gate；本 Result 才把它与 G3a chain/page/fault evidence 联合裁决为 V-008 PASS。
- sandbox 外 preflight 证明 exact forbidden file/Git/SQLite 可读，并证明 Source remote、公网 endpoint 与 DNS 可达；所以 deny 结果不是目标本来不存在。该 preflight 只执行固定解析/连接测试，没有 Provider/Model 请求，也没有传送 question、source、Bundle、structure result 或 answer 内容。
- OS enforcement 为 `/usr/bin/sandbox-exec`，digest `sha256:8857d087219f0f39d3e3c163e5d0a0aed690cc22f34b50c7eee3d74f93e69688`。exact Python 3.14.6 executable digest 为 `sha256:add77decc18420e3307d570e48d2d72e0bcdb0b741dc06e26c976025aa651d6a`；所有 sandboxed Python 固定使用 `-I -S -B`。
- Answer probe/workload PID 为 35828/35829，Projector 为 35831/35832；四个 PID 都与 launcher observation 相等且互异。probe/workload 在角色内共享 nonce，Answer 与 Projector nonce 不同。
- 两角色各自的九项 worker probe 均被 OS 拒绝：Source remote、公网、DNS、TCP、Unix socket、越界文件、SQLite、Git repository 和跨角色访问。外层 Python control 成功，fork、Git executable 与一般 subprocess probe 均被拒绝。
- 正常 Answer workload 审计 227 个 authorized event，Projector 审计 223 个；Source、Git、Evidence payload、authority DB、Evidence Store、other role、out-of-allowlist file、network、process 九类 prohibited count 在两边全部为 exact integer 0，violations 为空。
- protected Bundle/package/Store 以及三个 runtime dependency manifest 在 Answer 与 Projector 后均不变；最终 output manifest 与声明集合精确相等。seal 只由父级按 digest 从 Answer 单向复制到 Projector 并设为 `0444`，两角色反向访问 probe 都失败。
- recursive runtime roots 只包含 exact Python base prefix，以及 worker 实际依赖的 OpenSSL 1.1.1w、SQLite 3.53.3、zlib 1.3.2 canonical version roots和固定系统 dylib roots；整个 package-manager root 只作为 literal ancestor traversal，不递归开放 sibling 内容。dependency alias/root/full manifest 均进入证据与完整性比较。

## Failures and limitations

G3a 最终结果为 **PASS**，V-008 没有未处置 blocker。实现过程中发现并闭合了 process-local evaluation authority 与 live Response Control 混淆、应用零计数不能证明全局无 I/O、bundled runtime sibling capability 过宽、公开摘要不能自行证明来源，以及 Python `bool` 冒充 `int` 的问题。

以下限制不推翻本 exact run，但限定结论范围：

- package-owned deterministic strategy 与 process-local store 只服务 G3a；它们不替代 live `ResponseControlService` 的 Task/Use Epoch/qualification/permission/persistent dispatch/late Receipt authority。
- Seatbelt 证明 file/network/process capability denial，不等同于 Linux mount/network namespace，也不证明宿主路径不存在。
- literal ancestor traversal 会暴露 exact ancestor 的直接目录项名称，但不授权读取子文件内容；目录名敏感时须使用自包含 staged launcher 或 VM/container。
- Python audit hook 只覆盖 Python-visible operation；OS 强制边界由 Seatbelt 提供。
- expected PAGE/commit 是本 evidence run 的带外 anchor；任何 checkpoint、input、strategy identity、profile、runtime、workload 或 anchor 漂移都会使本 Result 陈旧。
- strategy 的外部语义资格仍属于 V-009 CC/closed CE；V-008 PASS 不允许推断任意 injected strategy 或 model 正确、安全或已获授权。

没有选择或调用任何外部 Provider/Adapter/Model，没有冻结 credential/endpoint，没有执行 CC、CE、controlled Direct/mature Agent baseline、V-009、G3b/G4、Product Validation 或 Activation。

## Findings and system write-back

G3a 的三个实现发现已唯一处置：

| Finding | Disposition |
|---|---|
| `FINDING-003-011` | 新回答权威链固定为 process-local `EVALUATION_ONLY` 路径；不得自动提升为 live Response Control。 |
| `FINDING-003-012` | V-008 分列应用端口零计数与真实 OS operation audit/deny probes；bundled runtime dependency 只逐项开放 canonical version root 并保存完整 manifest。 |
| `FINDING-003-013` | 页面读取必须同时消费带外 PAGE/commit anchor，staging 必须绑定 clean HEAD/tree，authority scalar 使用 exact type 验证。 |

处置已写回 Slice、Verification Matrix、owning System Contract/ADR、代码和测试；本 Result 不重新定义系统语义。

## Validity / supersession

本结果只对 G2 Result commit `b54fb2ba04d93578af36f8a9ee7467b0e921909e`、G3a checkpoint `f2269ecca5c1e85e69fafd93fe599c841227f3c7`、上述 frozen inputs、exact executor/runtime identities、双锚点和原始证据目录成立。

任一 G3a product/validation code、Bundle/Answer/Page contract、fixture/oracle、Seatbelt profile、Python executable/runtime dependency、staged input 或 trusted anchor 变化都会使本结果陈旧，并要求在新 clean checkpoint 上重跑 V-008。后续 Gate PASS 不能替代本结果；本结果也永远不能作为外部披露、Provider 调用、模型资格、浏览器模型质量、Product Validation 或 Production Activation 的授权。
