---
id: ITER-008-RESULTS
kind: results-index
status: draft
authority: project-evidence
owners: [quality, project]
depends_on: [ITER-008-VERIFICATION]
code: []
tests: []
iteration: ITER-008
---

# ITER-008 Results

尚无 Product Result。Proposal、Readiness 说明、开发者自拟问题或测试数量都不是 Product Result。

run-023 后的 formal product `run-004-freeze` 已通过 deterministic Gate 并形成 authorized evaluation grant，但正式 Web 在任何问题
POST 前显示旧三调用边界；同一 public validator 也会拒绝 bounded 4—6 call Result。startup request count 与模型调用均为 0，因此
没有形成或消费一份问题 Result。该实现漂移按 [FINDING-008-033](../findings/FINDING-008-033.md) 以 candidate `41b766a…`
修复；旧 freeze/grant 因 source identity 改变不可继续使用，新的 formal refreeze/Web 仍 blocking。hidden canary 未披露，Production
Activation 为 `NOT_EXECUTED`。

修复后的 formal `run-005-freeze`、authorized startup 与 4—6 call UI 均 PASS；首个登录题仍没有形成 Product Result。Gateway
authorized wrapper 在 560 ms 内因 packaged bounded workload self-integrity pin 过期而失败，terminal digest 为
`sha256:5288b0c2354251d2b762d755807b3ab8bde4bece21e4de5fd152e692ca00a791`。credential/TLS/HTTP/model call 与 retry 均为 0，
Source/Update/Direct/Evidence payload access 为 0，browser console clean；后续题未执行。该偏差按
[FINDING-008-034](../findings/FINDING-008-034.md) 以 `54bc8c8…` 修复；旧 run-005 freeze/grant/session 不可复用，新的 formal
refreeze/Web 继续 blocking。

再次修复后的 formal `run-006-freeze` 与 authorized startup PASS。登录题完成 4 个 DeepSeek HTTP 200；TLS 1、reuse 3、credential
4/4、retry 0，前三个 Investigation Result 均完成。第四个 Draft 已生成语义正确的中文答案，但旧契约随后要求复制 4 个 step Result
ID 与 35 个 support digest，输出在 1000 tokens 时截断并以 `STRUCTURED_OUTPUT_INVALID` 失败关闭；terminal digest 为
`sha256:bff896e44ab3ef05180946ce5b9230ba1133858259b65022b68305d2e98db01c`，browser console clean，后续题未执行。该 Owner
缺陷按 [FINDING-008-035](../findings/FINDING-008-035.md) 处置：Draft/Review exact authority collection 由 Application terminal
compiler 绑定，模型只返回语义字段和空 authority envelope。活动 identity 已升级为 `1.5.8/@17/@1.4.8`、suite/oracle `@1.5.8`；
旧 run-023 Qualification 与 run-006 freeze/grant/session 不可复用，新 Conformance/Capability 继续 blocking。

terminal-owner candidate `1725b44…` 的 run-024 Conformance 已 2/2 / 12/12 PASS。Capability freeze/authorization digest 为
`sha256:fa119ba7…90acf` / `sha256:490a1c6a…779a0`；前 39 responses / 17 Case 完成，Draft 以 104 tokens、raw 空 authority
collection PASS。第 40 次 Review request 在唯一 TLS session 复用 39 次、运行约 120 秒后以 `REMOTE_DISCONNECTED` outcome
unknown 关闭；HTTP/credential 40/40、retry 0，failure/terminal digest 为 `sha256:4f13c0e2…a771a` /
`sha256:3cf8ccd7…573f8`。这不是 Capability FAIL verdict，也没有形成 Qualification；授权已消费且不得 retry。

[FINDING-008-036](../findings/FINDING-008-036.md) 将 transport version 化为 Adapter `@7`、connection policy `@2`、audit `@2`
与 policy `@1.4.9`，每条 verified session 最多 20 dispatch，轮换在 credential/HTTP 前，request retry 仍为 0。上游
`1.5.8/@17` 与 suite/oracle 不变；新 identity 完整资格化前 formal product freeze/Web 继续 blocking。

clean exact candidate `34048ae770944a11aa4e01d0249b90933a30e8c7` / tree
`153c2dc625fd3e72e6b49c6d6cf94be95a3ef894` 的 run-025 已完成新 identity 资格化。Conformance 为 2 requests / 12/12
PASS；Capability 为 40 calls / 18 Case / 18/18 PASS，TLS attempt/success `2/2`、reuse `38`、HTTP/credential `40/40`、
unknown/retry `0`，实际执行两条各不超过 20 dispatch 的 verified session。Capability result/closed-document/
qualification-proof/qualification-document/terminal digest 为
`sha256:caf062a2a49fd28e6046937fd10f633c5155f9c47c60565a8d422c2a7b98cc11` /
`sha256:53fe0e402ee737ec4200ecc408618e4b42fff42dfaf6ae3bd9b5ec358fc1570a` /
`sha256:b407f6ad708d6a3b071325d599e9616af89cce249f7202b38e740f02eb948453` /
`sha256:7d3b4ea2c5527f1e621e5d268105626f5ccf06c00cc9e7b74ae3dcea6bea208a` /
`sha256:b0dd529152e6c7e43b231a3d439e65de38ea95542cc173b5a25dbe124564a8d6`。Qualification ref 为
`capability-evaluation:evaluation_result_81d1cb091ea249e78bbdf562aabc7403`，有效至
`2026-08-27T13:19:05.298209+00:00`。两份授权均已消费且不可 retry；V-002 PASS，下一步是全新 formal product freeze/Web，
hidden canary 与 Production Activation 仍未执行。

该证据写回后的 formal `run-007-freeze` 通过 deterministic Gate：report/deterministic qualification digest 为
`sha256:515a88b8dd73e3144479c8d3880ce025404d3ccce6008ce5ca8b97b0059492b0` /
`sha256:4995715615e23719ebc1a64a10c7fdefd09bbef601b370f1b86a9033dd81120d`；focused 89/89、candidate package 37/37、docs PASS，
full 1036 项只保留 exact historical 4 FAIL + 1 ERROR，freeze model dispatch 为 0。authorized grant/startup receipt digest 为
`sha256:6c433a11ede56cb37824e23e1eb02423eb3c4f03a39b88edf74560323b609594` /
`sha256:79b38f2c6da4ca7df25155d01361cf72ec25682d46a5b854625944035c6f9564`。

公开浏览器随后只提交 `登录流程是怎样的？`。Gateway 完成 5/5 DeepSeek HTTP 200，TLS `1/1`、reuse `4`、credential `5/5`、
unknown/retry `0`；Investigation、四份 COMPLETE Query Result、COMPLETE knowledge representation、SATISFIED Need 与覆盖失败记录、
异常和成功 session 的正确 Draft 均完成。旧 `@17` Review 仍只因 `business_discovery_recall=UNKNOWN` 返回 `QUERY_INCOMPLETE`；
terminal/Gateway summary digest 为 `sha256:2182903afd811555ed23a81609424684d6b07d8bb3877aa68540fc4554490399` /
`sha256:7349affd6d87133c46ec9bb941229c7c9190649f11c74ef2c124e1ca64f14e98`。页面失败关闭，第二题、hidden canary 与 Activation 未执行。

[FINDING-008-037](../findings/FINDING-008-037.md) 将根因归为 Review Contract 假阴性：business-discovery recall 只约束
bounded-negative claim，不能阻断由 COMPLETE 正向事实支持的行为答案。活动 identity 升级为 `1.5.9/@18/@1.4.10` 与
suite/oracle `@1.5.9`，`REVIEW-018` 同时覆盖 UNKNOWN recall 下的 negative REJECT 和 positive APPROVE；18 Case / 40 calls 与
其余 transport/compiler/budget/no-retry 边界不变。run-025 Qualification 和 run-007 freeze/grant/session 都不能复用；新 live
Conformance/Capability PASS 前没有 Product Result，也不得重试公开 Web。

`FINDING-008-037` candidate `ec2201abb96c8b2badb27835fe4508906681538d` 随后执行 run-026。Conformance 2/2 / 12/12
PASS；preflight/result/terminal digest 为 `sha256:a40590ba…b719` / `sha256:9542e5d5…f939` /
`sha256:2d36a4ba…9507`，TLS `1/1`、reuse `1`、HTTP/credential `2/2`、unknown/retry `0`。Capability freeze/authorization
digest 为 `sha256:20ffd6ed…2b13` / `sha256:ad6d3b26…0eb4`。

Capability 完整执行 40 calls / 18 Case，17 PASS、1 FAIL，tokens `83,190/2,478`；TLS `2/2`、reuse `38`、
HTTP/credential `40/40`、unknown/retry `0`。唯一失败为 positive `REVIEW-018`，其输出与 negative call 同为
`sha256:2c0317e0…c7e7`、同样 REJECT。result/closed/terminal digest 为 `sha256:5c03b738…a55b` /
`sha256:b5da8910…6fde` / `sha256:a7fbdfb5…ef3f`；授权已消费、没有 Qualification。

