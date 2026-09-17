# 账号目录与数据库布局

证据：C。来源：`src/config.rs`、`src/adapters/wechat/{contacts/mod.rs,moments.rs,planning/mod.rs}`、`src/adapters/wechat/media/{voice.rs,legacy_dat.rs,directory_layout.rs}`。可独立实现程度：已知路径和枚举规则可实现；完整目录清单与不同安装形式部分覆盖。

## 从固定账号开始

Windows发现路径的当前实现读取 `%APPDATA%/Tencent/xwechat/config/` 下的 ini 文本，把其内容解析为数据根，再查看 `xwechat_files/<account>/db_storage`。自动候选按库的最新修改时间排序；这只是一种发现策略，不能证明最近修改目录就是用户要处理的账号。进入处理前应固定账号根及配置，不在失败时切换账号。

下面是逻辑布局，`<account>`、`<conversation-md5>` 和 `<content-md5>` 均为占位符，不是实际账号数据：

```text
xwechat_files/<account>/
  db_storage/
    contact/contact.db
    session/session.db
    message/message_N.db
    message/media_N.db
    message/message_resource.db
    sns/sns.db
  msg/
    attach/<conversation-md5>/YYYY-MM/Img/<content-md5>.dat
    video/
```

`N` 表示已发现的分片编号，不保证连续，也不保证不同类型数据库相同 N 彼此对应。主库旁可能有 `-wal` 和 `-shm`；不要把缓存副本、旧目录或迁移目录自动纳入当前集合。库不存在与库读取失败是不同结果。

## 文件到记录

1. 清点固定根下已知数据库类型，保留相对路径作为 source。
2. 以各数据库自己的盐校验材料并解密到独立输出根，禁止覆盖加密源。
3. 按所需能力检查真实 schema，再查询；不能只看文件名推定字段存在。
4. 消息表分布由枚举与表名决定，跨分片合并要保留来源。
5. 媒体发现与消息关联分别执行；只有严格证据链通过后才能把文件作为某消息附件。

## 图片缓存路径

会话目录名通常由 UTF-8 username 的 MD5 小写十六进制组成。历史 DAT查找从 `msg/attach/<hash>/<年月>/Img` 选择文件；先试本地时区下时间戳减31天、原时间、加31天对应目录，再按目录名排序遍历。这并非严格的“前月/当月/后月”，月长差异会重复或跨过月份。

历史 DAT模式在每个目录内优先 `.dat`、`_h.dat`、`_t.dat`。目录导出另有 `_h.dat`、`.dat`、`_w.dat`、`_t.dat`、`_t_w.dat` 顺序，还支持另一种 `MsgAttach/<hash>/Image/<month>` 布局。两套策略不能混为统一微信规格；文件存在不能证明其内容、所属消息或账号。

错误边界包括目录穿越、符号链接/重解析点、大小写归一化重名、无法访问的分片、处理时源变化。独立实现应拒绝越出固定根的路径，并对不完整清点给出失败或明确的部分结果标记。
