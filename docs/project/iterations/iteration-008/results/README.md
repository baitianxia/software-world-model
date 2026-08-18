---
id: ITER-008-RESULTS
kind: results-index
status: draft
authority: project-evidence
owners: [quality, project]
depends_on: [ITER-008-VERIFICATION]
code: []
tests: []
iteration: ITER-008
---

# ITER-008 Results

尚无 Product Result。Proposal、Readiness 说明、开发者自拟问题或测试数量都不是 Product Result。

前置 Conformance Gate 的 run-001 已消费其单次授权，但返回 `PROVIDER_OUTCOME_UNKNOWN`，没有形成当前 Adapter `@8` 的 PASS Result；旧
runner 仅保留 invocation，实际调用只能界定为 1—2 次且原因码不可恢复。该失败按
[FINDING-008-007](../findings/FINDING-008-007.md) 保留，不得重试或解释为 Capability/Product 证据。39-call Capability、正式 Web、
hidden canary 和 Production Activation 均未执行。

修复 observability 后的 run-002 绑定 candidate `60e1081e…` 与 preflight `sha256:86874caa…fad45`；它在第 1 次 Provider request
以 `TLS_FAILURE` 密封关闭，exact attempt count 为 1，第二次 call 未发生。该授权同样已经消费且不得重试；sanitized failure/terminal
完整保留，证明修复生效但不构成 Conformance PASS。后续必须先按
[FINDING-008-008](../findings/FINDING-008-008.md) 独立诊断 TLS，不能直接创建 run-003。

credential-free direct TLS diagnostic run-001 随后只执行一次 handshake：TCP connect 成功后，在 certificate verification 前以
`SSLEOFError` / errno 8 关闭；credential、HTTP request 与 application payload byte 均为 0。该 Result 排除了本次 DNS、TCP connect
和 CA verify 阶段失败，但没有证明远端或 direct egress 中哪一方关闭连接。下一步只能是另行授权的 frozen loopback proxy 对照，仍不构成
Conformance 或 Product Result。

credential-free proxy TLS diagnostic run-002 随后完成唯一一条 loopback CONNECT，但其唯一 verified TLS handshake 仍在 certificate
verification 前以相同 `SSLEOFError` / errno 8 关闭；proxy authorization、credential、Ark HTTP request 和 target payload 均为 0。
因此不是 proxy 不可达或仅由 Adapter 禁用 ambient proxy 导致。live qualification 进入 environment/external-state hold，TLS 路径恢复前不再
生成 Conformance freeze；本诊断同样不是 Conformance 或 Product Result。

用户关闭系统代理并声明全流量 TUN 后，credential-free TUN direct diagnostic run-003 仍只执行一次 handshake，并在 certificate
verification 前得到相同 `SSLEOFError` / errno 8；其 sanitized Result 与原 direct probe 的文件 digest 完全相同。TUN 模式声明没有形成
路径恢复证据，hold 继续生效。

更换节点后，credential-free changed-node TLS diagnostic run-004 恰好一次 verified handshake PASS；随后单独冻结和授权的唯一一次
`ark-code-latest` 最小模型诊断也 PASS，请求模型为 `ark-code-latest`，Provider response model 为 `auto`，输出符合 Adapter-compatible
strict JSON。二者证明该时点替代路由与最小调用可用，但都不是 Adapter `@8` Conformance、Capability 或 Product Result。

切回原节点后，credential-free original-node TLS diagnostic run-005 恰好一次 handshake 再次以相同 `SSLEOFError` 关闭；用户同时在
全新无痕浏览器到达同一 endpoint 的 Ark HTTP `AuthenticationError`。因此当前结论是 Python/OpenSSL 与浏览器使用的客户端/路由路径
存在选择性差异，而不是 Ark 或该节点对所有客户端整体不可用；现有证据仍不支持修改应用 Adapter。

