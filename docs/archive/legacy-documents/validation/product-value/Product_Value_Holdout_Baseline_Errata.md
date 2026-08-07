# PV-HOLDOUT-001 冻结基线勘误

## E-001：H-03 单品促销输出价格

- 发现时间：2026-08-02，首轮两组结果均完成且独立评分产生之后
- 原冻结文件与 SHA-256：保持不变，作为实验预注册记录
- 影响范围：H-03 `promotionType=1` 的一个黄金答案短语及据此产生的首次评分

冻结基线写成：

> 显式用 SKU 促销价覆盖输出价格

固定 Revision `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` 的源码实际为：

```java
BigDecimal originalPrice = skuStock.getPrice();
cartPromotionItem.setPrice(originalPrice);
cartPromotionItem.setReduceAmount(
    originalPrice.subtract(skuStock.getPromotionPrice())
);
```

因此正确黄金答案是：

> `promotionType=1` 显式用 SKU 原价覆盖输出价格，单件减免为 SKU 原价减 SKU 促销价。

证据位置：`mall-portal/src/main/java/com/macro/mall/portal/service/impl/OmsPromotionServiceImpl.java:48-52`。

两组答案都陈述为 SKU 原价，均不应在该项扣分。该修正不能用于改变题目、增加评分项或修改实现，只用于消除冻结黄金答案自身的事实错误。

## E-002：H-03 无优惠路径的 `realStock` 表述边界

冻结基线中的“无优惠路径只是不设置 `realStock`”只适用于 **SKU 关联缺失** 的情况，不表示无优惠路径永远不设置该字段。源码规则是：

- 找到 SKU：`realStock = stock - lockStock`；
- 找不到 SKU：继续输出该行，但不设置 `realStock`。

证据位置：同文件 `159-171`，尤其是 `165-168` 的空值判断。

因此，只陈述无优惠 helper 在正常 SKU 存在时设置 `realStock` 并不构成错误；没有说明缺 SKU 分支则属于该评分点的信息不完整。

## E-003：H-03 满减档位排序与“最高档”结论

冻结基线将满减档位选择概括为“按 `fullPrice` 降序选择满足条件的最高档”。该表述比源码能够无条件证明的语义更强。

固定 Revision `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` 的实际比较器为：

```java
productFullReductionList.sort((o1, o2) ->
    o2.getFullPrice().subtract(o1.getFullPrice()).intValue()
);
```

随后代码按排序结果顺序遍历，并返回第一个满足订单金额条件的档位。由于 `BigDecimal` 差值会先转换为 `int`：

- 绝对值小于 `1` 的非零差值会被截断为 `0`，两个不同价格可能被比较为相等；
- `List.sort` 为稳定排序，因此被比较为相等的档位保留原相对顺序；
- 在缺少额外金额取值域约束时，不能把该实现无条件等同于严格数值降序，也不能无条件断言一定选择数值最高档。

准确的源码级结论应为：

> 系统按 `subtract(...).intValue()` 比较器稳定排序满减档位，再返回排序结果中第一个满足条件的档位。只有在正式知识能够证明该输入域上比较器符号与 `fullPrice` 的严格数值顺序等价时，才可进一步推断为“选择满足条件的最高档”。

证据位置：`mall-portal/src/main/java/com/macro/mall/portal/service/impl/OmsPromotionServiceImpl.java:175-188`。

该勘误修正 H-03 的黄金答案语义边界，也约束架构能力验证中的语义推断：模型或规则不得忽略比较器的截断行为；无法证明输入域约束时必须保留限制条件，而不能把更强结论作为 Fact 或无条件 Inference 发布。冻结基线本身继续保持不变。

## E-004：H-04 十分量表不能充当完整 Direct Claim Oracle

- 发现时间：2026-08-05，JWT validation-only Formal Contract 可执行性复核期间
- 原冻结文件与 SHA-256：保持不变，作为实验预注册记录
- 影响范围：H-04 后续架构能力验证的“同样正确、完整”判定；不追溯修改首轮 `1 / 10` 分数

冻结 H-04 黄金要点适合做粗粒度回归评分，但没有枚举源码中每个可以独立失败的边界。至少包括：

- 新过期判断使用严格的 `expTime < System.currentTimeMillis()`；两值恰好相等时该表达式返回未过期。
- 非 `Long` 的 `exp` 会转为 `Number` 后调用 `longValue()`；非 `Number`、空 Payload 或其他异常被捕获并视为过期。`Double` 等 `Number` 的小数部分会被 `longValue()` 截断。
- `created` 只显式接受 `Long` 或 `Date`；缺失或其他类型使 `tokenRefreshJustBefore` 返回 `false`，随后走重新签发分支。
- 30 分钟刷新窗口两端都是严格边界：`now > created` 且 `now < created + 1800s`；等于任一端点都不返回原 Token。
- `getExpiredDateFromToken` 改为只把 `Long / Integer` 转为 `Date`、其他类型返回 `null`，但目标版本中该 private helper 已没有正常调用点；“实现变化”与“可达运行影响”必须分开。
- 新 Token 自身的 `created` 序列化后会以何种 Java 类型被 Hutool 重新解析、`JWTUtil.createToken` 默认使用何种算法，以及旧 JJWT `String secret` 的具体库内解释，都不能仅由当前仓库源码确定；这些需要独立依赖库正式前提。

因此，两个答案可能都获得 H-04 `10 / 10`，却遗漏不同的实质 Claim，或者一方增加了错误结论。后续 JWT Capability Run 必须在被测运行前重新执行 Direct Agent，并冻结逐 Claim 的 Direct Claim Oracle；Software World Model 的 Delivered Claim 与全部实质 Oracle Item 必须按 target、context、modality、条件和限制双向守恒。10 分量表只在逐 Claim 门禁通过后作为辅助分数，不能单独证明“至少同样正确、完整”。

对应 Contract 修订见 [JWT Validation Formal Contract Revision 002](../../implementation/iteration-001/contracts/ITER-001-JWT-Validation-Formal-Contract-Revision-002.md)。
