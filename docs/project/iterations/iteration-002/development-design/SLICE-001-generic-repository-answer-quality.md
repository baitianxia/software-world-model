---
id: ITER-002-SLICE-001
kind: development-slice
status: completed
authority: historical-development
owners: [engineering]
depends_on: [ITER-002-PROPOSAL, SYS-ADR-013, SYS-ARCH-INVARIANTS, SYS-CONTRACT-SOURCE-ARTIFACT, SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING, SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL, SYS-CONTRACT-AI-CAPABILITY-EVALUATION, SYS-OPS-LOCAL-BROWSER]
code: [src/software_world_model, validation]
tests: [tests]
iteration: ITER-002
coding_input: false
---

# SLICE-001：通用工程问答可验收

## Status and dependencies

本 Slice 已按本机 Evidence-first 同步问答范围完成，不再是当前编码输入。根据 `FINDING-002-024` 和 `SYS-ADR-013`，本轮把浏览器问答改为证据优先路径；该历史结果不等于软件世界模型问答、后台知识沉淀或 Semantic View 已完成。

## Current vs expected behavior

旧行为把回答拆为需求、正式事实、事实复核、推理、充分性、答案选择、顺序和最终审核。复杂问题即使已取得正确源码，也可能因任一中间对象失败而没有答案，或把证明记录机械平铺给用户。

期望行为统一执行：保持原问题并形成检查清单；在 exact revision 和 Binding 内只读调查；把实际 Artifact 内容密封为 Evidence Packet；综合多条证据形成自然答案；由隔离审核角色从原问题逐项检查；若现有证据足够，携带具体 Finding 在同一 Packet 上重写；只有审核证明缺证据时才补充调查。答案通过后，知识沉淀可以独立异步执行。

## System contracts and invariants

执行遵守 `INV-002`、`INV-003`、`INV-004`、`INV-007`、`INV-008`、`INV-011`、`INV-012` 和 `INV-014`。正式知识仍只有 Admission / Publication 单路径；任务 Evidence Packet 没有正式知识资格。所有项目、语言、框架、文件名、符号类别和问题类型使用同一问题—证据—答案协议，不得添加定制分支。

## Interfaces and affected code

- `evidence_answer.py`：Question Checklist、Evidence Packet、Answer Draft、Review Finding、来源调查和 Response Control 编排。
- `evidence_answer_strategy.py`：问题理解、自然答案生成和独立审核三个隔离 no-tools 模型角色。
- Source Integration / SQLite：保持 exact 只读授权；分段 Artifact 身份包含实际 Coverage。
- Runtime / HTTP / Browser：浏览器优先进入证据问答，直接显示经审核的自然答案和实际源码位置；旧正式知识接口继续兼容。
- `validation`：能力评估和陌生工程产品验证改为评估新主路径；旧资格不能证明新实现。

## Compatibility, data and security boundaries

旧的 Knowledge Update / Use、Natural Task 和已发布 Snapshot 不删除、不改写，可继续由显式接口或后台任务使用。新浏览器响应使用 Evidence Packet ID，而不伪造 Snapshot ID。浏览器仍无认证且只允许 `127.0.0.1`；用户工程只读，Secret 不持久化。源码只会在明确授权的模型调用边界内作为 Evidence Packet 内容发送给已配置 Provider。

## Open questions and implementation risks

本切片没有需要用户选择才能继续的架构问题；以下失败、恢复和质量风险由实现与验证关闭。

- 结构化输出、Provider 结果未知、来源失败、授权漂移、重复无进展、审核未知或不收敛均失败关闭。
- SUPPORTED 段必须引用当前 Packet；UNKNOWN 段不得带虚假引用。
- `REWRITE_REQUIRED` 必须列出当前 Packet 中的具体 Evidence ID；重写时 Packet Digest 不变，也不新增 Source Operation。
- `MORE_EVIDENCE_REQUIRED` 必须指出物质性证据缺口；补充调查形成新 Packet 并重新生成、重新审核。
- 调用次数和 Token 只是高位安全熔断，不能减少检查清单、证据约束、审核维度或独立审核。达到熔断只能失败，不能输出降级答案。
- 相同幂等请求复用稳定的模型执行引用和来源操作记录；外部结果未知时不盲目重发。

## Acceptance scenarios

1. 中文和英文问题都得到同语言的自然答案，不暴露内部检查模板、证明记录或审核指令。
2. 任意语言和目录结构的工程都只通过通用 LIST、SEARCH、READ、COMPARE 或语言中立目标调查，不依赖约定入口文件。
3. 每个实质答案段均可追溯到 exact Evidence Packet 内容和源码位置；无依据内容明确 UNKNOWN。
4. 审核发现现有证据中的遗漏时，只重写答案且 Source Operation 数不增加；真正缺证据时只进行针对性补充调查。
5. 复杂调用链答案按问题要求综合解析、分派、策略选择、嵌入处理、异常包装等实际证据，既不遗漏也不机械重复。
6. 相关测试、完整回归、新路径能力评估、冻结陌生工程产品任务和本机浏览器体验全部达到 Verification Matrix 的期望。

## Findings

实现发现登记在 [Iteration 002 Findings](../findings/README.md)，并按[实现发现回写规则](../../../governance/implementation-feedback-policy.md)处置。
