# 覆盖矩阵

“可独立实现”表示本仓给出的格式和步骤足以编写相应范围的实现，可使用标准密码学/压缩库；不表示本轮已完成真实微信实机验证。C=代码可证实，T=合成检查，U=未知。实际检查结果见[候选状态](../STATUS.md)。

2026-09-18按固定提交修订命令、计划、产物、进程及原始语音边界。T只指文档自有合成检查；历史SILK封包检查不代表当前导出器执行规范化，生产Rust测试不在本次验证范围。

| 机制 | 覆盖程度 | 证据 | 主要边界 |
|---|---|---|---|
| [账号路径与库清点](../wechat/storage.md) | 部分覆盖 | C | 安装形态、完整目录与历史变体未穷尽 |
| [主库页与HMAC](../wechat/database-crypto.md) | 可独立实现 | C/T | 固定4096/80布局，输入已给定材料 |
| [WAL提交与页恢复](../wechat/database-crypto.md) | 格式与步骤可指导实现；端到端待验证 | C/T | 15项结构/认证/应用顺序检查；未执行WAL+AES端到端或实机验证 |
| [基础联系人/会话/消息](../wechat/records.md) | 可独立实现 | C/T | 限已列字段；完整私有schema未覆盖 |
| [群成员与通话摘要](../wechat/records.md) | 部分覆盖 | C | 成员schema变体、信令及录音未知 |
| [图片资源packed_info](../wechat/records.md) | 部分覆盖 | C | MD5提取启发式，非完整结构解析 |
| [DAT V1/V2/legacy XOR](../wechat/dat.md) | 可独立实现 | C/T | 不含WXGF内部解码与自动材料捕获 |
| [表情AES分支](../wechat/emoticons.md) | 可独立实现 | C/T | 输入为已取得密文/材料；目录schema部分覆盖 |
| [SNS帖子与媒体字段](../wechat/sns.md) | 部分覆盖 | C/T | 兼容解码可能丢失非法UTF-8；并非全部字段 |
| [SNS密钥流包装/视频前缀](../wechat/sns.md) | 部分覆盖 | C | ABI可描述；WASM内部算法与许可未解决 |
| [语音关联与原始SILK](../wechat/voice.md) | 可指导关联、原始导出及任务交付 | C | 共享选择/严格关联、双时间来源与完整组登记；不转码或ASR；任务不覆盖已有目录 |
| [历史SILK封包参考](../wechat/voice.md) | 规则与合成例子可实现 | 历史C/T | 旧固定提交证据；非当前产品能力，压缩内核未验证 |
| [聊天/朋友圈导出](../wechat/export.md) | 部分覆盖 | C | 可组合重建；历史兼容格式/游标未全冻结 |
| [数据库候选派生](../wechat/key-material.md) | 可独立实现 | C/T | 不含完整跨版本进程定位 |
| [worker材料与初始化](../implementation/architecture.md) | 部分覆盖 | C | 已绑定路径经broker；bootstrap直接Store；本轮未跑进程测试 |
| [不可变计划与受控产物](../implementation/plans-and-artifacts.md) | 部分覆盖 | C | 仅列明任务；原始语音读写独立授权，取消不回滚已登记组；不是全部入口对等 |
| [创建时Job归属](../implementation/architecture.md) | 部分覆盖 | C | Windows 10+；不兼容时拒绝，无本轮进程测试 |
| 密钥服务器保存/跨设备/根派生关系 | 待验证 | U | 没有证据，不作肯定或否定断言 |

优先补充：固定版本独立运行验证；用有权公开的合成向量加强WAL和SNS交叉验证；资源packed_info完整schema；各章节固定版本的独立实验记录。第一版不通过编造字段或复制未知许可资产消除缺口。
