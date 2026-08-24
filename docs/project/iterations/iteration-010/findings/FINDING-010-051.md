---
id: FINDING-010-051
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, ai-infrastructure, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-049, FINDING-010-050]
code: [src/software_world_model/ai_infrastructure/engineering_question_strategy.py]
tests: [tests/test_engineering_question_strategy.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: canonicalize-nonsemantic-followup-claim-role-order-before-domain-validation
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-051：合法 Answer claims 的展示角色乱序在 Domain 前缺少确定性归一化

## Observation and evidence

`FINDING-010-049/050` 的处置形成 clean candidate
`d12223f225d4cd57335a25a6d2eff4af5ee6ee7b` / tree
`5f7011668f5d76343a5b7b1ecb3c47eb739472f5`。fresh DeepSeek Conformance run-017 以 2/2 request PASS，Result
`sha256:dccfffa4991cd2f8df7f586f3e94e825f5859bcb0e96983fd032a6274992da12`，actual model
`deepseek-v4-pro`、retry 0。随后在固定 mall revision
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7` 的同一持续 Alpha 中依次提交三题：

- 原现场题“登录流程是怎样的？”只声明并完整读取 4 个 mandatory paths，1 次 Understanding + 7 次 Investigation 后成功 FINISH 并进入
  Answer；Provider 返回的 direct answer、9 个 follow-up claims、checklist/observation/evidence links 均完整，但 follow-up role 顺序为
  `USER_VISIBLE_PROCESS → IMPACT_OR_SIDE_EFFECT → USER_VISIBLE_PROCESS → IMPACT_OR_SIDE_EFFECT`，因而在 Review 前失败关闭；
- 本地构建/安全接入/resources unknown 混合题以 14 次 dispatch 得到 `APPROVED` reviewed Result。答案确认 POM 依赖、登录/JWT/filter/
  authorization 接入，并把未授权 resources 中的数据库连接、JWT 密钥和端口保留为未知；
- 401/403 排障题以 1 次 Understanding + 10 次 Investigation 完整读取 token filter、security configuration、dynamic manager 和 metadata
  source 后进入 Answer。Provider 正确区分三个检查面，但 follow-up role 顺序为
  `USER_VISIBLE_PROCESS → IMPACT_OR_SIDE_EFFECT → USER_VISIBLE_PROCESS`，再次在 Review 前以相同 Domain contract error 失败关闭。

terminal receipt
`sha256:e901faf295850f7aff1c94b36ab7f02cdda1c7d36f611821a9757445f077f69f` 记录 3 个 accepted question、
35 次 dispatch（9/14/12）、retry 0、Provider switch 0、Production Activation `NOT_EXECUTED`；全部 transport audit 为 verified TLS、无
post-dispatch outcome unknown。session、launch、Gateway SQLite 和 terminal receipt 均为 `0600`。同一 listener 上的 22,000 字符输入在本地
预检失败关闭，Gateway call root 在提交前后均为 35，证明没有外发；服务随后优雅停止。

## Root cause

Answer closed schema 能限制 `direct_answer` 唯一且 follow-up claims 不得使用 `DIRECT_ANSWER`，也能限制每个 claim 的合法 kind/content-role
组合，但可变长度 JSON array 不能用当前 closed variant 表达跨 item 的全局角色单调顺序。Prompt 与角色输入已明确要求
`USER_VISIBLE_PROCESS → IMPACT_OR_SIDE_EFFECT → IMPLEMENTATION_EVIDENCE → LIMITATION`，Provider 仍可能在形成 impact 后补充一个合法
process claim。可信 adapter 原样构造 Domain Proposal，使纯展示顺序偏差与 checklist、observation、evidence、kind 或正文语义错误使用同一
fail-closed 结果。两道异质题的独立复现证明该问题是系统性的，不是登录题特判。

## Decision and disposition

- Gateway 继续不可变保存 raw Provider output/digest；可信 Answer adapter 只对 follow-up claims 按既有受控 content-role 顺序做稳定排序，
  同一角色内保持 Provider 原顺序；唯一 `direct_answer` 仍固定首位；
- 归一化不得改写 claim ID、kind、content role、checklist links、material-observation links、文本或 evidence links。非法枚举、kind/role
  混类、重复/漏 coverage、证据分区、部分 observation overlap 和其余 Domain invariant 仍失败关闭；Application 对直接构造的乱序
  Proposal 也继续拒绝；
- Strategy identity 升级为 `@11`。current Engineering QA System Contract、Slice/Manifest/Verification 与确定性回归在同一变更中同步；
  回归证明跨 role 稳定排序且同 role 原顺序不变。新的 clean candidate、fresh Conformance 和三题 live 必须重新执行，本次 1 PASS + 2
  FAIL 只作为诊断证据，不能追认为体验或答案质量 PASS。
