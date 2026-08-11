---
id: ITER-003-RESULT-G3B
kind: iteration-result
status: pass
authority: evidence
owners: [project, quality, security]
depends_on: [ITER-003-RESULT-V009, ITER-003-VERIFICATION, ITER-003-SLICE-001, FINDING-003-022, FINDING-003-023, FINDING-003-024, FINDING-003-025, FINDING-003-026, FINDING-003-027, FINDING-003-028, FINDING-003-029, FINDING-003-030]
code: [src/software_world_model/ai_infrastructure/model_egress_gateway.py, src/software_world_model/ai_infrastructure/pinned_ark_https.py, src/software_world_model/interface/world_model_product.py, validation/structure_world_model_iteration_003/g3b]
tests: [tests/test_iteration_003_g3b.py, tests/test_model_egress_gateway.py, tests/test_pinned_ark_https.py, tests/test_world_model_live_execution.py, tests/test_world_model_product.py, tests/test_iteration_003_v009.py]
iteration: ITER-003
---

# ITER-003 Result：G3b Evaluation-only browser model run

## Verdict and scope

G3b 最终裁决为 **PASS**。初始 product checkpoint
`7933712d7d00d113abe0ec147729fa41562bea76` 虽完成 60/60 execution SUCCESS，却因两个
`WM-PRODUCT-007` run 丢失完整 root GA 而在独立评估中只有 58/60，曾被正确裁决为 FAIL。修复后没有
重写或重放旧 terminal；用户明确同意新批次后，product checkpoint
`b9b329a9b341b01fc41486ef9b0c809ac8665332` 重新准备并完整执行全新 60-run batch，最终独立评估为
60/60 PASS、重大错误 0，OS/Gateway/Answer/Projector 边界与性能均 PASS。

本 Result 同时保留初始 FAIL 与最终 revalidation PASS 的 exact lineage。G3b 只解除 G4/Product Validation
阻断；Production Activation 不在授权范围，始终为 `NOT_EXECUTED`。

## Authorization and frozen inputs

- 用户于 2026-08-11 明确授权 `ITER-003-G3B-EXACT-INPUTS@1.0.0` 的 product question/sealed
  View 模型分派、distinct Gateway Provider 调用和 OS denial audit，且无需重复确认；权限 digest 为
  `sha256:d0a572d621a1163e8e9e41add704f682dcac2aabb3a3e99c0408ed188813a8a9`；
- input freeze document digest 为
  `sha256:1577f5fe7c7949e5a06a1497572e42487afa74c3224efe2f59a60f9129a57ea2`，raw SHA-256 为
  `1b0bc300ea13b78c8b43d309e29d00c950e7f9994976ae7a9d61b26e0ddd01ec`；
- exact Provider/Adapter/model 为 Volcengine Ark /
  `openai-chat-completions-no-tools@8` / `glm-5-2-260617`（observed `glm-5.2`），endpoint 为
  `https://ark.cn-beijing.volces.com:443/api/coding/v3/chat/completions`，credential reference 为
  `env:ARK_API_KEY`；
- Product Suite raw digest 为 `sha256:c165af6b…`，mall/identity Oracle raw digest 分别为
  `sha256:412d2e03…` / `sha256:b02e4414…`；初始 batch 的 prepared registry document digest 为
  `sha256:1aef44d3f9d4a3eb6327e15e9b81104a600532b5f31e0cef3a7a25b7249472f0`。

权限明确排除 Production Activation，所有 invocation/batch/result 都记录 `NOT_EXECUTED`。

## Initial product checkpoint and preserved attempts

正式 product checkpoint/tree 为
`7933712d7d00d113abe0ec147729fa41562bea76` /
`11996e8a5dac0c1edb8d344198147e883736a46e`。正式证据目录为
`var/iteration-003/g3b/7933712d7d00d113abe0ec147729fa41562bea76/`。

之前的失败尝试全部保留，不覆盖、不择优：

- `a00848a…` 在 Provider 调用前因 40 个固定 ancestor profile slot 不足而 preflight FAIL，模型调用为 0；
- `1b24d8e…` 在 Provider 调用前因 inherited TCP data 需要 Seatbelt `network-outbound` 而 preflight
  FAIL，batch digest 为 `sha256:06b36cf5…`，模型调用为 0；
- `19a7462…` 的 preflight PASS，第一个 run 发生 1 次 Provider 调用后，本地 Citation broker
  cold import 失败，batch 立即终止为 0 SUCCESS/1 FAILURE，digest 为 `sha256:90cd3d19…`，未重试；
- `7933712…` 修正 staged broker 后使用全新 prepared/dispatch 目录执行正式 60-run batch。

