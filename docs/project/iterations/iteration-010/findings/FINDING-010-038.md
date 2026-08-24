---
id: FINDING-010-038
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [ai-infrastructure, application, quality]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-036, FINDING-010-037]
code: [src/software_world_model/ai_infrastructure/engineering_question_model_source.py, src/software_world_model/ai_infrastructure/engineering_question_strategy.py]
tests: [tests/test_engineering_question_model_source.py, tests/test_engineering_question_strategy.py]
iteration: ITER-010
classification: local-implementation
scope: systemic
disposition: make-evidence-class-exhaustion-and-claim-kind-role-pairs-explicit
target: src/software_world_model/ai_infrastructure/engineering_question_model_source.py
---

# FINDING-010-038：一个模态缺细节不是全局 Unknown，Limitation 也不能伪装成过程 Claim

## Observation

clean candidate `e15ec508fd194e286a2771c83a821dc706003973` 与 current DeepSeek Conformance
`sha256:5ef04be6b15542a485a633ef3c0664b6b82cbd6ea8bbe9f10b368a1bb4756525` 重跑原题时，Investigation 只搜索并读取
`REPOSITORY_DOCUMENT/README.md`，随后把四个 checklist items 全部 disposition 为 `UNKNOWN`，没有尝试仍受权且直接相关的 `SOURCE`
evidence class。Answer 已按 `FINDING-010-036` 正确给最终 coverage-only Limitation 返回空 observation links，但把其余 limitation
observations 分别放进 `content_role=USER_VISIBLE_PROCESS / IMPACT_OR_SIDE_EFFECT` 的 `kind=LIMITATION` Claims，违反既有 domain pair，最终以
`Engineering QA answer output violates the domain contract` 失败关闭。

该会话 5 次 role dispatch，retry/switch 0，TLS 1 次成功并复用 4 次，Gateway 主文件与 live WAL/SHM 均为 `0600`，Production Activation
为 `NOT_EXECUTED`。它证明上一修复被模型采用且 Domain 继续 fail-closed，但不构成答案或体验 PASS。

## Root cause

- 现有 domain 已只允许 `AFFIRMATIVE` 与 direct/process/impact/implementation 配对，以及 `LIMITATION` 与 direct/limitation 配对；Answer
  prompt 说明了角色顺序和 limitation evidence，却没有把合法 pair 写成显式 closed mapping。模型因而按文字主题把 limitation 误标为 process/
  impact；
- adaptive Investigation prompt 要求根据新 Result 决定下一步，但没有明确提醒：一个 evidence modality 没有细节不能证明其他已授权 evidence
  class 也没有；模型过早以 boundary receipts 结束；
- 两项都是通用 prompt/input-contract 表达缺口，不是 mall、登录、README、Java、类、方法、关键词、fixture 或 Oracle 特例。

## Decision and disposition

- 不放松 Domain。Answer role input 提供 exact `allowed_kind_by_content_role` closed mapping；prompt 明确禁止 `LIMITATION` 与 process/impact/
  implementation 配对。全为 non-supported 时，由唯一 direct limitation 覆盖 limitation observations，其他需要的说明只能放在末尾
  `LIMITATION` role；
- Initial 与 Verification Investigation 在以 UNKNOWN/CONFLICT/FAILED FINISH 前，必须检查 registered evidence classes 与 prior intents；只要
  未尝试的 eligible class 能在剩余 fuse 内直接减少 material unknown，就继续调查。一个模态缺细节不构成全局 absence；
- prompt/input contract 与定向测试处置该实现缺口。新 clean candidate、current Conformance 和完整持续 run 仍必须重新执行。
