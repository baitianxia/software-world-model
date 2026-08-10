---
id: FINDING-003-011
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, architecture, quality]
depends_on: [ITER-003-SLICE-001, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL]
code: [src/software_world_model/application_services/world_model_answering.py, src/software_world_model/interface/world_model_evaluation.py]
tests: [tests/test_world_model_answering.py, tests/test_world_model_evaluation.py, tests/test_iteration_003_g3a_integration.py]
iteration: ITER-003
classification: iteration-design
disposition: g3a-evaluation-only-parallel-authority-chain
target: ITER-003-SLICE-001
---

# FINDING-003-011：G3a 需要显式隔离于既有生产 Response Control

## Observation

既有 `response_control.py` 面向持久 Task、Use/qualification、permission、Adapter dispatch 与
迟到 Receipt 恢复；其 owner 读取路径也假定连接正式知识和持久仓库。G3a 的输入则只有调用方
冻结的有序 no-payload Structure Read Bundle，需要逐步展示 Requirement、candidate、Query、
Assessment、Draft、Review、Authorization 与 Delivery。直接复用既有入口会缺少 ordered Read Set
authority，或把尚未取得外部资格和生产授权的测试路径误写成 live Response Control。

## Evidence

- `world_model_answering.py` 新增 process-local immutable authority store、Bundle-only query owner、
  独立 generation/review invocation、稳定 digest 链和唯一 `EVALUATION_ONLY` sink。
- `world_model_evaluation.py` 只投影已交付且递归校验通过的十阶段 authority chain，并拒绝
  Evidence payload/Source/network 字段。
- fault tests 证明 Need 遗漏、伪造/0/N/跨 Session candidate、Result/Assessment/Claim/Receipt
  篡改、self-review 与未授权 Delivery 均失败关闭；真实 mall A1/B Bundle integration 不读取
  Source 或正式数据库。

## Impact and classification

该发现改变本轮 G3a 的实现路径，但不改变 System Contract：Response Control 仍是 live/product
响应的唯一 owner；新增路径只是确定性离线评测 authority。因而分类为 `iteration-design`。

## Decision and disposition

G3a 使用独立 `WorldModelResponseControlService`、process-local store 和 exact
`EVALUATION_ONLY` sink。它不得接入产品 Delivery Adapter，不授予 production activation，也不
证明外部 strategy/model 资格。若后续把该链接入 live 路径，必须重新闭合既有 Task、Use Epoch、
qualification、permission、persistent dispatch 和 late Receipt authority，不能由本 Finding 或
G3a Result 自动提升。

## Verification after disposition

V-008 只验收 deterministic offline chain、十阶段人工投影、fault closure 与 OS no-I/O 证据。
V-009 仍须在单独披露确认后冻结 exact Provider/Adapter/Model、egress policy、credential 与
Conformance/closed CE；G3a PASS 不解除这些阻断。