用户随后决定更换模型 Provider。Ark live qualification 自此停止，不再生成 Ark freeze 或调用；Provider-independent 的 bounded
investigation 实现与确定性验证已经闭合。新 Provider 明确前没有新的 Product Result；后续必须先冻结其 exact endpoint、协议、模型
identity、secret 与网络边界，再从独立 Conformance 和 Capability Gate 开始，不能继承上述 Ark 诊断或已消费授权。详见
[FINDING-008-009](../findings/FINDING-008-009.md)。

DeepSeek model diagnostic run-001 随后绑定 clean candidate `8cbb3ab69871603d4cc77826eee1082e4e566f55` 与 freeze
`sha256:1c17dbe86ae42cd7f9d0d8d210ad90cf971c5d9d2d41772b2cfe3a081622c6d9`，取得只授权一个静态 strict-JSON probe 的
post-freeze user grant。runner 恰好调用一次并返回 `MODEL_DIAGNOSTIC_PASS`：请求/响应 identity 均为 `deepseek-v4-pro`，input/output
tokens 为 115/5；result/terminal digest 分别为
`sha256:42d1cacddf878d367b7eea89029563b503fbcf049f244f32e8409b9e629d27b6` /
`sha256:6202f52af2656f6b101003cc60f4b2904a1df13cf73db910444c077319c261c5`。三份执行证据 digest 与 0600 权限复核 PASS，
credential、raw prompt/response 未持久化，授权已消费且不可重试。该诊断只证明 exact endpoint/model 在该时点可完成最小调用，不是
Conformance、Capability 或 Product Result；正式 runtime 仍保持 Ark。

DeepSeek Conformance run-001 随后绑定 clean candidate `45fe1523b286f944cdc1ea781f49fe2bc5461da2` 与 preflight
`sha256:243d154eb3d89072d947a9bd678fd52786ff847cee309cbc38e9ccdef452b3a6`，取得只授权两次 synthetic request 的 post-freeze user grant。
runner 恰好调用 2 次并返回 `CONFORMANCE_PASS`：12/12 case PASS，响应 identity 仅为 `deepseek-v4-pro`，input/output tokens 为
378/87，usage 完整。result/terminal digest 为
`sha256:390378f02094d70fff4b404acc48f1ce18050761aa027d9a64d43d91f151d37e` /
`sha256:4e81b6507cc6546ca1bc54bf682a0d2fda8ad68fa03a4c17160c56ced5154261`；证据 digest、0600 权限、secret/raw payload absence、
authorization consumed/no-retry 均复核 PASS。该 Result 是 Adapter Conformance 证据，不是 Capability 或 Product Result。

同一候选零调用生成的 Capability freeze
`sha256:ad1ba1fd75739e3dcbc5e127301bb0817a3cd6b3c3258af4d86782f6d7d72551` 在独立授权前校验中因 verifier 缺少 metric contract import
触发 `NameError`。因此没有申请该 freeze 的授权，也没有读取 credential 或执行任何 39-call Capability request。缺陷和正向回归按
[FINDING-008-011](../findings/FINDING-008-011.md) 修复；修复改变 exact candidate，旧 freeze 必须保留但不得执行，后续先重新取得与修复
candidate 相同的 Conformance 资格。

修复后的 candidate `3d2f35c35efe56edce7a1938afcc8e8acbb8425b` 随后以 preflight
`sha256:3a95fe038ac8ae8b8277187c0a8ea87516fc1f5d6688878dc2908af85eec8a36` 恰好执行 2 次 DeepSeek Conformance call 并 PASS；
Result 位于
`var/iteration-008/capability/run-003-conformance-result/CC-DEEPSEEK-CHAT-NO-TOOLS-001-ccrun_bd3d72cf9895446a9dc455c81cb59bcd.json`，
digest 为 `sha256:627ff4c9329f3e09d33b3b0d6b1ec5624d33006ab189f0fc9ea8a3ad22516438`，唯一 response identity 为
`deepseek-v4-pro`。

