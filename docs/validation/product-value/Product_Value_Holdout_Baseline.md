# Software World Model 产品价值留出测试基线

## 1. 基线身份

- 基线编号：`PV-HOLDOUT-001`
- 冻结日期：2026-08-01
- 被测工程：`macrozheng/mall`
- 固定 Revision：`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`
- 状态：**已冻结，尚未执行**
- 冻结时点：在增加通用正式知识检索工具、修复 Endpoint 复合 Evidence 之前

冻结前核对修正：初稿曾误记领券方法没有事务声明；在任何 Demo 代码修改或基线执行前，已按 Service 接口上的 `@Transactional` 和数据库约束证据修正 H-02。此后不得再改变题目和计分点。

本基线用于检验 Software World Model 是否能在不读取源码、不使用生产双路径的前提下，达到通用模型直接调查同一 Git 工程的任务完成度、正确性与关键证据覆盖下限。题目不是 Demo 构建配置，也不得转写成专用 View、专用规则或题目相关代码。

## 2. 隔离与执行规则

### 2.1 Software World Model 组

- Agent 只能通过公开的 Application / CLI 知识工具读取当前正式 Snapshot。
- 禁止读取 `validation-projects/mall`、SQLite 内部表、Artifact 原始 Payload、本文件黄金答案及直接调查组输出。
- 允许模型动态形成 Knowledge Requirement、组合通用搜索、单跳关系遍历和批量 Evidence 解释。
- 正式知识不足时只能报告 `KNOWLEDGE_GAP`，或通过正常 Knowledge Update 构建、审核并发布新 Snapshot 后重试；禁止临时读取源码补答案。

### 2.2 直接调查基线组

- 使用同等级基础模型，直接读取固定 Revision 的 Git 工程。
- 禁止读取 Demo、Software World Model 数据库、本文件黄金答案及另一组输出。
- 该路径只用于隔离评测，不是生产回答路径。

### 2.3 评分与成本

- 每题 10 分，总分 50 分；只评分事实、边界和证据，不评分文风。
- 另行记录：首次知识构建成本、每题端到端耗时、模型调用次数、知识工具调用次数、重复执行成本和 Snapshot 大小。
- 错误陈述不能用更多正确陈述抵消；与核心结论相冲突的错误，至少扣除其所在评分项全部分值。
- `KNOWLEDGE_GAP` 不算事实错误，但相应未完成项不得分。
- 执行前不得用这五题调试实现；首轮整套结果产生后才能诊断和迭代。

### 2.4 判定门禁

P0 非回归门禁同时满足才算通过：

- Software World Model 组没有直接调查组未犯的核心事实错误；
- 每题得分不低于直接调查组的 90%，且不得低于 8 分；
- 五题总分不低于直接调查组的 95%；
- 所有正式答案中的实质性 Claim 均能追溯到当前 Snapshot 的 Fact / Inference 及 Evidence；
- 未建模或覆盖不明时明确报告边界，不用空搜索证明“不存在”。

只有通过 P0 后，才评价复用、稳定身份、版本一致性、增量成本等 Software World Model 的额外价值。未通过时先判断是通用工具受限、正式知识缺失、模型调查失败还是审核失败，不能用生产源码兜底掩盖问题。

## 3. 冻结题目与黄金评分量表

### H-01：Maven 内部模块依赖图

**题目**

> 仅依据 Maven 描述文件，重建该项目内部模块的直接依赖图。请把聚合关系、dependencyManagement 声明和实际 dependency 边严格区分，并给出可行的拓扑分层及全部传递可达关系；不要把第三方依赖纳入图中。

**黄金要点**

- 根 POM 聚合 7 个模块。
- 实际直接依赖共 8 条：
  - `mall-mbg → mall-common`
  - `mall-security → mall-common`
  - `mall-demo → mall-mbg`
  - `mall-admin → mall-mbg`
  - `mall-admin → mall-security`
  - `mall-search → mall-mbg`
  - `mall-portal → mall-mbg`
  - `mall-portal → mall-security`
- 可行拓扑层：`mall-common → {mall-mbg, mall-security} → {mall-demo, mall-admin, mall-search, mall-portal}`。
- 应列出由直接边产生的传递可达关系，并确认图中无环。
- 聚合、`dependencyManagement` 与实际 `dependency` 不是同一种关系；版本管理声明不能当作依赖边。

