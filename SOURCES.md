# 来源与许可

原创说明、原创Mermaid图源和本仓合成检查采用[Apache-2.0](LICENSE)。此许可仅覆盖有权授权的内容，不替代第三方许可。没有从旧图、生成HTML、真实账号材料或未知许可二进制复制资产。

## 技术来源链

| 来源 | 与本仓内容的关系 | 许可/证据边界 |
|---|---|---|
| [wx-workbench](https://github.com/leyan2174/wx-workbench) | 当前源码实现与机制证据；各章给出具体路径 | 原创项目部分Apache-2.0；第三方部分仍各自适用 |
| [jackwener/wx-cli](https://github.com/jackwener/wx-cli) | 代码项目继承的Rust查询和数据库解密基础 | 已直接核对代码仓保留历史`8d32c08:LICENSE`中的MIT文本，全文保留于[第三方声明](THIRD_PARTY_NOTICES.md)；本仓不复制其源码 |
| [ylytdeng/wechat-decrypt](https://github.com/ylytdeng/wechat-decrypt) | 代码项目吸收的导出、媒体和微信数据解析；DAT注释指向decode_image.py | 授权证据未确认；代码仓本次审查未找到历史vendor中的独立LICENSE或README明确授权，本仓不把Apache-2.0扩展到上游衍生表达 |
| [LOGO127/wechat-ai-memory](https://github.com/LOGO127/wechat-ai-memory) | 账号SHA-512/HMAC捕获思路及SQLCipher派生参数参考 | MIT仅转述历史本地声明，未独立核实上游许可证；保留声明不等于确认授权，见[第三方声明](THIRD_PARTY_NOTICES.md) |
| [Frida](https://github.com/frida/frida)及[frida-rust](https://github.com/frida/frida-rust) | 代码项目账号捕获运行依赖 | 包括wxWindows Library Licence；本仓不分发运行库 |
| [hicccc77/WeFlow](https://github.com/hicccc77/WeFlow)与[LifeArchiveProject/WeChatDataAnalysis](https://github.com/LifeArchiveProject/WeChatDataAnalysis) | 代码仓记录的SNS WxIsaac64资产来源链 | 传入副本无明确许可证明；不分发WASM或相关镜像 |

本次来源映射到代码提交`ddb9d093c0b8ce7db5ad8b1808adf66e6e2432a3`的THIRD_PARTY_NOTICES.md。wx-cli许可证是本任务直接读取本地历史得到的文本证据；wechat-decrypt审查情况来自该提交的来源报告，LOGO127归属来自历史声明。后两项不是本任务独立取得的上游授权文件。上游链接用于定位归属，不表示对远端历史、全部许可证或每行来源完成独立审计。

历史LOGO127声明的本地源文件SHA-256为`958684992a3c894eb4f2d42d924a9a248b9ad5ba02b9fb6df308f77b6543debc`，已在历史证据清单记录；哈希只能固定声明文本，不能证明声明真实或授权有效。公开上游衍生源码前仍须补齐授权证据或审查并妥善替换受影响实现；移除vendor、语言翻译、AI改写或Private审阅均不自动解决该门槛。

本仓不是微信官方文档。不能将拆分仓库、重新叙述或AI生成理解为免除权利义务，也不把文档仓作为受限制代码/资产的替代下载渠道。发现来源错误或权利问题请按[贡献说明](CONTRIBUTING.md)提交可核验证据。
