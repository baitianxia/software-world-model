---
id: FINDING-010-006
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [application, quality]
depends_on: [ITER-010-SLICE-001, SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING]
code: [src/software_world_model/application_services/engineering_question_answering.py, src/software_world_model/interface/engineering_qa_source.py]
tests: [tests/test_engineering_question_answering.py, tests/test_engineering_qa_source.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: measure-investigation-progress-independently-of-operation-identity
target: src/software_world_model/application_services/engineering_question_answering.py
---

# FINDING-010-006：Result identity 不能充当调查进展 identity

## Observation

调查状态机原先用完整 `RetrievalResult.digest` 判断新 Result 是否产生进展。该 digest 正确绑定 Broker operation identity；但同一查询在新的
Ledger prefix 上会形成新的 Proposal 和 operation identity，即使 Worker 返回完全相同的观察，Result digest 仍然不同。因此模型重复
相同 search/read/parse 时，状态机会不断重置 `no-progress` 计数，直到较宽的 step 上限才失败关闭。

## Evidence and root cause

- Proposal、operation 和 Result 的完整身份都必须绑定当前 Ledger prefix，不能为了去重而复用；
- 原 `result_digests` 集合比较完整 Result digest，实际比较的是“是否同一次执行”，不是“是否获得新观察”；
- 连续三次相同 `REPOSITORY_DOCUMENT` search 的路径、内容、modality、Coverage 和资源观察完全相同，但三个 Result digest 不同；
- 高安全 step fuse 仍能终止循环，因此没有无限执行；缺口是更窄的 deterministic no-progress fuse 语义未实现。

根因是审计 identity 与进展 identity 复用了同一摘要。既有契约已要求 deterministic no-progress 熔断，Owner 和系统语义无需改变，分类为
`local-implementation / systemic`。

## Decision and disposition

- 保留完整 Result digest 对 request、operation、items、Coverage 和资源收据的原有绑定；
- 新增 `RETRIEVAL_PROGRESS@1` 摘要，只绑定 exact revision/Profile、操作语义、query/path、evidence class、无 operation identity 的实际
  observation、status、bytes/files、truncation 和 failure；
- 状态机跨初始调查与 successor 补证累计 progress digest。相同语义与相同观察不再重置 no-progress；不同查询、路径、operation、
  observation 或 outcome 仍可形成新进展；
- Ledger `SOURCE_RESULT` 记录 progress digest，便于解释熔断；Local Git search 的 `query_digest` 同样改为只绑定 literal query，
  不再误用完整 operation digest。

该处置只修改本地确定性实现和测试，不改变模型角色、权限、预算数值、Provider 外发或 Activation 边界。

## Verification

回归测试让 Investigation 连续提出同一 search，并由 Worker 返回相同内容：第一次建立观察，后两次不构成进展，状态机在第三个 Source
operation 后以 `NO_PROGRESS_FUSE_EXHAUSTED` 失败关闭；三个完整 Result identity 仍不同，而 progress digest 精确相同。完整状态机、
Broker/Worker 和 Web 测试继续通过。
