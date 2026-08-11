---
id: ITER-003-RESULT-G4
kind: iteration-result
status: pass
authority: evidence
owners: [product, project, quality]
depends_on: [ITER-003-RESULT-G3B, ITER-003-VERIFICATION, ITER-003-SLICE-001, FINDING-003-029]
code: [validation/structure_world_model_iteration_003/g3b/build_browser.py, src/software_world_model/interface/world_model_product.py]
tests: [tests/test_iteration_003_g1_integration.py, tests/test_iteration_003_g3b.py, tests/test_world_model_product.py]
iteration: ITER-003
---

# ITER-003 Result：G4 Human and Product Acceptance

## Verdict and exact subject

G4 最终裁决为 **PASS**。人工验收对象是 product checkpoint/tree
`b9b329a9b341b01fc41486ef9b0c809ac8665332` /
`43accc44508a1cce9066aead258ec11a5b6a4ef0` 的不可变 `EVALUATION_ONLY` 浏览器工件；它只读取新 G3b
batch `sha256:bf8ca1fe4c4e8861b3edb7a9853eb33f1536f5ee2a2bcfb90b38f1ac0bffc632` 的 60 个密封成功终态。

前置独立 evaluator checkpoint `9977269b246114810b431adb00207f286ec951ac` 已给出 60/60 PASS、重大错误
0、边界与性能 PASS。G4 不重新评分或修改任何 terminal，只在真实浏览器中核对其交付页面、交互和更新隔离。

## Immutable browser artifact

`build_browser.py` 对 batch、terminal、Answer summary、page digest 和每个 Citation Projection reference
逐项验签后生成 60 页索引：

- browser index document digest：
  `sha256:2989c45ec45e0d262ae7362b347e92586653eae96774303cfe3aed960f3aa819`；
- browser index raw SHA-256：
  `3c2d9480303152ee3cea9560cc98fed74b33084617de03ca69d3bcf43159b488`；
- mode=`WORLD_MODEL`，environment=`EVALUATION_ONLY`，run_count=60；
- 本地只读服务仅绑定 `127.0.0.1`，验收完成后已关闭；未构建 live/production route。

原始工件与人工记录位于
`var/iteration-003/g3b/b9b329a9b341b01fc41486ef9b0c809ac8665332/browser/`；`manual-review.md`
SHA-256 为 `c34f42eb954515e787218054463b0ed060ece150b30a7277d9e5e6a5b6607070`。

## Visual, interaction, and content review

Codex in-app browser 的实际页面检查为 PASS：

- 首屏永久显示 `EVALUATION_ONLY` 水印、`WORLD_MODEL`、exact product commit、原问题/答案、Provider 与网络
  operation、Snapshot 数、10 阶段 Authority、Session/Read Set/Bundle、Profile、Coverage、modality、limitation、
  Citation 和 sealed payload；桌面布局没有遮挡或必需内容截断；
- A/B/全部切换的 visible View labels 分别为 `A,A` / `B,B` / `A,B,A,B`，恢复后与初始相同；
- 点击 Citation 只发出浏览器到独立 projection JSON 的请求；所检 projection 含 10 个 locator/Artifact identity，
  不含 Evidence excerpt；
- canonical/paraphrase 的路径、diff、root direct dependency、scoped negative、同名 GA、修复后的完整 root GA、
  Knowledge Gap，以及 runtime-random Root/State/topology/同名 identity 页面均逐项核对；
- `WM-PRODUCT-007` 页面显示 source=`org.example.root:structure-fixture`、shared edge=true、
  dependencyManagement edge=false；unsupported why 页面诚实显示
  `CHANGE_INTENT_OUTSIDE_STRUCTURE_COVERAGE` 且没有正文 Citation button；
- 浏览器 console warning/error 均为 0。静态服务仅额外收到浏览器自动发出的可选 `/favicon.ico` 404；应用未引用
  favicon，且不影响任何必需资产、页面或交互。

## Independent update and old-session stability

页面保持打开时，`tests.test_iteration_003_g1_integration` 以独立临时数据库完成零 Question/Task/Session 的
A1→B→A2 update，1/1 PASS。随后重新选择原页面，Session 在前后均为
`structure_read_session_aa0c6090268f4d78bd8eaa9dba5bd0c1`，Read Set 仍为
`sha256:953fc5cd34e5ec70bc359d89083b6f7084605261228498d58bd63cb01e761e76`，product commit 和 SUCCESS
终态也未漂移。

## Regression and boundary

在 evaluator checkpoint `9977269…` 上：

- G3b/V-009 聚焦回归 46/46 PASS，日志 SHA-256
  `01951321f1f6f2caddbb4dd280832d1628c78b5c1636658c34adc5c8241bd240`；
- 完整回归 750/750 PASS，日志 SHA-256
  `6ceecbc8381d559080a58db1077f4915fecf14e249cbc16a52d9ddfbe8cbc076`；
- 日志路径为 `var/iteration-003/g3b/9977269b246114810b431adb00207f286ec951ac/postaccept/logs/`。

G4 只接受本机 Maven Structure World Model 的评测交付。它没有执行 Scheduler、旧 Scope Schema Migration、
多源融合、本机默认路径切换或 Production Activation；Production Activation 始终为 **NOT EXECUTED**。
