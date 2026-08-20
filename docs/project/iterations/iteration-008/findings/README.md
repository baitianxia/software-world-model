---
id: ITER-008-FINDINGS
kind: iteration-findings-index
status: open
authority: development-evidence
owners: [engineering, architecture, quality]
depends_on: [ITER-008-PROPOSAL]
code: []
tests: []
iteration: ITER-008
---

# ITER-008 Findings

本 Slice 当前登记二十八条 Finding；二十八条均已处置或被后续决定取代。`FINDING-008-027` 已把 search-term 资格约束收敛到
question-owned、产品真实的 concept，run-019 已完成当前 live 资格；`FINDING-008-028` 进一步以 versioned exact historical-hold gate
解除正式 product freeze 的机械死锁，但不把 raw suite 写成 PASS，也不豁免 Web、canary、SLICE-002 与 Production Activation gate：

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
  contract、Adapter `@1` 与独立 Gate 接入；最小 model diagnostic 与 2-call Conformance run-001 已分别按 exact authorization PASS，
  但正式 runtime 保持 Ark，39-call Capability 仍须独立冻结和授权。
- [FINDING-008-011](FINDING-008-011.md)：首次 DeepSeek Capability freeze 的独立校验在授权前暴露 verifier 缺失 metric contract import；
  以最小 import 和有效 freeze 正向回归修复，旧 freeze 不执行，修复后的 exact candidate 必须重新通过同候选 Conformance Gate。
- [FINDING-008-012](FINDING-008-012.md)：完整 DeepSeek Capability run-004 完成 39 calls / 18 Case 却只有 2 Case PASS，证明
  model-visible Proposal Contract 没有完整暴露 exact operation field shape、graph bounds、result-driven progress 与三层完整性规则；
  以 Provider-independent `1.3.1` / prompt-vocabulary `@5` 版本化处置，不降低或改写原 Oracle。
- [FINDING-008-013](FINDING-008-013.md)：`1.3.1` 的 run-005 完整完成 39 calls 并把结果提高到 13/18；剩余五个失败收敛为
  declared-set primary Need、remaining-budget 当前回合、逐字符 Ref、正/负 FINISH 与 Reviewer code precedence 歧义，以通用
  `1.3.2` / prompt-vocabulary `@6` 处置，原 Case、Oracle 与阈值不变。
- [FINDING-008-014](FINDING-008-014.md)：`1.3.2` run-006 完成 39 calls 并取得 12/18，但进一步证明让模型复制 opaque
  authority 参数是职责倒置，且旧资格包含产品不可达的 inventory、budget 与 negative 状态。活动契约升级为 `1.4.0`：模型只提
  semantic intent，Application 编译 exact typed arguments；修复 declaring-type、progress completeness 与 2-call FINISH 边界，并以
  产品可达的 18-case / 41-call suite/oracle 重新冻结离线资格输入。
- [FINDING-008-015](FINDING-008-015.md)：`1.4.0` run-007 的 Conformance 12/12 PASS，Capability 在第 38 次 request 后因重复
  search term 失败关闭；已完整评审的 15 Case 还证明单路径 Oracle 与按 operation 名称推导 cycle 会拒绝合法产品行为。
  活动契约升级为 `1.4.1`：Application 对有界 model-owned term 按 casefold 去重，Oracle 预冻结有限的等价 exact
  projection 集合，evaluator 只根据同一产品 Session 的 progress 证据判定 cycle。
- [FINDING-008-016](FINDING-008-016.md)：`1.4.1` run-008 Conformance 12/12 PASS，但 Capability 在第二次已完成的 Provider
  request 后因不可编译的 inventory intent 失败关闭；Adapter 未发送或冻结 temperature，实际继承 Provider 默认值 1。
  Provider 协议升级为 `deepseek-chat-completions-no-tools@2`，固定 `temperature: 0` 并由 configuration fingerprint 与
  Conformance `1.0.1` 共同约束；只允许一次全新 run-009 资格链。
