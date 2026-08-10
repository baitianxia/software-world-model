---
id: FINDING-003-014
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [engineering, architecture, quality]
depends_on: [ITER-003-SLICE-001, FINDING-003-011, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-CONTRACT-AI-CAPABILITY-EVALUATION]
code: [src/software_world_model/ai_infrastructure/world_model_answer_strategy.py, src/software_world_model/ai_infrastructure/world_model_capability_evaluation.py, validation/structure_world_model_iteration_003/v009]
tests: [tests/test_world_model_answer_strategy.py, tests/test_world_model_capability_evaluation.py, tests/test_iteration_003_v009.py]
iteration: ITER-003
classification: iteration-design
disposition: qualify-separate-model-proposal-strategy-with-standalone-evaluator
target: ITER-003-SLICE-001
---

# FINDING-003-014：V-009 不能把 G3a offline strategy 原地改成 live strategy

## Observation

G3a 通过的 `world_model_answering.py` 把 invocation 固定为
`DETERMINISTIC_OFFLINE`、`provider_route=null` 和 `external_dispatch=false`，并由
process-local authority store 与 `EVALUATION_ONLY` sink 闭合。若为了 V-009 直接给该实现增加
Provider route，会改变 V-008 已裁决的执行边界，也会在取得资格前把 test authority 误当成 live
Response Control。

同时，V-009 closed CE 的 evaluator 需要读取 projection/oracle；若让同一模型策略进程同时持有
这些字段，就无法证明 expected value 没有进入模型输入。

## Evidence

- 新 `world_model_answer_strategy.py` 只形成 model proposal：每 Case 一次调用、无 retry、无 Tool，
  Authorized Input Manifest 只有通用 instruction、sealed synthetic case input 与 Conformance
  qualification reference。
- frozen suite 的 `projection_fields`、`expected_normalized_result` 和 `forbidden_events` 不进入
  Manifest 或 Provider request；测试逐份检查七个 wire request。
- standalone evaluator 以 `python -I -S -B` 独立 PID 执行，只导入标准库；输入为密封 evaluator
  packet 与 normalized Result，输出 exact projection、forbidden-event audit 和实现 digest。
- V-009 runner 在 Conformance 首次网络分派前密封 exact invocation receipt，并要求 closed CE 只接受
  同 checkpoint、同 freeze digest 的 Result binding；裸 Result 或语义篡改后的 binding 均失败关闭。
- default-deny egress policy 明确区分 V-009 的 direct Adapter qualification transport 与 G3b 必须实现
  的 `Answer→AF_UNIX Gateway→exact HTTPS endpoint` OS boundary；V-009 结果不得冒充 G3b 隔离证明。

## Impact and classification

该发现收窄本轮 V-009 的实现路径，但不改变 System Contract：World Model 模型仍只能提交
Proposal，Model Gateway 仍是外部模型调用入口，Capability Evaluation 仍独立拥有 Oracle 与
PASS/VALID。故分类为 `iteration-design`。

## Decision and disposition

保留 G3a exact checkpoint `f2269ecca5c1e85e69fafd93fe599c841227f3c7` 及其 offline
authority semantics 不变；V-009 新增独立、版本化、可指纹化的 model proposal strategy 作为资格
subject。closed CE 必须绑定 G3a checkpoint、Provider/Adapter/requested+actual Model、Prompt、
output contract、tool policy、configuration、egress policy、suite 和 standalone evaluator digest。

V-009 Conformance、CE 与两条 baseline 可按冻结 policy 使用 direct Adapter transport，但这只属于
qualification/comparison preflight。首次 G3b product run 前仍必须实现 distinct Model Egress Gateway
process 和 OS denial audit，不能复用 V-009 direct transport 作为产品通信路径。

## Verification after disposition

`tests.test_world_model_answer_strategy` 验证七类 proposal 的 closed schema、单次调用、oracle-free
Manifest 和 failure closure；`tests.test_world_model_capability_evaluation` 验证七类 Definition/registry
绑定；`tests.test_iteration_003_v009` 以 fake transport 完整形成七 Case、独立 evaluator、generic
Capability Result `PASS/VALID`，同时证明该 harness 本身不需要真实外部调用。
