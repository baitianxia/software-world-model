---
id: ITER-010-VERIFICATION
kind: iteration-verification
status: failed
authority: execution-evidence
owners: [quality]
depends_on: [ITER-010-PROPOSAL]
code: []
tests: []
iteration: ITER-010
product_goal_gate: V-000
product_goal_outcome: user-visible-general-engineering-qa-delta
product_goal_evaluation: independent-hidden-plus-live-ad-hoc
product_goal_result_id: ITER-010-RESULT-SLICE-001-STOP-REDIRECT
---

# ITER-010 Verification Matrix

## Pre-freeze implementation evidence

截至 `2026-08-22`，candidate `b8360a3…` 的 focused 58/58、docs 389/389、full 1108/1103，以及修复
`FINDING-010-015` 后 candidate `50b08b5…` 的 focused 59/59、docs 391/391、full 1109/1104 均作为历史证据保留。后续 live
暴露 `FINDING-010-016—019` 后，Prompt `@4` 实现 focused 69/69、docs 395/395、`py_compile`、`git diff --check` 均 PASS；允许 AF_UNIX 的 full
discovery 共 1112 项，其中 1107 PASS，唯一 4 FAIL + 1 ERROR 的测试 identity、结果类型和 marker 仍精确等于
`FINDING-008-020`。因此 raw full suite 仍为 FAIL，deterministic gate 仅为
`PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD`。这些证据只允许提交新的 clean product freeze，不提前给真实产品 Case 下 PASS。
`FINDING-010-020/021` 的 latest-basis/eligible-locator 与 exact call-reserve 修复随后通过 focused 117/117、docs 397/397、`py_compile`、
`git diff --check`；full discovery 增至 1113 项，其中 1108 PASS，唯一 4 FAIL + 1 ERROR 仍保持同一历史 hold identity、marker 与 Codex
digest，没有新增失败。
`FINDING-010-023` 的 fail-closed Browser presentation 与 current Operations write-back 最终通过 focused 118/118、docs 399/399、
`py_compile`、`git diff --check`；full discovery 为 1114 项，其中 1109 PASS，唯一历史 4 FAIL + 1 ERROR identity/type/marker/digest 不变。
首次 full run 曾以新增 ITER-007 system fileset digest mismatch 阻断；同步 ITER-007/010 exact current fileset digest 后针对性 84/84 与最终
full gate 均闭合，因此没有把该新增失败混入 historical hold。
`FINDING-010-024/025` 随后把 FINISH 字段组合与 disposition support/boundary eligibility 提升为 Prompt + 动态 Application 控制；最终
Engineering QA focused 63/63、docs 401/401、`py_compile`、`git diff --check` PASS，full discovery 增至 1115 项，其中 1110 PASS；唯一
4 FAIL + 1 ERROR 的 identity/marker/Codex digest 仍精确保持同一历史 hold。
V-BASELINE/V-ARCH/V-QINTENT/V-COGNITION/V-INVESTIGATE/V-BROKER/
V-LEDGER/V-ISOLATION/V-REVIEW/V-LIMIT/V-SEC 的确定性子断言已有测试证据，但它们的 Case verdict 仍等待 clean freeze 或所要求的真实链；
`V-WEB-000` 前六次永久失败的真实尝试如下。candidate `b8360a3…` 在第二个 Provider output 暴露 live role-progress 大小写错误；2 次
dispatch，见 `FINDING-010-015`。修复后的 candidate `50b08b5…` 继续完成 4 次 dispatch，但目录级 SOURCE capability 的首个 search
耗尽 64 文件上限，后续 Broker 拒绝；模型随后提交含空引用的 FINISH，暴露 Schema/Prompt/shared validator 与领域 invariant 不一致，见
`FINDING-010-016/017`。第三个 candidate `e35d8f7…` 已用新 2-call qualification 和 17 个 exact 文件 Profile 运行；SOURCE search
完整检查 12 文件且未触发 fuse，但自然语言 literal query 返回 0 items 后，模型把 allowlisted path 误作 opaque locator reference，3 次
role dispatch 后失败关闭，见 `FINDING-010-018`。三次 Web run 共 9 次 role dispatch，另有 2 次 current qualification call，累计
11/20，见 `FINDING-010-018`。第四个 candidate `91dffec…` 正确完成 literal search 和 opaque locator read，但重复读取已返回完整内容的
同一路径；相同 progress digest 连续两次触发 no-progress fuse，5 次 role dispatch 后在 Answer/Review 前失败关闭，见
`FINDING-010-019`。四次 Web run 共 14 次 role dispatch，另有 2 次 current qualification call，累计 16/20；全部 retry 0、switch 0、
Production Activation `NOT_EXECUTED`。用户随后把总上限提高到 28；Prompt `@4` clean candidate `1f4e1b0…` 的第五次 run 完成 5 次
dispatch 后，模型未引用紧邻的最新 Ledger Result，并再次选择已返回 full content 的 locator。Application 在 Source operation 前失败关闭，
见 `FINDING-010-020`。五次 Web run 共 19 次 role dispatch，另有 2 次 current qualification call，累计 21/28；第五次仍为 retry 0、
switch 0、Production Activation `NOT_EXECUTED`。Prompt-only 控制已改为显式 latest-basis/eligible-locator 投影与 Application validation；同时
Preview Request call fuse 与 exact run grant 对齐以预留 Answer/Review，见 `FINDING-010-020/021`。旧 candidate/run 不能由后续修复追溯
覆盖。candidate `d6d8d02…` 随后在 7-call exact grant 下完成 Understanding、literal search 和 3 个不同 full-content READ；每步都满足
latest basis/eligible locator，no-progress 0。第 4 次 Investigation 后仍未完成全部 material conclusions，Application 在第 6 个 Provider
dispatch 前保留 Answer/Review 所需 2 次调用并以 `INDEPENDENT_REVIEW_RESERVE_EXHAUSTED` 关闭，Draft/Review 均为 0，见
`FINDING-010-022`。六次 Web run 共 24 次 role dispatch，另有 2 次 current qualification call，累计 26/28；全部 retry 0、switch 0、
Production Activation `NOT_EXECUTED`，剩余 2 次未使用。该 run 还暴露 fail-closed Result 被 UI 固定标成 `REVIEWED RESULT` 的显示缺口，
已按 `FINDING-010-023` 修复；因此 `d6d8d02…` 也成为 burned candidate。用户随后以
`sha256:815d868ca3df4795276934acbc21d12584fcfd4cb49b31c67696c72d3a5a6b74` 取消本次累计调用上限，其他披露/零重试/resources 排除/
非生产边界不变。candidate `31b1a19…` 的第七次 run 完成 7 次 dispatch，Prompt `@5` FINISH 错带 SOURCE evidence class，见
`FINDING-010-024`；candidate `449e925…` 的第八次 run 也完成 7 次 dispatch，字段组合已合法，但把 `SOURCE_RESULT` Ledger entry ID
误作 Package support/boundary reference，见 `FINDING-010-025`。两次都在 Answer/Review 前失败关闭。

