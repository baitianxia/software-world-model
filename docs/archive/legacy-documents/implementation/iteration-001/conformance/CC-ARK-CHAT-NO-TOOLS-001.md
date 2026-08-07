# CC-ARK-CHAT-NO-TOOLS-001 — Volcengine Ark Adapter Conformance Fixture

| 元数据 | 值 |
|---|---|
| Fixture ID | `CC-ARK-CHAT-NO-TOOLS-001` |
| Version | `1.6.0` |
| Status | `Live PASS — Coding Plan @8 Current` |
| Target Profile | [SWM-ADAPTER-ARK-CHAT-001@1.3.0](../contracts/ITER-001-Volcengine-Ark-No-Tools-Adapter-Profile.md) |
| Adapter | `openai-chat-completions-no-tools@8` |
| Model Reference | `glm-5-2-260617` |
| Validation Type | Contract Conformance；不是Capability Evaluation或Product Holdout |

> 2026-08-07已在Coding Plan Base URL上完成@8真实运行，12项Case全部PASS。旧结果因Adapter、实现或配置指纹变化失效；当前资格只由下列@8 Result提供，且仍不等价于业务能力评估或产品验收。

## 0. 当前真实运行记录

| 字段 | 值 |
|---|---|
| Run ID | `ccrun_66bbedf18020445c9df5fac11526fda1` |
| Outcome | `PASS / LIVE_CURRENT` |
| Requested Model | `glm-5-2-260617` |
| Actual Model | `glm-5.2` |
| Request Count | `2` |
| Usage | Input `318` / Output `72` tokens |
| Result Digest | `sha256:dee384a90d89193952a83959ba9e9fed9e07faa2edbfabf13b094f47d740668f` |
| Valid Until | `2026-09-05T21:04:18.073701Z` |

结果文件为`var/conformance-v8/CC-ARK-CHAT-NO-TOOLS-001-ccrun_66bbedf18020445c9df5fac11526fda1.json`。加载器已按当前Fixture、Implementation、Adapter、配置指纹、Model身份和Validity重新验证。

### 0.1 历史运行记录（不适用于当前@8）

| 字段 | 值 |
|---|---|
| Run ID | `ccrun_25bcd3f2fbf040ff957dabe02bf7ea63` |
| Outcome | `HISTORICAL_PASS / CURRENTLY_STALE` |
| Actual Model | `glm-5.2` |
| Request Count | `2` |
| Usage | Input `327` / Output `77` tokens |
| Result Digest | `sha256:91ccfbb2d084ee41888833d7519d1867cd96c91b22d5bed279032e76d5a0a5ac` |
| Valid Until | `2026-09-05T10:54:43.604984Z` |

该结果证明第7版Coding Plan适配实现。当前加载器会因Implementation Digest、Adapter Version和配置指纹不一致拒绝它；更早的在线推理Endpoint结果继续作为历史证据保留，不适用于当前运行。

## 1. 运行方式与数据边界

运行器发送两次最小Schema约束JSON Object请求。每次使用不同随机Canary，第二个请求不得包含第一个Canary。请求固定`thinking.type=disabled`，首个System Message确定性携带注册的closed JSON Schema。随后以本地Oracle验证工具输入/输出拒绝、closed Schema、精确单JSON围栏规范化、受限前导文本规范化和尾随文本拒绝。

运行结果只保存：

- Fixture、实现文件、配置、请求Body和证据摘要；
- Provider Request ID、实际Model身份、聚合Token Usage和执行时间；
- 每个Case的Outcome、Evidence Kind和Evidence Digest；
- 30天有效期及失效依赖。

结果不保存API Key、Authorization Header、Prompt正文、Canary值、模型输出正文或Provider错误正文。文件以`0600`权限、`O_EXCL`方式创建；同名文件不覆盖。

## 2. 必须通过的Case

| Case | Evidence | Oracle |
|---|---|---|
| `CC-ARK-01` | Live Wire | 两次请求均只发往冻结的方舟北京HTTPS Endpoint。 |
| `CC-ARK-02` | Live Wire | 请求顶层字段集合逐字等于Profile allowlist，没有调用方扩展透传。 |
| `CC-ARK-03` | Live Wire | `tools=[]`、`tool_choice=none`、`parallel_tool_calls=false`。 |
| `CC-ARK-04` | Live Wire | 无Conversation、Previous Response、托管Prompt、Context Management或Store字段；`stream=false,n=1`。 |
| `CC-ARK-05` | Live Wire + Response | 两次请求都使用`json_object`、确定性closed Schema System Message和固定`thinking.type=disabled`，并返回可由应用侧closed validator接受的完整结果。 |
| `CC-ARK-06` | Two-call Canary | 首次Canary只在首次请求，未进入第二次请求；两次输出各自匹配独立Schema。 |
| `CC-ARK-07` | Offline Negative Oracle | Tool输入/输出与Schema非法输出失败关闭；唯一JSON围栏及受限非结构前缀可确定性规范化，尾随文本仍拒绝。 |
| `CC-ARK-08` | Live Response | 请求值逐字等于冻结`model_ref`，两次实际返回Model身份逐字等于冻结的expected actual fingerprint；当前分别为`glm-5-2-260617`和`glm-5.2`。 |
| `CC-ARK-09` | Live Response | 两次Usage完整且总量算术一致，不以零替代未知。 |
| `CC-ARK-10` | Live Response | 两次均返回非空且不同的Provider Request ID。 |
| `CC-ARK-11` | Live Wire + Local Result | Secret只以`env:ARK_API_KEY`引用出现，不在Body、公开配置或结果中。 |
| `CC-ARK-12` | Offline Admission Oracle | 未加载已验证PASS结果时Adapter保持`OFFLINE_FIXTURE`；工具与Schema反例不产生可激活结果。 |

任一Case失败时整体为`FAIL`。已分派调用Outcome未知时不伪造PASS/FAIL Result，CLI返回`PROVIDER_OUTCOME_UNKNOWN`；必须保留原Request ID进行外部解析，无法解析时该次运行不能成为资格。

## 3. 不可变Result与加载门禁

Result Schema为`swm.ark-chat-conformance-result@1`。`result_digest`覆盖除自身外的完整closed Result。加载器重新验证：

- 顶层Schema、Fixture ID/Version和12项Case集合；
- Result与每项Evidence Digest格式及整体摘要；
- Outcome、Failure和Validity之间的一致性；
- 当前Fixture Digest、实现聚合Digest、Adapter Version和配置指纹；
- 请求Model别名、预期实际Model身份与唯一实际响应身份；
- Run时间、固定30天Validity Window及当前时间。

验证失败、配置变化、代码变化或过期均返回`QUALIFICATION_INVALID`。加载成功只形成Adapter Conformance Qualification；CE Definition注册和结果封存还会重新核对这份资格。

## 4. 执行命令

Provider、配置、Adapter、Fixture或相关实现变化后，从持有`ARK_API_KEY`的本地终端重新运行：

```bash
PYTHONPATH=src python3 -m software_world_model.interface.provider_cli conformance \
  --result-directory ./var/conformance \
  --operator local-operator
```

该命令会执行两次真实Provider调用。CLI摘要仍固定`production_eligible=false`和`qualification_status=CAPABILITY_EVALUATION_NOT_RUN`；它是CC阶段的不可变结论，不读取或回写下游CE。即使另有JWT CE Registration，CC PASS本身仍不能替代它。
