# 语音提取与编解码

证据：C。来源：`src/adapters/wechat/media/voice.rs`、`src/infrastructure/audio/mod.rs`。2026-09-17复核：关联文件仅迁移测试入口，SILK封包和24kHz输出规则保持；音频基础设施另增WAV输入校验，不属于本章已验证的SILK内核范围。可独立实现程度：数据库关联、SILK 外层封包和转换管线可实现；SILK 压缩算法内部不在本仓复刻，使用具备明确许可的兼容解码器。

**没有独立“语音密钥”的证据。** 数据库层解密后取得 SILK 字节；不能把音频解码器参数解释成加密密钥。

## 消息到媒体

输入是固定账号的离线明文数据库快照、username、完整来源 `message/message_N.db` 及消息 local_id。输出包含原始 SILK 字节和消息/媒体双方来源证据。

1. 精确读取指定分片的会话消息，验证是语音，取得 server_id 与 create_time。缺失、多行或身份矛盾均失败。
2. 枚举 `message/media_N.db`；在每个媒体库自己的 `Name2Id` 中，以 `user_name` 严格匹配会话，取得该库的 rowid。不能复用消息库里的 Name2Id 编号。
3. 在 `VoiceInfo` 中按 `chat_name_id` 与 `svr_id` 查找，跨分片也要求唯一。核对时间、字段类型、正负范围和其他关联证据；同值重复不是“随便取第一条”。
4. 读取 `voice_data` BLOB，保留原始字节，包括可能的 `02` 前缀。输出证据含 media_source、media_rowid、media_chat_name_id、media_local_id；媒体 local_id 与消息 local_id 不必相同。

核心关系为 `VoiceInfo.chat_name_id → 本媒体库 Name2Id.rowid`，以及 `VoiceInfo.svr_id → 消息 server_id`。仅凭时间戳或媒体 local_id 不够。项目限制单条语音16 MiB、媒体分片1024个、目录条目4096个；超限应明确报告，不能静默截断成完整结果。

## SILK 外层封包

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

## 音频输出

规范化封包交给 SILK 解码器，当前项目要求输出24,000 Hz、单声道、16位有符号小端 PCM。检查 PCM 非空且长度为偶数。WAV 封装或 FFmpeg MP3 编码在此之后进行；此输出采样率是项目的选择，不证明微信原始录音的采样率恒定。

PCM 字节数除以 `24000×1×2` 可计算秒数，例如96,000字节为2秒。转录文本是后续 ASR 结果，不能替代原始语音证据；远端 ASR 需要独立授权，不能由“读取语音”隐式触发。
