---
id: ITER-003-RESULT-V009
kind: iteration-result
status: pass
authority: evidence
owners: [project, quality, security]
depends_on: [ITER-003-RESULT-G3A, ITER-003-VERIFICATION, ITER-003-SLICE-001, FINDING-003-014, FINDING-003-015, FINDING-003-016, FINDING-003-017, FINDING-003-018, FINDING-003-019, FINDING-003-020, FINDING-003-021]
code: [validation/structure_world_model_iteration_003/v009, validation/structure_world_model_iteration_003/questions/direct-baseline-protocol-1.0.1.json, validation/structure_world_model_iteration_003/questions/mature-agent-baseline-protocol-1.0.3.json, validation/product_holdout_iteration_002/direct_answer.py]
tests: [tests/test_iteration_003_v009.py, tests/test_iteration_003_validation_assets.py, tests/test_product_holdout_direct_answer.py]
iteration: ITER-003
---

# ITER-003 Result：V-009 External qualification and sealed baselines

## Claim and scope

V-009 在 clean exact checkpoint `019f9fced69110c6a7e357a4ea2394ec6742fd2e` 上 **PASS**。冻结的 Ark
Adapter Conformance 为 PASS；七个 required closed Capability Evaluation Case 为 7 PASS、0 FAIL、
0 UNKNOWN，Result 为 PASS 且 Validity 为 VALID；在任何 G3b 产品分派前，controlled Direct 与 exact
Codex Mature Source Agent 两条 baseline 的各 55 个 run 已按原顺序全部执行并联合密封。

本 Result **只裁决 V-009**。它不执行、不授权也不证明 G3b Model Egress Gateway、隔离浏览器产品质量、
V-010/V-011、G4、Product Validation 或 Production Activation。用户两次确认均明确排除 G3b product
dispatch；开始 G3b 前仍需新的独立确认。

## Exact inputs and authorization

- checkpoint：`019f9fced69110c6a7e357a4ea2394ec6742fd2e`；tree：
  `2580a424593914800240e016dfb14997699d09c0`；执行前后产品工作树 clean；
- input freeze：`ITER-003-V009-EXACT-INPUTS@1.0.5` / raw digest
  `sha256:1949a62cc24563c8847c3b913db231cfcde7a90040d24921e42e529aea6b9f79`；
- Provider：Volcengine Ark OpenAI-compatible chat completions，requested model
  `glm-5-2-260617`，observed `glm-5.2`，adapter `openai-chat-completions-no-tools@8`，exact HTTPS
  endpoint 与 `env:ARK_API_KEY` credential reference 均由 freeze 绑定；credential 只由 transport 注入，
  未进入 request body；
- frozen disclosure confirmation 已在 freeze 中绑定。批量执行前，用户又明确确认“上述两批外部披露与
  调用”，消息 SHA-256 为
  `sha256:1598ff3231362a390c02037a08ffad7ce296655592010a3e0ac9bedb9620f8a0`；该确认只扩充执行授权记录，
  不改变任何模型输入；
- baseline runner SHA-256：
  `c94858c1cd69e21e42d16ab2db86dab9f409d6d0e5fa05d179bca33dac170bd5`；operator manifest document
  digest：`sha256:2c572410eb63f22faa76de2e1b571d26a0d7f49368eedd1caf1b0a3937f2901a`；
- 55-run product plan document digest：
  `sha256:550916a5549de7c9c534a9ec669b184fc2db18e09002d9d1e0ec7fa930ed3cd3`。计划含 7 个静态
  direct-parity case × 5 和 4 个运行时变形 case × 5；模型可见输入不含 expected、Oracle、seed、评分、
  Direct 或 world-model results。

## Adapter Conformance and closed Capability Evaluation

原始证据目录为
`var/iteration-003/v009/019f9fced69110c6a7e357a4ea2394ec6742fd2e/`。

- Conformance 在第一次调用前写入 O_EXCL invocation，完成 2 个 required request 后得到 exact PASS。
  binding document digest 为
  `sha256:d387450b24c3e8f01de39476dc3fdc719fd2fe83a9f926f789c155f32e989328`；绑定的 Conformance Result
  digest 为 `sha256:c86aad995802b8dcf687fafcbaf36bccb02768ba55b40151ec9aa4704518cade`；
