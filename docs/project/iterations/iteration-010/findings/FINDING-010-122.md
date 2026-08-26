---
id: FINDING-010-122
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [quality]
depends_on: [FINDING-010-118]
code: []
tests: [tests/test_engineering_chat_session_artifact.py]
iteration: ITER-010
classification: local-implementation
scope: individual-case
disposition: bind-artifact-qualification-fixture-validity-to-the-clock-owner-it-exercises
target: tests/test_engineering_chat_session_artifact.py
---

# FINDING-010-122：Artifact preparation 的 qualification fixture 不能随固定测试日期自然过期

## Observation and evidence

相邻回归在 `2026-08-26` 运行时，artifact preparation Case 构造的 qualification 以固定测试时钟 `2026-08-25` 加一天作为
`valid_until`，而生产 Adapter 按真实 UTC wall clock 验证资格。该 fixture 会随日历经过而从 PASS 变成 `QUALIFICATION_INVALID`，与产品
代码或 v4 合同无关。

## Disposition

测试现在按 Adapter 实际拥有的 UTC wall clock 构造未来一天的资格有效期；artifact Session 自身的 authorization/expiry 仍继续使用注入的
固定时钟，产品代码没有变化。相邻组合由此稳定为 84/84 PASS。该处置只修正测试 owner 的时间绑定，不修改资格规则、运行时 clock、
Provider、credential、Source、Browser 或 Production 行为，因此无需更新 System Contract。
