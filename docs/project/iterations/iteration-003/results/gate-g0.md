---
id: ITER-003-RESULT-G0
kind: iteration-result
status: pass
authority: evidence
owners: [project, quality]
depends_on: [ITER-003-VERIFICATION, ITER-003-SLICE-001, FINDING-003-001]
code: []
tests: [tests/test_iteration_003_fixture.py, tests/test_iteration_003_validation_assets.py]
iteration: ITER-003
---

# ITER-003 Result：G0 冻结输入

## Claim and scope

V-001/G0 在 exact 执行 checkpoint `af849fb198179cfe1d1514f272a1a06236684f43` 上通过，授权治理提交 Q 为 `42a3f1ababed73cded8aafb046105309a79c170e`。结果证明 ITER-003 的文档授权链、冻结 Structure 输入、Maven/Agent 工具、旧 Snapshot 兼容输入、Oracle/问题隔离和生成器在产品代码修改前可机械复核并可人工打开；它只解除 G1 的编码阻断，不证明 G1 及以后实现、模型资格、产品价值或 Activation。

## Exact inputs / baseline

- ITER-002 clean closure：`40c65840eaf146360c58ca888b97fc5bd9a0f2e2`。
- 开发前准备提交 P：`a4ae307c8ab04979e87e0460f19b6ec81fc915a3`。
- 用户授权治理提交 Q：`42a3f1ababed73cded8aafb046105309a79c170e`。
- G0 最终输入与执行 checkpoint：`af849fb198179cfe1d1514f272a1a06236684f43`。
- checkpoint Manifest 文件 digest：`sha256:c857c11822b6b19d665be0101e74934b1758cb36de0b29d4f10aa4a21799deec`。
- `40c6584..P` 与 `P..Q` 没有 `src/software_world_model` 产品代码变化；`P..Q` 也没有 `tests` 或 `validation` 变化。`Q..af849fb` 只处置 G0 验证协议 Finding，没有产品代码变化。

最终冻结对象如下；路径和完整 digest 也保存在 Manifest 与原始 `frozen-input-digests.log`：

| Input | Exact ref / digest |
|---|---|
| mall Oracle | `MALL-MAVEN-STRUCTURE@1.0.0` / `sha256:412d2e0381ab46cfc84c95e9769f1227733ac2a523487119a15130bcca74b625` |
| Maven identity fixture | `maven-identity-anti-name-stitch@1` / `sha256:418c223c43ee969b67370f664b8df04b10502553b5a138da09869284736f41d1` |
| Structure Schema | `MAVEN-REACTOR-STRUCTURE@1.0.0` / `sha256:947bea83028ff6658b01c18dccfd0c1ef028fa5e9a8701a4a0e90d16b8a58ce9` |
| Maven Evaluation Context | `MAVEN-EVALUATION-CONTEXT@1.0.0` / `sha256:4fce4ccbcc8ddbe254dc90e8419a178ce37c6fd9ea287e6fad8d15d571161ffd` |
| Maven Canonicalization | `MAVEN-REACTOR-CANONICALIZATION@1.0.0` / `sha256:4fae328bd8c2959cfc1eaaae3b9b27f40d601bf2ffb488bf3abe2cc81c5da6cf` |
| Product evaluator suite | `ITER-003-WORLD-MODEL-PRODUCT-SUITE@1.0.0` / `sha256:c165af6beb5ce66d45f035c3155ef4cb7d39b488fb6fe29af4b61e77217aaf2c` |
| Product-visible input suite | `ITER-003-WORLD-MODEL-PRODUCT-INPUT-SUITE@1.0.0` / `sha256:15bb9a72b68d69f8077ba95bd87b4c54861b0bc08e26ed38fb54221d71d1bfd4` |
| Closed capability suite | `ITER-003-WORLD-MODEL-CAPABILITY-SUITE@1.0.0` / `sha256:b9118d83aa40e58ade6e3c947ea86d1d6d73ebd50d3b1ae0797d5caa7e415ad6` |
| Metamorphic generator | `MAVEN-STRUCTURE-METAMORPHIC-GENERATOR@1.0.0` / `sha256:e3297436ff7ebcd0fb6fcb24b3e5104e95bb1b0d525dc72ad3c2bb9b2ae20ce6` |
| Legacy DB / report / generator | `sha256:081cc8e392d61204e20f97b48b5dfa44e14aa046edd49ce4eeda4a016d3daaff` / `sha256:28744a5f279461c13672079e04d984bbaf7a1e1a9cbefd136adadaa9bbf6dc71` / `sha256:e9b3bd97fbb184f636ec1a5963f251149fa97fef4ed29a49161601b807670638` |
| Controlled Direct protocol / implementation | `ITER-003-DIRECT-SOURCE-BASELINE@1.0.0` / `sha256:af074014318fab1b5e0fdc3dafab70c1fcd45fe1060da4141e8d8fc594094869` / `sha256:e04c6cca4eb484cd75512c9d748b3bd142027501c5ebe9c905fb5e1e96b06bbd` |
| Mature Agent protocol / answer schema | `ITER-003-MATURE-SOURCE-AGENT-BASELINE@1.0.1` / `sha256:4ac3e880dfc6f359718584e4edc54cc93d8e4b80f89c80804d02776ce8030d53` / `sha256:cfe6ea01dedfbbd795676d00a90f7bf74d8227694ccb35a6f9a356a720e8e17d` |

