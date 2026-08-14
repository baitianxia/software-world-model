---
id: ITER-007-RESULT-SLICE-001-PRODUCT-CANDIDATE-FREEZE-RUN-004
kind: iteration-result
status: candidate-frozen-awaiting-user-live-authorization
authority: execution-evidence
owners: [engineering, quality, security, product]
depends_on: [ITER-007-RESULT-SLICE-001-LIVE-RUN-002-FAILURE, ITER-007-RESULT-SLICE-001-PRODUCT-CANDIDATE-FREEZE-RUN-003-FAILURE, FINDING-007-007, ITER-007-RESULT-JAVA-SOURCE-SEMANTICS-CAPABILITY-RUN-003]
code: [src/software_world_model, validation/structure_world_model_iteration_007/slice1_freeze.py, validation/structure_world_model_iteration_007/slice1_live_authorize.py, validation/structure_world_model_iteration_007/slice1_live_evaluator.py]
tests: [tests/test_world_model_evaluation_grant.py, tests/test_iteration_007_slice1_freeze.py, tests/test_world_model_gateway_authorization.py, tests/test_java_source_semantics.py, tests/test_world_model_answer_strategy.py, tests]
iteration: ITER-007
---

# ITER-007 SLICE-001 Product Candidate Freeze run-004

## Decision

`FINDING-007-007` 修复后的替代候选已成功冻结。Answer role audit 现在从同一 frozen dispatch 输入取得 exact 连接期望；
三调用 Profile 要求 `unix_connect=3`，旧单调用 Profile 仍要求 1，Gateway/Projector 要求 0。

focused **67/67**、candidate Answer package **25/25**、full regression **912/912**、documentation check 和
unauthorized-prelisten Gate 全部 PASS。run-003 的 workspace sandbox AF_UNIX 失败原地保留；run-004 在允许本机 listener 的执行面
重跑未修改的完整冻结 helper。冻结期间没有外部模型分派。

## Exact product identity

- freeze report document/raw digest：
  `sha256:07f3431e919706f3c9a6fbe601906d7dd2c5532b53032b3fbefb5702cef725fe` /
  `496cddba443ae75b11a5003287dfd2d753a438bd34e50071bdc27e15f4c33f8a`；
- candidate stage manifest digest：
  `sha256:1b83463f83255767415ec94be78cb972d6c2820431157e61ca5668515a6635eb`；
- frozen producer commit/tree：
  `93a45888b9028bd793752839d54078ceae6eb219` /
  `260bc4b334ded3cd7bc24fcf0ae84842b6f6e33e`；
- producer source manifest digest：
  `sha256:901c545266a83d9dbbe7a401bedff05247e8e0f21ade7a94c0fcb5dff737f6be`；
- launcher manifest digest：
  `sha256:aec16688a531279aa042945b68534832bbbbf1f35ee9e7d88db0465475545ebb`。

冻结后 `src/`、role package、launcher、policy、Prompt、evaluator 或 authorization helper 的任何改变都会使本 freeze 失配。

## Qualification and deterministic gates

- capability qualification 继续使用已接受 run-003 的
  `sha256:f7466141339ba78de31393126fb33e1ba903456fb7e340530e1954e0213d1a41`；本修复不改变 Strategy、Prompt、vocabulary、
  egress policy、suite、Oracle 或 capability evaluator；
- deterministic qualification document digest：
  `sha256:41eacb1edba5e55344aecffb1788aac432772bf6b4e237f0cb85b33da0d3f859`；
- deterministic product probe digest：
  `sha256:7ac5f44a1dd24f789465d535bde76ff2e9a1bca1d44e6e757f358e4dbced1a48`；
- formal Gateway freeze digest：
  `sha256:ebec1cb7b52ea38415ac90ef9c56ba23d1de0bc2b4f4747f19200000c44893af`；
- focused 67、candidate package 25、full 912、docs 和 unauthorized-prelisten 全部 PASS；
- 未授权 grant 在 session/socket/listener 前失败，没有 Provider call；Production Activation 与仓库 Git stage/commit/push
  均未执行。

## Post-freeze live boundary

user-held live suite digest 为
`sha256:7fa49e7d9c4aa4fd3d97be3089a14e9f5c0407eaa05f2c77f187a06cb4d2cea6`，冻结时 questions/cases 为空。pending evaluation grant
digest 为 `sha256:40d32bbd39f03f947eee38ffe4a8948a6e0c3631fbb7fed17258ac97b6e8e6e6`，
`live_dispatch_authorized=false`。

正式 Web 启动需要一条发生在本 run-004 freeze 之后、明确绑定 run-004 的用户 live 授权，并写入全新 grant/session。run-002 的授权
已经消费且绑定旧冻结，不能复用；run-002 已披露问题也不能冒充 run-004 冻结前未知的 canary。新请求仍严格
Plan→Draft→Review 三次模型调用、无 retry，并由正式 terminal、Citation、浏览器和用户 verdict 判定。

## Subsequent startup and request evidence

用户 post-freeze 消息 `codex-user-message:sha256:739db790b45938601e16258a47a5c1f616751e6e827935b163986a76202aee6e`
已生成 authorized grant
`sha256:b59997736d703c960a88e74e6eae5493c88e928fc9cb902473a1b89db91ea57f`。正式 frozen launcher `READY`，startup receipt digest
`sha256:2623f83ea77ccc20251f557fad6aee9b12392dbeb639b5c6edab522f65fc19bd`。

首个问题 terminal `SUCCESS`，三次模型调用、0 retry、Answer/Gateway/Citation 与 browser console 技术回归 PASS，关闭
`FINDING-007-007` 的现场复现；产品答案因多个相关方法未唯一消歧为 `LIMITATION`，不计 supported。exact 证据见
[Live run-004](slice-001-live-run-004.md) 与 `FINDING-007-008`。
