---
id: FINDING-010-009
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [interface, security, quality]
depends_on: [ITER-010-SLICE-001, SYS-QUALITY-SECURITY, SYS-OPS-LOCAL-BROWSER]
code: [src/software_world_model/interface/engineering_qa_browser.py]
tests: [tests/test_engineering_qa_browser.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: reject-duplicate-json-keys-and-short-wsgi-bodies-before-product-routing
target: src/software_world_model/interface/engineering_qa_browser.py
---

# FINDING-010-009：浏览器入口不能接受歧义 JSON 或短读请求体

## Observation

Engineering QA WSGI 入口已限制字段和 request bytes，却使用普通 `json.loads`，相同 key 出现多次时会静默采用最后一个值；同时它按
`CONTENT_LENGTH` 调用 `read()` 后没有验证实际字节数。上游提前结束或测试 stream 短读时，入口可能把并非声明完整的 body 交给产品路由。

## Evidence and root cause

- `{"request_id":"a","request_id":"b","question":"safe"}` 原先解码为一个合法对象，无法证明客户端签名/观察的是哪一项；
- `CONTENT_LENGTH=512`、实际 body 更短时，原实现只要短内容本身是合法 JSON 就会继续；
- 字段 exact-set 检查发生在 JSON 解析之后，不能恢复已经丢失的重复 key 信息；
- 根因是 ingress parser 没有把 wire-level 唯一性和完整读取作为产品请求身份的一部分。

既有 loopback、安全和 closed request schema 已要求歧义输入失败关闭，因此分类为 `local-implementation / systemic`，无需新增协议。

## Decision and disposition

- JSON object 使用 `object_pairs_hook` 拒绝任意层级重复 key；
- 要求存在可读取的 WSGI input stream，并验证返回值是 bytes 且长度与已校验的 `CONTENT_LENGTH` 精确相等；
- UTF-8、JSON root、字段集合或完整读取任一失败统一在产品路由前返回 `INVALID_JSON`；
- 保留原 request-size、loopback remote/Host、字段类型和幂等边界。

## Verification

浏览器测试直接发送重复 `request_id` 与声明长度大于实际 body 的请求，均得到 `400 / INVALID_JSON`；正常问题、Citation、幂等 replay、
额外 authority 字段和非回环拒绝继续通过。
