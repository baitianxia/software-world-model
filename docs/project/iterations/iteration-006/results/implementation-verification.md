---
id: ITER-006-RESULT-IMPLEMENTATION-VERIFICATION
kind: iteration-result
status: implementation-verified-live-pending
authority: execution-evidence
owners: [engineering, quality]
depends_on: [ITER-006-VERIFICATION, ITER-006-FINDINGS]
code: [src/software_world_model/application_services/java_static_call.py, src/software_world_model/application_services/maven_structure_update.py, src/software_world_model/application_services/maven_workspace.py, src/software_world_model/application_services/structure_view.py, src/software_world_model/interface/world_model_product.py, src/software_world_model/interface/world_model_http.py, src/software_world_model/interface/world_model_browser_ui.py]
tests: [tests/test_structure_knowledge.py, tests/test_java_static_call.py, tests/test_java_static_call_update.py, tests/test_behavior_view.py, tests]
iteration: ITER-006
---

# ITER-006 Java 静态调用实现验证 Result

## Decision

`ITER-006-SLICE-001` 已完成当前授权内的 Java static-call deterministic implementation：V-001—V-007 PASS，V-010 保持
`NOT_EXECUTED`。V-008 真实模型比较没有披露授权而未运行；V-009 只完成 zero-provider UI 状态、formal Citation 与空 console，
尚未完成 live sealed-product browser/Citation 人工验收。因此本 Result 是 **implementation-verified-live-pending**，不是 Slice
或 Iteration Acceptance，不授权外部分派，也不授权 Production Activation。

## Exact implementation subject

开发基线是 clean commit/tree `bc0ecefb806c946f9c2b5938470be18ec780115b` /
`78064f71632ebb6bd58891f8af76a67f64f35be5`。当前实现尚未提交，不能把旧 `HEAD` 伪装成实现 identity；本 Result 用 31 个
`src/`、`tests/` 与 `validation/structure_world_model_iteration_006/` changed/untracked paths 的排序 SHA-256 manifest 固定实际
执行 subject：`sha256:9e6d1f4f37de14ea07a3c7deeffbf779a5a5ae6b4db193b1ac3ee8e7f28a8e50`。

独立 Oracle digest 为 `sha256:3e4d502cf78f167670380a9381795b2fc6b85a683c1129250de05be826feedfe`，fixture
file manifest digest 为 `sha256:3a6fe1622c14d9e92e206392bf82436c5109e3f98dca8d3fd107227a8ad8a6ff`。机器证据索引
保存在 `var/iteration-006/implementation-verification.json`，digest 为
`sha256:e187152d6c533b2748a3d5ec43529f7cffd4d2dc8a33bc6a2eec57f730e84655`。

新 Profile 固定：Schema `sha256:32ab1a12e5cb87a9751b25238d5ef6cace620ab0da47f0fc31f9d10e081e47c8`，
Evaluation Context `sha256:0b08eab7334a06e267da6270b9074d0f121a235b086b61a898eb66cb83507f5c`，
Canonicalization `sha256:598c0ab07e3411ecc46b80743332290305c4325f5a098a258a78cdd3d338582f`。

## Frozen source and independent Oracle

测试仓库固定 SHA-1 object format、author/committer identity 与 timestamp；每次运行都机械断言以下 commit/tree，不接受只比较
显示名或临时 branch：

| Revision | Commit / tree | Oracle result |
|---|---|---|
| R1 | `db44ddb8b8683f0157dfd7bafa6be46b7d478bfb` / `4ee62aea3eb6c905836c119a1f0b351228a321dd` | 2 types、4 methods、4 declarations、3 CALLS |
| R2 | `575ef5a1375bc38581b0c6301643b36be653157e` / `2bdd0dbfdec4c44593f00a178941f24726b203f2` | 2 types、5 methods、5 declarations、4 CALLS；surviving Roots 稳定 |
| R3 unsupported | `3ba3459dff08f83bee6d4cf69a3a18892ab1be7a` / `502b1c8465801a52059a702f48743a4692586672` | `JAVA_CALL_TARGET_AMBIGUOUS`；CURRENT 保持 R2 |

Oracle 不导入产品 evaluator，显式列出 R1/R2 type/method/call closure 与每条 declaration/call Evidence 的 exact locator、UTF-8
byte range 和 excerpt。评论/字符串 decoy 不成边；zero-target、歧义、变量 receiver、truncated source、symlink、content digest 和
tree Evidence tamper 都拒绝完整 Candidate。

## Update, publication and Source-off proof

真实 Git Workspace 以 `knowledge_profile_ref=JAVA_STATIC_CALL_GRAPH@1`、`source_root=src/main/java` 注册；R1 初始发布和 R2
`REPLACE_COVERAGE` 更新均经过受控 Source collection、独立 replay verifier、Admission、Publication、Bundle 和 Catalog。
R3 失败后 Version history 仍只有 R1/R2。

随后 authority SQLite 和 repository 都被改名为不可达路径；全新 Python 子进程只挂载 Catalog/Bundle，完成 declared-method
inventory、outgoing CALLS、call path 与 ordered diff。Source-off 前后 CURRENT tuple、Workspace/Update Attempt 数与 Source
Operation 数 exact 相等。真实 Java Evidence 由独立 Broker/Projector 按 View allowlist 投影 Citation；Answer capability input
中没有 source excerpt 或 Evidence payload。

## Product and browser evidence

正式 `WORLD_MODEL` product chain 的 deterministic capability port 覆盖方法 inventory、direct call、positive/no-path、R1→R2
diff 与 runtime/reflection/DI/design-intent Gap；答案持续显示 `JAVA_SOURCE_DECLARATION@1` /
`JAVA_SOURCE_STATIC_CALL@1`，不把静态边扩张成运行时语义。

本机 Browser skill 通过零 Provider 的 UI harness 人工检查 Java/Maven Coverage、Profile-specific examples、supported、Gap、Read
Set 切换、旧结果清除和响应式布局，console logs 为空。这个 harness 没有 Citation 数据、没有真实 model call，故只支持 V-009
`PARTIAL`；正式浏览器 Citation 点击和 live product page 仍等待 V-008 的 exact disclosure grant。

该限制是本 Result 生成时的事实。后续用户已对新的 exact run-003 suite 授权；candidate freeze 证据见
[Live Candidate Freeze](live-candidate-freeze.md)，不会反向改写本次 implementation-only Result。

更晚的实际 run-003 结果为 FAIL，见 [Live run-003](live-run-003.md)。该事实同样不反向改变这里记录的 deterministic PASS；
它证明 deterministic implementation Gate 不能替代新的 exact capability qualification。

## Regression, findings and limitations

最终 `PYTHONPATH=src python3 -m unittest discover -s tests -q` 为 **819/819 PASS，85.463 秒**。`git diff --check`、Python
compile 和最终文档检查结果在机器证据索引闭合。完整套件仍打印已有 SQLite connection `ResourceWarning`；没有测试失败，本
Result 也不把该警告称为已修复。

四条实现发现全部 dispositioned：Profile enum coupling、zero-target fail-open、exact/new-process verification fidelity 与 browser
Profile switch stale result，详见 [Findings](../findings/README.md)。当前仍不支持 Java 全语言、runtime dispatch、reflection、DI、
classpath/bytecode、多 Profile Read Set、Scheduler、真实 Delta、公网部署或 Production Activation。
