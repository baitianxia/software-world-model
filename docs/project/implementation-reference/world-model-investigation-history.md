---
id: PROJECT-REFERENCE-WORLD-MODEL-INVESTIGATION-HISTORY
kind: implementation-reference
status: historical
authority: historical-evidence
owners: [engineering, quality, project]
depends_on: [SYS-ADR-015, SYS-ARCH-BASELINE]
code: []
tests: []
coding_input: false
source_path: docs/system/architecture/decisions/ADR-015-bounded-world-model-investigation.md
as_of: 2026-10-02
---

# world-model investigation implementation history

以下内容从 ADR-015 的详细 Profile 说明迁出，保留历史 Contract、资格和传输实现信息。它们不是概要架构语义。

曾有 Profile 规定每题调查模型调用为 2—4 次，随后各 1 次 Draft 与 Review，总上限 6；首轮固定 candidate discovery，method query
最多携带 3 个 exact method Ref，`FINISH` 自身计作调用，预算、bytes、Support、trace 和 wall time 到达边界即失败关闭。
该实现还规定了 descriptor/TLS acquisition、persistent verified session、request retry=0、未消费 descriptor 丢弃以及 TLS attempt/success/
reuse 与 Provider call 分开收据。这些数字和传输策略只属于当时 Profile/资格实例；新的 Profile 必须重新定义并取得独立资格。