clean candidate `f38f6cc…` 的第九次 run `web-v-web-000-012` 以 Prompt `@7` 完成 9 次 dispatch：Understanding、6 次
Investigation、Answer、Review。5 个 Broker Decision 全部授权，no-progress 0；Package 为 37 support/citation + 14 boundary/audit；
Answer 形成 5 个 affirmative claim 和 1 个测试覆盖 limitation，独立 Review `APPROVED`。Browser 显示 `REVIEWED RESULT`，6 个 Source/
World Model Citation 全部实际打开且绑定同一 Package/Result，console 为空。terminal receipt 为 retry 0、switch 0、一次 TLS handshake
复用 8 次、Production Activation `NOT_EXECUTED`；全部 manifest 对 `src/main/resources` 匹配数为 0。九次 Web run 共 47 次 role
dispatch，另有 2 次 current qualification call；详见 `ITER-010-RESULT-V-WEB-000-LIVE-RUN-009`。因此 `V-WEB-000` 由当前 exact run
获得 PASS；旧失败不改写。`V-XD-001` 仍因 `mall` 未形成 declaration/`CALLS` Result 保持独立 blocking，见 `FINDING-010-014`。
随后冻结 4 条不同覆盖维度的公开方向题，suite digest 为
`sha256:f75f2e7881b8b57b4e9dd1b7ff01da9ac322bb4c853ed1853f881db9ca74f100`；现场题仍由用户持有。第一题绑定 clean candidate
`aa14234…`，在 5 次 dispatch 后因调查角色重复 `SOURCE / search("mall-security")` 触发 `NO_PROGRESS_FUSE_EXHAUSTED`，retry/switch 0、
Production Activation `NOT_EXECUTED`。`FINDING-010-026` 已把此前未投影的 attempt-scoped query/locator intent 加入 Ledger/角色输入，并由
Broker 在 Worker 前拒绝重复工作；Prompt 升级为 `@8`。该题与 candidate 永久失败，不重放。

修复后的 clean candidate `17cff66…` 只消费 successor freeze 中的 Q2—Q4，三题分别以 8/8/9 dispatch、0 no-progress 到达独立 Review
`APPROVED`；11 个 Citation 全部打开，公开题总分为 3 supported / 1 fail，达到两个非实现维度阈值。用户随后以 exact message digest
`sha256:684849e3…e9c9` 现场提出“登录流程是怎样的？”。clean candidate `8632904…` 的全新 onsite run 以 10 dispatch、6 个只读 Broker
operation、0 no-progress 形成 Result `engineering_result_e5f3c335944de0f2f57e8f9fdd48b419` 和 Review `APPROVED`；3 个 exact Source
Citation 全部打开、console `[]`、retry/switch/outcome-unknown 0、resources match 0、Production Activation `NOT_EXECUTED`。因此公开 4 题
与现场题合并后 `V-WEB-001` 技术 PASS。`FINDING-010-027` 同时保留正文仍以 Controller/Service/Filter 方法调用序列为主且省略
`insertLoginLog` 副作用的方向信号；用户随后以
`codex-user-message:sha256:d746968f58cea4d2b7689b5902c0ff97f42f63c93ffc4cbc40551cfa2c0359e0` 要求实现者自行复核并修复已知问题；旧记录曾将其解释为 `REDIRECT`。
`FINDING-010-028` 将共同根因定位到自由文本抽象层级、扁平 Answer Claim 和不可执行的 Review 方向质量 Gate。因此历史
`V-ANSWER-001`、`V-REVIEW-001`、`V-XD-001` 与 `V-PREVIEW-001` 继续为 FAIL；`V-REFLECT-001` PASS 只表示失败复盘完整。

[PDR-001](decisions/PDR-001-resume-as-rework.md) 依据最新用户收据修订的是迭代级决定，不改写上述执行事实。旧消息 `d746968f…` 没有明确
表达 `REDIRECT`；后续 `32b298de…` 收据已恢复 ITER-010/Slice1 的编码，live 仍未获得新 freeze 后授权。当前必须先执行以下持续 Web
Alpha Case，不能用旧的单题启动器、测试或固定 1+1 回放代替。

用户随后提供的 root + exact mall/DeepSeek scope 已授权持续 Alpha。candidate `b6e13eb…` 的首次会话真实启动并以 8 次 role dispatch、
retry/switch 0 回答现场登录题；完整 `UmsAdminServiceImpl` 已进入 Package/Reviewer，但正文再次遗漏成功登录审计写入，Reviewer 错误
`APPROVED`。该 Result 只把 `V-EXPERIENCE/V-ANSWER-REWORK` 推进为 in-progress，并以 `FINDING-010-033` 保留失败，不能取得 PASS。会话还
暴露 Gateway SQLite 主文件为 `0644`，见 `FINDING-010-034`。当前 worktree 已升级
`ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3`：FINISH 原子 evidence observations、Answer observation/evidence closure、Reviewer 独立
Package/Draft observation audit，以及 SQLite 主文件/WAL/SHM `0600` 创建测试均通过；新协议仍须 clean freeze、current Conformance 和完整
原题 + 两道异质题 + 受控失败的持续 browser run。

