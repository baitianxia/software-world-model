---
id: ITER-005-RESULT-SLICE-002-CANDIDATE-FREEZE
kind: iteration-result
status: candidate-requalified-live-gate-subsequently-passed
authority: execution-evidence
owners: [engineering, quality]
depends_on: [ITER-005-VERIFICATION, ITER-005-FINDINGS, ITER-005-RESULT-SLICE-001, ITER-005-RESULT-SLICE-002-RUN-006, ITER-005-SLICE-002]
code: [src/software_world_model/interface/world_model_http.py, src/software_world_model/interface/world_model_browser.py, src/software_world_model/interface/world_model_browser_ui.py, src/software_world_model/interface/world_model_product.py, src/software_world_model/interface/world_model_runtime.py, src/software_world_model/interface/world_model_runtime_assets/gateway_authorized_workload.py, validation/structure_world_model_iteration_005/slice2_freeze.py, validation/structure_world_model_iteration_005/slice2_product_probe.py, validation/structure_world_model_iteration_005/slice2_comparison.py, validation/structure_world_model_iteration_005/slice2_evaluator.py]
tests: [tests/test_world_model_http.py, tests/test_world_model_browser.py, tests/test_world_model_evaluation_grant.py, tests/test_world_model_gateway_authorization.py, tests/test_world_model_product.py, tests/test_iteration_005_slice2_comparison.py, tests/test_iteration_005_slice2_evaluator.py, tests]
iteration: ITER-005
---

# SLICE-002 Dynamic World Model Candidate Freeze

## Decision

`run-007` 在本次 freeze 时通过 SLICE-002 的确定性 candidate qualification，从而可以请求当前用户对该 exact suite 的
evaluation disclosure 作单独授权。它是在 `run-006` live gate `FAIL` 后按 `FINDING-005-009/010` 重新密封的候选；freeze
命令显式移除了 `ARK_API_KEY`，external model call 为 0。此后该 exact suite 已取得授权并完成 live gate，结果见
[Run-007 Live Result](slice-002-run-007-live.md)；本 freeze 自身仍不接受 SLICE-002 或 ITER-005，也不授权或执行 Production
Activation。

## Exact candidate subject

正式候选目录为 `var/iteration-005/slice-002/run-007/`，主报告 document digest
`sha256:ba65d6d01b2b6bc78fc6ba80a7d0c8896f61099d9b7471e4c446c3fecec71bf3`。当前实现尚未成为主仓库 clean commit，runner
把实际 `src/` 与 `pyproject.toml` 复制到隔离 provenance Git repository：

- producer commit `0c2b155d42a272d1b2172f5a82c41179855cd44d`；
- producer tree `f505499ef4a1891c43eeddb689812a2a660693e7`；
- source manifest `sha256:252e868e4295b7a99eaee042e22f7edf64cc29604f222839437f22cffd1540cd`；
- protected candidate stage `sha256:7cf5e8322af4ecd6a0f97be316229937f9cd8e09813b741e9cef332bea2476e8`；
- launcher manifest `sha256:30205910e8676c10766fd68870affb2cc6eb17e68292ae4c09093a083a08ad8d`；
- deterministic qualification `sha256:ce1ab384ab5445b1ebd9cedf43d4ed6367c26e42e5ec44f9ad08a950e1ee2dd4`。

candidate stage 相对 accepted baseline 只改变 Answer 的 `world_model_product.py` 与 Gateway 当前授权 wrapper。Prompt、Strategy、
Provider subject 继续绑定 accepted qualification；正式 launcher、runtime assets、role entrypoints、stage 与 Gateway inputs 均由
grant/qualification 的 raw digest 重新绑定。

## Randomized repository and sealed questions

本次 seed 为 `ef70ab74739ed0191018a85faf99c45a`、suffix 为 `889c635e`，R1/R2 revisions 分别为
`d961fcf5a41000a24fc291b6226de03de1c26d7c` 与 `f1a48ab5fd4280079f87649abc870d998011da2b`。single R1、single R2、
ordered R1→R2 Read Set 分别为 `read_set_40b58d420ddf5ddcf31133c0c1d79005`、
`read_set_fed0740ef3d736d2412376e670ce885c`、`read_set_0fba1ece3cd4eaf282c7721b2ad94916`。

