---
id: FINDING-010-084
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [engineering, quality, project]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-083]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py, src/software_world_model/ai_infrastructure/engineering_question_model_source.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_question_strategy.py, tests/test_engineering_question_model_source.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: material-effect-omission-layer-must-be-application-verified
target: SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING
---

# FINDING-010-084：run-031 暴露 material-effect omission 层级未受 Application 约束

## Observation and evidence

新 clean candidate commit `3c45072f43e880c38b77f831c91744f96ae02dbe`、tree
`1139230153a8c7cf9af70810bea8b00155d1b38a`，归档 SHA-256 为
`79c1967155ab19f8d348e0e25de08558ed5fbc3f77aced49c6337177618cc326`；mall 保持 exact clean
`0504e86b1f1b6f1b8aa6a734d37a90fb67346be7`。fresh DeepSeek Conformance run
`ccrun_c607b10555764aed92abc8e209199963` 为 2/2 PASS，result digest
`sha256:43118c1a1b970b084cfd8acd21eaffd30224d2f7c96d512f926f7d944181f798`，Provider request IDs 为
`0eacd3aa-5a6b-4734-a744-70b9a62e9f79` 与 `42aaa1bc-4423-4763-b0f1-82dea816d961`，request retry 0，
Production eligible false。此前 sandbox-only Conformance 因三次 DNS pre-dispatch handshake 失败而封存 FAIL，但
`http_dispatch_count=0`、credential resolution 0，不是 Provider request retry，也不作为 fresh live 资格证据。

run-031 持续 Browser 会话只提交 Q1 `登录流程是怎样的？`。该题 12 次 dispatch 全部 completed，HTTP dispatch 12、connection reuse 11、
request retry/provider switch/outcome unknown 均为 0；结果 `engineering_result_c1728310f6ac35c4922cb6a73bfebcff` 为
`FAILED_CLOSED`。第一次 challenge 发现配置值、未挂载 DTO/response 语义与后续令牌 handoff 等问题并触发一次合法同包 rewrite；第二次
comprehensive PASS 后，fresh challenge 从 `UmsAdminServiceImpl` full entry 发现 `getCacheService().setAdmin` 缓存写入，但同时：

- `checklist_assessment.application_material_observation_omissions` 与 `draft_material_observation_omissions` 均为空，独立 observation 列表也没有
  cache effect；
- material-effect assessment 仍返回 `DRAFT_OMITS_MATERIAL_EFFECT`，并将同一
  `FINDING_OMIT_CACHE_EFFECT` 绑定到 original-question fulfillment challenge；
- Finding 错选 `REWRITE_WITH_EXISTING_EVIDENCE`，尽管 sealed Package 没有 cache material-observation ID。按 current code 的 exact
  `maximum_same_package_rewrites=1`，该第二次 rewrite 请求形成 `SAME_PACKAGE_REWRITE_FUSE_EXHAUSTED` 安全关闭。

这不是 rewrite fuse 太小。放宽 fuse 会允许 Answer 用 full-entry prose 绕过缺失的 Application-owned observation。根因是 assessment 只返回
free-text evidence/Draft scope 与 disposition，没有 closed 字段区分效果缺在 `APPLICATION_PACKAGE` 还是只缺在 `DEFAULT_DRAFT`；Application
只检查 disposition-kind 与 Finding Claim 绑定，未重算 remediation 是否与 omission 层级一致。

会话随后 clean stop，terminal receipt document digest
`sha256:3de3d7f9009fcdedac5bc8fa79605aeaee12e733c8f5e8b8f073b136e18eb824`，Gateway quick check PASS、checkpoint
`0|0|0`、最终无 WAL/SHM，所有会话文件为 `0600`。第一次从非 frozen archive 路径启动时 launcher 在拒绝前创建了 4096-byte 空 DB；该文件
被保留而未覆盖，正式会话使用新的 `gateway-run031-live-v2.sqlite3`。由于 Q1 已证明新 systemic blocker，Q2/Q3 与 66,000-byte 负测未继续；
Production Activation 始终 `NOT_EXECUTED`。

## Decision and disposition

- full-entry material-effect omission 必须返回 exact omitted-effect statements 与 closed omission layer。
- `APPLICATION_PACKAGE` 只允许同 challenged entry evidence class 的 `INVESTIGATE_MISSING_EVIDENCE`；effect 不得已存在于 exact Package
  observations。
- `DEFAULT_DRAFT` 只允许 `REWRITE_WITH_EXISTING_EVIDENCE`；每个 effect statement 必须精确存在于 challenged entry 对应的
  Application material observations，Finding 也必须绑定该 entry。
- Application 必须重算上述关系并失败关闭错误层级/remediation；不增加 same-package rewrite fuse。run-031 永久保持 Q1 FAIL、Q2/Q3
  NOT-RUN，不得追认。
