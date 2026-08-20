---
id: FINDING-008-020
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality, project]
depends_on: [ITER-008-SLICE-001, FINDING-008-019, ITER-003-RESULT-V009]
code: []
tests: [tests/test_iteration_003_v009.py, tests/test_iteration_003_validation_assets.py]
iteration: ITER-008
classification: verification
disposition: preserve-historical-cli-freeze-and-record-environment-hold
target: ITER-008-VERIFICATION
---

# FINDING-008-020：当前桌面 Codex CLI 漂移使五项历史 exact-runtime 回归正确失败关闭

## Observation

`FINDING-008-019` 的实现完成后，允许 AF_UNIX listener 的完整测试执行面运行 985 项测试，其中 980 项通过，剩余四项 failure 和一项
error 全部来自 ITER-003 已接受 V-009 对成熟源码 Agent 的 exact Codex CLI runtime attestation。当前路径仍是
`/Applications/ChatGPT.app/Contents/Resources/codex`，但桌面应用自动更新后实际版本和 SHA-256 已变为：

- `codex-cli 0.148.0-alpha.15`；
- `sha256:7645c3caf5607e4528eb3a15b12496c284c2a918939aed34e863c760c1b421e7`。

ITER-003 冻结的 prepared runtime 则是 `codex-cli 0.147.0-alpha.1.2` 和
`sha256:9f6748b4ab10ffc92c28b9ccedae89e61a302bbc011df7d276ee38f55906e481`。共同失败原因是
`QUALIFICATION_INVALID: V-009 baseline protocol, implementation, schema, or binary drifted`，或同一 actual/expected binary digest
不相等；没有 ITER-008 产品断言、evidence-obligation transition 或 DeepSeek fixture 失败。

## Evidence and root cause

聚焦重放 `tests.test_iteration_003_v009` 与 `tests.test_iteration_003_validation_assets` 共 9 项：4 项 PASS，四项 failure 和一项 error
精确复现。前三项 V-009 harness 在 dispatch 前由 `verify_input_freeze_runtime()` 返回 code 2；mechanically-closed test 抛出同一
`QUALIFICATION_INVALID`；frozen-asset test 直接显示 current digest `7645…21e7` 不等于 prepared digest `9f67…e481`。

完整执行第一次在 workspace sandbox 中另有 7 项 AF_UNIX listener permission error；在允许该 listener 的执行面重跑后，这 7 项全部
通过，只剩上述五项。因此 AF_UNIX sandbox 限制和 CLI drift 是两个已分离的环境事实。常见本地 App、plugin 与 cache 位置没有找到
prepared `0.147.0-alpha.1.2` binary，当前环境不能真实重放该 exact runtime。

后续取证确认公开 npm package 存在精确版本 `@openai/codex@0.147.0-alpha.1.2-darwin-arm64`；其归档完整性与 registry metadata
一致，解包 binary 能报告 `codex-cli 0.147.0-alpha.1.2`，但实际 SHA-256 为
`c579255e7cacc6706175c709f3f5b350ab2d9a916ec53d38adb9434eb36448ca`，仍不等于 prepared App build 的 `9f67…e481`。版本字符串
相同不构成 binary identity；该可得 npm artifact 不能解除 hold，也不能替换或覆盖当前桌面 App binary。

根因分类为 verification/environment drift，而不是 active implementation regression。历史 freeze 的价值正是拒绝把不同 binary 冒充
已冻结 mature-agent baseline；让测试 skip、把 expected digest 改成当前 App，或伪造旧 executable 都会破坏已接受证据。

## Decision and disposition

保留 ITER-003 Manifest、input freeze、protocol 和测试断言原样，使这五项继续 fail closed。ITER-008 文档必须报告完整 suite 为
`980/985`，不得写成 PASS；V-REGRESSION-001 和 Slice Acceptance 也不能从该结果推导为通过。

该 hold 不阻断 active DeepSeek Conformance/Capability requalification：那条资格链不执行成熟源码 Agent、不读取该 Codex binary，且只
验证当前活动模型协议。允许它产生新的失败或 PASS 证据不等于豁免完整回归，也不允许进入正式 Web、canary、
SLICE-002 或 Production Activation。以后若需要重放 ITER-003 mature baseline，只能取得 digest 精确相等的 prepared binary，或为新
runtime 建立独立、前瞻性冻结和对照；两者都不能改写历史 Result。

主处置写入 `ITER-008-VERIFICATION`；Finding 本身已完成根因隔离和验证规则回写，状态为 `dispositioned`。

在 DeepSeek persistent-TLS route 适配 candidate 上重跑完整执行面得到 1010/1015；新增测试全部通过，唯一四项 failure 与一项 error
仍精确是上述 historical freeze drift。该最新计数同样不得写成 full-suite PASS。

## Subsequent gate refinement

后续 `FINDING-008-028` 不改变本 Finding 的历史 freeze、五项失败事实或 raw full-suite FAIL 裁决；它只取代“该已知 hold 永久阻断
formal Web freeze”这一产品门禁后果。ITER-008 现在只能通过 versioned `@2` qualification 机械证明五个测试 ID、4 failure + 1 error、
原因 marker 和其余全部测试精确闭合后，继续 `EVALUATION_ONLY` public Web。任何新增或不同失败仍阻断，且该 gate 不能推导
Acceptance、hidden canary 豁免或 Production Activation。
