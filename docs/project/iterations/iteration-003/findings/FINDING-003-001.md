---
id: FINDING-003-001
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality]
depends_on: [ITER-003-SLICE-001, ITER-003-VERIFICATION]
code: []
tests: [tests/test_iteration_003_validation_assets.py]
iteration: ITER-003
classification: verification
disposition: freeze-codex-cli-argv-partitions-and-parse-smoke
target: ITER-003-VERIFICATION
---

# FINDING-003-001：成熟 Agent 对照协议未冻结 Codex CLI 参数分区

## Observation

G0 人工核对发现，`ITER-003-MATURE-SOURCE-AGENT-BASELINE@1.0.0` 把顶层参数 `--ask-for-approval never` 与 `exec` 子命令参数放在同一个 `flags` 数组中，却没有冻结 argv 顺序。对准备阶段绑定的 exact Codex CLI，按 `codex exec --ask-for-approval never --help` 拼接会以退出码 2 拒绝；`codex --ask-for-approval never exec --help` 才可解析。

## Evidence

- exact binary：`/Applications/ChatGPT.app/Contents/Resources/codex`
- version：`codex-cli 0.147.0-alpha.1.2`
- binary digest：`sha256:9f6748b4ab10ffc92c28b9ccedae89e61a302bbc011df7d276ee38f55906e481`
- G0 首次 15 项资产测试全部通过，证明原测试只核对了 flag 存在性，没有证明协议 argv 可由 exact CLI 解析。
- 人工反例：`codex exec --ask-for-approval never --help` 失败；正确分区后的顶层参数顺序成功。

## Impact and classification

缺口不改变产品或 System Contract，但会使 V-009 前必须运行并密封的成熟源码 Agent baseline 存在不可执行歧义，因此属于冻结验证协议缺陷。若忽略它，G0 PASS 会错误声称两条对照协议可执行。

## Decision and disposition

保留 `1.0.0` 作为准备提交 P 中的未通过 G0 版本，新增 `ITER-003-MATURE-SOURCE-AGENT-BASELINE@1.0.1`。新版本固定 `BINARY → GLOBAL_FLAGS → SUBCOMMAND → EXEC_FLAGS → PROMPT`，把 `--ask-for-approval never` 放入 `global_flags`，其余执行参数放入 `exec_flags`。Manifest 改绑新 ref/path/digest；V-001 明确要求 exact CLI argv parse smoke；资产测试以真实 answer schema 路径执行 `--help` 解析检查。G0 必须在这些变化后完整重跑，首次通过记录只作为失败发现证据，不能计入最终 PASS。