- closed CE 每个 Case 恰好一次 no-tools 调用，无 hidden retry。总 input/output token 为 6,158/370；
  result ID 为 `evaluation_result_916b9000db544e92921ec1bdc02a3bc2`，Result digest 为
  `sha256:6ed1177e1222e11c03f7cd61ef28c9d00ccc21e9a129559c5842f3678933e6ce`；
- closed document digest 为
  `sha256:d91b0425a2b0cf42bf372f5740b871cd3545bfc5f359e01f14fb7005703ef620`；qualification ref 为
  `capability-evaluation:evaluation_result_916b9000db544e92921ec1bdc02a3bc2`，qualification digest 为
  `sha256:005b1bf43c76a64d123b0184cdac1a9e844331896e7ede6279875881d9bcc62c`；
- standalone evaluator PID、implementation/projection/sink digest 与 forbidden-event audit 均逐 Case 保存。
  Strategy 输入没有 Product suite/oracle、projection、expected 或 forbidden-event fields。

## Controlled Direct baseline

Direct protocol `1.0.1`、implementation semantic digest
`sha256:26a0d3e55188daa974f0ffcb9147a4606765453bb8b9a26174adc6b911d2caa4` 与同一 Ark
Provider/adapter/model 被固定。每个 run 使用 fresh process、fresh SQLite runtime、per-revision required POM
closure 与 union allowlist；每次 Provider dispatch 前后都有不可覆盖的 transport receipt。

- 55/55 run 均有 terminal receipt；15 SUCCESS、40 `FAILURE_KEPT_NO_RETRY`；
- run-level 失败包括 25 次 structured/action contract failure、13 次 Ark HTTP 429 和 2 次 Provider outcome
  unknown；没有 run-level retry，也没有等待限流恢复后补跑；
- transport 共记录 HTTP 200=510、HTTP 429=13、exception=2。15 个成功 run 合计 218 次 eligible model
  call、1,654,368 input token、40,059 output token、140 次 source action；失败 run 的调用和用量没有被伪装
  成成功 totals；
- 全部 55 个 executor terminal latency P50=40.213 秒、P95=101.502 秒；success-only P95=125.253 秒，
  failure-only P95=84.718 秒；
- batch Result document digest：
  `sha256:64a7a9c2357427f0b4f0c77b47a895c454de1cfce5830d759941764963ac871d`。

这些失败是 baseline 事实，不是 V-009 后补修对象。`FINDING-003-021` 规定 V-011 不得只挑 15 个成功样本、
不得为缺失质量输出做插值，也不得静默从 P95 population 删除 Provider failures。

## Mature Source Agent baseline and isolation

Mature baseline 固定 Codex CLI `0.147.0-alpha.1.2`、binary digest
`sha256:9f6748b4ab10ffc92c28b9ccedae89e61a302bbc011df7d276ee38f55906e481`、bundled model
`gpt-5.6-sol` / reasoning `low`、protocol `1.0.3`、root-deny permission profile、Web/Apps/multi-agent
disabled，以及 no-login/inherit-none 的四变量 shell environment。每个 run 使用只含授权 POM、answer schema
和本地 Git metadata 的独立 workspace。

- 首次正式预检发现物理 `/private/tmp` 下的 workspace parent 与 evaluator sibling 可读，立即形成
  `BLOCKED_PREFLIGHT_NO_MODEL_CALLS`；该 evidence 原样归档，未发出 Mature 模型请求；
- `FINDING-003-020` 在不改变 runner、plan、profile、Prompt、workspace commit 或 POM digest 的条件下，把
  控制树物理迁到系统 `$TMPDIR` 并保留逻辑路径。迁移 record document digest 为
  `sha256:a06218e29fbbe0b648caa3223b08a649c4e62221d7a65f1831eab32eb6a6e80e`；
- 最终正式预检 7/7 PASS：授权 POM read 成功；原仓库、workspace parent、Home、evaluator temp sentinel、
  operator environment 与本地 network 均拒绝。preflight document digest 为
  `sha256:04ac7b4b6bcbf6d96420a60e795fd031cafddb52f48eeb86677313f922100b80`；