[FINDING-008-038](../findings/FINDING-008-038.md) 将根因定位为 model-visible wire 冲突：SATISFIED 正向 Need 仍携带
`BUSINESS_DISCOVERY_RECALL_UNPROVEN`。Application terminal compiler `@2` 现编译不可伪造的 positive/three-layer scope，并只在
positive scope 删除不适用的三项 recall 字段；原 sealed authority 与 negative Gate 不变。活动 identity 升级为
`1.5.10/@19/@1.4.11` 与 suite/oracle `@1.5.10`；新 Conformance/Capability PASS 前没有 Product Result。

clean candidate `be9ab1e56dcd62bf3e3151bd5f1beb427f25203b` / tree
`25489f35236b00402effb8f036f393130906eb84` 随后完成 run-027。Conformance preflight/result/terminal digest 为
`sha256:c5101a8b…81c7` / `sha256:eb8f728b…010a` / `sha256:651d6a93…42a7`，2/2 requests / 12/12 PASS；TLS
`1/1`、reuse `1`、HTTP/credential `2/2`、unknown/retry `0`。Capability freeze/authorization digest 为
`sha256:68c2a118…841a` / `sha256:da6fca87…9c63`。

Capability 完整执行 40 calls / 18 Case / 18/18 PASS，tokens `83,527/2,461`；TLS `2/2`、reuse `38`、
HTTP/credential `40/40`、unknown/retry `0`。`REVIEW-018` 得到预期的 bounded-negative `REJECT / QUERY_INCOMPLETE` 与
supported-positive `APPROVE`；exact positive manifest 的 completeness 只含 Query/knowledge COMPLETE，并携带
`POSITIVE_SUPPORTED_ONLY / NOT_APPLICABLE / REJECT` scope。Capability result/closed/qualification-proof/
qualification-document/terminal digest 为 `sha256:af60335e…0a46` / `sha256:cb31bbbf…83ec` /
`sha256:2b1141f3…b634` / `sha256:4111846f…8138` / `sha256:8ca137b4…69af`；Qualification ref 为
`capability-evaluation:evaluation_result_012e7e5dd9b84a1f890c823094480c64`，有效至
`2026-08-27T14:34:15.238182+00:00`。两份授权均已消费且不可 retry；V-002 PASS，下一步是证据写回后的全新 formal
product freeze/Web。尚无 Product Result，hidden canary 与 Production Activation 均未执行。

资格证据写回提交 `173da886b6a9bf16065130837a4e85350478948f` 后的 formal `run-008-freeze` 未形成 report。它在外部模型
调用为 0 的 focused 阶段以 88 PASS / 1 ERROR 停止；唯一错误是 freeze unit test 仍从 producer-relative 未跟踪 `var/` 读取
ITER-006 baseline。实际 CLI 显式提供的 accepted baseline 已先成功完成 staging，故这不是 baseline drift。按
[FINDING-008-039](../findings/FINDING-008-039.md)，测试改用 hermetic temporary fixture，formal CLI 的 exact baseline digest Gate
不变；无历史 `var/` 的 clean producer 中单项 1/1、focused 89/89 PASS。run-008 失败目录保留且不得复用；下一尝试必须使用
`run-009-freeze` 未来路径。

run-009 在纯 Git checkout 中通过 focused 89/89 与 candidate-package 37/37，随后因缺少 full regression 的受保护本机输入而停止：
只发现 1020 项，出现 8 FAIL、25 ERROR 与 1 skip。缺失输入包括五个 ignored `validation-projects/` nested repositories 和
ITER-003/007 历史 frozen evidence；它们是历史验证语料，不是产品 source。run-009 没有 report、grant、Web 或外部模型调用，目录
保留且不可复用。处置见 [FINDING-008-040](../findings/FINDING-008-040.md)。

全新 `run-010-freeze` 从 exact tracked commit `3f4e4789adea9f0dfe7c754ea3d659e6d71c9c1f` / tree
`a7a38cc457e0a42223976566a0171fd98319f35f` 装配 clean product source，并独立挂载受保护历史验证输入。正式 freeze PASS：focused
89/89、candidate-package 37/37、docs 与 unauthorized-prelisten PASS；full 1038 中 1033 PASS，只保留
`FINDING-008-020` 的 exact 4 FAIL + 1 ERROR，gate 为 `PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD`。report/deterministic
qualification/candidate-stage digest 为 `sha256:42281ade…361a` / `sha256:96a96370…7876` / `sha256:ce4d635a…886c`；source
snapshot commit/tree/manifest 为 `e65691be…341` / `330a6505…011` / `sha256:e1f4c414…247`。freeze 外部模型 dispatch、Git 发布与
Activation 均为 `NOT_EXECUTED`。

pending evaluation grant digest 为 `sha256:e3c9bed5…b082`，仍为 `live_dispatch_authorized=false`；formal report 明确
`AWAITING_USER_AFTER_CODE_FREEZE`。因此尚无 Product Result，下一 Gate 是晚于该 exact freeze 的用户公开 Web 授权；hidden canary
仍未披露，Production Activation 未执行。

前置 Conformance Gate 的 run-001 已消费其单次授权，但返回 `PROVIDER_OUTCOME_UNKNOWN`，没有形成当前 Adapter `@8` 的 PASS Result；旧
runner 仅保留 invocation，实际调用只能界定为 1—2 次且原因码不可恢复。该失败按
[FINDING-008-007](../findings/FINDING-008-007.md) 保留，不得重试或解释为 Capability/Product 证据。39-call Capability、正式 Web、
hidden canary 和 Production Activation 均未执行。

修复 observability 后的 run-002 绑定 candidate `60e1081e…` 与 preflight `sha256:86874caa…fad45`；它在第 1 次 Provider request
以 `TLS_FAILURE` 密封关闭，exact attempt count 为 1，第二次 call 未发生。该授权同样已经消费且不得重试；sanitized failure/terminal
完整保留，证明修复生效但不构成 Conformance PASS。后续必须先按
[FINDING-008-008](../findings/FINDING-008-008.md) 独立诊断 TLS，不能直接创建 run-003。

credential-free direct TLS diagnostic run-001 随后只执行一次 handshake：TCP connect 成功后，在 certificate verification 前以
`SSLEOFError` / errno 8 关闭；credential、HTTP request 与 application payload byte 均为 0。该 Result 排除了本次 DNS、TCP connect
和 CA verify 阶段失败，但没有证明远端或 direct egress 中哪一方关闭连接。下一步只能是另行授权的 frozen loopback proxy 对照，仍不构成
Conformance 或 Product Result。

credential-free proxy TLS diagnostic run-002 随后完成唯一一条 loopback CONNECT，但其唯一 verified TLS handshake 仍在 certificate
verification 前以相同 `SSLEOFError` / errno 8 关闭；proxy authorization、credential、Ark HTTP request 和 target payload 均为 0。
因此不是 proxy 不可达或仅由 Adapter 禁用 ambient proxy 导致。live qualification 进入 environment/external-state hold，TLS 路径恢复前不再
生成 Conformance freeze；本诊断同样不是 Conformance 或 Product Result。

用户关闭系统代理并声明全流量 TUN 后，credential-free TUN direct diagnostic run-003 仍只执行一次 handshake，并在 certificate
verification 前得到相同 `SSLEOFError` / errno 8；其 sanitized Result 与原 direct probe 的文件 digest 完全相同。TUN 模式声明没有形成
路径恢复证据，hold 继续生效。

更换节点后，credential-free changed-node TLS diagnostic run-004 恰好一次 verified handshake PASS；随后单独冻结和授权的唯一一次
`ark-code-latest` 最小模型诊断也 PASS，请求模型为 `ark-code-latest`，Provider response model 为 `auto`，输出符合 Adapter-compatible
strict JSON。二者证明该时点替代路由与最小调用可用，但都不是 Adapter `@8` Conformance、Capability 或 Product Result。

切回原节点后，credential-free original-node TLS diagnostic run-005 恰好一次 handshake 再次以相同 `SSLEOFError` 关闭；用户同时在
全新无痕浏览器到达同一 endpoint 的 Ark HTTP `AuthenticationError`。因此当前结论是 Python/OpenSSL 与浏览器使用的客户端/路由路径
存在选择性差异，而不是 Ark 或该节点对所有客户端整体不可用；现有证据仍不支持修改应用 Adapter。

用户随后决定更换模型 Provider。Ark live qualification 自此停止，不再生成 Ark freeze 或调用；Provider-independent 的 bounded
investigation 实现与确定性验证已经闭合。新 Provider 明确前没有新的 Product Result；后续必须先冻结其 exact endpoint、协议、模型
identity、secret 与网络边界，再从独立 Conformance 和 Capability Gate 开始，不能继承上述 Ark 诊断或已消费授权。详见
[FINDING-008-009](../findings/FINDING-008-009.md)。

DeepSeek model diagnostic run-001 随后绑定 clean candidate `8cbb3ab69871603d4cc77826eee1082e4e566f55` 与 freeze
`sha256:1c17dbe86ae42cd7f9d0d8d210ad90cf971c5d9d2d41772b2cfe3a081622c6d9`，取得只授权一个静态 strict-JSON probe 的
post-freeze user grant。runner 恰好调用一次并返回 `MODEL_DIAGNOSTIC_PASS`：请求/响应 identity 均为 `deepseek-v4-pro`，input/output
tokens 为 115/5；result/terminal digest 分别为
`sha256:42d1cacddf878d367b7eea89029563b503fbcf049f244f32e8409b9e629d27b6` /
`sha256:6202f52af2656f6b101003cc60f4b2904a1df13cf73db910444c077319c261c5`。三份执行证据 digest 与 0600 权限复核 PASS，
credential、raw prompt/response 未持久化，授权已消费且不可重试。该诊断只证明 exact endpoint/model 在该时点可完成最小调用，不是
Conformance、Capability 或 Product Result；正式 runtime 仍保持 Ark。

