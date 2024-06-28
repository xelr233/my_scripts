#!/usr/bin/python3
# coding=utf-8
"""
Author: Xe
time: 2024/2/14
cron: 0 25 * * * *
new Env('监控AkileCloud');
"""
import requests
import json
import os
import time
from pprint import pprint
from notify import send

title = os.getenv('TITLE') or '监控_AkileCloud'
debug = os.getenv('DEBUG') or False
url = "https://api.akile.io/api/v1/store/GetVpsStore"
headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"}

def fetch_data():
    for _ in range(10):
        response = requests.get(url=url, headers=headers)
        if response.ok:
            if debug:
                print(f"获取成功，状态码：{response.status_code}")
                pprint(response.json())
            return response.json()
        else:
            print(f"获取失败，状态码：{response.status_code}, 重试中...,第{_+1}次")
        time.sleep(5)
    return None

def process_data(data_json):
    checked_nodes = []
    for item in data_json['data']:
        for node in item['nodes']:
            for plan in node['plans']:
                if plan['price_datas'][0]['price'] < 1700:
                    nodes_price = {
                        'name': plan['plan_name'],
                        'stock': plan['stock'],
                        'price': plan['price_datas'][0]['price'] / 100
                    }
                    checked_nodes.append(nodes_price)
    if debug:
        print("检查结果：")
        pprint(checked_nodes)
    return checked_nodes

data_json = fetch_data()
if data_json is None:
    print("获取失败")
    exit()

checked_nodes = process_data(data_json)

try:
    with open("result.log", 'r+', encoding="UTF-8") as f:
        context = json.loads(f.read())
        difference = [item for item in checked_nodes if item not in context]
        if difference:
            f.seek(0)
            f.write(json.dumps(checked_nodes))
            f.truncate()
            need_send_msg = True
        else:
            print("暂无更新")
            exit()
except FileNotFoundError:
    print("文件不存在")
    with open("result.log", 'w', encoding="UTF-8") as f:
        f.write(json.dumps(checked_nodes))
        difference = checked_nodes
        need_send_msg = True

msg = "\n".join([f"节点类型：{each['name']}🖥️ 价格：{each['price']}💰 数量：{each['stock']}✅" for each in difference])
send(title, msg)