- 55/55 cold process SUCCESS、0 FAILURE；batch Result document digest 为
  `sha256:1b10854b1dc17a022c35542a68b1bafd0ee238710c60dbdb461c5323688a2f6f`；
- terminal latency P50=67.931 秒、P95=94.455 秒。Mature 是跨模型质量 comparator，不用于跨模型性能比例；
- 780 个 JSONL event、480 个 model-generated read command 全部审计；0 event parse error、0 Web/MCP/browser/
  multi-agent/write/env dump/network/outside-workspace event，55 个 workspace 执行后全部 clean；
- 429 个 claim 的 3,553 个 locator 全部匹配 `A/`、`B/` 或 `SOURCE/` 下真实授权 POM 和有效行号。

## Joint seal and failure evidence

联合 baseline seal document digest 为
`sha256:7be049fe746a71cb3b9c3941d81e8e51076256d0f8dac61ba5a5c88c873ecbdd`。它绑定两个 batch Result、
全部 110 个 terminal digest、operator/plan identity，并明确 `failures_preserved=true`、
`world_model_product_results_visible_at_seal=false`、`g3b_product_dispatched=false` 与
`production_eligible=false`。

baseline 准备阶段还有一次零模型的本地 operator failure：登录成功文本位于 stderr，而旧检查只读取 stdout。
该随机 seed 与 plan 已归档为 `PRESERVE_AND_NEVER_REUSE`，failure document digest 为
`sha256:5ac24ae6d86701743e72006445765eef0319e53d74eae600d81e415815db0bd2`；修正后的 runner 使用全新 seed
和 plan。该失败没有 Provider dispatch，也没有覆盖旧证据。

密封完成后另以标准库只读脚本独立复核 runner/plan/seal digest、110 个 terminal、Direct transport
pre/terminal closure、全部失败证据、Mature event/command/citation audit、55 个 clean workspace 和两轮
preflight 归档。审计为 PASS，0 citation error、0 forbidden event、0 workspace drift，且未调用外部模型；
audit document digest 为
`sha256:7e360693cdf99b3189cbb5380a5a3a597131d1933f6bd1aa64f47b0ba3240bc3`，script SHA-256 为
`7e60c89e00593568e585915318ee92bdddcb35d8e6c601604f045fd9a04c0dc4`。

## Findings and write-back

V-009 的八条实现发现均已唯一处置：

| Finding | Disposition |
|---|---|
| `FINDING-003-014` | G3a offline authority 保持不变，closed CE subject 为独立 model proposal strategy。 |
| `FINDING-003-015` | Prompt 固定平台 uppercase owner enum，并从新 freeze 全量重跑。 |
| `FINDING-003-016` | Prompt 固定 PARTIAL coverage 的 Knowledge Gap status 规则，并全量重跑。 |
| `FINDING-003-017` | Direct 使用 per-revision required POM closure，path union 只作 allowlist。 |
| `FINDING-003-018` | 删除 legacy sandbox，使用 root-deny exact permission profile。 |
| `FINDING-003-019` | model-generated command no-login/inherit-none，仅显式注入非秘密环境。 |
| `FINDING-003-020` | 物理控制树迁到系统 `$TMPDIR`，并以最终物理位置证明 sibling denial。 |
| `FINDING-003-021` | Direct 全部失败保持可见；V-011 不得插值、择优或静默过滤。 |

处置已写回当前 Slice、Verification Matrix、Manifest 与 current context；本 Result 不重新定义 System 语义。

## Verdict, limitations and validity

V-009 最终结论为 **PASS**，解除的是 V-009 对 G3b 的技术前置阻断，不是 G3b 执行授权。V-010、V-011、
V-013、G3b、G4 与 iteration acceptance 仍为 NOT RUN；Product Validation 和 Production Activation 仍为
NOT EXECUTED。

本 Result 只对 checkpoint/tree、input freeze `1.0.5`、上述 exact Provider/Strategy/protocol/binary/model、
runner/plan、物理 staging disposition 与原始 evidence 成立。任一模型、Prompt、permission profile、shell
environment、问题、POM closure、suite、evaluator、checkpoint 或 baseline result 变化都会使对应资格/对照
陈旧。V-009 direct Adapter transport 和 Mature Seatbelt 证明都不能替代 G3b distinct Model Egress Gateway
process 与产品 Answer/Projector OS denial audit。