Engineering QA 83/83、docs/freeze/browser 86/86、current docs 427/427 PASS；在允许 AF_UNIX 的本机执行面运行 full 1144 项得到 1139 PASS，
raw 仍精确为既有 4 FAIL + 1 ERROR，见 `FINDING-010-035`。默认沙箱额外出现的 AF_UNIX denial 不属于产品回归，raw full suite 仍不写成
PASS。

clean candidate `fc827ce…` 已取得 current DeepSeek Conformance `sha256:c6f6a0f…` 并真实提交原题。5 次 role dispatch、retry/switch 0；
Package 与 Answer affirmative 正文已显式覆盖 `loginLogMapper.insert` 审计写入，Gateway 主文件/live WAL/SHM 为 `0600`。但 Answer 的末尾
coverage-only Limitation 因非空 link 规则错绑全部 supported observations，Application 以 `answer claim kind differs from its material
observation` 失败关闭；见 `FINDING-010-036`。该 Result 不能取得答案或体验 PASS。

coverage-only Limitation 收窄后的 Answer/strategy/model-source 49/49、Engineering QA 86/86、current docs 430/430 PASS；最终 full 1147 项
中 1142 PASS，raw 仍精确为既有 4 FAIL + 1 ERROR，见 `FINDING-010-037`。新修复尚未取得 clean freeze 后的 live Result。

clean candidate `e15ec50…` 与 current Conformance `sha256:5ef04be6…` 的原题 run 同样为 5 次 role dispatch、retry/switch 0、private SQLite。
上一修复的空-link coverage Limitation 已生效；但 Investigation 只读 README 后过早 FINISH，Answer 将 limitation observations 错标为
process/impact roles，Domain 以 structured-output violation 失败关闭。`FINDING-010-038` 已形成 closed kind/role mapping 与跨 evidence-class
unknown 消减规则，尚待新 clean candidate live 重验。

closed mapping/跨 evidence-class 修复后的 clean candidate `c7e32b5…` 以 current Conformance `sha256:8802280…` 启动同一持续会话。原现场题
用 7 次 dispatch 形成 `APPROVED` Result：固定 revision 的 Controller/Service Source、正文和独立 Reviewer 都覆盖登录主链、
`SecurityContext`、JWT、失败分支与 `loginLogMapper.insert` 审计副作用，private SQLite 成立。随后两道异质题均在首个角色调用收到
`PROVIDER_HTTP_ERROR`，每题一次调用、retry/switch 0，listener 继续；受控超限页面请求在 Provider 前拒绝，调用根不增加且 health 保持
`READY`。旧实现却把已知 HTTP 失败在页面/terminal audit 重标为 binding drift/outcome unknown，见 `FINDING-010-039`。因此该会话只证明
原题质量修复和请求隔离，不能取得三题 PASS；错误传播/审计修复的 Engineering QA 全组 87/87 PASS，仍须新 clean candidate live 重验。
允许本机 AF_UNIX 的完整回归为 1148 项、1143 PASS，raw 唯一 4 FAIL + 1 ERROR 仍与既有 V-009/Codex historical hold 完全相同，见
`FINDING-010-040`；默认沙箱额外 6 ERROR + 1 FAIL 精确属于 socket permission noise，不进入产品失败集合。

clean candidate `31a9ccd…` 随后使用正确 DeepSeek CLI 发起新的 current Conformance；run
`ccrun_717391edb4c6482d8809dd45be405626` 在第一次 dispatch 收到 HTTP 402，Result `sha256:44bf29b…` 为 FAIL、qualification
`NOT_ISSUED`、request 1、retry 0、TLS/credential 成功。官方错误码将 402 定义为余额不足，见 `FINDING-010-041`。旧 run-008 adapter
qualification 仍在有效期且 implementation/config digest 相同，但不证明当前账户可用或新候选三题质量；因此 live 保持 environment-blocked，
不得重试、切 Provider 或用旧答案补齐。

余额恢复后的后续候选最终推进到 clean `5ce5ab0…` 与 run-015 fresh DeepSeek Conformance 2/2 PASS。同一持续会话 3 题共 32 dispatch、
retry/switch 0，但 raw SQLite 复核否定页面的两个 `APPROVED`：原登录题再次漏掉 `insertLoginLog` 审计副作用；混合 support/unknown 题
输出两个 `DIRECT_ANSWER` 而失败关闭；401/403 题用 `SecurityConfig` 接线替代未读取的动态 manager 自身实现。见
`FINDING-010-048`。受控超限仍在 Provider 前拒绝，private files 与 Production `NOT_EXECUTED` 成立；这些安全/隔离事实不构成答案质量
PASS。当前 mandatory-read path、唯一 direct-answer shape 与独立 side-effect audit 的定向组合 96/96、docs 442/442 PASS；允许本机
AF_UNIX 的 full 1162 项中 1157 PASS，唯一 4 FAIL + 1 ERROR 仍精确为冻结 V-009/Codex historical hold。仍须 clean freeze、fresh
Conformance 和完整三题重验。

该处置形成 clean `00afecd…`，run-016 fresh DeepSeek Conformance 2/2 PASS；同一持续会话三题分别用 12/13/13 次 dispatch，全部未形成
交付答案。原题的第 12 次总 dispatch 为 post-dispatch `PROVIDER_OUTCOME_UNKNOWN`，Gateway raw state 正确但页面误报 binding drift；
另两题的 Question Understanding 分别声明 8/6 个 mandatory-read paths，12 次 Investigation 被 search/read 和非必读 locator 消耗，无法
FINISH。terminal receipt `sha256:b3c94c2…` 记录 38 dispatch、retry/switch 0、private files、Production `NOT_EXECUTED`；22,000 字符
输入仍在 Provider 前拒绝且 call root 不增加。见 `FINDING-010-049`。当前 4-path/fuse reachability、required-locator priority、remaining-fuse
投影与 exact outcome-unknown propagation 的 Engineering QA 组合 97/97、docs 444/444、compile/diff PASS；允许 AF_UNIX 的 full
1163 项中 1158 PASS，raw 唯一 4 FAIL + 1 ERROR 仍精确为冻结 V-009/Codex historical hold，见 `FINDING-010-050`。新 clean candidate
与 fresh live 仍待执行。