因此正式 batch 包含 60 次产品 Provider 调用；连同已保留的 `19a7462…` 失败尝试，G3b 实际观测到
61 次 product Provider 调用。本 Result 后的 evaluator 修正、本地产品修复和文档回写均未追加调用。

## Initial formal batch and isolation evidence

- invocation document digest 为
  `sha256:a5e91675df05bede12b7792dc05a562daf6fe00e92a367895a3734b31168a26c`；batch document digest 为
  `sha256:be7b87be4941f36afef19a3e86547bad70d017870021d229503238042835c185`；
- 40 个 static + 20 个 runtime metamorphic run 全部 terminal=`SUCCESS`，0 failure、0 selective retry，执行前后
  protected stage 不变；
- preflight document digest 为
  `sha256:54868b14359819ffde1e2cd5a244b996364563528d6ea789ea168c793890ea08`，OS enforcement 为
  `MACOS_SEATBELT_DENY_DEFAULT`；
- supervisor 无 credential/payload，只解析并连接 exact Provider peer；Gateway child 继承单一已连接 TCP fd
  和 trusted evaluator 预绑定的 exact `0600` AF_UNIX listener，新 AF_INET/AF_UNIX socket syscall 被 Seatbelt
  拒绝；
- selected address `198.18.0.26` 如实标记为 `EXECUTOR_SYNTHETIC_EXTERNAL`，不冒充公网 IP；child
  另复核 peer port 443、TLS certificate/SNI 和 exact HTTP path；
- Answer 不读 Source/Evidence payload/Oracle/baseline，Projector 只读 result-scoped disposable Citation Store；60 个 run
  的正常 workload 审计和 deny probes 均被最终 evaluator 接受。

该 macOS 机制只对 digest-sealed 闭合 Python workload 合格，不宣称能抵抗任意 native code 通过
`disconnectx`/`connectx` 重定向 inherited fd；任意 native compromise 威胁范围需要 VM/container/per-process
network namespace 或等价 exact-destination enforcement。

## Independent product evaluation

事后 evaluator 始终不调用外部模型，并保留每次结果：

- 两次 invocation 前失败先后发现 pretty-printed Oracle 和 newline-terminated baseline seal 被错用
  canonical runtime-receipt loader；都发生在 individual terminal scan 前，没有 Result；
- checkpoint `1ff44f0…` 的首份密封 Result 因 endpoint 表示和 diff counts 两个 evaluator 误判而报
  0/60 FAIL；它保留为 `product-evaluation.json`；
- checkpoint `4d75aaf…` 消除两个误判，`product-evaluation-v2.json` 收敛为 58/60 FAIL，但
  Direct population 字段把保留失败误报为 0；
- 最终 evaluator checkpoint/tree 为
  `bff20651c7b2b9b84f2bd9c845091ccc631ca096` /
  `1774fb5291d4b3aa047665914fd29edf279a34f0`，script digest 为
  `sha256:0716563d3269e40725883329b5b5f35253632124131afe1e7fbe2e9bcc846ec1`。它在扫描 terminal 前密封
  invocation digest `sha256:f0b95beb9f9a24fe16ef4fd22ca3a2e1973caff5e68f5840b5d12899fd6feb1c`；
- 最终 `product-evaluation-v3.json` document digest 为
  `sha256:99ea82bd99cab45128083bc5560b999ba9627505a7e2e9745a72ad3c85a74071`，raw SHA-256 为
  `2a9caf82b4b9c5a841cbedf5d9bb4388b7e580368ce2fea4262a98f83c5a5c8e`。

V3 Result 的精确裁决为：

- boundary PASS，performance PASS，58 PASS / 2 FAIL，major error run count=2；
- Direct population 为 55 terminal / 15 SUCCESS / 40 preserved failures，Mature 为 55/55 SUCCESS；
- World Model 首问 P95=10,726 ms，Direct=73,084 ms，ratio=146,762 ppm（限制 1,500,000）；
- World Model 重复问 P95=11,563 ms，Direct=113,850 ms，ratio=101,560 ppm（限制 500,000）；
- 失败 run 仅为 `static-WM-PRODUCT-007-run-02-paraphrase` 和
  `static-WM-PRODUCT-007-run-03-canonical`；两者的回答均缺少完整 root GA
  `org.example.root:structure-fixture`，World Model completeness=666,667 ppm，更强密封对照=1,000,000 ppm。

## Product remediation and local verification

`FINDING-003-029` 定位到 `ProductDraftGenerator._render_direct`：对 `canonical_ga is None` 的 root
`SOFTWARE_SYSTEM` 退化成了 artifactId。修复 checkpoint
`11e04ba934115d01ad187b4c2d25469a5547af9a` 改为从同一受信 Entity State 的 `effective_group_id` +
`artifact_id` 渲染完整 GA，字段缺失时 fail closed。它不从 question token 或其他 Entity 做名称拼接。