`SWM-WORLD-MODEL-HELD-OUT-SUITE@2` digest 为
`sha256:04f50cae8392296d8173921e56063abded7d66c33c17d97019d50ac965b9f884`。它在任何 external result 前密封 9 个与
`run-006` 同构但标识随机化的问题，以及每个 Read Set 的 exact POM closure。comparison controller 不把 suite 的
expected/required/forbidden/Oracle 字段写入任何 external input packet。exact disclosure-set digest 为
`sha256:803bb541c8c717a89e5757585babfbc1db2c272189d16d816c0c1ff61502380f`。

## Comparison protocol and authorization boundary

independent evaluator digest 为 `sha256:020287ba519bc3ff665d805d6360a645cd1e3b7b78c08f6297fbbf75d2d63529`，
comparison runner digest 为 `sha256:e3da9685a12903de71fffd950648f20a4b1d23fedfb90204488cf136b817364a`。顺序仍固定为
controlled Direct → Mature Source Agent → seal both baseline populations → World Model；每 surface 每题只运行一次，controller
retry 为 0，全部失败保留且不插值/筛选。

controlled Direct 新 protocol 显式密封 4096 output token 与
`STRICT_JSON_OBJECT_ANSWER_STRING_NO_TRAILING_TEXT`，用于修复 `run-005/006` 证明的截断和隐含序列化缺陷；问题、POM
closure、Provider、调用次数和 evaluator 不变。

| Surface | 外部任务上限 | 可观测 Provider calls | 披露 payload |
|---|---:|---:|---|
| World Model | 9 | 最多 9；每个 verified success terminal exact 1 | original question + no-payload published Structure |
| controlled Direct | 9 | 最多 9；每个 success terminal exact 1 | original question + 对应 exact sealed POM closure |
| Mature Source Agent | 9 个 exact `codex exec` task | CLI terminal 不可精确观测，记录 `null` | original question + 隔离 workspace 中对应 exact sealed POM closure |

Mature subject 固定 Codex CLI `0.147.0-alpha.1.2`、binary
`sha256:9f6748b4ab10ffc92c28b9ccedae89e61a302bbc011df7d276ee38f55906e481`、model `gpt-5.6-sol`、reasoning `low`、
root deny、exact workspace read、network deny、shell environment inherit-none。

pending comparison authorization 为
`sha256:3bbf4c01b79fa6130a9be1f9138b617e205714d11660db064fb46cb8ea6f2117`，pending product grant 为
`sha256:2eacfec68ca42cd47018a6972a3f8bb1dc8a5d93fd785e14220c7af460ef5d5d`。两者均为未授权；runner 在创建 output 前拒绝，
产品命令在创建 session/socket/listener 前拒绝。用户对 `run-006` 的授权只绑定 suite `sha256:ece08225…`，不能复用于本 suite。

## Deterministic qualification

- 9 条 sealed question 全部通过 formal proposal stub product probe；digest
  `sha256:bb75e610255c762d7522a6b1a95ee5658b073e5e3436e8ac4a8458059cb9be31`；
- 动态 Catalog/authority adapter probe digest
  `sha256:99c4717d901ee5d482406ea09094b6e5bfe3d82a2f72d0bedc56cc569f83f7c9`；
- focused tests 51/51 PASS；protected stage 的 exact Answer package tests 13/13 PASS；
- 允许本机 AF_UNIX 的 full regression 801/801 PASS；
- `python3 scripts/docs.py check` PASS；
- stage 测试前后 digest 不变；comparison unauthorized pre-dispatch 与 product unauthorized pre-listen 均 PASS；
- external model calls 为 0，Production Activation `NOT_EXECUTED`。

首次在受限工具 sandbox 内生成的部分目录已保留为
`var/iteration-005/slice-002/run-007-freeze-failed-sandbox-001/`；其 full suite 因 AF_UNIX 创建被环境拒绝而中止，不是候选
PASS。正式 `run-007` 在允许本机 Unix socket 的受控环境重新随机生成并完整通过，没有覆盖失败证据。

## Preserved evidence and subsequent gate

`run-006` 的授权、三条 population、baseline seal、comparison `FAIL` 与真实浏览器 PASS 均由
[Run-006 Live Result](slice-002-run-006-live.md) 保存，没有重试或覆写。随后用户对 `run-007` exact suite 作了新授权；三条
external population、independent evaluator 与真实浏览器复核已按 sealed 顺序执行并全部 PASS，由
[Run-007 Live Result](slice-002-run-007-live.md) 保存。该后续 PASS 不改变本文件所记录的 pre-dispatch freeze 事实，也不执行
Production Activation。