- [FINDING-008-017](FINDING-008-017.md)：run-009 证明 Adapter `@2` 的 temperature-zero Conformance 12/12 PASS，但
  Capability 在前 7 Case PASS 后因 path intent 携带 `BOTH_CALLS` 失败关闭；18 次实际 request 均完成。该 relation intent 不能无损
  忽略的旧判断与停止等待状态已由后续显式协议 redirect 取代；run-009 失败证据本身继续保留。
- [FINDING-008-018](FINDING-008-018.md)：用户明确要求集成层适配模型。固定 JSON envelope 不是所有 operation 共享语义的结构；
  Application 改为按 operation 只解释其拥有的 slot，非适用 slot 被确定性投影掉，相关 slot 与全部 authority/transition 仍严格校验。
  compiler 升级为 `@3`、Gateway policy 升级为 `@1.1.2`；Prompt、suite、Oracle、18/18 和 no-retry 不变，clean candidate 需全新资格。
- [FINDING-008-019](FINDING-008-019.md)：run-010 完整执行 41 calls / 18 Case 并取得 16/18；仅剩两次 premature FINISH，且合法
  method-only FINISH 同时 PASS。Application 因而冻结通用 evidence-obligation ledger，并拥有逐状态 transition、FINISH eligibility
  与 terminal reason；活动协议升级为 `1.5.0/@9/@4/@1.2.0` 和 suite/oracle `@1.5.0`，不加入题型、问题、工程或 evaluator 特判。
- [FINDING-008-020](FINDING-008-020.md)：完整 985 项回归中 980 项通过；剩余五项全部是 ITER-003 frozen mature Codex CLI 与当前
  桌面 App binary 漂移后按设计失败关闭。历史 freeze 和断言保持不变；该 environment hold 不冒充产品 regression，也不被写成
  full-suite PASS，且不阻断相互独立的活动 DeepSeek 资格链。
- [FINDING-008-021](FINDING-008-021.md)：run-011 Conformance 12/12 PASS；Capability 前 14 Case / 35 calls 全 PASS，但第 36 次
  completed request 因模型把“是否实现”解释为 candidate evidence 而非 method evidence，在本地 ledger exactness 校验失败。candidate
  discovery 是强制 prerequisite，不再是可终止 canonical obligation；raw candidate request 由 Application 保守向上归一为 method，
  活动协议升级为 `1.5.1/@10/@5/@1.2.1` 和 suite/oracle `@1.5.1`；相关回归 116/116、fake transport 18/18、docs 325/325
  PASS，full 仅保留 `FINDING-008-020` 的五项外部 CLI drift，Finding 已处置，新 live qualification 仍 blocking。
- [FINDING-008-022](FINDING-008-022.md)：run-012 Conformance 12/12 PASS；Capability 前 9 Case / 21 calls 全 PASS，第 22 次
  completed request 因模型为 outgoing trace 选择 method evidence、suite 选择重复 outgoing direct evidence 而失败关闭。正式 method
  result 已包含带 Support 的 exact outgoing CALLS；Application 将 standalone outgoing-direct alias 收敛到 method，path/incoming/both
  不变，活动协议升级为 `1.5.2/@11/@6/@1.2.2`、suite/oracle `@1.5.2` 与 18 Case / 40 calls；相关 169/169、fake transport
  18/18、docs 326/326 与本地完整门禁均已闭合。随后 run-013 Conformance 12/12、Capability 40 calls / 18/18 PASS，Finding 已处置。
- [FINDING-008-023](FINDING-008-023.md)：run-013 已资格化 DeepSeek，但正式 bounded policy/Gateway/runtime 仍只接受 Ark，不能把
  DeepSeek Result 错配给 Ark。Provider fallback 被定义为 product dispatch 前的 exact qualification route selection；本轮选择
  DeepSeek，任何已分派或 outcome-unknown request 均不得跨 Provider 重试，Ark 只有取得同 Contract 新资格后才能恢复优先级；
  system/code/test 处置已闭合，旧 run-013 因未绑定新 resource policy 被拒绝，全新资格链仍 blocking。
