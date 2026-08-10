---
id: ITER-003-VERIFICATION
kind: iteration-verification
status: in-progress
authority: planned-verification
owners: [quality]
depends_on: [ITER-003-PROPOSAL, PROJECT-GOVERNANCE-VERIFICATION, SYS-QUALITY-ACCEPTANCE]
code: []
tests: []
iteration: ITER-003
---

# Iteration 003 Verification Matrix

| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |
|---|---|---|---|---|---|---|
| V-001 | 文档、全部冻结资产、授权链和 exact clean baseline 闭合 | contract / preflight | 准备起点 `40c6584…`、准备包 commit、Manifest 全部 digest、fixture/schema/oracle/suites/generator/legacy/direct protocol | `scripts/docs.py check` 与两个 ITER-003 资产测试模块通过；Maven offline、JSON duplicate-key、manifest association、mall raw POM Oracle、generator 双重确定性/隔离和 mature Agent exact CLI argv parse smoke 均有原始输出；准备提交无产品代码差异；授权提交把 baseline、全部状态和 current 指针原子对齐；人工逐项打开核对 | `ITER-003-RESULT-G0`；`var/iteration-003/g0/af849fb198179cfe1d1514f272a1a06236684f43/` | PASS / G1 unblocked |
| V-002 | exact Schema/Evaluation Context/Canonicalization 与 Literal/Relation Fact 分型成立 | unit / contract | Manifest 三个 Definition digest、subject/object closure、悬空和混型反例 | digest 相等且 Coverage Root/State 固定 refs+digests；关系两端可验证；悬空、混型、字符串降级全部拒绝 | `ITER-003-RESULT-G1`；`var/iteration-003/g1/ddb8f5feba1e0c52d2f788c2bb66c93810f2b469/` | PASS / G1 complete |
| V-003 | Entity/Fact/Coverage Root 与 State 真正分离 | contract / counterexample | mall A/B 共有对象；同 GA 只改 path、label、version、Context、Evidence 的构造 | A=7 Entity/11 Relation、B=8/14；A/B 共有 7 Entity Root、11 Relation Fact Root 与同一 Coverage Root 稳定；所有 revision-bound State 改变；任何 path/label/version-based Root 假实现失败 | `ITER-003-RESULT-G1`；`oracle-audit.log`、`reports/oracle-comparison-summary.json` | PASS / G2 unblocked |
| V-004 | `ENRICH` 与 `REPLACE_COVERAGE` 语义唯一且删除成立 | contract / fault | A→B→A、同 Root 不同 State、重叠 Coverage、coverage 外成员、CAS/恢复失败 | ENRICH 不同 State 拒绝；重叠拒绝；B 新增项在新 A CURRENT 消失；旧 B 可读；coverage 外不丢；失败保持 CURRENT | `ITER-003-RESULT-G1`；`publication-audit.log`、`reports/a2.json`、聚焦 fault tests | PASS / G2 unblocked |
| V-005 | Maven 构建不依赖名称/GA 拼接且完整覆盖 root | product-contract | exact positive/exclusion/rejection fixture suite：nested、path≠artifactId、同名异 group、local-vs-inherited dependency、dependency version mismatch、same-GA/different-version、profile、path/symlink、env/unresolved property、range、external parent、duplicate declaration | 只按 frozen canonical rules 连边；root 与全部 child local declarations 被扫描；外部 GA 和 version mismatch 作为带原因 exclusion、不成边且 Coverage 可 COMPLETE；歧义、路径逃逸或求值不完整等 rejection 使整次构建失败且 CURRENT 不动；Maven 不可用即 G0 阻断而非 skip-pass | `ITER-003-RESULT-G1`；`focused-tests.log`、`reports/a1.json`、`reports/b.json`、`reports/a2.json` | PASS / G2 unblocked |
| V-006 | 零问题更新、mall A1→B→A2 与 Read Set 稳定性成立 | integration / fault | exact commits/tree/Oracle；Question/Task/Session 初始计数 0；manual Build Objective 无 Requirement binding；CURRENT 并发移动 fault | 无问题仍构建 A1、更新 B、再替换 A2；图、路径、diff、删除、root negative 与历史逐项相等；旧 Session 和已解析 ordered Read Set 不漂移 | `ITER-003-RESULT-G1`；`integration-tests.log`、`reports/`、`manual-review.md` | PASS / G2 unblocked |
| V-007 | 隔离重启后 Snapshot/View 不依赖源码、网络或 Evidence 重解析 | architecture / product | A1/B/A2；no-payload exact Snapshot Read Bundles；answer 应用输入只有 package+Bundle；Projector 应用输入只有 package+sealed Result+result-scoped disposable Citation Store；目标仓库/原工作树/权威与旧 DB/完整 Evidence Store 均在递归 allow roots 外；exact macOS Seatbelt profiles/runtime+ancestor capability parameters | Bundle 绑定与无 payload 机械验证；exact typed candidate/inventory/path/diff 成功；同名 mention 返回 N candidates，full GA 唯一绑定；正常 workload 的 Source、Git、Evidence/DB、越界 file 与 network Operation 全 0；外部 preflight 后，Source remote/公网/DNS/TCP/Unix/越界文件/SQLite/Git/subprocess/Answer↔Projector 探测全部由 OS 拒绝并审计；不新建 Snapshot；独立 Projector 只读 exact seal+Store、无出站和答案回传端口；两角色真实 workload 均执行并 PASS | `ITER-003-RESULT-G2`；`var/iteration-003/g2/82aef7563556c70527b3c92227d0711a28437587/`；`evidence-summary.json`、`isolation-run.json`、`manual-review.md` | PASS / G3a unblocked |
| V-008 | G3a 无外部分派的完整回答权威链与故障关闭成立 | contract / interface | package-owned deterministic strategy；exact no-payload Bundle；Need遗漏、伪造/0/N/跨Session candidate、tampered result/page/commit、wrong Read Set、self-review、非精确 scalar、Evidence payload/network、unauthorized delivery faults | 可人工展开 Requirement/Needs→Candidate resolution→Plan→Result→Assessments→Draft→Review→Authorization→Delivery；每个 fault 拒绝；staging 绑定 clean HEAD/tree，connected valid chain 预冻结 expected PAGE digest，Projector 以带外 commit/PAGE 双锚点验证 isolated seal；应用拥有的 Provider Call=0、network Operation=0；另以真实 Seatbelt package+Bundle-only answer/projector 证明正常 workload 的 Source/Evidence/authority DB/Git/network/越权 file/process prohibited count 全 0，外部 preflight 后 deny probes 全命中；各层证据不得互相替代 | `ITER-003-RESULT-G3A`；`var/iteration-003/g3a/f2269ecca5c1e85e69fafd93fe599c841227f3c7/`；`evidence-summary.json`、`isolation-run.json`、`manual-review.md`、`independent-audit.md` | PASS / V-009 input preflight unblocked by later disclosure confirmation |
| V-009 | G3a exact Strategy 取得外部执行资格并先密封两条 Agent baseline | CC / CE / comparison-preflight | G3a `f2269ec…`；当前 `ITER-003-V009-EXACT-INPUTS@1.0.3` 所定 Provider/Adapter/requested+actual Model/credential、exact endpoint/default-deny egress policy、披露确认、Strategy `1.0.2`/Prompt `@3`/schema/tool/config、closed CE suite+standalone evaluator；controlled Direct `1.0.1` per-revision source closure 与 mature Agent protocol；旧 freeze 结果只作历史证据 | Conformance 调用前先密封 exact HEAD/tree/参数 invocation、调用后绑定 immutable Result，且 exact PASS；裸 Result 不可用于 CE，Provider outcome unknown 永久阻断该次 run；七个 required Case 各一次 no-tools 调用且无 hidden retry；模型输入无 projection/expected/forbidden/Product oracle；standalone evaluator 独立 PID/implementation digest 并 exact projection；FAIL/UNKNOWN=0、Result closed PASS/VALID；随后在任何 G3b 产品运行前密封同 exact 模型 controlled Direct 和 exact Codex CLI/model mature Agent 全部 runs；Direct 必须分别闭合 A/B required POM paths，union 只作 allowlist；V-009 direct transport 不证明 G3b Gateway/OS isolation；任一输入 pending/漂移禁止 G3b | attempts 1/2: CE 6/1/0；attempt 3 `ce54319…`: Conformance PASS、CE 7/0/0 PASS/VALID，但 baseline preflight 被 `FINDING-003-017` 阻断且未发请求；v1.0.3 full rerun pending | current not-run / blocks G3b |
| V-010 | G3b 隔离评测浏览器交付可审计世界模型回答 | interface / human | V-009 exact inputs与五个冻结问题；exact Provider endpoint/network policy | 与 V-007 同级双进程/存储隔离；仅 Browser→Answer/Projector、Answer→exact Gateway、Gateway→exact Provider endpoint 可通信，其他出站与 Answer→Projector 探测全部拒绝并审计；永久 `EVALUATION_ONLY` 水印；显示模式、commit、Snapshot/Read Set、Bundle digest、View、Profile/关系 modality、Coverage、View Limitation/Knowledge Gap、Fact/Evidence和完整权威链；不更新、不回源、不读 Evidence payload、不激活 | pending | not-run / blocks G4 |
| V-011 | 非硬编码、重复真实模型与预先密封源码 Agent 对照成立 | product | evaluator-only exact product suite/oracles、运行时随机身份+拓扑、每题至少 5 次含 cold process、V-009 两条 sealed baselines | 产品/模型对 expected/oracle/baseline results 读取为0；动态 Oracle 满足；unsupported why 返回 Knowledge Gap且不做 parity；其余逐题重大错误0，完整性不低于两条基线中更强者；全部失败保留；相对 controlled Direct 首问P95≤1.5x、重复P95≤0.5x，成熟 Agent 不做跨模型性能比 | pending | not-run / blocks acceptance |
| V-012 | ITER-002 旧数据库和 Snapshot 可兼容读取 | compatibility | 首次 persistence edit 前由 `40c6584…` 生成并冻结的 old-schema DB/报告 | 新代码打开原 artifact 后 exact legacy Snapshot/ID/digest/locator 仍可读；不冒充新 Structure Schema；不原地改写历史 | `ITER-003-RESULT-G1`；`focused-tests.log`、`frozen-input-hashes.log` | PASS / G1 persistence complete |
| V-013 | 新契约不破坏显式 Direct Investigation、旧模式和完整系统 | regression | 相关测试与完整 suite | 相关测试、完整回归通过；模式身份不混淆 | pending | not-run / blocks acceptance |
| V-014 | Scheduler、多源、旧 Scope Schema Migration 与 Production Activation | boundary | 明确非目标 | NOT EXECUTED | pending | non-blocking / cannot be inferred |

