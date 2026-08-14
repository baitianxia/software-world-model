---
id: ITER-007-RESULT-SLICE-001-LIVE-RUN-004
kind: iteration-result
status: failed-preserved
authority: execution-evidence
owners: [engineering, quality, security, product]
depends_on: [ITER-007-RESULT-SLICE-001-PRODUCT-CANDIDATE-FREEZE-RUN-004, FINDING-007-007, FINDING-007-008]
code: [src/software_world_model/interface/world_model_runtime.py, src/software_world_model/interface/world_model_http.py, src/software_world_model/interface/world_model_browser_ui.py]
tests: [tests/test_world_model_evaluation_grant.py, tests/test_world_model_browser.py, tests/test_world_model_http.py]
iteration: ITER-007
---

# ITER-007 SLICE-001 Live run-004

## Decision

`FINDING-007-007` 的正式 Web 技术回归 **PASS**。页面显示 run-004 candidate `READY · 93a45888b`，收到独立问题请求后返回
HTTP 200；terminal `SUCCESS`，Answer/Gateway role 与 summary 均 PASS，Citation 已投影且可打开。原
`ROLE_POSTCONDITION` 误判没有复现。

问题“登录流程是怎样的？”的产品 outcome 为诚实 `LIMITATION`：多个相关方法无法唯一消歧，因此没有给出完整登录流程。该结果
不计为 supported 或 `V-XD-001` PASS。用户最终将产品效果判为 **FAIL**；停止裁决见
`ITER-007-RESULT-SLICE-001-STOP-DECISION`，详细根因见 `FINDING-007-008/009`。

## Authorization and startup

- post-freeze user message digest/ref：
  `sha256:739db790b45938601e16258a47a5c1f616751e6e827935b163986a76202aee6e` /
  `codex-user-message:sha256:739db790b45938601e16258a47a5c1f616751e6e827935b163986a76202aee6e`；
- authorized grant digest：
  `sha256:b59997736d703c960a88e74e6eae5493c88e928fc9cb902473a1b89db91ea57f`；
- startup receipt digest：
  `sha256:2623f83ea77ccc20251f557fad6aee9b12392dbeb639b5c6edab522f65fc19bd`；
- candidate commit/tree：
  `93a45888b9028bd793752839d54078ceae6eb219` /
  `260bc4b334ded3cd7bc24fcf0ae84842b6f6e33e`；
- dispatch policy：`THREE_ORDERED_CALLS_PER_QUESTION_NO_HIDDEN_RETRY`；页面加载期间模型调用为 0。

## Exact request evidence

- request ID：`wm-1cd63604-038f-40ab-bcb7-03f3cffe71b4`；
- browser result raw/page digest：
  `sha256:1804a21ab75a33b22efd909ba05ae2b5db18c9dada1e4c04242ce57693a22886` /
  `sha256:3f8a97e5c7446c677cac1a3bb8791321cdcbbf6a7e7fd2c5bba72432756b51fd`；
- terminal digest：
  `sha256:8554e1fb4a559e5e0cba3cbd1ab640c485a80ff6209214d0587fb45609620d21`；
- Answer/Gateway summary digest：
  `sha256:2e126d6d68dfa5466fbb1e1b439b9070db3fa6bd5a74094f3fae09d305a8c3df` /
  `sha256:42159daa8265b1d150ed4f59f82ce14a6923a62ea9c9778c3538807bdc898d40`；
- model call IDs：`model_call_a39fab17051b47db8f5832929a7cc081`、
  `model_call_d93db0d7abc44aadadc2049890cc62e6`、`model_call_3b7254ea64984168a48fc5dda4b4b297`；
- provider/network calls 3/3、attempt 1、selective retry 0、elapsed 22,858 ms；
- Answer audit `unix_connect=3`，Source/Evidence/authority/product oracle/baseline/git/process/other-role 等禁止项全部 0；
- Citation result `structure_view_result_a9a5c6b9547778ea9bef1fb5df527f12`，projection digest
  `sha256:0c2d5f2593762346c7c17b26ed6db2e066829c35f963d1cf0083f392e109e97c`，direct loopback GET HTTP 200 / 11,172 bytes；
- browser console logs `[]`；Production Activation `NOT_EXECUTED`。

## Product outcome boundary

技术回归证明三调用 role audit 修复、sealed terminal、Citation 和 Web 交付链成立。Need outcome 仍是 `LIMITATION`、assessment
`sufficient=false`，所以不能据此接受 `V-XD-001`、隐藏 canary 或 SLICE-001。用户产品正确性 verdict 已密封为 FAIL，当前服务不再是有效产品候选。
