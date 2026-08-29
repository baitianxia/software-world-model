---
id: FINDING-010-171
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai-infrastructure, quality]
depends_on: [FINDING-010-167, FINDING-010-170, ITER-010-PDR-012]
code: [src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: diagnose-effective-tool-domain-violations-exactly
target: src/software_world_model/ai_infrastructure/conversational_engineering_model.py
---

# FINDING-010-171：repair 无法从笼统 Context drift 定位已撤销的 Source operation

## Observation

fresh `run-061-mvp-experience` 绑定 exact product
`50ce444f149600ac71d47b28aa26cd3df99af8be / 4861519e1bd13a06ecf5613ca0e467c67368c080` 与 mall exact Source。冻结 Turn 1
执行 5 次 Ark dispatch 后以 `AGENT_MODEL_CALL_REJECTED / STRUCTURED_OUTPUT_INVALID` 失败关闭，Conversation 保持 `ACTIVE`。5 个 Gateway
call root 都为 `COMPLETED`，input token 仅为 `4,268 / 12,683 / 14,839 / 17,821 / 18,692`，而且每个输出的 first-non-whitespace character
都是 `{`；因此该 trace 没有复现 `FINDING-010-170` 的超长重复 Cognition 或 JSON 外 narration。

前两次 Source Search 都以 `SOURCE_FILE_FUSE_EXHAUSTED` 形成 terminal Boundary，随后一次已授权 Source Read 完整读取
`UmsAdminController.java`。可信 effective catalog 因 terminal Source denial 正确移除所有 Source operation，第 4/5 次 Primary input 都只列
`WORLD_MODEL_QUERY`。第 4 次输出仍提议 `SOURCE_READ(source_locator_329c18e6ac717a1d961136e15760573c)`；它复制完整 Observation prefix，
correction/superseded prefixes 也未漂移，但旧 decoder 把“operation 不在 effective catalog”与五类 Context/reference 条件合并成同一句
`Engineering Agent output drifted from the sealed Context or observation prefix`。第 5 次 same-profile repair 因而重复相同 `SOURCE_READ`，再次
失败关闭。

## Evidence and first divergence

- call 4/5 的 sealed `tool_catalog` 都只有 `WORLD_MODEL_QUERY`，`tool_reference_policy` 虽保留历史 locator 展示，但 terminal reason 已按合同使
  Source Read 不再有效；Application 没有执行越权 read，也没有 fallback。
- 两个 raw output 的 `observation_ids` 与 required 5-ID prefix 完全相同，accepted correction 与 superseded arrays 也都与 sealed empty prefix
  一致；因此 generic drift diagnostic 隐藏了唯一实际失败条件。
- terminal receipt 保存 Conversation/Turn `1/1`、Ark dispatch `5`、request retry `0`、DeepSeek dispatch `0`、human approval request `0` 和
  Production `NOT_EXECUTED`。run-061 不能被新诊断追认为 Answer 或开发体验候选。

## Classification and disposition

这是 `local-implementation`：effective operation domain、terminal Source fuse、一次 same-profile repair、route 和 fail-closed 语义都已经由
Engineering Conversation 合同拥有，本次只让既有 validator error 可操作且不泄露 untrusted value：

- decoder 在既有 grouped Context/reference 检查前单独检查 effective operation；
- action operation 不在当前 domain 时返回
  `$.action.operation must copy one operation from the current tool_catalog (allowed=[...])`，allowed 集合只从 trusted effective catalog 生成，
  不回显 locator 或其他 untrusted output；
- repair category 新增 `CLOSED_OUTPUT_CONTRACT`，与 JSON prefix、syntax 和 mechanical closed-field shape 区分；Primary Prompt 要求丢弃被当前
  catalog 排除的 prior action，final preflight 继续重复 exact trusted diagnostic 与 effective action templates。

确定性测试密封 terminal `SOURCE_FILE_FUSE_EXHAUSTED` receipt，让初始输出选择不可用 `SOURCE_READ`，验证 repair 只看到
`WORLD_MODEL_QUERY` allowed domain 并改为合法 action；既有 missing-operation、analysis-prefix 与 quote syntax repair 同时保持通过。本次不改变
Provider adapter、Source fuse、Cognition、预算或协议版本。Model 直接责任 `21/21` PASS，相关 Agent、Tool、routing、Browser、launcher、
runtime、artifact 与 CLI 组合 `99/99` PASS，文档 `577` 项检查 PASS；全部为本地验证、外部 dispatch 0。fresh successor 必须使用新
product/run identity，冻结问题 4/5 继续保持 unseen。