DeepSeek Conformance run-001 随后绑定 clean candidate `45fe1523b286f944cdc1ea781f49fe2bc5461da2` 与 preflight
`sha256:243d154eb3d89072d947a9bd678fd52786ff847cee309cbc38e9ccdef452b3a6`，取得只授权两次 synthetic request 的 post-freeze user grant。
runner 恰好调用 2 次并返回 `CONFORMANCE_PASS`：12/12 case PASS，响应 identity 仅为 `deepseek-v4-pro`，input/output tokens 为
378/87，usage 完整。result/terminal digest 为
`sha256:390378f02094d70fff4b404acc48f1ce18050761aa027d9a64d43d91f151d37e` /
`sha256:4e81b6507cc6546ca1bc54bf682a0d2fda8ad68fa03a4c17160c56ced5154261`；证据 digest、0600 权限、secret/raw payload absence、
authorization consumed/no-retry 均复核 PASS。该 Result 是 Adapter Conformance 证据，不是 Capability 或 Product Result。

同一候选零调用生成的 Capability freeze
`sha256:ad1ba1fd75739e3dcbc5e127301bb0817a3cd6b3c3258af4d86782f6d7d72551` 在独立授权前校验中因 verifier 缺少 metric contract import
触发 `NameError`。因此没有申请该 freeze 的授权，也没有读取 credential 或执行任何 39-call Capability request。缺陷和正向回归按
[FINDING-008-011](../findings/FINDING-008-011.md) 修复；修复改变 exact candidate，旧 freeze 必须保留但不得执行，后续先重新取得与修复
candidate 相同的 Conformance 资格。

修复后的 candidate `3d2f35c35efe56edce7a1938afcc8e8acbb8425b` 随后以 preflight
`sha256:3a95fe038ac8ae8b8277187c0a8ea87516fc1f5d6688878dc2908af85eec8a36` 恰好执行 2 次 DeepSeek Conformance call 并 PASS；
Result 位于
`var/iteration-008/capability/run-003-conformance-result/CC-DEEPSEEK-CHAT-NO-TOOLS-001-ccrun_bd3d72cf9895446a9dc455c81cb59bcd.json`，
digest 为 `sha256:627ff4c9329f3e09d33b3b0d6b1ec5624d33006ab189f0fc9ea8a3ad22516438`，唯一 response identity 为
`deepseek-v4-pro`。

同候选 Capability run-003 绑定 freeze
`sha256:05267d91cfe87347f48dab62f7b51c0268bf6908d9470f1fe5e075571c677ce8`，在第 25 次 Provider dispatch 以
`TLS_FAILURE / PROVIDER_OUTCOME_UNKNOWN` 密封关闭：attempted/completed request 为 25/24，completed case 为 11，无 retry。
随后以 Adapter 同一 CA fallback `/etc/ssl/cert.pem` 执行的 credential-free 对照连续 5/5 verified TLS 1.3 PASS；该诊断只校验
transport，不重试或改写 run-003。

Capability run-004 绑定 freeze
`sha256:946952576429932cd9fc8d979ad16d2d520f346d9f0a660376691063ed2c9292`，完整执行 39 次 Provider request 与 18 个 Case，
`unknown_count=0`，input/output tokens 为 88047/10249，唯一模型 identity 为 `deepseek-v4-pro`。closed Result 位于
`var/iteration-008/capability/run-004-capability-result/closed-evaluation-result.json`；result/document digest 为
`sha256:b2308facc71a051d644fbbb78f07551f840d0c1b2790610de4d86c2e46f3ccca` /
`sha256:6d698e8474c4ae3e3aa1f6705e5d7b4d2b2f6857602c7c923dedad554a11c876`。只有
`WM-JSS-I8-FIRST-CANDIDATES-001` 与 `WM-JSS-I8-DRAFT-017` PASS，其余 16 Case FAIL；Qualification 与 Production Activation 均为
`NOT_EXECUTED`。

该失败按 [FINDING-008-012](../findings/FINDING-008-012.md) 归因为 model-visible Proposal Contract 不充分：canonical operation field
shape、graph bounds、result-driven progress 和三层完整性 Review 规则没有完整进入 `prompt@4`。处置把 active contract 版本化为
`1.3.1` / prompt-vocabulary `@5`，但不修改原 18 Case、39-call、Oracle、metric、阈值或 no-retry 规则。run-003/004 作为失败证据
永久保留；新 contract 必须在新的 clean exact candidate 上重新通过 Conformance 与 Capability，不能继承本次资格。

`1.3.1` clean candidate `d9f401f290bd229f95e03853caa7e4089cf96873` 的 DeepSeek Conformance run-005 绑定 preflight
`sha256:f4dc39bdc0622f0066ee442502f587335794e7ca53d1b32ad1ca24f6a13ab71b`，恰好完成 2 次 request、12/12 Case PASS；result digest
为 `sha256:9d2aa4a2c511cb2449828888c26d314956683fba6892abd0242a1afd99bb80ae`，唯一模型 identity 为 `deepseek-v4-pro`，tokens 为
369/83，raw payload 未持久化。

同候选 Capability run-005 绑定 freeze
`sha256:5f8e06889286243ffdc4e4e3d060e800501a80bc7a1177c912f4984304386750`，完整执行 39 calls / 18 Case、无 retry、
`unknown_count=0`，tokens 为 117180/10108。closed Result
`var/iteration-008/capability/run-005-capability-result/closed-evaluation-result.json` 的 result/document digest 为
`sha256:271033468489b50107366d2cbff6e97fba3b4840f34bd6c26c8356eb96a75775` /
`sha256:aed052c6ad3db156fdb0de0b57f22e0aeb3fef7a551573917585ed3e69fadd02`。13/18 Case PASS；declared inventory、legal finish、max-four、
budget exhaustion 与 Review 五项 FAIL，所以 Qualification 与 Production Activation 均未执行。

该进展与剩余根因按 [FINDING-008-013](../findings/FINDING-008-013.md) 保留。active contract 继续版本化为 `1.3.2` / prompt-vocabulary
`@6`，只澄清 previous Result、budget、Ref copy、正/负 FINISH 和 Review taxonomy；18/39、Oracle、metric、阈值与 no-retry 不变。
完成 deterministic verification 后只再执行一轮新候选资格；run-005 的 standing authorization 已消费，不得复用。

`1.3.2` clean candidate `6e443a324d2289321457b6d828163d0dc9005300`（tree
`8ceb39e78eace1faac5280a867ebbd40a668e500`）的 DeepSeek Conformance run-006 绑定 preflight
`sha256:03d02deffe7afe7601536b68630ce98accf723799f50d7e168f1cb1815247990`，恰好完成 2 次 request、12/12 Case PASS；result digest
为 `sha256:b80972ae436dc5523b645bfb7efebc9b5c815141190f2fd7642320d8089bdf50`，唯一模型 identity 为 `deepseek-v4-pro`，tokens 为
375/76，raw payload 未持久化。

同候选 Capability run-006 绑定 freeze
`sha256:e2e40a3c7dc9ca6d82e6f38fca0d6ced2fa2384f38f4cdd17222e1977246a767`，完整执行 39 calls / 18 Case、无 retry、
`unknown_count=0`，tokens 为 126228/10227。closed Result
`var/iteration-008/capability/run-006-capability-result/closed-evaluation-result.json` 的 result/document/terminal digest 为
`sha256:85a51dc5c4182f99a9c9adaca9becbba213811d211e452b72a1d5dcda0f99692` /
`sha256:fa38bc981ed37efbe1b77642be4819e3d7cf45f0198bb50362371689356773d3` /
`sha256:884d6a35fdd3372a2af55ff206e11752ff4995385ee5d86a9f0a2b3828205cf5`。12/18 Case PASS；N candidates、result-driven batch、
declared inventory、budget exhaustion、negative complete 与 negative query-unknown 六项 FAIL，所以 Qualification 与 Production
Activation 均未执行。

该失败按 [FINDING-008-014](../findings/FINDING-008-014.md) 处置为 system-contract 架构证据，而不是继续 Prompt 重试：模型只输出
semantic intent，Application 编译 exact authority arguments；qualification 只使用产品可达 previous Result，补入正式 progress
completeness projection，并使一个 executed Result + FINISH 成为合法 2-call investigation。active contract/Strategy 已版本化为
`1.4.0`、prompt/vocabulary `@7`、policy `@1.1.0`、suite/oracle `@1.4.0`。18 Case、metric、18/18 threshold、forbidden events 与
no-retry 不变；显式合法 transition 使 fake-transport exact count 调整为 41。本架构处置没有发起新的 Provider call；live
requalification 仍待新的 clean candidate，正式 runtime 保持 Ark。

`1.4.0` 离线验证已形成：affected contract/policy/capability/product/runtime 117/117 PASS；同一个 production compiler 下的
18-case fake transport 41 calls / 18/18 PASS；full discovery 978/978 PASS、退出码 0，仅出现既有 SQLite connection
`ResourceWarning`；318 份 current documents 与 `git diff --check` PASS。这些是实现与资格输入证据，不是 Product Result、live
Capability Qualification 或 Activation。

