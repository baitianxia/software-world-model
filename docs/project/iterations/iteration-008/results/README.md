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
