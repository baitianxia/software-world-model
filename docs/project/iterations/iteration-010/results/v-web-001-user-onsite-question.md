---
id: ITER-010-RESULT-V-WEB-001-USER-ONSITE-QUESTION
kind: iteration-result
status: passed-browser-checkpoint-awaiting-user-direction-decision
authority: execution-evidence
owners: [product, engineering, quality, security]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, ITER-010-RESULT-V-WEB-001-PUBLIC-DIRECTION-QUESTIONS, FINDING-010-027]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py, src/software_world_model/interface/engineering_qa_browser.py, src/software_world_model/interface/engineering_qa_browser_ui.py, src/software_world_model/interface/engineering_qa_preview_cli.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py, tests/test_engineering_qa_live.py, tests/test_engineering_qa_preview_cli.py, tests/test_engineering_qa_browser.py, tests]
iteration: ITER-010
case_id: V-WEB-001
case_verdict: PASS
acceptance: NOT_ACCEPTANCE
production_activation: NOT_EXECUTED
---

# ITER-010 V-WEB-001 用户现场题执行证据

## Decision

用户在公开 4 题结果写回并形成 clean candidate 后，现场提出“登录流程是怎样的？”。同一 product-owned loopback
`ENGINEERING_QA` Web 使用 exact prepared question 和新的一次性 run grant 完成 10 次 DeepSeek role dispatch，形成 sealed
Ledger/Question Evidence Package、Answer 与独立 Review `APPROVED`。页面显示 `REVIEWED RESULT`，3 个 Citation 全部由 in-app Browser
实际打开，developer console 为 `[]`。

结合 `ITER-010-RESULT-V-WEB-001-PUBLIC-DIRECTION-QUESTIONS`，`V-WEB-001` 所需 4 条不同覆盖维度公开题与至少一条用户现场题都已真实
执行，Browser checkpoint 为 `PASS`。这仍不是 `V-PREVIEW-001`、Slice Result 或 Acceptance：现场正文仍显著按方法调用顺序展开并省略登录
日志副作用，已由 `FINDING-010-027` 原样保留，必须由用户给出 `CONTINUE / REDIRECT / REJECT`，实现者不能代为判断。

## Exact freeze and authorization

- onsite freeze：`var/iteration-010/slice-001/run-004-direction-preview/onsite-question-freeze.json` /
  `sha256:69813d778adf9fa81c2915fadd1b00a600035119fea61e54f9f31879afee6acb`，在任何本题 Provider dispatch 前写入并设为 `0600`；
- exact product candidate commit/tree：`8632904d4e97e152d6379d7ccc203f5a0234c34c` /
  `48b2ab7089a33e1fb4187909d102ad7241754a4f`，运行前 clean；
- exact user question message digest：
  `sha256:684849e3116168fb6dd67fbc9f9f70df0e5d1b8385b5f72f711cd75d62f1e9c9`；它把此前 root live authorization
  `sha256:815d868ca3df4795276934acbc21d12584fcfd4cb49b31c67696c72d3a5a6b74` 收窄到本题；
- prepared request/run：`iter-010-v-web-001-onsite-001` / `iter-010-v-web-001-onsite-run-001`；Request digest
  `sha256:f749d2544fbde6099b133a46de46c6bfdb928af264a7dda3f5fe6a9d3ce854b1`；evaluation subject
  `sha256:0c8ee7a2468349cb5451a3f335aee91fae842763d70918725450bbbb8711a392`；run authorization
  `sha256:632ea2e141bdeea9c6598fe44954657acd13ac0c71f709f86f30c7547da28124`；
- repository `mall` revision `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`，Binding
  `binding_4ef0d3446b3e44c79ed3c0ffc855d5c9`，Source Profile `ITER-010-MALL-JWT-SOURCE:2` /
  `sha256:4746c3e41de9d93c10b3b3eaa752b6e0959290e2e7772499a359031a7d497301`；
- Maven Snapshot `structure_snapshot_5033a7fc944141d08ecd5ad3879ce1ba`，read authority
  `sha256:9cd68a23017fcd3ca6d91d5f63cd49021038e29f0a327c710c9a4bd2cda01c16`；
- Provider `DEEPSEEK / deepseek-v4-pro / https://api.deepseek.com/chat/completions`；qualification
  `CC-DEEPSEEK-CHAT-NO-TOOLS-001:sha256:01c6fbef5fbe11678b0bac3f9e16d6b5b9f0fb9e341a60383931a9509e534218`，有效期内；
- 用户取消累计调用上限，但产品每题 24-call fuse、retry 0、Provider switch 0、`src/main/resources`/配置凭据排除与 Production
  Activation `NOT_EXECUTED` 不变。

## Delivered answer and independent Review

主视图交付的答案把登录主链表达为：客户端 POST `/admin/login` 并提交用户名/密码；Controller 调用
`adminService.login`；Service 加载用户、验证密码与 enabled 状态，把认证写入 `SecurityContextHolder` 并生成 JWT；Controller 返回
`token`/`tokenHead` 或 token-null validation failure；后续请求由 `JwtAuthenticationTokenFilter` 提取、校验 JWT 并建立认证上下文。
正文同时声明 Evidence Package 没有完整时序图和所有异常分支，因此不确认全部错误处理路径。

