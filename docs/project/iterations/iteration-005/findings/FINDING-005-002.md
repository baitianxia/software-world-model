---
id: FINDING-005-002
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, project]
depends_on: [ITER-005-SLICE-002, ITER-005-READINESS]
code: []
tests: []
iteration: ITER-005
classification: iteration-design
disposition: split-pre-coding-contract-freeze-from-pre-listen-implementation-seal
target: ITER-005-SLICE-002
---

# FINDING-005-002：新增 launcher 的实现 digest 无法在编码前存在

## Observation

SLICE-002 原文同时要求新增 `software_world_model.interface.world_model_http`，并要求在授权编码前固定该 launcher 的 exact
file digest。目标文件尚未实现，因此两个条件形成循环：不编码无法产生 bytes，未产生 bytes 又不得编码。

## Evidence

- SLICE-002 的 public module、请求边界与启动参数已经由 Development Design 冻结；
- 当前工作树在授权点不存在 `src/software_world_model/interface/world_model_http.py`；
- Answer/Prompt/Strategy、Gateway、Broker、Projector、role worker、sandbox profile 和 Provider qualification 已有接受过的
  exact package/digest，可在不调用 Provider 的情况下先固定；
- 新 launcher 会改变 trusted assembly 和动态数据集发现，因此旧 ITER-003/004 Product Result 不能替代实现后的重新密封、
  preflight 和新仓库 Product Validation。

## Impact and classification

该问题不改变 System Owner、安全边界或外部接口，只影响本轮门禁的可执行顺序，分类为 `iteration-design`。

## Decision and disposition

门禁拆成两个不可互相替代的阶段：

1. 编码前冻结 public contract、继承的 exact role package、Provider/资格 subject，并由用户授权 SLICE-002 编码；
2. 实现完成后、任何监听或真实外部分派前，密封新增 launcher/runner/profile 的 exact provenance，重跑启动资格与 OS
   preflight；未密封或漂移时必须拒绝监听。

真实 World Model、controlled Direct 与成熟 Source Agent 的问题披露仍需单独用户授权，编码授权不能推导该权限。

## Verification after disposition

Manifest、Readiness、SLICE-002 与 `project/current.md` 已写入上述顺序。对应 fail-closed 启动校验由
`tests/test_world_model_http.py` 和 V-007 证据闭合。