`mall` remote 为 `https://github.com/macrozheng/mall.git`；A/B revision 与 tree 分别为 `a50870fba92d59021f07cacbe947442b1871e78f` / `be7748004ce90f9260936124476f1b385e1cc61f` 和 `cfaadb201bb7aa6425de069fab5e57bf8b5048f3` / `1d84b1d4dd9861f2678b21d92f6202cbce5786ac`。

## Execution and evidence

原始证据目录为 `var/iteration-003/g0/af849fb198179cfe1d1514f272a1a06236684f43/`。所有管道命令启用 `pipefail`；该目录保留 stdout/stderr、生成输入/Oracle 和离线 Maven 输出。

- `python3 scripts/docs.py check`：156 份 current 文档通过，见 `docs-check.log`。
- `PYTHONPATH=src:. python3 -m unittest -v tests.test_iteration_003_fixture`：10 项通过，7.529 秒，见 `test-iteration-003-fixture.log`。
- `PYTHONPATH=src:. python3 -m unittest -v tests.test_iteration_003_validation_assets`：5 项通过，2.966 秒，见 `test-iteration-003-validation-assets.log`。
- Maven `3.9.16`、Java `21.0.8`；冻结 Codex binary 为 `/Applications/ChatGPT.app/Contents/Resources/codex`，版本 `codex-cli 0.147.0-alpha.1.2`，digest `sha256:9f6748b4ab10ffc92c28b9ccedae89e61a302bbc011df7d276ee38f55906e481`。身份与 Git 边界见 `environment-and-lineage.log`。
- Maven 使用空 settings、独立 local repository、`--offline` 验证正式 identity fixture 与 metamorphic A/B reactor，均 `BUILD SUCCESS`；见三个 `maven-*-offline.log`。
- 相同 seed 独立生成两次得到相同 revision A/B、tree A/B、Oracle digest 和公开 POM 内容；Product 目录均不含 `oracle.json`，见两个 generation JSON 与 `metamorphic-determinism-and-isolation.log`。
- 全部冻结 JSON 通过 duplicate-key 拒绝加载；Product input 只有问题、selector、模式和语言，expected/oracle 只存在 evaluator suite；closed CE 的 7 个 Case 与 Product case ID 分离。Manifest path/ref/digest association、mall raw POM Oracle 和 generator 独立 import 由资产测试逐项检查。
- legacy DB `PRAGMA integrity_check` 为 `ok`。它仍包含 exact Snapshot `knowledge_snapshot_00000000000000000000000000000001`、Scope `scope_00000000000000000000000000000001`、revision 1、Schema `INITIAL@1`、Manifest digest `sha256:6ce176e7aba4be9214608f7d66f1f86ff476e8555d7a0e672be6e0e708a71b2a`、一个 Entity 和一个 Fact；两条记录均可沿 Evidence ref 读取 locator `src/LegacyOrderService.java:1`。见 `legacy-snapshot-readonly.log`。

人工逐项打开了 fixture 关键 POM、三个 Definition、mall Oracle、Product input/evaluator、closed CE suite、两条 baseline protocol、legacy report/DB 和 Verification Matrix。核对结论与冻结说明一致：root 与 child dependencies 均在 Coverage；两个同名 `common-lib` 必须按完整 GA/GAV 区分；A/B 为 7/11 与 8/14 的 Entity/Relation 图；why 问题只允许 Knowledge Gap；exclusion 报告不进入 Snapshot 答案知识。

## Result, failures and limitations

G0 最终结果为 **PASS**，V-001 已满足，G1 可以开始。

G0 首次机械测试虽通过，但人工命令核对发现成熟 Agent `1.0.0` 把 Codex 顶层参数与 `exec` 参数混在单一数组。`codex exec --ask-for-approval never --help` 在 exact binary 上退出 2；该失败保存在 `mature-agent-v1.0.0-negative-argv.log`。`FINDING-003-001` 将协议版本化为 `1.0.1`，冻结 argv 分区并新增真实 parse smoke；`codex --ask-for-approval never exec ... --help` 退出 0，见 positive log。最终 PASS 绑定修复后的 checkpoint，不能解释成 Q 中 `1.0.0` 原样通过。

本 Gate 没有外部模型分派，也没有选择 Provider/Adapter/Model、credential 或披露源码/结构结果。它不证明 typed Root/State、Publication、Source-off View、回答链、产品对照或浏览器体验；这些仍由 G1 及以后 Gate 独立阻断。

## Findings and system write-back

`FINDING-003-001` 已处置到 ITER-003 Verification：Manifest 改绑成熟 Agent protocol `1.0.1`，V-001 增加 exact CLI argv parse smoke，资产测试使用真实 answer schema 路径验证 exact binary。该发现不改变 System Contract，也没有产品代码变化。

## Validity / supersession

本结果只对授权 Q、执行 checkpoint `af849fb198179cfe1d1514f272a1a06236684f43`、Manifest digest `sha256:c857c11822b6b19d665be0101e74934b1758cb36de0b29d4f10aa4a21799deec` 和上列输入成立。任一 frozen asset、测试、工具 binary/version、Manifest association、mall revision/tree 或授权链变化都会使 G0 结果陈旧并要求重跑；后续 Gate PASS 不能删除本次失败记录。
