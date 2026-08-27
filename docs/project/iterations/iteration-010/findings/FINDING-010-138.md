---
id: FINDING-010-138
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, quality, ai, application]
depends_on: [ITER-010-RESULT-V-CHAT-EXPERIENCE-001-PDR005-DIRECTION-CANARY, ITER-010-PDR-005, SYS-ADR-018]
code: [src/software_world_model/application_services/conversational_engineering_tools.py, src/software_world_model/application_services/engineering_question_cognition.py, src/software_world_model/application_services/java_source_semantics.py, src/software_world_model/ai_infrastructure/conversational_engineering_model.py]
tests: [tests/test_conversational_engineering_tools.py, tests/test_engineering_question_cognition.py, tests/test_java_source_semantics.py, tests/test_conversational_engineering_model.py]
iteration: ITER-010
classification: iteration-design
scope: systemic
disposition: same-slice-cognition-query-projection-and-source-selection-rework
target: ITER-010-SLICE-001
---

# FINDING-010-138：相关 Java 认知存在，但自然语言查询和后续源码选择没有取得它

## Observation

`run-043-pdr005-direction-canary` 的登录语义链没有形成可用答案。exact Java Snapshot 已包含
`UmsAdminServiceImpl.login(String,String)` 及其源码位置，但 live World Model projection 漏掉该方法；随后 Source 调查又把有限预算消耗在
大量同词但无关的 `loginType` 生成代码上，没有读取 controller 已明确调用的 `UmsAdminServiceImpl.java`。

该问题不是源码中没有答案，也不是 Web 丢失了已经批准的正确答案。它首先发生在 Cognition query/projection，Agent 的 Source selection
又形成独立下游故障；Reviewer limit 和 Provider outcome unknown 不能覆盖这个最早偏差。

## Evidence

- 首个主 Agent 输出的 semantic `evidence_need` 已明确要求 admin login controller、security configuration 和 token generation，但密封的
  `WORLD_MODEL_QUERY` action 为 `arguments=[]`；实际 Cognition query 仍使用中文 original Turn，没有把 Agent 已形成的 evidence need
  编译成受控查询参数；
- exact Snapshot 中存在 `UmsAdminServiceImpl.login(String,String) -> String`，source path 为
  `mall-admin/src/main/java/com/macro/mall/service/impl/UmsAdminServiceImpl.java`；live projection 返回 36 项但漏掉该 entity，命中项主要是
  `refreshToken`、`updateLoginTimeByUsername` 和无关关系；
- literal Source search 检查 56 个文件后截断，前 17 项是生成模型中的 `loginType`，最后才出现 `UmsAdminController` 的 `/login`、controller
  method 与 `adminService.login(...)`；Agent 读取了 controller 和两个登录日志类，却没有沿已取得的 caller evidence 读取 service
  implementation；
- 同一 run 的未见 Maven 结构题只用一次 World Model observation 就准确回答 `mall-portal` 的直接依赖，证明 Session binding、窄结构认知和
  Web delivery 可以工作，不能把登录失败归因于整个 World Model 未装载；
- run-043 的完整产品事实、输入、运行身份和失败结果保存在
  `ITER-010-RESULT-V-CHAT-EXPERIENCE-001-PDR005-DIRECTION-CANARY`。其 DeepSeek 调度违规另由 `FINDING-010-139 / PDR-007` 处置，
  两种失败不能互相替代。

## Decision and disposition

该发现处置到当前 Slice1 的通用 REWORK：

- Cognition owner 必须把主 Agent 的 typed evidence need 确定性编译为受控 World Model query，并证明相关 exact entity、Coverage 和 Gap 能由
  自然语言问题取得；不得加入工程名、题目文本、固定关键词、类名或方法名特判；
- World Model projection 必须按声明的 Profile/query capability 返回问题相关认知，并保留未命中、Coverage 与 Unknown；不能用返回整个
  Snapshot 或 lexical top-N 冒充问题相关认知；
- Agent/Source owner 必须能沿已密封 caller/callee、symbol、path 和 observation 关系选择下一只读操作，不能让宽泛同词结果耗尽全部
  scan/read 预算；
- 修复前先用 run-043 已有产物离线形成最小复现，再验证至少两个未参与修复的异质问题；只有通用本地证据通过，才冻结后继 candidate 并
  申请一个新的 exact live canary grant；
- 本发现不授权 Provider、Source disclosure、Browser 或 Production，也不能把 run-043 追认为方向、Chat、Quality 或 Acceptance PASS。

## Implementation evidence

通用修复已在 clean successor `3a6089fa0ff1d5df88f43199ae77ae4c4ecc6f19` / tree
`b1fd51bb533c8ff393dc42b6864a08e5c94929c0` 上完成：

- Strategy/Prompt/Primary Input 升为 `@8/@8/@8`；`WORLD_MODEL_QUERY` 不再接受 model-authored query argument，主 Agent 只提交具体
  `evidence_need`，Application 再把它与 exact current User Turn 确定性编译为 bounded semantic query；
- 同一 Turn 已使用的 World Model `evidence_need` 进入 closed forbidden domain；重复 need、显式 `query` argument 或 action identity 漂移均
  在工具执行前失败关闭；
- 旧 explicit-query Tool API 只保留受信兼容调用方；current `@8` model contract 不能取得该 argument domain；
- 真实 run-043 双 Profile bundle 的零外部调用诊断中，通用“凭据验证/认证/token/失败/状态”语义需要取得
  `UmsAdminServiceImpl.login`；两个未参与修复的异质问题分别取得 `mall-portal` 的 `mall-security/mall-mbg` 直接依赖，以及
  `PmsProductServiceImpl.handleUpdateSkuStockList/handleSkuStockCode`。三个 Context digest 分别为
  `sha256:1d5c198ee3edaf7fc60357954f1c675fc3a26009b168450eb52055e5e62f3b90`、
  `sha256:f2e25b8ea75e4aa9f142ff4ac879af9e1d4e9851d6954c0396faa8dd7bbb8638`、
  `sha256:7a917480902ecbf51626d63d2867aa78a287eee19eea3eb19ee5ef1953842fc6`；query-time Source read 与外部调用均为 0。

上述证据关闭本地 query projection 修复条件，但不证明真实 Agent 会稳定产生足够具体的 need、沿 caller/callee 选择正确 Source 或形成获批
答案；这些仍由一次新的合规 direction canary 裁决。
