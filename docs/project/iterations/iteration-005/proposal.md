---
id: ITER-005-PROPOSAL
kind: iteration-proposal
status: accepted
authority: project-proposal
owners: [product, engineering]
depends_on: [ITER-004-RESULT-ACCEPTANCE, SYS-PRODUCT-VISION, SYS-PRODUCT-SUCCESS, SYS-QUALITY-ACCEPTANCE]
code: []
tests: []
iteration: ITER-005
coding_input: false
---

# ITER-005 Proposal：用户指定 Maven 仓库的软件世界模型工作区

## Trigger and evidence

当前不是缺少世界模型知识内核，而是产品组合仍被验收数据绑死：

- `ApplicationRuntime` 和 CLI 已能配置任意本机 Local Git、解析 exact commit、构建 Maven Structure Snapshot、打开
  Read Session，并生成 Snapshot/Ordered no-payload Bundle；相关聚焦测试实际运行 5/5 PASS。
- 对 `validation-projects/transmittable-thread-local@9c6552b…` 的临时冷探针在零问题状态成功发布 COMPLETE
  Snapshot，证明入口不是 mall 专用；该仓库只有单一 Entity，不能替代多模块泛化验证。
- ITER-004 launcher 仍硬编码 ITER-003 product commit、`var/` 工件和
  `ORDERED_A_B / EXACT_B / EXACT_FIXTURE_VALID` 三个 dataset，用户新构建的 Bundle 无法进入浏览器。
- 当前 Maven 更新逐次扫描完整 Git tree 并读取 covered POM，是完整重建式更新，不是真 Delta 增量。
- 当前页面声称覆盖“插件、属性、父子结构”，但 `MAVEN_REACTOR_STRUCTURE@1` 只正式表达递归 reactor child
  membership、POM 本地声明的直接内部依赖及 Snapshot 差异。这是可复现的界面实现错误，不是 Schema 已具备该能力。

因此下一轮最短缺口是：把已经存在的更新、Snapshot、Bundle、View 和问答能力连接到用户指定仓库，并在进入浏览器
开发前先证明当前 Maven Profile 对真实多模块项目有足够适用性。

## Outcome and users

本机开发者或评测者可以：

1. 用一个受控管理入口登记符合当前 Profile 的本机 Maven Git 仓库；
2. 在没有提问、Question、Task 或 Session 的情况下，对指定 exact commit 完成构建或更新；
3. 得到可人工检查的 Snapshot、Coverage、结构图、Bundle Receipt 和动态 Read Set；
4. 关闭源码访问并重启读取服务后，仍能选择该 Read Set 在浏览器中回答模块、直接内部依赖、路径和版本差异问题；
5. 仓库产生新提交后只在用户显式更新时产生新 Snapshot；旧 Snapshot 和已打开 Read Set 保持不变。
6. 通过 `src/software_world_model` 提供的稳定本机 Web 启动命令进入统一页面，而不是运行 iteration-specific validation
   script；后续世界模型迭代继续复用该入口展示新增能力。

这直接验证“软件世界模型可被独立构建、跨任务复用、更新与提问解耦”，而不是把浏览器包装成另一个读源码 Agent。

## Scope / non-goals

本轮只支持 `MAVEN_REACTOR_STRUCTURE@1` 与其冻结 Evaluation Context。所谓“用户指定仓库”是指符合该 Profile 的
本机 Maven Git 仓库，不表示任意语言、任意 Maven 工程或任意软件问题。

明确不做：

- Scheduler、文件监听或来源事件自动刷新；
- 提问触发 Update、临时生成 Bundle 或 Direct Investigation 回退；
- 真 Delta 解析、性能优化或把完整重建称为增量更新；
- 多 Source Binding 融合、其他语言、Behavior、Business、History 或新 Semantic View；
- Schema Evolution、对话记忆、认证、网络部署和 Production Activation；
- 把仓库路径、权威数据库、Evidence payload 或更新能力交给 Answer worker。

本轮所称“正式 Web 入口”是产品代码拥有、System Operations 记录、可重复启动的本机 loopback 入口；由于尚无认证和
Production Activation，它仍只能以 `WORLD_MODEL / EVALUATION_ONLY` 运行，不等于公网或生产部署。

## Adopted system IDs

- `SYS-CONTRACT-APPLICATION-MANAGEMENT`
- `SYS-CONTRACT-APPLICATION-KNOWLEDGE-UPDATE`
- `SYS-CONTRACT-SOURCE-ARTIFACT`
- `SYS-CONTRACT-KNOWLEDGE-STRUCTURE-MODEL`
- `SYS-CONTRACT-KNOWLEDGE-SNAPSHOT-PUBLICATION`
- `SYS-CONTRACT-KNOWLEDGE-PERSISTENCE`
- `SYS-CONTRACT-APPLICATION-KNOWLEDGE-USE`
- `SYS-CONTRACT-APPLICATION-STRUCTURE-VIEW`
- `SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING`
- `SYS-ARCH-DEPLOYMENT`
- `SYS-CONTRACT-AI-MODEL-GATEWAY`
- `SYS-OPS-LOCAL-BROWSER`
- `SYS-QUALITY-SECURITY`
- `SYS-QUALITY-ACCEPTANCE`

## Development slices and dependencies

### SLICE-001：Maven 工作区、独立更新与动态 Read Set

