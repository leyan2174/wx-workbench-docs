# 联系人、会话、消息与通话关联

证据：C。来源：`src/adapters/wechat/contacts/mod.rs`、`src/adapters/wechat/messages/{sessions.rs,read/mod.rs,summary.rs}`、`src/adapters/wechat/media/resource.rs`。可独立实现程度：已描述的基础字段与关联可实现；资源 packed_info 是启发式提取，完整私有 schema 部分覆盖。

## 最小字段图谱

| 数据源 | 表及字段 | 作用 |
|---|---|---|
| contact/contact.db | contact：id、username、nick_name、remark | 稳定账号标识与显示名称 |
| 同上 | chat_room：id、owner、群标识列 | 群身份；群标识列需按 schema 探测 |
| 同上 | chatroom_member：room_id、member_id | room_id关联chat_room.id；member_id关联contact.id |
| session/session.db | SessionTable：username、unread_count、summary、last_timestamp、last_msg_type、last_msg_sender、last_sender_display_name | 会话概览；不替代历史消息 |
| message/message_N.db | Msg_加会话MD5：local_id、local_type、create_time、real_sender_id、message_content、WCDB_CT_message_content；server_id、sort_seq按schema使用 | 分片内消息 |
| 同上 | Name2Id：rowid、user_name | 该分片发送者编号映射 |
| message/message_resource.db | ChatName2Id：rowid、user_name | 资源库自己的会话编号 |
| 同上 | MessageResourceInfo：chat_id、message_local_id、message_local_type、message_create_time、packed_info | 消息到附件内容标识 |

显示名称与 username 不可互换。备注、昵称可能重复或变化；导出保留 username 作为关联键。群成员表可用时查询全量成员；缺失时从历史消息观察到的发送者构成的是**已观察发送者集合**，不能命名为完整群成员。

## 消息表与分片

对会话 username 的 UTF-8 字节计算 MD5小写十六进制，得到表名 `Msg_<digest>`。合成会话 `abc` 对应 `Msg_900150983cd24fb0d6963f7d28e17f72`。发现表后检查真实 schema，不能将任意外部字符串直接拼成 SQL 标识符。

来源应为完整的根相对分片路径。相同 local_id 可以出现在不同分片或会话；读取一条消息必须限定来源、会话和 ID，并以最多两行检测歧义。server_id 是跨媒体关联证据之一，不是所有表通用主键。合并分页要使用确定的排序与来源决胜字段；只按 create_time 排序会在同秒消息中出现重复或遗漏。

发送者通过当前消息库的 `Name2Id.rowid=real_sender_id` 解出。另一个库相同数字的 rowid可能对应另一个人。引用回复同样需要保存源身份，不能在全库用 local_id撞配。

## 内容解码与类型

内容是 SQLite TEXT或BLOB。BLOB且 `WCDB_CT_message_content=4` 时使用 Zstandard；读取解压结果到预算+1字节以检测超限，其余TEXT/BLOB作为原字节处理。NULL、列缺失、超限和解压错误独立报告。随后再按消息类型解析文本/XML，不能先把二进制强制当UTF-8。

当前语义类型使用 `local_type & 0xFFFFFFFF`：1文本、3图片、34语音、43/62视频、49结构化消息、50通话、10000/10002系统。高位可能携带额外标志或子类型；**类型分类可以取低32位，严格资源关联必须保留完整local_type**。未识别类型保留原数值与原始内容，不伪装成空文本。

## 图片资源关联

1. 先得到唯一消息的 username、local_id、完整local_type和create_time。
2. 在资源库 `ChatName2Id` 用大小写敏感 username查出唯一rowid。
3. 查询 `MessageResourceInfo`，四条件同时等于 `chat_id/message_local_id/message_local_type/message_create_time`；要求字段是整数、packed_info是有界非空BLOB，并且唯一。
4. 从packed_info提取内容标识，随后在固定账号附件根查找并复核，再按[DAT](dat.md)恢复。

当前packed_info实现先搜索 `12 22 0A 20` 标记，取其后32字节ASCII十六进制；不成功则搜索第一个连续32字节十六进制片段并转小写。后者是启发式，可能误认其他字段；这不是完整Protocol Buffers schema，也不能称为密码学证明。完整编码结构仍待验证。

历史元数据接口还可能在精确时间匹配失败后选同local_id/低位类型的最新行；严格媒体发布路径不采用这项回退。独立实现不要无声地混用两者。

## 公众号文章解析

项目 `src/adapters/wechat/articles.rs::parse_push` 对可解析的 XML 遍历 `item`，只从各项的直接子字段取文本；字段包含嵌套元素时不接受该字段。文本与 CDATA 由 XML 解析器读取，合并文本节点并去首尾空白；标题或 URL 缺失/为空的项不产生文章。`pub_time` 不能解析为整数时使用收到消息的时间，不能把这个回退值解释为已证实的文章发布时间。

整个 XML 无法解析时保留 `InvalidContent` 问题标记，并尝试有限的 item 文本片段恢复；恢复到文章不表示输入完整有效。这是固定版本的适配器策略，不是公众号全部私有 schema；类型49也不限于文章。

## 通话记录

通话类消息低位类型为50。当前摘要解析在含`<voip`的XML中读取`msg`文本并折叠空白。`Duration:`后保留时长文本；已识别状态包括`Canceled`、`Line busy`、`Already answered elsewhere`、`Declined on other device`、`Call canceled by caller`、`Call not answered`及`Call wasn't answered`；其他文本保留为Other。

合成例子：`<voip><msg>Duration: 00:42</msg></voip>` 可导出为时长文本00:42。不能据此认定时长字段恒为统一数值单位，也不能推出完整呼叫信令、对方实际接听设备或存在通话录音。导出通话日志是筛选和投影消息；不是解码通话录音。

## 合成关联例子

在message_0中，Name2Id rowid=7表示`synthetic-sender`；在media_2中，rowid=7可以表示别的会话。消息 `(source=message/message_0.db, chat=abc, local_id=12, server_id=9001)` 的语音应在media库重新查询abc的编号，并以svr_id=9001匹配。故意制造两个匹配行时必须报歧义；删掉一个分片时应报告来源不完整，不能称为“没有媒体”。