`1.4.0` clean candidate `f056cb86b76ab3364208d9cfbba7f2562ed68688` 的 DeepSeek Conformance run-007 随后恰好
2 calls / 12 Case PASS；preflight/result digest 为
`sha256:c8e962711ce617f113e9589564b75eb00538e6e0b8506686a10394f5e1245ac0` /
`sha256:26a6460003c7f930d99c139d5813efd6046523a46a19eea25f421962c1a09bd0`。同候选 Capability run-007 绑定 freeze
`sha256:975b195a060bbc51a5376dc80af0ad551d4a8c2eb46c72a8efb1fb07d3cd64a2`，在第 38 次 request 已返回后因
model-owned search term 重复而失败关闭；37 次 request 与 15 Case 完整落盘，无 retry。failure/terminal digest 为
`sha256:82905e643b9c9968ce9d00f3b1e3f87c33a5a92d98ab24eaca4e39251ef174b5` /
`sha256:0f160da005c79fc488a1ff66b249dffe9c35788fc5b044cdeb43a84c7036a8df`，未形成 Qualification 或 Activation。

完整评审的 15 Case 为 10 PASS / 5 FAIL。按 [FINDING-008-015](../findings/FINDING-008-015.md)，活动 contract 已版本化为
capability/Strategy `1.4.1`、prompt/vocabulary `@8`、argument compiler `@2`、policy `@1.1.1` 与 suite/oracle `@1.4.1`：
Application 对有界 search term 按 casefold 保留首次顺序去重；Oracle 可预冻结有限的等价 exact projection 集合；
evaluator 不再把不同 sealed-state 样本的同名 operation 视为 cycle。本地 affected 66/66、fake transport 41 calls /
18/18 与 full discovery 980/980 PASS；新 live qualification 仍必须绑定 clean exact candidate 和全新 freeze。

`1.4.1` clean candidate `e299c097ee02dd89c404a368f070da9d546ba973` 的 DeepSeek Conformance run-008 绑定 preflight
`sha256:e031932adb843c4109a3920337d2502e406a71b28ff97d4db119388c599cb005`，恰好完成 2 calls / 12 Case PASS；
result/terminal digest 为 `sha256:e13ac784248589ec1b029a98fbe8a2515bebe8619275977d5d65b57921ba3d27` /
`sha256:a52bf779d5d4727805a359c5ee1f10b659f9e6f25de373e752e2fd6bbd073151`，唯一模型 identity 为 `deepseek-v4-pro`，tokens 为
372/84，usage 完整。

同候选 Capability run-008 绑定 freeze
`sha256:ac0f0c6e76fe7b6bed003185b74622b9af6c6d88ab4a9b04380c97440916dca1`，在第二次已完成 Provider request 后失败关闭。
`WM-JSS-I8-FIRST-CANDIDATES-001` 独立 Review PASS；`ZERO-CANDIDATES-002:call-1` 返回没有 exact `JAVA_TYPE` Ref 可绑定的
`declared_method_inventory` intent，compiler 以 `INVALID_ARGUMENT` 拒绝。attempted requests / completed Cases 为 2 / 1，
failure/terminal digest 为 `sha256:463cd849706040c44ee7f62bdfe2e37bcaa83177ea1651ac1799ea000e8e89c4` /
`sha256:7b8cdbd8ab55a5b12f8f39c665cf16597f3a8029109b21ccf32c92e722535416`；无 retry，未形成 Qualification 或 Activation。

按 [FINDING-008-016](../findings/FINDING-008-016.md)，这不是继续调整 Prompt 的依据。Adapter `@1` 没有发送或冻结
temperature，实际继承 Provider 默认值 1；Provider protocol 改为 `deepseek-chat-completions-no-tools@2`、Conformance fixture
`1.0.1`，固定 JSON numeric `temperature: 0` 并由 configuration fingerprint 与 live wire Case 共同验证。旧 `@1` Result 全部 stale；
新 clean candidate 只允许一次 run-009 Conformance + Capability 资格链。

temperature-zero protocol repair 的 clean candidate `5d2bce381e9c9495571c148a69c3fb43ee3f6dc8` 随后完成 run-009。
Conformance preflight/result/terminal digest 为
`sha256:7408d2ee7f49d4f3ff83b93321510e38003d9da4436af77f1bb0d2a485860d4e` /
`sha256:c2b999fb4c313e0913a49284ddb3783672761fd6155924f9a7154a0d6298db76` /
`sha256:197a15e21fa90d2e001db8fe0cdb1357c2abf0537adbf29cf7fd64a90bb873c1`；Adapter `@2`、fixture `1.0.1` 恰好执行
2 calls / 12 Case PASS，temperature 为 numeric 0，唯一模型 identity 为 `deepseek-v4-pro`，tokens 为 377/77，usage 完整。

同候选 Capability run-009 绑定 freeze
`sha256:d436a104be64ef22caf8f499c950863b36cecf12cede1fb4c624b14e1a6eec35`，前 7 个 required Case 均取得 independent
Review PASS。第 8 个 `ALL-SIMPLE-PATHS-008:call-3` Provider response 完成后，因 `all_simple_paths` intent 携带只适用于 direct
neighborhood 的 `BOTH_CALLS` 而失败关闭。18 个实际 request 全部 `COMPLETED`，tokens 为 46,946/1,021，identity/usage 完整；
failure/terminal digest 为 `sha256:beadc9bbca1544bebcf29620a13b98128e65bdcc9c72364515c1fc2a38e763fb` /
`sha256:99fc7923db8696f4a3a3b81ac5960459b81698737597a2a0325d82a28e4f422c`。无 retry，未形成 Qualification 或 Activation。

按 [FINDING-008-017](../findings/FINDING-008-017.md)，run-009 是该路径预提交的最终尝试。不会创建 run-010，也不会放宽 Prompt、
compiler、Oracle 或 18/18 threshold；后续 live Product Gate 等待新的显式模型或 constrained-protocol redirect decision。

该等待状态随后由用户消息
`codex-user-message:sha256:375246d919e8541021acd7b319f13d5af928794ff23a022ae01a82531a09a8e2` 明确解除。按
[FINDING-008-018](../findings/FINDING-008-018.md)，run-009 的 `all_simple_paths` 已选对 operation；错误在 Application 把只对
direct-neighborhood 有意义的固定 relation slot 当成 path 语义。新 compiler `@3` 按 operation 投影 semantic slot，Gateway policy
升级为 `@1.1.2`；相关 slot、authority 和 transition 仍严格验证。Prompt、suite、Oracle、Provider 参数、18/18 和 no-retry 不变。
run-009 Result 不改写、不 retry；新 clean candidate 必须以全新 Conformance/Capability freeze 重新资格，PASS 前不进入 Product Gate。
该 redirect 的本地证据为定向 54/54、含原反例的 fake transport 41 calls / 18/18、full discovery 982/982、current documents
322/322、diff 与 secret scan PASS；这些不替代 live Qualification。

compiler `@3` clean candidate `4e79a126faf8c6992c1649ad8f82150d69cd414d` 随后完成 run-010。Conformance preflight/result/
terminal digest 为 `sha256:60ac01be1f28d5766256fa1eb5c2996500683bb90e90dcfd90d48e7acd822a9a` /
`sha256:a145a64ba15f49a14825f95c13accb58424f6ffe2b388f2b9b82663bef82075b` /
`sha256:326bd75035792d20634f8a1ad3db550dc920532b131cbd9230c96ed5719ac056`，恰好 2 requests / 12 Case PASS。
同候选 Capability freeze `sha256:9e425d2fec706658d6574305730ff20cc37ee45a1824f0b1ac2e6eca6ec8fcfb` 无 retry 地完成
41/41 requests 和全部 18 Case，唯一 response identity 为 `deepseek-v4-pro`，usage 完整，tokens 为 105,890/2,680，
`unknown_count=0`。closed Result 只有 16/18 PASS；result/document/terminal digest 为
`sha256:47436f2f24eb39cf359dba08c1437a35c93aebe67daedd0447daf235f3d1a193` /
`sha256:341777308d364d2732c528c1d705cd9b823702c960119f4bf0980bdf65bab9dd` /
`sha256:3937818ae9f39677945592dbb6a68a685b0fc68fd1b24c1f66711779e74135ff`。没有 Qualification、正式 Web、canary 或 Activation。

run-009 的 all-simple-paths slot 反例在 run-010 已 PASS。仅剩 `MAX-FOUR-010` 第 3 回合和 `BUDGET-EXHAUSTION-011` 第 4 回合
premature FINISH，分别遗漏 direct CALLS 与 all-simple-paths；method-only `LEGAL-FINISH-009` 正确结束。按
[FINDING-008-019](../findings/FINDING-008-019.md)，这证明 Application 缺少跨回合不可变 evidence obligation 和 FINISH Owner，
不是模型 transport/identity/shape/Ref 问题，也不能用“总是多查一步”修复。

