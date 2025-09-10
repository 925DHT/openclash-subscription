import requests, yaml, socket, time, re, random

CLASH_SUB_LIST = [
    "https://raw.githubusercontent.com/learnhard-cn/free_proxy_ss/main/clash.yaml",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/clash.yml",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge_yaml.yml"
]
OPTIMAL_IP_LIST_URL = "https://raw.githubusercontent.com/ethgan/yxip/main/ip.txt"
PRIORITY_PORTS = [8443,2086,2089,4443]
TEST_TARGETS = [
    ("github.com",443),("www.google.com",443),("www.youtube.com",443),
    ("api.cloudflarewarp.com",443),("t.me",443),("chat.openai.com",443)
]
CLASH_SUPPORT_TYPES = {"ss", "vmess", "trojan"}

def fetch_optimal_ip_list():
    try:
        resp = requests.get(OPTIMAL_IP_LIST_URL, timeout=10)
        return [ip.strip() for ip in resp.text.splitlines() if re.match(r"^(\d{1,3}\.){3}\d{1,3}$", ip)]
    except: return []

def replace_with_optimal_ip(node, ips):
    if not ips: return node
    domain = node.get("server","")
    if not re.match(r"^(\d{1,3}\.){3}\d{1,3}$", domain):
        node["server"] = random.choice(ips)
    return node

def test_latency(node):
    delays = []
    ok = True
    for host,port in TEST_TARGETS:
        try:
            t0=time.time()
            s=socket.create_connection((node["server"],int(node["port"])),timeout=2.5)
            s.close()
            delays.append((time.time()-t0)*1000)
        except:
            ok = False
            delays.append(9999)
    return max(delays) if ok else 99999

def fetch_nodes():
    proxies = []
    for url in CLASH_SUB_LIST:
        try:
            resp = requests.get(url, timeout=20)
            data = yaml.safe_load(resp.text)
            for node in data.get("proxies", []):
                if node.get("type") in CLASH_SUPPORT_TYPES and node.get("name") and node.get("server") and node.get("port"):
                    proxies.append(dict(node))
        except: pass
    addr_set, unique = set(), []
    for n in proxies:
        key = f"{n['server']}:{n['port']}"
        if key not in addr_set:
            addr_set.add(key)
            unique.append(n)
    return unique[:200]

def prefer_ports(nodes):
    preferred, others = [], []
    for x in nodes:
        if int(x["port"]) in PRIORITY_PORTS: preferred.append(x)
        else: others.append(x)
    return (preferred+others)[:200]

def filter_available_and_low_latency(nodes, ips):
    tested=[]
    for n in nodes:
        n["delay"]=test_latency(n)
        tested.append(n)
    available = [n for n in tested if n["delay"] < 200]
    if len(available)<50:
        sorted_all = sorted(tested, key=lambda x:x["delay"])
        for n in sorted_all:
            if n not in available and n["delay"] < 10000:
                n=replace_with_optimal_ip(n,ips)
                available.append(n)
            if len(available)>=50: break
    return sorted(available, key=lambda x:x["delay"])[:50]

def save_clash_yaml(nodes):
    names=[n["name"] for n in nodes]
    config={
        "port":7890, "socks-port":7891, "allow-lan": True, "mode":"Rule", "log-level":"info",
        "external-controller":"127.0.0.1:9090",
        "proxies":nodes,
        "proxy-groups":[
            {"name":"🚀 节点选择","type":"select","proxies":names},
            {"name":"自动选择","type":"url-test","proxies":names,"url":"http://www.gstatic.com/generate_204","interval":300},
            {"name":"♻️ 自动切换","type":"fallback","proxies":names,"url":"http://www.gstatic.com/generate_204"}
        ],
        "rules":[
            "DOMAIN-SUFFIX,cn,DIRECT", "GEOIP,CN,DIRECT","DOMAIN-SUFFIX,baidu.com,DIRECT",
            "DOMAIN-SUFFIX,qq.com,DIRECT","DOMAIN-SUFFIX,weixin.qq.com,DIRECT",
            "DOMAIN-SUFFIX,alipay.com,DIRECT","DOMAIN-SUFFIX,taobao.com,DIRECT",
            "DOMAIN-SUFFIX,tmall.com,DIRECT","DOMAIN-SUFFIX,zhihu.com,DIRECT",
            "DOMAIN-SUFFIX,bilibili.com,DIRECT", "DOMAIN-SUFFIX,163.com,DIRECT",
            "DOMAIN-SUFFIX,126.com,DIRECT","DOMAIN-SUFFIX,iqiyi.com,DIRECT",
            "DOMAIN-SUFFIX,youku.com,DIRECT","DOMAIN-SUFFIX,sohu.com,DIRECT","DOMAIN-SUFFIX,sina.com,DIRECT",
            "DOMAIN-SUFFIX,gov.cn,DIRECT","DOMAIN-SUFFIX,edu.cn,DIRECT",
            "DOMAIN-SUFFIX,netflix.com,🚀 节点选择","DOMAIN-KEYWORD,netflix,🚀 节点选择",
            "DOMAIN-SUFFIX,openai.com,🚀 节点选择","DOMAIN-SUFFIX,chatgpt.com,🚀 节点选择",
            "DOMAIN-SUFFIX,auth0.com,🚀 节点选择","DOMAIN-SUFFIX,poe.com,🚀 节点选择",
            "DOMAIN-SUFFIX,telegram.org,🚀 节点选择","DOMAIN-SUFFIX,t.me,🚀 节点选择",
            "DOMAIN-SUFFIX,google.com,🚀 节点选择","DOMAIN-SUFFIX,facebook.com,🚀 节点选择",
            "DOMAIN-SUFFIX,instagram.com,🚀 节点选择","DOMAIN-SUFFIX,twitter.com,🚀 节点选择",
            "DOMAIN-KEYWORD,youtube,🚀 节点选择","DOMAIN-SUFFIX,github.com,🚀 节点选择",
            "MATCH,自动选择"
        ]
    }
    with open("subscription.yaml","w",encoding="utf-8") as f: yaml.dump(config,f,allow_unicode=True,sort_keys=False)

def save_subscription_links():
    raw_base = "https://raw.githubusercontent.com/925DHT/kalifox/main/"
    with open("SUBSCRIBE.md", "w", encoding="utf-8") as f:
        f.write(
            "# 订阅链接一览\n\n"
            "本仓库自动聚合并输出以下订阅文件，支持 Clash 客户端。\n\n"
            f"- Clash（YAML）：[{raw_base}subscription.yaml]({raw_base}subscription.yaml)\n\n"
            "将上述链接复制到你对应客户端的订阅/导入栏，即可一键获取最新免费节点！\n\n"
            f"仓库地址：[https://github.com/925DHT/kalifox](https://github.com/925DHT/kalifox)\n"
        )

def main():
    print("Step1: 获取节点...")
    nodes = fetch_nodes()
    print("Step2: 优选端口...")
    nodes = prefer_ports(nodes)
    print("Step3: 拉取优选IP...")
    ips = fetch_optimal_ip_list()
    print("Step4: 可用性&延迟筛选...")
    nodes = filter_available_and_low_latency(nodes, ips)
    print("Step5: 保存配置文件...")
    save_clash_yaml(nodes)
    save_subscription_links()
    print("全部完成！")

if __name__ == "__main__":
    main()
