import requests
import yaml
import time
import subprocess

# 可用的公共clash订阅源（可自行增加）
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
                # 只要有 name+server+port 就收
                if node.get('name') and node.get('server') and node.get('port'):
                    proxies.append(node)
        except Exception as e:
            print(f"Failed: {e}")
    # 按 server+port 去重
    unique = []
    addr_set = set()
    for p in proxies:
        key = f"{p['server']}:{p['port']}"
        if key not in addr_set:
            addr_set.add(key)
            unique.append(p)
    return unique[:50]  # 最多抓50个

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

    # 测速
    for node in nodes:
        node['delay'] = ping_node(node['server'])
        print(f"{node['name']} - {node['server']} 延迟: {node['delay']} ms")

    # 取延迟最低的20个
    nodes = sorted(nodes, key=lambda x: x['delay'])[:20]

    # 生成 subscription.yaml
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