同候选 Capability run-003 绑定 freeze
`sha256:05267d91cfe87347f48dab62f7b51c0268bf6908d9470f1fe5e075571c677ce8`，在第 25 次 Provider dispatch 以
`TLS_FAILURE / PROVIDER_OUTCOME_UNKNOWN` 密封关闭：attempted/completed request 为 25/24，completed case 为 11，无 retry。
随后以 Adapter 同一 CA fallback `/etc/ssl/cert.pem` 执行的 credential-free 对照连续 5/5 verified TLS 1.3 PASS；该诊断只校验
transport，不重试或改写 run-003。

Capability run-004 绑定 freeze
`sha256:946952576429932cd9fc8d979ad16d2d520f346d9f0a660376691063ed2c9292`，完整执行 39 次 Provider request 与 18 个 Case，
`unknown_count=0`，input/output tokens 为 88047/10249，唯一模型 identity 为 `deepseek-v4-pro`。closed Result 位于
`var/iteration-008/capability/run-004-capability-result/closed-evaluation-result.json`；result/document digest 为
`sha256:b2308facc71a051d644fbbb78f07551f840d0c1b2790610de4d86c2e46f3ccca` /
`sha256:6d698e8474c4ae3e3aa1f6705e5d7b4d2b2f6857602c7c923dedad554a11c876`。只有
`WM-JSS-I8-FIRST-CANDIDATES-001` 与 `WM-JSS-I8-DRAFT-017` PASS，其余 16 Case FAIL；Qualification 与 Production Activation 均为
`NOT_EXECUTED`。

该失败按 [FINDING-008-012](../findings/FINDING-008-012.md) 归因为 model-visible Proposal Contract 不充分：canonical operation field
shape、graph bounds、result-driven progress 和三层完整性 Review 规则没有完整进入 `prompt@4`。处置把 active contract 版本化为
`1.3.1` / prompt-vocabulary `@5`，但不修改原 18 Case、39-call、Oracle、metric、阈值或 no-retry 规则。run-003/004 作为失败证据
永久保留；新 contract 必须在新的 clean exact candidate 上重新通过 Conformance 与 Capability，不能继承本次资格。

`1.3.1` clean candidate `d9f401f290bd229f95e03853caa7e4089cf96873` 的 DeepSeek Conformance run-005 绑定 preflight
`sha256:f4dc39bdc0622f0066ee442502f587335794e7ca53d1b32ad1ca24f6a13ab71b`，恰好完成 2 次 request、12/12 Case PASS；result digest
为 `sha256:9d2aa4a2c511cb2449828888c26d314956683fba6892abd0242a1afd99bb80ae`，唯一模型 identity 为 `deepseek-v4-pro`，tokens 为
369/83，raw payload 未持久化。

同候选 Capability run-005 绑定 freeze
`sha256:5f8e06889286243ffdc4e4e3d060e800501a80bc7a1177c912f4984304386750`，完整执行 39 calls / 18 Case、无 retry、
`unknown_count=0`，tokens 为 117180/10108。closed Result
`var/iteration-008/capability/run-005-capability-result/closed-evaluation-result.json` 的 result/document digest 为
`sha256:271033468489b50107366d2cbff6e97fba3b4840f34bd6c26c8356eb96a75775` /
`sha256:aed052c6ad3db156fdb0de0b57f22e0aeb3fef7a551573917585ed3e69fadd02`。13/18 Case PASS；declared inventory、legal finish、max-four、
budget exhaustion 与 Review 五项 FAIL，所以 Qualification 与 Production Activation 均未执行。

该进展与剩余根因按 [FINDING-008-013](../findings/FINDING-008-013.md) 保留。active contract 继续版本化为 `1.3.2` / prompt-vocabulary
`@6`，只澄清 previous Result、budget、Ref copy、正/负 FINISH 和 Review taxonomy；18/39、Oracle、metric、阈值与 no-retry 不变。
完成 deterministic verification 后只再执行一轮新候选资格；run-005 的 standing authorization 已消费，不得复用。