先用当前代码对两个未参与实现的多模块 Maven 仓库，以及同一 Scope 内“有效 revision → 明确不支持 revision”的序列
执行 G0。只有两个受支持仓库都能产生与独立 Oracle 一致的 COMPLETE Structure，且拒绝序列保持旧 CURRENT，才实现
一个高层、幂等、可恢复的管理工作流：登记仓库 → exact revision → Snapshot → Bundle → 动态 Read Set Catalog。该
Slice 不调用模型、不实现浏览器写操作，并提供可人工展开的报告。

若 G0 暴露当前 Profile 对真实多模块仓库普遍不适用，立即停止；不得先做动态浏览器再用题型补丁掩盖上游缺口。

### SLICE-002：正式本机 World Model Web 问答入口

仅在 SLICE-001 Result 被人工接受后再单独授权，但它是本轮完成的必需 Slice，不是可选后续。产品自有 Web 入口从已
验证的动态 Catalog 枚举 exact Read Set，不再依赖固定 dataset ID、mall/fixture 分支或 `validation.*` 启动器；问题请求
仍只包含 `request_id + read_set_id + question`。Answer、Gateway、Broker、Projector 继续遵守既有隔离边界，并在新仓库
上重新执行产品验证。

## Risks and unknowns

1. **Profile 适用性：** external parent/BOM、active profile、不支持 type/classifier 或不可求值 property 可能使真实仓库
   正确地失败关闭；G0 必须先量化，不得把拒绝改成猜测。
2. **第二权威风险：** 动态 Catalog 固定为 `SWM-READ-SET-CATALOG@1`：由 trusted Management/Knowledge Use 在权威
   数据库可见时生成的、不可变且 digest-sealed 的 no-payload manifest。它内嵌机械验证所需的 exact Bundle Receipt、
   相对 Bundle locator 与完整 file manifest/digest，只引用 Workspace、Scope、Snapshot/Read Session 和
   Profile/Coverage；不能复制 Entity/Fact、重解释或修补知识。读取进程只挂载该 Catalog root 和 Bundles，不读取权威
   数据库。
3. **跨 Owner 恢复：** Snapshot 已发布但 Bundle 失败时，不能伪造全局回滚。新版本必须标为
   `READ_BUNDLE_UNAVAILABLE`，旧可查询版本继续可用，恢复沿原幂等步骤继续。
4. **问答泛化：** 当前解释器只支持封闭的 Structure operation vocabulary；未知措辞必须形成明确 Limitation/Gap 或
   失败关闭，不能在 Provider 分派前变成无解释内部错误，也不能回源。
5. **资格漂移：** 若 Answer、Prompt、Strategy、Provider 配置或隔离 package 改变，必须重新执行 CC、closed CE 和完整
   Product Validation；仅改变 trusted catalog/launcher 也必须做新仓库产品验证。
6. **成本误称：** 本轮记录 TREE/POM reads、bytes 和时间，但不承诺真增量收益。
7. **动态隔离：** 历史 mall 路径探针不能证明新 Workspace 安全。每个产品 Workspace 都必须把其 actual repository、
   `.git`、authority DB、Evidence Store 和其他角色输出纳入新的沙箱外可达/Answer 内拒绝探针。

## Verification and acceptance

每个阻断 Gate 都必须产生人工可看的内容，而不只给测试数字：

- G0：三仓兼容性表、exact commit、独立结构 Oracle、拒绝原因和当前 Profile 边界；
- SLICE-001：零问题 R1→R2 更新报告、Root/State、结构图/diff、删除项、Source 操作、Snapshot/Bundle/Catalog digest，
  以及 Source-off 重启后的数据集/View 页面；
- SLICE-002：新仓库动态数据集页面、supported answer、Knowledge Gap、A/B diff、十阶段 Authority、独立 Citation，
  稳定产品启动命令，以及提问前后 Update Attempt/CURRENT/Source Operation 不变报告；
- 最终产品 Gate：在 World Model 结果产生前冻结的新仓库、问题、Oracle、controlled Direct 与成熟 Source Agent 对照；
  全部失败保留，逐题重大错误为 0且完整性不低于两条可评 baseline 中较强者，不允许固定项目名、dataset ID、问题文本
  或拓扑分支。

完整接受还要求从正式本机 Web 入口人工提交至少一条 supported question 和一条边界/Gap question、所有 Finding 已
处置、相关测试与全量回归通过、current System 文档和启动手册按实际能力回写，并继续明确 Production Activation
`NOT_EXECUTED`。SLICE-001 即使独立通过，也不能形成 ITER-005 Acceptance。

## Authorization decision

用户于 `2026-08-11T18:10:12+08:00` 明确要求开发 ITER-005，本 Proposal 已接受。G0 exact 输入与独立 Oracle 已冻结并在
baseline `a91dc7c…` 上通过；Workspace/Catalog Owner 与持久化边界已写回 current System Contract。因此当前只授权
`ITER-005-SLICE-001`。SLICE-002 的 exact product/Provider 输入仍未冻结，不会因前一 Slice 通过而自动获得授权；未完成
SLICE-002 时本 Iteration 必须保持未完成，Production Activation 仍不授权。

后续授权与结果由 Readiness addendum 和 Result 拥有：用户已接受 SLICE-001、授权 SLICE-002 编码，并分别对 exact live
suite 作披露授权；`run-007` engineering gate 已 PASS，当前等待用户接受 SLICE-002 / ITER-005 Result。该后续状态不改变
本 Proposal 当时只授权 SLICE-001 的历史决定，也不授权 Production Activation。
