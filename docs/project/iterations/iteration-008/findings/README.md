---
id: ITER-008-FINDINGS
kind: iteration-findings-index
status: dispositioned
authority: development-evidence
owners: [engineering, architecture, quality]
depends_on: [ITER-008-PROPOSAL]
code: []
tests: []
iteration: ITER-008
---

# ITER-008 Findings

本 Slice 当前登记十条已处置 Finding：

- [FINDING-008-001](FINDING-008-001.md)：活动 contract alias 会使 ITER-007 资格被错误解释为新协议；历史 `1.2.2` 与有界
  `1.3.0` 的 Strategy、Schema、operation、policy 和 closed Result identity 保持不可互换。
- [FINDING-008-002](FINDING-008-002.md)：显式 `FINISH` 本身占用模型调用；保留冻结 4—6 安全 envelope，实际调用与预建 6 个
  descriptor 分开审计，未使用 descriptor 必须关闭，不为凑下界伪造 terminal。
- [FINDING-008-003](FINDING-008-003.md)：正式 Answer worker 不读取评测 Oracle；提问前的独立召回 result 只以绑定 exact
  Snapshot/Bundle/Profile/discovery Contract 的 `STRUCTURE_ORDERED_READ_BUNDLE@2` 权威进入，同一 Formal Web 才能安全形成
  bounded absence；旧 `@1` 和无证明路径保持 Limitation。
- [FINDING-008-004](FINDING-008-004.md)：有界 `1.3.0` 不改写 ITER-007 的 Answer 资产和
  `WORLD_MODEL_EVALUATION_PAGE@1`；新运行资产显式加入 bounded closure，携带调查 Trace 的页面使用独立 `@2` identity。
- [FINDING-008-005](FINDING-008-005.md)：当前 Adapter `@8` 没有可继承的 Conformance Result；先对 clean exact candidate
  单独冻结并授权 2-call Conformance，PASS 后再冻结并另行授权 18-case / 39-call Capability Evaluation，两份授权均不可继承或复用。
- [FINDING-008-006](FINDING-008-006.md)：request、authorization 与实际执行的 freeze 必须在 credential/transport 前重新做 exact
  ref、digest 和 scope 绑定；仅让每份文档各自 digest 正确不能构成分派授权。
- [FINDING-008-007](FINDING-008-007.md)：run-001 的 Provider 结果未知且旧 runner 未密封 exact attempt/reason；该一次性授权已消费且
  不得重试，后续 runner 必须在返回控制前写入 sanitized failure/terminal，并以实际 dispatch count 约束 qualification。
- [FINDING-008-008](FINDING-008-008.md)：direct、loopback proxy tunnel 与用户声明的 TUN 路径都在证书验证前以 TLS EOF 关闭；
  当前 live qualification 进入 environment/external-state hold，路径恢复前不得改 Adapter 或生成下一份 Conformance freeze。
- [FINDING-008-009](FINDING-008-009.md)：替代节点已证明 Ark TLS 和一次最小模型调用可用，原节点则呈现 Python/OpenSSL
  与浏览器路径分流；用户决定更换 Provider，因此停止 Ark live 工作，Provider-independent 实现保持冻结，新 Provider 必须以 exact
  contract 和独立资格 Gate 接入。
- [FINDING-008-010](FINDING-008-010.md)：DeepSeek 已以独立 `DEEPSEEK` Provider、exact endpoint/model/secret/wire/network
  contract、Adapter `@1` 与 2-call Conformance 接入；离线 Gate 已闭合，但正式 runtime 保持 Ark，先等待 API Key 和独立最小模型
  diagnostic 授权，不能从离线测试推导 live 可用性。

后续 Finding 仍须区分：查询架构缺口、World Model 表示缺口、实现缺陷、环境/配置问题和评测问题；尤其不得把隐藏工程暴露后的
表示缺口用题目、工程、关键词或符号补丁掩盖。
