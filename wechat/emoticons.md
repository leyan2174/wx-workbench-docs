# 表情媒体

证据：C。来源：`src/adapters/wechat/emoticons/remote_format.rs`、`src/application/emoticons/download.rs`。2026-09-17复核：纯格式文件哈希未变，下载编排已迁入application。可独立实现程度：已给定密文及材料的 AES 分支可实现；表情数据库完整 schema 和所有格式转换部分覆盖。

## 材料与恢复

输入是表情元数据提供的资源地址、内容标识及可选 AES 材料；地址和 token 可能敏感，不应进入公开日志。内容标识采用 32 个十六进制字符的 MD5 文本，不能当作下载内容真实性的充分凭据。

加密分支将材料按十六进制解析成恰好 16 字节；空白只允许在完整字节之间。例如 `00 01` 合法、`0 0` 非法。使用 **AES-128-CBC，IV=key**。这与 DAT 的 ECB 分段算法不同。

```text
K = parse_hex_exactly_16_bytes(material)
P = AES128_CBC_decrypt_without_unpadding(K, IV=K, ciphertext)
if 1 <= P[-1] <= 16 and last P[-1] bytes all equal P[-1]:
    remove those bytes
return P
```

密文必须满足 AES 块长度；实现对合法 PKCS#7 尾部进行去除，尾部不匹配时保留原字节，而非严格拒绝。复现时保留这一差别；若使用严格库函数，需要显式说明行为变化。CBC 无认证标签，填充成功不能代替媒体验证。

## 格式与下载边界

头部识别 JPEG、PNG、GIF、RIFF/WEBP；`WXGF` 或前256字节内 HEVC VPS 起始码 `00 00 00 01 40 01` 进入 HEVC 分支。当前识别是启发式，RIFF 不保证一定是 WebP。提取 HEVC 和转 GIF 等操作属于媒体转换，不是 AES 恢复本身。

当前下载器默认超时15秒、上限32 MiB、最多5次重定向；FFmpeg 为可配置的外部转换依赖。这些是项目策略，不是微信格式上限。应记录下载、解密、识别、转换、缓存命中各自结果；转换失败不能宣称生成了目标格式。

合成验证方法：取 K=`00 01 … 0F`，人工明文追加合法16字节块填充，以 K 同时作为 CBC 的 key 和 IV 加密，再调用恢复；同时构造非填充末尾，确认兼容分支保留。此处材料完全人工构造，不代表账号材料。具体可复现向量见[验证](validation.md)。