**关键证据**

根 `pom.xml` 与七个 `mall-*/pom.xml`。

**10 分量表**

- 1 分：列全 7 个模块。
- 1 分：正确区分聚合、版本管理和实际依赖。
- 4 分：列全 8 条直接边，每两条 1 分；错误边在同档扣分。
- 2 分：拓扑分层正确。
- 1 分：传递可达关系正确。
- 1 分：无环结论及 POM 证据。

### H-02：会员领取优惠券的控制流与一致性边界

**题目**

> 从 `POST /member/coupon/add/{couponId}` 入口开始，完整说明一次请求的控制流、所有可观察终止结果、成功时写入/更新的数据，以及实现对重复领取、并发与多步写入一致性所能提供的保证。只陈述源码能够证明的保证。

**黄金要点**

- 获取当前会员和 Coupon。
- 按顺序拒绝：Coupon 不存在、库存不大于 0、未到启用时间、该会员历史领取数达到 `perLimit`。
- 成功时插入 Coupon History：16 位领取码由毫秒时间后 8 位、4 位随机数字、会员 ID 补齐或截取后的 4 位组成；`getType=1`、`useStatus=0`，并设置会员与领取时间等字段。
- Coupon 数量减 1；`receiveCount` 为 `null` 时设为 1，否则加 1；Controller 返回成功。
- Service 接口方法声明了 `@Transactional`；在正常 Spring 代理调用下，两次 Mapper 写入处于同一事务，业务异常属于运行时异常并触发默认回滚。
- 源码没有行锁、原子条件更新或相应唯一约束，仍不能保证并发下不超领或不丢失更新。事务原子性与并发竞争保证必须分开陈述。

**关键证据**

`UmsMemberCouponController.java`、`UmsMemberCouponService.java`、`UmsMemberCouponServiceImpl.java`、`GlobalExceptionHandler.java`、`SmsCoupon.java`、`SmsCouponHistory.java`、两个 Mapper / Example，以及 `document/sql/mall.sql`。

**10 分量表**

- 1 分：入口与当前会员。
- 3 分：四个拒绝条件及顺序。
- 2 分：History 字段。
- 1 分：领取码规则。
- 1 分：Coupon 计数更新。
- 1 分：响应结果。
- 1 分：正确区分事务原子性与并发隔离 / 竞争保证。

### H-03：购物车促销计算规则

**题目**

> 对 `GET /cart/list/promotion` 触发的计算，给出从购物车行到 `CartPromotionItem` 的完整确定性规则。须覆盖输入筛选与分组、促销资料装配、每一种分支、档位选择、金额/库存/积分字段、输出次序，以及关联资料缺失时源码所定义的结果。

**黄金要点**

- 读取当前会员的全部有效购物车项；只有 `cartIds` 非空时才过滤。
- 按 `productId` 使用 `TreeMap` 分组，并批量查询促销资料。
- `promotionType=1`：显式用 SKU 促销价覆盖输出价格，单件减免为 SKU 原价减促销价。
- `promotionType=3`：按同一 SPU 跨 SKU 总数量，阶梯 `count` 降序选择最高满足档，单件减免为 `SKU 原价 × (1 - discount)`；输出价格仍由属性复制保留购物车行价格。
- `promotionType=4`：按 SKU 原价乘数量计算同一 SPU 总额，`fullPrice` 降序选择最高满足档，单件分摊为 `SKU 原价 / 总额 × reducePrice`，采用 `HALF_EVEN`；输出价格仍由属性复制保留购物车行价格。
- 其他类型或未达到档位：无优惠，`reduceAmount=0`。
- `realStock=stock-lockStock`，积分和成长值来自商品资料。
- `TreeMap` 使 SPU 按 ID 升序，组内保留输入次序。
- 关联 Product 缺失会在读取 `promotionType` 时抛出空指针；需要 SKU 的分支缺 SKU 会在解引用时报错；无优惠路径只是不设置 `realStock`。

**关键证据**

`OmsCartItemController.java`、`OmsCartItemServiceImpl.java`、`OmsPromotionServiceImpl.java`、`PortalProductDao.java/.xml`、`PromotionProduct.java`、`CartPromotionItem.java`。

**10 分量表**

