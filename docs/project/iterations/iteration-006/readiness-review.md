---
id: ITER-006-READINESS
kind: iteration-readiness
status: accepted
authority: project-authorization
owners: [project, architecture, quality]
depends_on: [ITER-006-PROPOSAL, ITER-006-VERIFICATION, ITER-005-RESULT-ACCEPTANCE]
code: []
tests: []
iteration: ITER-006
authorized_by: user
authorized_at: 2026-08-12T09:18:11+08:00
---

# Iteration 006 Readiness Review

## Reviewed exact inputs

基线为 clean commit/tree `bc0ecefb806c946f9c2b5938470be18ec780115b` /
`78064f71632ebb6bd58891f8af76a67f64f35be5`。已核对 ITER-005 Acceptance、Semantic View Candidate、Schema Core、
Snapshot Publication、Knowledge Update/Use、现有 Structure View、World Model Answering、安全与本机浏览器契约。

## Outcome, scope and non-goals

Outcome 是在新 Scope 初始采用 `JAVA_STATIC_CALL_GRAPH@1`，把受支持 Java 源码的类型、方法声明和可唯一解析的静态直接调用
形成正式 Snapshot，并通过既有本机产品入口 Source-off 问答。静态关系不等于运行时行为；已有 Maven Scope、其他语言、
自动刷新、外部披露、认证、网络部署和 Production Activation 不在范围。

## System contracts and unresolved decisions

现有 Schema Registry、Admission/Publisher、Read Session/Bundle/Catalog、World Model Answering 与 Citation 隔离边界可复用。
本轮必须先增加并接受 `SYS-CONTRACT-KNOWLEDGE-JAVA-STATIC-CALL-MODEL` 和
`SYS-CONTRACT-APPLICATION-BEHAVIOR-VIEW`，并确保既有 Maven frozen sets 不从 enum 全集隐式扩张。

实现前允许在 Slice 内闭合的决定只有 Profile 的更窄语法细节与错误码；若证据要求变量类型推断、classpath、字节码、已有
Scope 的 Schema 切换或新的权威事务边界，必须登记 Finding 并暂停相关扩张，不得自行纳入。

## Slice, dependency and risk closure

SLICE-001 是单一纵向 Slice：先冻结 fixture/Oracle，再沿 Source → Candidate → independent verifier → Admission → Publication →
Bundle/Catalog → Behavior View → Product Web 顺序推进。无模型确定性实现可以立即编码。真实 Provider 调用不属于当前授权，
必须等 implementation 后 exact freeze 和单独披露许可。

## Verification readiness

Matrix 已区分 contract、update、isolation、product/live、browser 与 activation。V-001—V-007 可在本机无外部披露运行；V-008
明确被用户授权阻断；V-009 的确定性浏览器路径可实现和测试，真实模型人工验收随 V-008 授权后执行。原始运行证据只保存在
`var/iteration-006`，Git 只记录 Result ID、digest、路径和限制。

## Authorization decision

Readiness 为 **ACCEPTED**。用户“开发 ITER-006”的消息授权 `ITER-006-SLICE-001` 的文档、代码和本机无外部披露验证；不
授权把任何问题或源码发送给 Provider，不授权接受 Iteration，也不授权 Production Activation。

## Subsequent live disclosure authorization

实现和 run-003 exact suite 冻结后，用户回复“同意授权”。外部分派安全审查认定该消息没有明确点名火山引擎 Ark、OpenAI
Codex 与 exact Java source closure payload，因而拒绝执行；Provider calls 为 0。该消息不能作为可执行 disclosure grant，仍需
用户明确授权；它也不接受 Iteration，不授权 Production Activation、提交或推送。

## Subsequent exact run-003 outcome

用户随后明确点名 Ark、OpenAI Codex、suite `sha256:32de10fb…`、exact Java source closure 和 World Model no-payload
Structure，授权通过并按 freeze 执行。Direct/Codex 各 6/6；World Model 4/6，两个 generic planning case 因
`declared_method_inventory` 没有新的 exact capability qualification 而在 Provider dispatch 前拒绝。该结果不改变 Readiness
对开发范围的授权，但阻断 Acceptance；下一 live run 必须重新资格化、freeze，并取得绑定新 suite 的授权。

## Subsequent capability qualification and product re-freeze

用户随后精确授权 capability freeze `sha256:7a3948a3…` / suite `sha256:93be2f87…` 的八次 Ark synthetic closed evaluation；
run-002 已 8/8 PASS、无 retry，并形成 `PASS_VALID` qualification。该授权不包含产品问题、源码、Evidence payload 或 Codex，且
已经消费。新的 run-007 product candidate/suite `sha256:66192cdf…` 已在零 Provider 下完成 55/55、18/18、835/835 与两道
fail-closed Gate。Readiness 仍不授权该三路 comparison；必须另取绑定新 suite、Ark/Codex 目的地和三路 payload boundary 的
独立授权，最终 Acceptance 也仍由用户单独裁决。

## Subsequent exact run-007 outcome

用户随后提交了上述独立三路授权，run-007 按序执行且无 retry。Direct/Codex 各 6/6；World Model 六次内部 Ark call 均完成，
但 Java baseline 自带 seal 与授权 wrapper 外层 seal 的同名键冲突使六题都在 `ROLE_POSTCONDITION` 失败。comparison report 为
FAIL，授权已消费。该结果不改变 Readiness 的开发授权范围；本地修复必须重新 freeze 并另取授权，且仍不能自行 Acceptance。

## Subsequent run-008 remediation freeze

wrapper 最小修复随后在零 Provider 的 run-008 重新冻结，完成 56/56 focused、18/18 candidate Answer package、836/836 full
regression、docs 与两道 fail-closed Gate；外部调用为 0。新 freeze report `sha256:a036921c…`、suite `sha256:0793db73…` 与
disclosure set `sha256:1ffb8aa6…` 尚未获得独立三路授权。run-003、capability 与 run-007 授权均不可复用；Readiness 仍不授权
外部分派、Production Activation、提交、推送或最终 Acceptance。

## Subsequent exact run-008 outcome

用户随后精确绑定 run-008 freeze report、suite、disclosure set 与三路 payload boundary 作出独立授权。Direct、Codex 与 World
Model 各 6/6 SUCCESS，controller retry 0；independent comparison `sha256:857085c4…` PASS、blocker 0、无筛选或插值。
该授权已消费，旧 grant 均未复用。技术 Gate 已闭合，但 Readiness 不拥有最终 Acceptance，也仍不授权 Production Activation、
提交或推送。

## Subsequent final Acceptance

用户于 `2026-08-13T11:45:33+08:00` 接受 exact run-008 已证明的窄范围，最终裁决为 `ITER-006-RESULT-ACCEPTANCE`。该用户裁决
满足最终 Acceptance Gate，但不追溯扩张 Readiness：当前页面仍只是 Java static-call 评测入口，不是正式最终 Web Chat；
Production Activation、提交和推送仍未授权、未执行。
