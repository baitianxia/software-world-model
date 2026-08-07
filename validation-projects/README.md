# 外部验证项目

本目录保存 Software World Model 的独立验证输入。三个子目录都是各自的 Git 仓库，不属于平台源码、System 文档或本仓库 Baseline；父仓库只跟踪本说明，不跟踪外部历史或把它们创建为 gitlink。

| 本地目录 | 用途 | 本地 Checkout / 任务绑定身份 |
|---|---|---|
| `mall/` | 完整回归与历史 Demo；JWT 架构/能力验证 | Checkout HEAD `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`；JWT 单独绑定 target `dacce5f28dfc1734f2db09668d928d7fac2a3a7a` 与 parent `00bd03591cfd91f82ebe48787315eed613754277`，不要求 target 是 HEAD 的祖先 |
| `transmittable-thread-local/` | 未见项目产品验收 | tag `v2.14.5` / `9c6552bbd7eda52b7bfb03c24c4f9aee514e91f3` |
| `poi-tl/` | 未见项目产品验收 | tag `v1.12.2` / `58fdb6c7d9db7da53cd420ff1ebde49813bd7af2` |

## 本地准备

在仓库根目录执行；不要把平台专用答案、评分规则或运行结果写入这些工程：

```bash
git clone https://github.com/macrozheng/mall.git validation-projects/mall
git -C validation-projects/mall checkout --detach 0504e86b1f1b6f1b8aa6a734d37a90fb67346be7

git clone --branch v2.14.5 --single-branch \
  https://github.com/alibaba/transmittable-thread-local.git \
  validation-projects/transmittable-thread-local

git clone --branch v1.12.2 --single-branch \
  https://github.com/Sayi/poi-tl.git \
  validation-projects/poi-tl
```

产品验证的精确 Commit、Tree、远程身份、许可证摘要、六个问题和资源限制由 [`validation/product_holdout_iteration_002/suite.json`](../validation/product_holdout_iteration_002/suite.json) 固定。执行前离线校验：

```bash
PYTHONPATH=src:. python3 -m validation.product_holdout_iteration_002.cli verify-inputs \
  --workspace-root .
```

完整生产测试包含依赖这些 Checkout 的 Case，并按各自 Fixture 校验适用的目录、工作区、Revision、Tree、Tag、Remote、License 或清洁状态条件；任一适用条件不成立时，相关测试按设计失败关闭。这属于环境前置条件，不是可以跳过的普通缓存。

上段 Tree/Tag/License/工作树条件适用于 Product Holdout 的两个工程；mall 的 JWT 条件由 [`validation/jwt_iteration_001/manifest.py`](../validation/jwt_iteration_001/manifest.py) 固定并按其 remote、target、parent 与 Git object 规则校验。不同 Fixture 的条件不能互相套用。
