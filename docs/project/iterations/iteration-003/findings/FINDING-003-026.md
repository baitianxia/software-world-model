---
id: FINDING-003-026
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-003-SLICE-001, ITER-003-VERIFICATION, FINDING-003-025]
code: [validation/structure_world_model_iteration_003/g3b/materialize_citations.py, validation/structure_world_model_iteration_003/g3b/run_g3b.py]
tests: [tests/test_iteration_003_g3b.py]
iteration: ITER-003
classification: local-implementation
disposition: import-citation-repository-from-owning-module-and-test-staged-cold-start
target: validation/structure_world_model_iteration_003/g3b/materialize_citations.py
---

# FINDING-003-026：Citation broker 的 staged cold start 依赖了未公开的聚合导出

## Observation

checkpoint `19a7462df9f3f59c3a94896f7ec0e48a22df8f84` 的正式 G3b dispatch 通过完整三角色
preflight，并完成第一个 Answer/Gateway run 的唯一 Provider 调用；两个正常 workload audit 与 summary 均为
PASS。随后 evaluator 启动可信 Citation broker 时，`materialize_citations.py` 从
`software_world_model.infrastructure` 聚合入口导入 `SqliteStructureKnowledgeRepository`，但该聚合入口没有导出
此内部 adapter，staged cold process 因 `ImportError` 失败，terminal 以 `POSTCONDITION` 失败关闭且没有选择性重试。

## Evidence

- 失败 dispatch 保存在
  `var/iteration-003/g3b/19a7462df9f3f59c3a94896f7ec0e48a22df8f84/dispatch`；
- `preflight.json` 记录 Answer/Gateway/Projector 全部 PASS、stage unchanged；
- run `01` 的 Answer/Gateway role report、summary 与 transport audit 均 PASS，Provider call/HTTPS dispatch 各为
  1，Source/Evidence payload/oracle/baseline 读取和正常 workload `connect`/`bind` 均为 0；
- `citations/01/evaluator/broker-stderr.log` 精确记录未公开聚合导出的 `ImportError`，尚未产生 Citation Store 或
  Projector Result；batch 在 1/60 后停止，`selective_retry_count=0`，Production Activation 为 `NOT_EXECUTED`。

## Impact and classification

根因是验证 broker 的局部 import 与 staging cold-start 覆盖缺口，不改变 Citation owner、Store 边界、Provider
协议、产品回答或系统安全契约，分类为 `local-implementation`。该 checkpoint 已产生一次产品 Provider 调用，旧
evidence root 必须原样保留，不能补写、复用或从第 2 个 run 继续。

## Decision and disposition

broker 改为分别从 owning module `sqlite_database` 与 `sqlite_structure_knowledge_repository` 导入两个 adapter，不扩大
`infrastructure.__init__` 的公共表面。聚焦测试使用与正式 runner 相同的 `_stage_packages` 和 isolated Python
入口，对 staged broker 执行 cold import/`--help`，从而在任何 Provider 调用前捕获聚合导出漂移。runner 同时把
role summary 验证与 Citation projection 区分为 `ROLE_POSTCONDITION` / `CITATION_PROJECTION` failure phase，保留
更精确的失败证据且不记录异常 payload。

## Verification after disposition

运行更新后的聚焦测试、完整回归与文档检查；随后形成新 clean checkpoint、新 prepared registry 和全新 dispatch，
从 60 个冻结 run 的第 1 个重新开始。旧 `19a7462…` batch 保持 FAIL，不能升级为 Product Result。
