---
id: ITER-006-RESULT-PRODUCT-CANDIDATE-FREEZE-RUN-007
kind: iteration-result
status: executed-with-failed-live-result
authority: execution-evidence
owners: [engineering, quality, security]
depends_on: [ITER-006-RESULT-JAVA-CAPABILITY-RUN-002, ITER-006-VERIFICATION, FINDING-006-006, FINDING-006-011]
code: [validation/structure_world_model_iteration_006/live_freeze.py, validation/structure_world_model_iteration_006/live_comparison.py, validation/structure_world_model_iteration_006/live_evaluator.py, validation/structure_world_model_iteration_006/live_product_probe.py, validation/structure_world_model_iteration_006/live_authorize.py]
tests: [tests]
iteration: ITER-006
---

# ITER-006 Product Candidate Freeze run-007

## Decision

Java capability `PASS_VALID` 后，`run-007` 已把新的产品候选、六题 held-out suite、独立 evaluator、三路 comparison protocol、
role packages 与 disclosure boundary 重新冻结。deterministic product probe、55 项 focused tests、18 项 protected candidate Answer
tests、835 项 full regression 和 docs check 全部 PASS；未授权 comparison pre-dispatch 与 product pre-listen gate 均 PASS。

这是 **candidate freeze，不是 live result 或 Acceptance**。`live_dispatch_authorized=false`，没有外部产品模型调用，没有 Codex task，
没有 Java source closure 披露，Production Activation 与 Git stage/commit/push 均未执行。冻结只对本机 Codex CLI 做 `--help` 参数
解析检查，不创建任务、不发送问题或源码。

## Exact candidate and suite

- producer commit/tree：`d5ae049a8d103300a35f83ae159ee66d07bfb3a1` /
  `c6c3ea41fd00e558e13858541328beb62df78e6f`；
- producer source manifest：
  `sha256:01821d6d9027579916258a4cc6e6b196993307b4c872810536677df83e727813`；
- protected candidate stage：
  `sha256:15183e2a8a357e7e973ab6d0530ebe64eed9716e716fbcd8a42aec019f47edaf`；
- held-out suite：
  `sha256:66192cdfe9fd2f437d480d3f13426aea82520740cb51f7317988861577975df0`；
- independent evaluator：
  `sha256:bb972939badfbebf8f0f3365e86a0ffc841bf70b38466f247f3aad383bbb7e03`；
- comparison runner：
  `sha256:d35cf82381d736c6a9255cd3b58e0a89521ccd4b194eeb35d1868a4de5082440`；
- deterministic qualification：
  `sha256:72d70e87f2bc607e1acfbd43d5998b500a472398fa8398eb765cd69b9e8fd79f`；
- Java product Gateway freeze：
  `sha256:c1d54d18d3eaea8aa4241192301695ee74b92b6a1054c3a1b182ddbe06dac8f2`；
- freeze report：
  `sha256:c9bebe0686bf69702263a6e9316585d3dd54665ec24c2cf6457fe7861e7c0dee`。

suite 在 World Model result count 为 0 时密封，包含 method inventory、direct call、positive path、supported negative path、ordered
diff 与 runtime Knowledge Gap 六题。suite raw SHA-256 为 `30f86d30…`；report raw SHA-256 为 `3d5d9ede…`。原始问题、Oracle、
source closure 与所有运行目录只保存在本机 `var/iteration-006/live/run-007/`。

## Qualification and zero-provider gates

候选精确绑定 capability proof
`capability-evaluation:evaluation_result_7ac1e5f69296449f8068cd2853be8c5a`、proof digest `sha256:65d18436…`、closed Result
document `sha256:e6d39d16…`、Ark conformance `sha256:c86aad99…` 与 permission `sha256:dadcc47d…`。该 capability validity 截至
`2026-08-19T07:10:03.636096Z`；若在有效期外启动，Gateway 必须失败关闭并重新资格化。

capability freeze checkpoint 与 run-007 前工作树的逐项差异只有 iteration validation stub
`validation/structure_world_model_iteration_006/live_product_probe.py`；所有 `src/` qualified artifacts、Strategy/Prompt/policy 与
Gateway 字节未漂移。run-007 又以新的 protected stage manifest 单独冻结实际产品 subject。

deterministic qualification 明确记录 `external_model_called=false`、comparison authorization `NOT_AUTHORIZED`、full regression
835/835 PASS 与 Production Activation `NOT_EXECUTED`。拒绝探针后 `blocked-comparison`、`blocked-session`、`blocked-sockets` 均
不存在，证明拒绝发生在输出创建、session 建立和 listener 绑定之前。

## Preserved failed attempts

- `run-004` 使用了不存在的 conformance 输入路径，在资格安装前失败；无外部调用；
- `run-005` 的 deterministic product probe 暴露 Java formal stub 未声明 Strategy 1.1.0 identity，见 `FINDING-006-011`；
- 修复后的同一 `run-005` suite 本地重放 6/6 PASS；
- `run-006` 在受限 sandbox 的 full regression 中被 AF_UNIX policy 拒绝，835 项出现 6 error/1 failure；失败原样保留；
- `run-007` 只增加本机 AF_UNIX 能力，在仍为 zero-provider 的环境重新随机化并完成全部 Gate。

## Authorization boundary

comparison authorization document 当前为 `NOT_AUTHORIZED`，digest
`sha256:c97e2f3f4a58871cb290f2b9abbcfe2f3f0704c1b186bcf6c2a79ddb5415cdf3`；disclosure set digest 为
`sha256:6d51ca6c7d0fc4539b8883e6905e371acf2dce87dfe360b79428c5f2abf04f69`；evaluation grant digest 为
`sha256:a92c57f14dea25ee66c765405e4efdab202792e5108b1839da7ce147ab646553`，且 `live_dispatch_authorized=false`。

该候选后来已获 exact 授权并执行；实际证据见 [Live run-007](live-run-007.md)。授权已消费，不能用于修复后重跑。run-007 的
Direct/Codex 各 6/6，而 World Model 六题因 Java baseline / wrapper 同名摘要冲突在外层 postcondition 全部失败；freeze 时的
zero-provider PASS 不被追溯改写，但也不能支持 Acceptance。任何修复后 run 必须重新冻结新 suite 并另取授权。