Answer 包含 6 个 affirmative claim 和 1 个 limitation claim；输出 digest
`sha256:a349bf1edaa377eacf7319b97a98657949759d1e22ff6d9fb368327ae1660c75`。独立 Review
`engineering_review_8599387390a720f279c67844adf31033` 返回 `APPROVED`、findings 为空，Review output digest
`sha256:1877579df5b0a3f049e910b84b09c6acda1a05d7b4d2d501667f4d4fa6241636`。

Result 为 `engineering_result_e5f3c335944de0f2f57e8f9fdd48b419` /
`sha256:2aba0555d732282f5a925360c60f3a7e7ce383e55a49634bb4fd4a04dd992360`，terminal reason `APPROVED`，elapsed
56,059 ms。

## Browser, Citation and quality inspection

3 个 Citation 都由 Browser 实际打开：

- `UmsAdminController.java`：exact `POST /admin/login`、请求体、Service 调用、token-null 分支和 `token`/`tokenHead` response；
- `UmsAdminServiceImpl.java`：`loadUserByUsername`、password/enabled checks、`SecurityContextHolder`、JWT generation；
- `JwtAuthenticationTokenFilter.java`：后续请求的 header/prefix extraction、username/token validation 与 Security Context population。

三者都绑定 exact revision `0504e86…`、Package ID `question_package_368b16f0ffb9e36f1ef91679fa5b2ad5`、Package digest
`sha256:a69bc1d3c8731144b87ac28b5806999193a23143ef2b669df7bcb96af62e1037`、seal
`sha256:934a86397ec2f935df5cbd8c54e348dec8de0c91421c93ec037190fb641609ed` 和同一 Result；origin class 全为
`EXACT_REVISION_SOURCE`，`projection_is_answer_input=false`。主页面只展示原问题、答案、Limitation 和 Citation，开发者诊断默认折叠，
console 为 `[]`。

人工检查没有发现 affirmative claim 与引用冲突，但 exact Service Source 在 token 生成后还执行 `insertLoginLog(username)`，正文未提该副作用；
整体层级也仍以类/方法/调用顺序为主。该信号按 `FINDING-010-027` 交给用户方向判断，不由 Reviewer `APPROVED` 自动消除。

## Package, usage, transport and preservation

- 1 Question Understanding + 7 Initial Investigation + 1 Answer + 1 Review = 10 role dispatch；6 个 Broker Decision 全为
  `AUTHORIZED / POLICY_COMPILED`，0 verification investigation、0 no-progress；
- Ledger seal `sha256:cd368301c7b3b949d7be2ccde7016eb4d4898848addfec1766381ca884b8e685`；Package 为 38
  support/citation + 15 boundary/audit；
- 6 source operations、17 source-file observations、73,333 source bytes、40,621 World Model bytes；document/build/test bytes 均为 0；
- 283,781 input tokens、2,439 output tokens，10/10 usage complete；requested/actual model 都只有 `deepseek-v4-pro`；
- verified TLS handshake 1/1、connection reuse 9、HTTP/credential resolution 10/10、post-dispatch outcome unknown 0、request retry 0、
  Provider switch 0；
- Gateway 共 30 个 manifest item，对 `src/main/resources` 的 exact 匹配数为 0；Answer/Initial Investigation/Verification
  Investigation/Review direct Source authority 均为 false；
- launch/terminal document digest：`sha256:9cb6aaf9acf3691cede755c4c4f3fd81d9bf3783a35145443edd68578338b13f` /
  `sha256:80baeb902ecd5c5f38e19f576ef16233e59aa72a89ef1965b82ebf61a0a51270`；raw launch/terminal/Gateway SHA-256：
  `e23fc0d8047700cb859467a1116abcf4baaef272d03dc4c880a54f96b349396a` /
  `51da22c4fce8ae745ada94f7715065bdb037e6f5749a1c9f2260d55cd97cf547` /
  `72daf78a43aba86b00587983a899f0145c12e66298a2d63cca08f85ecd8af753`；
- 原始证据永久保存在
  `var/iteration-010/slice-001/run-004-direction-preview/web-v-web-001-onsite-001/`；listener 已优雅停止，terminal receipt 已密封；
  Production Activation `NOT_EXECUTED`。

## Verdict and remaining gate

`V-WEB-001: PASS`：公开 4 题与用户现场题均从同一真实 Web 执行，答案/失败关闭、可打开 Citation、折叠诊断、console、安全与非生产边界
有真实证据。

仍 blocking：`V-PREVIEW-001` 等待用户看过本现场答案后给出 `CONTINUE / REDIRECT / REJECT`；`V-REFLECT-001` 必须消费该新决定和
`FINDING-010-027`；`V-XD-001` 仍因 Maven Cognition 不含 accepted declaration/`CALLS` 独立 blocking。没有 Slice Result、Acceptance、
hidden、跨工程、三臂 comparison、持久恢复或 Production evidence。
