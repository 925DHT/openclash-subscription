import requests
import yaml
import socket
import time
import re
import random

# 节点公开源，可扩展更多
CLASH_SUB_LIST = [
    "https://raw.githubusercontent.com/learnhard-cn/free_proxy_ss/main/clash.yaml",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/clash.yml",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge_yaml.yml",
    # 你可扩展Telegram、YouTube、Google等渠道的订阅链接
]

OPTIMAL_IP_LIST_URL = "https://raw.githubusercontent.com/ethgan/yxip/main/ip.txt"
CLASH_SUPPORT_TYPES = {"ss", "vmess", "trojan"}
PRIORITY_PORTS = [8443, 2086, 2089, 4443]
TEST_TARGETS = [
    ("github.com", 443),
    ("www.youtube.com", 443),
    ("www.google.com", 443),
    ("api.cloudflarewarp.com", 443),  # warp
    ("t.me", 443),                   # Telegram
    ("chat.openai.com", 443),        # ChatGPT
]

# ---------------- 节点抓取部分 -------------------
def fetch_clash_nodes():
    proxies = []
    for url in CLASH_SUB_LIST:
        try:
            resp = requests.get(url, timeout=20)
            data = yaml.safe_load(resp.text)
            for node in data.get("proxies", []):
                if node.get("type") not in CLASH_SUPPORT_TYPES:
                    continue
                if not (node.get("name") and node.get("server") and node.get("port")):
                    continue
                proxies.append(dict(node))
        except Exception as e:
            print(f"Failed: {e}")
    # 去重
    addr_set = set()
    unique = []
    for n in proxies:
        key = f"{n['server']}:{n['port']}"
        if key not in addr_set:
            addr_set.add(key)
            unique.append(n)
    return unique[:200]  # 只保留前200个节点

# --------------- 优选端口筛选 --------------------
def prefer_ports(nodes):
    preferred = []
    others = []
    for node in nodes:
        if int(node["port"]) in PRIORITY_PORTS:
            preferred.append(node)
        else:
            others.append(node)
    # 优先端口节点在前，其余补满
    ret = preferred + others
    return ret[:200]

# --------------- 优选IP -------------------------
def fetch_optimal_ip_list():
    try:
        resp = requests.get(OPTIMAL_IP_LIST_URL, timeout=10)
        ips = []
        for line in resp.text.splitlines():
            line = line.strip()
            if re.match(r"^(\d{1,3}\.){3}\d{1,3}$", line):
                ips.append(line)
        return ips
    except Exception as e:
        print(f"获取优选IP列表失败: {e}")
        return []

def replace_with_optimal_ip(node, optimal_ips):
    if not optimal_ips:
        return node
    # 仅对常见CDN域名或延迟高的节点替换
    domain = node.get("server", "")
    cdn_keywords = ["cloudflare", "cdn", "workers.dev", "jsdelivr", "githubusercontent"]
    if (any(kw in domain for kw in cdn_keywords)
        or not re.match(r"^(\d{1,3}\.){3}\d{1,3}$", domain)):
        new_ip = random.choice(optimal_ips)
        node["server"] = new_ip
    return node

# --------------- 连通性与延迟测试 ----------------
def test_node_latency(node):
    # 仅简单TCP连通性/延迟测试
    delays = []
    for host, port in TEST_TARGETS:
        try:
            start = time.time()
            s = socket.create_connection((node["server"], int(node["port"])), timeout=3)
            # 实测可用再测目标站点
            s2 = socket.create_connection((host, port), timeout=3)
            s.close()
            s2.close()
            delays.append((time.time() - start) * 1000)  # ms
        except Exception:
            delays.append(9999)
    return max(delays)  # 取最慢的延迟（最保守）

def filter_low_latency(nodes, optimal_ips):
    tested = []
    for node in nodes:
        delay = test_node_latency(node)
        node["delay"] = delay
        tested.append(node)
        print(f"{node['name']}@{node['server']}:{node['port']} 延迟: {delay:.1f}ms")
    # 首先保留所有 <200ms 的
    low = [n for n in tested if n["delay"] < 200]
    # 补足到50个（优先优选IP替换高延迟节点）
    if len(low) < 50:
        sorted_all = sorted(tested, key=lambda x: x["delay"])
        for n in sorted_all:
            if n not in low:
                # 替换延迟高的节点IP
                n = replace_with_optimal_ip(n, optimal_ips)
                low.append(n)
            if len(low) >= 50:
                break
    # 最终只保留50个
    return sorted(low, key=lambda x: x["delay"])[:50]