`1.3.2` clean candidate `6e443a324d2289321457b6d828163d0dc9005300`（tree
`8ceb39e78eace1faac5280a867ebbd40a668e500`）的 DeepSeek Conformance run-006 绑定 preflight
`sha256:03d02deffe7afe7601536b68630ce98accf723799f50d7e168f1cb1815247990`，恰好完成 2 次 request、12/12 Case PASS；result digest
为 `sha256:b80972ae436dc5523b645bfb7efebc9b5c815141190f2fd7642320d8089bdf50`，唯一模型 identity 为 `deepseek-v4-pro`，tokens 为
375/76，raw payload 未持久化。

同候选 Capability run-006 绑定 freeze
`sha256:e2e40a3c7dc9ca6d82e6f38fca0d6ced2fa2384f38f4cdd17222e1977246a767`，完整执行 39 calls / 18 Case、无 retry、
`unknown_count=0`，tokens 为 126228/10227。closed Result
`var/iteration-008/capability/run-006-capability-result/closed-evaluation-result.json` 的 result/document/terminal digest 为
`sha256:85a51dc5c4182f99a9c9adaca9becbba213811d211e452b72a1d5dcda0f99692` /
`sha256:fa38bc981ed37efbe1b77642be4819e3d7cf45f0198bb50362371689356773d3` /
`sha256:884d6a35fdd3372a2af55ff206e11752ff4995385ee5d86a9f0a2b3828205cf5`。12/18 Case PASS；N candidates、result-driven batch、
declared inventory、budget exhaustion、negative complete 与 negative query-unknown 六项 FAIL，所以 Qualification 与 Production
Activation 均未执行。

该失败按 [FINDING-008-014](../findings/FINDING-008-014.md) 处置为 system-contract 架构证据，而不是继续 Prompt 重试：模型只输出
semantic intent，Application 编译 exact authority arguments；qualification 只使用产品可达 previous Result，补入正式 progress
completeness projection，并使一个 executed Result + FINISH 成为合法 2-call investigation。active contract/Strategy 已版本化为
`1.4.0`、prompt/vocabulary `@7`、policy `@1.1.0`、suite/oracle `@1.4.0`。18 Case、metric、18/18 threshold、forbidden events 与
no-retry 不变；显式合法 transition 使 fake-transport exact count 调整为 41。本架构处置没有发起新的 Provider call；live
requalification 仍待新的 clean candidate，正式 runtime 保持 Ark。

`1.4.0` 离线验证已形成：affected contract/policy/capability/product/runtime 117/117 PASS；同一个 production compiler 下的
18-case fake transport 41 calls / 18/18 PASS；full discovery 978/978 PASS、退出码 0，仅出现既有 SQLite connection
`ResourceWarning`；318 份 current documents 与 `git diff --check` PASS。这些是实现与资格输入证据，不是 Product Result、live
Capability Qualification 或 Activation。

`1.4.0` clean candidate `f056cb86b76ab3364208d9cfbba7f2562ed68688` 的 DeepSeek Conformance run-007 随后恰好
2 calls / 12 Case PASS；preflight/result digest 为
`sha256:c8e962711ce617f113e9589564b75eb00538e6e0b8506686a10394f5e1245ac0` /
`sha256:26a6460003c7f930d99c139d5813efd6046523a46a19eea25f421962c1a09bd0`。同候选 Capability run-007 绑定 freeze
`sha256:975b195a060bbc51a5376dc80af0ad551d4a8c2eb46c72a8efb1fb07d3cd64a2`，在第 38 次 request 已返回后因
model-owned search term 重复而失败关闭；37 次 request 与 15 Case 完整落盘，无 retry。failure/terminal digest 为
`sha256:82905e643b9c9968ce9d00f3b1e3f87c33a5a92d98ab24eaca4e39251ef174b5` /
`sha256:0f160da005c79fc488a1ff66b249dffe9c35788fc5b044cdeb43a84c7036a8df`，未形成 Qualification 或 Activation。

