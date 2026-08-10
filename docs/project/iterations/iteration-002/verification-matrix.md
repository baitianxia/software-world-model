---
id: ITER-002-VERIFICATION
kind: iteration-verification
status: pass
authority: evidence
owners: [quality]
depends_on: [ITER-002-PROPOSAL, PROJECT-GOVERNANCE-VERIFICATION, SYS-QUALITY-ACCEPTANCE]
code: [validation]
tests: [tests]
iteration: ITER-002
---

# Iteration 002 Verification Matrix

| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |
|---|---|---|---|---|---|---|
| V-001 | 当前文档授权链、ADR、Contract 和链接闭合 | contract | 当前工作区文档 | `scripts/docs.py check` 通过 | 2026-08-10：生成 derived docs 后检查通过 | PASS |
| V-002 | Question Checklist、Evidence Packet、Answer Draft、Review 和 Source 边界成立 | unit / contract | 当前工作区与相关测试 | 同包重写不读来源；缺证据补检索；越界引用拒绝；分段 Artifact 不碰撞 | 2026-08-10：Evidence-first 核心、模型、产品适配和浏览器相关 20 项测试通过 | PASS |
| V-003 | 跨模块回归没有破坏旧正式知识、管理、来源和接口能力 | regression | 当前工作区完整 `tests` 套件 | 全部通过 | 2026-08-10：451 项通过，耗时 16.364 秒 | PASS |
| V-004 | exact Ark Adapter 仍符合 no-tools 接口 | CC | 当前 endpoint、model、adapter 和 schema registry | PASS 且未过期、未漂移 | `ccrun_66bbedf18020445c9df5fac11526fda1`：Adapter `@8`、observed model `glm-5.2`、result digest `sha256:dee384a9…668f`；Evidence-first schemas 纳入当前 Strategy 实现摘要与重新资格化 | PASS / does not independently qualify strategy |
| V-005 | 问题理解、通用源码调查、证据生成、独立审核和定向重写在当前 Strategy 上成立 | CE | Evidence-first capability suite；Oracle 为冻结契约与 Codex 独立判断 | 每个职责及组合路径 PASS；审核能拒绝响应语言错误、时间顺序颠倒、未证实意图和题外自检；无工程/语言/题型特例 | Suite `1.3.0` 十类全部 PASS；Result `evaluation_result_26fdfbbea40b4c87aede82270eed68dd`，Qualification `sha256:3d529903…acd54` | PASS |
| V-006 | 陌生工程复杂问题答案正确、完整、可读且引用实际源码 | product | 冻结陌生工程与问题；Codex 按源码独立复核，不使用同一生成答案作 Oracle | 无重大错误、无关键遗漏、无机械证明转储；至少覆盖一次同包重写或明确无需重写 | 两个陌生 Java 工程六题、33 维度全部正确完整；系统与直接基线均 `1.000 / 1.000`，重大错误 `0`；Attestation `product_validation_dc02535f3c837cc0b469e14f51fef93d` | PASS |
| V-007 | 浏览器实际进入新主路径并可供人工体验 | interface / experience | 任意本地 Git 工程、中文与英文通用问题 | 返回经独立审核的自然答案、Evidence Packet ID 和源码位置；工程切换不串会话 | `local-browser` 已绑定当前资格和产品证明；真实页面连接 `poi-tl@58fdb6c7d9db` 后正确回答超时/异常传播问题，显示“已基于固定版本复核”、2 条事实与 2 处源码位置 | PASS |
| V-008 | 正式知识沉淀不阻塞同步回答 | architecture / contract | 模拟后台沉淀成功、失败和未运行 | 三种情况均不改变已审核同步答案；Evidence Packet 不获得 Snapshot 资格 | 契约已接受；后台调度实现不属于本切片同步验收 | non-blocking for chat / required before claiming async materialization |
| V-009 | 生产启用 | activation | 不在本轮范围 | NOT EXECUTED | 无 | non-blocking / cannot be inferred from local acceptance |
| V-010 | 本轮结果不能被解释为软件世界模型产品闭环已通过 | architecture / product boundary | Snapshot-first 问答、Structure View、独立更新、跨版本身份与删除语义均无本轮冻结运行 | NOT EVALUATED | `FINDING-002-031` 与最终 Acceptance | not-run / blocks any world-model completion claim; does not invalidate the narrow Evidence-first result |

V-001 至 V-007 的证据彼此独立。模型调用次数或 Token 上限只能导致失败关闭，不能通过减少检查清单、检索、引用或独立审核换取 PASS。历史旧路径资格和产品失败保留为架构变更证据，没有用于替代新实现的重新评估。V-008 的异步调度仍是本轮明确非阻塞边界；V-009 生产启用未执行；V-010 禁止把本轮局部 PASS 外推为软件世界模型完成。
