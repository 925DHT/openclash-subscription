# GitHub Actions 自动获取港澳台/大陆友好 Clash/OpenClash 节点订阅（每日自动更新）

本项目通过 GitHub Actions 自动抓取机场榜单、社区推荐、港澳台/大陆友好节点源，每日测速/健康检查，优选可用节点并生成 Clash/OpenClash 订阅，实现“国内高速一键即用”。

---

## 1. 新建专用仓库

1. 登录 [GitHub](https://github.com)。
2. 点击右上角“+” → New repository。
3. 仓库名建议为：`openclash-subscription`。
4. 选择 Public（公开），便于客户端访问订阅文件。
5. 点击 Create repository。

---

## 2. 上传核心文件

### 2.1 仓库目录结构

```
openclash-subscription/
├── .github/
│   └── workflows/
│       └── update_subscription.yml
├── update_subscription.py
└── README.md
```

### 2.2 文件内容

#### 2.2.1 update_subscription.py —— 港澳台/大陆优选+健康筛查

详见本仓库 `update_subscription.py`，核心优化亮点：

- 多渠道机场榜、港澳台节点源抓取
- 港澳台/大陆友好关键词筛选
- 优选端口优先、优选 IP 替换（IP 列表源自 [ethgan/yxip](https://github.com/ethgan/yxip/blob/main/ip.txt)）
- 境内常用网站为健康/延迟测试目标（更贴合国情）
- 失效节点自动剔除
- 每日自动筛查，随时保证国内可用性

#### 2.2.2 工作流文件

```yaml
name: Update Clash Subscription

on:
  schedule:
    - cron: '0 16 * * *'    # UTC+8 00:00
    - cron: '0 4 * * *'     # UTC+8 12:00
  workflow_dispatch:

jobs:
  update-subscription:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install requests PyYAML

      - name: Run update script
        run: python update_subscription.py

      - name: Commit & Push changes
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add subscription.yaml
          git commit -m "自动更新订阅 $(date '+%Y-%m-%d %H:%M:%S')" || echo "No changes"
          git push https://x-access-token:${GITHUB_TOKEN}@github.com/${{ github.repository }}.git HEAD:main
```

### 2.3 项目说明

- 推荐补充/替换 `CLASH_SUB_LIST` 为主打港澳台/大陆/社区机场榜
- 机场榜单/港澳台节点更适合国内科学上网
- 可定制自建优选 IP 列表，进一步提升可用性
- 优选 IP 源地址：[ethgan/yxip/main/ip.txt](https://github.com/ethgan/yxip/blob/main/ip.txt)

---

## 3. 配置 Actions 权限

1. 打开你的仓库主页，点击上方 `Settings`
2. 侧边栏选择 `Actions` → `General`
3. 下拉找到 **Workflow permissions**
4. 勾选 **Read and write permissions**
5. 建议再勾选 **Allow GitHub Actions to create and approve pull requests**
6. 点击下方 **Save** 保存

---

## 4. 启动并验证 Actions

1. 上传全部文件后，点击仓库上方 `Actions`
2. 首次启用需点击 `Enable workflows`
3. 可手动点击 `Run workflow` 测试自动化任务能否正常运行
4. 稍等片刻，刷新页面，查看是否自动生成了 `subscription.yaml`，并查看日志是否有报错

---

## 5. 获取订阅链接

将以下链接添加到 Clash/OpenClash 客户端的订阅中即可：

```
https://raw.githubusercontent.com/<你的GitHub用户名>/openclash-subscription/main/subscription.yaml
```

请将 `<你的GitHub用户名>` 替换为你的实际用户名。

---

## 6. 常见问题排查

- **没有生成 subscription.yaml？**
  - 检查 Actions 日志是否有报错
  - 检查 `update_subscription.py` 是否在仓库根目录

- **workflow 推送时报权限错误（403）？**
  - 检查第3步的 Actions 权限设置是否为“读写权限”
  - 仓库是否为 fork，fork 的仓库默认 Actions 不能推送，建议新建仓库

- **节点不可用或订阅内容为空？**
  - 公共订阅源网络波动大，可更换或添加更多订阅源

---

## 7. 进阶

- 更换或自定义订阅规则，编辑 `update_subscription.py` 里的 `config['rules']`
- 更换或增加订阅源，在 `CLASH_SUB_LIST` 变量中添加链接
- 调整自动执行频率，修改 `.github/workflows/update_subscription.yml` 的 `cron` 表达式

---

## 8. 免责声明

本项目仅供学习交流，所有节点来自互联网公开资源，请勿用于非法用途。
