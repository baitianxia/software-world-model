---
id: ITER-005-RESULT-G0
kind: iteration-result
status: passed
authority: execution-evidence
owners: [engineering, quality]
depends_on: [ITER-005-VERIFICATION]
code: [validation/structure_world_model_iteration_005/g0.py, validation/structure_world_model_iteration_005/g0_inputs.json]
tests: [tests/test_iteration_005_g0.py]
iteration: ITER-005
---

# G0 Generalization Preflight Result

## Exact subject

G0 在产品 baseline commit `a91dc7c8446f3815bf7b4f9a1123b6242620a97e` / tree
`73b8cf52e0ab5202137dd833445ced237ef698cd` 上运行。Oracle 为
`validation/structure_world_model_iteration_005/g0_inputs.json` / `sha256:3989a536…`；runner 不导入产品 package，系统
仅通过 `software_world_model.interface.cli` 子进程执行。

## Result

| Case | Exact revision | Oracle | Actual |
|---|---|---|---|
| TTL3 | `01639f2…` / tree `68a6f3c…` | 8 modules、5 direct internal edges、2 absence | COMPLETE / PASS |
| Gson | `310ac34…` / tree `ff83ee01…` | 7 modules、6 direct internal edges、2 absence | COMPLETE / PASS |
| Maven Wrapper | `e10ec82…` → `62c6a95…` | valid graph 后拒绝 reactor internal `type=pom` | valid COMPLETE；unsupported `INVALID_ARGUMENT`；CURRENT 均为 `structure_snapshot_53eaf6…` |

完整人读/机器报告位于 `var/iteration-005/g0/a91dc7c-r2/report.md` 与 `report.json`；JSON digest 为
`sha256:bcd7a269aacc4db54e22a2a2ebae805394024837ee60c13072bbf2483c6f7ab9`。首次 runner 尝试因读取错误的报告字段停止在
`var/iteration-005/g0/a91dc7c/`；它没有形成 Gate 结论，修正后在新目录全量重跑，失败记录未删除。

## Decision and limits

V-001 PASS，允许授权 SLICE-001。结果只证明当前 Profile 对这两个真实多模块仓库的最低泛化能力，以及一个明确拒绝边界；
它不扩展 Profile、不证明任意 Maven 项目可用，也不授权 SLICE-002 或 Production Activation。
