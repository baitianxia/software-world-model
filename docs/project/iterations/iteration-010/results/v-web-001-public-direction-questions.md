---
id: ITER-010-RESULT-V-WEB-001-PUBLIC-DIRECTION-QUESTIONS
kind: iteration-result
status: executed-public-subset-complete
authority: execution-evidence
owners: [engineering, quality, security, product]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, ITER-010-RESULT-V-WEB-000-LIVE-RUN-009, FINDING-010-026]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py, src/software_world_model/interface/engineering_qa_browser.py, src/software_world_model/interface/engineering_qa_browser_ui.py, src/software_world_model/interface/engineering_qa_preview_cli.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_cognition.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py, tests/test_engineering_qa_source.py, tests/test_engineering_qa_live.py, tests/test_engineering_qa_preview_cli.py, tests/test_engineering_qa_browser.py, tests]
iteration: ITER-010
---

# ITER-010 V-WEB-001 公开方向题执行证据

## Decision

同一 product-owned `ENGINEERING_QA` loopback Web 已执行 4 条预冻结、不同覆盖维度的公开方向题：3 条形成独立 Review
`APPROVED / REVIEWED RESULT`，1 条因真实 no-progress 安全熔断失败关闭并按 FAIL 计数。公开题子集达到 `V-ANSWER-001` 的方向阈值：
3/4 supported、至少两个非实现维度、未观察到重大事实错误，且 3 个获批答案的物质肯定结论都绑定可打开 Citation。失败题没有重试、
替换或追认。

本 Result 本身只拥有公开 4 题证据，不单独给 `V-WEB-001` 下 PASS。用户随后提供并执行现场题，见
`ITER-010-RESULT-V-WEB-001-USER-ONSITE-QUESTION`；两份 Result 合并后 `V-WEB-001` PASS。`V-PREVIEW-001` 仍要求用户看过真实结果后
作出 `CONTINUE / REDIRECT / REJECT`，因此 Slice/Iteration 尚未接受，Production Activation 仍为 `NOT_EXECUTED`。

## Exact freeze and authorization

- 初始 4 题 suite：
  `var/iteration-010/slice-001/run-004-direction-preview/direction-suite-freeze.json` /
  `sha256:f75f2e7881b8b57b4e9dd1b7ff01da9ac322bb4c853ed1853f881db9ca74f100`；candidate
  `aa1423465a240f3155f9773bcd97652cf88e4a1f` / tree `5f589efde7ba89aeaf8ea9bc37f499ed518b8726`；
- Q1 暴露系统性输入闭包缺口后永久烧毁。`FINDING-010-026` 修复并由 focused 64/64、docs 403/403、compile/diff 和 full
  1116 中 1111 PASS + exact historical 4 FAIL/1 ERROR hold 验证；
- 未消费 Q2—Q4 的 successor suite：
  `var/iteration-010/slice-001/run-004-direction-preview/direction-suite-successor-freeze.json` /
  `sha256:b509042147f9c02123652c8be3a884a7c5233fd4d8fb93e50bb5286f7d56b93d`；candidate
  `17cff661dc0f3fd51fcbce0721b801ccd2fbb8e3` / tree `dc8ce84cc1eb36a6a60f695bca6c327ac923f0fe`；Q1 不在 successor
  remaining set 中；
- repository `mall` revision `0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`，Binding
  `binding_4ef0d3446b3e44c79ed3c0ffc855d5c9`，Maven Snapshot
  `structure_snapshot_5033a7fc944141d08ecd5ad3879ce1ba`；Source Profile `ITER-010-MALL-JWT-SOURCE:2` /
  `sha256:4746c3e41de9d93c10b3b3eaa752b6e0959290e2e7772499a359031a7d497301`；
- Provider `https://api.deepseek.com/chat/completions` / `deepseek-v4-pro`，qualification
  `CC-DEEPSEEK-CHAT-NO-TOOLS-001:sha256:01c6fbef5fbe11678b0bac3f9e16d6b5b9f0fb9e341a60383931a9509e534218`；
- root live authorization `codex-user-message:sha256:815d868ca3df4795276934acbc21d12584fcfd4cb49b31c67696c72d3a5a6b74`；
  累计调用不限，但每题仍绑定 24-call 产品安全熔断、retry 0、Provider switch 0、resources/credential 排除与非生产边界。

## Four-question result

| ID / dimension | Exact question | Candidate | Result / Review | Browser outcome | Dispatch / elapsed |
|---|---|---|---|---|---:|
| Q1 / system purpose + overall architecture | `mall-admin` 安全子系统职责；`mall-admin`/`mall-security` 边界、依赖方向、认证/授权分工与证据边界 | `aa14234…` | `engineering_result_b15fde6075bb591118c4c57c62b5463c`；Answer/Review 未到达 | `FAILED_CLOSED / NO_PROGRESS_FUSE_EXHAUSTED`；0 Citation | 5 / 26,511 ms |
| Q2 / basic startup + configuration + evidence boundary | 本地启动并调用管理员登录/受保护接口时，可确认的构建依赖、安全接入步骤与 resources 参数未知 | `17cff66…` | `engineering_result_99c0b25a4d48468270b66b5e0513c2ea` / `sha256:06cc2fa76c5e949fa147694cd384a9bafa6e5b54177e104d82fbda0386cb7f5a`；Review `engineering_review_7308ea330a1200a1584f19a765461716` APPROVED | 4 Citation 全部打开 | 8 / 39,241 ms |
| Q3 / fault diagnosis + business flow | 登录后持 JWT 访问受保护接口仍为 401/403 时，区分令牌提取/校验、认证上下文与动态权限检查面 | `17cff66…` | `engineering_result_de7ce1ef7744b233a984ac31fb9ea473` / `sha256:22fb5648465f053d9ecbd9f4a71bd8eb0b630c90e878a551640bd85f5b0231bf`；Review `engineering_review_d3f72745e68ae9b2d0055d58d71349ee` APPROVED | 3 Citation 全部打开 | 8 / 45,678 ms |
| Q4 / change impact + test intent + evidence boundary | 修改 JWT header/prefix/expiration 对两模块的影响、回归风险、测试覆盖与不能下的结论 | `17cff66…` | `engineering_result_1ba12924eabce112d32dd00be410d5e5` / `sha256:396ed0cbba47b7dfbdaacd4611a4ec7f74834625cedc18c00a819d2a7bb25da1`；Review `engineering_review_a046bd992588fde79baf556d6c2000a3` APPROVED | 4 Citation 全部打开 | 9 / 49,110 ms |

