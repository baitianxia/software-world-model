---
id: FINDING-010-081
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, quality, product]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-079, FINDING-010-080]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py, tests/test_engineering_qa_live.py]
iteration: ITER-010
classification: verification
scope: systemic
disposition: run-030-two-pass-one-material-actionability-fail-preserved
target: ITER-010-VERIFICATION
---

# FINDING-010-081：run-030 的 Q2 被错误批准但没有闭合受保护请求的可执行接入步骤

## Observation and evidence

`FINDING-010-079/080` 的处置形成 clean product commit
`9ae982b1d9615b82f64a71143302cc45f0be8af5` / tree
`63602c4bedffce69a11f84d5640cc4855124dc26`。隔离 product clone 与 exact mall
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` 都是 detached、clean exact revision；product archive digest 为
`sha256:d862ca835bdcb3602d55837c9a24347c2c613deb49b773d4464f29801ea9c1dd`。

run-030 先执行 fresh DeepSeek Conformance 2/2 PASS，Result digest 为
`sha256:7edcc4aca2dc80bcd21c099fe0e4a2f126cc634d32b4d8d5d732f80ef5048e8a`；两个 Provider request ID 为
`48e6a91e-ae5e-4dc2-88c9-0396c89d2e48`、`4def1981-7ddf-4c46-b1b5-2b60d9a55bf1`，retry 0，
Production eligible 为 false。持续 Alpha Session Authority digest 为
`sha256:7a6e87b00ba18fa07e96c9ace55df4f8f2ddc8c6028fb8794f5d4dd481d1ea27`；同一 Browser/Listener 的三题分别使用
14/14/8 次 dispatch，共 36 次，retry/switch/outcome-unknown 均为 0。三题页面 Result 为：

- Q1 `engineering_result_d845145811d10e16c038410d17245305`。raw Answer 最终覆盖密码和启用状态校验、SecurityContext、JWT、失败
  分支以及 `insertLoginLog` 创建并通过 `loginLogMapper.insert` 持久化管理员登录审计；最终 comprehensive/challenge 都为
  finding-free PASS，独立复核 PASS。
- Q2 `engineering_result_fead9d5a281e60cc97ce787fafcde414` 被页面标为 `APPROVED`。第一轮 challenge 正确拒绝了未挂载
  `UmsAdminLoginParam` 的 `username/password` 字段扩张，rewrite 也保留了既有 Package observation；但最终正文只并列了模块依赖、
  `POST /admin/login`、JWT filter 和 dynamic authorization 组件。它没有把登录响应的 `token/tokenHead` 明确交接为后续受保护请求的
  header 输入，也没有把配置化 header 名与 prefix 纳入 resources 排除造成的明确未知项。因此新开发者仍不能按答案完成原问题要求的
  安全接入步骤。raw final challenge 的 8 个 lead 全部错误 `WITHIN_EVIDENCE_BOUNDARY`、Findings 为空，独立复核为重大 material
  actionability omission，Q2 FAIL。
- Q3 `engineering_result_93be4b0f492aaad945aedef2de191adf`。正文明确分开令牌提取/校验、认证上下文建立和动态权限判定，并把
  缺少 handler implementation 导致的最终 401/403 mapping 保留为未知；11 个 final challenge assessment 全部在证据边界内，独立复核
  PASS。

66,000 个 exact ASCII 字符通过 Browser 填入后，在 Provider 前以 local preview limit 拒绝；accepted question 与 Gateway dispatch
仍保持 3/36。Browser console 为 0，listener 随后优雅停止，8765 无监听。SQLite checkpoint 返回 `0|0|0` 且 `quick_check=ok`，最终无
WAL/SHM；Session、DB、launch、terminal 四个文件均为 `0600`。其 SHA-256 分别为
`40d8311b622bfeaafc6f7e9388641f1904b679486113d49acd7151875218a888`、
`67b97bd3fac728e75d060896b72261617d9af9a666e124caa4859299c8fa4016`、
`ea091f0459b96b8fe3db286212dd6e2185eb7466369701b8668b47dbfb04801a`、
`970288d3eae80a53f1894eaa73d02a676da0b99af24b1dbf570ce5a09bdd98c3`；terminal document digest 为
`sha256:ec4e1e9ab5e88c67c1969defb1daf2e063e5a945941f3d3ebe065cf3d9a25ebf`。Production Activation 为
`NOT_EXECUTED`。

## Decision and disposition

- run-030 永久保持 2 PASS + 1 FAIL；页面 `APPROVED`、零重试和持续 listener 都不能替代原问题独立履约复核。
- 根因是 Question Understanding 把“启动并调用/安全接入步骤”压缩成组件清单，而 final challenge 只逐项检查现有 evidence-boundary
  lead，没有独立检查原问题要求的用户动作顺序、输入/输出交接和 known/unknown 边界。
- 本 Finding 写入 `ITER-010-VERIFICATION`；系统契约与通用实现处置由 `FINDING-010-082` 记录。ITER-010 保持 `REWORK`，
  `V-ANSWER-REWORK-001` 继续 blocking；Slice2/3、hidden、Acceptance 和 Production 状态不变。
