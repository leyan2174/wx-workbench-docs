# 版本与永久链接

目标微信版本：Windows 4.1.13.65。最近源码映射：2026-09-17，Private源码基线为`b9fcd4c9a5de5f3290502235af36bc4a404bf1f9`，父提交为本轮阅读锚点`f6f3ba9479f693b8dad73586a0b284016fd3d1b3`。经差异核对，两者间生产机制源码未变；变化包括来源/技术文档及worker密钥测试断言。这是Private交付映射，不是Public许可验收或新增实机验证。

正式代码仓：[leyan2174/wx-workbench](https://github.com/leyan2174/wx-workbench)。当前文件与SHA-256见[source-manifest.json](source-manifest.json)，逐文件记录是否与上述commit一致及复核方式。未变更文件复用前轮相关段落阅读并核对哈希；变化文件按符号/差异重读，不声称通读每个文件全部行。代码仓README/docs由其他维护任务更新，不作为本次新增架构结论的唯一依据。

41个登记文件已映射至该完整提交；清单内source_link为固定提交链接，Private仓库需要访问权限，本任务未验证远端推送及登录可读结果。源码版本入口：[b9fcd4c固定版本](https://github.com/leyan2174/wx-workbench/tree/b9fcd4c9a5de5f3290502235af36bc4a404bf1f9)。

Windows工作树可能使用CRLF，Git对象使用LF。清单保留两份原始哈希，`byte_exact_commit_match`表示字节完全一致，`matches_observed_commit`仅将CRLF归一化为LF后比较；不忽略其他空白或内容差异。

首次阅读发生于2026-09-16，当时HEAD为`d4e22a0cc76f82d49afd33456002a32098ab9e04`且工作树在变；原清单保留于[历史清单](source-manifest-2026-09-16.json)，不是当前路径索引。历史candidate-first-review同样只标识旧候选，不能据此认定当前文件哈希失配。

本次确认src/toolkit已删除，迁移路径及broker/bootstrap分支见[架构](../implementation/architecture.md)。数据库加密、DAT、SNS密钥流和表情纯格式文件哈希未变；语音关联仅测试入口迁移；朋友圈增加导出快照适配；provider为saved/memory/account，旧auto已拒绝。没有继承旧生产测试计数，也没有在本轮运行生产Rust测试。

## 引用策略

正文直接说明算法，使用源码仓相对路径作为证据名称，不使用指向另一仓`../src`的悬空链接。固定链接采用`https://github.com/leyan2174/wx-workbench/blob/<完整40位commit>/<路径>`；本轮清单不使用未经核验的行号。文件改名时保留旧版本映射，不把旧永久链接改为新的不相关文件。

文档仓发布时也记录自身完整提交。一次机制修订应同时说明适用微信版本、源码提交、证据等级、变化原因及验证范围。公开URL能访问不代表其历史已经通过隐私和许可审核；最终验收由发布负责人单独执行。

当前目标仍为Private。代码基线映射已完成，待负责人记录文档Git提交并核验远端访问。如未来采用不同的公开历史或源码快照，应重新建立映射，不能把当前Private基线自动当作Public授权通过的依据。
