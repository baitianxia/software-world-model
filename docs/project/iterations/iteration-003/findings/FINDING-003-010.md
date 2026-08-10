---
id: FINDING-003-010
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, architecture, security, quality]
depends_on: [ITER-003-SLICE-001, ITER-003-VERIFICATION, SYS-ARCH-DEPLOYMENT, SYS-QUALITY-SECURITY]
code: [validation/structure_world_model_iteration_003/isolation/run_isolation.py, validation/structure_world_model_iteration_003/isolation/probe_worker.py, validation/structure_world_model_iteration_003/isolation/workload_worker.py, validation/structure_world_model_iteration_003/isolation/answer_workload.py, validation/structure_world_model_iteration_003/isolation/projector_workload.py, validation/structure_world_model_iteration_003/isolation/answer.sb, validation/structure_world_model_iteration_003/isolation/projector.sb]
tests: [tests/test_iteration_003_g2_isolation.py]
iteration: ITER-003
classification: iteration-design
disposition: exact-seatbelt-capability-evidence
target: ITER-003-SLICE-001
---

# FINDING-003-010：macOS G2 隔离证明是 capability sandbox，不是 mount namespace

## Observation

本机 G2 运行环境是 macOS，不能用 Linux mount/network namespace 作为实际执行事实。当前验证器
使用固定 `/usr/bin/sandbox-exec` 和两个独立 deny-default Seatbelt profile：它拒绝全部网络、
fork 和未授权文件操作，但宿主机上的拒绝目标仍存在于全局文件系统 namespace。Python 进程还
必须读取精确解释器、运行库、动态加载器、随机设备与时区文件，并需要一组 literal ancestor
directory 权限穿越到 canonical allowlisted roots。因而“文件 allowlist 只有 package + Bundle”
只能准确描述应用/产品输入，不能描述进程的全部 OS 文件 capability。

## Evidence

- `answer.sb` 与 `projector.sb` 均为 `(deny default)`、`(deny network*)` 和
  `(deny process-fork)`；分别开放不同的 package/input/output roots。
- 两个 profile 只对 canonical root 的 ancestor directory 给出 `literal` read，用于目录穿越；
  Seatbelt 的 `file-read*` 因而允许枚举这些 exact directory 的直接条目名，但不以 `subpath`
  开放其子文件内容。递归 runtime reads 只包括 `/System/Library`、`/usr/lib`、
  `/private/var/db/dyld`、exact Python runtime 以及各角色自己的根。
- `run_isolation.py plan` 固定输出 `NOT_EXECUTED/NOT_EVALUATED`；只有 `run` 模式确认 Darwin、
  固定 sandbox executable/profile/worker，以 `-I -S -B` 禁止 user site、`site` 与 `.pth`
  启动代码，完成外部可达性 preflight 并真实启动 child，才可
  形成 OS isolation evidence。
- Worker 分别验证 authorized package/Bundle 或 seal/Store read 和独立 output write；同时主动
  探测 Source remote、公网 IP、DNS、本机 TCP、Unix socket、越界文件、SQLite、Git 文件/进程、
  subprocess 与 Answer↔Projector callback，全部必须由 OS 拒绝。

## Impact and classification

现有 System Contract 已要求默认拒绝的文件/网络能力边界；发现没有改变 Owner、正式输入或安全
下限，只把本轮 Slice 的 Linux 化机制措辞收敛为本机可真实执行和审计的 macOS enforcement。
因此分类为 `iteration-design`。若仍把“未挂载/没有 namespace route”作为字面 Oracle，当前
Seatbelt 运行不能证明它，必须更换 VM/container executor，不能在 Result 中把 capability denial
改写成 mount namespace 事实。

## Decision and disposition

V-007 对本机 G2 使用 exact Seatbelt capability claim：answer 的应用输入只有 package 与
no-payload Bundle，Projector 的应用输入只有 package、sealed Result 与 exact disposable
Citation Store；两者另有独立 output root。解释器/runtime subpaths、固定系统 runtime
subpaths、精确设备/时区文件和 canonical root ancestor literals 必须由 plan 完整列举并以 profile
  digest 绑定；ancestor literal 允许路径穿越、metadata 与该 exact directory 的直接条目名枚举，
  但不代表其子文件可读。该名称披露必须作为本机 executor limitation 进入证据；若名称本身也属
  机密，则必须改用自包含 staged launcher 或 VM/container executor。目标仓库、原工作树、权威/旧
数据库、Evidence Store 与另一角色的输入/输出根不得落入任何 recursive allow root，并必须用
外部 preflight + sandbox 内拒绝探测证明不可读。

网络验收改写为 OS-enforced deny-all，而不是声称创建了 network namespace 或删除宿主 route。
每个角色的固定 digest-bound probe child 与产品 workload child 必须分开执行；产品代码不得在
trusted probe report 密封前后进入同一解释器。两角色 workload 都必须真实执行且 PASS，最终
output manifest 必须与声明集合精确相等；probe-only、plan、mock 或 worker 自报都不能完成
V-007。原始 isolation report 保持 `v007_gate_status=NOT_EVALUATED`，由结合 Bundle/View/引用和
人工核对的 Gate Result 作最终裁决。

## Verification after disposition

保存 profile/worker/executable digest、完整 capability parameters、staged input/output manifests、
外部 preflight、两个不同 PID/nonce/command/environment、每项 allow/deny probe、workload output、
单向 seal transfer 和运行前后 protected-input digest。任何 runtime root 漂移、allow root 重叠、
symlink、额外 Store 文件、网络成功、反向连接、workload 未执行或输入变化均使本次 G2 证据失败。