# ----------------- OpenClash规则 ---------------
def openclash_config(nodes):
    proxies = nodes
    names = [n["name"] for n in proxies]
    config = {
        "port": 7890,
        "socks-port": 7891,
        "allow-lan": True,
        "mode": "Rule",
        "log-level": "info",
        "external-controller": "127.0.0.1:9090",
        "proxies": proxies,
        "proxy-groups": [
            {
                "name": "🚀 节点选择",
                "type": "select",
                "proxies": names
            },
            {
                "name": "自动选择",
                "type": "url-test",
                "proxies": names,
                "url": "http://www.gstatic.com/generate_204",
                "interval": 300
            },
            {
                "name": "♻️ 自动切换",
                "type": "fallback",
                "proxies": names,
                "url": "http://www.gstatic.com/generate_204"
            }
        ],
        "rules": [
            # 境内常用直连
            "DOMAIN-SUFFIX,cn,DIRECT",
            "GEOIP,CN,DIRECT",
            "DOMAIN-SUFFIX,baidu.com,DIRECT",
            "DOMAIN-SUFFIX,qq.com,DIRECT",
            "DOMAIN-SUFFIX,weixin.qq.com,DIRECT",
            "DOMAIN-SUFFIX,alipay.com,DIRECT",
            "DOMAIN-SUFFIX,taobao.com,DIRECT",
            "DOMAIN-SUFFIX,tmall.com,DIRECT",
            "DOMAIN-SUFFIX,zhihu.com,DIRECT",
            "DOMAIN-SUFFIX,bilibili.com,DIRECT",
            "DOMAIN-SUFFIX,163.com,DIRECT",
            "DOMAIN-SUFFIX,126.com,DIRECT",
            "DOMAIN-SUFFIX,iqiyi.com,DIRECT",
            "DOMAIN-SUFFIX,youku.com,DIRECT",
            "DOMAIN-SUFFIX,sohu.com,DIRECT",
            "DOMAIN-SUFFIX,sina.com,DIRECT",
            "DOMAIN-SUFFIX,gov.cn,DIRECT",
            "DOMAIN-SUFFIX,edu.cn,DIRECT",
            # 解锁类
            "DOMAIN-SUFFIX,netflix.com,🚀 节点选择",
            "DOMAIN-SUFFIX,netflix.net,🚀 节点选择",
            "DOMAIN-KEYWORD,netflix,🚀 节点选择",
            "DOMAIN-SUFFIX,openai.com,🚀 节点选择",
            "DOMAIN-SUFFIX,chatgpt.com,🚀 节点选择",
            "DOMAIN-SUFFIX,auth0.com,🚀 节点选择",
            "DOMAIN-SUFFIX,poe.com,🚀 节点选择",
            "DOMAIN-SUFFIX,telegram.org,🚀 节点选择",
            "DOMAIN-SUFFIX,t.me,🚀 节点选择",
            "DOMAIN-SUFFIX,google.com,🚀 节点选择",
            "DOMAIN-SUFFIX,facebook.com,🚀 节点选择",
            "DOMAIN-SUFFIX,instagram.com,🚀 节点选择",
            "DOMAIN-SUFFIX,twitter.com,🚀 节点选择",
            "DOMAIN-KEYWORD,youtube,🚀 节点选择",
            "DOMAIN-SUFFIX,github.com,🚀 节点选择",
            # 兜底
            "MATCH,自动选择"
        ]
    }
    return config

# ----------------- 主流程 ----------------------
def main():
    print("获取节点...")
    nodes = fetch_clash_nodes()
    print(f"原始节点数: {len(nodes)}")
    nodes = prefer_ports(nodes)
    print(f"优选端口后节点数: {len(nodes)}")
    print("拉取优选IP...")
    optimal_ips = fetch_optimal_ip_list()
    print("节点延迟实测筛选...")
    nodes = filter_low_latency(nodes, optimal_ips)
    config = openclash_config(nodes)
    with open("subscription.yaml", "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)
    print("subscription.yaml 已生成。")

if __name__ == "__main__":
    main()
