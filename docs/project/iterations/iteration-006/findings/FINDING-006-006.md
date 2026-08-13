---
id: FINDING-006-006
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-006-SLICE-001, ITER-006-VERIFICATION]
code: [validation/structure_world_model_iteration_006/live_freeze.py]
tests: [tests]
iteration: ITER-006
classification: verification
disposition: preserve-sandbox-failure-and-rerun-in-af-unix-capable-environment
target: ITER-006-VERIFICATION
---

# FINDING-006-006：完整回归需要可创建本机 AF_UNIX socket 的环境

## Observation and evidence

run-002 的 Java fixture、product probe 和 focused tests 已通过，但受限工具 sandbox 拒绝 AF_UNIX bind/connect，导致既有
Model Egress Gateway 与 G3b socket tests 报错；同一 819 项 suite 在允许本机 AF_UNIX 的受控环境全部 PASS。新的产品
re-freeze `run-006` 再次复现同一环境限制：835 项中出现 6 error/1 failure；同一候选在只增加本机 AF_UNIX 能力的 `run-007`
环境 835/835 PASS。

## Classification and disposition

失败属于 verification environment，不是产品实现失败。run-002/run-006 原样保留且不算候选 PASS；run-003/run-007 在沙箱外
仅取得本机 AF_UNIX 能力，freeze 仍不调用 Provider，并重新随机化、重新运行全部 Gate 后才成为正式候选。以后不得把 sandbox
socket 拒绝改写为测试 PASS，也不得仅跳过相关测试。
