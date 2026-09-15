---
id: FINDING-010-290
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, quality]
depends_on: [FINDING-010-284]
code: [src/software_world_model/application_services/lightweight_engineering_agent.py]
tests: [tests/test_lightweight_engineering_agent.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: code-and-tests-only
target: src/software_world_model/application_services/lightweight_engineering_agent.py
---

# FINDING-010-290：保留搜索熔断前已授权的 Source READ 候选

真实 loopback 轨迹显示，Source SEARCH 在返回可读候选后可能触发 Broker 搜索
熔断；Application 若把该边界直接当作整个 Source 路径关闭，会丢弃同一快照中
已经由 cognition provenance 授权的 READ 选项。当前修正只在搜索熔断且仍有
未消费候选时保留 Source 路径，继续使用原有 READ 预算和 authority receipt；
不会增加预算、协议字段、Provider 或题面规则。无未消费候选时仍按原契约
fail-closed。现有 lightweight Agent 定向套件 34/34 通过。
