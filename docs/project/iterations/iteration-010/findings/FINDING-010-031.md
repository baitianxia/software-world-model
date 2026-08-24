---
id: FINDING-010-031
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [security, interface, quality]
depends_on: [ITER-010-SLICE-001, FINDING-010-029, SYS-QUALITY-SECURITY, SYS-OPS-LOCAL-BROWSER]
code: [src/software_world_model/interface/engineering_qa_browser.py]
tests: [tests/test_engineering_qa_browser.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: require-exact-same-origin-json-before-session-question-receipt
target: SYS-QUALITY-SECURITY
---

# FINDING-010-031：loopback 不等于用户主动提交

## Observation

持续 Alpha 把浏览器提交动作作为 exact question disclosure acknowledgement，但只校验 `REMOTE_ADDR` 与 `Host` 仍不足以证明请求来自当前
页面。恶意网页可以向 `http://127.0.0.1:8765` 发送不触发 CORS preflight 的 `text/plain` JSON；即使它读不到响应，也可能伪造
`disclosure_acknowledged=true` 并消费本机 Session 的 Provider 调用额度。

## Evidence and root cause

- WSGI 路由此前在 JSON 解码前不检查 `Origin` 或 media type；
- `fetch(..., {Content-Type: text/plain})` 属于浏览器 simple request，CORS 只阻止读取响应，不阻止 POST 副作用；
- exact loopback `Host` 能阻止 DNS rebinding 的非 loopback Host，却不能区分同机页面与跨站发起者；
- 根因是把网络位置约束误当成用户提交来源证明，范围影响所有会产生模型 dispatch 的 session question。

## Decision and disposition

问题 POST 必须在 JSON 读取、receipt 签发、transport 构造和 credential resolution 前同时满足：`Origin` 精确等于当前
`http://<validated-loopback-host>`、`Content-Type` 精确为 `application/json`，且浏览器若发送 `Sec-Fetch-Site` 则只能是
`same-origin`。缺失或不匹配统一 `CONTROL_STATE_DENIED`；GET 页面、health 与 Result-scoped Citation 保持原 loopback 边界。

该约束写回 Engineering QA Contract、Security 与 Local Browser Operations；它不把 loopback Alpha 宣称为有账号认证的非本机产品。

## Verification

浏览器测试分别发送 cross-origin/cross-site JSON 与 same-origin `text/plain` 请求，二者均在 session execution factory 调用前返回
`403`；正常 same-origin `application/json` 的连续提问、失败隔离和 Citation 回归继续通过。
