import requests
import yaml
import socket
import time
import re
import random

# 节点公开源（港澳台/机场榜/社区推荐）
CLASH_SUB_LIST = [
    "https://raw.githubusercontent.com/learnhard-cn/free_proxy_ss/main/clash.yaml",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/clash.yml",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge_yaml.yml",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/main/sub/share/v2ray.txt",
    "https://raw.githubusercontent.com/AmazingDM/sub/master/Clash.yaml",
    "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ACL4SSR_Online_Full_Mannix.yml"
]

# 优选IP（来自 ethgan/yxip 仓库，可自建）
OPTIMAL_IP_LIST_URL = "https://raw.githubusercontent.com/ethgan/yxip/main/ip.txt"

CLASH_SUPPORT_TYPES = {"ss", "vmess", "trojan"}
PRIORITY_PORTS = [8443, 2086, 2089, 4443]
# 境内常用站测速目标
TEST_TARGETS = [
    ("baidu.com", 443),
    ("qq.com", 443),
    ("bilibili.com", 443),
    ("weixin.qq.com", 443),
]

# 港澳台/大陆友好关键词
CN_FRIENDLY_KEYWORDS = [
    "港", "hk", "hongkong", "hong kong",
    "台", "tw", "taiwan",
    "澳门", "mo", "macao",
    "中国", "大陆", "cn", "china",
    "IEPL", "直连", "专线", "国内", "CMI", "CN2", "深港", "沪港", "广港"
]

def is_cn_friendly(node):
    """节点名或server字段是否含港澳台/国内关键词"""
    name = str(node.get("name", "")).lower()
    server = str(node.get("server", "")).lower()
    for kw in CN_FRIENDLY_KEYWORDS:
        if kw.lower() in name or kw.lower() in server:
            return True
    return False

def fetch_clash_nodes():
    proxies = []
    for url in CLASH_SUB_LIST:
        try:
            resp = requests.get(url, timeout=20)
            if url.endswith('.txt'):
                # txt订阅特殊处理
                txt = resp.text
                # v2rayN格式节点（简单支持vmess/trojan/ss链接）
                for line in txt.splitlines():
                    line = line.strip()
                    if line.startswith(("ss://", "vmess://", "trojan://")):
                        # 可用 clash2singbox/any2clash 或本地转换工具预处理，或留空
                        continue
                continue
            data = yaml.safe_load(resp.text)
            for node in data.get("proxies", []):
                if node.get("type") not in CLASH_SUPPORT_TYPES:
                    continue
                if not (node.get("name") and node.get("server") and node.get("port")):
                    continue
                if is_cn_friendly(node):
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
    return unique[:200]

def prefer_ports(nodes):
    preferred = []
    others = []
    for node in nodes:
        if int(node["port"]) in PRIORITY_PORTS:
            preferred.append(node)
        else:
            others.append(node)
    ret = preferred + others
    return ret[:200]

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
    domain = node.get("server", "")
    cdn_keywords = ["cloudflare", "cdn", "workers.dev", "jsdelivr", "githubusercontent"]
    if (any(kw in domain for kw in cdn_keywords)
        or not re.match(r"^(\d{1,3}\.){3}\d{1,3}$", domain)):
        new_ip = random.choice(optimal_ips)
        node["server"] = new_ip
    return node

def test_node_latency(node):
    # TCP连通性/延迟测试（对境内目标）
    delays = []
    for host, port in TEST_TARGETS:
        try:
            start = time.time()
            s = socket.create_connection((node["server"], int(node["port"])), timeout=3)
            s2 = socket.create_connection((host, port), timeout=3)
            s.close()
            s2.close()
            delays.append((time.time() - start) * 1000)
        except Exception:
            delays.append(9999)
    return max(delays)

def filter_low_latency(nodes, optimal_ips):
    tested = []
    for node in nodes:
        delay = test_node_latency(node)
        node["delay"] = delay
        tested.append(node)
        print(f"{node['name']}@{node['server']}:{node['port']} 延迟: {delay:.1f}ms")
    low = [n for n in tested if n["delay"] < 200]
    if len(low) < 50:
        sorted_all = sorted(tested, key=lambda x: x["delay"])
        for n in sorted_all:
            if n not in low:
                n = replace_with_optimal_ip(n, optimal_ips)
                low.append(n)
            if len(low) >= 50:
                break
    low = [n for n in low if n["delay"] < 5000]
    return sorted(low, key=lambda x: x["delay"])[:50]

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
            "MATCH,自动选择"
        ]
    }
    return config

def main():
    print("抓取港澳台/国内友好节点中...")
    nodes = fetch_clash_nodes()
    print(f"原始港澳台友好节点数: {len(nodes)}")
    nodes = prefer_ports(nodes)
    print(f"优选端口后节点数: {len(nodes)}")
    print("拉取优选IP...")
    optimal_ips = fetch_optimal_ip_list()
    print("节点健康与延迟实测筛选...")
    nodes = filter_low_latency(nodes, optimal_ips)
    config = openclash_config(nodes)
    with open("subscription.yaml", "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)
    print("subscription.yaml 已生成。")

if __name__ == "__main__":
    main()
