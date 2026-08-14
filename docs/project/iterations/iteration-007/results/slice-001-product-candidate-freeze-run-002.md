---
id: ITER-007-RESULT-SLICE-001-PRODUCT-CANDIDATE-FREEZE-RUN-002
kind: iteration-result
status: candidate-frozen-live-failed-preserved
authority: execution-evidence
owners: [engineering, quality, security, product]
depends_on: [ITER-007-RESULT-SLICE-001-LIVE-RUN-001-FAILURE, FINDING-007-006, ITER-007-RESULT-JAVA-SOURCE-SEMANTICS-CAPABILITY-RUN-003]
code: [src/software_world_model, validation/structure_world_model_iteration_007/slice1_freeze.py, validation/structure_world_model_iteration_007/slice1_live_authorize.py, validation/structure_world_model_iteration_007/slice1_live_evaluator.py]
tests: [tests/test_iteration_007_slice1_freeze.py, tests/test_world_model_browser.py, tests/test_world_model_http.py, tests/test_world_model_evaluation_grant.py, tests/test_world_model_gateway_authorization.py, tests/test_world_model_answer_strategy.py, tests/test_java_source_semantics.py, tests]
iteration: ITER-007
---

# ITER-007 SLICE-001 Product Candidate Freeze run-002

## Decision

`FINDING-007-006` 修复后的替代候选已冻结。runtime exact `-I -S -B` Answer entrypoint import PASS，且
`tree_sitter`/`tree_sitter_java` 均未加载；focused **66/66**、candidate Answer package **24/24**、full regression
**911/911**、documentation check 和 unauthorized-prelisten Gate 全部 PASS。冻结期间无外部模型分派。

run-001 freeze、live grant 和四个失败 terminal 保持原样；run-002 不覆盖旧证据，也不能把旧问题作为本次冻结前未知的验收问题。

## Exact product identity

- freeze report document digest：
  `sha256:f47fe21bdd0b56be39434dd973ef9adb5364bedf0b54f73511235b931f418cbb`；
- freeze report raw SHA-256：
  `f4b7417ff8f54baffc0ac4029d7fc0bac368e8cd76e933bf113dbbb6a1b15f35`；
- candidate stage manifest digest：
  `sha256:9ae036801af29245b96c5cacece50d3fb54427422384915cf9e95127235e1337`；
- frozen producer commit/tree：
  `82bf20a890907c55cea29e3e3415fa413cfe9719` /
  `c4c1d9c8b35a9eedd170b629b4aee68b0b44f07d`；
- producer source manifest digest：
  `sha256:110c4b590fee7e506a832b576e2e5c8452d7eeb354aab4c39b9b8160c9f5fe0b`；
- launcher manifest digest：
  `sha256:c14da7172a6dd985de399ae160ad107b088f8f6cbe39a7db83b6bbdc1f06fe1d`。

冻结后 `src/`、role package、launcher、policy、Prompt、evaluator 或 authorization helper 的任何改变都使本 freeze 失配。

## Qualification and deterministic gates

- capability qualification digest 保持 run-003 已通过的
  `sha256:f7466141339ba78de31393126fb33e1ba903456fb7e340530e1954e0213d1a41`；本修复不改变 Strategy、Prompt、vocabulary、
  egress policy、suite、Oracle 或 capability evaluator；
- deterministic qualification document digest：
  `sha256:7aaaa3b3ae940f6dd5565f53ed3218ea1093c0457d78a33c222fb842f70db999`；
- deterministic product probe digest：
  `sha256:8bf4ba2e79fe4334d6057c05038b82c67c0ea5116e565f1ea9d1101f305bc654`；
- formal Gateway freeze digest：
  `sha256:ebec1cb7b52ea38415ac90ef9c56ba23d1de0bc2b4f4747f19200000c44893af`；
- exact package import probe 用真实 frozen Answer root 执行，return code 0，parser module count `0/0`；
- 未授权 grant 在 session/socket/listener 前失败，没有 Provider call。

## Post-freeze live boundary

user-held live suite digest 为
`sha256:da1ed2bc58f02196c9d362f216c5a455bb994ea21a76b94c633d1029fde1a525`，冻结时 questions/cases 仍为空。pending evaluation
grant digest 为 `sha256:333a483d44fe0591835020df5db6c36e3e89921539525f36f34c4538b46a2737`，
`live_dispatch_authorized=false`。

下一次正式 Web 启动需要一条发生在本 freeze 之后、绑定 run-002 的用户 live 授权，并写入全新的 grant/session 路径。用户提交问题
后仍必须严格 Plan→Draft→Review 三次调用、无 retry，并由独立 evaluator 与用户 verdict 判定。Production Activation 与 Git
stage/commit/push 均未执行。

## Subsequent startup evidence

用户 post-freeze 消息 `codex-user-message:sha256:66921b7d7f71a6f865cabc6c802964b77eda3b6189028de80f0711634be64e0b`
已生成 authorized grant
`sha256:0671865671bd482b2a09bf4b58b909c2d1c7f7c113739ae4f2ba88530a20de5a`。正式 frozen launcher 启动 PASS，startup
receipt digest 为 `sha256:08de90c5cb4c9cc762046368e22436639cd28f0f4add7a2a79ee39b2cd585d79`，页面显示
`READY · 82bf20a89` 和 `Plan → Draft → Review · 3 次模型调用`，browser console error/warn 为 0。页面加载期间无模型调用。
随后用户发起两个独立请求：第一个在单次 Plan 后以 `DomainError` 失败；第二个完成严格三调用且 Answer/Gateway 均 PASS，但被
遗留的 `unix_connect=1` role audit 在 `ROLE_POSTCONDITION` 误判。exact 证据见
[Live run-002 Failure](slice-001-live-run-002-failure.md) 与 `FINDING-007-007`；本 freeze、grant 和 session 保留且不再用于修复后
验证。
