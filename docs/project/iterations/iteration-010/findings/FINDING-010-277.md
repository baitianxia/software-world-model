---
id: FINDING-010-277
kind: implementation-finding
status: dispositioned
authority: execution-evidence
owners: [application, quality]
depends_on: [FINDING-010-270, FINDING-010-273, FINDING-010-276, SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION]
code: [src/software_world_model/application_services/lightweight_engineering_agent.py]
tests: [tests/test_lightweight_engineering_agent.py]
iteration: ITER-010
classification: system-contract
scope: systemic
disposition: application-owned-fixed-budget-candidate-projection
target: SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION
---

# FINDING-010-277：固定工具预算内需要收敛已有证据候选

## Observation

`run-156-phase-c-loopback` 的 q5 在固定工具预算内完成了 8 个合法工具动作；Primary 随后提交的答案被 fresh Reviewer 正确判为
`MORE_EVIDENCE`。Application 按当前 Engineering Conversation 契约在 `remaining=0` 时关闭工具并以
`BUDGET_EXHAUSTED` 结束，未恢复工具、扩大预算或重试 Reviewer。这一终态本身不是 Reviewer 或预算实现缺陷。

同一 trace 显示 World Model 与 cognition→Source bridge 已经完成 material candidate construction。第二次 cognition search 将同名
controller、implementation 与 interface declaration 作为前三个等分实体紧邻返回，Application 分配的 `read_index=4/5/6` 分别指向这三项；
Primary 读取 4、5 后跳过 6。后续 Primary input 还提供 resource implementation 与 request filter 的未读候选，Primary 仍选择了其他路径。
此外，分页 cognition 可能再次发现同一 Source 文件中的另一个实体；既有 path-keyed navigation capability 必须幂等复用，不能再次向 Broker
申请相同 opaque binding。相同文件的 line/literal hit 仍不是完整 cognition navigation，不能误作已覆盖。
因此最早可修复偏差位于 Application-owned cognition→Source candidate construction/Primary evidence planning projection，而不是
knowledge construction/retrieval、Source authority、Citation parser、Provider transport 或 Reviewer。

## Evidence

- `/Users/baitianxia/project/software-world-model/var/iteration-010/slice-001/run-156-phase-c-loopback/terminal.json` 记录 q5 的
  8 个合法工具动作、一次 fresh Reviewer `MORE_EVIDENCE` 以及随后按固定预算 fail-closed 的终态；独立监督已在 supervision lane 封存该
  terminal 与其 digest。
- q5 第二次 `SEARCH_COGNITION` 的 sealed Observation 已返回同名 controller、implementation、interface declaration；后续 sealed Primary
  inputs 的 `read_candidates` 还包含 resource implementation 与 request filter。相关路径均已获得既有 opaque read capability，证明
  cognition construction、retrieval 与 Broker bridge 不是最早缺口。
- 受控异质夹具验证 Source READ 的 coverage 以 exact source revision + canonical resource locator 连接 navigation 与 Broker retrieval，
  不要求两者共享 opaque reference；同一文件的 line/literal candidate 不会抑制 exact cognition navigation。
- 真实 `EngineeringAgentEvidenceToolAdapter` 的同一 Turn stateful fixture 先注册同路径 type，再以不同 exact locator 注册 method；第二次
  registration 保留第一项完整 citation/authority identity，只更新 Application 内部 typed-origin sidecar，不重复 bridge 或制造冲突。
- 当前 owner contract 已规定 `maximum=8`、`remaining=0` 时 effective catalog 为空、缺证据时不得恢复工具；因此本 Finding 不改变预算、Reviewer
  调用次数、答案/Agent schema 或任何 Provider 行为。
- 历史 run-156 sealed Gateway payload 只保存 model-facing candidate fields，不含 opaque `citation_ref`、content digest 或 authority receipt；
  因而 raw identity replay 明确记录为机器可读 `NOT_RUN`，不以 synthetic placeholder 冒充执行。model-facing ordering replay 与 live bridge
  identity fixture 分别提供可核验的已执行证据。

## Disposition

Application 在每次 Primary dispatch 前，从已经签发且未 READ 的候选、当前有序 Observation、candidate 的受信 cognition origin/typed entity
attributes 与固定 `remaining` 预算机械构造一个收敛的呈现顺序。只调整 model input 中既有 candidate entry 的顺序；`read_index` 与 opaque
capability identity 在首次签发后不得重绑、删除或改写，所有候选继续可见，Primary 仍须显式选择既有 `SOURCE_READ` 才能取得 Citation。cognition
provenance 转换为 Source candidate 时，先以 full-resource Source identity 判断是否已覆盖；已有 cognition-navigation path capability 则按
exact revision + canonical path 幂等复用，并把新的 exact locator 只记录在 Application 内部 sidecar。line/literal/search candidate 不属于这两类，
仍须为尚未建立的 cognition path 请求受控 capability。
排序不得读取题面正文、工程/业务词、类名、方法名或 path substring，也不得自动读 Source、隐藏可选项或声称技术相关性。

Owner `SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION` 同步上述 fixed-budget candidate projection。实现不引入新的 versioned Agent
option、输入/输出字段、Prompt、Reviewer 重试或题目/工程特判，也不改变固定 8-action fuse。实现后须先以 run-156 sealed payload 证明缺失的
未读 declaration/effect candidate 被保留并前置，再用至少两个异质 fixture 复验 candidate ordering、resource coverage 与 path-keyed
navigation 幂等；历史 payload 缺少 authority receipt 时，测试必须输出并断言机器可读 `NOT_RUN`，不能用 unittest skip 或 synthetic identity
冒充 raw replay。Reviewer 仍可在证据不足时如实要求更多证据，预算耗尽时继续 fail-closed。本 Finding 不宣告 Phase C 完成或 `ADVANCE`。
