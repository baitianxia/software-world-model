---
id: FINDING-008-015
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, ai, engineering, quality]
depends_on: [ITER-008-SLICE-001, FINDING-008-014, SYS-ADR-015, SYS-CONTRACT-AI-CAPABILITY-EVALUATION, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-APPLICATION-IMPLEMENTATION-QUERY]
code: [src/software_world_model/application_services/bounded_world_model_investigation.py, src/software_world_model/ai_infrastructure/versioned_world_model_answer_strategy.py, validation/structure_world_model_iteration_008/capability/evaluator.py, validation/structure_world_model_iteration_008/capability/live_runner.py, validation/structure_world_model_iteration_008/capability/manifest.py]
tests: [tests/test_bounded_world_model_investigation.py, tests/test_world_model_answer_strategy.py, tests/test_iteration_008_capability_harness.py, tests/test_iteration_008_capability_qualification.py]
iteration: ITER-008
classification: verification
disposition: freeze-equivalent-exact-projections-and-normalize-model-search-terms
target: ITER-008-VERIFICATION
---

# FINDING-008-015：run-007 暴露可规范化 intent 与独立状态 Oracle 的错误边界

## Observation

clean candidate `f056cb86b76ab3364208d9cfbba7f2562ed68688`（tree
`57f86a0865251abcb66995c0069e2c235f5ed69b`）的 DeepSeek Conformance run-007 绑定 preflight
`sha256:c8e962711ce617f113e9589564b75eb00538e6e0b8506686a10394f5e1245ac0` 与 single-use authorization
`sha256:068fd55a2b6dfcb01835451a7d013328333cc802ed62d27ad84f9cd43fa47722`，恰好完成 2 次 request 并 PASS。
12/12 Conformance Case PASS，唯一模型 identity 为 `deepseek-v4-pro`，input/output tokens 为 364/60，result digest 为
`sha256:26a6460003c7f930d99c139d5813efd6046523a46a19eea25f421962c1a09bd0`。

同候选 Capability run-007 绑定 freeze
`sha256:975b195a060bbc51a5376dc80af0ad551d4a8c2eb46c72a8efb1fb07d3cd64a2` 与 authorization
`sha256:a69f67e71f7d54dd325516d5bc8d68ce5837caa792152c226e2e31fb8b631b9e`。runner 在第 38 次 Provider request 已返回后，编译
`WM-JSS-I8-NEGATIVE-REPRESENTATION-UNKNOWN-016:call-1` 时以
`INVESTIGATION_TEXT_LIST_DUPLICATE / INVALID_ARGUMENT` 失败关闭；37 次 request 和 15 个 Case 已完整落盘，第 38 次 request
只进入 attempted evidence。failure/terminal document digest 分别为
`sha256:82905e643b9c9968ce9d00f3b1e3f87c33a5a92d98ab24eaca4e39251ef174b5` 与
`sha256:0f160da005c79fc488a1ff66b249dffe9c35788fc5b044cdeb43a84c7036a8df`。授权已消费、无 retry；raw prompt/response、Bearer 和配置的
secret 均未进入结果目录，Production Activation 未执行。

## Evidence and root cause

第 38 次 normalized model output 的 `search_terms` 在 12 个合法字符串中把 `order` 返回了两次。JSON Schema 没有声明
`uniqueItems`，而 production argument compiler 使用通用 typed-list validator 把归一化重复视为不可恢复错误。对检索词而言，按
casefold 保留第一次出现即可无损得到平台要求的唯一有序集合；重复既不扩大权限，也不改变 Snapshot、Ref、operation 或 query
bounds。把它升级为整轮失败是 compiler normalization 缺口。

更重要的是，已完整评审的 15 个 Case 中 10 个 PASS、5 个 FAIL。逐调用证据显示其中多项不是模型违反产品协议：

- `DIRECT-NEIGHBORHOOD-006` 与 `ALL-SIMPLE-PATHS-008` 中，模型从 candidate Result 的合法 `JAVA_METHOD` Ref 直接选择所请求的
  relation/path；compiler 能安全编译该操作，产品也允许该更短路径，但单一 Oracle 强制先执行并非必需的 method implementation；
- 每次资格调用只看到一个独立 sealed previous Result。evaluator 却仅比较相邻 operation 名称，把两个不同 sealed-state 决策都选择
  relation/path 记作 `QUERY_REPEATED`。production 的 cycle guard 实际比较执行后的 operation + exact Result progress token，而不是
  operation 名称；
