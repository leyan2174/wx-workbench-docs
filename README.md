# wx-workbench-docs

独立保存 Windows 微信本地数据机制与可重建知识。已知目标为 **Windows 微信 4.1.13.65**；这是源码适配的目标范围，不代表所有章节均有该版本的独立实机验证。

本仓库的主要内容无需打开项目源码即可阅读。可重建程度逐项见[覆盖矩阵](evidence/coverage.md)。项目实现仓库为 [wx-workbench](https://github.com/leyan2174/wx-workbench)。本文档已通过Private交付验收，尚未宣布公开验收完成。

2026-09-18按固定源码提交修订入口、不可变计划、受控产物、创建时Job归属及跨入口原始语音任务，范围见[版本证据](evidence/versions.md)。当前候选目标仍为Private；文档合成检查不等于生产版本运行验收。

当前Private源码基线为`ddb9d093c0b8ce7db5ad8b1808adf66e6e2432a3`。上游授权证据仍有未决项，见[来源与许可](SOURCES.md)；不把本候选的Private交付条件解释为公开衍生源码已获准分发。

## AI 作者声明

**本仓库当前的原创文档均由 AI 生成、整理和撰写，不是人类手工撰写的。** 人类维护者提出需求并决定收录与发布；这不表示已经逐项完成人工事实核验。

引用或参考的第三方资料、既有代码和许可证文本仍归原作者及权利人，不宣称它们由本仓库的 AI 原创。AI 撰写不保证内容无误，证据等级、验证范围和未知项见各章节及[覆盖矩阵](evidence/coverage.md)。

## 微信机制

1. [范围、术语与证据](wechat/scope.md)
2. [账号目录与数据库布局](wechat/storage.md)
3. [数据库页加解密与 WAL](wechat/database-crypto.md)
4. [联系人、会话、消息与通话关联](wechat/records.md)
5. [图片 DAT](wechat/dat.md)
6. [表情媒体](wechat/emoticons.md)
7. [朋友圈与 SNS 媒体](wechat/sns.md)
8. [语音关联、原始SILK与外部解码](wechat/voice.md)
9. [聊天与朋友圈导出](wechat/export.md)
10. [密钥材料及生命周期](wechat/key-material.md)
11. [验证方法与未知项](wechat/validation.md)

## 项目实现与通用设计

- [当前实现与执行边界](implementation/architecture.md)
- [不可变计划与受控产物](implementation/plans-and-artifacts.md)
- [账号隔离、确定定位与原子发布](design/reliable-processing.md)

## 证据与贡献

- [版本与永久链接策略](evidence/versions.md)、[覆盖矩阵](evidence/coverage.md)
- [来源与许可](SOURCES.md)、[纠错与贡献](CONTRIBUTING.md)、[候选状态](STATUS.md)

原创文档首版采用 Apache-2.0，第三方既有贡献不被重新授权。代码项目当前开发、修改与重构由 AI 完成、维护者未手写代码，这是维护者的声明；不表示第三方历史代码是本项目 AI 原创。独立知识仓库不构成权利争议或移除要求的豁免，也不提供未知许可 WASM 的镜像。