活动协议现为 capability/Strategy `1.5.0`、prompt/vocabulary `@9`、compiler `@4`、Gateway policy `@1.2.0`、suite/oracle
`@1.5.0`。Application 首轮冻结通用 operation/relation evidence ledger，后续从 ledger、立即前序 Result 和预算推导唯一 transition；
raw operation、premature FINISH 和 terminal text 均不获得 authority。当前 targeted 96/96、Gateway AF_UNIX、fake transport
41 calls / 18/18 与 current documents 324/324 PASS。允许 AF_UNIX listener 的完整测试执行面为 980/985；剩余五项均由当前桌面
Codex CLI 与 ITER-003 frozen mature-agent binary 的 exact drift 触发，已由
[FINDING-008-020](../findings/FINDING-008-020.md) 保留 fail-closed。历史 freeze/断言未改，full suite 未声明 PASS；该环境 hold 与
DeepSeek 资格链相互独立。clean candidate 和全新 live qualification 尚待完成，因此 V-002 继续 blocking。

上述实现以 clean candidate `ab87c442218a06292829c0508963508d88d54119` / tree
`190b186656fe3cd29c55d04cb8987cdeb06d5821` 进入 run-011。Conformance preflight/result digest 为
`sha256:5661c28fde972b366f89aeb92093acac703a2dbdd83dc6180325df6c4f8c43ee` /
`sha256:32ff8a4a3a45b55a229c60bfe28486937e6eb24aca3cdb587289a7db4bc1d464`，恰好 2 requests / 12/12 PASS，唯一
identity `deepseek-v4-pro`，tokens 381/79，usage 完整。Capability freeze
`sha256:f708e49f453a14959b588be3c91424dccb6f20d5320f4ab10fc6b65a4b7407f8` 的前 14 Case / 35 accepted calls 全部
independent PASS；第 36 次 Provider request 完成后，`NEGATIVE-QUERY-UNKNOWN-015:call-1` 因 raw candidate evidence 与 frozen method
ledger 不一致在本地失败关闭。failure/terminal document digest 为 `sha256:5e9d8a7199bafb8dd46deba170faf2c1f0fe0d4fd59905debc78d2f9f7bc7a6b` /
`sha256:c2847e3fc0597ae503cfc69f3353530099ef341246a1034103cb0c7c6842dbfc`；无 retry、Qualification、Web、canary 或 Activation。

[FINDING-008-021](../findings/FINDING-008-021.md) 将根因定位为 candidate discovery 的双重角色。它本来是强制首 transition，不能又是
非零候选可终止 evidence class；Application 现把 raw `implementation_candidates` evidence alias 无条件向上归一为
`method_implementations`，不加入问题/工程/Case/Oracle 特判。活动协议为 `1.5.1/@10/@5/@1.2.1` 与 suite/oracle `@1.5.1`；相关
回归 116/116（含 Gateway AF_UNIX 12/12）、fake transport 41 calls / 18/18、current documents 325/325 PASS。完整回归 980/985，
唯一五项仍是 `FINDING-008-020` 的 ITER-003 frozen CLI drift；compileall、diff check 与路径级 secret scan 通过。
`FINDING-008-021` 已处置，clean candidate 与全新 live qualification 待完成，V-002 继续 blocking。

上述实现以 clean candidate `5ef09d4f29f538fc40985613c963d9c29bd2ee15` / tree
`f912744582d4864c26697295668a9560a07f21d1` 进入 run-012。Conformance preflight/result digest 为
`sha256:51d892770d777073e3337e074122b22acc6954610a1d5e357e73894a9442ecec` /
`sha256:f50ea41a6ec5502df6a7cc90e840d52e3474b5f78b3c593e0f58672f8b69715c`，2 requests / 12/12 PASS，唯一 identity
`deepseek-v4-pro`，tokens 376/86，temperature 0、thinking disabled、usage 完整。Capability freeze
`sha256:4964298813d036ee59e2ffec7fd9013a88e4d16ac557c1703c4ca4ec5bd61d93` 的前 9 Case / 21 calls 全部 independent
PASS；第 22 次 request 完成后，`MAX-FOUR-010:call-1` 因 raw method evidence 与 frozen outgoing-direct ledger 不一致失败关闭。
failure/terminal digest 为 `sha256:58c1a33c3fb458db0dd592c1871072dac6a6ec815f7aaba5ca57350ed8d9382a` /
`sha256:fabb08a4731f4d2d6d5b8f1890f203e887048229c57e9edec29f149dd7b03f4c`；无 retry、Qualification、Web、canary 或 Activation。

[FINDING-008-022](../findings/FINDING-008-022.md) 证明 method Result 已包含带 Support/Coverage 的 exact outgoing `CALLS`；standalone
outgoing direct 是重复 evidence alias。Application 现按 formal relation 收敛到 method，path/incoming/both 不变，不加入题目或 evaluator
特判。活动协议为 `1.5.2/@11/@6/@1.2.2`、suite/oracle `@1.5.2`、closed evaluation `@1.0.2` 与 18 Case / 40 calls；
相关回归 169/169、fake transport 40 calls / 18/18、current documents 326/326 PASS；完整回归 980/985，唯一五项是
`FINDING-008-020` 已隔离的 ITER-003 frozen CLI drift。compileall、diff check、路径级 secret scan 与 System Contract fileset 重算
通过，`FINDING-008-022` 已处置；clean candidate 与全新 run-013 live qualification 待完成，V-002 继续 blocking。

上述实现形成 clean candidate `a93666ce51f24149a487581a3c12283691cbd14b` / tree
`e3ffdb9d72aa1202a6029a5202db20af3178ad8b` 并完成 run-013。Conformance preflight/authorization/result/terminal digest 为
`sha256:38a95bcddae1bbb03de98c419d8577cd98903560ecbca681524b2379f9ce467e` /
`sha256:1c0225c7420bcea9634a805bc1a1181a73f29ed28c8906bce5ce569f8bb6d1cf` /
`sha256:8505983e13d9e2ab4ec9fbeec6b92b2cc9369fb89f921582457fd8703146c2c1` /
`sha256:cb4cd8efd219e18ea88d0a78ae6f34cb5410daa38863e96780ef18dd393fb6ad`；2 requests / 12/12 PASS，唯一 identity
`deepseek-v4-pro`，tokens 374/86，temperature 0、thinking disabled、usage 完整。

Capability freeze/authorization/result/closed-document/qualification/qualification-document/terminal digest 为
`sha256:11524d4c219c13c8593cbdfb499e2b23c809b3cfdcf56eb4e06d3adddf9b469b` /
`sha256:d56412847278bdf15ba59522dede32c4eebfb6594c7a7271616ebd6a3f602fbb` /
`sha256:b05583d6edf669008253618c0bd3cd2c872da037da33a8dacae3c46f2ee1ca25` /
`sha256:e8995c818c48734b186b20019d3077303fe88928ab025b64cf7420399755e352` /
`sha256:61f18bd62d217ad68ac778a5aa4e8537eff180f4009067a75c8e2c011102a0c1` /
`sha256:b2fcb7e4f26256a369c7d5ae9bad63f2e049bfdba4ae13c6cb35ae4d45a79109` /
`sha256:e5200a15709585be50f6cb4c56a5f3ff7087f0e53bc8483518a58bc48cdab7fd`。40 requests / 18 Case 全部执行，18/18
independent PASS、failure/unknown 为 0，唯一 identity `deepseek-v4-pro`，tokens 103471/2909、usage 全部完整；same-authorization retry
为 false，hidden canary、正式 Web 与 Production Activation 均未执行。资格有效至 `2026-08-27T05:19:50.677774+00:00`；V-002
转为 PASS，后续 product/runtime、Source-off、security、公开 Web 与 early canary Gate 仍 blocking。

run-013 后的产品接入审查形成 `FINDING-008-023`：其 DeepSeek Capability 不能喂给仍固定 Ark 的 bounded Gateway。活动实现按
`VOLCENGINE_ARK → DEEPSEEK` 在 dispatch 前选择 current exact qualification route；本轮密封 DeepSeek，且任何 request dispatch 或
outcome unknown 后都禁止跨 Provider retry。DeepSeek 获得与历史 Ark 相同等级的 exact endpoint、selected credential、preconnected
socket、TLS/SNI/certificate、response cap、4—6 call 与 unused descriptor 审计；未选择的 Ark credential/socket 不进入角色环境。

该 product egress policy 变化属于 Capability Contract 明列的 Gateway connection policy 变化。资格加载器现要求 Definition 绑定
`ITER-008-BOUNDED-JAVA-SOURCE-SEMANTICS-MODEL-EGRESS-GATEWAY@1.3.0` 的 exact digest 和 DeepSeek Adapter `@2`，因此 run-013
只保留为 Strategy 能力与 Finding 证据，不能授权新 product candidate。新 Conformance/Capability Result、正式 product freeze、Web、
canary、Agent 对照、Reflection 与 Activation 均尚未执行。

route candidate `5ffb6ef1def72be56c3343d2fc97a4398208fd16` 的 run-014 Conformance preflight/result digest 为
`sha256:7ad47dcd17262fc1f79610b79e4e5b16756d4749ea0b0d1a3204040d131dc104` /
`sha256:58881d22757b91d31422e55705c32ea76eed6659840db29b94e63cffd58a839a`；2 requests / 12/12 PASS、唯一 identity
`deepseek-v4-pro`、temperature 0、thinking disabled、usage 完整。随后 Capability freeze
`sha256:e3424e6515a72d61a97f5b015ef6bf3814c523b23743b0eb9831d1fa253a998c` 在前 3 Case / 3 requests PASS 后，第 4 个
独立 TLS session 于 certificate verification 前失败，以 `PROVIDER_OUTCOME_UNKNOWN` 密封。该授权已消费且没有 retry。

