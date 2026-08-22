---
id: FINDING-010-017
kind: implementation-finding
status: dispositioned
authority: development-evidence
owners: [quality, engineering]
depends_on: [ITER-010-SLICE-001, ITER-010-VERIFICATION, FINDING-010-005, FINDING-010-016]
code: []
tests: []
iteration: ITER-010
classification: verification
scope: individual
disposition: narrow-the-representative-run-profile-to-exact-relevant-files-without-raising-product-fuses
target: ITER-010-VERIFICATION
---

# FINDING-010-017：代表题的目录级 Source Profile 在首个搜索中耗尽 64 文件上限

## Observation

第二次真实 `V-WEB-000` run 将 `mall-admin/src/main/java` 与 `mall-security/src/main/java` 两个目录登记为 SOURCE capability。对字面量
`JWT` 的首个 search 按 exact revision 检查 64 个文件、读取 127,961 bytes，只在排序靠前的 `mall-admin` 文件中返回一个命中，并以
`PARTIAL / SOURCE_FILE_FUSE_EXHAUSTED` 结束。随后更具体的 `JwtTokenUtil` search 在 dispatch 前被 Broker 拒绝，因为 question-scoped
`maximum_source_files=64` 已耗尽。

该限制来自 ITER-010 Manifest 和 Request 的既定产品安全上限，不是临时网络错误，也不是 Worker 少读了已授权结果。目录级 Profile
实际包含 167 个 allowed entries，远大于代表题需要的登录/JWT 相关文件集合；把整个目录作为该一题的 capability 是 verification
configuration 过宽。

## Decision and disposition

保持 `maximum_source_files=64`、bytes/operation/wall-time/no-progress 上限和所有 Broker/Worker 检查不变。下一次代表题 run 只登记 exact
revision 中与管理员登录、Security configuration、JWT token/filter、动态授权、README/POM 和现存测试直接相关的明确文件路径；不登记
`src/main/resources`，不发送其中的配置或 credential，也不把未登记文件在运行时追加进 Profile。

这只是收窄用户已经授权的 disclosure 范围，不扩大授权或产品能力。最终 launch receipt 必须密封新的 Profile ref/digest 和逐路径
allowlist；如果收窄后仍因安全上限无法回答，`V-WEB-000` 保持 FAIL，不能调高 fuse 或把 answerable 问题改写为 boundary PASS。

## Verification

run `web-v-web-000-004` 永久保留 FAIL：4 dispatch、0 retry、0 switch、Production Activation `NOT_EXECUTED`。下一次 clean candidate
run 必须证明精确路径 Profile 的 allowed file count 不超过 64、所有实际读取均在该 Profile 和用户授权范围内，并从同一 Web 完成 Answer、
Citation 与独立 Review；当前尚未执行。
