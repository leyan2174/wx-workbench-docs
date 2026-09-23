# 语音关联、原始SILK与外部解码

当前证据：C；来源为固定提交 `b7015ad2b7060a5dff6ddb9a9e2cc3a88403e86e` 的 `src/adapters/wechat/media/voice.rs`、`src/adapters/wechat/media/voice_export.rs`、`src/daemon/operations/voices.rs` 及 `src/business/VOICE_EXPORT.md`。本章的消息关联与原始导出说明属于当前实现；后文封包规范化和 PCM 示例是历史代码参考与独立合成检查，不属于当前产品能力。

**没有独立“语音密钥”的证据。** 数据库层解密后取得 SILK 字节；不能把音频解码器参数解释成加密密钥。

## 消息到媒体

输入是固定账号的离线明文数据库快照、username、完整来源 `message/message_N.db` 及消息 local_id。输出包含原始 SILK 字节和消息/媒体双方来源证据。

1. 精确读取指定分片的会话消息，验证是语音，取得 server_id 与 create_time。缺失、多行或身份矛盾均失败。
2. 枚举 `message/media_N.db`；在每个媒体库自己的 `Name2Id` 中，以 `user_name` 严格匹配会话，取得该库的 rowid。不能复用消息库里的 Name2Id 编号。
3. 在 `VoiceInfo` 中按 `chat_name_id` 与 `svr_id` 查找，跨分片也要求唯一。核对时间、字段类型、正负范围和其他关联证据；同值重复不是“随便取第一条”。
4. 读取 `voice_data` BLOB，保留原始字节，包括可能的 `02` 前缀。输出证据含 media_source、media_rowid、media_chat_name_id、media_local_id；媒体 local_id 与消息 local_id 不必相同。

核心关系为 `VoiceInfo.chat_name_id → 本媒体库 Name2Id.rowid`，以及 `VoiceInfo.svr_id → 消息 server_id`。仅凭时间戳或媒体 local_id 不够。上述严格关联路径限制单条语音16 MiB、媒体分片1024个、目录条目4096个；超限应明确报告，不能静默截断成完整结果。

## 当前原始导出

`wx voices` 输出 `.silk` 和 `.voice.json` 证据，保留原始字节及已有 `02` 前缀，不规范化封包、不追加结束标记、不转 WAV/MP3、不执行 ASR。`voice-messages`、MCP `get_voice_messages` 和 HTTP `/api/voice-messages` 只查询目录，不读取音频正文。

`voices` 的 `_voice_export_summary.json` 包含 manifest；聊天目录可保留语音引用并生成 `_voice_manifest.json`。消息身份由精确会话与非零 server_id 表达，账号另由 account_id 限定。媒体行坐标只定位来源证据，不能替代消息身份。字节已导出但关联尚未证明时，报告 partial 与 incomplete_items，并以非零状态结束；不能据此认定完整成功。

原始导出的媒体目录选择与前述严格消息关联是两步：先按账号媒体清单选择，再尝试完整消息来源上的严格关联。选择接受历史媒体分片命名，按时间/local_id及稳定分片、rowid顺序分页；该兼容清单不等同只接受编号分片的严格关联库存。各分片独立只读事务，不承诺跨库原子快照。源码入口经 `service::worker_keys::database_keys` 取得材料，固定运行账号与 ConfigPin；音频、证据和汇总分别受保护发布，证据发布失败不会回滚已落盘音频。

当前 `is_raw_silk` 只检查可选前缀后的 `#!SILK_V3` 头，不验证完整压缩包或可播放性。sender 与 duration_ms 是可选元数据，缺失不猜测；时长来自消息 XML，不能当作解码测量结果。

