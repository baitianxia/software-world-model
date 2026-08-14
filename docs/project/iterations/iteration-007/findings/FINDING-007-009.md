---
id: FINDING-007-009
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, product, quality]
depends_on: [ITER-007-SLICE-001, ITER-007-RESULT-SLICE-001-LIVE-RUN-004, ITER-007-VERIFICATION]
code: [src/software_world_model/interface/world_model_product.py, src/software_world_model/application_services/world_model_answering.py, src/software_world_model/application_services/structure_view.py]
tests: [tests/test_world_model_answer_strategy.py, tests/test_world_model_answering.py, tests/test_java_source_semantics.py]
iteration: ITER-007
classification: roadmap
disposition: stop-fixed-single-method-answering-and-redesign-capability-path-step-1
target: ROADMAP-CANDIDATE-BOUNDED-WORLD-MODEL-INVESTIGATION
---

# FINDING-007-009：run-004 证伪固定单方法问答协议

## Observation

run-004 正式 Web 共保留三个独立请求：两次“登录流程是怎样的？”和一次“下单流程是怎样的？”。三个请求都严格
完成 Plan→Draft→Review 三次 Provider call，terminal `SUCCESS`、Source access 0，但都只交付 Limitation。

- 登录题找到 `authenticate(boolean)`、`issueSession()` 和 `recordFailure()`；三个方法对流程都有用，但固定
  selector 要求候选数必须为 1，因此在读取实现语义前阻断；
- 下单题的授权工程只有 `LoginService.java`，没有订单实现。候选查询仍返回三个登录方法；它们只命中了
  `return` / `throw` 通用语义词，没有命中 `order` / `payment` / `inventory` 等业务词。

## Evidence and classification

- 两个登录 browser result digest：
  `sha256:1804a21ab75a33b22efd909ba05ae2b5db18c9dada1e4c04242ce57693a22886` /
  `sha256:a6db6e510d9f50e113b1c8b61453eecbc7096d971456bed0a85bfb9661fefd18`；
- 下单 browser result digest：
  `sha256:2ba1b8e7e6571760dfe36670e9aed96c2df046c3dc27ed8b2324e1d1247083c3`；
- 下单 Answer summary / terminal digest：
  `sha256:6a05103720b9572e55b38fea446879ff200d95e42b198efe464a03bab57ab8dc` /
  `sha256:65b625d7aa0a86cfdb7198ae513b59909c124ff2c98f99eed01ba9ee0c36ad8c`；
- 可见工程只含 `pom.xml` 和 `src/main/java/dev/acme/auth/LoginService.java`；
- `FINDING-007-008` 已证明登录题所需的当前 Profile 语义已进入 Bundle，失败首先发生在问答编排，而不是知识不存在。

根因是两层叠加：

1. 固定一次 Plan 在看到 Query Result 前就锁定“候选查询 + 单方法查询”，不能根据多候选继续调查；
2. 候选检索对任一 token 采用 OR 命中，且把业务发现词与 `return` / `throw` 等回答 facet 词混合计分，无法形成可靠的“当前范围无相关实现”结论。

这不是 Provider 调用失败。三次模型调用成功只证明 transport/schema 链成立，不能把不能回答的产品结果改记为 PASS。

## Decision and disposition

run-004 作为“技术链 PASS / 产品 FAIL”永久保留。`ITER-007-SLICE-001` 触发已冻结的 stop/redirect 条件，
不执行 hidden canary，不授权 `SLICE-002/003`，不再为同一固定协议增加资格调用或问题补丁。

该失败通过 `ROADMAP-CANDIDATE-BOUNDED-WORLD-MODEL-INVESTIGATION` 路由到 `ROADMAP-M-002` 的 Step 1：保留问题前更新、
Snapshot、no-payload、Support、Citation 和正式 Web 资产，重新设计“Agent 只通过 World Model 工具做有界、结果驱动、多方法
调查”的候选方案。这个 Roadmap 处置不提前接受新 System Contract 或授权编码。
