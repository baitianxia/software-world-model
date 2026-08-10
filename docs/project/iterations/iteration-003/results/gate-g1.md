---
id: ITER-003-RESULT-G1
kind: iteration-result
status: pass
authority: evidence
owners: [project, quality]
depends_on: [ITER-003-RESULT-G0, ITER-003-VERIFICATION, ITER-003-SLICE-001, FINDING-003-002, FINDING-003-003, FINDING-003-004, FINDING-003-005, FINDING-003-006, FINDING-003-007, FINDING-003-008]
code: [src/software_world_model/source_integration, src/software_world_model/knowledge_engine, src/software_world_model/application_services, src/software_world_model/infrastructure, src/software_world_model/interface]
tests: [tests/test_source_operations.py, tests/test_artifact_use_authority.py, tests/test_structure_knowledge.py, tests/test_structure_publication.py, tests/test_maven_structure.py, tests/test_maven_structure_update.py, tests/test_maven_structure_update_authority.py, tests/test_structure_read_session.py, tests/test_context_comparison.py, tests/test_legacy_formal_reader.py, tests/test_maven_structure_cli.py, tests/test_iteration_003_g1_integration.py]
iteration: ITER-003
---

# ITER-003 Result：G1 Knowledge Kernel

## Claim and scope

V-002 至 V-006 与 V-012/G1 在 exact implementation checkpoint `ddb8f5feba1e0c52d2f788c2bb66c93810f2b469` 上通过。结果证明 frozen Maven Schema/Evaluation Context/Canonicalization 下的 typed Relation/Literal Fact、Entity/Fact/Coverage Root-State 分离、`ENRICH`/`REPLACE_COVERAGE`、完整 Maven reactor Coverage、零问题 A1→B→A2 更新、exact Structure Read Session/ordered Read Set 稳定性，以及 ITER-002 legacy Snapshot 只读兼容均有机械和人工可读证据。

本结果只解除 G2 的开发阻断。它不证明 Source-off Snapshot/View、Read Bundle 或隔离查询，不证明回答链、Capability Evaluation、真实模型质量、外部 Provider 资格、源码或结构结果披露、浏览器体验、Product Validation 或 Production Activation。

## Exact inputs / baseline

- 上一 Gate 的已提交 G0 PASS Result commit：`7286c0108394baac4254a14fc3405029707dd10d`。
- G1 实现与执行 checkpoint：`ddb8f5feba1e0c52d2f788c2bb66c93810f2b469`；其 parent 为上述 G0 Result commit，checkpoint message 为 `feat: implement iteration 003 g1 knowledge kernel`。
- checkpoint Manifest 文件 digest：`sha256:c857c11822b6b19d665be0101e74934b1758cb36de0b29d4f10aa4a21799deec`。
- frozen Structure Schema、Maven Evaluation Context 与 Canonicalization digest 分别为 `sha256:947bea83028ff6658b01c18dccfd0c1ef028fa5e9a8701a4a0e90d16b8a58ce9`、`sha256:4fce4ccbcc8ddbe254dc90e8419a178ce37c6fd9ea287e6fad8d15d571161ffd` 和 `sha256:4fae328bd8c2959cfc1eaaae3b9b27f40d601bf2ffb488bf3abe2cc81c5da6cf`。
- mall Oracle digest 为 `sha256:412d2e0381ab46cfc84c95e9769f1227733ac2a523487119a15130bcca74b625`；A/B exact revisions 为 `a50870fba92d59021f07cacbe947442b1871e78f` 与 `cfaadb201bb7aa6425de069fab5e57bf8b5048f3`。
- legacy DB/report digest 为 `sha256:081cc8e392d61204e20f97b48b5dfa44e14aa046edd49ce4eeda4a016d3daaff` 与 `sha256:28744a5f279461c13672079e04d984bbaf7a1e1a9cbefd136adadaa9bbf6dc71`。
- checkpoint 验证开始时 worktree clean；`frozen-input-hashes.log` 将上述文件逐一重新绑定到 G0 冻结 digest。

## Execution and evidence

原始证据目录为 `var/iteration-003/g1/ddb8f5feba1e0c52d2f788c2bb66c93810f2b469/`。目录保存 checkpoint/lineage、环境、测试、diff、输入 digest、Oracle/Publication 审计、人工复核和十一份 JSON 报告。

