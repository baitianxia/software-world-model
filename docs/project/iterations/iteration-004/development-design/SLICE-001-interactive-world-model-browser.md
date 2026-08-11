---
id: ITER-004-SLICE-001
kind: development-slice
status: authorized
authority: current-development
owners: [engineering]
depends_on: [ITER-004-PROPOSAL, SYS-ARCH-DEPLOYMENT, SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING, SYS-CONTRACT-APPLICATION-STRUCTURE-VIEW, SYS-CONTRACT-AI-MODEL-GATEWAY, SYS-OPS-LOCAL-BROWSER, SYS-QUALITY-SECURITY]
code: [src/software_world_model/interface, validation/structure_world_model_iteration_003/g3b]
tests: [tests]
iteration: ITER-004
coding_input: true
---

# SLICE-001：自由提问接入隔离 World Model

## Status and dependencies

本 Slice 已由用户明确授权。它依赖 ITER-003 accepted G3b product package、prepared Read Bundles、Gateway inputs
和本机 macOS capability runner；这些工件任一缺失或漂移都阻断启动。

## Current vs expected behavior

当前服务的自由输入只进入 Evidence-first `DIRECT_INVESTIGATION`；ITER-003 页面只回放冻结 terminal。期望行为是
独立的 `WORLD_MODEL / EVALUATION_ONLY` 页面接收新问题，为 allowlisted exact Read Set 启动同一隔离 Answer、Gateway
和 Citation Projector，返回刚生成且验签通过的 Result。绝不静默调用 Direct path。

## System contracts and invariants

遵守 `SYS-CONTRACT-APPLICATION-WORLD-MODEL-ANSWERING` 的 exact Read Authority、通用 View、完整 Need/Constraint、
Gap 与十阶段 Authority；遵守 `SYS-ARCH-DEPLOYMENT` 和 `SYS-QUALITY-SECURITY` 的三角色文件/网络边界、exact Gateway
与独立 Citation；遵守 `SYS-OPS-LOCAL-BROWSER` 的模式可见性、回环绑定和评测水印。

## Interfaces and affected code

- 新的 interface-owned WSGI browser application 提供 health、allowlisted dataset、问题提交、Result 与 Citation GET；
- 一个窄 runner Protocol 把 HTTP 与 security-sensitive evaluation orchestration 分开；
- evaluation launcher 只从 accepted ITER-003 evidence root 装配 immutable package/Bundles/Gateway input，并为每个请求创建
  新的 0700 run directory；
- 浏览器显示原问题、答案、Snapshot/Read Set、View/Coverage/Gap、Citation 与完整 Authority，并明确 dataset 与
  accepted product commit。

## Compatibility, data and security boundaries

现有 `http_api` 与 Evidence-first 页面保持不变；新入口使用独立进程和端口，不能共享或伪造 activation。Answer 只看到
package、chosen Bundle、gateway socket 和专属 output；Gateway 独占 credential；trusted broker 在 Answer Result 密封后
才读 authority DB；Projector 无网络且没有答案回传端口。HTTP 无认证，只绑定 `127.0.0.1`。用户问题和已发布 typed
Structure 可以发送到 exact Provider；Source/Evidence payload、Oracle 和 baseline 禁止发送或挂载。

## Open questions and implementation risks

- accepted stage 是本机忽略工件，缺失时提供可操作错误但不得自动重建或下载；
- Product interpreter 只覆盖 Maven reactor Structure，任意文本可以提交但不是任意知识都能回答；
- 一个问题可能耗时数十秒，UI 必须显示进行中并防止并发重复提交；
- 任何需要改变 accepted Answer/Gateway/Projector package 的缺陷都使复用资格失效，必须停下并重新验证产品，而不是
  由 launcher 绕过。

## Acceptance scenarios

1. 页面加载即显示 `WORLD_MODEL`、`EVALUATION_ONLY`、accepted product commit 和三个固定 dataset；没有仓库路径输入。
2. 支持问题产生新 request ID、1 次 Provider call、完整 Authority page 与可独立打开的 Citation Projection。
3. 不支持的设计动机问题返回 Knowledge Gap、0 正文 Citation，不读取 Source 或切换 Direct。
4. 篡改 dataset、Result、Citation URL/digest、accepted stage 或输入边界均失败关闭并显示明确错误。
5. 服务只绑定回环；一次请求进行中时不能重复发送；刷新不把旧 Result 伪装成新执行。
6. focused、full regression、docs gate 与真实浏览器人工验收全部通过。

## Findings

链接本轮的 [Findings](../findings/README.md) 与[实现发现回写规则](../../../governance/implementation-feedback-policy.md)。
