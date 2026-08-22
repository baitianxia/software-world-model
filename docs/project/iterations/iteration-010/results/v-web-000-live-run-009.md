---
id: ITER-010-RESULT-V-WEB-000-LIVE-RUN-009
kind: iteration-result
status: passed-micro-checkpoint
authority: execution-evidence
owners: [product, engineering, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-024, FINDING-010-025]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py, src/software_world_model/interface/engineering_qa_browser.py, src/software_world_model/interface/engineering_qa_browser_ui.py, src/software_world_model/interface/engineering_qa_preview_cli.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py, tests/test_engineering_qa_browser.py, tests/test_engineering_qa_live.py, tests/test_engineering_qa_preview_cli.py]
iteration: ITER-010
case_id: V-WEB-000
case_verdict: PASS
acceptance: NOT_ACCEPTANCE
production_activation: NOT_EXECUTED
---

# ITER-010 V-WEB-000 Live Run 009 Result

## Claim and scope

`V-WEB-000` 的最早真实 Web 微纵切已通过。一个普通用户从 product-owned loopback `ENGINEERING_QA` 页面提交代表问题，系统以 exact Maven
World Model Cognition 开始，按模型逐步决策执行一次 literal SOURCE search 和四次不同 exact-revision full-content READ，密封同一
Ledger/Question Evidence Package，生成结论优先答案，并由隔离的独立 Reviewer `APPROVED`。主视图展示 6 个可打开 Citation 和一条诚实的
测试证据 limitation。

这是 `DIRECTION_PREVIEW / NOT_ACCEPTANCE / NOT_PRODUCTION` 微检查点 Result。它不给 `V-XD-001`、`V-WEB-001`、Slice1 方向体验、隐藏
验证、比较、Reflection、Slice Acceptance 或 Production Activation 下 PASS，也不替代后续用户方向裁决。

## Exact freeze and authorization

- product candidate commit/tree：`f38f6cced15962a3fb659214ce43c7c679a92faf` /
  `1a03bda4e20d97a276e2560da90a5ac7a092a76b`，运行前 clean；
- candidate verification：Engineering QA focused 63/63、docs 401/401、`py_compile`、`git diff --check` PASS；允许 AF_UNIX 的 full
  discovery 1115 项中 1110 PASS，唯一 4 FAIL + 1 ERROR identity/marker/Codex digest 精确保持 `FINDING-008-020` 历史 hold；raw full
  suite 仍为 FAIL，只以 `PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD` gate 继续本次非生产验证；
- exact mall repository revision：`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`；Binding
  `binding_4ef0d3446b3e44c79ed3c0ffc855d5c9`；Source Profile `ITER-010-MALL-JWT-SOURCE:2` /
  `sha256:4746c3e41de9d93c10b3b3eaa752b6e0959290e2e7772499a359031a7d497301`；
- World Model Snapshot `structure_snapshot_5033a7fc944141d08ecd5ad3879ce1ba`；read authority
  `sha256:9cd68a23017fcd3ca6d91d5f63cd49021038e29f0a327c710c9a4bd2cda01c16`；
- current DeepSeek qualification：
  `CC-DEEPSEEK-CHAT-NO-TOOLS-001:sha256:01c6fbef5fbe11678b0bac3f9e16d6b5b9f0fb9e341a60383931a9509e534218`；
- prepared request/run：`iter-010-v-web-000-mall-jwt-012` / `iter-010-v-web-000-mall-jwt-run-012`；request digest
  `sha256:709a48e6e3577198650b409779c062a829676c31ef9f45d90ca834aef6ec97fc`；
- user authorization message digest：
  `sha256:815d868ca3df4795276934acbc21d12584fcfd4cb49b31c67696c72d3a5a6b74`；用户取消本次累计调用上限，但每题冻结的
  24-call 安全熔断、零重试、零 Provider 切换、`src/main/resources` 排除和 Production Activation `NOT_EXECUTED` 保持不变；
- run authorization/evaluation subject：
  `sha256:2442b3862b400387620e0025fa0c9999a50928747557227d3f47eba16067eb3d` /
  `sha256:d9ae475aca25a8380d719384d1bf714ee465d25b5afc2103a1de4cd1c17bcaf9`。

## Product execution

