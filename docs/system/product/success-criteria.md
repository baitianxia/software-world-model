---
id: SYS-PRODUCT-SUCCESS
kind: system-product
status: current
authority: normative
owners: [product]
depends_on: [SYS-PRODUCT-VISION, SYS-QUALITY-ACCEPTANCE]
code: []
tests: []
---

# 长期成功标准

## 当前产品目标与 MVP 门槛

当前所有产品迭代必须共同逼近同一个目标：系统在提问前把经授权的软件来源构建成版本固定、可跨任务复用的软件世界
模型，并在未参与开发的真实工程上，通过同一个产品 Web 入口支持通用工程问答。默认 `ENGINEERING_QA` 把世界模型作为工程地图、手册、已知证据和检索入口，并在同一授权 exact revision 上按问题只读核实源码、仓库内文档、构建/运行配置和测试；严格 `WORLD_MODEL` 另行保留 Source-off 复用语义。这里的“通用”不是承诺所有问题都有答案，而是要求：

- 用户可以自由表述关于系统用途、结构、功能实现、调用过程、业务规则、条件与状态变化、配置和异常路径的问题，不能
  依赖预先枚举的题型、工程名、问题文本或关键词补丁；
- 问答能力可以动态分解 Need，并组合已经接受的结构、代码与行为知识；新增知识域必须进入同一查询和回答链，不能形成
  只能单独体验、不能与既有能力组合的孤立 Profile、View 或入口；
- `ENGINEERING_QA` 在请求开始前固定模式、exact revision、World Model Read Authority、Source allowlist、Provider disclosure 和资源熔断；只有隔离 Retrieval Worker 可以只读 Source，Answer/Reviewer 只读密封 Question Evidence Package，不触发同步 Knowledge Update，不静默切换 `WORLD_MODEL` 或 `DIRECT_INVESTIGATION`；
- 答案先回应用户目标并匹配期望抽象层级，代码细节只按问题需要展开；每个实质结论绑定包内真实引用，经授权软件来源仍不能证明的设计动机或其他内容明确返回 unknown/limitation；
- 在未参与实现的工程上，由独立评测方或用户持有、实现阶段不可见的 held-out 自由问题，加上验收现场临时提出的问题，
  答案重大错误为零，完整性逐题不低于同等输入与资源约束下成熟源码 Agent 中较强的有效基线。

在达到该门槛前，模块图、静态调用图、单个 Semantic View、解析器或固定问题集的 PASS 都只能作为中间证据，不能单独
称为产品 MVP。

系统达到产品价值必须同时满足：

1. 对目标任务的每个实质 Need 都能从同一密封 Question Evidence Package 重建支持链，或明确返回 unknown/limitation；严格世界模型验收仍以同一固定 Snapshot/Read Set 为唯一输入。
2. 用户可见 Claim 不扩张引用证据的 Context、Modality 或 Coverage。
3. 来源、生成、准入、发布、答案生成和答案审核之间不存在未授权旁路。
4. 更新后旧知识不会因局部成功被静默删除；并发失败不会产生部分正式状态。
5. 同等输入和资源约束下，系统答案相对成熟源码 Agent 不能出现任何重大事实错误，且结论完整性逐任务不得退步；同时单独证明预构建 World Model 产生可测的复用/检索价值。
6. 资格、有效期和启用范围可机械验证；过期、漂移或未知结果安全关闭。

测试数量、模型分数和一次运行的 PASS 只是证据，不是这些标准本身。