该处置形成 clean `d12223f…`，run-017 fresh DeepSeek Conformance 2/2 PASS。三题调查均在 4-path/12-call contract 内进入 Answer；混合
构建/安全/resources unknown 题以 14 次 dispatch 获得 `APPROVED`，并把 resources 中运行参数保留为未知。原登录题与 401/403 题分别以
9/12 次 dispatch 到达 Answer，却都因 follow-up claims 的 role 次序为“process → impact → process …”在 Review 前失败关闭；raw claims 的
checklist、observation、evidence links 完整。terminal receipt `sha256:e901faf2…` 记录 35 dispatch、retry/switch 0、private files、
Production `NOT_EXECUTED`，22,000 字符输入在 Provider 前拒绝且 call root 不变。见 `FINDING-010-051`。可信 adapter 的受控稳定排序回归
已使 Engineering QA 98/98 PASS；docs 446/446、compile/diff PASS，允许 AF_UNIX 的 full 1164/1159，raw 唯一 4 FAIL + 1 ERROR 仍为
冻结 historical hold，见 `FINDING-010-052`。新 clean/fresh live 尚未闭合。

该处置形成 clean `88e33bd…`，run-018 fresh DeepSeek Conformance 2/2 PASS。原登录题与构建/resources unknown 题分别以 13/15 次
dispatch 得到 `APPROVED`；401/403 题以 8 次 dispatch 形成三个检查面、401/403 区分、Citation 和独立
`IMPLEMENTATION_EVIDENCE` 核对依据，但后者独自绑定的 3 个 material observations 被默认正文无条件隐藏，因而在 Review 前失败。
terminal receipt `sha256:08d84045…` 记录 36 dispatch、retry/switch 0、private files、Production `NOT_EXECUTED`，22,000 字符输入在
Provider 前拒绝且 call root 不变。见 `FINDING-010-053`。conditional implementation-evidence visibility 的 Engineering QA 99/99 PASS；
docs 448/448、compile/diff PASS；允许 AF_UNIX 的 full 1165 项中 1160 PASS，raw 唯一 4 FAIL + 1 ERROR 仍为冻结 historical hold，见
`FINDING-010-054`。确定性 Gate 已闭合，新 clean/fresh live 尚未执行。

该处置形成 clean `c65617e…`，run-019 fresh DeepSeek Conformance 2/2 PASS。同一持续会话三题分别以 12/15/12 次 dispatch 获得模型
`APPROVED`，且第三题 requested implementation evidence 已进入默认正文；但独立技术复核发现其一处把未认证与权限不足都归为 403，后一处
又正确区分为 401/403。raw Review 逐字复述冲突仍将四项 quality 全部 PASS。terminal receipt `sha256:cfed19a1…` 记录 39 dispatch、
retry/switch 0、private files、verified transport、Production `NOT_EXECUTED`；超限输入在 Provider 前失败且 call root 保持 39。见
`FINDING-010-055`。新增第五项 closed `claim_consistency` 已有三模块 62/62 定向证据，完整 deterministic 与 fresh live 尚未闭合。

上述修复最终通过 Engineering QA 99/99、docs 450/450、compile/diff；允许 AF_UNIX 的 full 1165 项中 1160 PASS，raw 唯一 4 FAIL +
1 ERROR 仍为冻结 historical hold，没有 ITER-010 新失败，见 `FINDING-010-056`。确定性 Gate 已闭合，新 clean/fresh live 尚未执行。

该处置形成 clean `274e5ea…`，run-020 fresh DeepSeek Conformance 2/2 PASS。Q1 以 10 次 dispatch 获得独立可接受的 `APPROVED`；Q2 已
声明 4 个 mandatory paths，却因没有 direct locator 而把 path/filename 当内容搜索词，5 次 dispatch 后触发
`NO_PROGRESS_FUSE_EXHAUSTED`；同一 listener 随后接受 Q3，后者以 11 次 dispatch 完整读取四个决定性实现，却在一个 `SUPPORTED`
FINISH item 混入 `LIMITATION` 与 search-only boundary reference，被本地 validator 以 `STRUCTURED_OUTPUT_INVALID` 正确关闭。22,000
ASCII 字符约 22 KB，低于 65,536-byte server limit，合法发生 1 次 dispatch 后人工停止；terminal receipt `sha256:1408e827…` 记录
4 题、27 dispatch（10/5/11/1）、retry/switch 0、verified transport 与 Production `NOT_EXECUTED`。见 `FINDING-010-057/058`。
Request + attempt + Profile-bound direct locator、结构互斥 FINISH arrays 和 modality-minimal Understanding Prompt 的 Engineering QA
101/101、docs/compile/diff PASS；允许 AF_UNIX 的 full 1167 项中 1162 PASS，raw 唯一 4 FAIL + 1 ERROR 仍为冻结 historical hold，见
`FINDING-010-059`。确定性 Gate 已闭合，新 clean/fresh live 尚未执行。

该确定性处置形成 clean `dfba244…`，run-021 fresh Conformance 2/2 PASS。同一持续 Alpha 中，Q1/Q3 各以 8 次 dispatch 得到独立可接受的
`APPROVED`；Q2 的 4 个 mandatory paths 已全部通过 direct locator READ，但第 5 个 Investigation call 在仍有 8 个含当前动作 call 时
FINISH，并把 3 个 UNKNOWN 同时放入 supported 与 non-supported arrays，被本地 Schema 以 `STRUCTURED_OUTPUT_INVALID` 正确关闭。
Q2 后 listener 继续接受 Q3；66,000-byte 输入在 Provider 前拒绝且 Gateway 根保持 22。terminal receipt `sha256:d38d94bb…` 记录
8/6/8 dispatch、retry/switch 0、verified TLS、private files 和 Production `NOT_EXECUTED`。见 `FINDING-010-060`。当前 exact-once
partition 与 post-mandatory material-gap exhaustion 的 Engineering QA 101/101、docs/compile/diff PASS；允许 AF_UNIX 的 full 1167 项中
1162 PASS，raw 唯一 4 FAIL + 1 ERROR 仍为冻结 historical hold，见 `FINDING-010-061`。deterministic Gate 已闭合，新 clean/fresh live
尚待执行。

| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |
|---|---|---|---|---|---|---|
| V-EXPERIENCE-001 | 同一产品成为可持续体验的 Web Alpha | product / browser | 一条固定且文档化的启动命令；`http://127.0.0.1:8765/`；固定一个工程和 exact revision；同一启动会话提交原失败题、至少两个相邻或异质问题及一个受控失败场景 | 无认证；体验者不拼装逐题 freeze/grant/run 参数；连续自由提问无需逐题重启；页面显示产品/工程版本、已知限制、答案/Citation/请求失败；受控失败只关闭当前 Request，服务继续且 identity 不串扰；Gateway DB/WAL/SHM 从创建起为 `0600`；答案真实经过世界模型—调查—Broker/Source—证据链而非预制回放；无平行演示入口 | `dfba244…` / run-021 已证明 Q2 fail 后同一 listener 接受并批准 Q3、66,000-byte Provider 前拒绝、private files、retry/switch 0；但 Q2 仍为 structured-output/过早 FINISH FAIL，不能取得体验质量 PASS | NOT-RUN / blocking |
| V-ANSWER-REWORK-001 | 答案与 Reviewer 的已知缺陷以通用机制修复 | product / quality | 原现场登录题；至少两个相邻或异质题；至少一题非实现走读；独立技术复核 | 重大错误 0；重要结论有 Citation；Reviewer 阻断层级错配、物质遗漏、无据结论和错误 Citation；无工程/问题/关键词/符号/类/方法/fixture/Oracle 特判 | run-021 的 Q1/Q3 独立可接受，Q2 暴露 duplicate FINISH partition 与 mandatory-minimum 过早结束；`FINDING-010-060/061` 已闭合 deterministic Gate，仍须新 clean/fresh 三题 Result 与独立技术复核 | NOT-RUN / blocking |
| V-PREVIEW-002 | 用户基于持续自由提问版本决定是否进入夯实 | product / direction | V-EXPERIENCE-001、V-ANSWER-REWORK-001 的真实 Result 与已知限制 | 独立评测先裁决技术质量；用户实际连续提问后决定 CONTINUE/REWORK/REDIRECT/REJECT；单题失败默认 REWORK，不自动 REDIRECT | not-executed | NOT-RUN / blocking |

| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |
|---|---|---|---|---|---|---|
| V-000 | 本轮相对 rejected baseline 可测缩短通用工程问答差距并证明完整 World Model Cognition 的独立价值 | product / comparison | 三个唯一 Slice Result；最终隐藏 10+2；现场题；完整认知、locator-only/empty 同链、成熟源码 Agent 三臂；新收据预提交 protocol | 完整认知与成熟 Agent 先过零重大错误/boundary/逐结论质量门；完整认知再相对 locator control 达到预提交质量或非 locator 调查成本增益；计建模成本/复用周期；同一 Web/Citation/Source 隔离成立 | ITER-010-RESULT-SLICE-001-STOP-REDIRECT#V-000 | FAIL / blocking |
| V-PRE-001 | exact product baseline、planning input 与 ITER-009 rejected 产品结论被准确分离 | readiness / baseline | product commit `1fb997bab6444523f82ebf1a514a1abbf79656c7` / tree `1369ce932c778c57a118123e8257ede476229d73`；planning commit `01dcfe2233625dfaa021495850fb18ae1323063b` / tree `8e364ae854bfaa48580ab080a3e0d9c9c43c3d6f`；predecessor Result | 技术资产复用；不继承 Acceptance/live grant/qualification；授权只基于 exact planning input；dirty baseline 禁止 | Git object/tree/branch inspection；Proposal/Manifest/Readiness | PASS / readiness blocking |
| V-PRE-002 | ITER-009 用户反馈被判为系统性架构/产品方向证据而非单题文风 | readiness / evidence | `ITER-009-RESULT-SLICE-001-STOP-REDIRECT`、ROADMAP Candidate、现场答案与用户裁决 | baseline gap 是默认实现走读、Reviewer 层级 Gate 缺失和 Source-off 通用问答边界，不按个别问题修 Prompt | Proposal Trigger、Result、Candidate | PASS / readiness blocking |
| V-PRE-003 | ENGINEERING_QA、严格 WORLD_MODEL 和显式 DIRECT 三种模式及新自适应调查职责已冻结 | readiness / architecture | FINDING-010-002、ADR-013/014/015/016、owning Contract list、V-ARCH-001 | World Model 概念不变；ENGINEERING_QA 使用 Investigation→Broker/Worker→Ledger→seal→Answer/Review；无 silent fallback | Proposal、Readiness、Slice1 Phase0 | PASS / readiness blocking |
| V-PRE-004 | 新收据只授权 Slice1 产品开发，没有扩大 live、Source disclosure、credential、Provider、browser、hidden 或 Production 权限 | readiness / authorization | planning receipt `d3b60bda…`、development receipt `585f02c4…`、此前设计绑定的 `1b327024… + 5cdb7000…`、Manifest authorization | Slice1 authorized/coding true 且是唯一 active Slice；Slice2/3 proposed/coding false；所有 live/disclosure 另取 exact grant | Readiness、Manifest、Current、Slice1 | PASS / readiness blocking |
| V-PRE-005 | hidden、成熟 Agent 历史输入、三臂消融授权边界、burn 和方向体验顺序明确 | readiness / comparison | final 10+2、early 5+2；旧 `6ca47f7d…` Agent/rubric/cache/source-bytes protocol；新增 `engineering_qa_ablation` proposed mapping | 首段 preview 可先执行；新三臂 protocol/digest/阈值不得伪用旧收据，Slice2 前须新用户收据；披露后产品变化烧毁输入 | Proposal、Manifest bindings | PASS / readiness blocking |
| V-PRE-006 | A1—A5、逐 Slice Reflection、自适应调查、证据分区、独立补证调查和资源/质量边界可机械核对 | readiness / architecture | Proposal assumption catalog、Manifest 三 nested mappings、System fileset、answer_protocol | prior-result/Broker/Ledger/seal 精确；support/citation 与 boundary/audit 不混；Slice1 仅 preview 一次补证，后续无永久一轮上限；answerable 超限 FAIL | Proposal、Manifest、Readiness、docs gate | PASS / readiness blocking |
| V-BASELINE-001 | Slice1 实际开发 subject 仍是 exact baseline 且没有未记录产品变化 | development / baseline | Git ancestry/tree、worktree、predecessor Result | baseline 可复现；任何变化归属 Slice1；旧运行 identity 不继承 | not-executed | NOT-RUN / blocking |
| V-ARCH-001 | 新模式先取得正式架构与 Contract Owner，世界模型概念及旧模式边界不被静默改写 | architecture / contract | FINDING-010-001/002、SYS-ADR-016、Product Success、runtime/Agentic/Evidence/World Model/Response/Source/Security/Browser、Manifest fileset、docs gate/tests | ENGINEERING_QA 明确为 adaptive investigation；World Model 保持持久外部认知；strict WORLD_MODEL source-off 与 DIRECT identity 保留 | not-executed | NOT-RUN / blocking |
| V-QINTENT-001 | Question Understanding 忠实表达用户目标、受众、抽象层级、物质结论和证据需求 | application / contract | 用途/架构/运行/故障/影响/实现、多条件、改述、不同受众 fixture | 原问题约束不丢失/新增；无题型/工程/关键词/符号路由；输出 schema 可审计 | not-executed | NOT-RUN / blocking |
| V-COGNITION-001 | World Model 作为 exact、持久、版本化、可验证、可更新的软件外部认知进入问答 | architecture / knowledge | context/scope/schema/snapshot、实体/关系/行为/约束/状态/evidence/coverage/unknown fixtures | 手册/地图只作为投影；认知不退化为 cache/hints；coverage 不足不成为 Source recall Gate | not-executed | NOT-RUN / blocking |
| V-INVESTIGATE-001 | Investigation LLM 根据 prior Ledger Result 自适应提出下一步并合法结束 | application / investigation | 至少两步依赖链、partial/zero cognition、no-progress、premature finish、改述 fixture | 每步引用 prior result/progress；不是 upfront 固定计划；无题目/工程/关键词/符号/类/方法/fixture/oracle 分支 | not-executed | NOT-RUN / blocking |
| V-BROKER-001 | Source Broker/Worker 在模型无直接 Source 权限下编译并执行受控读操作 | security / integration | 合法抽象 proposal、request/attempt/profile-bound mandatory-path locator、跨 attempt/forged locator、path/symlink/write/exec/network/secret/disclosure probes、exact revision drift | Broker policy 决定唯一合法操作；direct locator 不赋予模型 path authority；Worker execution only；所有模型 direct FS/Shell/network/credential/source=0；完整操作/bytes/outcome audit | not-executed | NOT-RUN / blocking |
| V-LEDGER-001 | Evidence Ledger 只追加，调查结束后才密封双分区 Package，identity 与 seal 语义正确 | application / evidence | append/overwrite、finish/stop、admissible/rejected、gap/failure/partial/conflict/unknown、old/new revision fixtures | 历史不可改；未 finish 不 seal；support/citation 仅 admissible；boundary/audit 强制保留且不得支持肯定 Claim；seal 非 truth；旧 Review 不批新包 | not-executed | NOT-RUN / blocking |
| V-ISOLATION-001 | Investigation、Answer、Reviewer 与实际 Source 权限物理/应用隔离 | security / isolation | source injection、path/write/exec/network/secret probes；role package/import/mount audit | 只有 Broker/Worker 受控读；Source untrusted；Investigation/Answer/Reviewer 直接 repo/source/tool access=0；非法动作失败关闭 | not-executed | NOT-RUN / blocking |
| V-ANSWER-001 | Preview 跨类型问题先给直接、层级匹配的答案，代码细节按需 | product / answer | 一个真实工程 4 条不同覆盖维度问题、exact Package、结论级 rubric | 至少 3 supported 且覆盖至少 2 个非实现维度；重大错误 0；每个物质结论 Citation；无内部诊断平铺 | ITER-010-RESULT-SLICE-001-STOP-REDIRECT#V-ANSWER-001 | FAIL / blocking |
| V-REVIEW-001 | Reviewer 阻断缺陷并以具体 gap 启动独立 Verification Investigation | application / review | 对抗 Draft、current Package/Ledger、specific/invalid gap、两步结果驱动补证 fixture | Reviewer 不提可执行操作；新调查用新上下文读 gap+current Package/Ledger，经 Application/Broker/Worker 多步适应；不回初始调查；新包重答重审 | ITER-010-RESULT-SLICE-001-STOP-REDIRECT#V-REVIEW-001 | FAIL / blocking |
| V-LIMIT-001 | Preview 在调查或证据不足、安全熔断耗尽时保持诚实 | application / boundary | 可回答、证据不足、合法补证、无进展、上限耗尽、answerable/boundary fixture | 不伪造、不把未查到写成不存在；Slice1 最多一次补证；answerable 因熔断未回答计 FAIL；boundary 仅可独立审核 Limitation 或 fail closed | not-executed | NOT-RUN / blocking |
| V-SEC-001 | Slice1 exact revision、allowlist、untrusted Source、Provider disclosure、Secret、预算与 Web 安全成立 | security / integration | drift、oversize、injection、unauthorized fragment/provider、review tamper、outcome unknown、non-loopback probes | 全部失败关闭；request retry/provider switch/source write/update/silent fallback=0；合法本地确定性路径完成 | not-executed | NOT-RUN / blocking |
| V-XD-001 | 同一 ENGINEERING_QA 答案组合 ITER-006 accepted World Model 认知与 query-time 新来源 Evidence | product / integration | declaration/`CALLS` Result + repository document/config/test/source conclusion；无符号自然问题 | 同一 Ledger/Package/Answer/Review；结论分别绑定正确来源；不是两个正文或模式拼接 | ITER-010-RESULT-SLICE-001-STOP-REDIRECT#V-XD-001 | FAIL / blocking |
| V-WEB-000 | Slice1 在完整夯实前交付最早可体验的真实 Web 微纵切 | product / browser | exact freeze/live grant、普通用户无认证、一条 World Model + query-time Source 代表问题 | 最小真实链可用；exact revision/read-only/untrusted Source/support-citation 分区/Citation/独立 Review 全部成立；非回放/CLI | `ITER-010-RESULT-V-WEB-000-LIVE-RUN-009`；candidate `f38f6cc…` / exact mall `0504e86…` / Result `engineering_result_2025ba4a523a363c6a8f463e670dfc31` / 9 dispatch / 6 opened Citation / Review APPROVED / retry 0 / switch 0 / Production Activation NOT_EXECUTED；前 8 run 永久失败保留 | PASS / blocking |
| V-WEB-001 | 微纵切后从同一 product-owned ENGINEERING_QA loopback Web 执行完整方向体验 | product / browser | V-WEB-000 后 exact freeze/live grant、4 条任务和至少一条现场题 | 页面交付答案/limitation与可打开 Citation；诊断折叠；console clean；持久恢复/复杂矩阵未完成不冒充 Acceptance | ITER-010-RESULT-SLICE-001-STOP-REDIRECT#V-WEB-001 | PASS / blocking |
| V-PREVIEW-001 | 在全面夯实前取得真实用户方向裁决 | product / directional-preview | V-WEB-001、4 个不同覆盖维度、现场题、非验收/非生产标识 | 用户能判断是否像工程问答助手并决定 CONTINUE/REDIRECT/REJECT | ITER-010-RESULT-SLICE-001-STOP-REDIRECT#V-PREVIEW-001 | FAIL / blocking |
| V-REFLECT-001 | Slice1 复盘架构迁移、真实 preview 和 A1—A3 | architecture / reflection | Slice1 exact Result、A1—A5、owned Cases、Findings、用户新 decision receipt | A1—A3 exact Verdict；A4/A5 early signal；完整决策 CONTINUE/REDIRECT/REJECT | ITER-010-RESULT-SLICE-001-STOP-REDIRECT#V-REFLECT-001 | PASS / blocking |
| V-GENERAL-002 | 同一协议跨第二工程、不同命名/结构/来源仍不依赖特判 | product / generalization | 第二真实工程、改述、不同目录/框架、source/doc/config/test mixes | 问题层级正确；无 project/question/keyword/symbol/class/method/fixture/oracle branch | not-executed | NOT-RUN / blocking |
| V-RERETRIEVE-002 | 独立补证调查在复杂 gap、冲突、重复和 no-progress 上机械夯实 | application / contract | omission、unsupported inference、citation gap、specific/duplicate/conflicting gap、持久恢复、no-progress cases | 新上下文读 gap+Package/Ledger 并多步结果驱动；不回初始调查；同包 rewrite/新包严格区分；去重恢复正确；不可修复关闭 | not-executed | NOT-RUN / blocking |
| V-ASYNC-002 | 知识沉淀不阻塞或改写当前问答 | application / knowledge | approved Package/Answer、async proposal success/reject/failure | Delivery 独立完成；异步路径重新走 Update/Admission/Publication；任何结果不追认/撤销原答案 | not-executed | NOT-RUN / blocking |
| V-HARDEN-002 | Investigation/Verification Investigation、持久 Ledger/Package、coverage/conflict/dedup 和安全熔断闭合 | application / reliability | recovery/truncation/pagination/conflict/oversize/cycle/no-progress/drift/stale package；revision/call/ops/bytes/wall-time/no-progress fuses | 无漏页、越权、无界循环、历史回写、旧包审批或伪完整；无永久一轮补证 cap；answerable 超限 FAIL，boundary 准确 limitation 或 fail closed | not-executed | NOT-RUN / blocking |
| V-SEC-002 | 第二段保持 Source/role/Provider/Secret/loopback 与 no-retry 隔离 | security / integration | 合法/非法 end-to-end probes、Gateway disclosure/transport audit | 合法路径完成；非法全部失败关闭；模型 direct source/FS/Shell/network=0，write/update/fallback/retry/secret exposure=0 | not-executed | NOT-RUN / blocking |
| V-XD-002 | 第二工程同一答案组合 accepted Snapshot 与本轮多来源 Evidence | product / integration | accepted declaration/`CALLS` + new doc/config/test/source evidence、无符号题 | 同一 answer/limitation 和 Citation 完成真实组合 | not-executed | NOT-RUN / blocking |
| V-WEB-002 | Slice2 从同一真实 Web 执行 V-XD-002 | product / browser | product-owned loopback Web、第二工程、exact qualification/run grant | answerable/boundary 用户可见；Citation 可核对；无平行入口 | not-executed | NOT-RUN / blocking |
| V-CANARY-002 | Slice2 通过独立第二工程 5 answerable + 2 boundary canary | product / independent-hidden | Slice2 code freeze 后用户披露 exact project/suite；burn rule | 5/5 supported、2/2 boundary、重大错误 0、无特判；披露后产品变化=0 | not-executed | NOT-RUN / blocking |
| V-NEG-EARLY-002 | bounded absence 与 coverage limitation 在第二工程保持区分 | product / early falsification | canary 两类 boundary、不同命名/入口/同义改述 | 三层完整才 absence；否则具体 limitation；无关证据 FAIL | not-executed | NOT-RUN / blocking |
| V-COMP-EARLY-002 | 正式验收前用三臂同题消融判断完整 World Model Cognition 的独立价值 | product / comparison | 新用户收据冻结 protocol；完整 Cognition、locator-only/empty 同链、成熟 Agent；same revision/model/questions/budget/cache/rubric；Agent first sealed | 完整认知与成熟 Agent 零重大错误/boundary 正确且完整认知逐结论不退步；再相对 locator control 达预提交质量或 non-locator cost 增益；计建模成本/复用周期 | not-executed | NOT-RUN / blocking |
| V-DIAG-002 | 对同一问题逐层定位首次偏差 | architecture / diagnostic | Source observation、World Model Cognition、Question Understanding、Investigation、Broker/Worker、Ledger/Package、Draft、Review、Web exact refs | 每层独立 verdict；首次偏差决定分类；不从最终答案猜根因 | not-executed | NOT-RUN / blocking |
| V-REGRESSION-002 | accepted scope、strict WORLD_MODEL、DIRECT 与 Preview 主线无退步 | regression / product | ITER-003—006 accepted oracles、Slice1 Result、current full suite | accepted behavior与三模式隔离保持；无新增 fallback/入口分叉 | not-executed | NOT-RUN / blocking |
| V-REFLECT-002 | Slice2 复盘跨工程、合同、安全、Agent/value 与 A1—A4 | architecture / reflection | Slice1/2 Results、A1—A5、Findings、用户新 decision receipt | A1—A4 exact Verdict；A5 early verdict；CONTINUE/REDIRECT/REJECT | not-executed | NOT-RUN / blocking |
| V-HIDDEN-003 | 最终两个未见工程 10 answerable + 2 boundary 验证泛化 | product / independent-hidden | final code freeze 后用户披露 exact projects/suite；至少 8 no-symbol、每工程至少 3 | answerable 10/10、boundary 2/2、重大错误 0、披露后产品变化=0 | not-executed | NOT-RUN / blocking |
| V-COMP-001 | 最终三臂消融证明 ENGINEERING_QA 质量与完整 Cognition 增益 | product / comparison | final same revision/model/questions/budget/cache/rubric；完整 Cognition、locator-only/empty 同链、成熟 Agent；frozen ablation protocol | 完整认知与成熟 Agent 先过质量门；完整认知再相对 locator control 达质量或 non-locator cost 增益；建模成本按冻结复用周期摊销；exact report 可重放 | not-executed | NOT-RUN / blocking |
| V-SEC-003 | 最终产品链保持全部授权、安全、role 和 disclosure 边界 | security / product | final hidden/live sessions、source/Gateway/transport/Ledger/package/Citation audit | Source only via Broker/Worker；所有模型 direct source/FS/Shell/network=0；write/update/fallback/secret/hidden retry=0；loopback | not-executed | NOT-RUN / blocking |
| V-XD-003 | 最终问题在同一答案链组合 accepted Snapshot 与多来源 Evidence | product / integration | final hidden no-symbol cross-source question、accepted Result、新 protocol | 同一正式答案和 Citation 支持旧+新能力 | not-executed | NOT-RUN / blocking |
| V-WEB-003 | Slice3 从同一正式 ENGINEERING_QA Web 执行 final suite | product / browser | exact frozen Web、final 10+2、run grant | 页面交付答案/limitation/Citation；console clean；与内部链相同 | not-executed | NOT-RUN / blocking |
| V-ADHOC-001 | 用户从正式 Web 提出两条现场问题 | product / browser | product freeze 后现场题；至少一条 no-symbol 且跨域 | answerable supported；真实 boundary 正确；Citation 可核对；无 fallback | not-executed | NOT-RUN / blocking |
| V-REGRESSION-003 | 最终候选保持 accepted scope与 Slice1/2 结果 | regression / product | prior oracles、两个 Slice Results、full suite | 无新增失败、能力降级、source leak 或三模式分叉 | not-executed | NOT-RUN / blocking |
| V-010 | 本机验证和 Acceptance 不产生 Production Activation | activation | exact final Iteration Result | NOT_EXECUTED | not-executed | NOT-RUN / blocking |
| V-REFLECT-003 | 最终复盘 A1—A5 并由用户裁决 | architecture / reflection | 三个 exact Slice Results、10+2、现场题、Agent/value、安全、Findings | A1—A5 exact Verdict；只有全部 SUPPORTED 与用户新 ACCEPT 才能申请 Acceptance | not-executed | NOT-RUN / blocking |

