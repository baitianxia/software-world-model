---
id: FINDING-008-016
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai, engineering, quality]
depends_on: [ITER-008-SLICE-001, FINDING-008-015, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
code: [src/software_world_model/ai_infrastructure/deepseek_chat_adapter.py, src/software_world_model/ai_infrastructure/deepseek_chat_conformance.py]
tests: [tests/test_deepseek_chat_adapter.py, tests/test_deepseek_chat_conformance.py, tests/test_iteration_008_capability_harness.py]
iteration: ITER-008
classification: iteration-design
disposition: freeze-deterministic-deepseek-sampling-and-run-one-final-requalification
target: ITER-008-SLICE-001
---

# FINDING-008-016：run-008 暴露未冻结的 DeepSeek 采样配置

## Observation

`1.4.1` clean candidate `e299c097ee02dd89c404a368f070da9d546ba973`（tree
`50f4e101ec986e4988e2830c63c28560db220c67`）的 DeepSeek Conformance run-008 绑定 preflight
`sha256:e031932adb843c4109a3920337d2502e406a71b28ff97d4db119388c599cb005`，恰好执行 2 次 request 并取得
12/12 PASS。result/terminal digest 为
`sha256:e13ac784248589ec1b029a98fbe8a2515bebe8619275977d5d65b57921ba3d27` /
`sha256:a52bf779d5d4727805a359c5ee1f10b659f9e6f25de373e752e2fd6bbd073151`；唯一 response identity 为
`deepseek-v4-pro`，input/output tokens 为 372/84，usage 完整。

同候选 Capability run-008 绑定 freeze
`sha256:ac0f0c6e76fe7b6bed003185b74622b9af6c6d88ab4a9b04380c97440916dca1`。第一个
`WM-JSS-I8-FIRST-CANDIDATES-001` Case 的独立 Review 为 PASS；第二个
`WM-JSS-I8-ZERO-CANDIDATES-002:call-1` Provider request 已完成，但模型选择
`declared_method_inventory`，没有可由 Application 绑定的 exact `JAVA_TYPE` Ref，因此 compiler 以 `INVALID_ARGUMENT` 失败关闭。
runner 密封的 attempted request / completed Case 为 2 / 1；failure/terminal digest 为
`sha256:463cd849706040c44ee7f62bdfe2e37bcaa83177ea1651ac1799ea000e8e89c4` /
`sha256:7b8cdbd8ab55a5b12f8f39c665cf16597f3a8029109b21ccf32c92e722535416`。无 retry，credential 与 raw
prompt/response 未持久化，Production Activation 未执行。

## Evidence and root cause

run-008 的第二个 SQLite call record 达到 `COMPLETED` revision，response identity 为 `deepseek-v4-pro`，usage 为 2556/37；其
closed JSON 只有 `declared_method_inventory` semantic intent，没有 search term、relation intent 或 finish reason。相同
`ZERO-CANDIDATES` sealed state 在 run-007 曾合法选择 negative `FINISH`，说明相同 Adapter、prompt、suite 和 Oracle 下仍存在影响
离散协议决策的运行间采样差异。该证据不支持再次修改 Prompt、Oracle 或 threshold。

代码审查确认 Adapter `deepseek-chat-completions-no-tools@1` 的 wire body 没有发送 `temperature`，configuration fingerprint、公开状态
和 Conformance allowlist 也没有绑定该参数。因此之前的 Conformance 只能证明服务端接受请求，不能证明能力运行采用确定性采样配置。
DeepSeek 官方 Chat Completion 文档给出的默认 temperature 为 `1`，并允许 `0`—`2`；官方参数建议又明确对 Coding / Math 使用
`0.0`。Thinking Mode 文档只在开启 thinking 时声明 temperature 不支持，而本 Adapter 已显式发送
`thinking: {"type":"disabled"}`：

- <https://api-docs.deepseek.com/api/create-chat-completion>
- <https://api-docs.deepseek.com/quick_start/parameter_settings/>
- <https://api-docs.deepseek.com/guides/thinking_mode>

根因分类是 Provider configuration/protocol 缺口：本次结构化编码决策依赖稳定采样，但 Adapter 静默继承了 Provider 默认值。模型在
run-008 做出的具体错误仍属于模型行为；temperature 不能保证正确，只能消除一个未冻结且与官方编码建议不一致的变量。

## Impact and classification

该变化不改变 Application/AI Owner、bounded investigation contract、Prompt、suite、Oracle、18/18 threshold、41-call 上限、
no-retry 或正式 runtime 的 Ark 状态；`SYS-CONTRACT-AI-MODEL-GATEWAY` 已要求每个 Provider Configuration 具有明确版本和独立
Conformance，因此无需新增 System 语义。它改变 ITER-008 对 DeepSeek 的最终资格路径和 exact wire configuration，主分类为
`iteration-design`，目标为 `ITER-008-SLICE-001`。

## Decision and disposition

将非思考 DeepSeek Adapter 升级为 `deepseek-chat-completions-no-tools@2`，固定发送 JSON numeric `temperature: 0`。该值进入
configuration fingerprint、sanitized public status 和 Conformance Result；任何非 exact zero 配置均在 dispatch 前失败关闭。Conformance
fixture 升级为 `1.0.1`，wire allowlist 和 strict live case 必须验证 exact temperature。所有 `@1` / fixture `1.0.0` Result 因 Adapter、
implementation、configuration 与 fixture identity 变化而失效，不能继承。

完成本地与全量验证并形成 clean candidate 后，只执行一次全新的 run-009 Conformance + Capability 资格链。run-009 不修改
Prompt/suite/Oracle/threshold，不允许 retry；若 Capability 仍未取得 18/18，停止继续调整 Prompt 或 Provider 参数并保留失败 Result。

## Verification after disposition

- Adapter/Conformance/ITER-008 runner 的定向回归 40/40 PASS，证明 exact temperature wire field、配置漂移拒绝、tamper 失效、
  2-call Conformance 和 41-call fake Capability contract 保持。
- full discovery 981/981 PASS，退出码 0，仅出现仓库既有 SQLite connection `ResourceWarning`；320 份 current documents、
  secret scan 与 `git diff --check` PASS。新 live Result 不由本地测试推导。
