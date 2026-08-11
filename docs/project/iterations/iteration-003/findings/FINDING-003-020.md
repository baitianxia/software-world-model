---
id: FINDING-003-020
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality, security]
depends_on: [ITER-003-SLICE-001, FINDING-003-019, ITER-003-VERIFICATION]
code: [validation/structure_world_model_iteration_003/questions/mature-agent-baseline-protocol-1.0.3.json]
tests: [tests/test_iteration_003_validation_assets.py]
iteration: ITER-003
classification: iteration-design
disposition: stage-mature-control-tree-under-system-tmpdir-and-prove-physical-sibling-denial
target: ITER-003-SLICE-001
---

# FINDING-003-020：`/private/tmp` 不能由 `:slash_tmp` 特殊项推定为已隔离

## Observation

最终 V-009 baseline operator 在任何 Mature 模型调用前，以 protocol `1.0.3` 的同一
`mature_source` permission profile 执行真实预检。精确工作区 POM 可读，原仓库、Home 与本地网络均被
拒绝；但当控制树物理位于 `/private/tmp` 时，读取 workspace parent 的目录项和 evaluator sibling sentinel
却成功。该主机/CLI 组合下，profile 的 `:slash_tmp=deny` 不能被解释为对 canonical
`/private/tmp` sibling 内容的机械拒绝证明。

预先使用 `tempfile.TemporaryDirectory` 的演练位于系统 `$TMPDIR`，因此曾正确得到 7/7 PASS；两次结果的
差异来自物理 staging root，而不是模型、Prompt、问题、POM、workspace commit、permission profile 或
shell environment 变化。

## Evidence

- 阻断性正式预检：
  `var/iteration-003/v009/019f9fced69110c6a7e357a4ea2394ec6742fd2e/baselines/mature-preflight-failure-01/preflight.json`，
  document digest
  `sha256:9d4bcb8d9d4818b8cfcf2e807c1c2278f6a7924bf82fb70f46035984c47f7d7d`；
- 该批次 Result 为 `BLOCKED_PREFLIGHT_NO_MODEL_CALLS`，`external_model_called=false`；
- 同 profile 的 symlink 等价诊断把物理数据放入系统 `$TMPDIR`，精确工作区读取成功，workspace parent、
  evaluator sibling、原仓库、Home、operator sentinel 与本地网络全部拒绝；
- 迁移记录：
  `baselines/operator/mature-workspace-relocation.json`，document digest
  `sha256:a06218e29fbbe0b648caa3223b08a649c4e62221d7a65f1831eab32eb6a6e80e`；
- 迁移后的正式预检 7/7 PASS，document digest
  `sha256:04ac7b4b6bcbf6d96420a60e795fd031cafddb52f48eeb86677313f922100b80`；
- 55 个 workspace 的 Git commit/tree 与逐文件 digest 在迁移前后相等，逻辑路径不变，Direct 结果不变。

## Impact and classification

第一次正式预检正确阻止了 Mature 模型调用，所以没有发生越界披露。缺口只影响本轮 baseline staging 与
隔离证明，未改变产品实现、System Contract、Provider/Model、问题或 Oracle，分类为
`iteration-design`。不能把特殊路径名称本身当作 OS enforcement 证据；必须用实际物理位置的 sibling
probe 证明。

## Decision and disposition

保留失败预检和全部控制文件，不覆盖、不选择性忽略。Mature 控制树物理迁移到本机系统 `$TMPDIR`；原
`/private/tmp/iter003-baselines-019f9fced691` 只保留指向该物理树的逻辑链接，使已密封 plan、workspace
manifest、问题、POM 与 Direct connector identity 不漂移。permission profile、shell environment、Codex
binary/model、Prompt 与 runner bytes 均不修改，因此不重新解释为新的 baseline 输入。

后续同类 macOS runner 必须记录 logical 与 physical root，并在首次模型调用前用最终物理 staging root
验证 exact workspace 可读且 parent、evaluator sibling、原 workspace、Home、operator environment、temp
sentinel 与 network 全部拒绝。只验证 `$TMPDIR` 或只匹配 `:slash_tmp` 名称均不足。

## Verification after disposition

迁移后正式预检 7/7 PASS；55 个 Mature cold process 全部完成，事件审计没有 Web、MCP、browser、
multi-agent、write、env dump、network 或 outside-workspace 事件。执行后 55 个 workspace commit/tree、
answer schema 与 POM digest 再次逐项相等。
