---
id: FINDING-007-008
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, product, quality]
depends_on: [ITER-007-SLICE-001, ITER-007-RESULT-SLICE-001-PRODUCT-CANDIDATE-FREEZE-RUN-004, ITER-007-VERIFICATION]
code: [src/software_world_model/interface/world_model_product.py, src/software_world_model/application_services/world_model_answering.py, src/software_world_model/application_services/structure_view.py]
tests: [tests/test_world_model_product.py, tests/test_world_model_answer_strategy.py, tests/test_java_source_semantics.py]
iteration: ITER-007
classification: verification
disposition: preserve-run-004-ambiguity-as-non-passing-live-product-evidence
target: ITER-007-VERIFICATION
---

# FINDING-007-008：无符号登录流程问题未从多个相关方法中形成唯一实现链

## Observation

run-004 修复候选启动后，正式 Web 收到“登录流程是怎样的？”。严格 Plan→Draft→Review 三调用、Answer/Gateway、terminal、
Citation projection 和浏览器交付全部成功；但产品答案是 `LIMITATION`，不是登录流程实现答案。

Plan 的 `implementation_candidates` 在 `LoginService` 中找到 `authenticate(boolean)`、`issueSession()` 和 `recordFailure()` 三个
相关方法。当前 selector 只允许唯一方法参数进入 `method_implementation`，因此 resolution 为
`ENTITY_RESOLUTION_NOT_UNIQUE`，第二个 Query step 被阻断。回答正确披露不能确认分支、return/throw 和调用顺序，没有编造实现。

## Evidence and classification

- browser result raw digest：
  `sha256:1804a21ab75a33b22efd909ba05ae2b5db18c9dada1e4c04242ce57693a22886`；
- page digest：
  `sha256:3f8a97e5c7446c677cac1a3bb8791321cdcbbf6a7e7fd2c5bba72432756b51fd`；
- terminal digest `sha256:8554e1fb4a559e5e0cba3cbd1ab640c485a80ff6209214d0587fb45609620d21`，status `SUCCESS`；
- assessment `sufficient=false`，Need outcome `LIMITATION`，codes 为 `ENTITY_RESOLUTION_NOT_UNIQUE` 与
  `IMPLEMENTATION_ENTITY_RESOLUTION_AMBIGUOUS`；
- Answer/Gateway 各自 PASS，3 Provider calls、3 network operations、0 retries、Source access 0；
- Citation projection 1 个且本机 direct GET 返回 HTTP 200；browser console logs 为空。

这不是 `FINDING-007-007` 的 runtime 回归；原后置条件误判已经关闭。它是 V-004/V-XD-001 的产品验证事实：功能描述确实发现了
相关正式知识，但当前“一次只选唯一方法”的 Query Plan 不能组成跨方法流程答案。

## Decision and disposition

保留 run-004 exact 结果，不能把诚实 Limitation 计为 supported 或跨域 PASS，也不能针对已披露问题加入关键词、方法名或 fixture
分支。`V-WEB-001` 的技术链路可记为 PASS，但产品正确性、`V-XD-001` 与隐藏 canary 仍阻断 SLICE-001 Acceptance。

若继续改产品，必须从通用 contract 出发评估“候选集→入口方法/多方法链”的确定性消歧与组合查询，而不是放宽唯一 typed argument
校验；任何产品代码变化都要求新 freeze 和新的 post-freeze 问题，当前问题/result 只保留为失败/限制证据。