## Freeze and scoring rules

- Slice1 先执行 V-WEB-000 一题最小真实纵切，再执行一个真实工程 4 条不同覆盖维度问题和至少一条现场题；至少 3 supported、至少 2 个
  非实现维度。exact revision、只读、不可信 Source、Citation、独立 Review 在微检查点不可延后；持久恢复、复杂冲突/去重和完整异常矩阵
  在 `CONTINUE` 后进入 Slice2。
- Slice2 early canary 与最终 10+2 互不复用，在所属 Slice code freeze 后由用户披露；披露后任何产品/Prompt/schema/route/disclosure 改动
  烧毁输入并保留失败 Result。
- 最终 10 条 answerable 是 supported 分母，Gap 不计 PASS；2 条 boundary 单独要求 2/2。
- 新三臂消融当前 `proposed / not authorized`；旧 `6ca47f7d…` 只保留成熟 Agent/rubric/cache/source-bytes 历史输入，不能冻结新增 Arm、
  protocol、digest 或阈值。Slice2 前须新用户收据。执行时三臂同 revision/model/questions、模型与来源 budget、cache policy/state、rubric/
  evaluator；完整认知与成熟 Agent 先过质量 Gate，locator control 失败不能降低完整认知门。增益再按预提交质量或 normalized non-locator
  investigation cost 判定，并单列 World Model build/update/storage/Provider 成本及冻结复用周期。
- Slice1 每题最多一次独立 Verification Investigation 只服务快速 preview。Slice2/3 禁止永久固定一轮，以预密封 package revision、model
  call、Broker operations、source bytes、wall-time、no-progress 熔断控制；answerable 因熔断未答计 FAIL。
- 调用次数和成本不构成质量裁剪目标；高安全上限触发失败关闭，不能删除 checklist、Evidence、Citation 或独立 Review。
- 每个 `V-REFLECT` PASS 只表示复盘完整。Slice1/2 需要新的 `CONTINUE` 才能授权下一段；最终需要新的 `ACCEPT` 才能接受迭代。
- Product Result 必须聚合三个唯一 Slice Result；测试数量、模型调用成功、旧 Web result 或旧资格不能替代。