- [FINDING-008-024](FINDING-008-024.md)：新 route 的 run-014/015 分别在第 4、10 次请求前遭遇相同 TLS EOF；此前请求与 evaluator
  均 PASS。当前 TUN 对大量独立 TLS session 间歇失败，而 endpoint 明确支持同一 verified connection 的 HTTP/1.1 keep-alive。
  处置把 bounded credential-free TLS acquisition 与 HTTP request dispatch 分开：只允许发送凭据/HTTP 前最多三次握手，已发送后
  仍绝不 retry，并在一个授权运行内复用 verified TLS session。direct/pinned transport、freeze、资格 loader、runtime 与文档 Owner
  已闭合；完整回归 1010/1015，唯一五项仍是 `FINDING-008-020` 的历史 runtime drift，新 live qualification 继续 blocking。
- [FINDING-008-025](FINDING-008-025.md)：persistent candidate 的 run-016 Conformance 12/12、transport 健康，但 Capability 前
  6 Case / 12 calls PASS 后，模型在 reachability Case 选择 method evidence，并复制 prompt 示例词。旧 Adapter 把 schema 与任务语义
  分成两个 system turns；活动适配改为单一 leading system authority，并以通用 reachability precedence 和 example-only term 规则
  升级为 Adapter `@4`、Contract `1.5.3/@12`、Conformance fixture `1.2.0`、policy `@1.4.1`、suite/oracle `@1.5.3`。不放宽
  Application/evaluator、不加入题目或 Oracle 特判；相关 128/128、fake 18/18、docs 329/329 PASS，完整执行面 1011/1016，唯一
  五项仍是 `FINDING-008-020` 的历史 drift。Finding 已处置，新 live 资格继续 blocking。
- [FINDING-008-026](FINDING-008-026.md)：`1.5.3/@12` 的 run-017 已修复旧 PATH-EXISTS Case，但第 22 次 request 把要求解释
  authentication workflow 的问题误选为 binary `path_exists`，并复制非 Investigation section 的 `order/return/throw/audit`。
  Gateway 现于 Manifest 前按 sealed capability 选择唯一 prompt entry，并绑定 `capability-prompt-selection@1`；活动身份升级为
  `1.5.4/@13/@1.4.2` 与 suite/oracle `@1.5.4`，Adapter `@4`、compiler `@6`、18/40、Oracle、18/18 和 no-retry 不变。
  run-017 永久失败关闭，新 live 资格仍 blocking。
- [FINDING-008-027](FINDING-008-027.md)：`1.5.4/@13` 的 run-018 完成 40 calls / 18 Case、transport 零 unknown/retry，且
  PATH-EXISTS、MAX-FOUR、operation/compiler/Ref projection 均正确，但两个首轮 search-term semantic constraint 使结果为 16/18。
  REF-PROVENANCE 暴露 question concept 与 instruction vocabulary 重叠时的来源判定歧义；RESULT-DRIVEN-BATCH 则证明旧 suite
  把未请求的 `return/throw` 实现机制误作唯一等价表达。活动身份升级为 `1.5.5/@14/@1.4.3` 与 suite/oracle `@1.5.5`；
  operation Oracle、18 Case / 40 calls、18/18、Adapter `@4`、compiler `@6` 和 no-retry 不变。run-018 永久 FAIL；exact
  candidate `6dc7a9e4…` 的 run-019 Conformance 12/12、Capability 40 calls / 18/18 PASS，V-002 对当前 Contract 已闭合，formal
  product freeze/Web 仍是下一 blocking Gate。
- [FINDING-008-028](FINDING-008-028.md)：旧 product freeze 同时要求 raw full-suite PASS 和保留 `FINDING-008-020` 的五项
  exact-runtime FAIL，形成永久死锁。确定性 qualification 升级为 bounded-route-only `@2`：只有五个测试各执行一次、精确 4 FAIL +
  1 ERROR、原因 marker 相等且其余测试全 PASS 时，才以 `PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD` 继续 evaluation-only Web；
  任何新增/不同失败仍阻断，历史断言、raw FAIL、canary/Acceptance/Activation 边界不变。

后续 Finding 仍须区分：查询架构缺口、World Model 表示缺口、实现缺陷、环境/配置问题和评测问题；尤其不得把隐藏工程暴露后的
表示缺口用题目、工程、关键词或符号补丁掩盖。