- `python3 scripts/docs.py check`：164 份 current 文档通过，见 `docs-check.log`。
- G1 focused suites：132/132 通过，17.701 秒，见 `focused-tests.log`。覆盖 typed endpoint/identity、Root-State、Coverage、Admission/Publication、Maven evaluator/update、Source selector 与 Artifact-use authority、故障恢复、Structure Read Session、legacy reader 和 CLI 审计输出。
- frozen mall integration：1/1 通过，2.215 秒，见 `integration-tests.log`。公共 CLI 完成零 Question/Task 的 A1→B→A2，验证 stale CURRENT CAS、旧 B 查询和 B 后固定 Read Session/ordered A1→B Read Set 在 A2 后不漂移。
- 完整回归：589/589 通过，48.318 秒，见 `full-suite.log`；没有用 skip 代替 Gate claim。
- `git diff --check` 通过且无输出，见 `diff-check.log`；checkpoint clean 状态见 `worktree-status.log`。
- 十一份 `reports/*.json` 均成功解析，见 `json-parse-check.log`。A1/B/A2 报告逐行展示 Snapshot ID/revision、Entity Root/State、Relation source/predicate/target 与 Fact Root/State、Evidence locator、Coverage Root/State、每条 dependency 的 resolved GA/version/GAV、Profile/exclusion、删除和旧 Snapshot 查询，并同时展示 Verifier Assessment、Admission 与 Artifact-use Confirmation authority。
- `oracle-audit.log` 的 `oracle_comparison` 为 `PASS`：A1/A2 为 7 Entity、11 Relation，B 为 8/14；Coverage Root 稳定，A/B 共有 Root 的 revision-bound State 均变化；A1/A2 manifest 与 read set 相等；B 历史可读；B→A2 删除 security Entity 及三条 Relation；mall 仓库签名不变。
- 路径核对与 frozen Oracle 相等：A 只有 `mall-admin -> mall-mbg -> mall-common`，B 新增 `mall-admin -> mall-security -> mall-common`，且 B 中 `mall-admin` 到 `mall-search` 无内部路径。`publication-audit.log` 记录三个 `PUBLISHED` Result、三个 `ACCEPT` Admission、三个独立 verifier `PASS` 与 owner-verifiable Artifact-use Confirmation。
- V-012 直接打开 frozen ITER-002 artifact，通过 immutable read-only SQLite URI 重算 Snapshot、Entity/Fact/Inference/Evidence authority、locator、predecessor 与 additive membership；读取前后原 artifact digest/metadata/目录不变。

人工打开并核对了 A1/B/A2、historical B、三个 Structure Read Session、Oracle comparison、Publication audit 和冻结输入摘要。结论记录在 `manual-review.md`：V-002 至 V-006 与 V-012 均有 direct executable 和 human-readable evidence。

## Result, failures and limitations

G1 最终结果为 **PASS**。V-002、V-003、V-004、V-005、V-006 与 V-012 在同一 clean checkpoint 上满足；G2 可以开始。

最终 checkpoint 没有未处置的 G1 失败。对抗验证已覆盖悬空/混型 endpoint、同 Root 多 State、重叠 Coverage、`ENRICH` 状态冲突、路径/GA 名称拼接、version/profile/property/symlink/路径逃逸、Source/Scope/Binding 撤权、Artifact Package/Closure/Protection 与 Confirmation 篡改、同 verifier ref 自签、伪造或缺失 Admission/Assessment/Publication Receipt、CURRENT CAS、before/after-commit 与 `OUTCOME_PENDING` recovery；拒绝路径不污染 CURRENT，也不重新 dispatch Source effect。

G2 及以后内容均未执行：没有生成或验证 Source-off Bundle/View，没有进行隔离 answer/query 进程或网络/mount allowlist 测试，没有实现或运行完整回答权威链，没有选择或调用任何外部 Provider/Adapter/Model，没有取得源码或结构结果披露授权，没有运行 Capability Evaluation、同模型 baseline、真实浏览器评测或 Product Validation，也没有执行 Activation。G1 PASS 不得被解释为这些事项已通过。

## Findings and system write-back

G1 产生的实现发现均已 dispositioned；它们闭合既有合同要求，没有引入新的架构分支或 ADR：

| Finding | Disposition |
|---|---|
| `FINDING-003-002` | 新增版本化 Local Git tree-entry Artifact，保留旧 LIST 兼容并证明 regular file/symlink 与 exact tree object。 |
| `FINDING-003-003` | 闭合 Objective/Target/Schema/Verifier/Admission/Publication 与 durable Attempt/Result authority chain，并对不确定 Publication 结果执行同键恢复。 |
| `FINDING-003-004` | 将 parent/property/dependencyManagement/endpoint provenance 与跨 POM profile 相关性纳入 COMPLETE 判定。 |
| `FINDING-003-005` | 封闭 Local Git selector、binding-aware Target Resolution、symbolic-ref freeze、classification 与 eligibility digest 的 dispatch authority。 |
| `FINDING-003-006` | legacy reader 重算完整对象/Evidence authority，并验证 support kind、predecessor chain 与 additive membership。 |
| `FINDING-003-007` | 新增 exact Structure Read Session authority，绑定 Scope/Task/caller、caller-declared order、Snapshot/Coverage 与 Knowledge-owned Context Comparison。 |
| `FINDING-003-008` | 在 payload 前重验当前 Scope/Source/Binding，以 exact Package/Closure/Protection 限定 replay，并让 Admission 与 Publisher owner-read candidate-bound persistent-use Confirmation。 |

这些 Finding 的处置已写回各自列明的 local implementation、测试和相关 current System Contract；G1 Result 不用结果文档重新定义系统语义。没有 Finding 被留到 G2 隐式解决。

## Validity / supersession

本结果只对 G0 Result commit `7286c0108394baac4254a14fc3405029707dd10d`、实现 checkpoint `ddb8f5feba1e0c52d2f788c2bb66c93810f2b469`、Manifest digest `sha256:c857c11822b6b19d665be0101e74934b1758cb36de0b29d4f10aa4a21799deec`、上列 frozen inputs 和原始证据目录成立。

任一 G1 产品代码、current contract、测试、frozen Schema/Evaluation Context/Canonicalization、mall revision/tree/Oracle、legacy artifact、Manifest association 或 authority composition 变化都会使本结果陈旧，并要求在新 exact checkpoint 上重跑 V-002 至 V-006/V-012。后续 Gate PASS 不能替代本结果或删除其 Finding/故障证据；本结果也永远不能作为外部 Provider、披露、浏览器、Product Validation 或 Production Activation 的授权。