完整评审的 15 Case 为 10 PASS / 5 FAIL。按 [FINDING-008-015](../findings/FINDING-008-015.md)，活动 contract 已版本化为
capability/Strategy `1.4.1`、prompt/vocabulary `@8`、argument compiler `@2`、policy `@1.1.1` 与 suite/oracle `@1.4.1`：
Application 对有界 search term 按 casefold 保留首次顺序去重；Oracle 可预冻结有限的等价 exact projection 集合；
evaluator 不再把不同 sealed-state 样本的同名 operation 视为 cycle。本地 affected 66/66、fake transport 41 calls /
18/18 与 full discovery 980/980 PASS；新 live qualification 仍必须绑定 clean exact candidate 和全新 freeze。

`1.4.1` clean candidate `e299c097ee02dd89c404a368f070da9d546ba973` 的 DeepSeek Conformance run-008 绑定 preflight
`sha256:e031932adb843c4109a3920337d2502e406a71b28ff97d4db119388c599cb005`，恰好完成 2 calls / 12 Case PASS；
result/terminal digest 为 `sha256:e13ac784248589ec1b029a98fbe8a2515bebe8619275977d5d65b57921ba3d27` /
`sha256:a52bf779d5d4727805a359c5ee1f10b659f9e6f25de373e752e2fd6bbd073151`，唯一模型 identity 为 `deepseek-v4-pro`，tokens 为
372/84，usage 完整。

同候选 Capability run-008 绑定 freeze
`sha256:ac0f0c6e76fe7b6bed003185b74622b9af6c6d88ab4a9b04380c97440916dca1`，在第二次已完成 Provider request 后失败关闭。
`WM-JSS-I8-FIRST-CANDIDATES-001` 独立 Review PASS；`ZERO-CANDIDATES-002:call-1` 返回没有 exact `JAVA_TYPE` Ref 可绑定的
`declared_method_inventory` intent，compiler 以 `INVALID_ARGUMENT` 拒绝。attempted requests / completed Cases 为 2 / 1，
failure/terminal digest 为 `sha256:463cd849706040c44ee7f62bdfe2e37bcaa83177ea1651ac1799ea000e8e89c4` /
`sha256:7b8cdbd8ab55a5b12f8f39c665cf16597f3a8029109b21ccf32c92e722535416`；无 retry，未形成 Qualification 或 Activation。

按 [FINDING-008-016](../findings/FINDING-008-016.md)，这不是继续调整 Prompt 的依据。Adapter `@1` 没有发送或冻结
temperature，实际继承 Provider 默认值 1；Provider protocol 改为 `deepseek-chat-completions-no-tools@2`、Conformance fixture
`1.0.1`，固定 JSON numeric `temperature: 0` 并由 configuration fingerprint 与 live wire Case 共同验证。旧 `@1` Result 全部 stale；
新 clean candidate 只允许一次 run-009 Conformance + Capability 资格链。

未来必须先为 SLICE-001 形成绑定 early canary、early Agent 对照和 `V-REFLECT-001` 的独立 Result；只有产品 Case PASS、复盘完整、
`reflection_decision: CONTINUE` 且用户另行授权，才允许执行 SLICE-002。最终 Product Result 再聚合两个 Slice Result，不能覆盖
前一段的证据或失败。

每个 Result 必须绑定 exact product code freeze、Snapshot/Bundle、对应隐藏 project/suite、成熟源码 Agent baseline（若适用）、
正式 Web 现场题、逐 Case verdict、模型/工具预算和 Source/Update/Direct audit；若产品失败，按 `failed-preserved` 保留，不得创建
Acceptance。

每个 Slice Result 还必须包含 `Architecture reflection and continuation decision`，记录假设/实际、问题分类、四层架构复核、成熟
方案对照、Finding 去向和下一风险。每个当前 Slice 已到期的假设都必须有 Expected、exact Evidence、Verdict 与 Impact；最终
Result 覆盖 A1—A8，并分别填写偏差分类、
Source→Snapshot→Query→Trace→Draft/Review→Web 诊断、替代方案/下一风险和决策理由。`reflection_gate_status: PASS` 只说明复盘完成；
是否继续由独立的 `reflection_decision` 决定，并必须绑定 `reflection_decision_ref` 的 exact 用户消息。最终 Product Result 还必须
报告正向价值 actual/unit/direction/threshold 与 exact replay report digest；只写 `PASS` 无效。
