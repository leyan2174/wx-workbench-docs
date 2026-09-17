# 朋友圈记录与 SNS 媒体

证据：C。来源：`src/adapters/wechat/moments.rs`、`src/adapters/wechat/moments/{decode.rs,query_xml.rs,legacy.rs}`、`src/adapters/wechat/media/{sns_keystream.rs,SNS_KEYSTREAM.md}`。可独立实现程度：记录读取、外层恢复协议可实现；**WxIsaac64内部状态初始化、递推和输出算法未独立审计，不能仅凭本章重写内部引擎**。

## 记录输入与结构

解密的`sns/sns.db`中，`SnsTimeLine(tid,user_name,content)`提供帖子行。content解析出的TimelineObject包含id、username、createTime、contentDesc及ContentObject等字段。保留数据库tid、数据库user_name与XML身份的区别；冲突要报告，不能直接覆盖。

`SnsMessage_tmp3`提供评论/通知等记录，包含feed_id、create_time、type、from_username、from_nickname、to_username、to_nickname、content；某些查询还使用local_id、is_unread。评论导出排除`COALESCE(del_status,0)≠0`，按create_time排序。字段和表名属于已适配schema；不得推断未来仍叫tmp3。帖子与通知通过feed_id及帖子身份核对，不能用用户昵称连接。

### content外层解码

- BLOB以`28 B5 2F FD`开头时按Zstandard解压，窗口log最大23，结果最多800,000字节；否则按原字节处理。
- TEXT去首尾空白，以`<`开头直接作为XML文本；否则去全部空白，若长度≥16、偶数且全为十六进制则hex解码；再尝试长度≥24且为4倍数的标准Base64。解出字节按BLOB规则处理。两者都不适用时保留文本。
- 兼容路径解UTF-8时丢弃非法字节，执行HTML实体反转义；这可能丢失信息，证据输出应保留解码质量标记。
- 编码输入上限1,600,000字节，XML最多200,000字符。拒绝DOCTYPE或ENTITY声明；处理XML不能加载外部实体。

这些是项目适配策略，不表示微信所有content都允许上述任意形式。出现无法解析的行应计数并报告部分覆盖。

### 媒体元数据

从`TimelineObject/ContentObject/mediaList/media`逐项读取id、type、sub_type；url和thumb的文本为地址，其属性可含md5、key、token、enc_idx；enc的key作为enc_key；size的width、height、totalSize读取为整数。视频还可能有videomd5、videoDuration。缺失值保留缺失，不以0或空串伪造完整性。地址、token及密钥材料不写公开日志。

合成XML（无地址、无密钥）：

```xml
<TimelineObject><id>101</id><username>synthetic-user</username>
<createTime>1700000000</createTime><contentDesc>合成测试</contentDesc>
<ContentObject><mediaList><media><id>201</id><type>2</type>
<size width="32" height="32" totalSize="64"/>
</media></mediaList></ContentObject></TimelineObject>
```

## WxIsaac64宿主协议

当前桥接依赖显式提供的固定哈希WASM，支持资产SHA-256：`dca796bacec37d8522c7983b3945e5d579bd74164e3b21f0ebc773be6dfc8b6e`。这是资产身份，不是账号秘密，也不是许可证明。

输入key为调用方提供字符串，原始UTF-8最多1024字节；去首尾空白及BOM后不能为空，保留NEL（U+0085）。不要自行把字符串转换成宿主整数，否则`00042`、负号、超大数及空白行为可能改变。内部数值解释交给现有模块，异常输入语义未完整审计。

请求n字节时，`A=(n+7)&~7`向上按8对齐；要求n≥1、A≤25 MiB且受调用方预算限制。模块构造WxIsaac64对象，生成A字节，通过回调取得完整字节数组，**反转整个A字节数组再取前n字节**；不是逐8字节反转，也不是先截断再反转。

```text
stream(n,key) = reverse(module_generate(trim(key), round_up_8(n)))[0:n]
image_plain[i] = encrypted_image[i] XOR stream(image_length,key)[i]
p = min(video_length, 131072)
video_plain[0:p] = encrypted_video[0:p] XOR stream(p,key)
video_plain[p:] = encrypted_video[p:]
```

图片路径按完整响应长度恢复；相册下载器仅在响应格式未识别、去空白后的key非空且不等于字符串`0`时调用引擎。底层引擎的合成`0`输入测试不表示下载器会用该值恢复图片。来源补充：`src/application/moments/album_images.rs`。2026-09-17复核迁移路径，密钥流引擎文件哈希未变，本轮没有新增引擎运行验证。

视频只处理最多128 KiB前缀，后缀逐字节保持。明文视频若长度≥12且偏移4..8为`ftyp`，可直接复制。恢复后仍仅检查这一格式标记，不是MAC、完整MP4解析或播放验证；不能保证检出所有错误key。

### 最小ABI边界

模块导出memory、构造初始化、malloc/free和dynCall。宿主在embind注册回调中识别`WxIsaac64`并取得构造/生成invoker及析构函数。字符串内存为`[u32 UTF-8长度][字节][NUL]`，构造经`dynCall_iii`、生成经`dynCall_viii`、析构经`dynCall_vi`。ASM_CONSTS编号434460对应的生成回调只接受`ii`签名与预期对齐长度的一次有界复制。未知宿主能力应trap，不能为兼容而开放任意文件、网络或JS执行。

该ABI摘要不足以独立复刻WASM；重建无二进制依赖的引擎仍需有权使用的算法规范及交叉向量。现有内部合成向量覆盖key `0/1/-1/18446744073709551615/00042/带空白42`与8字节边界、128KiB边界，但本仓不复制未经许可审查的资产或声称已运行这些向量。

## 首发限制

公开默认构建不携带、不嵌入、不下载、不自动发现该WASM。加密单视频须由用户通过`--wasm`显式提供已获授权且匹配固定哈希的本地资产；明文MP4直通。相册目前没有外部WASM参数，因此依赖该密钥流的远端加密图片/视频报告engine unavailable。已有明文或不依赖引擎的缓存路径另行判断，不能宣传为所有SNS媒体开箱即用。

沙箱资源默认内存64MiB、燃料硬上限300,000,000；内存视频API输入上限256MiB，流式CLI不能直接套用该整文件限额。每次调用独立状态，完成或失败后清除guest内存与未返回密钥流；这不等于整个进程绝无残留。