网络恢复对照后形成的独立 Capability run-015 freeze
`sha256:157a4dfc61cd5e0d9cc3f1e57450e55bdef3f627954f4882075d1e7bf465c6e4` 复用仍 current 的同候选 Conformance，并在前
5 Case / 9 requests PASS 后，于第 10 个独立 TLS session 发生相同失败。第二份授权同样已消费、没有 retry，不能与 run-014
拼接为 closed qualification。credential-free TLS 对照首组 4/5、后续带间隔 12/12 verified TLS 1.3 PASS，成功连接 certificate
digest 一致；一个 verified TLS connection 上的两次无凭据 HTTP request 均得到预期 401、`Connection: keep-alive` 且
`will_close=false`。这些对照不是模型调用或 Capability 证据，但把重复故障定位为当前 TUN 对大量独立 TLS session 的间歇 EOF。

`FINDING-008-024` 将 direct 与 pinned DeepSeek transport 改为同一授权 run 内的 persistent verified TLS：最多 3 次
credential-free acquisition，成功后才解析 credential；HTTP dispatch 后仍绝不 retry。正式资格 Result 新增 TLS attempts/successes、
certificate、HTTP dispatch、reuse、credential resolution、post-dispatch unknown 与零 retry 证据；product Gateway 预置 3 个
descriptor 并分列 consumed/unused-close。Adapter/fixture/Result/egress policy 分别升级为 `@3` / `1.1.0` / `@2` / `@1.4.0`。
旧 run-014/015 永久保留为失败证据。当前实现的核心 50/50、跨模块 89/89、Gateway 13/13、`compileall` 与 diff check PASS；完整
执行面 1010/1015，唯一五项是 `FINDING-008-020` 的历史 exact runtime drift，因此不冒充 full-suite PASS。新 exact clean candidate
与 live Conformance/Capability 尚未完成，正式 product freeze、Web、canary、Agent 对照、Reflection 与 Activation 继续阻断。

上述 persistent 实现随后形成 clean candidate `139e61c94f218a6076022f1863cf871b2d3104f2` / tree
`efb2cd48b6fb02365ab2a2544f3a5e9adec890cf` 并执行 run-016。Conformance preflight/authorization/result digest 为
`sha256:6af24a38abc6292787f7abc2f714669827877b2c6ddf85150d0a1480fbaba63a` /
`sha256:be4747138d0a3c46e65c0e645db22ea1d4d60156c7e346ef810d2dc52d7e84ee` /
`sha256:9e035d75899140ecb02f5513666b16ff09f72f5490ff8c259201353aa8c1d83b`；2 requests / 12/12 PASS，唯一 identity
`deepseek-v4-pro`，tokens 373/75、usage 完整。transport 只取得 1 个 verified TLS session 并复用 1 次，HTTP/credential 各 2 次，
unknown/retry 为 0。

Capability freeze/authorization 为 `sha256:63151e87fc13d241b1586429276dfd8269af8c9f59f10f9b09e67e263c13f43d` /
`sha256:886488fabd2d88a3492544e1c6e44fb4e1f7cebb2febab318166fef57506d514`。前 6 Case / 12 calls 全部 PASS；第 13 次已完成
request 在 `WM-JSS-I8-PATH-EXISTS-007:call-1` 选择 `method_implementations(OUTGOING_CALLS)`，与 frozen `path_exists` obligation
不一致，runner 以 `QUALIFICATION_INVALID` 失败关闭。failure/terminal digest 为
`sha256:b698c9820a8f4770d7b49b158038e01378ca263afc83ac660732c9977ad95f64` /
`sha256:e85fb34aca3ee21cedc3486d78c270c749fa4923c355026de017f74b98761d42`。失败时 transport 仍为 TLS 1/1、reuse 12、HTTP/credential
13/13、unknown/retry 0；因此不是网络回归。授权已消费，没有 Qualification、Web、canary 或 Activation。

[FINDING-008-025](../findings/FINDING-008-025.md) 保留 exact 输出证据：模型识别 `reach/path`，却选择 method evidence，并把 prompt
示例中的 `direct/all/method/implementation/candidate` 当作 search terms。旧 DeepSeek wire 将 Adapter schema 与 Gateway semantic
prompt 分成两个 system turns。当前候选不放宽 ledger/evaluator、不读取问题/Case/Oracle，而是将两项 authority 合并为一个 leading
system message，并以通用 prompt 明确 capability section isolation、example-only terms 与 reachability precedence。活动身份升级为
Adapter `@4`、Conformance fixture `1.2.0` / Result `@2`、capability/Strategy `1.5.3`、prompt/vocabulary `@12`、policy `@1.4.1`、
suite/oracle `@1.5.3`；本地门禁与全新 live qualification 尚待闭合。

上述候选随后形成 clean commit `e3cc34fdd830498414480684151944139ca9489c` / tree
`0d83e59ed273c2f6c01dba977f2089576eda2da2` 并执行 run-017。Conformance preflight/authorization/result digest 为
`sha256:7dbff2868c58e8582e44e3fd989282430dc762d13c529607ab6f4a0a3c2a9dad` /
`sha256:901b6a9158beae9fab35f921e6617939859908d5349c67a2d62fbaba7ea96875` /
`sha256:f17c58dd13ece22e3bf7da216119fb2e00d552fed7bd31e9bec23accb98d02f4`；2 requests / 12/12 PASS，唯一
identity `deepseek-v4-pro`、tokens 407/68、usage 完整。transport 为 TLS 1/1、reuse 1、HTTP/credential 2/2、unknown/retry 0。

Capability freeze/authorization 为 `sha256:38d07801b13fa581fc7d82120cc1bd319202862b76a79b044895b2a96fb86deb` /
`sha256:d4f9518043a0c6c030e3a74b60267f50216f43efb5ebd4d69dd35216f41dad2f`。run-016 失败的 PATH-EXISTS Case 已完整
PASS；前 9 Case / 21 calls 后，第 22 次 completed request 在 `MAX-FOUR-010:call-1` 把 workflow trace 选为 binary
`path_exists`，并在原问题之外复制 `order/return/throw/audit`。failure/terminal digest 为
`sha256:9877b420f138743bb948c2f9e02f5d7095863ab86678a3acf3b191994364793d` /
`sha256:c1c50229d3dbc5b6e5f5803532aa68c67c53b1d7fc69689ad24b64e709705a59`。失败时 TLS 1/1、reuse 21、
HTTP/credential 22/22、unknown/retry 0；授权已消费，没有 Qualification、Web、canary 或 Activation。

[FINDING-008-026](../findings/FINDING-008-026.md) 将首次偏差定位为 capability 输入隔离：`@12` 每次实际发送完整 monolithic
prompt，非 Investigation section 虽被声明 inactive，仍与当前指令共享一个 system authority。活动 Contract `1.5.4/@13` 为三个
capability 冻结独立 prompt entry，并在 Manifest 前按 sealed stage 选择、绑定 `capability-prompt-selection@1`；Gateway/live runner
校验所选 digest。只有显式 binary reachability 使用 `path_exists`，workflow trace 使用 method evidence。policy/suite/oracle 升级为
`@1.4.2/@1.5.4`；Adapter `@4`、fixture `1.2.0`、compiler `@6`、18 Case / 40 calls、Oracle、18/18、persistent TLS 与
no-retry 不变。相关回归 121/121、fake 40-call / 18/18、docs 330/330、compileall/diff/secret scan PASS；完整执行面
1012/1017，唯一五项仍为 `FINDING-008-020` 的历史 drift。System fileset digest 为
`sha256:0143229ee22d1db3962e6bc6fedf7982fea96642fe84d1f116667f3b144219a5`；新 live qualification 尚待闭合。

`1.5.4/@13` candidate 随后形成 clean commit `51c8ac369b29b609d6a5dcf53f55370a0cb49f04` / tree
`10abd04fd45fdd13a156fac9349a7a6e21690d8b` 并执行 run-018。Conformance preflight/authorization/result digest 为
`sha256:5e1d00112eb592e68b3e8861c1a99a8d88d83b38e0456e05badc436d3b477934` /
`sha256:eb8b08aea2f44cafb0fbbfef4ceabb35160cf7dc4d6e7851ae366d728f6341c2` /
`sha256:e5ac81e07a36badc53c34699e262168b2ca2052d1503d9d25e2ea71eb37f4727`，2 requests / 12/12 PASS。Capability
freeze/authorization digest 为 `sha256:93cef5a0c2315ed6bc603ee6a9ae5a327a120d5bb3781010f85f8d3f75ac059d` /
`sha256:b41bad4b7a56553b9601b102cc856a7db3c35b8157a5cb13671dbe860b9f3d2a`；40 calls / 18 Case 全部完成，TLS 1/1、
reuse 39、HTTP/credential 40/40、unknown/retry 0，input/output tokens 73,874/2,584。closed result 为 16/18 FAIL，
result/document/terminal digest 为 `sha256:6cd3f4f8…2459e` / `sha256:4fe292ac…99f04` / `sha256:39a86a2d…8cbf2`。

