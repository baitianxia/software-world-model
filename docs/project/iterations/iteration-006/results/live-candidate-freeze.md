---
id: ITER-006-RESULT-LIVE-CANDIDATE-FREEZE
kind: iteration-result
status: executed-with-failed-live-result
authority: execution-evidence
owners: [engineering, quality]
depends_on: [ITER-006-VERIFICATION, ITER-006-RESULT-IMPLEMENTATION-VERIFICATION, ITER-006-FINDINGS]
code: [validation/structure_world_model_iteration_006/live_freeze.py, validation/structure_world_model_iteration_006/live_comparison.py, validation/structure_world_model_iteration_006/live_evaluator.py, validation/structure_world_model_iteration_006/live_product_probe.py, validation/structure_world_model_iteration_006/live_authorize.py]
tests: [tests]
iteration: ITER-006
---

# ITER-006 Live Candidate Freeze

## Decision

`run-003` 已把 ITER-006 Java 候选、随机化 held-out suite、独立 evaluator、三路 comparison protocol 与 disclosure boundary
冻结并通过 deterministic Gate。早先泛化“同意授权”被 external dispatch review 在调用前拒绝；随后用户给出绑定 exact
suite、两个目的地与 payload boundary 的完整授权，新授权文档生成并执行。真实 outcome 见
[Live run-003](live-run-003.md)：两套 baseline 各 6/6，World Model 4/6，V-008 FAIL。

本 Result 仍只拥有 freeze 事实，不由后续授权改写为 PASS，也不接受 Slice 或 Iteration。

## Exact subject and suite

- producer commit/tree：`1d194f9639a12194291f94914071dfe9128420b7` /
  `c718396b35586d7e6c33fc4996c08bb0e63df1e3`；
- producer source manifest：`sha256:023dc23c6296ed703b86a81764053758fbcde402bb4b8a1e91e2f7cb3a840780`；
- protected role-package stage：`sha256:d42b8bee0f8d33e10aaf81a29bb22593c8a8a1baa297aa189206eaf9a1032a19`；
- launcher manifest：`sha256:3a35e8f3d585093d83fa48f6a671bf1743a103396da55e0dc995363bac9fdc07`；
- deterministic qualification：`sha256:3335abaad138234b46c645cfc94aae98bf3ebaf58411e4b9027c7935aca52487`；
- held-out suite：`sha256:32de10fb1c13c3317c23c624c3fabfdafd909e8d6c4d9e23bad77b8f804aab60`；
- independent evaluator：`sha256:2f186c9d33317a37eec3f34bf6012eaa48ce4c77f59c6a6a018477c8026e18d3`；
- comparison runner：`sha256:d35cf82381d736c6a9255cd3b58e0a89521ccd4b194eeb35d1868a4de5082440`；
- freeze report：`sha256:05516188f9986607579d3e47def9b384722ad01aabcafd6b51180a4212e8cf97`。

suite 使用随机 suffix `5f781f57`，固定 6 题：method inventory、direct call、positive path、supported negative path、ordered
graph diff 与 runtime Knowledge Gap。R1/R2 revision 分别为 `a83fb578f782017980973169af20927d1089168e` /
`54899593be2b176f825c218e82148258e9649b69`；三个 Read Set 均由 suite 内 exact Java source closure 绑定。

## Comparison and disclosure boundary

执行顺序固定为 controlled Direct → Mature Source Agent → seal both baselines → World Model；每题每 surface 一次、controller
retry 为 0，失败全部保留且不筛选或插值。

| Surface | 外部任务上限 | 披露 payload |
|---|---:|---|
| World Model | 6 | original question + no-payload published Java Structure |
| controlled Direct | 6 | original question + 对应 exact sealed Java source closure |
| Mature Source Agent | 6 个 exact Codex task | original question + 隔离 workspace 中的 exact sealed Java source closure |

用户消息引用为
`codex-user-message:sha256:64d9829b734029652d99484a689be3fd54d9d749d49cf2260bdbe55ec55ad230`；comparison
authorization、disclosure authorization 与 product evaluation grant 的候选机器文档 digest 分别为
`sha256:68da9ca3ae5c1a211ac98b6edef56addfe85a4b544ae35ac6a2e9e7093f1a35c`、
`sha256:75e377dc1c91aa7dc77b4e7d6d753aff1dc368a1e17f84fed9c33f3391e70388`、
`sha256:1891ce3c78587df3cf9797e898458e01f967112eee5e79046544633e5af090d0`。这些文档未通过外部分派安全审查，属于
**non-operative** evidence，不能用于启动 comparison 或 product；取得更明确用户授权后必须生成绑定新消息的新文档。

后续明确授权引用为 `codex-user-message:sha256:4f48e0d5…`，机器文档与 live evidence 只记录在新目录
`var/iteration-006/live/run-003-live-explicit/`。它没有复用上述 non-operative 文档；完整 digest 见 live Result。

## Deterministic evidence and preserved failures

run-003 的 deterministic product probe 6/6 PASS；focused tests 53/53、protected candidate Answer tests 17/17、full regression
819/819 与 docs check PASS。授权前 comparison 与 product listener 均在创建输出/session/socket/listener 前拒绝，external model
calls 为 0，Production Activation 为 `NOT_EXECUTED`。

`run-001` 因 held-out inventory 题使用产品未声明的“全部方法”措辞而正确返回 Gap；`run-002` 已通过产品 probe，但 full suite
在受限 sandbox 中因 AF_UNIX 被 OS 拒绝而失败。两次失败均保留，未覆盖或伪装为 PASS；run-003 在允许本机 Unix socket、仍为
zero-provider 的受控环境重新随机生成并通过。
