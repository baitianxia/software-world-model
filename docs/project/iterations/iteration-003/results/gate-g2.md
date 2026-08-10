---
id: ITER-003-RESULT-G2
kind: iteration-result
status: pass
authority: evidence
owners: [project, quality]
depends_on: [ITER-003-RESULT-G1, ITER-003-VERIFICATION, ITER-003-SLICE-001, FINDING-003-009, FINDING-003-010]
code: [src/software_world_model/application_services, src/software_world_model/infrastructure, src/software_world_model/interface, validation/structure_world_model_iteration_003/isolation]
tests: [tests/test_structure_read_bundle.py, tests/test_structure_view.py, tests/test_structure_view_cli.py, tests/test_citation_projector.py, tests/test_iteration_003_g2_integration.py, tests/test_iteration_003_g2_isolation.py]
iteration: ITER-003
---

# ITER-003 Result：G2 Source-off Snapshot/View

## Claim and scope

V-007/G2 在 exact implementation checkpoint `82aef7563556c70527b3c92227d0711a28437587` 上通过。结果证明 no-payload exact Snapshot Read Bundle、ordered Read Set、Coverage-aware Structure View、typed candidate resolution、A1/B/A2 inventory/path/diff、Result-scoped disposable Citation Store 与独立 Citation Projector，能在真实 macOS deny-default Seatbelt capability 边界内完成 source-off 重启和查询；查询与引用投影不修改 Snapshot/authority。

本结果只解除 G3a 无外部分派回答权威链的开发阻断。它不授权或证明外部 Provider/Model 调用、Conformance、Capability Evaluation、源码或结构结果披露、同模型 baseline、G3b 浏览器模型运行、Product Validation 或 Production Activation。首次外部 CE 或模型分派前仍须单独取得本轮披露确认。

## Exact inputs / lineage

- 上一 Gate 的已提交 G1 PASS Result commit：`801717d6e75459afeddb7299234a2e32b65aad16`。
- G2 实现与执行 checkpoint：`82aef7563556c70527b3c92227d0711a28437587`；其 parent 正是上述 G1 Result，tree 为 `52d73bd204713b0f43076d1228ccd0ff10462f2c`。
- checkpoint Manifest digest：`sha256:c857c11822b6b19d665be0101e74934b1758cb36de0b29d4f10aa4a21799deec`。
- frozen mall Oracle digest：`sha256:412d2e0381ab46cfc84c95e9769f1227733ac2a523487119a15130bcca74b625`；A/B exact revisions 仍为 `a50870fba92d59021f07cacbe947442b1871e78f` 与 `cfaadb201bb7aa6425de069fab5e57bf8b5048f3`。
- frozen Maven identity fixture tree digest：`sha256:418c223c43ee969b67370f664b8df04b10502553b5a138da09869284736f41d1`；其 Oracle digest 为 `sha256:b02e4414f2c03fb38da433b343ddeebb8a381a23dad3e0ba3e89792bc468b268`。
- 执行从 clean checkpoint 开始。Answer 与 Projector 的 87-file staged product package 均与 checkout 逐文件相等；workload、probe、profile、Python executable 和 `sandbox-exec` 另有 digest 绑定。

## Execution and evidence

原始证据目录为 `var/iteration-003/g2/82aef7563556c70527b3c92227d0711a28437587/`。它保存 lineage、测试日志、connected summary、八份 staged Bundle、两角色 package/input/output、Citation Store、isolation config/raw report、24 项聚合检查、人工复核、两路独立审计和 222 个文件 hash。

- G2 focused unit/contract/isolation suites：60/60 PASS，2.027 秒，见 `logs/focused-tests.log`。
- frozen mall/identity integration：1/1 PASS，2.719 秒，见 `logs/integration.log`。
- 完整回归：650/650 PASS，45.964 秒且进程退出码为 0，见 `logs/full-regression-confirm.log`。
- implementation checkpoint 文档检查：167 份 current documents PASS；Result write-back 后的 current 文档检查另行通过。`git diff --check`、JSON 解析、staged package byte comparison 与直接 no-payload scan 均通过。
- 30 份 JSON 原始/派生证据均可解析；`evidence-summary.json` 的 24 项检查全部为 `true`，`all_checks_pass=true`。`manual-review.md` 联合裁决 Bundle/View/Citation、authority/query invariance 与 OS report；`independent-audit.md` 记录 Gate 与安全两路只读复核均 PASS、无 blocker。

## Bundle, View and Citation result

- Answer staged input 的八个文件覆盖 mall A1/B/A2 Snapshot Bundle、两个 ordered envelope，以及 frozen identity A/B Bundle/envelope。connected 与 isolated 两次机械审计均未发现 `artifact_bytes`、`excerpt`、`observation`、`provider_input` 或 `source_bytes` payload key。
- source-off Answer 产生 27 个 typed Result。mall inventory 为 A1=6、B=7、A2=6；`mall-admin -> mall-common` 全部简单路径为 1/2/1；B root→security 与 admin→search 均为 Coverage 支持的完整否定。
- A1→B 新增一个 Entity 与三条 Relation；B→A2 删除同一个 Entity 和三条 Relation，旧 B 仍可读。A2 是 B 后再次对 source revision A replacement 得到的新 Snapshot，不是第三个 source revision。
- frozen identity POM 由真实 G1 Maven evaluator 生成完整图并与 Oracle 相等。mention `common-lib` 返回两个 typed candidates/`AMBIGUOUS`；shared 与 legacy full GA 各自唯一。Billing 只连 shared，不连 legacy，后者是完整 Coverage 支持的否定。
- 所有 View Result 绑定 Coverage 与 exact support。Coverage 不足返回 `PARTIAL / INCOMPLETE_COVERAGE`，不得支持负结论；candidate 只匹配 type-specific public identity/display 字段，不接受 revision、scope 或 binding provenance 作为实体名称。
- trusted broker 从实际 sealed Result 的 typed Evidence allowlist 物化 disposable Store；物理集合严格为 `manifest.json` 加 10 个 observation。Result/Store/allowlist digest 逐层相等，独立 Projector 输出恰好 10 条 citation。seal 只由父级按 digest 单向复制并设为 `0444`。
- authority 在 source-off query 与 projection 前后全表计数相同，`knw_structure_snapshots` 始终为 3；查询没有新建 Snapshot。

