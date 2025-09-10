# GitHub Actions 自动获取 Clash/OpenClash 节点订阅完整教程（每日自动更新）

本教程将手把手教你如何用 GitHub Actions 实现每天自动抓取、测速、筛选并发布可用的 Clash/OpenClash 节点订阅链接，实现“一键即用”。

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

你的仓库应如下（注意文件夹及文件名）：

```
openclash-subscription/
├── .github/
│   └── workflows/
│       └── update_subscription.yml
├── update_subscription.py
└── README.md
```

### 2.2 文件内容

#### 2.2.1 update_subscription.py

```python name=update_subscription.py
import requests
import yaml
import subprocess

CLASH_SUB_LIST = [
    "https://raw.githubusercontent.com/learnhard-cn/free_proxy_ss/main/clash.yaml",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/clash.yml",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge_yaml.yml"
]

def fetch_clash_nodes():
    proxies = []
    for url in CLASH_SUB_LIST:
        try:
            print(f"Fetching: {url}")
            resp = requests.get(url, timeout=15)
            data = yaml.safe_load(resp.text)
            for node in data.get('proxies', []):
                if node.get('name') and node.get('server') and node.get('port'):
                    proxies.append(node)
        except Exception as e:
            print(f"Failed: {e}")
    unique = []
    addr_set = set()
    for p in proxies:
        key = f"{p['server']}:{p['port']}"
        if key not in addr_set:
            addr_set.add(key)
            unique.append(p)
    return unique[:50]

def ping_node(server):
    try:
        r = subprocess.run(['ping', '-c', '1', '-W', '1', server], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if r.returncode == 0:
            for line in r.stdout.decode().split('\n'):
                if 'time=' in line:
                    return float(line.split('time=')[-1].split()[0])
        return 9999
    except Exception:
        return 9999

def main():
    print("获取节点...")
    nodes = fetch_clash_nodes()
    print(f"共获取到 {len(nodes)} 个节点，开始测速...")
    for node in nodes:
        node['delay'] = ping_node(node['server'])
        print(f"{node['name']} - {node['server']} 延迟: {node['delay']} ms")
    nodes = sorted(nodes, key=lambda x: x['delay'])[:20]
    config = {
        "port": 7890,
        "socks-port": 7891,
        "allow-lan": True,
        "mode": "Rule",
        "log-level": "info",
        "external-controller": "127.0.0.1:9090",
        "proxies": nodes,
        "proxy-groups": [
            {
                "name": "🚀 节点选择",
                "type": "select",
                "proxies": [n['name'] for n in nodes]
            },
            {
                "name": "自动选择",
                "type": "url-test",
                "proxies": [n['name'] for n in nodes],
                "url": "http://www.gstatic.com/generate_204",
                "interval": 300
            }
        ],
        "rules": [
            "DOMAIN-SUFFIX,google.com,🚀 节点选择",
            "DOMAIN-SUFFIX,facebook.com,🚀 节点选择",
            "DOMAIN-KEYWORD,youtube,🚀 节点选择",
            "DOMAIN-SUFFIX,github.com,🚀 节点选择",
            "MATCH,自动选择"
        ]
    }
    with open("subscription.yaml", "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)
    print("subscription.yaml 已生成。")

if __name__ == "__main__":
    main()
```

---

#### 2.2.2 工作流文件（用于定时自动运行）

```yaml name=.github/workflows/update_subscription.yml
name: Update Clash Subscription

on:
  schedule:
    - cron: '0 3 * * *' # 每天 UTC+8 上午11点自动执行
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
        run: |
          pip install requests PyYAML

      - name: Run update script
        run: |
          python update_subscription.py

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

---

#### 2.2.3 项目说明

可直接将本教程内容保存为 `README.md`。

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

1. 上传全部文件后，点击仓库上方 `Actions`。
2. 首次启用需点击 `Enable workflows`。
3. 可手动点击 `Run workflow` 测试自动化任务能否正常运行。
4. 稍等片刻，刷新页面，查看是否自动生成了 `subscription.yaml`，并查看日志是否有报错。

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
