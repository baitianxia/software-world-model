---
id: FINDING-002-002
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, architecture]
depends_on: [SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL]
code: [src/software_world_model/application_services/response_control.py, src/software_world_model/interface/http_api.py]
tests: [tests/test_response_control.py, tests/test_browser_chat_interface.py]
iteration: ITER-002
classification: system-contract
disposition: updated-current-response-control-contract
target: SYS-CONTRACT-APPLICATION-RESPONSE-CONTROL
---

# FINDING-002-002：已满足问题仍可能存在应用限制

## Observation

一个 Need 可以有足够的正式事实而被判定为 satisfied，同时仍有与应用结果相关、必须向用户披露的限制。旧 Claim 类型只能把文本塞入正式事实或 Gap，二者都不准确。

## Evidence / reproduction

`ResponseControlService.prepare` 需要在正式事实之外投影 `SufficiencyItem.limitations`；若把限制当成知识 Gap，会错误地把已满足 Need 改写为未满足，若当成正式知识则缺少正式引用。

## Impact

该差异影响 Response Control 的 Claim 权威分类和浏览器展示，属于跨模块契约语义。

## Classification rationale

它改变用户可见 Claim 必须绑定哪类权威结果，因此归类为 system-contract。

## Decision and disposition

在 Response Control 现行契约中明确：已满足 Need 的应用限制是独立 Claim，绑定同一 Sufficiency Proof，但不是正式知识或 Knowledge Gap。代码和测试按该规则实现。

## Verification after disposition

`tests/test_response_control.py` 验证构造、校验和篡改拒绝；`tests/test_browser_chat_interface.py` 验证限制与事实按 Need 展示。