## OS isolation result

- raw `isolation-run.json` 的 `isolation_status=PASS`。它的 `v007_gate_status=NOT_EVALUATED` 是刻意的 OS-only 边界：raw harness 不自封产品 Gate；本 Result 才把它与 Bundle/View/Citation、查询不变性和人工核对联合裁决为 V-007 PASS。
- sandbox 外 preflight 证明 exact forbidden file/Git/SQLite 可读，并证明 Source remote、公网 endpoint 与 DNS 可达；拒绝结果不是目标本来不存在造成的假阳性。
- OS enforcement 为 `/usr/bin/sandbox-exec`，digest `sha256:8857d087219f0f39d3e3c163e5d0a0aed690cc22f34b50c7eee3d74f93e69688`。bundled exact Python 3.12 executable digest 为 `sha256:eb9d74b9c7cfdfb2c9b91614edb2c3607360ba46c5aa7fc4557b3a4a23e97cff`；所有 sandboxed Python 使用 exact `-I -S -B`。
- Answer probe/workload PID 为 84722/84723，Projector 为 84724/84725；四个 PID 都与 launcher observation 相等且互异。probe/workload 在角色内共享 nonce，Answer 与 Projector nonce 不同。
- 两角色各自的九项 worker probe 均被 OS 拒绝：Source remote、公网、DNS、TCP、Unix socket、越界文件、SQLite、Git repository 和跨角色访问。外层 control 成功，fork、Git executable 与一般 subprocess probe 均被拒绝。
- 正常 Answer workload 审计 214 个 authorized event，Projector 审计 244 个；Source、Git、Evidence payload、authority DB、Evidence Store、other role、out-of-allowlist file、network、process 九类 prohibited count 在两边全部为 0。
- protected-input digest 在 Answer 与 Projector 后均不变；Answer 最终只含三个声明文件且无额外目录，Projector 只含两个声明文件且无额外目录。Store 文件与目录物理集合也精确等于 allowlist 及其隐含父目录。额外文件、空目录、symlink、hardlink/alias 与 path escape 反例均失败关闭。

## Failures and limitations

G2 最终结果为 **PASS**，没有未处置 blocker。已修复的审查 blocker 包括 Coverage 不足时的错误完整性、以 provenance 字段命中 candidate、probe/workload 自证明耦合，以及 closed output/Store 忽略空目录。

以下限制已进入原始报告与人工复核，但不推翻本次 exact run：

- Seatbelt 证明 file/network/process capability denial，不等同于 Linux mount/network namespace，也不证明宿主路径不存在。
- literal ancestor traversal 会暴露 exact ancestor 的直接目录项名称，但不授权读取子文件内容；目录名敏感时须改用自包含 launcher 或 VM/container。
- Python audit hook 只覆盖 Python-visible operation；OS 强制边界仍由 Seatbelt 提供。
- 证据绑定 exact Python executable/root、profile、workers、展开参数和 staged manifests，但未 hash 整棵 Python runtime tree。
- harness 一般性上未禁止把 evidence output 配到 protected stage root；本次实际证据路径位于两个 role root 之外，因此没有影响已执行的边界。

没有选择或调用任何外部 Provider/Adapter/Model，没有执行 CC、CE、两条源码 Agent baseline、G3b/G4、Product Validation 或 Activation。G2 PASS 不得被解释为这些事项已经完成。

## Findings and system write-back

G2 的两个实现发现已唯一处置：

| Finding | Disposition |
|---|---|
| `FINDING-003-009` | 将 Citation Projector 边界收窄为 trusted broker 按 sealed Result allowlist 物化的 result-scoped disposable Store；Projector 不直接读取完整 Evidence Store。 |
| `FINDING-003-010` | 把本机隔离事实限定为 macOS Seatbelt capability boundary，并明确 application input、runtime/ancestor capability、probe/workload/PID/nonce、closed output 与 executor limitation。 |

处置已写回 owning System Contract、ADR、Slice、验证矩阵、代码和测试；本 Result 不重新定义系统语义。

## Validity / supersession

本结果只对 G1 Result commit `801717d6e75459afeddb7299234a2e32b65aad16`、G2 checkpoint `82aef7563556c70527b3c92227d0711a28437587`、上述 frozen inputs、exact executor/runtime identities 和原始证据目录成立。

任一 G2 product/validation code、Bundle/View/Citation contract、frozen fixture/oracle、Seatbelt profile、Python executable/runtime root 或 staged input 变化都会使本结果陈旧，并要求在新 clean checkpoint 上重跑 V-007。后续 Gate PASS 不能替代本结果；本结果也永远不能作为外部披露、Provider 调用、浏览器模型质量、Product Validation 或 Production Activation 的授权。
