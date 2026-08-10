---
id: FINDING-003-013
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, security, quality]
depends_on: [ITER-003-SLICE-001, ITER-003-VERIFICATION, FINDING-003-011, FINDING-003-012]
code: [src/software_world_model/interface/world_model_evaluation.py, validation/structure_world_model_iteration_003/g3a, tests/test_iteration_003_g3a_integration.py]
tests: [tests/test_world_model_answering.py, tests/test_world_model_evaluation.py, tests/test_iteration_003_g3a_integration.py]
iteration: ITER-003
classification: verification
disposition: require-out-of-band-page-and-checkpoint-provenance
target: ITER-003-VERIFICATION
---

# FINDING-003-013：公开摘要只能证明一致性，不能自行证明评测页来源

## Observation

评测页内部 record/page digest 都是公开、无密钥的确定性摘要。读取端即使逐层复算 ID、digest 和
cross-link，也只能拒绝不一致篡改；能够同时重签全部公开摘要的一方仍可伪造语义上不同但内部一致的
页面。`implementation_commit` 若只检查 40 位格式并由 Answer/Projector 原样传递，也可能把当前
package 错标为另一个 commit。

审计还发现 Python 的 `bool` 是 `int` 子类；只用 truthiness 或 `==` 会让 `0/1` 冒充离线计数、
fidelity、assessment 或截断标记。该问题属于同一类“结构看似一致但缺少精确输入权威”的验证缺口。

## Evidence

- 协调修改 Answer body、Delivery、chain/page digest 的反例曾被旧 reader 接受；修改
  `implementation_commit` 后重算 page digest 也会被 Projector 原样输出。
- 以全零 40-hex commit 调用旧 staging 路径能够生成带错误标签的 isolation config。
- 重签 `OfflineStrategyInvocation`、Requirement/Assessment 和 `StructureViewResult` 的反例证明
  `False == 0`、`True == 1` 会绕过非精确类型检查。

## Impact and classification

System Contract 已要求完整权威链与 exact checkpoint；发现不改变 owner 或产品语义，而是提高
V-008 对来源、重放和精确 scalar 的证据下限，因此分类为 `verification`。

## Decision and disposition

1. evaluation reader 和独立 Projector 必须同时接收调用方带外冻结的 exact implementation commit
   与 PAGE digest；文件内摘要不得充当自己的来源锚点。
2. PAGE digest 在 staging 前由独立 connected mall chain 经递归 `require_valid()` 后生成；connected
   与 isolated workload 的全部确定性输入/strategy identity 保持相等，Projector argv 在运行前冻结。
3. staging 必须证明环境 commit 等于 clean Git `HEAD`、记录 exact tree，再复制 package；最终证据还
   要逐文件比较 staged package 与 checkpoint。
4. authority DTO、Result 和页面边界的 bool/int 必须按 exact Python type 验证，不能依赖 truthiness
   或数值相等。

内部十阶段重建仍作为 defense-in-depth，但不宣称公开 hash 能抵抗完整重签。任一 anchor、Git
lineage、package byte comparison 或 exact scalar 检查失败都使 V-008 失败。

## Verification after disposition

`ITER-003-RESULT-G3A` 必须保存 pre-run config、connected expected PAGE digest、isolated actual digest、
Projector anchor comparison、clean checkpoint/tree、staged package comparison和协调篡改反例。该
provenance 只裁决离线 V-008，不构成外部 Provider/Model 资格或披露授权。