| Stage | Exact outcome |
|---|---|
| Question Understanding | 1 次；保留原问题并形成 6 个 material conclusions/checklist items |
| Initial Investigation | 6 次 role call：literal `JwtTokenUtil` search、4 个不同 full-content READ、1 个 FINISH；5 个 Broker Decision 全为 `AUTHORIZED / POLICY_COMPILED`；no-progress 0 |
| Evidence Package | Ledger seal `sha256:7c1211abaa761dbd94a96b6fd94b4a185857f91943c672d313cea6c6a62c2f81`；Package digest `sha256:4f159c9156d57e9a09aa657e53c2ec0ffa50486973fef3612a83bcd625c2e77e`；37 support/citation + 14 boundary/audit |
| Answer | 1 次；5 个 affirmative claim + 1 个 limitation claim；测试未读取，因此明确“不知道当前测试覆盖”，没有把 allowlist 存在冒充已取得证据 |
| Independent Review | 1 次；`engineering_review_d151cc0fb8311fd8673fec8a4af63e90 / APPROVED`，findings 为空，无补证请求 |
| Result | `engineering_result_2025ba4a523a363c6a8f463e670dfc31 / APPROVED`；Result digest `sha256:98dadad019064aadc37fc432842cb3f7644d5b19045b6c2d76245ded9688bf49`；elapsed 58,851 ms |

总计 9 个 Provider dispatch：1 Understanding + 6 Investigation + 1 Answer + 1 Review。usage 为 5 source operations、16 source-file
observations、67,896 source bytes、40,621 World Model bytes、0 test/build/document bytes、0 verification investigation。Answer、Initial
Investigation、Verification Investigation 和 Review 的 direct Source authority 均为 false；只有 Broker/Worker 执行只读来源操作。

## Browser and Citation evidence

in-app Browser 主视图显示 `REVIEWED RESULT`、原问题、结论优先正文、测试证据 limitation 和 6 个 Citation button；Developer Details
显示 `terminal_reason=APPROVED`、`answer_reached=true`、`review_reached=true`、9-call usage 和独立 Review。console log 为空。

6 个 Citation 均由 Browser 实际打开并成功解析：

- exact Source：`UmsAdminServiceImpl.java`、`JwtTokenUtil.java`、`JwtAuthenticationTokenFilter.java`、`CommonSecurityConfig.java`；
- World Model Cognition：`mall-admin` 与 `mall-security` 两个 exact Maven module entity；
- 每个 Citation 都绑定 repository revision `0504e86…`、同一 Package digest 和同一 Result ID；Source/Cognition origin class 分别为
  `EXACT_REVISION_SOURCE` / `WORLD_MODEL_COGNITION`；`projection_is_answer_input=false`。

主答案没有暴露 Ledger/Broker/Gateway 诊断，开发者详情默认折叠。Citation projection 在密封 Result 后读取，不进入 Answer/Review 输入。

## Safety and preservation

- terminal receipt：9 completed dispatch、retry 0、Provider switch 0、Production Activation `NOT_EXECUTED`；verified TLS handshake 1 次，
  keep-alive reuse 8 次，post-dispatch outcome unknown 0；
- Gateway 9 次均在 verified TLS 后逐次解析 credential，secret 只记录为 `env:DEEPSEEK_API_KEY` reference；
- exact Request allowlist 只有指定的 Java/README/POM/test path，不含 resources；全部 9 个 model manifest item 对
  `src/main/resources` 的匹配数为 0；
- launch receipt / terminal receipt / Gateway database raw SHA-256：
  `32e8b63f53e724124015646087d6edd722ca532718dd7f1116aa3ef9ac8e80c8` /
  `a36219074747457f2cccd319adeb56633f3b1dc420b810b38ccf21a427490e9d` /
  `a6cb68fbfd126093ccd5df3adefa058e2094777ffcaab927f58afb5ff25f49ab`；永久目录为
  `var/iteration-010/slice-001/run-003-preview/web-v-web-000-012/`。

此前 8 个失败关闭 run 继续永久保留，不能由本 PASS 改写。九个 Web run 共 47 次 role dispatch，另有 2 次 current qualification call；
全部 retry/provider switch 为 0，Production Activation 均 `NOT_EXECUTED`。

## Verdict and remaining gates

`V-WEB-000: PASS`。exact revision、read-only/untrusted Source、World Model + query-time Source、Ledger/Package 分区、用户可打开 Citation、
独立 Review、普通用户 loopback 页面和安全收据均有真实执行证据。

仍 blocking：`V-XD-001` 需要真实 declaration/`CALLS` + 新来源 Evidence 的同答案组合；`V-WEB-001` 还需同一产品入口运行 4 条不同覆盖
维度问题和至少一条现场题；`V-PREVIEW-001`、`V-REFLECT-001` 及后续 Slice 均未形成 Result。ITER-010 仍未接受。
