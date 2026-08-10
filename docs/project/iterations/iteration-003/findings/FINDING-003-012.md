---
id: FINDING-003-012
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, security, quality]
depends_on: [ITER-003-SLICE-001, ITER-003-VERIFICATION, FINDING-003-010]
code: [src/software_world_model/application_services/world_model_answering.py, validation/structure_world_model_iteration_003/g3a, validation/structure_world_model_iteration_003/isolation/run_isolation.py]
tests: [tests/test_world_model_answering.py, tests/test_iteration_003_g2_isolation.py, tests/test_iteration_003_g3a_integration.py]
iteration: ITER-003
classification: verification
disposition: require-os-isolation-for-g3a-no-io-proof
target: ITER-003-VERIFICATION
---

# FINDING-003-012：应用计数不能单独证明 G3a 全局无 I/O

## Observation

G3a authority chain 的 `provider_call_count` 与 `network_operation_count` 只覆盖应用拥有的端口。
注入的 Python strategy callback 仍可能绕过端口直接执行文件、socket 或子进程 I/O，也可能对
Requirement/Draft/Review 作出语义上错误但结构有效的 Proposal。因此两个应用计数为零不是全局
无 Source/Evidence/network 证明，也不是 strategy/model qualification。

隔离烟测还发现当前 bundled Python 3.14.6 的 `_sqlite3` 通过 `@rpath` 读取
`sys.base_prefix` 的 sibling package；只开放 base prefix 会在产品 workload 前错误阻断运行时。
该路径是解释器动态依赖，不是产品输入，但必须作为显式、可审计 capability 记录。

## Evidence

- package-owned G3a deterministic workload 仅接收 exact Snapshot/ordered Bundles，产生 sealed
  authority page；独立 projector 只接收单向复制的 page 和零 Evidence payload marker Store。
- G2 的固定 deny-default Seatbelt harness 对 answer/projector 分别审计正常 workload 文件、网络
  和进程事件，并以独立 probe 验证 Source、Git、authority DB、Evidence Store、DNS/公网/TCP、
  Unix socket、subprocess 与跨角色访问被拒绝。
- runtime helper 始终只开放 exact `sys.base_prefix`；形如
  `pkgs/<distribution>/<version>` 的 bundled layout 另把 worker 实际需要的 OpenSSL、SQLite、zlib
  stable alias 分别解析为 canonical version root，拒绝开放包含其他工具的整个 `pkgs` root。
  exact executable、dependency alias/root/manifest、profile parameters 和实际 operation audit 都进入原始证据。

## Impact and classification

该发现提高 V-008 的证据下限，不改变 World Model Answering 或 Response Control 的 System
语义，分类为 `verification`。任意 strategy 的语义资格仍属于 V-009 CC/closed CE。

## Decision and disposition

V-008 必须分列两层证据：

1. authority chain 中应用拥有的 Provider/network port count 均为零；
2. package-owned deterministic strategies 在真实 macOS Seatbelt package+Bundle-only 环境运行，
   answer/projector 正常 workload 的 Source、Evidence、authority DB、Git、network、越界文件和
   process prohibited count 全部为零，且拒绝 probes 全部命中。

runtime capability 不得被描述为应用数据输入，其 root 不得包含受限产品数据；dependency root
必须逐项闭合并保存完整 namespace/content manifest，不能用 package-manager ancestor 代替。任何正常
workload 违规、probe 成功、额外输出、反向传递或 runtime root 漂移都使证据失败。

## Verification after disposition

`ITER-003-RESULT-G3A` 必须绑定 exact checkpoint、staged package/Bundle manifests、Python 与
Seatbelt identities、normal workload audit、deny probes、单向 seal transfer 和人工十阶段页面。
Result 只裁决 V-008；外部语义资格、Provider 披露和 G3b 仍保持阻断。
