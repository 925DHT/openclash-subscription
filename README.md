# Free Proxy Node Aggregator 自动聚合免费代理节点

## 功能亮点

- **多源聚合**：自动抓取 GitHub、Telegram、Google、YouTube、Warp 等免费节点
- **多协议支持**：Clash、V2ray、Singbox 三大格式同步输出
- **节点智能筛选**：延迟测速、优选端口、自动优选IP替换
- **一键云端自动部署**：GitHub Actions 定时任务，无需服务器
- **支持所有主流客户端**：OpenClash、Clash Verge、V2rayN、Sing-box 等

---

## 订阅链接（每次自动更新后最新）

- Clash（YAML）: [https://raw.githubusercontent.com/925DHT/kalifox/main/clash.yaml](https://raw.githubusercontent.com/925DHT/kalifox/main/clash.yaml)
- V2ray（JSON）: [https://raw.githubusercontent.com/925DHT/kalifox/main/v2ray.json](https://raw.githubusercontent.com/925DHT/kalifox/main/v2ray.json)
- Singbox（JSON）: [https://raw.githubusercontent.com/925DHT/kalifox/main/singbox.json](https://raw.githubusercontent.com/925DHT/kalifox/main/singbox.json)

将上述链接复制到你对应客户端的订阅/导入栏，即可一键获取最新免费节点！

---

## 使用教程

1. Fork 本仓库
2. 可选：补充你自己的节点源（在 `update_proxy.py` 的 `CLASH_SUB_LIST` 里加）
3. Actions 页面启用工作流（首次需点 Enable workflows）
4. 等待自动运行（每天北京时间0点/12点自动更新），或手动触发
5. 下载 clash.yaml / v2ray.json / singbox.json 订阅文件，导入任意客户端即可

## 高级自定义

- 自定义节点保留数量、端口、测速目标等，可编辑 `update_proxy.py`
- 支持更多聚合源，欢迎提交 PR 或 issue 建议

## 免责声明

本项目仅用于学习交流，所有节点均来自互联网，不保证可用性和安全性，请勿用于违法用途。

---

> **订阅链接简明索引也见 SUBSCRIBE.md**  