- 1 分：入口与筛选。
- 1 分：分组与 DAO 装配。
- 2 分：类型 1。
- 2 分：类型 3。
- 2 分：类型 4。
- 1 分：默认分支及公共字段。
- 1 分：输出顺序与缺失资料行为。

### H-04：JWT 迁移提交的语义影响

**题目**

> 比较提交 `dacce5f28dfc1734f2db09668d928d7fac2a3a7a` 与其父提交，说明它在依赖、令牌生成、解析/验签、过期判断、校验和刷新上的全部语义影响。把源码可证明的结论与依赖库默认行为造成的未知项分开。

**黄金要点**

- 父提交为 `00bd035…`，修改范围为根 POM、`mall-security/pom.xml`、`JwtTokenUtil.java`。
- 根/安全 POM 移除 JJWT 版本、`dependencyManagement` 和直接依赖。
- `Claims/Jwts/HS512` 改为 `JWTUtil`，Secret 改为 UTF-8 字节。
- `exp` 从 JJWT `Date` 设置改为手工毫秒 `long`；解析先验签，再读取 Map。
- 坏签名或格式返回 `null`；校验新增用户名空值保护。
- 无 `exp` 时新实现判为未过期；错误或不可转换的 `exp` 判为过期。
- 刷新同时接受 `created` 的 `Long` / `Date`；30 分钟内返回原 Token，否则重新签发。
- 不能只凭仓库断言 Hutool `createToken` 的默认算法；旧注释中的 HS512 不能作为新实现证据。

**关键证据**

目标 Commit、父 Commit、根 `pom.xml`、`mall-security/pom.xml`、`JwtTokenUtil.java`。

**10 分量表**

- 1 分：父提交与三文件范围。
- 2 分：依赖变化。
- 2 分：生成与 `exp`。
- 2 分：解析、校验与异常。
- 2 分：刷新。
- 1 分：正确标注算法等证据边界。

### H-05：`listCart` 优惠券可用性与边界反例

**题目**

> 为 `UmsMemberCouponServiceImpl#listCart` 写出与实现等价的优惠券可用性判定规范，并审查它在金额、时间、使用范围和请求分类的边界上是否自洽。必须用覆盖边界的正例/反例消解任何歧义；不得用注释代替代码证据。

**黄金要点**

- DAO 只读取当前会员且 `use_status=0` 的 Coupon History。
- 金额为 `(price-reduceAmount) × quantity`；`useType=0` 统计全车，`useType=1` 仅统计关联分类，`useType=2` 仅统计关联商品。
- 共同时间条件为 `now.before(endTime)`；范围 1/2 还要求 `total.intValue()>0`；门槛均使用 `(total-minPoint).intValue()>=0`。
- 反例：`total=99.50, minPoint=100` 会被判可用；范围相关总额 `0.50, minPoint=0` 会因 `intValue()==0` 被判不可用。
- 恰好等于 `endTime` 不可用；未检查 `startTime`。
- 未识别的 `useType` 不进入可用或不可用集合。
- 请求 `type==1` 返回可用集合；其他非空值都返回不可用集合；`null` 会空指针。Controller 文档声称 0/1，但实现没有校验。

**关键证据**

`UmsMemberCouponServiceImpl.java`、`UmsMemberCouponController.java`、`SmsCouponHistoryDao.xml`、`CartPromotionItem.java` 及关系模型。

**10 分量表**

- 1 分：数据范围。
- 2 分：金额公式与三种使用范围。
- 2 分：三个分支的精确谓词。
- 2 分：至少两个有效边界反例。
- 1 分：时间边界。
- 1 分：`useType` / `type` 分区。
- 1 分：注释与代码证据边界。

## 4. 已知但不豁免的架构压力

- 当前正式知识图能够表达 Maven 模块依赖、Java 类型/方法、部分调用、失败条件和有限历史事实，但不保证已经表达参数值、一般控制流、数据流、事务、并发语义、MyBatis XML 语句或任意 Commit 的完整 Diff。
- 这些缺口正是测试内容，不得从评分中删除。通用查询工具只能释放已有正式知识，不能把未建模 Artifact 伪装成已知 Fact。
- 若首轮失败，应据此决定 Knowledge Update 需要增加哪些模型主导认知能力和哪些系统可信约束；不得为 H-01 至 H-05 编写专用解析路径。