两个失败均只有首轮 `SEMANTIC_CONSTRAINT_NOT_SATISFIED`；operation、typed projection、第二步 candidate binding 和 exact Ref
provenance 均 PASS。REF-PROVENANCE 遗漏了原问题明确包含的 `implementation`；RESULT-DRIVEN-BATCH 的输出已覆盖原问题概念，
旧 suite 却要求未请求的 `return/throw`。按 [FINDING-008-027](../findings/FINDING-008-027.md)，活动 Prompt 改为 question-origin
check，System Capability Evaluation 禁止把一种可能执行机制当成唯一等价表达；活动身份为 `1.5.5/@14/@1.4.3`、suite/oracle
`@1.5.5`。operation Oracle、18 Case / 40 calls、18/18、Adapter `@4`、compiler `@6`、persistent TLS 与 no-retry 不变。
System fileset digest 为 `sha256:948647ad…7aaa4`。run-018 不重评、不 retry，也没有 Qualification、Web、canary 或 Activation；
相关 117/117、fake 40-call / 18/18、docs 331/331、compileall/diff/secret scan PASS；完整执行面 1013/1018，唯一五项仍为
`FINDING-008-020` 的历史 drift。当时新 live qualification 仍 blocking。

新 identity 的 exact candidate `6dc7a9e4…` / tree `229d11d1…` 已完成 run-019。Conformance
preflight/authorization/result/terminal digest 为 `sha256:18cc7ea9…4d3` / `sha256:c36214d5…6ebb` /
`sha256:c3ce9386…120c` / `sha256:507ef676…dc6a`，2 calls / 12/12 PASS。Capability freeze/authorization/result/closed/
qualification proof/document/terminal digest 为 `sha256:a7e99c16…386e` / `sha256:e2a11233…93ee` /
`sha256:16e9e6bc…5020b` / `sha256:17422796…42528` / `sha256:7e460107…224fc` /
`sha256:b0ec3ad1…e556` / `sha256:a1cd6fb6…981f`，40 calls / 18/18 PASS。两阶段 transport 分别为 TLS 1/1、reuse 1/39、
HTTP/credential 2/2 与 40/40、unknown/retry 0；Capability tokens 为 78,618/2,602，有效期到
`2026-08-27T09:09:31.851862Z`。

run-018 两个失败 Case 在 run-019 均 PASS：RESULT-DRIVEN-BATCH 只返回 question-owned flow concepts，REF-PROVENANCE 保留 explicit
`implementations/candidate` 并继续 exact 绑定第二步 Result/Refs。全部 freeze/authorization/result 核心文件为 0600，secret scan 无命中；
授权均已消费，没有 hidden canary、Web 或 Activation。该证据形成 current Capability Qualification，不是 Product Result；下一步只能
生成新的 formal product freeze 并执行公开 Web Gate。

正式 freeze producer 审查随后形成 [FINDING-008-028](../findings/FINDING-008-028.md)：旧 `@1` 资格只能表达 raw full-suite PASS，
与 `FINDING-008-020` 必须保留的五项 historical exact-runtime hold 构成永久死锁。当前 bounded route 已升级为 deterministic
qualification `@2`，精确复核五个测试各执行一次、4 FAIL + 1 ERROR、V-009/prepared-binary marker 和“其余全部 PASS”；通过时仍
记录 raw `full_regression_pass: false`，gate status 为 `PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD`。任何新增/不同失败继续阻断，且
该状态不能推导 canary、Acceptance 或 Activation。parser/runtime/authorize 定向 19/19 PASS；首次 full 1023 项执行在 System Contract
刚写回而 manifest digest 尚未重算时得到 1017 PASS / 5 FAIL / 1 ERROR，其中新增的 ITER-007 readiness digest failure 被 gate 正确拒绝。
ITER-008/ITER-007 fileset 随后重算为 `sha256:80b5393b…b311` / `sha256:3f25570e…4819`，正式 full gate 尚须重跑。
最终定向 parser/runtime/authorize 22/22 PASS；完整执行面重跑 1026 项，1021 项通过，raw exit 1，唯一 4 FAIL + 1 ERROR 精确为
五项 preserved hold。结构化 gate status 为 `PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD`，stdout/stderr digest 为
`sha256:f9b8e964…73e0` / `sha256:76a79e6d…5e27`；该结果仍不冒充 raw full-suite PASS，下一步是 clean commit 后生成正式 product
freeze。

formal product `run-001-freeze` 随后以 `SWM-ITER-008-SLICE-001-CANDIDATE-FREEZE@2` PASS；report document/raw digest 为
`sha256:dd8839fa2df177b048dbec2828249437810226d3b0d26baa8ccf65ef761fb7fd` /
`sha256:2597dd156ddeaf1e60860fb3ae7d12e79cb5697e1a832985426dc78abcf0fdd3`，deterministic qualification digest 为
`sha256:71c1ecb83aa481b218ab3fd865565132b0f3e220584a2b5d2ab9105204678c83`。raw full regression 仍为 false，exact historical-hold
gate、87 focused、36 package、1026 full、docs、unauthorized-prelisten 均 PASS；freeze 阶段模型 dispatch、hidden canary 与
Production Activation 均为 `NOT_EXECUTED`。post-freeze evaluation grant digest 为
`sha256:483257f4e97228601bdc98180695525b1bdd196d691eb2c26a39cd2147f6df24`，只授权 DeepSeek EVALUATION_ONLY route。

该 freeze 的第一次正式 Web 请求 `登录流程是怎样的？` 没有形成产品答案。唯一模型 call 成功完成 TLS/HTTP/JSON，并返回
`implementation_candidates`、search terms `登录/流程` 与 `method_implementations` evidence；Answer 随后失败，Web 返回 502，terminal
document digest 为 `sha256:1cca15fad283152f9594565bf432bea110bfd2d4472529e078ee0cef32c14f0f`。运行只消费 1 Provider call，
selective retry 0、Source/Update/Direct/Citation/Activation 0。exact sealed replay 将首次偏差定位为 ASCII-only Query tokenizer，
不是 DeepSeek availability 或 shape failure；详见 [FINDING-008-029](../findings/FINDING-008-029.md)。因此该正式 Web Result 为 FAIL，
run-019 qualification、run-001 freeze/grant 和失败 session 均被新 `1.5.6` identity 永久失效，不能继续下单题或 hidden canary。
本地处置随后以相关 128/128、fake 40 calls / 18/18、docs 333/333 和完整执行面 1022/1027 闭合；完整回归唯一五项仍精确属于
`FINDING-008-020`。这些是新 identity 的 deterministic candidate evidence，不是 live Qualification 或产品重试结果。

`1.5.6/@15` 的 exact clean candidate `5bdf83b3931f2aa9f3065f23593c4e0bf3da7030` / tree
`b7f69fbff52d54216050c73157a865d5d57b8b13` 随后执行 run-020。Conformance preflight/result digest 为
`sha256:3afe56e2ce253b30f81494d1cafea2b1a2fe43c42a4696ea4b9b899cc70cddba` /
`sha256:e20eef6cad6267fc9ef203c7cfc136f4f8537ef6b0c74a652b5ed1ecaa00c0eb`；2/2 calls PASS，TLS 1/1、reuse 1、
HTTP/credential 2/2、unknown/retry 0，valid until `2026-09-19T10:17:22.817950Z`。Capability freeze/authorization digest 为
`sha256:07982a4e689f3eeac7ddd5cb5eb7828b60200428019dba530d397fae3f6c02f4` /
`sha256:49925d394f7c35391d048fd151d08d82a020e1e8c4baf377e3807c9712d32722`。

Capability 前 13 Case / 32 calls 已完成，第 33 次 Provider request 也已成功返回，但第 14 Case 在本地 evidence obligation exactness
校验以 `QUALIFICATION_INVALID` 停止。failure/terminal digest 为
`sha256:b227f51378b7d5cfb94f13853d662949fce19a47a27b1b61a3b890d5dc2ed445` /
`sha256:011425a39a26d9bbdcde4c1cf03d1660af2765337bd9444208aae652b5682a1d`；TLS 1/1、reuse 32、HTTP/credential
33/33、unknown/retry 0。中文 Case 已给出 `invalid/credential/authentication/exception/log/success/return/session`，旧 evaluator
却只接受 `record|audit`；Case 007/012/013 省略被 operation/topic 覆盖的显式 term，第 14 Case 则把 implementation existence 错选为
`path_exists`。按 [FINDING-008-030](../findings/FINDING-008-030.md)，活动 identity 已升级为
`1.5.7/@16/@1.4.5` 与 suite/oracle `@1.5.7`。run-020 永久 FAIL、授权不可 retry，没有 Qualification、formal product、canary 或
Activation；新 live qualification 仍 blocking。本地相关 115/115、fake 40 calls / 18/18、docs 334/334 与完整执行面
1022/1027 已闭合；唯一 4 FAIL + 1 ERROR 仍精确属于 `FINDING-008-020`。

`1.5.7/@16/@1.4.5` 的 exact candidate `0e6b60f166e37e1397c483260ee70b6ad9f91cb8` / tree
`9c24a0eb2ae552131a26b651296f791ebe27daba` 随后执行 run-021。preflight/Conformance authorization/result digest 为
`sha256:4b1675d55c1e387876cf512258c99978527cf53079acc373e936c5656491bfd4` /
`sha256:23bda2528122855768b0c0045d3f4f9fa1420ac7457feb9ec9e451a2faee106f` /
`sha256:bc28d3d358bcff18487a098480a8a94fcae1827d2ae539ad0d284ea8b2126813`，2 calls PASS。Capability
freeze/authorization digest 为 `sha256:732fbdc3e75b951cc1397fc68334ac40e7ff1b7f4cfe616ccdbd6deeedb29158` /
`sha256:ce4ee5b4b8678318c401292ac1a0936ebc79e400f48b46e1b08ee52c94fd635e`。