Q1 的前三个 search/read 动作取得观察后，角色因输入里没有先前 query 又重复相同 SEARCH；第二次重复 observation 触发 no-progress 2。
修复没有提高熔断：Ledger 追加 attempt-scoped action intent，角色输入显式投影，Broker 在 Worker 前以
`DUPLICATE_ACTION_INTENT` 拒绝重复 query/locator，Prompt 升为 `@8`。Q2—Q4 在新 candidate 上分别以 0 no-progress 完成。

## Answer and Citation inspection

- Q2 直接给出 `mall-admin` 内外部构建依赖与 `MallSecurityConfig` 的接入职责，并把未授权 resources 中的端口、数据库连接等运行参数保留为
  unknown；4 个打开的 Citation 为 1 个 exact POM、1 个 exact Java Source、2 个 World Model relation；
- Q3 给出令牌提取/校验 → Security Context → 动态权限判定的定位顺序；本题 Package 没有读入动态权限实现时，正文明确不声称其内部
  检查点；3 个 Citation 均为 exact Java Source；
- Q4 说明 `UmsAdminServiceImpl` 的生成/刷新调用、Filter 的 header/prefix/validate 链、`JwtTokenUtil` 的 expiration/`exp` 逻辑和公共
  Bean 装配；本题没有 Test/Build/runtime observation，因此没有伪造测试覆盖或具体运行回归结论；4 个 Citation 均为 exact Java Source；
- 11 个 Citation 都由 in-app Browser 实际打开。每题内部 Citation 的 revision、Package digest/seal、Result ID/digest 完全一致，
  `origin_class` 只为 `EXACT_REVISION_SOURCE` 或 `WORLD_MODEL_COGNITION`，`projection_is_answer_input=false`；
- suite 完成后同一 Browser tab 的 developer console log 为 `[]`。主视图只展示问题、答案/limitation 与 Citation；Cognition、Ledger、
  Broker、Package、usage 和 Review 保持折叠。

## Package, usage and transport audit

| Q | Package digest / seal | Ledger seal | support/citation | boundary/audit | Source operations / files / bytes | Role calls | Input / output tokens |
|---|---|---|---:|---:|---:|---:|---:|
| Q1 | `sha256:72e1e158…` / failed-close package | `sha256:cca22990…` | 34 | 9 | 4 / 37 / 138,218 | 5 | 90,968 / 954 |
| Q2 | `sha256:364f6dd3…` / `sha256:71683df7…` | `sha256:c3303f71…` | 35 | 10 | 4 / 17 / 65,877 | 8 | 173,014 / 1,714 |
| Q3 | `sha256:34f7983d…` / `sha256:a6476f5c…` | `sha256:816fb2ec…` | 36 | 11 | 4 / 15 / 53,278 | 8 | 181,244 / 2,262 |
| Q4 | `sha256:6f047cee…` / `sha256:d35816de…` | `sha256:58dc0f30…` | 37 | 14 | 5 / 16 / 67,896 | 9 | 239,435 / 2,597 |

合计 30 次 role dispatch、17 次 Broker-authorized read-only operation、85 file observations、325,269 source bytes、684,661 input tokens、
7,527 output tokens、160,540 ms；3 个 approved 答案实际打开 11 个 Citation。每个 run 均为一次 verified TLS handshake，合计复用 26 次；
post-dispatch outcome unknown、request retry、Provider switch、Source write、silent fallback 均为 0。四个 Gateway 共 90 个 model manifest
item，对 `src/main/resources` 的 exact 匹配数为 0；所有模型角色 direct Source/FS/Shell/network/credential authority 为 false；Production
Activation 均为 `NOT_EXECUTED`。

原始收据永久保存在 `var/iteration-010/slice-001/run-004-direction-preview/` 下四个独立 run 目录。launch/terminal/Gateway SHA-256、exact
Request/evaluation-subject/run-authorization digest 和逐 dispatch audit 都已核对。后续现场题确实使用全新目录、exact question grant 和
clean candidate 执行，没有覆盖这些文件。

## Remaining blocking work

- 用户现场题已由 `ITER-010-RESULT-V-WEB-001-USER-ONSITE-QUESTION` 完成，公开题与该 Result 合并后 `V-WEB-001` PASS；
- 用户实际判断这些 Web 结果并给出 `CONTINUE / REDIRECT / REJECT` 后，才可执行 `V-PREVIEW-001` 与 Slice Reflection；
- `V-XD-001` 仍因当前 Maven Cognition 不含 accepted declaration/`CALLS` 保持独立 blocking；本结果没有把 Maven relation 冒充 Java
  call behavior；
- 本结果不是 Slice Result、Acceptance、hidden、跨工程、三臂 comparison、持久恢复或 Production evidence。