项目宿主的 CLI 与任务都通过 `prepare_voice_snapshot` 创建私有解密来源，再由 SQLite Backup 生成静态副本，仅对副本设置 `journal_mode=DELETE`。严格关联仍拒绝 WAL/SHM/journal；每库备份不保证跨库原子一致性。该准备可能耗时，读取时源变化会拒绝，应等待写入稳定后重试，不删除源侧车。机制属于项目宿主，不能改写为微信本身的存储规范或全版本兼容保证。具体生命周期见[项目架构](../implementation/architecture.md#私有数据库快照与有界读取)。

## 同步CLI与原始语音任务

持久任务 `export_voices` 与同步 `wx voices` 复用 `business::voice_export::select`、微信媒体 Catalog、严格消息关联及原字节写入。任务接受 `voice_export` 选择对象，不接受输出路径、数据库路径、账号、解码或转录参数；仅写入全新的宿主受控任务根，拒绝 `overwrite=true`。同步CLI仍允许显式输出目录及 `--overwrite`，两者不是完整参数对等。

```powershell
wx tasks submit export_voices --chat synthetic-user --offset 0 --limit 10 --wait
```

| 输入 | 选择语义 |
|---|---|
| 省略或null的 `chat` | 全账号媒体目录；不是任意账号选择 |
| 显式 `chat` | username精确匹配优先，否则按账号内不区分大小写的子串匹配；必须唯一，空白值拒绝 |
| 省略或null的 `limit` | None，不设业务条数上限；资源预算仍然生效 |
| `limit=0` | Some(0)，明确空选集，不回退默认条数 |
| `offset` / `limit` | 跨分片合并排序之后全局应用，不按每个分片分别截取 |
| `since` / `until` | 本地时间且包含端点；纯日期until为当天23:59:59，倒置区间拒绝 |

先按媒体时间、媒体local_id升序排列；并列保留适配器的有序分片及rowid顺序。有时间条件时未知媒体时间不入选。关联证明只补充消息证据，不改变选集、分页或文件名。语音目录查询的默认条数不能套用到原始导出；资源不足必须明确失败或报告不完整，不能悄悄添加业务条数上限。

## 时间来源与关联证据

不同对象中的同名 `timestamp` 不能混用：

| 对象字段 | 来源 |
|---|---|
| `summary.manifest[].timestamp` | 严格关联成功时为消息时间，由 `evidence.timestamp_source` 标识；未证实时保留媒体时间及来源 |
| 任务 `summary.items[].timestamp` | 媒体时间，`timestamp_source=media` |
| 任务sidecar顶层 `timestamp` | 媒体时间，`timestamp_source=media` |
| 任务sidecar的 `message_timestamp` / `message_timestamp_source` | 仅记录已证实消息时间；没有证据时为null，不从媒体时间伪造 |

当前严格反向关联要求消息与媒体时间一致，冲突仍为未证实。即使两个数值恰好相同，来源标签也不能互换。媒体坐标和来源字段仅用于诊断，不构成进一步读取文件的授权。

## 文件组与交付状态

任务结果的 `scope=raw_voices`；`selected_rows=null` 表示选集尚未确定，0才表示已确定为空。`exported` 只统计完成登记的SILK/证据组，`associated`、`unproven` 和 `incomplete_items` 分别表达关联和完整性，不把字节导出等同消息关联成功。

两个文件都发布并通过身份与摘要核对后，才一次写入产物索引。第二个文件失败时，第一个孤立文件不会进入清单或成功计数；先前完整登记组保留，后续汇总失败也不会抹掉它们。这是登记原子性，不是两次文件写入的事务。任务证据及汇总投影移除输出绝对路径，不把同步CLI的路径输出原样交付。

读取沿用受控产物清单、分块与下载接口。MCP与Web的写入开关、独立读取权限、幂等恢复及取消语义见[计划与产物](../implementation/plans-and-artifacts.md#原始语音任务与读写授权)。

## SILK 外层封包参考

本节保留 [b9fcd4c 历史音频实现](https://github.com/leyan2174/wx-workbench/blob/b9fcd4c9a5de5f3290502235af36bc4a404bf1f9/src/infrastructure/audio/mod.rs) 的规范化规则，历史哈希见[旧清单](../evidence/source-manifest-2026-09-17.json)。该文件不在当前源码版本中。下面的合成检查只验证这组封包规则，不验证 SILK 压缩内核，也不能证明当前导出器会执行这些步骤。

可选单字节 `02` 后必须是 ASCII `#!SILK_V3`（9字节）。之后循环读取 i16 小端长度：

```text
strip one optional leading 02
require header '#!SILK_V3'
while bytes remain:
    n = read_i16_le()
    if n == -1: require exact end and at least one packet; finish
    require 1 <= n <= 1024
    read exactly n payload bytes
    count += 1; require count <= 6000
if ended at packet boundary without -1:
    require at least one packet; append FF FF
```

只能在长度字段位置解释 `FF FF` 为结束标记，不能在压缩载荷中搜索它。拒绝半个长度字段、截断载荷、0或小于-1长度、结束标记之后的尾随数据、无音频包文件。

合成封包 `02 || '#!SILK_V3' || 01 00 || 00` 可测试规范化应去前缀并补 `FF FF`。其中 `00` 是人工占位载荷，**不保证可被 SILK 解码器解码**。

## 外部解码示例

外部工具可选择具备明确许可的 SILK 解码器。历史实现采用24,000 Hz、单声道、16位有符号小端 PCM；这只是本节计算示例的约定，不是当前项目的输出承诺。检查 PCM 非空且长度为偶数。WAV 封装或 FFmpeg MP3 编码在此之后进行；此输出采样率是解码方案的选择，不证明微信原始录音的采样率恒定。

PCM 字节数除以 `24000×1×2` 可计算秒数，例如96,000字节为2秒。转录文本是后续 ASR 结果，不能替代原始语音证据；远端 ASR 需要独立授权，不能由“读取语音”隐式触发。