Capability 无 retry 完成 40 calls / 18 Case，15 PASS、3 FAIL、unknown 0；result/document digest 为
`sha256:4757153bab4b9ce1b5bd7c616cdbc5934686539ae70723f376e6ca7247d7d60e` /
`sha256:6096b6b3be57d4dd3083c65d3408b655eb11415a5f4047485ff3e2bfb862437e`。两阶段 transport 均为 TLS 1/1，Capability
reuse 39、HTTP/credential 40/40、unknown/retry 0。此前中文 Case、014—016 和全部 later-step typed transition 已 PASS；三个失败只
来自首轮 lexical coverage，模型分别把 `reach/method/implementation` 交给 operation/evidence request 表达而没有保留在
`search_terms`。

按 [FINDING-008-031](../findings/FINDING-008-031.md)，上游 `1.5.7/@16` 与 suite/oracle 不再调整；DeepSeek Adapter 升级为
`@5`，以 schema-scoped、无题目/Case/具体词例、无 response post-processing 的 wire adaptation 保持该字段自己的语义，policy
升级为 `@1.4.6`。run-021 及其授权永久 FAIL/consumed，没有 Qualification、formal product、canary 或 Activation；新 clean
Conformance/Capability 仍 blocking。

`deepseek-chat-completions-no-tools@5` 的 exact candidate `c925496f5ae752f93c92f49e4aeae0bc0ac7be8a` / tree
`e82ad3c809e027f8b94a9f1430216fc6025e3d1b` 随后执行 run-022。preflight/Conformance authorization/result/terminal digest 为
`sha256:0799476577f8fb40b95a351cedeeec045972c942959f6e3d34336478df9ff67a` /
`sha256:24fb1890502de9eae4061eeb0b8012afb86ea769eb47eefbf9c0ff3d6c7bcac0` /
`sha256:f1ca95cad091efef15960e29a0ce7f196540b70ae318c7906a48254a6afc31bb` /
`sha256:ddced0061202015a2246833755a36cbe790e510d767691aa816b0aa5e242b18e`，2 calls / 12/12 PASS；TLS 1/1、reuse 1、
HTTP/credential 2/2、unknown/retry 0，valid until `2026-09-19T10:54:56.247888Z`。

Capability freeze/authorization digest 为 `sha256:b1003abf30ae9a7a13c3bbe54b16df76fdd7c34843aa47dbf710a52c7dfd73ef` /
`sha256:722fc1064e0200f602fd5d6b9685767cfb079319986d86c6d9b1e95bc0f1ca5a`。运行完成 40 calls / 18 Case，16 PASS、2 FAIL；
result/closed-document/terminal digest 为 `sha256:e47b0ade3ce8571c29f263c41e70fbf8711ad3fcfd3a34ceb6b9bfd1562dfc1c` /
`sha256:49a22c816f9ae074fb517e1dbeef2cd5bd651bfa7bea753558a27d07fb2d339d` /
`sha256:1de7e3870666df154f012324bfbfec5404d32c983e510567dcded5e09ef636ad`；TLS 1/1、reuse 39、HTTP/credential 40/40、
unknown/retry 0。PATH-EXISTS 已 PASS；CYCLE-PROGRESS 的 12 个认证 normalization 仍遗漏 `methods`，REF-PROVENANCE 仍遗漏
`implementations`。没有 Qualification、formal product、canary 或 Activation；授权已消费且不可 retry。

按 [FINDING-008-032](../findings/FINDING-008-032.md)，`FINDING-008-031` 的 Adapter-owned disposition 已被取代。活动 Application
compiler 升级为 `@7`，以 closed deterministic merge 优先保留 direct ASCII question terms，raw model output/digest 不变，cross-script
translation 仍由模型负责；DeepSeek Adapter 移除领域 adaptation 并升级为 `@6`，policy 升级为 `@1.4.7`。上游
`1.5.7/@16`、suite/oracle `@1.5.7`、18/40/18/18 与 no-retry 不变。本地相关 127/127、fake 40-call / 18/18、docs 336/336
PASS；完整执行面 1024/1029 的唯一 4 FAIL + 1 ERROR 仍精确属于 `FINDING-008-020`。新 clean Conformance/Capability 仍 blocking。

上述处置形成 clean exact candidate `837171e611ae6e1dd3a0939e446e0658b1d08d6c` / tree
`11b4a2a083d1e1c0f239e0a132e61cd125cd12ec`，并执行 run-023。preflight/Conformance authorization/result/terminal digest 为
`sha256:c7c730f556e994c7b3278a35104c47a631e46dd84997122f95c1133783813703` /
`sha256:fbc6a8c70f7d3b6bd19f17e636591459bc10c0ac700b1450838b3ee94264b93c` /
`sha256:16e947ad1aaf698227ae59f06db3ec53caca04eb9f1c46375adf6ae1bd960522` /
`sha256:5eb114c04f745b46137c4408ed16788be92d7979f0e4c1630a9b33ac342077fb`。Conformance 恰好 2 calls / 12/12 PASS；
requested/actual model 均为 `deepseek-v4-pro`，temperature 0、thinking disabled，input/output tokens 398/64；TLS 1/1、
reuse 1、HTTP/credential 2/2、unknown/retry 0。

Capability freeze/authorization digest 为
`sha256:7bfd08c6307314a15b7f0d41e666d559154f7906c9818f4296ac5937fb724cae` /
`sha256:fdf3e0e23cc7010225e9d3e952dbc6390e051e7cc63578744d25bbb37ec0b43d`。无 retry 地完成 40 calls / 18 Case / 18/18
PASS，input/output tokens 84,396/2,560；TLS 1/1、reuse 39、HTTP/credential 40/40、unknown/retry 0。result/closed-document/
qualification-proof/qualification-document/terminal digest 为
`sha256:9306f487e79b4594154dd60e8dd55854cc9289b2ce057ed5fea0851baf03ba6d` /
`sha256:d17e6d67aa1ad8eeb0ac320d227faa4003094fc7ff098d72658758c19a62d977` /
`sha256:0c78cb15260a57ceac7d61c9cdcb9301c16854240d52b2186a5d77c4932f0c31` /
`sha256:15f4d4f19bd7acf6183e44db6b5cfa0721ae2b4888bc31718528a8fe4aa148ba` /
`sha256:c2175a9b2d200cf559f855267b8b3a438aa8eaf5472658c141426e2acd525563`。Qualification ref 为
`capability-evaluation:evaluation_result_8f299a82dbdc4d67bda87c77bde013b1`，validity ref/digest 为
`evaluation_validity_626049896a934beab53cad3737f40509@1` /
`sha256:dceb274443a5a415adee1baa39759208dd3930a3afc45c30fec2bca04c825fc7`，valid until
`2026-08-27T11:28:37.309517+00:00`。

全部 18 Case 均 PASS。其中 CYCLE-PROGRESS 首轮保留 `methods`，REF-PROVENANCE 保留 `implementations`，
PATH-EXISTS 保留 `authentication/reach/session/issuance/static/calls`；这些 Case 的 semantic constraints、typed operation 与
projection 均 PASS。authorization 权限为 0600，credential-shaped secret scan 无命中，两份授权均已消费且不可 retry。
hidden canary 未披露，Production Activation 为 `NOT_EXECUTED`。run-023 因而关闭 V-002，但不是 Product Result；
下一步是从证据写回后的 clean producer 生成绑定该 qualification chain 的 SLICE-001 formal product freeze。

未来必须先为 SLICE-001 形成绑定 early canary、early Agent 对照和 `V-REFLECT-001` 的独立 Result；只有产品 Case PASS、复盘完整、
`reflection_decision: CONTINUE` 且用户另行授权，才允许执行 SLICE-002。最终 Product Result 再聚合两个 Slice Result，不能覆盖
前一段的证据或失败。

每个 Result 必须绑定 exact product code freeze、Snapshot/Bundle、对应隐藏 project/suite、成熟源码 Agent baseline（若适用）、
正式 Web 现场题、逐 Case verdict、模型/工具预算和 Source/Update/Direct audit；若产品失败，按 `failed-preserved` 保留，不得创建
Acceptance。

每个 Slice Result 还必须包含 `Architecture reflection and continuation decision`，记录假设/实际、问题分类、四层架构复核、成熟
方案对照、Finding 去向和下一风险。每个当前 Slice 已到期的假设都必须有 Expected、exact Evidence、Verdict 与 Impact；最终
Result 覆盖 A1—A8，并分别填写偏差分类、
Source→Snapshot→Query→Trace→Draft/Review→Web 诊断、替代方案/下一风险和决策理由。`reflection_gate_status: PASS` 只说明复盘完成；
是否继续由独立的 `reflection_decision` 决定，并必须绑定 `reflection_decision_ref` 的 exact 用户消息。最终 Product Result 还必须
报告正向价值 actual/unit/direction/threshold 与 exact replay report digest；只写 `PASS` 无效。
