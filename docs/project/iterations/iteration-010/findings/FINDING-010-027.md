---
id: FINDING-010-027
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [product, quality, engineering]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, ITER-010-RESULT-V-WEB-001-PUBLIC-DIRECTION-QUESTIONS]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_strategy.py, tests/test_engineering_qa_browser.py]
iteration: ITER-010
classification: verification
scope: individual-direction-sensitive
disposition: preserve-onsite-quality-signal-for-user-direction-decision
target: ITER-010-VERIFICATION
---

# FINDING-010-027：现场登录题获批，但正文仍以方法调用序列为主

## Observation

用户在 product freeze 后现场提出“登录流程是怎样的？”。exact `ENGINEERING_QA` loopback Web 返回独立 Review `APPROVED` 的答案，6 个
affirmative claim 都有同一 sealed Package 中的 exact Source support，3 个 Citation 也由 in-app Browser 实际打开。没有发现重大事实错误，
页面和安全链按设计完成。

同时，正文主要依次展开 `/admin/login`、`UmsAdminController.login`、`UmsAdminServiceImpl.login`、
`UsernamePasswordAuthenticationToken`、`SecurityContextHolder`、`JwtTokenUtil.generateToken` 与
`JwtAuthenticationTokenFilter`。这条真实现场答案仍明显接近类/方法/调用顺序走读，而不是先用较高层级概括用户登录、签发 token、后续请求
认证三个阶段。exact `UmsAdminServiceImpl.login` Citation 还显示 token 生成后调用 `insertLoginLog(username)`，正文没有提及这个登录
副作用；其 Limitation 只声明没有完整时序图和全部异常分支，没有点明该副作用省略。

## Evidence and classification

- onsite freeze：`var/iteration-010/slice-001/run-004-direction-preview/onsite-question-freeze.json` /
  `sha256:69813d778adf9fa81c2915fadd1b00a600035119fea61e54f9f31879afee6acb`；candidate
  `8632904d4e97e152d6379d7ccc203f5a0234c34c` / tree `48b2ab7089a33e1fb4187909d102ad7241754a4f`；
- Result `engineering_result_e5f3c335944de0f2f57e8f9fdd48b419` /
  `sha256:2aba0555d732282f5a925360c60f3a7e7ce383e55a49634bb4fd4a04dd992360`；Review
  `engineering_review_8599387390a720f279c67844adf31033 / APPROVED`，findings 为空；
- 3 个 Citation 分别是 `UmsAdminController.java`、`UmsAdminServiceImpl.java` 和 `JwtAuthenticationTokenFilter.java`，全部绑定 exact
  revision `0504e86…`、Package `sha256:a69bc1d3…` / seal `sha256:934a8639…`，`projection_is_answer_input=false`；
- 10 次 role dispatch、6 次 Broker-authorized read-only operation、0 no-progress、retry/switch/outcome-unknown 0；console 为 `[]`，
  Production Activation `NOT_EXECUTED`。

该观察不是 Source、Citation、隔离或实现正确性缺陷，也不足以把获批答案改写成重大错误；它是
  `verification / individual-direction-sensitive` 的真实产品质量信号。它直接对应 ITER-010 stop condition“默认答案仍为方法、分支、调用顺序或
内部诊断走读”。实现者不应在已经识别该客观条件后要求用户重复确认问题是否存在；用户后续消息已按 `REDIRECT` 消费该信号。

## Decision and disposition

- 不重试、不改写现场题，也不以独立 Review `APPROVED` 掩盖层级与完整性信号；
- `V-WEB-001` 只按真实 Web、Citation、console、授权与安全交付事实取得技术 PASS；
- 本观察已处置到 `ITER-010-VERIFICATION` 的 `V-PREVIEW-001` evidence；用户决定收据
  `codex-user-message:sha256:d746968f58cea4d2b7689b5902c0ff97f42f63c93ffc4cbc40551cfa2c0359e0` 构成 `REDIRECT`；
- 根因由 `FINDING-010-028` 处置到 Roadmap Candidate。本运行作为方向失败证据永久保留，不进入 Slice2，不执行 Production Activation。