### V-007 macOS capability evidence interpretation

本轮本机 executor 使用固定 `/usr/bin/sandbox-exec`，其可证明事实是 deny-default Seatbelt
capability enforcement，不是 Linux mount/network namespace。Result 只能声称目标操作被实际 OS
policy 拒绝，不能声称宿主路径不存在、已 unmount 或 route 已删除。Answer 与 Projector 的应用
输入分别按上表收窄；解释器/runtime、精确设备/时区文件、独立输出和 literal ancestor directory
traversal 是单列的启动 capability，不得被算作产品输入或包含受限数据。Seatbelt 的 exact
ancestor `file-read*` 会暴露该目录的直接条目名，但不开放子文件内容；此 executor limitation
必须明确记录，不能描述为 metadata-only 或路径不可见。

原始证据必须保存 exact executable/profile/worker digest、`ANCESTOR_00`—`ANCESTOR_39` 的
展开值、recursive allow roots、staged physical manifests、外部可达性 preflight、不同 PID/nonce
的两个真实 child、每项 authorized/prohibited probe、实际 workload output、单向 seal transfer 和
运行前后 protected-input digest。Ancestor 参数只对每个 canonical runtime/role root 的自身与父
目录给出 literal traversal，不能用 `subpath` 放开祖先内容。所有 sandboxed Python 必须使用
`-I -S -B`；probe 与 workload 必须是同 profile 下的独立 child，role nonce 不同，所有 PID
互异，最终 output manifest 与声明集合精确相等。`plan` 固定是
`NOT_EXECUTED/NOT_EVALUATED`；即使 OS report 为 PASS，也只证明该边界，必须再与 exact
Bundle/View/Citation、查询不变性和人工内容核对共同形成 V-007 Result。