最终 main evidence merge checkpoint/tree 为
`9d0a683dde8ed392cfced0b657935cb92dbddb3e` /
`06bc77b6c4d52a80ffa4544d361d43a3bd380168`，它同时保留产品修复和 `bff2065…` evaluator lineage。在同一代码 tree
上的本地证据为：

- G3b/V-009 聚焦回归 46/46 PASS，日志 SHA-256
  `cf5edd45a64cfaaec47c85f5d5805f59af85135bcfdc2d0389b8cdc853cdf657`；
- 完整回归 750/750 PASS，日志 SHA-256
  `1a98928663a293d4498046903c1cd82279198c75ac033137ac1381e5074ef18b`；
- 文档检查 189/189 PASS，日志 SHA-256
  `fe3fbd87a6d4362bd24f5c318cd9d26f167b40c24065745bcb1b9f7942eb0400`。

日志位于 `var/iteration-003/g3b/5a44c51/postfix/logs/`；merge 只改变 Git DAG，不改上述 tree。

## Revalidation batch and final verdict

用户在得知“修复后代码必须重新冻结并完整执行新 60-run batch”后以独立消息明确回复“同意”；该消息 raw
SHA-256 为 `905819e2e3a059a02087855e9f326d05c877c1767ec31dc012c5c44652840230`。新运行严格绑定
product checkpoint/tree `b9b329a9b341b01fc41486ef9b0c809ac8665332` /
`43accc44508a1cce9066aead258ec11a5b6a4ef0`，没有复用旧 prepared input 或模型输出：

- prepared registry digest：
  `sha256:ace18c7c0b6c43a1a17a76be810a9d378d8069b34fa679c263de5d74729f4407`；
- invocation / preflight / batch digest：
  `sha256:c4c2276fd9131b7300f23a03f37168c279b391793ca132ff74ec704fe67267ee` /
  `sha256:058e507b3dfcf2d47f34a7c0b1600b48892423a9bc25484bb28ef4a3e018f53f` /
  `sha256:bf8ca1fe4c4e8861b3edb7a9853eb33f1536f5ee2a2bcfb90b38f1ac0bffc632`；
- 40 static + 20 runtime metamorphic terminal 全部 `SUCCESS`，0 failure、0 selective retry，protected stage
  前后 digest 相同；
- OS boundary 沿用已裁决的 inherited exact connected Provider fd、prebound `0600` AF_UNIX listener、
  child new-socket syscall denial 和 peer/TLS/HTTP exact binding；selected address 仍如实标记
  `EXECUTOR_SYNTHETIC_EXTERNAL`。

新 batch 后才创建 evaluator-only descendant checkpoint/tree
`9977269b246114810b431adb00207f286ec951ac` /
`daa2d987a8deaa1e16cff3adfa4ddbc213adaa64`；相对 product checkpoint 的 closed Git delta 只有
`evaluate_results.py` 与其测试。evaluator protocol 为
`ITER-003-G3B-INDEPENDENT-EVALUATOR@1.0.1`，script digest 为
`sha256:771e9271ed1c319c7ad46abd97273e08e832afdd83544373b8b4af3710ddf4e1`。它在读取 individual
terminal 前密封 invocation digest
`sha256:e569c009e1d71ebd894644c838befb7ba32b2d21a9b4e060bf5cef5c9ea98a8b`。

最终 `product-evaluation.json` document digest 为
`sha256:7952bd9b6a68e50beb7a6370942ea163ac1e1359c2922cd77500903f149f2b1c`，raw SHA-256 为
`7488a2800f226e2660692cc9a58494a03cff9abc4724ec501f68c16a2c5b0203`。裁决为：

- 60/60 PASS，major error count=0，boundary PASS；
- Direct 55 terminal = 15 SUCCESS + 40 preserved failure，Mature 55/55 SUCCESS；
- World Model 首问 P95=13,041 ms，Direct=73,084 ms，ratio=178,437 ppm（限制 1,500,000）；
- World Model 重复问 P95=13,323 ms，Direct=113,850 ms，ratio=117,022 ppm（限制 500,000）；
- 五个 `WM-PRODUCT-007` run 均显示 exact root GA `org.example.root:structure-fixture`，完整性
  1,000,000 ppm，不低于任一 eligible stronger comparator。

新批次增加 60 次 product Provider 调用；连同初始 checkpoint 及其失败尝试，G3b 全部保留证据共观测 121 次
product Provider 调用。没有 hidden/选择性 retry。最终 evaluator、浏览器构建、人工验收和回归均未调用外部模型。

因此旧 58/60 结果继续只证明旧 checkpoint FAIL，新 60/60 结果独立证明修复后的 exact product checkpoint
PASS。G3b/V-010/V-011 阻断已解除；Production Activation 始终为 **NOT EXECUTED**。
