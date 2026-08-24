---
id: FINDING-010-058
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [ai-infrastructure, application, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-047, FINDING-010-057]
code: [src/software_world_model/ai_infrastructure/engineering_question_model_source.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/application_services/engineering_question_answering.py]
tests: [tests/test_engineering_question_model_source.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_answering.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: split-finish-dispositions-into-structurally-exclusive-supported-and-non-supported-arrays
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-058：条件化 FINISH item schema 未阻止真实模型再次混合 supported 与 limitation

## Observation and evidence

run-020 的第二题失败后，同一 listener 无重启地接受第三题，证明请求级失败隔离成立。第三题用 1 次 Question Understanding + 10 次 Initial
Investigation 完整读取 `JwtAuthenticationTokenFilter`、`JwtTokenUtil`、`DynamicAuthorizationManager` 与
`DynamicSecurityMetadataSource`，raw FINISH 已正确区分令牌提取/校验、SecurityContext 建立、动态权限判定以及 401/403；但第五个
`SUPPORTED` disposition 又附加一条 `LIMITATION` observation，声称已搜索的 `PmsDaoTests` 没有认证/授权断言，并把该 search-only boundary
item 留在 parent supported references 中。Adapter/Application 因而以 `STRUCTURED_OUTPUT_INVALID` 关闭当前题，没有进入 Answer 或 Review，
没有把错误内容交付为答案。

本地 closed schema 原已用 nested `anyOf` 表达 supported/affirmative 与 non-supported/limitation 两个 item variant，且确定性 schema 测试会拒绝
混类；但 DeepSeek Chat 运行只获得 `json_object` 输出约束和随 Prompt 发送的 schema instruction，Provider 仍可生成不满足 nested 条件分支的
JSON，必须由本地 validator 拒绝。单一 `finish_dispositions` 数组要求模型同时正确选择 parent outcome 和 child kind，真实运行再次证明这种条件
组合虽安全失败关闭，却对可交付性不够稳健。Question Understanding 还把“给出可核对依据”扩张为问题未要求的 TEST need，增加了这条无关
coverage observation 的诱因。

会话随后提交了 22,000 个 ASCII 字符；其约 22 KB，低于 65,536-byte 服务端上限，因此合法发生 1 次 Question Understanding dispatch，不能
冒充 oversize 前置拒绝。为避免非业务题继续调用，listener 被人工停止。terminal receipt file
`sha256:1408e82757b454bc8246f9cc5ea0be2f180243a16a300715ecfdfeae25e477f2` / document
`sha256:96ba92fc83bb50f89ea2d4dd24e49d59c7424dc4cbf19e61030ac44041acf898` 真实记录 `STOPPED_AFTER_DISPATCH`、4 个 accepted
question、27 次 dispatch（10/5/11/1）、request retry 0、Provider switch 0、verified TLS 与 Production Activation `NOT_EXECUTED`。

## Root cause

Domain 的 outcome/observation/reference partition invariant 正确，不能为提高通过率而放松。缺口在 Provider-facing shape：一个数组 item 的
parent outcome 与 nested observation kind 依赖条件分支，而 DeepSeek 端没有原生执行该 JSON Schema 的资格；Prompt 约束也不能保证每次严格
服从。除此之外，Question Understanding 没有足够明确地区分“用户要求可核对源码依据”与“用户要求测试/日志/配置本身”，可把 merely available
modality 误提升为 material need。

## Decision and disposition

- Initial/Verification closed output 删除单一 `finish_dispositions`，改为两个必填、结构上互斥的数组：
  `supported_finish_dispositions` 的 item schema 只能产生 `SUPPORTED` + affirmative observations；
  `non_supported_finish_dispositions` 只能产生 `UNKNOWN/CONFLICT/FAILED` + `LIMITATION` observations。SEARCH/READ/PARSE 必须让两数组都空；
  FINISH 必须把每个 checklist item 恰好放入其中一个数组。可信 adapter 只合并两个已验证数组为既有 Domain disposition，不改写 outcome、
  observation、statement 或 evidence links；
- Question Understanding Prompt 明确：不能因 modality 可用或用户只要求“可核对依据”就引入 TEST/log/config；只有该 modality 本身属于显式问题
  的 material conclusion 时才选择，源码位置已经可以作为 source-behavior claim 的核对依据；
- Initial/Verification schema 升为 `@6`，Strategy/Prompt 升为 `@14/@23`。Domain 双分区、support/boundary eligibility、混类拒绝与零 transport retry
  均保持。三模块定向测试与完整 Engineering QA 100/100 PASS；run-020 第三题仍是 structured-output FAIL，不得追认答案质量 PASS。