## Frozen mall oracle

- “reactor child modules”固定表示 root `modules` 元素的递归闭包，排除 root `mall` project；root 由 `SOFTWARE_SYSTEM` 表示。A/B 的 root 与所有 child `dependencies` 元素都属于完整扫描范围。
- A `a50870fba92d59021f07cacbe947442b1871e78f`：6 个 reactor child modules、6 条 `CONTAINS_MODULE`、5 条内部 `DEPENDS_ON`；连同 system root 是 7 Entity、11 Relation Fact；`mall-admin → mall-common` 只有 `mall-admin → mall-mbg → mall-common`。
- B `cfaadb201bb7aa6425de069fab5e57bf8b5048f3`：7 个 child modules、7 条 contains、7 条内部 depends；连同 system root 是 8 Entity、14 Relation Fact；路径有 `mall-admin → mall-mbg → mall-common` 与新增的 `mall-admin → mall-security → mall-common`。
- A→B 仅新增 `mall-security`、`mall → mall-security`、`mall-admin → mall-security`、`mall-security → mall-common`，没有内部图删除。B→A 时这些成员从新 CURRENT 消失，历史 B Snapshot 仍可读。
- `dependencyManagement`、Maven parent 与外部依赖不形成内部直接边。
- `CONTAINS_MODULE` 只表示 system 对递归 child module 的扁平成员关系，不表达 nested aggregator/parent 层级；`DEPENDS_ON` 只表示 POM 本地声明的直接内部依赖，不得把答案扩大为 effective、传递、compile 或 runtime 图。