- `BUDGET-EXHAUSTION-011` 在 `remaining_budget=1` 时允许执行最后一次有证据增益的 path query；真实产品会在该步执行后由
  session 自动封结 `LIMITATION / INVESTIGATION_BUDGET_EXHAUSTED`，不需要额外 `FINISH` 调用。问题是资格评估把独立
  sealed-state 样本当成了连续会话，且模型在仍有明确证据可查时过早 `FINISH`；
- `LEGAL-FINISH-009` 的 synthetic method Result 只暴露 count、digest 和 Ref，没有 production method payload 中用于判断问题已覆盖的
  ordered typed atoms；要求模型据此判定 branch evidence 足够并不具备产品等价输入；
- `DECLARED-INVENTORY-005` 是真实模型缺口：明确的 declared-inventory 目标必须在四次预算内优先走
  candidate method → declaring type → inventory → FINISH，不能先消费 method implementation。

因此 run-007 同时暴露一个本地 canonicalization 缺陷和一个资格 Oracle/evaluator 缺陷。后者把合法的自适应路径、互相独立的决策样本
以及对产品预算终态的错误解释混在同一 exact-sequence 判定中；不能用继续增加 opaque 参数提示或降低 18/18 阈值处置。

## Impact and classification

产品的 semantic-intent/Application-authority Owner 边界、operation allowlist、2—4 调查预算、三层完整性、Source-off 与 no-retry
不变。变化集中在资格 Case 如何表达多个预先冻结的合法 typed projection、如何区分独立 sealed-state 决策与 production cycle，以及
compiler 对无害重复检索词的确定性规范化，主分类为 `verification`，目标为 `ITER-008-VERIFICATION`。本地 compiler 修复属于既有
Owner 边界内的实现闭合，不新增调用方权限或查询语义。

## Decision and disposition

以 capability/Strategy `1.4.1`、prompt/vocabulary `@8`、argument compiler `@2`、bounded egress policy `@1.1.1` 与
suite/oracle `@1.4.1` 处置。保留 18 个 required Case、18/18 threshold、41-call 上限、no-retry 与独立 stdlib evaluator；
Oracle 可为同一个 sealed state 冻结一个或多个同等合法的 exact typed projection，模型实际 projection 必须精确命中其之一；不再以
operation 名称相同推导 cycle；最后一个预算调用若选择 query，必须由产品 session 在执行后自动封结 terminal Limitation；method fixture 补齐
product-shaped typed atom 摘要；declared inventory 仍保持唯一四步合法路径。任何新 live run 必须绑定修复后的 clean commit、全新
Conformance 与 Capability freeze。

suite/oracle raw digest 分别为
`sha256:e7a4a08d9969759d86e7024f4107314f8934b2cb885779488c9ac5fdf36c4b20` 与
`sha256:f6c1ff74dc9ba73a94060dc11fcfa09d56f0b960609609623489f5534dba3576`；policy raw digest 为
`sha256:f4af859a4fcd033024f598f78628a1705fb8a064e128b48952bd82a1d2c5e72d`。System Contract 同步明确了有限 accepted-set、
independent sealed-state 与 product progress cycle 的边界，12-file current Contract set digest 为
`sha256:753d8abd85b79b05c0c162038a50e5049ee8bc9d83cd4f1eb8d931a2fd649c25`；Verification Matrix 保留 live Capability blocking Gate。

## Verification after disposition

- compiler 回归证明 raw list 仍受 12 项上限，`account, order, ORDER, locking` 按首次顺序编译为唯一
  `account, order, locking`；Ref 与其他 authority collection 的重复拒绝规则未改。
- fake-transport harness 仍恰好执行 41 calls / 18 Case 并 18/18 PASS；新回归证明第二个预冻结 exact projection
  可 PASS，且不会因相邻独立样本的 operation 同名产生 `QUERY_REPEATED`。
- affected contract/policy/capability/runtime 测试 66/66 PASS；full discovery 980/980 PASS，退出码 0，仅出现仓库既有
  SQLite connection `ResourceWarning`。
- `python3 scripts/docs.py check` 与 `git diff --check` PASS。这些只闭合修复后的本地候选；新 Conformance/
  Capability、正式 Web、hidden canary、SLICE-002 与 Production Activation 均未由本处置执行。
