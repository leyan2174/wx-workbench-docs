# 版本与永久链接

微信机制目标范围仍为Windows微信4.1.13.65，不代表每章都有该版本实机验证。项目实现固定在 `b7015ad2b7060a5dff6ddb9a9e2cc3a88403e86e`，tree `b8ddc0abdb7a7366423889c87c331ccd17f31971`；2026-09-23在本地Git对象库核实。工作树和其他提交不纳入此源码基线。

代码仓：[leyan2174/wx-workbench](https://github.com/leyan2174/wx-workbench)。[固定版本](https://github.com/leyan2174/wx-workbench/tree/b7015ad2b7060a5dff6ddb9a9e2cc3a88403e86e)及[source-manifest.json](source-manifest.json)提供逐文件链接、Git blob SHA-256与字节数。Private链接需要访问权限，未逐链接验证远端可读性。

## 证据范围

本次相对 `468bcc50aadc4b2f1e4901c1038b19de8b8c2a87` 有界阅读实际改变的机制和接口：`media_snapshot` 与语音宿主的静态副本准备、`ResourceSnapshot` Backup/DELETE、运行目录与计划扫描Pin、配置/进程身份/图片读取预算、文章XML直接字段、Web账号和联系人投影及会话顺序。既有CLI注册、计划引用、完整组登记、Job创建时绑定和材料授权的未变化部分复用先前相关阅读。没有逐行重审全部变更文件、运行生产Rust或访问真实账号。

清单schema 3直接读取 `git show <commit>:<path>` 的精确字节，不读取工作树，不按当前HEAD改选版本，不进行换行归一化。90个来源文件的捕获包括相关实现及入口文件；`sha256`与`git_blob_sha256`表示同一Git blob。新增或变化文件的哈希采集不等于逐行审计，未变化文件仅复用此前相关段落阅读。

```text
python tools/capture_sources.py <source-repository> --publication-commit b7015ad2b7060a5dff6ddb9a9e2cc3a88403e86e --check
```

## 历史证据

[2026-09-18清单](source-manifest-2026-09-18.json)原字节保留前次468bcc50固定基线，用于本轮Git blob比较。[2026-09-17清单](source-manifest-2026-09-17.json)保留b9fcd4c历史映射；其音频实现仅用于[语音章节](../wechat/voice.md)的外部封包/PCM参考，不属于当前源码。[2026-09-16清单](source-manifest-2026-09-16.json)及首轮候选指纹同样只用于历史版本。历史链接和原作者归属不随基线更新改指其他代码。

此前维护方按target修复复验合并的2367通过、0剩余失败、22忽略包含4项未提交G5测试，不是468bcc50单次全绿的证明；不得混入本次固定提交统计。历史WAL和密码学合成检查也不是本次执行。

## 维护方运行证据与限制

维护方报告本次源码在隔离状态下完成34个测试target，共2424通过、0失败、23忽略；fmt与strict Clippy退出0，23个独立fixture编译检查退出0，Web 29项、npm 36项通过。本任务转述该交付信息，不冒充执行者。fixture编译不是fixture全部运行；忽略测试仍未执行，G5 new_messages改动及ASR遗留不在本提交中。

这些结果不证明所有真实微信功能、媒体可播放性、所有权限ACL或所有微信版本兼容。源变化仍可能导致私有快照拒绝，不能用删除WAL绕过。上游授权未决项、SNS内部引擎与部分schema缺口继续保留。

## 候选与发布

本次独立文档已通过维护方的Private内容验收，实际提交与远端状态以Git记录为准。文件指纹由[candidate-manifest.json](candidate-manifest.json)记录，不包含其自身或Git元数据。源码、独立文档、二进制和npm分别验收；文档检查不能证明公开分发许可已解决。来源与许可边界见[来源说明](../SOURCES.md)。