## Frozen browser questions

1. 分别列出 A 和 B 的全部递归 Maven reactor child modules（不含 root `mall` project）。
2. 分别列出 A 和 B 中 `mall-admin` 到 `mall-common` 的全部简单内部依赖路径，并指出新增路径。
3. 只说明 A→B 的内部 reactor 模块图变化。
4. B 的 root POM `dependencies` 元素是否直接声明了 reactor 内部 `mall-security`？答案为否；root dependencies 已完整扫描，`dependencyManagement` 不算直接依赖。
5. `mall-admin` 到 `mall-search` 是否存在内部依赖路径？答案为当前内部图中不存在，不能扩大成“任何关系都不存在”。

## Frozen anti-hardcode and comparison protocol

- 每个冻结问题至少准备一个不改变语义的中文措辞变体；Requirement 必须保存原文并得到同一 Oracle。
- fixture 使用 `billing`、两个不同 group 的 `common-lib` 和 version mismatch 查询，证明答案使用 typed identity。
- 验证器在运行时生成身份、module path、节点数和边拓扑都由随机 seed 决定的 A/B 临时 reactor；seed 只在产品代码加载后产生，期望图由不导入任何产品 parser/query 代码的独立 generator 计算并记录 input/output digest。产品流程不得出现 mall、billing、固定拓扑或冻结标识分支。
- 问“为什么 B 新增 `mall-security`？”时，当前 Structure Coverage 不含变更意图，必须返回对应 Knowledge Gap，不能猜测或转入 Direct Investigation。
- G3a exact checkpoint 后、首次外部分派前记录 Provider、Adapter、Model、credential reference、Conformance 与披露确认；closed CE PASS/VALID 后，必须先按 G0 protocols 完成同模型 controlled Direct 与 exact Codex CLI/model mature Agent 两条基线，再进入隔离 G3b。每题至少五次且含独立 cold process，缓存状态和所有失败均保存；任何漂移重跑相应对照，不得看过世界模型结果后改弱基线或只挑成功样本。

测试、CC、CE、Product Validation 与 Activation 不得互相替代。人工只挑成功样本、问题触发源码回退或目标仓库仍可被读取都使 Gate 失败。
