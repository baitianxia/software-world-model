---
id: FINDING-003-027
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-003-SLICE-001, ITER-003-VERIFICATION, FINDING-003-026]
code: [validation/structure_world_model_iteration_003/g3b/evaluate_results.py]
tests: [tests/test_iteration_003_g3b.py]
iteration: ITER-003
classification: iteration-design
disposition: seal-descendant-evaluator-checkpoint-with-closed-non-product-delta
target: ITER-003-SLICE-001
---

# FINDING-003-027：人工维护的冻结 Oracle 不是 canonical JSON 运行收据

## Observation

product checkpoint `7933712d7d00d113abe0ec147729fa41562bea76` 的新正式 batch 完成 60/60 SUCCESS、
零失败、零选择性重试，随后独立 evaluator 在扫描单个 terminal 前读取
`mall-structure-1.0.0.json` 时失败。该文件是按原始文件 SHA-256 冻结的 pretty-printed 人工 Oracle；evaluator
却复用了只适用于机器运行收据的 canonical-JSON loader，因缩进和末尾换行拒绝了内容。两个 Oracle 的原始摘要
仍与冻结 Product Suite 的 registry 完全一致，未发生语义或字节漂移。

## Evidence

- 正式 batch 位于
  `var/iteration-003/g3b/7933712d7d00d113abe0ec147729fa41562bea76/dispatch`，其 batch digest 为
  `sha256:be7b87be4941f36afef19a3e86547bad70d017870021d229503238042835c185`，60 个 terminal 均为
  SUCCESS，preflight/stage integrity PASS，Production Activation 为 `NOT_EXECUTED`；
- Product Suite 原始摘要为 `sha256:c165af6b…`，其 Oracle registry 固定 mall
  `sha256:412d2e03…` 与 identity `sha256:b02e4414…`；宿主重算结果逐字节相同；
- evaluator 在 `_load(MALL_ORACLE)` 抛出 `document is not canonical JSON`，没有创建 Product Evaluation
  Result，也没有发起网络、Provider 或模型调用；
- evaluator 的既有 `_load_relaxed` 已对同类冻结 baseline plan 使用 duplicate-key-safe 的格式无关解析，说明错误是
  loader 分类而非 Oracle 内容。

## Impact and classification

修复不会改变产品 runtime、60 个请求、Snapshot/Read Set、问题、Oracle、baseline comparator、隔离 profile 或任何
terminal；但它要求把“产品执行 checkpoint”和“事后独立 evaluator checkpoint”显式分列，改变本轮 Gate 的证据
路径而不改变 System 契约，分类为 `iteration-design`。仅把新 evaluator 冒充产品 implementation commit 不可接受；
仅因本地 loader 错误再发送 60 次相同外部 payload 也会增加未必要的披露与成本。

## Decision and disposition

Product Suite 和两份人工 Oracle 先按冻结的原始文件 SHA-256 与 exact registry 校验，再以拒绝 duplicate key 的
格式无关 JSON loader 解析；机器生成的 batch、terminal、timing、preflight 和 Result 仍强制 canonical JSON。

独立 evaluator 允许在 product checkpoint 的 descendant clean commit 运行，但 Git delta 必须严格闭合为
evaluator 自身、对应测试以及 Finding/Slice/Matrix/派生索引，禁止任何 `src/` 产品 runtime、G3b runner/profile、
prepared input、Product Suite、Oracle 或 baseline 变化。evaluator 在扫描 individual terminal 前先以 O_EXCL 密封
invocation，记录 product/evaluator commit+tree、evaluator script digest、closed delta、batch/prepared/comparator
digest 与 Product Suite/Oracle 原始摘要。`product-evaluation@2` 同时绑定两个 checkpoint 和 invocation digest。

因此保留 `7933712…` 的完整 60-run batch并对其执行修正后的纯本地独立评估，不再产生 Provider 调用。该处理不是
选择性产品重跑，也不能单靠 batch SUCCESS 宣称 G3b PASS；只有新 evaluator 的全部 oracle/baseline/isolation/
performance 裁决 PASS 后才可继续浏览器验收。

## Verification after disposition

新增 pretty-printed + exact raw digest 正例、字节篡改反例和 product-runtime delta 拒绝测试；运行聚焦、完整回归与
文档检查。在 descendant clean evaluator checkpoint 上密封 invocation并评估 immutable `7933712…` batch，确认
整个过程 `external_model_called=false`、Production Activation=`NOT_EXECUTED`。
